"""
Unit Tests - Reporting Repository
Repository for reporting and analytics queries
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from repositories.reporting_repository import ReportingRepository


@pytest.mark.unit
def test_reporting_repository_init():
    """Test ReportingRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ReportingRepository(database=mock_db)
    
    assert repo.session == mock_session


@pytest.mark.unit
def test_reporting_repository_imports():
    """Test that ReportingRepository can be imported"""
    from repositories.reporting_repository import ReportingRepository
    
    assert ReportingRepository is not None


@pytest.mark.unit
def test_reporting_repository_module_structure():
    """Test reporting_repository module structure"""
    import repositories.reporting_repository as reporting_repo_module
    
    # Check for expected class
    assert hasattr(reporting_repo_module, 'ReportingRepository')
    
    # Check for expected imports
    assert hasattr(reporting_repo_module, 'Asset')
    assert hasattr(reporting_repo_module, 'RecurringPlan')
    assert hasattr(reporting_repo_module, 'Transaction')
    assert hasattr(reporting_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_reporting_repository_extends_base():
    """Test ReportingRepository extends BaseRepository"""
    from repositories.reporting_repository import ReportingRepository
    from repositories.base import BaseRepository
    
    assert issubclass(ReportingRepository, BaseRepository)


@pytest.mark.unit
def test_get_monthly_balance():
    """Test get_monthly_balance method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_rows = [('Gelir', Decimal('1000.00')), ('Gider', Decimal('500.00'))]
        mock_query.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = mock_rows
        
        repo = ReportingRepository(database=mock_db)
        
        income, expense = repo.get_monthly_balance(2025, 1, tenant_id='test_tenant')
        
        assert income == Decimal('1000.00')
        assert expense == Decimal('500.00')


@pytest.mark.unit
def test_get_monthly_balance_no_tenant():
    """Test get_monthly_balance without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_rows = [('Gelir', Decimal('1000.00'))]
        mock_query.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = mock_rows
        
        repo = ReportingRepository(database=mock_db)
        
        income, expense = repo.get_monthly_balance(2025, 1)
        
        assert income == Decimal('1000.00')
        assert expense == Decimal('0.00')


@pytest.mark.unit
def test_get_monthly_balance_empty():
    """Test get_monthly_balance with no data"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = []
        
        repo = ReportingRepository(database=mock_db)
        
        income, expense = repo.get_monthly_balance(2025, 1, tenant_id='test_tenant')
        
        assert income == Decimal('0.00')
        assert expense == Decimal('0.00')


@pytest.mark.unit
def test_get_actual_cash():
    """Test get_actual_cash method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal('5000.00')
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_actual_cash(tenant_id='test_tenant')
        
        assert result == Decimal('5000.00')


@pytest.mark.unit
def test_get_actual_cash_no_tenant():
    """Test get_actual_cash without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = Decimal('3000.00')
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_actual_cash()
        
        assert result == Decimal('3000.00')


@pytest.mark.unit
def test_get_actual_cash_null():
    """Test get_actual_cash when result is None"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = None
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_actual_cash(tenant_id='test_tenant')
        
        assert result == Decimal('0.00')


@pytest.mark.unit
def test_get_total_assets():
    """Test get_total_assets method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = Decimal('100000.00')
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_total_assets(tenant_id='test_tenant')
        
        assert result == Decimal('100000.00')


@pytest.mark.unit
def test_get_total_assets_no_tenant():
    """Test get_total_assets without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.scalar.return_value = Decimal('75000.00')
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_total_assets()
        
        assert result == Decimal('75000.00')


@pytest.mark.unit
def test_get_total_assets_null():
    """Test get_total_assets when result is None"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = None
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_total_assets(tenant_id='test_tenant')
        
        assert result == Decimal('0.00')


@pytest.mark.unit
def test_get_total_debts():
    """Test get_total_debts method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal('25000.00')
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_total_debts(tenant_id='test_tenant')
        
        assert result == Decimal('25000.00')


@pytest.mark.unit
def test_get_total_debts_no_tenant():
    """Test get_total_debts without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = Decimal('15000.00')
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_total_debts()
        
        assert result == Decimal('15000.00')


@pytest.mark.unit
def test_get_total_debts_null():
    """Test get_total_debts when result is None"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = None
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_total_debts(tenant_id='test_tenant')
        
        assert result == Decimal('0.00')


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_transactions_by_date_range():
    """Test get_transactions_by_date_range method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.filter_by.return_value.all.return_value = mock_transactions
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_transactions_by_date_range('2025-01-01', '2025-12-31', tenant_id='test_tenant')
        
        assert result == mock_transactions


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_transactions_by_date_range_no_tenant():
    """Test get_transactions_by_date_range without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.all.return_value = mock_transactions
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_transactions_by_date_range('2025-01-01', '2025-12-31')
        
        assert result == mock_transactions


@pytest.mark.unit
def test_serialize_calendar_tx():
    """Test _serialize_calendar_tx method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ReportingRepository(database=mock_db)
    
    mock_transaction = Mock()
    mock_transaction.id = 1
    mock_transaction.category = 'Test Category'
    mock_transaction.description = 'Test Description'
    mock_transaction.note = 'Test Note'
    mock_transaction.type = 'Gider'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.50
    mock_transaction.origin = 'manual'
    
    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '100,50'
        
        result = repo._serialize_calendar_tx(mock_transaction)
        
        assert result['id'] == 1
        assert result['category'] == 'Test Category'
        assert result['description'] == 'Test Description'
        assert result['note'] == 'Test Note'
        assert result['type'] == 'Gider'
        assert result['status'] == 'Ödendi'
        assert result['amount'] == 100.50
        assert result['amount_fmt'] == '100,50'
        assert result['origin'] == 'manual'


@pytest.mark.unit
def test_serialize_calendar_tx_empty_fields():
    """Test _serialize_calendar_tx with empty fields"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ReportingRepository(database=mock_db)
    
    mock_transaction = Mock()
    mock_transaction.id = 1
    mock_transaction.category = 'Test Category'
    mock_transaction.description = None
    mock_transaction.note = None
    mock_transaction.type = 'Gider'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.50
    mock_transaction.origin = None
    
    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '100,50'
        
        result = repo._serialize_calendar_tx(mock_transaction)
        
        assert result['description'] == ''
        assert result['note'] == ''


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_calendar_month_data():
    """Test get_calendar_month_data method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    mock_transaction1 = Mock()
    mock_transaction1.date = '2025-01-15'
    mock_transaction1.type = 'Gelir'
    mock_transaction1.amount = 1000.00
    mock_transaction1.id = 1
    mock_transaction1.category = 'Salary'
    mock_transaction1.description = 'Monthly Salary'
    mock_transaction1.note = None
    mock_transaction1.status = 'Ödendi'
    mock_transaction1.origin = 'manual'
    
    mock_transaction2 = Mock()
    mock_transaction2.date = '2025-01-15'
    mock_transaction2.type = 'Gider'
    mock_transaction2.amount = 500.00
    mock_transaction2.id = 2
    mock_transaction2.category = 'Rent'
    mock_transaction2.description = 'Monthly Rent'
    mock_transaction2.note = None
    mock_transaction2.status = 'Ödendi'
    mock_transaction2.origin = 'manual'
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.filter.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_transaction1, mock_transaction2]
        
        repo = ReportingRepository(database=mock_db)
        repo._serialize_calendar_tx = Mock(side_effect=lambda t: {
            'id': t.id,
            'category': t.category,
            'description': t.description or '',
            'note': t.note or '',
            'type': t.type,
            'status': t.status,
            'amount': t.amount,
            'amount_fmt': f'{t.amount:.2f}',
            'origin': t.origin,
        })
        
        result = repo.get_calendar_month_data(2025, 1, tenant_id='test_tenant')
        
        assert '2025-01-15' in result
        assert len(result['2025-01-15']['income']) == 1
        assert len(result['2025-01-15']['expense']) == 1
        assert result['2025-01-15']['income_total'] == 1000.00
        assert result['2025-01-15']['expense_total'] == 500.00
        assert result['2025-01-15']['net'] == 500.00


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_calendar_month_data_no_tenant():
    """Test get_calendar_month_data without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_calendar_month_data(2025, 1)
        
        assert result == {}


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_calendar_month_data_investment():
    """Test get_calendar_month_data with investment transactions"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    mock_transaction = Mock()
    mock_transaction.date = '2025-01-15'
    mock_transaction.type = 'Yatırım'
    mock_transaction.amount = 2000.00
    mock_transaction.id = 1
    mock_transaction.category = 'Stocks'
    mock_transaction.description = 'Stock Purchase'
    mock_transaction.note = None
    mock_transaction.status = 'Ödendi'
    mock_transaction.origin = 'manual'
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.filter.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_transaction]
        
        repo = ReportingRepository(database=mock_db)
        repo._serialize_calendar_tx = Mock(side_effect=lambda t: {
            'id': t.id,
            'category': t.category,
            'description': t.description or '',
            'note': t.note or '',
            'type': t.type,
            'status': t.status,
            'amount': t.amount,
            'amount_fmt': f'{t.amount:.2f}',
            'origin': t.origin,
        })
        
        result = repo.get_calendar_month_data(2025, 1, tenant_id='test_tenant')
        
        assert '2025-01-15' in result
        assert len(result['2025-01-15']['investment']) == 1
        assert result['2025-01-15']['investment_total'] == 2000.00
        assert result['2025-01-15']['net'] == -2000.00


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_pending_payments():
    """Test get_pending_payments method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.filter.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_transactions
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_pending_payments('2025-01-01', '2025-12-31', tenant_id='test_tenant')
        
        assert result == mock_transactions


@pytest.mark.unit
@pytest.mark.skip(reason="Complex SQLAlchemy query requires integration test")
def test_get_pending_payments_no_tenant():
    """Test get_pending_payments without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_transactions = [Mock()]
    
    with patch('repositories.reporting_repository.Transaction') as mock_tx_class:
        mock_query = Mock()
        mock_tx_class.query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = mock_transactions
        
        repo = ReportingRepository(database=mock_db)
        
        result = repo.get_pending_payments('2025-01-01', '2025-12-31')
        
        assert result == mock_transactions


@pytest.mark.unit
def test_reporting_repository_module_has_required_imports():
    """Test reporting_repository module has required imports"""
    import repositories.reporting_repository as reporting_repo_module
    
    # Custom imports
    assert hasattr(reporting_repo_module, 'Asset')
    assert hasattr(reporting_repo_module, 'RecurringPlan')
    assert hasattr(reporting_repo_module, 'Transaction')
    assert hasattr(reporting_repo_module, 'BaseRepository')
    assert hasattr(reporting_repo_module, 'ReportingRepositoryContract')
