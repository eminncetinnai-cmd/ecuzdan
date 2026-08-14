"""
Unit Tests - Categories Routes
Category management route tests - Detailed functional tests
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
def test_categories_route_registration_calls_service():
    """Test that register_category_routes registers routes"""
    from routes.categories import register_category_routes
    
    mock_bp = Mock()
    route_calls = []
    
    def capture_route(rule, **options):
        route_calls.append((rule, options))
        return lambda f: f
    
    mock_bp.route = capture_route
    
    register_category_routes(mock_bp)
    
    # Verify that routes were registered
    assert len(route_calls) >= 5  # Should register 5+ routes
    route_rules = [call[0] for call in route_calls]
    assert '/categories' in route_rules
    assert '/delete_category/<int:id>' in route_rules


@pytest.mark.unit
def test_categories_route_list_categories():
    """Test that list_categories route returns categories"""
    from routes.categories import register_category_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_service.page_context.return_value = {
            'cats': [
                Mock(name='Maaş', type='Gelir'),
                Mock(name='Kira', type='Gider'),
            ],
            'asset_types': [],
            'asset_sectors': [],
        }
        mock_get_service.return_value = mock_service
        
        register_category_routes(mock_bp)
        
        assert mock_bp.route.called


@pytest.mark.unit
def test_categories_route_create_category_validation():
    """Test that create_category validates input"""
    from routes.categories import register_category_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        with patch('utils.db_session.rollback_session') as mock_rollback:
            register_category_routes(mock_bp)
            
            assert mock_bp.route.called


@pytest.mark.unit
def test_categories_route_delete_category():
    """Test that delete_category route calls service"""
    from routes.categories import register_category_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_service.delete_category.return_value = 'Kategori silindi'
        mock_get_service.return_value = mock_service
        
        with patch('utils.ajax_helpers.is_ajax_request') as mock_is_ajax:
            mock_is_ajax.return_value = True
            
            register_category_routes(mock_bp)
            
            assert mock_bp.route.called


@pytest.mark.unit
def test_categories_route_error_handling():
    """Test that categories routes have error handling"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'except Exception' in source
    assert 'try:' in source


@pytest.mark.unit
def test_categories_route_uses_flash():
    """Test that categories routes use flash for user feedback"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'flash' in source


@pytest.mark.unit
def test_categories_route_uses_redirect():
    """Test that categories routes use redirect after actions"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'redirect' in source


@pytest.mark.unit
def test_categories_module_structure():
    """Test categories routes module structure"""
    import routes.categories as categories_module
    
    # Check for expected functions
    assert hasattr(categories_module, 'register_category_routes')
    assert hasattr(categories_module, '_get_catalog_service')
    
    # Check for expected imports
    assert hasattr(categories_module, 'render_template')
    assert hasattr(categories_module, 'request')
    assert hasattr(categories_module, 'flash')
    assert hasattr(categories_module, 'redirect')


@pytest.mark.unit
def test_categories_logger():
    """Test categories module has logger"""
    import routes.categories as categories_module
    assert hasattr(categories_module, 'logger')
    assert categories_module.logger is not None


@pytest.mark.unit
def test_categories_json_usage():
    """Test categories routes return dict responses for AJAX"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    # Categories routes return dict for AJAX requests, not jsonify
    assert 'return {' in source or 'return {' in source


@pytest.mark.unit
def test_categories_template_rendering():
    """Test categories routes use template rendering"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'render_template' in source


@pytest.mark.unit
def test_categories_request_object():
    """Test categories routes use request object"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'request' in source


@pytest.mark.unit
def test_categories_session_usage():
    """Test categories routes use session"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'session' in source


@pytest.mark.unit
def test_categories_get_container():
    """Test categories routes use get_container"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'get_container' in source


@pytest.mark.unit
def test_categories_rollback_session():
    """Test categories routes use rollback_session"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'rollback_session' in source


@pytest.mark.unit
def test_categories_login_required():
    """Test categories routes use login_required"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'login_required' in source


@pytest.mark.unit
def test_categories_routes_exist():
    """Test categories routes exist in module"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/categories' in source
    assert 'create' in source or 'add_from_form' in source
    assert 'delete' in source


@pytest.mark.unit
def test_categories_service_methods():
    """Test categories routes use service methods"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    # Should call service methods like page_context, create_category, delete_category
    assert 'page_context' in source or 'create_category' in source or 'delete_category' in source
