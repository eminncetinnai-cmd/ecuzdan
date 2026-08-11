"""
Unit Tests - Profile Repository
Investor profile repository tests
"""

import pytest
from unittest.mock import Mock, patch
from repositories.profile_repository import ProfileRepository


@pytest.mark.unit
def test_profile_repository_module_imports():
    """Test profile_repository module can be imported"""
    from repositories.profile_repository import ProfileRepository
    assert ProfileRepository is not None


@pytest.mark.unit
def test_profile_repository_module_structure():
    """Test profile_repository module structure"""
    import repositories.profile_repository as profile_module
    
    # Check for expected class
    assert hasattr(profile_module, 'ProfileRepository')


@pytest.mark.unit
def test_profile_repository_init():
    """Test ProfileRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    assert repo.db == mock_db
    assert repo.session == mock_session


@pytest.mark.unit
def test_profile_repository_inheritance():
    """Test ProfileRepository inherits from BaseRepository"""
    from repositories.profile_repository import ProfileRepository
    from repositories.base import BaseRepository
    
    assert issubclass(ProfileRepository, BaseRepository)


@pytest.mark.unit
def test_get_active_profile():
    """Test get_active_profile method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_profile = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_profile
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        result = repo.get_active_profile(tenant_id='test_tenant', user_id=1)
        
        assert result == mock_profile
        mock_query.filter_by.assert_called_once_with(
            tenant_id='test_tenant',
            user_id=1,
            is_active=True
        )


@pytest.mark.unit
def test_get_active_profile_not_found():
    """Test get_active_profile when profile not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = None
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        result = repo.get_active_profile(tenant_id='test_tenant', user_id=1)
        
        assert result is None


@pytest.mark.unit
def test_list_history():
    """Test list_history method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_profiles = [Mock(), Mock()]
    mock_query = Mock()
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = mock_profiles
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        result = repo.list_history(tenant_id='test_tenant', user_id=1)
        
        assert result == mock_profiles


@pytest.mark.unit
def test_list_history_with_limit():
    """Test list_history method with limit"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_profiles = [Mock()]
    mock_query = Mock()
    mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_profiles
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        result = repo.list_history(tenant_id='test_tenant', user_id=1, limit=10)
        
        assert result == mock_profiles
        mock_query.filter_by.return_value.order_by.return_value.limit.assert_called_once_with(10)


@pytest.mark.unit
def test_deactivate_active_profiles():
    """Test deactivate_active_profiles method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_query = Mock()
    mock_query.filter_by.return_value.update.return_value = None
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        repo.deactivate_active_profiles(tenant_id='test_tenant', user_id=1)
        
        mock_query.filter_by.assert_called_once_with(
            tenant_id='test_tenant',
            user_id=1,
            is_active=True
        )
        mock_query.filter_by.return_value.update.assert_called_once_with({'is_active': False})


@pytest.mark.unit
def test_add_profile():
    """Test add_profile method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    repo.add = Mock(return_value=Mock())
    
    mock_profile = Mock()
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.return_value = mock_profile
        repo.add.return_value = mock_profile
        
        result = repo.add_profile(tenant_id='test_tenant', user_id=1, risk_level='Moderate')
        
        assert result == mock_profile
        mock_profile_class.assert_called_once_with(tenant_id='test_tenant', user_id=1, risk_level='Moderate')
        repo.add.assert_called_once_with(mock_profile)


@pytest.mark.unit
def test_add_answer():
    """Test add_answer method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    repo.add = Mock(return_value=Mock())
    
    mock_answer = Mock()
    
    with patch('repositories.profile_repository.InvestorProfileAnswer') as mock_answer_class:
        mock_answer_class.return_value = mock_answer
        repo.add.return_value = mock_answer
        
        result = repo.add_answer(profile_id=1, question_id=1, answer='Yes')
        
        assert result == mock_answer
        mock_answer_class.assert_called_once_with(profile_id=1, question_id=1, answer='Yes')
        repo.add.assert_called_once_with(mock_answer)


@pytest.mark.unit
def test_get_profile():
    """Test get_profile method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_profile = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_profile
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        result = repo.get_profile(profile_id=1, tenant_id='test_tenant')
        
        assert result == mock_profile
        mock_query.filter_by.assert_called_once_with(id=1, tenant_id='test_tenant')


@pytest.mark.unit
def test_get_profile_not_found():
    """Test get_profile when profile not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = None
    
    with patch('repositories.profile_repository.InvestorProfile') as mock_profile_class:
        mock_profile_class.query = mock_query
        
        result = repo.get_profile(profile_id=1, tenant_id='test_tenant')
        
        assert result is None


@pytest.mark.unit
def test_list_answers():
    """Test list_answers method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_answers = [Mock(), Mock()]
    mock_query = Mock()
    mock_query.filter_by.return_value.all.return_value = mock_answers
    
    with patch('repositories.profile_repository.InvestorProfileAnswer') as mock_answer_class:
        mock_answer_class.query = mock_query
        
        result = repo.list_answers(profile_id=1)
        
        assert result == mock_answers
        mock_query.filter_by.assert_called_once_with(profile_id=1)


@pytest.mark.unit
def test_list_answers_empty():
    """Test list_answers when no answers"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = ProfileRepository(database=mock_db)
    
    mock_query = Mock()
    mock_query.filter_by.return_value.all.return_value = []
    
    with patch('repositories.profile_repository.InvestorProfileAnswer') as mock_answer_class:
        mock_answer_class.query = mock_query
        
        result = repo.list_answers(profile_id=1)
        
        assert result == []


@pytest.mark.unit
def test_profile_repository_has_required_methods():
    """Test ProfileRepository has required methods"""
    from repositories.profile_repository import ProfileRepository
    
    repo = ProfileRepository(database=Mock())
    
    assert hasattr(repo, 'get_active_profile')
    assert hasattr(repo, 'list_history')
    assert hasattr(repo, 'deactivate_active_profiles')
    assert hasattr(repo, 'add_profile')
    assert hasattr(repo, 'add_answer')
    assert hasattr(repo, 'get_profile')
    assert hasattr(repo, 'list_answers')
    
    assert callable(repo.get_active_profile)
    assert callable(repo.list_history)
    assert callable(repo.deactivate_active_profiles)
    assert callable(repo.add_profile)
    assert callable(repo.add_answer)
    assert callable(repo.get_profile)
    assert callable(repo.list_answers)
