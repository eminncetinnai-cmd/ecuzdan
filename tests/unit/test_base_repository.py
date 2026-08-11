"""
Unit Tests - Base Repository
SQLAlchemy repository primitives tests
"""

import pytest
from unittest.mock import Mock, patch
from repositories.base import BaseRepository, TenantScopedRepository


@pytest.mark.unit
def test_base_repository_module_imports():
    """Test base_repository module can be imported"""
    from repositories.base import BaseRepository, TenantScopedRepository
    assert BaseRepository is not None
    assert TenantScopedRepository is not None


@pytest.mark.unit
def test_base_repository_module_structure():
    """Test base_repository module structure"""
    import repositories.base as base_module
    
    # Check for expected classes
    assert hasattr(base_module, 'BaseRepository')
    assert hasattr(base_module, 'TenantScopedRepository')


@pytest.mark.unit
def test_base_repository_init_with_database():
    """Test BaseRepository initialization with database"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    
    assert repo.db == mock_db
    assert repo.session == mock_session


@pytest.mark.unit
def test_base_repository_init_without_database():
    """Test BaseRepository initialization without database - skipped due to Flask context requirement"""
    pytest.skip("Requires Flask application context")


@pytest.mark.unit
def test_base_repository_query():
    """Test BaseRepository query method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    
    result = repo.query('Model1', 'Model2')
    
    assert result == mock_query
    mock_session.query.assert_called_once_with('Model1', 'Model2')


@pytest.mark.unit
def test_base_repository_get():
    """Test BaseRepository get method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_entity = Mock()
    mock_session.get.return_value = mock_entity
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    
    result = repo.get('Model', 1)
    
    assert result == mock_entity
    mock_session.get.assert_called_once_with('Model', 1)


@pytest.mark.unit
def test_base_repository_add():
    """Test BaseRepository add method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    mock_entity = Mock()
    
    result = repo.add(mock_entity)
    
    assert result == mock_entity
    mock_session.add.assert_called_once_with(mock_entity)


@pytest.mark.unit
def test_base_repository_delete():
    """Test BaseRepository delete method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    mock_entity = Mock()
    
    repo.delete(mock_entity)
    
    mock_session.delete.assert_called_once_with(mock_entity)


@pytest.mark.unit
def test_base_repository_commit():
    """Test BaseRepository commit method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    
    repo.commit()
    
    mock_session.commit.assert_called_once()


@pytest.mark.unit
def test_base_repository_rollback():
    """Test BaseRepository rollback method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = BaseRepository(database=mock_db)
    
    repo.rollback()
    
    mock_session.rollback.assert_called_once()


@pytest.mark.unit
def test_tenant_scoped_repository_init():
    """Test TenantScopedRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    assert repo.db == mock_db
    assert repo.session == mock_session


@pytest.mark.unit
def test_tenant_scoped_repository_require_tenant_id_explicit():
    """Test TenantScopedRepository require_tenant_id with explicit tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    result = repo.require_tenant_id(tenant_id='test_tenant')
    
    assert result == 'test_tenant'


@pytest.mark.unit
def test_tenant_scoped_repository_require_tenant_id_from_flask():
    """Test TenantScopedRepository require_tenant_id from Flask context - skipped due to Flask context requirement"""
    pytest.skip("Requires Flask application context")


@pytest.mark.unit
def test_tenant_scoped_repository_require_tenant_id_no_context():
    """Test TenantScopedRepository require_tenant_id raises error when no context"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    try:
        repo.require_tenant_id()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Tenant context bulunamadı" in str(e)


@pytest.mark.unit
def test_tenant_scoped_repository_filter_for_tenant():
    """Test TenantScopedRepository filter_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    mock_query = Mock()
    mock_filtered_query = Mock()
    mock_query.filter.return_value = mock_filtered_query
    
    mock_model = Mock()
    mock_model.tenant_id == 'test_tenant'  # This creates a comparison expression
    
    result = repo.filter_for_tenant(mock_query, mock_model, 'test_tenant')
    
    assert result == mock_filtered_query
    mock_query.filter.assert_called_once()


@pytest.mark.unit
def test_tenant_scoped_repository_get_for_tenant():
    """Test TenantScopedRepository get_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_query = Mock()
    mock_entity = Mock()
    mock_query.filter.return_value.first.return_value = mock_entity
    mock_session.query.return_value = mock_query
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    mock_model = Mock()
    
    result = repo.get_for_tenant(mock_model, 1, 'test_tenant')
    
    assert result == mock_entity
    mock_session.query.assert_called_once_with(mock_model)


@pytest.mark.unit
def test_tenant_scoped_repository_get_for_tenant_not_found():
    """Test TenantScopedRepository get_for_tenant when not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    mock_model = Mock()
    
    result = repo.get_for_tenant(mock_model, 1, 'test_tenant')
    
    assert result is None


@pytest.mark.unit
def test_tenant_scoped_repository_assert_same_tenant_valid():
    """Test TenantScopedRepository assert_same_tenant with valid tenant"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    mock_record = Mock()
    mock_record.tenant_id = 'test_tenant'
    
    result = repo.assert_same_tenant(mock_record, 'test_tenant')
    
    assert result == mock_record


@pytest.mark.unit
def test_tenant_scoped_repository_assert_same_tenant_invalid():
    """Test TenantScopedRepository assert_same_tenant with invalid tenant"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    mock_record = Mock()
    mock_record.tenant_id = 'other_tenant'
    
    try:
        repo.assert_same_tenant(mock_record, 'test_tenant')
        assert False, "Should have raised PermissionError"
    except PermissionError as e:
        assert "Bu kaydı görüntüleme yetkiniz yok" in str(e)


@pytest.mark.unit
def test_tenant_scoped_repository_assert_same_tenant_none_record():
    """Test TenantScopedRepository assert_same_tenant with None record"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    try:
        repo.assert_same_tenant(None, 'test_tenant')
        assert False, "Should have raised PermissionError"
    except PermissionError as e:
        assert "Bu kaydı görüntüleme yetkiniz yok" in str(e)


@pytest.mark.unit
def test_tenant_scoped_repository_assert_same_tenant_custom_error():
    """Test TenantScopedRepository assert_same_tenant with custom error message"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = TenantScopedRepository(database=mock_db)
    
    mock_record = Mock()
    mock_record.tenant_id = 'other_tenant'
    
    custom_msg = "Custom error message"
    
    try:
        repo.assert_same_tenant(mock_record, 'test_tenant', custom_msg)
        assert False, "Should have raised PermissionError"
    except PermissionError as e:
        assert custom_msg in str(e)


@pytest.mark.unit
def test_base_repository_inheritance():
    """Test BaseRepository inherits from BaseRepositoryContract"""
    from repositories.base import BaseRepository
    from repositories.contracts import BaseRepositoryContract
    
    assert issubclass(BaseRepository, BaseRepositoryContract)


@pytest.mark.unit
def test_tenant_scoped_repository_inheritance():
    """Test TenantScopedRepository inherits from BaseRepository"""
    from repositories.base import TenantScopedRepository, BaseRepository
    
    assert issubclass(TenantScopedRepository, BaseRepository)
