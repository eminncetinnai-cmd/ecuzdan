"""
Unit Tests - Financial Repository
Read repositories for financial screens
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from werkzeug.exceptions import NotFound
from repositories.financial_repository import FinancialRepository


@pytest.mark.unit
def test_financial_repository_init():
    """Test FinancialRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = FinancialRepository(database=mock_db)
    
    assert repo.session == mock_session


@pytest.mark.unit
def test_financial_repository_imports():
    """Test that FinancialRepository can be imported"""
    from repositories.financial_repository import FinancialRepository
    
    assert FinancialRepository is not None


@pytest.mark.unit
def test_financial_repository_module_structure():
    """Test financial_repository module structure"""
    import repositories.financial_repository as financial_repo_module
    
    # Check for expected class
    assert hasattr(financial_repo_module, 'FinancialRepository')
    
    # Check for expected imports
    assert hasattr(financial_repo_module, 'Asset')
    assert hasattr(financial_repo_module, 'Category')
    assert hasattr(financial_repo_module, 'Payment')
    assert hasattr(financial_repo_module, 'RecurringPlan')
    assert hasattr(financial_repo_module, 'Transaction')
    assert hasattr(financial_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_financial_repository_extends_base():
    """Test FinancialRepository extends BaseRepository"""
    from repositories.financial_repository import FinancialRepository
    from repositories.base import BaseRepository
    
    assert issubclass(FinancialRepository, BaseRepository)


@pytest.mark.unit
def test_resolve_tenant_id_with_explicit_tenant():
    """Test _resolve_tenant_id with explicit tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = FinancialRepository(database=mock_db)
    result = repo._resolve_tenant_id(tenant_id='test_tenant')
    
    assert result == 'test_tenant'


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context")
def test_resolve_tenant_id_from_g():
    """Test _resolve_tenant_id from Flask g"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = FinancialRepository(database=mock_db)
    
    with patch('flask.g') as mock_g:
        mock_g.get.return_value = 'g_tenant'
        result = repo._resolve_tenant_id()
        
        assert result == 'g_tenant'


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context")
def test_resolve_tenant_id_no_context():
    """Test _resolve_tenant_id when no tenant context available"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = FinancialRepository(database=mock_db)
    
    with patch('flask.g', side_effect=Exception("No g")):
        try:
            repo._resolve_tenant_id()
            assert False, "Should raise RuntimeError"
        except RuntimeError as e:
            assert "Tenant context bulunamadı" in str(e)


@pytest.mark.unit
def test_transaction_page():
    """Test transaction_page method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_paginate = Mock()
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter_by.return_value.order_by.return_value.paginate.return_value = mock_paginate
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        result = repo.transaction_page(page=1, per_page=50, tenant_id='test_tenant')
        
        assert result == mock_paginate


@pytest.mark.unit
def test_get_transaction():
    """Test get_transaction method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transaction = Mock()
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.first.return_value = mock_transaction
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        result = repo.get_transaction(1, tenant_id='test_tenant')
        
        assert result == mock_transaction


@pytest.mark.unit
def test_list_transactions():
    """Test list_transactions method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query = mock_query
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = mock_transactions
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_transactions(tenant_id='test_tenant', order_desc=True)
        
        assert result == mock_transactions


@pytest.mark.unit
def test_list_transactions_no_tenant():
    """Test list_transactions without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query = mock_query
        mock_query.order_by.return_value.all.return_value = mock_transactions
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_transactions(order_desc=True)
        
        assert result == mock_transactions


@pytest.mark.unit
def test_add_transaction():
    """Test add_transaction method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transaction = Mock()
    mock_transaction.id = 1
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.return_value = mock_transaction
        
        repo = FinancialRepository(database=mock_db)
        repo.session = mock_session
        repo.commit = Mock()
        
        # Pass tenant_id explicitly to avoid Flask g dependency
        result = repo.add_transaction(
            date='2025-01-01',
            category='Test Category',
            description='Test',
            type_='Gider',
            amount=100,
            status='Bekliyor',
            tenant_id='test_tenant'
        )
        
        assert result == mock_transaction


@pytest.mark.unit
@pytest.mark.skip(reason="Requires domain.ledger.models.ledger_models.Account")
def test_add_transaction_with_ledger():
    """Test add_transaction with ledger dual-write (status=Ödendi)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transaction = Mock()
    mock_transaction.id = 1
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.return_value = mock_transaction
        
        repo = FinancialRepository(database=mock_db)
        repo.session = mock_session
        repo.commit = Mock()
        
        # Pass tenant_id explicitly to avoid Flask g dependency
        with patch('domain.ledger.models.ledger_models.Account') as mock_account_class:
            mock_cash_acct = Mock()
            mock_cash_acct.id = 1
            mock_target_acct = Mock()
            mock_target_acct.id = 2
            
            mock_account_class.query.filter_by.side_effect = [mock_cash_acct, mock_target_acct]
            
            with patch('repositories.financial_repository.LedgerService') as mock_ledger_service:
                result = repo.add_transaction(
                    date='2025-01-01',
                    category='Test Category',
                    description='Test',
                    type_='Gelir',
                    amount=100,
                    status='Ödendi',
                    tenant_id='test_tenant'
                )
                
                assert result == mock_transaction


@pytest.mark.unit
def test_update_transaction():
    """Test update_transaction method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transaction = Mock()
    mock_transaction.type = 'Gider'
    
    mock_category = Mock()
    mock_category.type = 'Gider'
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.first.return_value = mock_transaction
        
        with patch('repositories.financial_repository.Category') as mock_cat_class:
            mock_cat_class.query.filter_by.return_value.first.return_value = mock_category
            
            repo = FinancialRepository(database=mock_db)
            repo._resolve_tenant_id = Mock(return_value='test_tenant')
            repo.commit = Mock()
            
            result = repo.update_transaction(
                1,
                date='2025-01-01',
                category='Test Category',
                description='Updated',
                amount=200,
                status='Ödendi',
                tenant_id='test_tenant'
            )
            
            assert result == mock_transaction


@pytest.mark.unit
def test_update_transaction_not_found():
    """Test update_transaction when transaction not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.first.return_value = None
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        try:
            repo.update_transaction(1, date='2025-01-01', category='Test', description='Test', amount=100, status='Bekliyor')
            assert False, "Should raise NotFound"
        except NotFound as e:
            assert "bulunamadı" in str(e)


@pytest.mark.unit
def test_update_transaction_invalid_category():
    """Test update_transaction with invalid category"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transaction = Mock()
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.first.return_value = mock_transaction
        
        with patch('repositories.financial_repository.Category') as mock_cat_class:
            mock_cat_class.query.filter_by.return_value.first.return_value = None
            
            repo = FinancialRepository(database=mock_db)
            repo._resolve_tenant_id = Mock(return_value='test_tenant')
            
            try:
                repo.update_transaction(1, date='2025-01-01', category='Invalid', description='Test', amount=100, status='Bekliyor')
                assert False, "Should raise ValueError"
            except ValueError as e:
                assert "Geçersiz Kategori" in str(e)


@pytest.mark.unit
def test_delete_transaction():
    """Test delete_transaction method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transaction = Mock()
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.first.return_value = mock_transaction
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        repo.session = mock_session
        repo.commit = Mock()
        
        repo.delete_transaction(1, tenant_id='test_tenant')
        
        mock_session.delete.assert_called_once_with(mock_transaction)


@pytest.mark.unit
def test_delete_transaction_not_found():
    """Test delete_transaction when transaction not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.first.return_value = None
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        try:
            repo.delete_transaction(1, tenant_id='test_tenant')
            assert False, "Should raise NotFound"
        except NotFound as e:
            assert "bulunamadı" in str(e)


@pytest.mark.unit
@pytest.mark.skip(reason="Complex query chain mocking requires integration test")
def test_pending_transactions_between():
    """Test pending_transactions_between method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.financial_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value.filter.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_transactions
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        result = repo.pending_transactions_between('2025-01-01', '2025-12-31', tenant_id='test_tenant')
        
        assert result == mock_transactions


@pytest.mark.unit
def test_plan_description():
    """Test _plan_description method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = FinancialRepository(database=mock_db)
    mock_plan = Mock()
    mock_plan.name = 'Test Plan'
    mock_plan.installments = 1
    
    result = repo._plan_description(mock_plan, 0)
    
    assert result == 'Test Plan (1/1)'


@pytest.mark.unit
def test_list_recurring_plans():
    """Test list_recurring_plans method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_plans = [Mock()]
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_query = Mock()
        mock_plan_class.query = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = mock_plans
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_recurring_plans(flow_type='Gider', tenant_id='test_tenant')
        
        assert result == mock_plans


@pytest.mark.unit
def test_list_recurring_plans_no_filters():
    """Test list_recurring_plans without filters"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_plans = [Mock()]
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_query = Mock()
        mock_plan_class.query = mock_query
        mock_query.order_by.return_value.all.return_value = mock_plans
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_recurring_plans()
        
        assert result == mock_plans


@pytest.mark.unit
def test_get_recurring_plan_for_tenant():
    """Test get_recurring_plan_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_plan = Mock()
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.query.filter_by.return_value.first.return_value = mock_plan
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.get_recurring_plan_for_tenant(1, 'test_tenant')
        
        assert result == mock_plan


@pytest.mark.unit
def test_list_assets():
    """Test list_assets method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_assets = [Mock()]
    
    with patch('repositories.financial_repository.Asset') as mock_asset_class:
        mock_query = Mock()
        mock_asset_class.query = mock_query
        mock_query.filter_by.return_value.all.return_value = mock_assets
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_assets(tenant_id='test_tenant')
        
        assert result == mock_assets


@pytest.mark.unit
def test_list_assets_no_tenant():
    """Test list_assets without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_assets = [Mock()]
    
    with patch('repositories.financial_repository.Asset') as mock_asset_class:
        mock_asset_class.query.all.return_value = mock_assets
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_assets()
        
        assert result == mock_assets


@pytest.mark.unit
def test_list_assets_by_name():
    """Test list_assets_by_name method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_assets = [Mock()]
    
    with patch('repositories.financial_repository.Asset') as mock_asset_class:
        mock_query = Mock()
        mock_asset_class.query = mock_query
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = mock_assets
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.list_assets_by_name(tenant_id='test_tenant')
        
        assert result == mock_assets


@pytest.mark.unit
def test_asset_page():
    """Test asset_page method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_paginate = Mock()
    
    with patch('repositories.financial_repository.Asset') as mock_asset_class:
        mock_query = Mock()
        mock_asset_class.query.order_by.return_value.filter_by.return_value.paginate.return_value = mock_paginate
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.asset_page(page=1, per_page=20, tenant_id='test_tenant')
        
        assert result == mock_paginate


@pytest.mark.unit
def test_get_asset_for_tenant():
    """Test get_asset_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset = Mock()
    
    with patch('repositories.financial_repository.Asset') as mock_asset_class:
        mock_query = Mock()
        mock_asset_class.query.filter_by.return_value.filter_by.return_value.first.return_value = mock_asset
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.get_asset_for_tenant(1, tenant_id='test_tenant')
        
        assert result == mock_asset


@pytest.mark.unit
def test_get_asset_for_tenant_no_tenant():
    """Test get_asset_for_tenant without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset = Mock()
    
    with patch('repositories.financial_repository.Asset') as mock_asset_class:
        mock_query = Mock()
        mock_asset_class.query.filter_by.return_value.first.return_value = mock_asset
        
        repo = FinancialRepository(database=mock_db)
        
        result = repo.get_asset_for_tenant(1)
        
        assert result == mock_asset


@pytest.mark.unit
def test_add_recurring_plan():
    """Test add_recurring_plan method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_plan = Mock()
    mock_plan.id = 1
    mock_plan.installments = 12
    
    mock_category = Mock()
    mock_category.type = 'Gider'
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.return_value = mock_plan
        
        with patch('repositories.financial_repository.Category') as mock_cat_class:
            mock_cat_class.query.filter_by.return_value.first.return_value = mock_category
            
            repo = FinancialRepository(database=mock_db)
            repo.session = mock_session
            repo.commit = Mock()
            repo._create_transactions_from_plan = Mock()
            
            # Pass tenant_id explicitly to avoid Flask g dependency
            result = repo.add_recurring_plan(
                name='Test Plan',
                category='Test Category',
                amount=100,
                installments=12,
                payment_day=15,
                tenant_id='test_tenant'
            )
            
            assert result == mock_plan


@pytest.mark.unit
def test_add_recurring_plan_invalid_category():
    """Test add_recurring_plan with invalid category"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.financial_repository.Category') as mock_cat_class:
        mock_cat_class.query.filter_by.return_value.first.return_value = None
        
        repo = FinancialRepository(database=mock_db)
        
        try:
            repo.add_recurring_plan(
                name='Test Plan',
                category='Invalid',
                amount=100,
                installments=12,
                payment_day=15,
                tenant_id='test_tenant'
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Geçersiz kategori" in str(e)


@pytest.mark.unit
def test_add_recurring_plan_invalid_category_type():
    """Test add_recurring_plan with invalid category type"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    mock_category = Mock()
    mock_category.type = 'InvalidType'
    
    with patch('repositories.financial_repository.Category') as mock_cat_class:
        mock_cat_class.query.filter_by.return_value.first.return_value = mock_category
        
        repo = FinancialRepository(database=mock_db)
        
        try:
            repo.add_recurring_plan(
                name='Test Plan',
                category='Test Category',
                amount=100,
                installments=12,
                payment_day=15,
                tenant_id='test_tenant'
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "yalnızca gelir, gider veya yatırım" in str(e)


@pytest.mark.unit
def test_add_recurring_plan_installments_limit():
    """Test add_recurring_plan with installments over limit"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    mock_category = Mock()
    mock_category.type = 'Gider'
    
    with patch('repositories.financial_repository.Category') as mock_cat_class:
        mock_cat_class.query.filter_by.return_value.first.return_value = mock_category
        
        repo = FinancialRepository(database=mock_db)
        
        try:
            repo.add_recurring_plan(
                name='Test Plan',
                category='Test Category',
                amount=100,
                installments=601,
                payment_day=15,
                tenant_id='test_tenant'
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "600'ü geçemez" in str(e)


@pytest.mark.unit
def test_update_recurring_plan():
    """Test update_recurring_plan method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_plan = Mock()
    
    mock_category = Mock()
    mock_category.type = 'Gider'
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.query.filter_by.return_value.first.return_value = mock_plan
        
        with patch('repositories.financial_repository.Category') as mock_cat_class:
            mock_cat_class.query.filter_by.return_value.first.return_value = mock_category
            
            repo = FinancialRepository(database=mock_db)
            repo._resolve_tenant_id = Mock(return_value='test_tenant')
            repo.commit = Mock()
            repo._create_transactions_from_plan = Mock()
            
            with patch('repositories.financial_repository.Transaction') as mock_tx_class:
                mock_tx_class.query.filter_by.return_value.delete.return_value = 0
                
                result = repo.update_recurring_plan(
                    1,
                    name='Updated Plan',
                    category='Test Category',
                    amount=200,
                    installments=24,
                    payment_day=20,
                    tenant_id='test_tenant'
                )
                
                assert result == mock_plan


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context for Category.query")
def test_update_recurring_plan_not_found():
    """Test update_recurring_plan when plan not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.query.filter_by.return_value.first.return_value = None
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        try:
            repo.update_recurring_plan(
                1,
                name='Updated Plan',
                category='Test Category',
                amount=200,
                installments=24,
                payment_day=20,
                tenant_id='test_tenant'
            )
            assert False, "Should raise NotFound"
        except NotFound as e:
            assert "bulunamadı" in str(e)


@pytest.mark.unit
def test_delete_plan():
    """Test delete_plan method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_plan = Mock()
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.query.filter_by.return_value.first.return_value = mock_plan
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        repo.session = mock_session
        repo.commit = Mock()
        
        with patch('repositories.financial_repository.Payment') as mock_payment_class:
            mock_payment_class.query.filter_by.return_value.delete.return_value = 0
            
            with patch('repositories.financial_repository.Transaction') as mock_tx_class:
                mock_tx_class.query.filter_by.return_value.all.return_value = []
                
                result = repo.delete_plan(1, tenant_id='test_tenant')
                
                assert result['success'] is True


@pytest.mark.unit
def test_delete_plan_not_found():
    """Test delete_plan when plan not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.query.filter_by.return_value.first.return_value = None
        
        repo = FinancialRepository(database=mock_db)
        repo._resolve_tenant_id = Mock(return_value='test_tenant')
        
        result = repo.delete_plan(1, tenant_id='test_tenant')
        
        assert result is False


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context for RecurringPlan.query")
def test_create_payment():
    """Test create_payment method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_payment = Mock()
    mock_payment.id = 1
    
    mock_plan = Mock()
    mock_plan.tenant_id = 'test_tenant'
    mock_plan.installments = 12
    mock_plan.category = 'Test Category'
    mock_plan.name = 'Test Plan'
    mock_plan.flow_type = 'Gider'
    
    with patch('repositories.financial_repository.Payment') as mock_payment_class:
        mock_payment_class.return_value = mock_payment
        
        repo = FinancialRepository(database=mock_db)
        repo.db = mock_db
        repo.session = mock_session
        repo.commit = Mock()
        
        # Pass tenant_id explicitly to avoid Flask g dependency
        with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
            mock_plan_class.query.filter_by.return_value.first.return_value = mock_plan
            
            with patch('repositories.financial_repository.Transaction') as mock_tx_class:
                mock_tx_class.query.filter_by.return_value.first.return_value = None
                
                with patch.object(repo, 'add_transaction') as mock_add_tx:
                    mock_add_tx.return_value = Mock(id=1)
                    
                    result = repo.create_payment(
                        plan_id=1,
                        amount=100,
                        payment_date='2025-01-01',
                        installment_number=1,
                        tenant_id='test_tenant'
                    )
                    
                    assert result == mock_payment


@pytest.mark.unit
def test_create_payment_invalid_amount():
    """Test create_payment with invalid amount"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = FinancialRepository(database=mock_db)
    
    try:
        repo.create_payment(
            plan_id=1,
            amount=0,
            payment_date='2025-01-01',
            installment_number=1,
            tenant_id='test_tenant'
        )
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "sıfırdan büyük olmalıdır" in str(e)


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context for RecurringPlan.query")
def test_create_payment_existing_payment():
    """Test create_payment when payment already exists"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    mock_plan = Mock()
    mock_plan.tenant_id = 'test_tenant'
    mock_plan.installments = 12
    
    mock_existing_payment = Mock()
    
    with patch('repositories.financial_repository.RecurringPlan') as mock_plan_class:
        mock_plan_class.query.filter_by.return_value.first.return_value = mock_plan
        
        repo = FinancialRepository(database=mock_db)
        repo.db = mock_db
        repo.session = mock_session
        repo.commit = Mock()
        
        with patch('repositories.financial_repository.Payment') as mock_payment_class:
            mock_payment_class.query.filter_by.return_value.first.return_value = mock_existing_payment
            
            try:
                repo.create_payment(
                    plan_id=1,
                    amount=100,
                    payment_date='2025-01-01',
                    installment_number=1,
                    tenant_id='test_tenant'
                )
                assert False, "Should raise ValueError"
            except ValueError as e:
                assert "zaten bir ödeme kaydı mevcut" in str(e)


@pytest.mark.unit
def test_financial_repository_module_has_required_imports():
    """Test financial_repository module has required imports"""
    import repositories.financial_repository as financial_repo_module
    
    # Custom imports
    assert hasattr(financial_repo_module, 'Asset')
    assert hasattr(financial_repo_module, 'Category')
    assert hasattr(financial_repo_module, 'Payment')
    assert hasattr(financial_repo_module, 'RecurringPlan')
    assert hasattr(financial_repo_module, 'Transaction')
    assert hasattr(financial_repo_module, 'BaseRepository')
    assert hasattr(financial_repo_module, 'BaseRepositoryContract')
    assert hasattr(financial_repo_module, 'FinancialRepositoryContract')
