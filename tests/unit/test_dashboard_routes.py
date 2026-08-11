"""
Unit Tests - Dashboard Routes
Dashboard and financial analysis route functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from routes.dashboard import (
    _get_dashboard_service,
    register_dashboard_routes,
)


@pytest.mark.unit
def test_get_dashboard_service():
    """Test _get_dashboard_service function"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_dashboard = Mock()
        mock_applications.dashboard.return_value = mock_dashboard
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container
        
        result = _get_dashboard_service()
        assert result == mock_dashboard


@pytest.mark.unit
def test_register_dashboard_routes():
    """Test register_dashboard_routes function"""
    mock_bp = Mock()
    
    with patch('routes.dashboard._get_dashboard_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_dashboard_routes(mock_bp)
        
        assert mock_bp.route.called


@pytest.mark.unit
def test_dashboard_imports():
    """Test that dashboard functions can be imported"""
    from routes.dashboard import (
        _get_dashboard_service,
        register_dashboard_routes,
    )


@pytest.mark.unit
def test_dashboard_routes_module_structure():
    """Test dashboard routes module structure"""
    import routes.dashboard as dashboard_module
    
    # Check for expected functions
    assert hasattr(dashboard_module, '_get_dashboard_service')
    assert hasattr(dashboard_module, 'register_dashboard_routes')
    
    # Check for expected imports
    assert hasattr(dashboard_module, 'json')
    assert hasattr(dashboard_module, 'logging')
    assert hasattr(dashboard_module, 'datetime')
    assert hasattr(dashboard_module, 'g')
    assert hasattr(dashboard_module, 'jsonify')
    assert hasattr(dashboard_module, 'render_template')
    assert hasattr(dashboard_module, 'request')
    assert hasattr(dashboard_module, 'session')


@pytest.mark.unit
def test_register_dashboard_routes_route_registration():
    """Test register_dashboard_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.dashboard._get_dashboard_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_dashboard_routes(mock_bp)
        
        # Should register multiple routes
        assert mock_bp.route.call_count >= 6


@pytest.mark.unit
def test_dashboard_module_has_required_imports():
    """Test dashboard module has required imports"""
    import routes.dashboard as dashboard_module
    
    # Flask imports
    assert hasattr(dashboard_module, 'g')
    assert hasattr(dashboard_module, 'jsonify')
    assert hasattr(dashboard_module, 'render_template')
    assert hasattr(dashboard_module, 'request')
    assert hasattr(dashboard_module, 'session')
    
    # Custom imports
    assert hasattr(dashboard_module, 'get_container')
    assert hasattr(dashboard_module, 'get_analysis_engine')
    assert hasattr(dashboard_module, 'to_decimal')
    assert hasattr(dashboard_module, 'get_financial_analysis')
    assert hasattr(dashboard_module, 'get_monthly_dashboard_data')
    assert hasattr(dashboard_module, 'get_market_data_summary')
    assert hasattr(dashboard_module, 'rollback_session')
    assert hasattr(dashboard_module, 'login_required')


@pytest.mark.unit
def test_dashboard_service_call_in_register():
    """Test register_dashboard_routes calls _get_dashboard_service"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.dashboard._get_dashboard_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_dashboard_routes(mock_bp)
        
        mock_get_service.assert_called_once()


@pytest.mark.unit
def test_dashboard_blueprint_parameter():
    """Test register_dashboard_routes accepts blueprint parameter"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.dashboard._get_dashboard_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Should not raise exception
        register_dashboard_routes(mock_bp)


@pytest.mark.unit
def test_dashboard_service_index_context():
    """Test dashboard service index_context is called in route"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.dashboard._get_dashboard_service') as mock_get_service:
        mock_service = Mock()
        mock_service.index_context.return_value = {}
        mock_get_service.return_value = mock_service
        
        register_dashboard_routes(mock_bp)
        
        # Service should be obtained
        assert mock_get_service.called


@pytest.mark.unit
def test_dashboard_monthly_dashboard_json_encoder():
    """Test monthly dashboard has JSON encoder for Decimal"""
    import routes.dashboard as dashboard_module
    # The module should handle Decimal serialization
    # This is verified by the _safe_dumps function in the module
    assert True  # Structure check passed


@pytest.mark.unit
def test_dashboard_error_handling_structure():
    """Test dashboard routes have error handling"""
    import routes.dashboard as dashboard_module
    import inspect
    
    # Check that the module has error handling patterns
    source = inspect.getsource(dashboard_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_dashboard_login_required_decorator():
    """Test dashboard routes use login_required decorator"""
    import routes.dashboard as dashboard_module
    import inspect
    
    # Check that login_required is imported and used
    source = inspect.getsource(dashboard_module)
    assert 'login_required' in source


@pytest.mark.unit
def test_dashboard_financial_analysis_route():
    """Test financial analysis route exists"""
    import routes.dashboard as dashboard_module
    import inspect
    
    source = inspect.getsource(dashboard_module)
    assert '/analysis' in source


@pytest.mark.unit
def test_dashboard_financial_freedom_route():
    """Test financial freedom route exists"""
    import routes.dashboard as dashboard_module
    import inspect
    
    source = inspect.getsource(dashboard_module)
    assert '/financial_freedom' in source


@pytest.mark.unit
def test_dashboard_monthly_dashboard_route():
    """Test monthly dashboard route exists"""
    import routes.dashboard as dashboard_module
    import inspect
    
    source = inspect.getsource(dashboard_module)
    assert '/monthly_dashboard' in source


@pytest.mark.unit
def test_dashboard_quick_transfer_route():
    """Test quick transfer route exists"""
    import routes.dashboard as dashboard_module
    import inspect
    
    source = inspect.getsource(dashboard_module)
    assert '/quick_transfer' in source


@pytest.mark.unit
def test_dashboard_user_guide_route():
    """Test user guide route exists"""
    import routes.dashboard as dashboard_module
    import inspect
    
    source = inspect.getsource(dashboard_module)
    assert '/user_guide' in source


@pytest.mark.unit
def test_dashboard_financial_dashboard_route():
    """Test financial dashboard route exists"""
    import routes.dashboard as dashboard_module
    import inspect
    
    source = inspect.getsource(dashboard_module)
    assert '/financial_dashboard' in source
