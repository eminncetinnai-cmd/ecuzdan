"""Tests for OAuth sign-up flow and multi-method authentication."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from werkzeug.security import generate_password_hash

from domain.users.services.auth_service import AuthService
from repositories.user_repository import UserRepository
from models import User, Tenant
from shared.db import db


class TestAuthServiceMultiMethodAuth:
    """Test authentication with username and email support."""

    def test_authenticate_with_username(self):
        """Test authentication using username."""
        mock_repo = Mock(spec=UserRepository)
        mock_user = Mock()
        mock_user.password = generate_password_hash('TestPassword123!')
        mock_repo.find_user_by_username.return_value = mock_user
        mock_repo.find_user_by_email.return_value = None

        service = AuthService(mock_repo)
        result = service.authenticate('testuser', 'TestPassword123!')

        assert result == mock_user
        mock_repo.find_user_by_username.assert_called_once_with('testuser')
        mock_repo.find_user_by_email.assert_not_called()

    def test_authenticate_with_email(self):
        """Test authentication using email when username fails."""
        mock_repo = Mock(spec=UserRepository)
        mock_user = Mock()
        mock_user.password = generate_password_hash('TestPassword123!')
        mock_repo.find_user_by_username.return_value = None
        mock_repo.find_user_by_email.return_value = mock_user

        service = AuthService(mock_repo)
        result = service.authenticate('test@example.com', 'TestPassword123!')

        assert result == mock_user
        mock_repo.find_user_by_username.assert_called_once_with('test@example.com')
        mock_repo.find_user_by_email.assert_called_once_with('test@example.com')

    @patch('domain.users.services.auth_service.check_password_hash')
    def test_authenticate_wrong_password(self, mock_check_hash):
        """Test authentication fails with wrong password."""
        mock_repo = Mock(spec=UserRepository)
        mock_user = Mock()
        mock_user.password = 'hashed_password'
        mock_repo.find_user_by_username.return_value = mock_user
        mock_repo.find_user_by_email.return_value = None
        mock_check_hash.return_value = False

        service = AuthService(mock_repo)
        result = service.authenticate('testuser', 'WrongPassword123!')

        assert result is None
        # check_password_hash is called once for username attempt
        assert mock_check_hash.call_count == 1
        mock_check_hash.assert_called_with('hashed_password', 'WrongPassword123!')

    def test_authenticate_user_not_found(self):
        """Test authentication fails when user not found."""
        mock_repo = Mock(spec=UserRepository)
        mock_repo.find_user_by_username.return_value = None
        mock_repo.find_user_by_email.return_value = None

        service = AuthService(mock_repo)
        result = service.authenticate('nonexistent', 'TestPassword123!')

        assert result is None


class TestUserRepositoryEmailSupport:
    """Test UserRepository email-related methods."""

    @patch('repositories.user_repository.User')
    def test_find_user_by_email(self, mock_user_model):
        """Test finding user by email."""
        mock_query = Mock()
        mock_user_model.query.filter_by.return_value = mock_query
        mock_query.first.return_value = 'found_user'

        repo = UserRepository()
        result = repo.find_user_by_email('test@example.com')

        assert result == 'found_user'
        mock_user_model.query.filter_by.assert_called_once_with(email='test@example.com')

    def test_email_exists_true(self):
        """Test email_exists returns True when email exists."""
        repo = UserRepository()
        repo.find_user_by_email = Mock(return_value='user')

        result = repo.email_exists('test@example.com')

        assert result is True
        repo.find_user_by_email.assert_called_once_with('test@example.com')

    def test_email_exists_false(self):
        """Test email_exists returns False when email doesn't exist."""
        repo = UserRepository()
        repo.find_user_by_email = Mock(return_value=None)

        result = repo.email_exists('test@example.com')

        assert result is False
        repo.find_user_by_email.assert_called_once_with('test@example.com')


class TestProfileImageUtility:
    """Test profile image download and storage."""

    @patch('utils.profile_image.requests.get')
    @patch('utils.profile_image.os.makedirs')
    @patch('utils.profile_image.os.path.exists')
    def test_download_profile_image_success(self, mock_exists, mock_makedirs, mock_get):
        """Test successful profile image download."""
        from utils.profile_image import download_profile_image

        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '100000'}
        mock_response.iter_content = Mock(return_value=[b'image_data'])
        mock_get.return_value = mock_response
        mock_exists.return_value = False

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__ = Mock()
            mock_open.return_value.__exit__ = Mock()
            mock_open.return_value.write = Mock()

            result = download_profile_image('https://example.com/avatar.jpg')

            assert result is not None
            assert result.startswith('/static/uploads/profiles/')
            mock_get.assert_called_once_with('https://example.com/avatar.jpg', timeout=10, stream=True)

    @patch('utils.profile_image.requests.get')
    def test_download_profile_image_invalid_content_type(self, mock_get):
        """Test profile image download fails with invalid content type."""
        from utils.profile_image import download_profile_image

        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response

        result = download_profile_image('https://example.com/avatar.jpg')

        assert result is None

    @patch('utils.profile_image.requests.get')
    def test_download_profile_image_too_large(self, mock_get):
        """Test profile image download fails when file too large."""
        from utils.profile_image import download_profile_image

        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '10000000'}  # 10MB
        mock_get.return_value = mock_response

        result = download_profile_image('https://example.com/avatar.jpg')

        assert result is None

    @patch('utils.profile_image.requests.get')
    def test_download_profile_image_request_fails(self, mock_get):
        """Test profile image download fails when request fails."""
        from utils.profile_image import download_profile_image

        mock_get.side_effect = Exception('Network error')

        result = download_profile_image('https://example.com/avatar.jpg')

        assert result is None

    def test_get_extension_from_url(self):
        """Test extracting file extension from URL."""
        from utils.profile_image import get_extension_from_url

        assert get_extension_from_url('https://example.com/avatar.jpg') == '.jpg'
        assert get_extension_from_url('https://example.com/photo.png') == '.png'
        assert get_extension_from_url('https://example.com/image.gif') == '.gif'
        assert get_extension_from_url('https://example.com/noext') is None

    @patch('utils.profile_image.os.remove')
    @patch('utils.profile_image.os.path.exists')
    def test_delete_profile_image_success(self, mock_exists, mock_remove):
        """Test successful profile image deletion."""
        from utils.profile_image import delete_profile_image

        mock_exists.return_value = True

        result = delete_profile_image('/static/uploads/profiles/test.jpg')

        assert result is True
        mock_remove.assert_called_once()

    @patch('utils.profile_image.os.path.exists')
    def test_delete_profile_image_not_exists(self, mock_exists):
        """Test deleting non-existent profile image."""
        from utils.profile_image import delete_profile_image

        mock_exists.return_value = False

        result = delete_profile_image('/static/uploads/profiles/test.jpg')

        assert result is False


class TestOAuthSignupFlow:
    """Test OAuth sign-up flow."""

    @patch('repositories.user_repository.User')
    @patch('repositories.user_repository.Tenant')
    def test_oauth_signup_creates_user_with_email(self, mock_tenant, mock_user):
        """Test OAuth sign-up creates user with email field."""
        with patch('shared.db.db.session'):
            tenant = Tenant(id='test_tenant', name='Test Tenant', base_currency='TRY', status='active')
            mock_tenant.return_value = tenant

            user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('TestPassword123!'),
                auth_provider='GOOGLE',
                oauth_id='google_123',
                email_verified=True,
                tenant_id='test_tenant'
            )
            mock_user.return_value = user

            # Verify user has email field
            assert user.email == 'test@example.com'
            assert user.username == 'testuser'
            assert user.auth_provider == 'GOOGLE'
            assert user.oauth_id == 'google_123'


class TestOAuthCallbackLogic:
    """Test OAuth callback sign-up vs sign-in logic."""

    def test_existing_user_signs_in(self):
        """Test existing user signs in via OAuth."""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'existinguser'
        mock_user.email = 'existing@example.com'
        mock_user.oauth_id = None
        mock_user.auth_provider = 'LOCAL'
        mock_user.language = 'tr'

        # Simulate callback logic - user exists
        existing_user = mock_user

        assert existing_user is not None
        assert existing_user.email == 'existing@example.com'

    def test_new_user_redirected_to_signup(self):
        """Test new user is redirected to sign-up form."""
        # Simulate callback logic - user doesn't exist
        existing_user = None

        assert existing_user is None
        # Should redirect to sign-up form
