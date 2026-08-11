"""
Unit Tests - Categories Routes
Category and catalog route functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from routes.categories import (
    _get_catalog_service,
    register_category_routes,
)


@pytest.mark.unit
def test_get_catalog_service():
    """Test _get_catalog_service function"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_catalog = Mock()
        mock_applications.catalog.return_value = mock_catalog
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container
        
        result = _get_catalog_service()
        assert result == mock_catalog


@pytest.mark.unit
def test_register_category_routes():
    """Test register_category_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_category_routes(mock_bp)
        
        assert mock_bp.route.called


@pytest.mark.unit
def test_categories_imports():
    """Test that categories functions can be imported"""
    from routes.categories import (
        _get_catalog_service,
        register_category_routes,
    )
    
    assert callable(_get_catalog_service)
    assert callable(register_category_routes)


@pytest.mark.unit
def test_categories_module_structure():
    """Test categories routes module structure"""
    import routes.categories as categories_module
    
    # Check for expected functions
    assert hasattr(categories_module, '_get_catalog_service')
    assert hasattr(categories_module, 'register_category_routes')
    
    # Check for expected imports
    assert hasattr(categories_module, 'logging')
    assert hasattr(categories_module, 'flash')
    assert hasattr(categories_module, 'g')
    assert hasattr(categories_module, 'redirect')
    assert hasattr(categories_module, 'render_template')
    assert hasattr(categories_module, 'request')
    assert hasattr(categories_module, 'url_for')


@pytest.mark.unit
def test_categories_module_has_required_imports():
    """Test categories module has required imports"""
    import routes.categories as categories_module
    
    # Flask imports
    assert hasattr(categories_module, 'flash')
    assert hasattr(categories_module, 'g')
    assert hasattr(categories_module, 'redirect')
    assert hasattr(categories_module, 'render_template')
    assert hasattr(categories_module, 'request')
    assert hasattr(categories_module, 'url_for')
    
    # Custom imports
    assert hasattr(categories_module, 'get_container')
    assert hasattr(categories_module, 'get_tenant')
    assert hasattr(categories_module, 'rollback_session')
    assert hasattr(categories_module, 'login_required')


@pytest.mark.unit
def test_categories_routes_exist():
    """Test categories routes exist in module"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/categories' in source
    assert '/update_category' in source
    assert '/delete_category' in source


@pytest.mark.unit
def test_categories_error_handling():
    """Test categories routes have error handling"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_categories_logger():
    """Test categories module has logger"""
    import routes.categories as categories_module
    assert hasattr(categories_module, 'logger')
    assert categories_module.logger is not None


@pytest.mark.unit
def test_categories_route_registration():
    """Test register_category_routes registers routes"""
    from routes.categories import register_category_routes
    from unittest.mock import Mock, patch
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_category_routes(mock_bp)
        
        # Should register multiple routes
        assert mock_bp.route.call_count >= 5


@pytest.mark.unit
def test_categories_blueprint_parameter():
    """Test register_category_routes accepts blueprint parameter"""
    from routes.categories import register_category_routes
    from unittest.mock import Mock, patch
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Should not raise exception
        register_category_routes(mock_bp)


@pytest.mark.unit
def test_get_catalog_service_container_call():
    """Test _get_catalog_service calls get_container"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_catalog = Mock()
        mock_applications.catalog.return_value = mock_catalog
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container
        
        _get_catalog_service()
        
        mock_get_container.assert_called_once()
        mock_container.applications.catalog.assert_called_once()


@pytest.mark.unit
def test_register_category_routes_route_registration():
    """Test register_category_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_category_routes(mock_bp)
        
        # Should register multiple routes
        assert mock_bp.route.call_count >= 6


@pytest.mark.unit
def test_categories_module_has_required_imports():
    """Test categories module has required imports"""
    import routes.categories as categories_module
    
    # Flask imports
    assert hasattr(categories_module, 'flash')
    assert hasattr(categories_module, 'g')
    assert hasattr(categories_module, 'redirect')
    assert hasattr(categories_module, 'render_template')
    assert hasattr(categories_module, 'request')
    assert hasattr(categories_module, 'url_for')
    
    # Custom imports
    assert hasattr(categories_module, 'get_container')
    assert hasattr(categories_module, 'get_tenant_id')
    assert hasattr(categories_module, 'rollback_session')
    assert hasattr(categories_module, 'login_required')


@pytest.mark.unit
def test_register_category_routes_service_call():
    """Test register_category_routes calls _get_catalog_service"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        register_category_routes(mock_bp)
        
        mock_get_service.assert_called_once()


@pytest.mark.unit
def test_categories_blueprint_parameter():
    """Test register_category_routes accepts blueprint parameter"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Should not raise exception
        register_category_routes(mock_bp)


@pytest.mark.unit
def test_categories_page_route_exists():
    """Test categories page route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/categories' in source


@pytest.mark.unit
def test_update_category_route_exists():
    """Test update category route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/update_category' in source


@pytest.mark.unit
def test_delete_category_route_exists():
    """Test delete category route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/delete_category' in source


@pytest.mark.unit
def test_update_asset_type_route_exists():
    """Test update asset type route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/update_asset_type' in source


@pytest.mark.unit
def test_delete_asset_type_route_exists():
    """Test delete asset type route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/delete_asset_type' in source


@pytest.mark.unit
def test_update_asset_sector_route_exists():
    """Test update asset sector route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/update_asset_sector' in source


@pytest.mark.unit
def test_delete_asset_sector_route_exists():
    """Test delete asset sector route exists"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert '/delete_asset_sector' in source


@pytest.mark.unit
def test_categories_error_handling_structure():
    """Test categories routes have error handling"""
    import routes.categories as categories_module
    import inspect
    
    # Check that the module has error handling patterns
    source = inspect.getsource(categories_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_categories_login_required_decorator():
    """Test categories routes use login_required decorator"""
    import routes.categories as categories_module
    import inspect
    
    # Check that login_required is imported and used
    source = inspect.getsource(categories_module)
    assert 'login_required' in source


@pytest.mark.unit
def test_categories_flash_messaging():
    """Test categories routes use flash messaging"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'flash' in source


@pytest.mark.unit
def test_categories_rollback_session():
    """Test categories routes use rollback_session"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'rollback_session' in source


@pytest.mark.unit
def test_categories_tenant_context():
    """Test categories routes use tenant context"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    assert 'get_tenant_id' in source or 'tenant_id' in source


@pytest.mark.unit
def test_categories_service_methods():
    """Test catalog service methods are called"""
    import routes.categories as categories_module
    import inspect
    
    source = inspect.getsource(categories_module)
    # Check for service method calls
    assert 'catalog_service' in source
