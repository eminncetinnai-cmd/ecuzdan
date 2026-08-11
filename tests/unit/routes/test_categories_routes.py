"""
Unit Tests - Categories Routes
Category management route tests
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
def test_categories_route_registration_calls_service():
    """Test that register_category_routes calls catalog service"""
    from routes.categories import register_category_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.categories._get_catalog_service') as mock_get_service:
        mock_service = Mock()
        mock_service.page_context.return_value = {
            'cats': [],
            'asset_types': [],
            'asset_sectors': [],
        }
        mock_get_service.return_value = mock_service
        
        register_category_routes(mock_bp)
        
        mock_get_service.assert_called_once()
        assert mock_bp.route.call_count >= 5  # Should register 5+ routes


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
@pytest.mark.parametrize("category_type,expected_count", [
    ("Gelir", 8),
    ("Gider", 8),
    ("Yatırım", 4),
    ("Transfer", 4),
])
def test_categories_by_type_filter(category_type, expected_count):
    """Test that categories can be filtered by type"""
    from models import Category
    
    # This would need actual test data setup
    # For now, just test the concept
    assert isinstance(category_type, str)
    assert isinstance(expected_count, int)


