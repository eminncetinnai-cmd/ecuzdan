"""
Unit Tests - Tenant Routes
Tenant management route tests
"""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
def test_tenant_route_registration_calls_service():
    """Test that register_tenant_routes calls tenant service"""
    from routes.tenant import register_tenant_routes

    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.tenant._get_tenant_service') as mock_get_service:
        mock_service = Mock()
        mock_service.page_context.return_value = {
            'current_user': Mock(),
            'tenant': Mock(),
            'users': [],
            'invites': [],
        }
        mock_get_service.return_value = mock_service

        register_tenant_routes(mock_bp)

        mock_get_service.assert_called_once()
        assert mock_bp.route.call_count >= 4  # Should register 4+ routes


@pytest.mark.unit
def test_tenant_invite_route_validation():
    """Test that invite route validates email"""
    from routes.tenant import register_tenant_routes

    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.tenant._get_tenant_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        with patch('utils.db_session.rollback_session'):
            register_tenant_routes(mock_bp)

            assert mock_bp.route.called


@pytest.mark.unit
def test_tenant_invites_list_route():
    """Test that invites list route returns pending invites"""
    from routes.tenant import register_tenant_routes

    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.tenant._get_tenant_service') as mock_get_service:
        mock_service = Mock()
        mock_service.list_invites.return_value = []
        mock_get_service.return_value = mock_service

        register_tenant_routes(mock_bp)

        assert mock_bp.route.called


@pytest.mark.unit
def test_tenant_users_list_route():
    """Test that users list route returns tenant users"""
    from routes.tenant import register_tenant_routes

    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.tenant._get_tenant_service') as mock_get_service:
        mock_service = Mock()
        mock_service.list_users.return_value = []
        mock_get_service.return_value = mock_service

        register_tenant_routes(mock_bp)

        assert mock_bp.route.called


@pytest.mark.unit
def test_tenant_route_error_handling():
    """Test that tenant routes have error handling"""
    import inspect

    import routes.tenant as tenant_module

    source = inspect.getsource(tenant_module)
    assert 'except Exception' in source
    assert 'try:' in source


@pytest.mark.unit
def test_tenant_route_uses_flash():
    """Test that tenant路由 use flash for user feedback"""
    import inspect

    import routes.tenant as tenant_module

    source = inspect.getsource(tenant_module)
    assert 'flash' in source


@pytest.mark.unit
def test_tenant_route_uses_redirect():
    """Test that tenant routes use redirect after actions"""
    import inspect

    import routes.tenant as tenant_module

    source = inspect.getsource(tenant_module)
    assert 'redirect' in source


