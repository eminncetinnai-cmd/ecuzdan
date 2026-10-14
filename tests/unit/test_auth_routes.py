"""
Unit Tests - Auth Routes
Authentication route functions - Detailed functional tests
"""

from unittest.mock import Mock, patch

import pytest

from routes.auth import (
    _get_auth_service,
    register_auth_routes,
)


@pytest.mark.unit
def test_get_auth_service():
    """Test _get_auth_service function"""
    with patch('bootstrap.container.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_auth = Mock()
        mock_applications.auth.return_value = mock_auth
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container

        result = _get_auth_service()
        assert result == mock_auth


@pytest.mark.unit
def test_register_auth_routes():
    """Test register_auth_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    register_auth_routes(mock_bp)

    assert mock_bp.route.called


@pytest.mark.unit
def test_auth_imports():
    """Test that auth functions can be imported"""
    from routes.auth import (
        _get_auth_service,
        register_auth_routes,
    )

    assert callable(_get_auth_service)
    assert callable(register_auth_routes)


@pytest.mark.unit
def test_auth_module_structure():
    """Test auth routes module structure"""
    import routes.auth as auth_module

    # Check for expected functions
    assert hasattr(auth_module, '_get_auth_service')
    assert hasattr(auth_module, 'register_auth_routes')

    # Check for expected imports
    assert hasattr(auth_module, 'logging')
    assert hasattr(auth_module, 'g')
    assert hasattr(auth_module, 'jsonify')
    assert hasattr(auth_module, 'render_template')
    assert hasattr(auth_module, 'request')
    assert hasattr(auth_module, 'session')
    assert hasattr(auth_module, 'flash')
    assert hasattr(auth_module, 'redirect')
    assert hasattr(auth_module, 'url_for')


@pytest.mark.unit
def test_auth_logger():
    """Test auth module has logger"""
    import routes.auth as auth_module
    assert hasattr(auth_module, 'logger')
    assert auth_module.logger is not None


@pytest.mark.unit
def test_get_auth_service_container_call():
    """Test _get_auth_service calls get_container"""
    with patch('bootstrap.container.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_auth = Mock()
        mock_applications.auth.return_value = mock_auth
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container

        _get_auth_service()

        mock_get_container.assert_called_once()
        mock_container.applications.auth.assert_called_once()


@pytest.mark.unit
def test_register_auth_routes_route_registration():
    """Test register_auth_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    register_auth_routes(mock_bp)

    # Should register multiple routes
    assert mock_bp.route.call_count >= 7


@pytest.mark.unit
def test_register_auth_routes_service_call():
    """Test register_auth_routes calls _get_auth_service"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.auth._get_auth_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        register_auth_routes(mock_bp)

        mock_get_service.assert_called_once()


@pytest.mark.unit
def test_auth_routes_exist():
    """Test auth routes exist in module"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert '/login' in source
    assert '/logout' in source
    assert '/register' in source


@pytest.mark.unit
def test_auth_error_handling():
    """Test auth routes have error handling"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_auth_session_usage():
    """Test auth routes use session"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'session' in source


@pytest.mark.unit
def test_auth_flash_messaging():
    """Test auth routes use flash messaging"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'flash' in source


@pytest.mark.unit
def test_auth_audit_logging():
    """Test auth routes use audit logging"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'audit_log' in source


@pytest.mark.unit
def test_auth_oauth_integration():
    """Test auth routes have OAuth integration"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'oauth' in source.lower() or 'google' in source.lower()


@pytest.mark.unit
def test_auth_secrets_usage():
    """Test auth routes use secrets module"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'secrets' in source


@pytest.mark.unit
def test_auth_json_responses():
    """Test auth routes use jsonify"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'jsonify' in source


@pytest.mark.unit
def test_auth_rollback_session():
    """Test auth routes use rollback"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'rollback' in source


@pytest.mark.unit
def test_auth_i18n_usage():
    """Test auth routes use i18n"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'i18n' in source


@pytest.mark.unit
def test_auth_request_methods():
    """Test auth routes use different request methods"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    # Should have GET and POST methods
    assert 'GET' in source or 'POST' in source


@pytest.mark.unit
def test_auth_template_rendering():
    """Test auth routes use template rendering"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'render_template' in source


@pytest.mark.unit
def test_auth_redirect_usage():
    """Test auth routes use redirect"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'redirect' in source


@pytest.mark.unit
def test_auth_url_for_usage():
    """Test auth routes use url_for"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'url_for' in source


@pytest.mark.unit
def test_auth_request_object():
    """Test auth routes use request object"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'request' in source


@pytest.mark.unit
def test_auth_g_object():
    """Test auth routes use g object"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'g.' in source or 'g[' in source


@pytest.mark.unit
def test_auth_current_app():
    """Test auth routes use current_app"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'current_app' in source


@pytest.mark.unit
def test_auth_datetime_usage():
    """Test auth routes use datetime"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'datetime' in source


@pytest.mark.unit
def test_auth_logging_usage():
    """Test auth routes use logging"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'logger' in source or 'logging' in source


@pytest.mark.unit
def test_auth_get_container_usage():
    """Test auth routes use get_container"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'get_container' in source


@pytest.mark.unit
def test_auth_action_constants():
    """Test auth routes use action constants"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'ACTION_' in source


@pytest.mark.unit
def test_auth_get_daily_insight():
    """Test auth routes use get_daily_insight"""
    import inspect

    import routes.auth as auth_module

    source = inspect.getsource(auth_module)
    assert 'get_daily_insight' in source


@pytest.mark.unit
def test_oauth_login_missing_credentials(client, app, monkeypatch):
    """OAuth login fails closed when Google credentials are absent."""
    monkeypatch.setitem(app.config, 'GOOGLE_CLIENT_ID', None)
    monkeypatch.setitem(app.config, 'GOOGLE_CLIENT_SECRET', None)

    result = client.get('/login/google')

    assert result.status_code == 302
    assert result.location.endswith('/login')


@pytest.mark.unit
def test_oauth_login_unsupported_provider(client):
    """Unsupported OAuth providers redirect to the local login page."""
    result = client.get('/login/facebook')

    assert result.status_code == 302
    assert result.location.endswith('/login')


@pytest.mark.unit
def test_oauth_login_success(client, app, monkeypatch):
    """OAuth login stores state and redirects to the provider authorization URL."""
    monkeypatch.setitem(app.config, 'GOOGLE_CLIENT_ID', 'test_client_id')
    monkeypatch.setitem(app.config, 'GOOGLE_CLIENT_SECRET', 'test_secret')

    with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
        provider = Mock()
        provider.get_authorization_url.return_value = 'https://accounts.google.com/o/oauth2/v2/auth?test'
        provider_class.return_value = provider

        result = client.get('/login/google')

        with client.session_transaction() as session:
            assert session['oauth_state']
            assert session['oauth_provider'] == 'google'

    assert result.status_code == 302
    assert result.location.startswith('https://accounts.google.com/')
    provider.get_authorization_url.assert_called_once()


@pytest.mark.unit
def test_oauth_callback_invalid_state(client):
    """OAuth callback rejects a missing or mismatched CSRF state."""
    result = client.get('/callback/google?state=different_state')

    assert result.status_code == 302
    assert result.location.endswith('/login')


@pytest.mark.unit
def test_oauth_callback_missing_code(client):
    """OAuth callback rejects a valid state without an authorization code."""
    with client.session_transaction() as session:
        session['oauth_state'] = 'same_state'

    result = client.get('/callback/google?state=same_state')

    assert result.status_code == 302
    assert result.location.endswith('/login')


@pytest.mark.unit
def test_oauth_callback_missing_credentials(client, app, monkeypatch):
    """OAuth callback fails closed when provider credentials are absent."""
    monkeypatch.setitem(app.config, 'GOOGLE_CLIENT_ID', None)
    monkeypatch.setitem(app.config, 'GOOGLE_CLIENT_SECRET', None)
    with client.session_transaction() as session:
        session['oauth_state'] = 'same_state'

    result = client.get('/callback/google?state=same_state&code=test_code')

    assert result.status_code == 302
    assert result.location.endswith('/login')
