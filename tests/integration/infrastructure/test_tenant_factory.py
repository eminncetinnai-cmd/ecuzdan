"""
Unit Tests - Tenant Factory
Tenant-aware model factory tests
"""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
def test_tenant_factory_module_imports():
    """Test tenant_factory module can be imported"""
    from utils.tenant_factory import _resolve_tenant_id, new_asset, new_recurring_plan, new_transaction
    assert new_transaction is not None
    assert new_asset is not None
    assert new_recurring_plan is not None
    assert _resolve_tenant_id is not None


@pytest.mark.unit
def test_tenant_factory_module_structure():
    """Test tenant_factory module structure"""
    import utils.tenant_factory as tenant_factory_module

    # Check for expected functions
    assert hasattr(tenant_factory_module, '_resolve_tenant_id')
    assert hasattr(tenant_factory_module, 'new_transaction')
    assert hasattr(tenant_factory_module, 'new_asset')
    assert hasattr(tenant_factory_module, 'new_recurring_plan')

    # Check for expected imports
    assert hasattr(tenant_factory_module, 'Asset')
    assert hasattr(tenant_factory_module, 'RecurringPlan')
    assert hasattr(tenant_factory_module, 'Transaction')


@pytest.mark.unit
def test_resolve_tenant_id_explicit():
    """Test _resolve_tenant_id with explicit tenant_id"""
    from utils.tenant_factory import _resolve_tenant_id

    result = _resolve_tenant_id(explicit_tenant_id='test_tenant')
    assert result == 'test_tenant'


@pytest.mark.unit
def test_resolve_tenant_id_from_context(app):
    """Test _resolve_tenant_id from the active tenant context."""
    from domain.tenant.context import TenantContext
    from utils.tenant_factory import _resolve_tenant_id

    with app.test_request_context('/'):
        TenantContext.set('context_tenant')
        try:
            assert _resolve_tenant_id() == 'context_tenant'
        finally:
            TenantContext.set(None)


@pytest.mark.unit
def test_resolve_tenant_id_no_tenant():
    """Test _resolve_tenant_id raises error when no tenant_id"""
    from utils.tenant_factory import _resolve_tenant_id

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = None

        try:
            _resolve_tenant_id()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "tenant_id belirlenemedi" in str(e)


@pytest.mark.unit
def test_resolve_tenant_id_context_fallback():
    """Test _resolve_tenant_id falls back to context when no explicit tenant_id"""
    from utils.tenant_factory import _resolve_tenant_id

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = 'context_tenant'

        result = _resolve_tenant_id()
        assert result == 'context_tenant'


@pytest.mark.unit
def test_new_transaction_with_explicit_tenant():
    """Test new_transaction with explicit tenant_id"""
    from utils.tenant_factory import new_transaction

    with patch('utils.tenant_factory.Transaction') as mock_tx_class:
        mock_tx = Mock()
        mock_tx_class.return_value = mock_tx

        result = new_transaction(tenant_id='test_tenant', amount=100)

        assert result == mock_tx
        mock_tx_class.assert_called_once_with(tenant_id='test_tenant', amount=100)


@pytest.mark.unit
def test_new_transaction_with_context_tenant():
    """Test new_transaction with context tenant"""
    from utils.tenant_factory import new_transaction

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = 'context_tenant'

        with patch('utils.tenant_factory.Transaction') as mock_tx_class:
            mock_tx = Mock()
            mock_tx_class.return_value = mock_tx

            result = new_transaction(amount=100)

            assert result == mock_tx
            mock_tx_class.assert_called_once_with(tenant_id='context_tenant', amount=100)


@pytest.mark.unit
def test_new_transaction_no_tenant():
    """Test new_transaction raises error when no tenant_id"""
    from utils.tenant_factory import new_transaction

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = None

        try:
            new_transaction(amount=100)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "tenant_id belirlenemedi" in str(e)


@pytest.mark.unit
def test_new_asset_with_explicit_tenant():
    """Test new_asset with explicit tenant_id"""
    from utils.tenant_factory import new_asset

    with patch('utils.tenant_factory.Asset') as mock_asset_class:
        mock_asset = Mock()
        mock_asset_class.return_value = mock_asset

        result = new_asset(tenant_id='test_tenant', name='Test Asset')

        assert result == mock_asset
        mock_asset_class.assert_called_once_with(tenant_id='test_tenant', name='Test Asset')


@pytest.mark.unit
def test_new_asset_with_context_tenant():
    """Test new_asset with context tenant"""
    from utils.tenant_factory import new_asset

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = 'context_tenant'

        with patch('utils.tenant_factory.Asset') as mock_asset_class:
            mock_asset = Mock()
            mock_asset_class.return_value = mock_asset

            result = new_asset(name='Test Asset')

            assert result == mock_asset
            mock_asset_class.assert_called_once_with(tenant_id='context_tenant', name='Test Asset')


@pytest.mark.unit
def test_new_asset_no_tenant():
    """Test new_asset raises error when no tenant_id"""
    from utils.tenant_factory import new_asset

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = None

        try:
            new_asset(name='Test Asset')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "tenant_id belirlenemedi" in str(e)


@pytest.mark.unit
def test_new_recurring_plan_with_explicit_tenant():
    """Test new_recurring_plan with explicit tenant_id"""
    from utils.tenant_factory import new_recurring_plan

    with patch('utils.tenant_factory.RecurringPlan') as mock_plan_class:
        mock_plan = Mock()
        mock_plan_class.return_value = mock_plan

        result = new_recurring_plan(tenant_id='test_tenant', name='Test Plan')

        assert result == mock_plan
        mock_plan_class.assert_called_once_with(tenant_id='test_tenant', name='Test Plan')


@pytest.mark.unit
def test_new_recurring_plan_with_context_tenant():
    """Test new_recurring_plan with context tenant"""
    from utils.tenant_factory import new_recurring_plan

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = 'context_tenant'

        with patch('utils.tenant_factory.RecurringPlan') as mock_plan_class:
            mock_plan = Mock()
            mock_plan_class.return_value = mock_plan

            result = new_recurring_plan(name='Test Plan')

            assert result == mock_plan
            mock_plan_class.assert_called_once_with(tenant_id='context_tenant', name='Test Plan')


@pytest.mark.unit
def test_new_recurring_plan_no_tenant():
    """Test new_recurring_plan raises error when no tenant_id"""
    from utils.tenant_factory import new_recurring_plan

    with patch('utils.tenant_factory._get_tenant_from_context') as mock_get_tenant:
        mock_get_tenant.return_value = None

        try:
            new_recurring_plan(name='Test Plan')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "tenant_id belirlenemedi" in str(e)
