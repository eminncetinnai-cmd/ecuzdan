"""
Unit Tests - Catalog Repository
Repositories for category and catalog lookups
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from repositories.catalog_repository import CatalogRepository, _generate_gl_code


@pytest.mark.unit
def test_generate_gl_code_revenue():
    """Test _generate_gl_code for revenue (Gelir)"""
    result = _generate_gl_code('Gelir', 1)
    assert result == 'GLR-6001'
    
    result = _generate_gl_code('Gelir', 99)
    assert result == 'GLR-6099'


@pytest.mark.unit
def test_generate_gl_code_expense():
    """Test _generate_gl_code for expense (Gider)"""
    result = _generate_gl_code('Gider', 1)
    assert result == 'GDR-7001'
    
    result = _generate_gl_code('Gider', 50)
    assert result == 'GDR-7050'


@pytest.mark.unit
def test_generate_gl_code_investment():
    """Test _generate_gl_code for investment (Yatırım)"""
    result = _generate_gl_code('Yatırım', 1)
    assert result == 'YTR-1001'
    
    result = _generate_gl_code('Yatırım', 99)
    assert result == 'YTR-1099'


@pytest.mark.unit
def test_catalog_repository_init():
    """Test CatalogRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = CatalogRepository(database=mock_db)
    
    assert repo.session == mock_session


@pytest.mark.unit
def test_catalog_repository_imports():
    """Test that CatalogRepository can be imported"""
    from repositories.catalog_repository import CatalogRepository
    
    assert CatalogRepository is not None


@pytest.mark.unit
def test_catalog_repository_module_structure():
    """Test catalog_repository module structure"""
    import repositories.catalog_repository as catalog_repo_module
    
    # Check for expected class
    assert hasattr(catalog_repo_module, 'CatalogRepository')
    assert hasattr(catalog_repo_module, '_generate_gl_code')
    
    # Check for expected imports
    assert hasattr(catalog_repo_module, 'Asset')
    assert hasattr(catalog_repo_module, 'AssetSector')
    assert hasattr(catalog_repo_module, 'AssetType')
    assert hasattr(catalog_repo_module, 'Category')
    assert hasattr(catalog_repo_module, 'Transaction')
    assert hasattr(catalog_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_catalog_repository_extends_base():
    """Test CatalogRepository extends BaseRepository"""
    from repositories.catalog_repository import CatalogRepository
    from repositories.base import BaseRepository
    
    assert issubclass(CatalogRepository, BaseRepository)


@pytest.mark.unit
def test_visible_categories_query():
    """Test visible_categories_query method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_filtered_query = Mock()
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query = mock_query
        
        repo = CatalogRepository(database=mock_db)
        with patch('repositories.catalog_repository.db.or_') as mock_or:
            mock_query.filter.return_value = mock_filtered_query
            result = repo.visible_categories_query(tenant_id='test_tenant')
            
            assert result == mock_filtered_query


@pytest.mark.unit
def test_visible_categories_query_no_tenant():
    """Test visible_categories_query without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query = mock_query
        
        repo = CatalogRepository(database=mock_db)
        result = repo.visible_categories_query()
        
        assert result == mock_query


@pytest.mark.unit
def test_list_visible_categories():
    """Test list_visible_categories method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.get_cached') as mock_get_cached:
        mock_categories = [Mock()]
        mock_categories[0].tenant_id = None
        mock_get_cached.return_value = mock_categories
        
        repo = CatalogRepository(database=mock_db)
        result = repo.list_visible_categories(tenant_id='test_tenant')
        
        assert result == mock_categories


@pytest.mark.unit
def test_list_visible_categories_no_tenant():
    """Test list_visible_categories without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.get_cached') as mock_get_cached:
        mock_categories = [Mock()]
        mock_get_cached.return_value = mock_categories
        
        repo = CatalogRepository(database=mock_db)
        result = repo.list_visible_categories()
        
        assert result == mock_categories


@pytest.mark.unit
def test_list_categories_by_type():
    """Test list_categories_by_type method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_categories = [Mock()]
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query = mock_query
        repo = CatalogRepository(database=mock_db)
        repo.visible_categories_query = Mock(return_value=mock_query)
        mock_query.filter_by.return_value.all.return_value = mock_categories
        
        result = repo.list_categories_by_type('Gelir', tenant_id='test_tenant')
        
        assert result == mock_categories


@pytest.mark.unit
def test_find_category_by_name():
    """Test find_category_by_name method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_filtered_query = Mock()
    mock_category = Mock()
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query.filter_by.return_value = mock_filtered_query
        
        repo = CatalogRepository(database=mock_db)
        with patch('repositories.catalog_repository.db.or_') as mock_or:
            mock_filtered_query.filter.return_value.first.return_value = mock_category
            result = repo.find_category_by_name('Test Category', tenant_id='test_tenant')
            
            assert result == mock_category


@pytest.mark.unit
def test_find_category_by_name_no_tenant():
    """Test find_category_by_name without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_category = Mock()
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        result = repo.find_category_by_name('Test Category')
        
        assert result == mock_category


@pytest.mark.unit
def test_category_exists():
    """Test category_exists method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_filtered_query = Mock()
    mock_category = Mock()
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query.filter_by.return_value = mock_filtered_query
        
        repo = CatalogRepository(database=mock_db)
        with patch('repositories.catalog_repository.db.or_') as mock_or:
            mock_filtered_query.filter.return_value.first.return_value = mock_category
            result = repo.category_exists('Test Category', tenant_id='test_tenant')
            
            assert result is True


@pytest.mark.unit
def test_category_exists_not_found():
    """Test category_exists when category not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_filtered_query = Mock()
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.query.filter_by.return_value = mock_filtered_query
        
        repo = CatalogRepository(database=mock_db)
        with patch('repositories.catalog_repository.db.or_') as mock_or:
            mock_filtered_query.filter.return_value.first.return_value = None
            result = repo.category_exists('Test Category', tenant_id='test_tenant')
            
            assert result is False


@pytest.mark.unit
def test_list_asset_types():
    """Test list_asset_types method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset_types = [Mock()]
    
    with patch('repositories.catalog_repository.AssetType') as mock_asset_type_class:
        mock_asset_type_class.query.all.return_value = mock_asset_types
        
        repo = CatalogRepository(database=mock_db)
        result = repo.list_asset_types()
        
        assert result == mock_asset_types


@pytest.mark.unit
def test_asset_type_exists():
    """Test asset_type_exists method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_asset_type = Mock()
    
    with patch('repositories.catalog_repository.AssetType') as mock_asset_type_class:
        mock_asset_type_class.query.filter_by.return_value.first.return_value = mock_asset_type
        
        repo = CatalogRepository(database=mock_db)
        result = repo.asset_type_exists('Stock')
        
        assert result is True


@pytest.mark.unit
def test_asset_type_exists_not_found():
    """Test asset_type_exists when asset type not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.AssetType') as mock_asset_type_class:
        mock_asset_type_class.query.filter_by.return_value.first.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.asset_type_exists('Stock')
        
        assert result is False


@pytest.mark.unit
def test_add_asset_type():
    """Test add_asset_type method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset_type = Mock()
    
    with patch('repositories.catalog_repository.AssetType') as mock_asset_type_class:
        mock_asset_type_class.return_value = mock_asset_type
        
        repo = CatalogRepository(database=mock_db)
        repo.add = Mock(return_value=mock_asset_type)
        
        result = repo.add_asset_type('Stock')
        
        assert result == mock_asset_type


@pytest.mark.unit
def test_list_asset_sectors():
    """Test list_asset_sectors method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_sectors = [Mock()]
    
    with patch('repositories.catalog_repository.AssetSector') as mock_sector_class:
        mock_sector_class.query.all.return_value = mock_sectors
        
        repo = CatalogRepository(database=mock_db)
        result = repo.list_asset_sectors()
        
        assert result == mock_sectors


@pytest.mark.unit
def test_asset_sector_exists():
    """Test asset_sector_exists method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_sector = Mock()
    
    with patch('repositories.catalog_repository.AssetSector') as mock_sector_class:
        mock_sector_class.query.filter_by.return_value.first.return_value = mock_sector
        
        repo = CatalogRepository(database=mock_db)
        result = repo.asset_sector_exists('Technology')
        
        assert result is True


@pytest.mark.unit
def test_asset_sector_exists_not_found():
    """Test asset_sector_exists when sector not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.AssetSector') as mock_sector_class:
        mock_sector_class.query.filter_by.return_value.first.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.asset_sector_exists('Technology')
        
        assert result is False


@pytest.mark.unit
def test_add_asset_sector():
    """Test add_asset_sector method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_sector = Mock()
    
    with patch('repositories.catalog_repository.AssetSector') as mock_sector_class:
        mock_sector_class.return_value = mock_sector
        
        repo = CatalogRepository(database=mock_db)
        repo.add = Mock(return_value=mock_sector)
        
        result = repo.add_asset_sector('Technology')
        
        assert result == mock_sector


@pytest.mark.unit
def test_catalog_repository_module_has_required_imports():
    """Test catalog_repository module has required imports"""
    import repositories.catalog_repository as catalog_repo_module
    
    # Custom imports
    assert hasattr(catalog_repo_module, 'Asset')
    assert hasattr(catalog_repo_module, 'AssetSector')
    assert hasattr(catalog_repo_module, 'AssetType')
    assert hasattr(catalog_repo_module, 'Category')
    assert hasattr(catalog_repo_module, 'Transaction')
    assert hasattr(catalog_repo_module, 'db')
    assert hasattr(catalog_repo_module, 'BaseRepository')
    assert hasattr(catalog_repo_module, 'BaseRepositoryContract')
    assert hasattr(catalog_repo_module, 'CatalogRepositoryContract')


@pytest.mark.unit
def test_add_category():
    """Test add_category method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.id = 1
    mock_category.code = None
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        repo.add = Mock(return_value=mock_category)
        repo.commit = Mock()
        
        with patch('repositories.catalog_repository._generate_gl_code') as mock_gl_code:
            mock_gl_code.return_value = 'GLR-6001'
            result = repo.add_category('Test', 'Gelir', tenant_id='test_tenant', user_id='user1')
            
            assert result == mock_category


@pytest.mark.unit
def test_add_category_with_code():
    """Test add_category method with existing code"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.id = 1
    mock_category.code = 'CUSTOM-001'
    
    with patch('repositories.catalog_repository.Category') as mock_category_class:
        mock_category_class.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        repo.add = Mock(return_value=mock_category)
        repo.commit = Mock()
        
        result = repo.add_category('Test', 'Gelir', code='CUSTOM-001', tenant_id='test_tenant', user_id='user1')
        
        assert result == mock_category


@pytest.mark.unit
def test_update_category():
    """Test update_category method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.tenant_id = 'test_tenant'
    mock_category.version = 1
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        repo.commit = Mock()
        
        with patch('utils.ref_cache.invalidate') as mock_invalidate:
            result = repo.update_category(1, 'New Name', 'Gelir', tenant_id='test_tenant', user_id='user1')
            
            assert result == mock_category


@pytest.mark.unit
def test_update_category_not_found():
    """Test update_category when category not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.update_category(1, 'New Name', 'Gelir')
        
        assert result is None


@pytest.mark.unit
def test_update_category_system_category():
    """Test update_category with system category (tenant_id is None)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.tenant_id = None
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        
        try:
            repo.update_category(1, 'New Name', 'Gelir')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Sistem kategorileri düzenlenemez" in str(e)


@pytest.mark.unit
def test_update_category_version_conflict():
    """Test update_category with version conflict"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.tenant_id = 'test_tenant'
    mock_category.version = 2
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        
        try:
            repo.update_category(1, 'New Name', 'Gelir', version=1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Çakışma Hatası" in str(e)


@pytest.mark.unit
def test_delete_category():
    """Test delete_category method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.tenant_id = 'test_tenant'
    mock_category.name = 'Test Category'
    mock_category.id = 1
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        repo.delete = Mock()
        repo.commit = Mock()
        
        with patch('repositories.catalog_repository.Transaction') as mock_tx_class:
            mock_tx_class.query.filter_by.return_value.count.return_value = 0
            
            with patch('utils.ref_cache.invalidate') as mock_invalidate:
                result = repo.delete_category(1, tenant_id='test_tenant', user_id='user1')
                
                assert result is True


@pytest.mark.unit
def test_delete_category_not_found():
    """Test delete_category when category not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.delete_category(1)
        
        assert result is False


@pytest.mark.unit
def test_delete_category_system_category():
    """Test delete_category with system category"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.tenant_id = None
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        
        try:
            repo.delete_category(1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Sistem kategorileri silinemez" in str(e)


@pytest.mark.unit
def test_delete_category_with_transactions():
    """Test delete_category when category has transactions (soft delete)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_category.tenant_id = 'test_tenant'
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_category
        
        repo = CatalogRepository(database=mock_db)
        repo.commit = Mock()
        
        with patch('repositories.catalog_repository.Transaction') as mock_tx_class:
            mock_tx_class.query.filter_by.return_value.count.return_value = 5
            
            with patch('utils.ref_cache.invalidate') as mock_invalidate:
                result = repo.delete_category(1, tenant_id='test_tenant')
                
                assert result is True
                assert mock_category.is_active is False


@pytest.mark.unit
def test_update_asset_type():
    """Test update_asset_type method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset_type = Mock()
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_asset_type
        
        repo = CatalogRepository(database=mock_db)
        repo.commit = Mock()
        
        with patch('utils.ref_cache.invalidate') as mock_invalidate:
            result = repo.update_asset_type(1, 'New Name')
            
            assert result == mock_asset_type


@pytest.mark.unit
def test_update_asset_type_not_found():
    """Test update_asset_type when asset type not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.update_asset_type(1, 'New Name')
        
        assert result is None


@pytest.mark.unit
def test_delete_asset_type():
    """Test delete_asset_type method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset_type = Mock()
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_asset_type
        
        repo = CatalogRepository(database=mock_db)
        repo.delete = Mock()
        repo.commit = Mock()
        
        with patch('repositories.catalog_repository.Asset') as mock_asset_class:
            mock_asset_class.query.filter_by.return_value.count.return_value = 0
            
            with patch('utils.ref_cache.invalidate') as mock_invalidate:
                result = repo.delete_asset_type(1)
                
                assert result is True


@pytest.mark.unit
def test_delete_asset_type_not_found():
    """Test delete_asset_type when asset type not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.delete_asset_type(1)
        
        assert result is False


@pytest.mark.unit
def test_delete_asset_type_in_use():
    """Test delete_asset_type when asset type is in use"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset_type = Mock()
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_asset_type
        
        repo = CatalogRepository(database=mock_db)
        
        with patch('repositories.catalog_repository.Asset') as mock_asset_class:
            mock_asset_class.query.filter_by.return_value.count.return_value = 5
            
            try:
                repo.delete_asset_type(1)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "kullanılıyor" in str(e)


@pytest.mark.unit
def test_update_asset_sector():
    """Test update_asset_sector method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_sector = Mock()
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_sector
        
        repo = CatalogRepository(database=mock_db)
        repo.commit = Mock()
        
        with patch('utils.ref_cache.invalidate') as mock_invalidate:
            result = repo.update_asset_sector(1, 'New Name')
            
            assert result == mock_sector


@pytest.mark.unit
def test_update_asset_sector_not_found():
    """Test update_asset_sector when sector not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.update_asset_sector(1, 'New Name')
        
        assert result is None


@pytest.mark.unit
def test_delete_asset_sector():
    """Test delete_asset_sector method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_sector = Mock()
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_sector
        
        repo = CatalogRepository(database=mock_db)
        repo.delete = Mock()
        repo.commit = Mock()
        
        with patch('repositories.catalog_repository.Asset') as mock_asset_class:
            mock_asset_class.query.filter_by.return_value.count.return_value = 0
            
            with patch('utils.ref_cache.invalidate') as mock_invalidate:
                result = repo.delete_asset_sector(1)
                
                assert result is True


@pytest.mark.unit
def test_delete_asset_sector_not_found():
    """Test delete_asset_sector when sector not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = None
        
        repo = CatalogRepository(database=mock_db)
        result = repo.delete_asset_sector(1)
        
        assert result is False


@pytest.mark.unit
def test_delete_asset_sector_in_use():
    """Test delete_asset_sector when sector is in use"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_sector = Mock()
    
    with patch('repositories.catalog_repository.db.session.get') as mock_get:
        mock_get.return_value = mock_sector
        
        repo = CatalogRepository(database=mock_db)
        
        with patch('repositories.catalog_repository.Asset') as mock_asset_class:
            mock_asset_class.query.filter_by.return_value.count.return_value = 3
            
            try:
                repo.delete_asset_sector(1)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "kullanılıyor" in str(e)
