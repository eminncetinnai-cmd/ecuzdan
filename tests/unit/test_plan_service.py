"""
Unit Tests - Plan Service
Plan and payment calendar service tests
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


@pytest.mark.unit
def test_plan_service_payment_calendar_context():
    """Test payment_calendar_context returns correct data"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    # Mock transactions
    mock_tx1 = Mock()
    mock_tx1.type = 'Gelir'
    mock_tx1.amount = 5000
    mock_tx1.status = 'Ödendi'
    
    mock_tx2 = Mock()
    mock_tx2.type = 'Gider'
    mock_tx2.amount = 1000
    mock_tx2.status = 'Ödendi'
    
    mock_financial_repo.list_transactions.return_value = [mock_tx1, mock_tx2]
    mock_financial_repo.pending_transactions_between.return_value = []
    
    result = service.payment_calendar_context()
    
    assert result['today_cash'] == 4000  # 5000 - 1000
    assert 'week_p' in result
    assert 'month_p' in result
    assert 'cal_year' in result
    assert 'cal_month' in result
    assert 'cal_month_name' in result
    assert 'today_iso' in result


@pytest.mark.unit
def test_plan_service_month_data():
    """Test month_data returns correct calendar data"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    with patch('domain.planning.services.plan_service.get_calendar_month_data') as mock_get_data:
        mock_get_data.return_value = {'days': [1, 2, 3]}
        
        result = service.month_data(2024, 8)
        
        assert result['year'] == 2024
        assert result['month'] == 8
        assert result['month_name'] == 'Ağustos'
        assert 'today' in result
        assert 'days' in result


@pytest.mark.unit
def test_plan_service_daily_balance():
    """Test daily_balance returns correct balance data"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    mock_financial_repo.list_transactions.return_value = []
    
    with patch('domain.planning.services.plan_service.calculate_monthly_daily_balance') as mock_calc:
        mock_calc.return_value = ([datetime(2024, 8, 1), datetime(2024, 8, 2)], [1000, 2000])
        
        with patch('domain.planning.services.plan_service.format_date') as mock_format:
            mock_format.side_effect = lambda d: d.strftime('%Y-%m-%d')
            
            result = service.daily_balance(2024, 8)
            
            assert result['year'] == 2024
            assert result['month'] == 8
            assert 'labels' in result
            assert 'data' in result


@pytest.mark.unit
def test_plan_service_add_payment_plan_not_found():
    """Test add_payment raises LookupError when plan not found"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    mock_financial_repo.get_recurring_plan_for_tenant.return_value = None
    
    mock_dto = Mock()
    mock_dto.plan_id = 999
    mock_dto.amount = 1000
    mock_dto.payment_date = '2024-01-01'
    mock_dto.installment_number = 1
    mock_dto.notes = 'Test'
    
    with pytest.raises(LookupError) as exc_info:
        service.add_payment(mock_dto, 'tenant_123')
    
    assert "Plan bulunamadı." in str(exc_info.value)


@pytest.mark.unit
def test_plan_service_add_payment_invalid_installment():
    """Test add_payment raises ValueError for invalid installment number"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    mock_plan = Mock()
    mock_plan.installments = 12
    mock_plan.plan_type = 'Taksit'
    mock_plan.target_asset_id = None
    
    mock_financial_repo.get_recurring_plan_for_tenant.return_value = mock_plan
    
    mock_dto = Mock()
    mock_dto.plan_id = 123
    mock_dto.amount = 1000
    mock_dto.payment_date = '2024-01-01'
    mock_dto.installment_number = 15  # Invalid: > 12
    mock_dto.notes = 'Test'
    
    with pytest.raises(ValueError) as exc_info:
        service.add_payment(mock_dto, 'tenant_123')
    
    assert "Taksit numarası" in str(exc_info.value)


@pytest.mark.unit
def test_plan_service_add_payment_dca_plan():
    """Test add_payment handles DCA plan with asset transfer"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    mock_plan = Mock()
    mock_plan.installments = 0
    mock_plan.plan_type = 'DCA'
    mock_plan.target_asset_id = 'asset_123'
    
    mock_financial_repo.get_recurring_plan_for_tenant.return_value = mock_plan
    
    mock_dto = Mock()
    mock_dto.plan_id = 123
    mock_dto.amount = 1000
    mock_dto.payment_date = '2024-01-01'
    mock_dto.installment_number = 1
    mock_dto.notes = 'Test'
    
    with patch('domain.transactions.services.financial_ledger.transfer_cash_to_asset') as mock_transfer:
        with patch('domain.planning.services.plan_service.create_payment') as mock_create:
            mock_create.return_value = None
            
            service.add_payment(mock_dto, 'tenant_123')
            
            mock_transfer.assert_called_once()
            mock_create.assert_called_once()


@pytest.mark.unit
def test_plan_service_plans_context():
    """Test plans_context returns correct plan data"""
    from domain.planning.services.plan_service import PlanService
    
    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)
    
    # Mock plans
    mock_income_plan = Mock()
    mock_income_plan.plan_type = 'Dönemsel'
    mock_income_plan.amount = 5000
    
    mock_expense_plan = Mock()
    mock_expense_plan.plan_type = 'Abonelik'
    mock_expense_plan.amount = 1000
    
    mock_investment_plan = Mock()
    mock_investment_plan.plan_type = 'DCA'
    mock_investment_plan.amount = 2000
    
    mock_financial_repo.list_recurring_plans.side_effect = [
        [mock_income_plan],  # Gelir
        [mock_expense_plan],  # Gider
        [mock_investment_plan],  # Yatırım
    ]
    
    mock_catalog_repo.list_categories_by_type.return_value = []
    
    result = service.plans_context('tenant_123')
    
    assert result['income_total'] == 5000
    assert result['expense_total'] == 1000
    assert result['dca_total'] == 2000
    assert result['net_total'] == 4000
    assert result['plan_count'] == 3
    assert 'subscription_plans' in result
    assert 'installment_plans' in result
    assert 'dca_plans' in result
    assert 'periodic_plans' in result
