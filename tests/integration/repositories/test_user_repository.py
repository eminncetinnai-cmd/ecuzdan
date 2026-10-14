"""
Unit Tests - User Repository
User, tenant and invite repository tests
"""

from unittest.mock import Mock, patch

import pytest

from repositories.user_repository import UserRepository


@pytest.mark.unit
def test_user_repository_module_imports():
    """Test user_repository module can be imported"""
    from repositories.user_repository import UserRepository
    assert UserRepository is not None


@pytest.mark.unit
def test_user_repository_module_structure():
    """Test user_repository module structure"""
    import repositories.user_repository as user_module

    # Check for expected class
    assert hasattr(user_module, 'UserRepository')


@pytest.mark.unit
def test_user_repository_init():
    """Test UserRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    assert repo.db == mock_db
    assert repo.session == mock_session


@pytest.mark.unit
def test_user_repository_inheritance():
    """Test UserRepository inherits from BaseRepository"""
    from repositories.base import BaseRepository
    from repositories.user_repository import UserRepository

    assert issubclass(UserRepository, BaseRepository)


@pytest.mark.unit
def test_get_user():
    """Test get_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.get = Mock()

    mock_user = Mock()
    repo.get.return_value = mock_user

    result = repo.get_user(user_id=1)

    assert result == mock_user
    repo.get.assert_called_once()


@pytest.mark.unit
def test_list_users():
    """Test list_users method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_users = [Mock(), Mock()]

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query.all.return_value = mock_users

        result = repo.list_users()

        assert result == mock_users


@pytest.mark.unit
def test_list_users_for_tenant():
    """Test list_users_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_users = [Mock()]
    mock_query = Mock()
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = mock_users

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query = mock_query

        result = repo.list_users_for_tenant(tenant_id='test_tenant')

        assert result == mock_users
        mock_query.filter_by.assert_called_once_with(tenant_id='test_tenant')


@pytest.mark.unit
def test_count_users_for_tenant():
    """Test count_users_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_query = Mock()
    mock_query.filter_by.return_value.count.return_value = 5

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query = mock_query

        result = repo.count_users_for_tenant(tenant_id='test_tenant')

        assert result == 5
        mock_query.filter_by.assert_called_once_with(tenant_id='test_tenant')


@pytest.mark.unit
def test_find_user_by_username():
    """Test find_user_by_username method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_user = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_user

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query = mock_query

        result = repo.find_user_by_username(username='testuser')

        assert result == mock_user
        mock_query.filter_by.assert_called_once_with(username='testuser')


@pytest.mark.unit
def test_find_user_by_username_not_found():
    """Test find_user_by_username when user not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = None

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query = mock_query

        result = repo.find_user_by_username(username='testuser')

        assert result is None


@pytest.mark.unit
def test_find_user_by_oauth_id():
    """Test find_user_by_oauth_id method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_user = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_user

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.query = mock_query

        result = repo.find_user_by_oauth_id(provider='google', oauth_id='12345')

        assert result == mock_user
        mock_query.filter_by.assert_called_once_with(auth_provider='google', oauth_id='12345')


@pytest.mark.unit
def test_username_exists():
    """Test username_exists method when username exists"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.find_user_by_username = Mock(return_value=Mock())

    result = repo.username_exists(username='testuser')

    assert result is True


@pytest.mark.unit
def test_username_exists_not():
    """Test username_exists method when username does not exist"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.find_user_by_username = Mock(return_value=None)

    result = repo.username_exists(username='testuser')

    assert result is False


@pytest.mark.unit
def test_add_user():
    """Test add_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.add = Mock(return_value=Mock())

    mock_user = Mock()

    with patch('repositories.user_repository.User') as mock_user_class:
        mock_user_class.return_value = mock_user
        repo.add.return_value = mock_user

        result = repo.add_user(username='testuser', email='test@example.com')

        assert result == mock_user
        mock_user_class.assert_called_once_with(username='testuser', email='test@example.com')
        repo.add.assert_called_once_with(mock_user)


@pytest.mark.unit
def test_get_tenant():
    """Test get_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.get = Mock()

    mock_tenant = Mock()
    repo.get.return_value = mock_tenant

    result = repo.get_tenant(tenant_id='test_tenant')

    assert result == mock_tenant
    repo.get.assert_called_once()


@pytest.mark.unit
def test_find_tenant():
    """Test find_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_tenant = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_tenant

    with patch('repositories.user_repository.Tenant') as mock_tenant_class:
        mock_tenant_class.query = mock_query

        result = repo.find_tenant(tenant_id='test_tenant')

        assert result == mock_tenant
        mock_query.filter_by.assert_called_once_with(id='test_tenant')


@pytest.mark.integration
def test_get_user_with_preference(app, test_user):
    """Joined loading returns the user, tenant and preference in one repository call."""
    from models import UserPreference, db

    with app.app_context():
        db.session.add(UserPreference(user_id=test_user.id, theme='dark'))
        db.session.commit()

        result = UserRepository(database=db).get_user_with_preference(test_user.id)

    assert result.id == test_user.id
    assert result.tenant.id == 'default'
    assert result.preference.theme == 'dark'


@pytest.mark.unit
def test_add_tenant():
    """Test add_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.add = Mock(return_value=Mock())

    mock_tenant = Mock()

    with patch('repositories.user_repository.Tenant') as mock_tenant_class:
        mock_tenant_class.return_value = mock_tenant
        repo.add.return_value = mock_tenant

        result = repo.add_tenant(name='Test Tenant')

        assert result == mock_tenant
        mock_tenant_class.assert_called_once_with(name='Test Tenant')
        repo.add.assert_called_once_with(mock_tenant)


@pytest.mark.unit
def test_find_invite():
    """Test find_invite method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_invite = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_invite

    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query = mock_query

        result = repo.find_invite(token='test_token')

        assert result == mock_invite
        mock_query.filter_by.assert_called_once_with(token='test_token')


@pytest.mark.unit
def test_find_active_invite():
    """Test find_active_invite method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_invite = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_invite

    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query = mock_query

        result = repo.find_active_invite(email='test@example.com', tenant_id='test_tenant')

        assert result == mock_invite
        mock_query.filter_by.assert_called_once_with(email='test@example.com', tenant_id='test_tenant', used_at=None)


@pytest.mark.unit
def test_list_invites():
    """Test list_invites method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_invites = [Mock(), Mock()]
    mock_query = Mock()
    mock_query.filter_by.return_value.order_by.return_value.all.return_value = mock_invites

    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query = mock_query

        result = repo.list_invites(tenant_id='test_tenant')

        assert result == mock_invites
        mock_query.filter_by.assert_called_once_with(tenant_id='test_tenant')


@pytest.mark.unit
def test_list_invites_with_invited_by():
    """Test list_invites method with invited_by filter"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_invites = [Mock()]
    mock_query = Mock()
    mock_query.filter_by.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_invites

    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.query = mock_query

        result = repo.list_invites(tenant_id='test_tenant', invited_by=1)

        assert result == mock_invites


@pytest.mark.unit
def test_add_invite():
    """Test add_invite method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.add = Mock(return_value=Mock())

    mock_invite = Mock()

    with patch('repositories.user_repository.TenantInvite') as mock_invite_class:
        mock_invite_class.return_value = mock_invite
        repo.add.return_value = mock_invite

        result = repo.add_invite(email='test@example.com', tenant_id='test_tenant')

        assert result == mock_invite
        mock_invite_class.assert_called_once_with(email='test@example.com', tenant_id='test_tenant')
        repo.add.assert_called_once_with(mock_invite)


@pytest.mark.unit
def test_delete_user():
    """Test delete_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.delete = Mock()

    mock_user = Mock()

    repo.delete_user(mock_user)

    repo.delete.assert_called_once_with(mock_user)


@pytest.mark.unit
def test_find_preference():
    """Test find_preference method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_preference = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_preference

    with patch('repositories.user_repository.UserPreference') as mock_pref_class:
        mock_pref_class.query = mock_query

        result = repo.find_preference(user_id=1)

        assert result == mock_preference
        mock_query.filter_by.assert_called_once_with(user_id=1)


@pytest.mark.unit
def test_find_preference_not_found():
    """Test find_preference when not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = None

    with patch('repositories.user_repository.UserPreference') as mock_pref_class:
        mock_pref_class.query = mock_query

        result = repo.find_preference(user_id=1)

        assert result is None


@pytest.mark.unit
def test_add_preference():
    """Test add_preference method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)
    repo.add = Mock(return_value=Mock())

    mock_preference = Mock()

    with patch('repositories.user_repository.UserPreference') as mock_pref_class:
        mock_pref_class.return_value = mock_preference
        repo.add.return_value = mock_preference

        result = repo.add_preference(user_id=1, language='tr')

        assert result == mock_preference
        mock_pref_class.assert_called_once_with(user_id=1, language='tr')
        repo.add.assert_called_once_with(mock_preference)


@pytest.mark.unit
def test_reset_financial_data_for_tenant():
    """Test reset_financial_data_for_tenant method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    mock_query = Mock()
    mock_query.filter_by.return_value.delete.return_value = None
    mock_asset_ids_query = Mock()
    mock_asset_ids_query.filter_by.return_value = mock_asset_ids_query

    with patch('repositories.user_repository.Transaction') as mock_tx_class:
        mock_tx_class.query.filter_by.return_value.delete.return_value = None

        with patch('repositories.user_repository.RecurringPlan') as mock_rp_class:
            mock_rp_class.query.filter_by.return_value.delete.return_value = None

            with patch('repositories.user_repository.Asset') as mock_asset_class:
                mock_asset_class.query.filter_by.return_value = mock_asset_ids_query

                with patch('repositories.user_repository.AssetUpdate') as mock_au_class:
                    mock_au_class.query.filter.return_value.delete.return_value = None

                    with patch('repositories.user_repository.AssetTransaction') as mock_at_class:
                        mock_at_class.query.filter.return_value.delete.return_value = None

                        repo.reset_financial_data_for_tenant(tenant_id='test_tenant')


@pytest.mark.unit
def test_reset_financial_data_for_tenant_empty_tenant_id():
    """Test reset_financial_data_for_tenant with empty tenant_id raises error"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    try:
        repo.reset_financial_data_for_tenant(tenant_id='')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "tenant_id boş olamaz" in str(e)


@pytest.mark.unit
def test_reset_financial_data_for_tenant_none_tenant_id():
    """Test reset_financial_data_for_tenant with None tenant_id raises error"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = UserRepository(database=mock_db)

    try:
        repo.reset_financial_data_for_tenant(tenant_id=None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "tenant_id boş olamaz" in str(e)


@pytest.mark.integration
def test_reset_financial_data(app, test_transaction):
    """Global reset is safe to verify because the app fixture uses an isolated database."""
    from models import Transaction, db

    with app.app_context():
        assert Transaction.query.count() == 1
        UserRepository(database=db).reset_financial_data()
        db.session.commit()
        assert Transaction.query.count() == 0


@pytest.mark.unit
def test_user_repository_has_required_methods():
    """Test UserRepository has required methods"""
    from repositories.user_repository import UserRepository

    repo = UserRepository(database=Mock())

    methods = [
        'get_user', 'list_users', 'list_users_for_tenant', 'count_users_for_tenant',
        'find_user_by_username', 'find_user_by_oauth_id', 'username_exists',
        'add_user', 'get_tenant', 'find_tenant', 'get_user_with_preference',
        'add_tenant', 'find_invite', 'find_active_invite', 'list_invites',
        'add_invite', 'delete_user', 'find_preference', 'add_preference',
        'reset_financial_data_for_tenant', 'reset_financial_data'
    ]

    for method in methods:
        assert hasattr(repo, method), f"Missing method: {method}"
        assert callable(getattr(repo, method)), f"Method not callable: {method}"
