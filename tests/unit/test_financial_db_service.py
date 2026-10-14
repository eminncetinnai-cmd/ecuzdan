"""
Unit Tests - Financial DB Service
Database service layer for financial data retrieval tests
"""

from unittest.mock import Mock, patch

import pytest

from infrastructure.database.financial_db_service import (
    _resolve_tenant_id,
    get_actual_cash,
    get_total_assets,
    get_total_debts,
)


@pytest.mark.unit
def test_financial_db_service_module_imports():
    """Test financial_db_service module can be imported"""
    from infrastructure.database.financial_db_service import get_actual_cash
    assert get_actual_cash is not None


@pytest.mark.unit
def test_financial_db_service_module_structure():
    """Test financial_db_service module structure"""
    import infrastructure.database.financial_db_service as service_module

    # Check for expected functions
    assert hasattr(service_module, '_resolve_tenant_id')
    assert hasattr(service_module, 'get_actual_cash')
    assert hasattr(service_module, 'get_total_assets')
    assert hasattr(service_module, 'get_total_debts')


@pytest.mark.unit
def test_resolve_tenant_id_explicit():
    """Test _resolve_tenant_id with explicit tenant_id"""
    result = _resolve_tenant_id('test_tenant')
    assert result == 'test_tenant'


@pytest.mark.unit
def test_resolve_tenant_id_none():
    """Test _resolve_tenant_id with None and no context"""
    with patch('infrastructure.database.financial_db_service.has_request_context', return_value=False):
        result = _resolve_tenant_id(None)
        assert result is None


@pytest.mark.unit
def test_resolve_tenant_id_from_context(app):
    """_resolve_tenant_id reads g.tenant_id during a request."""
    from flask import g

    with app.test_request_context('/'):
        g.tenant_id = 'context_tenant'
        assert _resolve_tenant_id() == 'context_tenant'


@pytest.mark.unit
def test_get_actual_cash_with_tenant():
    """Test get_actual_cash with tenant_id"""
    mock_transaction1 = Mock()
    mock_transaction1.type = 'Gelir'
    mock_transaction1.amount = 1000
    mock_transaction1.status = 'Ödendi'

    mock_transaction2 = Mock()
    mock_transaction2.type = 'Gider'
    mock_transaction2.amount = 500
    mock_transaction2.status = 'Ödendi'

    mock_transaction3 = Mock()
    mock_transaction3.type = 'Gelir'
    mock_transaction3.amount = 200
    mock_transaction3.status = 'Bekliyor'  # Should be ignored

    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = [mock_transaction1, mock_transaction2, mock_transaction3]

    with patch('infrastructure.database.financial_db_service.Transaction') as mock_transaction_model:
        mock_transaction_model.query = mock_query

        result = get_actual_cash(tenant_id='test_tenant')

        assert result == 500  # 1000 - 500
        mock_query.filter_by.assert_called_once_with(tenant_id='test_tenant')


@pytest.mark.unit
def test_get_actual_cash_no_tenant():
    """Test get_actual_cash without tenant_id"""
    mock_transaction1 = Mock()
    mock_transaction1.type = 'Gelir'
    mock_transaction1.amount = 1000
    mock_transaction1.status = 'Ödendi'

    mock_transaction2 = Mock()
    mock_transaction2.type = 'Gider'
    mock_transaction2.amount = 300
    mock_transaction2.status = 'Ödendi'

    mock_query = Mock()
    mock_query.all.return_value = [mock_transaction1, mock_transaction2]

    with patch('infrastructure.database.financial_db_service.Transaction') as mock_transaction_model:
        with patch('infrastructure.database.financial_db_service.has_request_context', return_value=False):
            mock_transaction_model.query = mock_query

            result = get_actual_cash()

            assert result == 700  # 1000 - 300
            mock_query.filter_by.assert_not_called()


@pytest.mark.unit
def test_get_actual_cash_empty_transactions():
    """Test get_actual_cash with no transactions"""
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = []

    with patch('infrastructure.database.financial_db_service.Transaction') as mock_transaction_model:
        mock_transaction_model.query = mock_query

        result = get_actual_cash(tenant_id='test_tenant')

        assert result == 0


@pytest.mark.unit
def test_get_actual_cash_all_expenses():
    """Test get_actual_cash with only expenses"""
    mock_transaction = Mock()
    mock_transaction.type = 'Gider'
    mock_transaction.amount = 500
    mock_transaction.status = 'Ödendi'

    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = [mock_transaction]

    with patch('infrastructure.database.financial_db_service.Transaction') as mock_transaction_model:
        mock_transaction_model.query = mock_query

        result = get_actual_cash(tenant_id='test_tenant')

        assert result == -500


@pytest.mark.unit
def test_get_total_assets_with_tenant():
    """Test get_total_assets with tenant_id"""
    mock_asset1 = Mock()
    mock_asset1.value = 10000

    mock_asset2 = Mock()
    mock_asset2.value = 5000

    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = [mock_asset1, mock_asset2]

    with patch('infrastructure.database.financial_db_service.Asset') as mock_asset_model:
        mock_asset_model.query = mock_query

        result = get_total_assets(tenant_id='test_tenant')

        assert result == 15000
        mock_query.filter_by.assert_called_once_with(tenant_id='test_tenant')


@pytest.mark.unit
def test_get_total_assets_no_tenant():
    """Test get_total_assets without tenant_id"""
    mock_asset = Mock()
    mock_asset.value = 10000

    mock_query = Mock()
    mock_query.all.return_value = [mock_asset]

    with patch('infrastructure.database.financial_db_service.Asset') as mock_asset_model:
        with patch('infrastructure.database.financial_db_service.has_request_context', return_value=False):
            mock_asset_model.query = mock_query

            result = get_total_assets()

            assert result == 10000
            mock_query.filter_by.assert_not_called()


@pytest.mark.unit
def test_get_total_assets_empty():
    """Test get_total_assets with no assets"""
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = []

    with patch('infrastructure.database.financial_db_service.Asset') as mock_asset_model:
        mock_asset_model.query = mock_query

        result = get_total_assets(tenant_id='test_tenant')

        assert result == 0


@pytest.mark.unit
def test_get_total_debts_with_tenant():
    """Test get_total_debts with tenant_id"""
    mock_plan1 = Mock()
    mock_plan1.amount = 1000
    mock_plan1.installments = 12

    mock_plan2 = Mock()
    mock_plan2.amount = 500
    mock_plan2.installments = 6

    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = [mock_plan1, mock_plan2]

    with patch('infrastructure.database.financial_db_service.RecurringPlan') as mock_plan_model:
        mock_plan_model.query.filter_by.return_value = mock_query

        result = get_total_debts(tenant_id='test_tenant')

        assert result == 15000  # (1000 * 12) + (500 * 6)
        mock_plan_model.query.filter_by.assert_any_call(flow_type='Gider')
        mock_query.filter_by.assert_called_with(tenant_id='test_tenant')


@pytest.mark.unit
def test_get_total_debts_no_tenant():
    """Test get_total_debts without tenant_id"""
    mock_plan = Mock()
    mock_plan.amount = 1000
    mock_plan.installments = 12

    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = [mock_plan]

    with patch('infrastructure.database.financial_db_service.RecurringPlan') as mock_plan_model:
        with patch('infrastructure.database.financial_db_service.has_request_context', return_value=False):
            mock_plan_model.query.filter_by.return_value = mock_query

            result = get_total_debts()

            assert result == 12000
            # filter_by is called once for flow_type='Gider'
            mock_plan_model.query.filter_by.assert_called_once_with(flow_type='Gider')


@pytest.mark.unit
def test_get_total_debts_empty():
    """Test get_total_debts with no plans"""
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = []

    with patch('infrastructure.database.financial_db_service.RecurringPlan') as mock_plan_model:
        mock_plan_model.query.filter_by.return_value = mock_query

        result = get_total_debts(tenant_id='test_tenant')

        assert result == 0


@pytest.mark.unit
def test_get_total_debts_filters_expenses():
    """Test get_total_debts filters by flow_type='Gider'"""
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.all.return_value = []

    with patch('infrastructure.database.financial_db_service.RecurringPlan') as mock_plan_model:
        mock_plan_model.query.filter_by.return_value = mock_query

        get_total_debts(tenant_id='test_tenant')

        mock_plan_model.query.filter_by.assert_called_once_with(flow_type='Gider')


@pytest.mark.unit
def test_financial_db_service_module_has_logging():
    """Test financial_db_service module has logging configured"""
    import infrastructure.database.financial_db_service as service_module
    assert hasattr(service_module, 'logger')
