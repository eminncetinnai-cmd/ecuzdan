"""
Unit Tests - Category Repository
Repository for category management
"""

from unittest.mock import Mock, patch

import pytest

from repositories.category_repository import CategoryRepository, TenantCategoryRepository


@pytest.mark.unit
def test_category_repository_init():
    """Test CategoryRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = CategoryRepository(database=mock_db)

    assert repo.session == mock_session


@pytest.mark.unit
def test_category_repository_imports():
    """Test that CategoryRepository can be imported"""
    from repositories.category_repository import CategoryRepository

    assert CategoryRepository is not None


@pytest.mark.unit
def test_category_repository_module_structure():
    """Test category_repository module structure"""
    import repositories.category_repository as category_repo_module

    # Check for expected classes
    assert hasattr(category_repo_module, 'CategoryRepository')
    assert hasattr(category_repo_module, 'TenantCategoryRepository')

    # Check for expected imports
    assert hasattr(category_repo_module, 'Category')
    assert hasattr(category_repo_module, 'BaseRepository')
    assert hasattr(category_repo_module, 'TenantScopedRepository')


@pytest.mark.unit
def test_category_repository_extends_base():
    """Test CategoryRepository extends BaseRepository"""
    from repositories.base import BaseRepository
    from repositories.category_repository import CategoryRepository

    assert issubclass(CategoryRepository, BaseRepository)


@pytest.mark.unit
def test_get_category():
    """Test get_category method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.get = Mock(return_value=mock_category)

    result = repo.get_category(1)

    assert result == mock_category
    repo.get.assert_called_once()


@pytest.mark.unit
def test_find_category_by_name_with_tenant():
    """Test find_category_by_name with tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.find_category_by_name('Test Category', tenant_id='test_tenant')

    assert result == mock_category


@pytest.mark.unit
def test_find_category_by_name_without_tenant():
    """Test find_category_by_name without tenant_id (standard categories)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.find_category_by_name('Test Category')

    assert result == mock_category


@pytest.mark.unit
def test_find_category_by_code_with_tenant():
    """Test find_category_by_code with tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.find_category_by_code('GLR-6001', tenant_id='test_tenant')

    assert result == mock_category


@pytest.mark.unit
def test_find_category_by_code_without_tenant():
    """Test find_category_by_code without tenant_id (standard categories)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.find_category_by_code('GLR-6001')

    assert result == mock_category


@pytest.mark.unit
def test_get_standard_categories():
    """Test get_standard_categories method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_categories = [Mock()]
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.all.return_value = mock_categories

    result = repo.get_standard_categories()

    assert result == mock_categories


@pytest.mark.unit
def test_get_categories_by_type_with_tenant():
    """Test get_categories_by_type with tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_categories = [Mock()]
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.all.return_value = mock_categories

    result = repo.get_categories_by_type('Gider', tenant_id='test_tenant')

    assert result == mock_categories


@pytest.mark.unit
def test_get_categories_by_type_without_tenant():
    """Test get_categories_by_type without tenant_id (standard categories)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_categories = [Mock()]
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.all.return_value = mock_categories

    result = repo.get_categories_by_type('Gider')

    assert result == mock_categories


@pytest.mark.unit
def test_get_tenant_categories():
    """Test get_tenant_categories method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_categories = [Mock()]
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.all.return_value = mock_categories

    result = repo.get_tenant_categories('test_tenant')

    assert result == mock_categories


@pytest.mark.unit
def test_add_category():
    """Test add_category method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()

    with patch('repositories.category_repository.Category') as mock_category_class:
        mock_category_class.return_value = mock_category

        repo = CategoryRepository(database=mock_db)
        repo.add = Mock(return_value=mock_category)

        result = repo.add_category(name='Test', type='Gider')

        assert result == mock_category


@pytest.mark.unit
def test_delete_category():
    """Test delete_category method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.delete = Mock()

    repo.delete_category(mock_category)

    repo.delete.assert_called_once_with(mock_category)


@pytest.mark.unit
def test_is_category_name_exists_with_tenant():
    """Test is_category_name_exists with tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.is_category_name_exists('Test Category', tenant_id='test_tenant')

    assert result is True


@pytest.mark.unit
def test_is_category_name_exists_without_tenant():
    """Test is_category_name_exists without tenant_id (standard categories)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.is_category_name_exists('Test Category')

    assert result is True


@pytest.mark.unit
def test_is_category_name_exists_not_found():
    """Test is_category_name_exists when category not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = None

    result = repo.is_category_name_exists('Test Category', tenant_id='test_tenant')

    assert result is False


@pytest.mark.unit
def test_is_category_name_exists_with_exclude_id():
    """Test is_category_name_exists with exclude_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.filter.return_value.first.return_value = mock_category

    result = repo.is_category_name_exists('Test Category', tenant_id='test_tenant', exclude_id=1)

    assert result is True


@pytest.mark.unit
def test_is_category_code_exists_with_tenant():
    """Test is_category_code_exists with tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.is_category_code_exists('GLR-6001', tenant_id='test_tenant')

    assert result is True


@pytest.mark.unit
def test_is_category_code_exists_without_tenant():
    """Test is_category_code_exists without tenant_id (standard categories)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = mock_category

    result = repo.is_category_code_exists('GLR-6001')

    assert result is True


@pytest.mark.unit
def test_is_category_code_exists_not_found():
    """Test is_category_code_exists when category not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.first.return_value = None

    result = repo.is_category_code_exists('GLR-6001', tenant_id='test_tenant')

    assert result is False


@pytest.mark.unit
def test_is_category_code_exists_with_exclude_id():
    """Test is_category_code_exists with exclude_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = CategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    mock_query.filter_by.return_value.filter_by.return_value.filter.return_value.first.return_value = mock_category

    result = repo.is_category_code_exists('GLR-6001', tenant_id='test_tenant', exclude_id=1)

    assert result is True


# TenantCategoryRepository tests

@pytest.mark.unit
def test_tenant_category_repository_init():
    """Test TenantCategoryRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = TenantCategoryRepository(database=mock_db)

    assert repo.session == mock_session


@pytest.mark.unit
def test_tenant_category_repository_imports():
    """Test that TenantCategoryRepository can be imported"""
    from repositories.category_repository import TenantCategoryRepository

    assert TenantCategoryRepository is not None


@pytest.mark.unit
def test_tenant_category_repository_extends_base():
    """Test TenantCategoryRepository extends TenantScopedRepository"""
    from repositories.base import TenantScopedRepository
    from repositories.category_repository import TenantCategoryRepository

    assert issubclass(TenantCategoryRepository, TenantScopedRepository)


@pytest.mark.unit
def test_get_categories_for_tenant():
    """Test get_categories_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_tenant_categories = [Mock()]
    mock_standard_categories = [Mock()]
    mock_query = Mock()

    repo = TenantCategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    repo.require_tenant_id = Mock(return_value='test_tenant')
    mock_query.filter_by.side_effect = [
        Mock(all=Mock(return_value=mock_tenant_categories)),
        Mock(all=Mock(return_value=mock_standard_categories))
    ]

    result = repo.get_categories_for_tenant('test_tenant')

    assert result == mock_tenant_categories + mock_standard_categories


@pytest.mark.unit
def test_get_tenant_specific_categories():
    """Test get_tenant_specific_categories method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_categories = [Mock()]
    mock_query = Mock()

    repo = TenantCategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    repo.require_tenant_id = Mock(return_value='test_tenant')
    mock_query.filter_by.return_value.all.return_value = mock_categories

    result = repo.get_tenant_specific_categories('test_tenant')

    assert result == mock_categories


@pytest.mark.unit
def test_find_category_for_tenant_tenant_specific():
    """Test find_category_for_tenant when tenant-specific category exists"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = TenantCategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    repo.require_tenant_id = Mock(return_value='test_tenant')
    mock_query.filter_by.return_value.first.return_value = mock_category

    result = repo.find_category_for_tenant('Test Category', 'test_tenant')

    assert result == mock_category


@pytest.mark.unit
def test_find_category_for_tenant_standard():
    """Test find_category_for_tenant when only standard category exists"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()
    mock_query = Mock()

    repo = TenantCategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    repo.require_tenant_id = Mock(return_value='test_tenant')
    # First call (tenant-specific) returns None, second (standard) returns category
    mock_query.filter_by.side_effect = [
        Mock(first=Mock(return_value=None)),
        Mock(first=Mock(return_value=mock_category))
    ]

    result = repo.find_category_for_tenant('Test Category', 'test_tenant')

    assert result == mock_category


@pytest.mark.unit
def test_find_category_for_tenant_not_found():
    """Test find_category_for_tenant when category not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()

    repo = TenantCategoryRepository(database=mock_db)
    repo.session.query.return_value = mock_query
    repo.require_tenant_id = Mock(return_value='test_tenant')
    # Both calls return None
    mock_query.filter_by.side_effect = [
        Mock(first=Mock(return_value=None)),
        Mock(first=Mock(return_value=None))
    ]

    result = repo.find_category_for_tenant('Test Category', 'test_tenant')

    assert result is None


@pytest.mark.unit
def test_is_valid_category_for_tenant_true():
    """Test is_valid_category_for_tenant when category is valid"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_category = Mock()

    repo = TenantCategoryRepository(database=mock_db)
    repo.find_category_for_tenant = Mock(return_value=mock_category)

    result = repo.is_valid_category_for_tenant('Test Category', 'test_tenant')

    assert result is True


@pytest.mark.unit
def test_is_valid_category_for_tenant_false():
    """Test is_valid_category_for_tenant when category is not valid"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = TenantCategoryRepository(database=mock_db)
    repo.find_category_for_tenant = Mock(return_value=None)

    result = repo.is_valid_category_for_tenant('Test Category', 'test_tenant')

    assert result is False
