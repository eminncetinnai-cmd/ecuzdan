"""
Unit Tests - User Repository
Repository for users, tenants and invites
"""

import pytest
from unittest.mock import Mock, patch
from repositories.user_repository import UserRepository


@pytest.mark.unit
def test_user_repository_init():
    """Test UserRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = UserRepository(database=mock_db)
    
    assert repo.session == mock_session


@pytest.mark.unit
def test_user_repository_imports():
    """Test that UserRepository can be imported"""
    from repositories.user_repository import UserRepository
    
    assert UserRepository is not None


@pytest.mark.unit
def test_user_repository_module_structure():
    """Test user_repository module structure"""
    import repositories.user_repository as user_repo_module
    
    # Check for expected class
    assert hasattr(user_repo_module, 'UserRepository')
    
    # Check for expected imports
    assert hasattr(user_repo_module, 'User')
    assert hasattr(user_repo_module, 'Tenant')
    assert hasattr(user_repo_module, 'TenantInvite')
    assert hasattr(user_repo_module, 'UserPreference')
    assert hasattr(user_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_user_repository_extends_base():
    """Test UserRepository extends BaseRepository"""
    from repositories.user_repository import UserRepository
    from repositories.base import BaseRepository
    
    assert issubclass(UserRepository, BaseRepository)


@pytest.mark.unit
def test_get_user():
    """Test get_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    
    repo = UserRepository(database=mock_db)
    repo.get = Mock(return_value=mock_user)
    
    result = repo.get_user(1)
    
    assert result == mock_user


@pytest.mark.unit
def test_list_users():
    """Test list_users method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_users = [Mock()]
    
    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query.all.return_value = mock_users
        
        repo = UserRepository(database=mock_db)
        
        result = repo.list_users()
        
        assert result == mock_users


@pytest.mark.unit
def test_list_users_for_tenant():
    """Test list_users_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_users = [Mock()]
    mock_query = Mock()
    
    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query.filter_by.return_value.order_by.return_value.all.return_value = mock_users
        
        repo = UserRepository(database=mock_db)
        
        result = repo.list_users_for_tenant('test_tenant')
        
        assert result == mock_users


@pytest.mark.unit
def test_count_users_for_tenant():
    """Test count_users_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query.filter_by.return_value.count.return_value = 5
        
        repo = UserRepository(database=mock_db)
        
        result = repo.count_users_for_tenant('test_tenant')
        
        assert result == 5


@pytest.mark.unit
def test_find_user_by_username():
    """Test find_user_by_username method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    
    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query.filter_by.return_value.first.return_value = mock_user
        
        repo = UserRepository(database=mock_db)
        
        result = repo.find_user_by_username('testuser')
        
        assert result == mock_user


@pytest.mark.unit
def test_find_user_by_oauth_id():
    """Test find_user_by_oauth_id method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    
    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query.filter_by.return_value.first.return_value = mock_user
        
        repo = UserRepository(database=mock_db)
        
        result = repo.find_user_by_oauth_id('google', '12345')
        
        assert result == mock_user


@pytest.mark.unit
def test_username_exists_true():
    """Test username_exists when username exists"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    
    repo = UserRepository(database=mock_db)
    repo.find_user_by_username = Mock(return_value=mock_user)
    
    result = repo.username_exists('testuser')
    
    assert result is True


@pytest.mark.unit
def test_username_exists_false():
    """Test username_exists when username does not exist"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = UserRepository(database=mock_db)
    repo.find_user_by_username = Mock(return_value=None)
    
    result = repo.username_exists('testuser')
    
    assert result is False


@pytest.mark.unit
def test_add_user():
    """Test add_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    
    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.return_value = mock_user
        
        repo = UserRepository(database=mock_db)
        repo.add = Mock(return_value=mock_user)
        
        result = repo.add_user(username='testuser', email='test@example.com')
        
        assert result == mock_user


@pytest.mark.unit
def test_get_tenant():
    """Test get_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_tenant = Mock()
    
    repo = UserRepository(database=mock_db)
    repo.get = Mock(return_value=mock_tenant)
    
    result = repo.get_tenant(1)
    
    assert result == mock_tenant


@pytest.mark.unit
def test_find_tenant():
    """Test find_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_tenant = Mock()
    
    with patch('repositories.user_repository.Tenant') as mock_tenant_class:
        mock_tenant_class.query.filter_by.return_value.first.return_value = mock_tenant
        
        repo = UserRepository(database=mock_db)
        
        result = repo.find_tenant('test_tenant')
        
        assert result == mock_tenant


@pytest.mark.unit
def test_get_user_with_preference():
    """Test get_user_with_preference method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    mock_query = Mock()
    
    with patch('repositories.user_repository.joinedload') as mock_joinedload:
        mock_joinedload.return_value = Mock()
        
        repo = UserRepository(database=mock_db)
        repo.session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_user
        
        result = repo.get_user_with_preference(1)
        
        assert result == mock_user


@pytest.mark.unit
def test_add_tenant():
    """Test add_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_tenant = Mock()
    
    with patch('repositories.user_repository.Tenant') as mock_tenant_class:
        mock_tenant_class.return_value = mock_tenant
        
        repo = UserRepository(database=mock_db)
        repo.add = Mock(return_value=mock_tenant)
        
        result = repo.add_tenant(name='Test Tenant')
        
        assert result == mock_tenant


@pytest.mark.unit
def test_find_invite():
    """Test find_invite method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_invite = Mock()
    
    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query.filter_by.return_value.first.return_value = mock_invite
        
        repo = UserRepository(database=mock_db)
        
        result = repo.find_invite('test_token')
        
        assert result == mock_invite


@pytest.mark.unit
def test_find_active_invite():
    """Test find_active_invite method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_invite = Mock()
    
    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query.filter_by.return_value.first.return_value = mock_invite
        
        repo = UserRepository(database=mock_db)
        
        result = repo.find_active_invite('test@example.com', 'test_tenant')
        
        assert result == mock_invite


@pytest.mark.unit
def test_list_invites():
    """Test list_invites method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_invites = [Mock()]
    mock_query = Mock()
    
    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query.filter_by.return_value.order_by.return_value.all.return_value = mock_invites
        
        repo = UserRepository(database=mock_db)
        
        result = repo.list_invites('test_tenant')
        
        assert result == mock_invites


@pytest.mark.unit
def test_list_invites_with_invited_by():
    """Test list_invites with invited_by filter"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_invites = [Mock()]
    mock_query = Mock()
    
    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query.filter_by.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_invites
        
        repo = UserRepository(database=mock_db)
        
        result = repo.list_invites('test_tenant', invited_by=1)
        
        assert result == mock_invites


@pytest.mark.unit
def test_add_invite():
    """Test add_invite method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_invite = Mock()
    
    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.return_value = mock_invite
        
        repo = UserRepository(database=mock_db)
        repo.add = Mock(return_value=mock_invite)
        
        result = repo.add_invite(email='test@example.com', tenant_id='test_tenant')
        
        assert result == mock_invite


@pytest.mark.unit
def test_delete_user():
    """Test delete_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_user = Mock()
    
    repo = UserRepository(database=mock_db)
    repo.delete = Mock()
    
    repo.delete_user(mock_user)
    
    repo.delete.assert_called_once_with(mock_user)


@pytest.mark.unit
def test_find_preference():
    """Test find_preference method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_preference = Mock()
    
    with patch('repositories.user_repository.UserPreference') as mock_pref_class:
        mock_pref_class.query.filter_by.return_value.first.return_value = mock_preference
        
        repo = UserRepository(database=mock_db)
        
        result = repo.find_preference(1)
        
        assert result == mock_preference


@pytest.mark.unit
def test_add_preference():
    """Test add_preference method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_preference = Mock()
    
    with patch('repositories.user_repository.UserPreference') as mock_pref_class:
        mock_pref_class.return_value = mock_preference
        
        repo = UserRepository(database=mock_db)
        repo.add = Mock(return_value=mock_preference)
        
        result = repo.add_preference(user_id=1, theme='dark')
        
        assert result == mock_preference


@pytest.mark.unit
def test_reset_financial_data_for_tenant():
    """Test reset_financial_data_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    
    with patch('repositories.user_repository.Transaction') as mock_tx_class:
        with patch('repositories.user_repository.RecurringPlan') as mock_plan_class:
            with patch('repositories.user_repository.Asset') as mock_asset_class:
                with patch('repositories.user_repository.AssetUpdate') as mock_update_class:
                    with patch('repositories.user_repository.AssetTransaction') as mock_tx_class2:
                        repo = UserRepository(database=mock_db)
                        repo.session.query.return_value.filter_by.return_value = mock_query
                        
                        repo.reset_financial_data_for_tenant('test_tenant')


@pytest.mark.unit
def test_reset_financial_data_for_tenant_empty_tenant_id():
    """Test reset_financial_data_for_tenant with empty tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = UserRepository(database=mock_db)
    
    try:
        repo.reset_financial_data_for_tenant('')
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "tenant_id boş olamaz" in str(e)


@pytest.mark.unit
def test_reset_financial_data_for_tenant_none_tenant_id():
    """Test reset_financial_data_for_tenant with None tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = UserRepository(database=mock_db)
    
    try:
        repo.reset_financial_data_for_tenant(None)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "tenant_id boş olamaz" in str(e)


@pytest.mark.unit
def test_reset_financial_data():
    """Test reset_financial_data method (global reset)"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.user_repository.Transaction') as mock_tx_class:
        with patch('repositories.user_repository.RecurringPlan') as mock_plan_class:
            with patch('repositories.user_repository.Asset') as mock_asset_class:
                with patch('repositories.user_repository.AssetUpdate') as mock_update_class:
                    repo = UserRepository(database=mock_db)
                    
                    repo.reset_financial_data()
