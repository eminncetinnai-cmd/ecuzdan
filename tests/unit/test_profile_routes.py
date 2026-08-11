"""
Unit Tests - Profile Routes
Investor profile route functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from routes.profile import (
    _get_profile_service,
    register_profile_routes,
)


@pytest.mark.unit
def test_get_profile_service():
    """Test _get_profile_service function"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_profile = Mock()
        mock_applications.profile.return_value = mock_profile
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container
        
        result = _get_profile_service()
        assert result == mock_profile


@pytest.mark.unit
def test_register_profile_routes():
    """Test register_profile_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.profile._get_profile_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_profile_routes(mock_bp)
        
        assert mock_bp.route.called


@pytest.mark.unit
def test_profile_imports():
    """Test that profile functions can be imported"""
    from routes.profile import (
        _get_profile_service,
        register_profile_routes,
    )
    
    assert callable(_get_profile_service)
    assert callable(register_profile_routes)


@pytest.mark.unit
def test_profile_routes_structure():
    """Test profile routes module structure"""
    import routes.profile as profile_module
    
    # Check for expected functions
    assert hasattr(profile_module, '_get_profile_service')
    assert hasattr(profile_module, 'register_profile_routes')
    
    # Check for expected imports
    assert hasattr(profile_module, 'logging')
    assert hasattr(profile_module, 'g')
    assert hasattr(profile_module, 'jsonify')
    assert hasattr(profile_module, 'redirect')
    assert hasattr(profile_module, 'render_template')
    assert hasattr(profile_module, 'request')
    assert hasattr(profile_module, 'session')
    assert hasattr(profile_module, 'url_for')


@pytest.mark.unit
def test_profile_logger_exists():
    """Test profile module has logger"""
    import routes.profile as profile_module
    assert hasattr(profile_module, 'logger')
    assert profile_module.logger is not None


@pytest.mark.unit
def test_get_profile_service_container_call():
    """Test _get_profile_service calls get_container"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_profile = Mock()
        mock_applications.profile.return_value = mock_profile
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container
        
        _get_profile_service()
        
        mock_get_container.assert_called_once()
        mock_container.applications.profile.assert_called_once()


@pytest.mark.unit
def test_register_profile_routes_route_registration():
    """Test register_profile_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.profile._get_profile_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_profile_routes(mock_bp)
        
        # Should register multiple routes
        assert mock_bp.route.call_count >= 7


@pytest.mark.unit
def test_profile_module_has_required_imports():
    """Test profile module has required imports"""
    import routes.profile as profile_module
    
    # Flask imports
    assert hasattr(profile_module, 'g')
    assert hasattr(profile_module, 'jsonify')
    assert hasattr(profile_module, 'redirect')
    assert hasattr(profile_module, 'render_template')
    assert hasattr(profile_module, 'request')
    assert hasattr(profile_module, 'session')
    assert hasattr(profile_module, 'url_for')
    
    # Custom imports
    assert hasattr(profile_module, 'get_container')
    assert hasattr(profile_module, 'get_tenant_id')
    assert hasattr(profile_module, 'handle_ajax_or_flash')
    assert hasattr(profile_module, 'is_ajax_request')
    assert hasattr(profile_module, 'flash_error')


@pytest.mark.unit
def test_register_profile_routes_service_call():
    """Test register_profile_routes calls _get_profile_service"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.profile._get_profile_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_profile_routes(mock_bp)
        
        mock_get_service.assert_called_once()


@pytest.mark.unit
def test_profile_blueprint_parameter():
    """Test register_profile_routes accepts blueprint parameter"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.profile._get_profile_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Should not raise exception
        register_profile_routes(mock_bp)


@pytest.mark.unit
def test_profile_index_route_exists():
    """Test profile index route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/' in source and 'index' in source


@pytest.mark.unit
def test_profile_start_route_exists():
    """Test profile start route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/start' in source


@pytest.mark.unit
def test_profile_submit_route_exists():
    """Test profile submit route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/submit' in source


@pytest.mark.unit
def test_profile_result_route_exists():
    """Test profile result route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/result' in source


@pytest.mark.unit
def test_profile_api_questions_route_exists():
    """Test profile API questions route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/api/questions' in source


@pytest.mark.unit
def test_profile_api_submit_route_exists():
    """Test profile API submit route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/api/submit' in source


@pytest.mark.unit
def test_profile_api_profile_route_exists():
    """Test profile API profile route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/api/profile' in source


@pytest.mark.unit
def test_profile_api_history_route_exists():
    """Test profile API history route exists"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert '/api/history' in source


@pytest.mark.unit
def test_profile_error_handling_structure():
    """Test profile routes have error handling"""
    import routes.profile as profile_module
    import inspect
    
    # Check that the module has error handling patterns
    source = inspect.getsource(profile_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_profile_ajax_handling():
    """Test profile routes use AJAX helpers"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert 'is_ajax_request' in source or 'handle_ajax_or_flash' in source


@pytest.mark.unit
def test_profile_json_responses():
    """Test profile routes use jsonify"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert 'jsonify' in source


@pytest.mark.unit
def test_profile_tenant_context():
    """Test profile routes use tenant context"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert 'get_tenant_id' in source or 'tenant_id' in source


@pytest.mark.unit
def test_profile_service_methods():
    """Test profile service methods are called"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    # Check for service method calls
    assert 'profile_service' in source


@pytest.mark.unit
def test_profile_session_usage():
    """Test profile routes use session"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert 'session' in source


@pytest.mark.unit
def test_profile_flash_messaging():
    """Test profile routes use flash messaging"""
    import routes.profile as profile_module
    import inspect
    
    source = inspect.getsource(profile_module)
    assert 'flash_error' in source
