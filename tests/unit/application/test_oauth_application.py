"""
Unit tests for OAuth application service
"""

from unittest.mock import Mock, patch

import pytest

from application.users.oauth_application_service import OAuthApplicationService
from application.users.ports.oauth_provider import OAuthProvider, OAuthUserInfoDto


@pytest.mark.unit
class TestOAuthApplicationService:
    """Test OAuthApplicationService"""

    def test_initialization(self):
        """Test service initialization"""
        mock_provider = Mock(spec=OAuthProvider)
        mock_event_bus = Mock()

        service = OAuthApplicationService(
            oauth_provider=mock_provider,
            event_bus=mock_event_bus
        )

        assert service.provider == mock_provider
        assert service.event_bus == mock_event_bus

    def test_initialization_without_event_bus(self):
        """Test service initialization without event bus"""
        mock_provider = Mock(spec=OAuthProvider)

        service = OAuthApplicationService(
            oauth_provider=mock_provider,
            event_bus=None
        )

        assert service.provider == mock_provider
        assert service.event_bus is None

    @patch('application.users.oauth_application_service.db')
    def test_verify_and_login_new_user(self, mock_db):
        """Test verify_and_login with new user"""
        mock_provider = Mock(spec=OAuthProvider)
        mock_provider.exchange_code_for_token.return_value = {'access_token': 'test_token'}
        mock_provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            given_name='Test',
            family_name='User',
            avatar_url='https://avatar.url',
            provider_id='google_123',
            provider='google',
            email_verified=True
        )
        mock_event_bus = Mock()

        service = OAuthApplicationService(
            oauth_provider=mock_provider,
            event_bus=mock_event_bus
        )

        # Mock User.query to return None (no existing user)
        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_user_model.query.filter_by.return_value.first.return_value = None

            # Mock Tenant creation
            mock_tenant = Mock()
            mock_tenant.id = 'tenant_test'

            mock_user_instance = Mock()
            mock_user_instance.id = 1
            mock_user_instance.username = 'test@example.com'
            mock_user_instance.tenant_id = 'tenant_test'
            mock_user_model.return_value = mock_user_instance

            result = service.verify_and_login('code123', 'https://callback')

            assert result == mock_user_instance
            mock_provider.exchange_code_for_token.assert_called_once_with('code123', 'https://callback')
            mock_provider.verify_token_and_get_user_info.assert_called_once_with('test_token')
            mock_db.session.add.assert_called()
            mock_db.session.commit.assert_called_once()
            mock_event_bus.publish.assert_called_once()

    @patch('application.users.oauth_application_service.db')
    def test_verify_and_login_existing_user(self, mock_db):
        """Test verify_and_login with existing user"""
        mock_provider = Mock(spec=OAuthProvider)
        mock_provider.exchange_code_for_token.return_value = {'access_token': 'test_token'}
        mock_provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            given_name='Test',
            family_name='User',
            avatar_url='https://avatar.url',
            provider_id='google_123',
            provider='google',
            email_verified=True
        )
        mock_event_bus = Mock()

        service = OAuthApplicationService(
            oauth_provider=mock_provider,
            event_bus=mock_event_bus
        )

        # Mock User.query to return existing user
        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_existing_user = Mock()
            mock_existing_user.id = 1
            mock_existing_user.oauth_id = None
            mock_existing_user.auth_provider = 'LOCAL'
            mock_user_model.query.filter_by.return_value.first.return_value = mock_existing_user

            result = service.verify_and_login('code123', 'https://callback')

            assert result == mock_existing_user
            assert mock_existing_user.oauth_id == 'google_123'
            assert mock_existing_user.auth_provider == 'GOOGLE'
            mock_db.session.commit.assert_called_once()
            mock_event_bus.publish.assert_called()

    def test_verify_and_login_no_access_token(self):
        """Test verify_and_login when no access token is returned"""
        mock_provider = Mock(spec=OAuthProvider)
        mock_provider.exchange_code_for_token.return_value = {}
        mock_event_bus = Mock()

        service = OAuthApplicationService(
            oauth_provider=mock_provider,
            event_bus=mock_event_bus
        )

        with pytest.raises(ValueError, match="OAuth token alınamadı"):
            service.verify_and_login('code123', 'https://callback')

    @patch('application.users.oauth_application_service.db')
    def test_verify_and_login_unverified_email(self, mock_db):
        """Test verify_and_login with unverified email"""
        mock_provider = Mock(spec=OAuthProvider)
        mock_provider.exchange_code_for_token.return_value = {'access_token': 'test_token'}
        mock_provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            email_verified=False
        )
        mock_event_bus = Mock()

        service = OAuthApplicationService(
            oauth_provider=mock_provider,
            event_bus=mock_event_bus
        )

        with pytest.raises(ValueError, match="e-posta adresi doğrulanmamış"):
            service.verify_and_login('code123', 'https://callback')

    @patch('application.users.oauth_application_service.db')
    def test_create_tenant_for_user(self, mock_db):
        """Test _create_tenant_for_user method"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider)

        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User'
        )

        with patch('application.users.oauth_application_service.Tenant') as mock_tenant_model:
            mock_tenant = Mock()
            mock_tenant.id = 'tenant_test'
            mock_tenant_model.return_value = mock_tenant

            result = service._create_tenant_for_user(user_info)

            assert result == mock_tenant
            mock_db.session.add.assert_called_with(mock_tenant)

    @patch('application.users.oauth_application_service.db')
    def test_update_user_metadata(self, mock_db):
        """Test _update_user_metadata method"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider)

        mock_user = Mock()
        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            avatar_url='https://avatar.url',
            email_verified=True
        )

        service._update_user_metadata(mock_user, user_info)

        assert mock_user.last_login_at is not None
        assert mock_user.avatar_url == 'https://avatar.url'
        assert mock_user.email_verified is True

    @patch('application.users.oauth_application_service.db')
    def test_update_user_metadata_without_avatar(self, mock_db):
        """Test _update_user_metadata without avatar URL"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider)

        mock_user = Mock()
        mock_user.avatar_url = 'existing_avatar'
        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            avatar_url=None,
            email_verified=True
        )

        service._update_user_metadata(mock_user, user_info)

        assert mock_user.last_login_at is not None
        # Avatar should not be updated if not provided
        assert mock_user.avatar_url == 'existing_avatar'
        assert mock_user.email_verified is True

    @patch('application.users.oauth_application_service.db')
    def test_find_or_create_user_existing_with_oauth_already_linked(self, mock_db):
        """Test _find_or_create_user when existing user already has OAuth linked"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider)

        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            provider_id='google_123',
            provider='google'
        )

        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_existing_user = Mock()
            mock_existing_user.id = 1
            mock_existing_user.oauth_id = 'google_456'  # Already has different OAuth ID
            mock_existing_user.auth_provider = 'GOOGLE'
            mock_user_model.query.filter_by.return_value.first.return_value = mock_existing_user

            result = service._find_or_create_user(user_info)

            # Should not update OAuth fields if already set
            assert result == mock_existing_user
            assert mock_existing_user.oauth_id == 'google_456'  # Should not change

    @patch('application.users.oauth_application_service.db')
    def test_find_or_create_user_existing_without_event_bus(self, mock_db):
        """Test _find_or_create_user without event bus"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider, event_bus=None)

        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            provider_id='google_123',
            provider='google'
        )

        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_existing_user = Mock()
            mock_existing_user.id = 1
            mock_existing_user.oauth_id = None
            mock_existing_user.auth_provider = 'LOCAL'
            mock_user_model.query.filter_by.return_value.first.return_value = mock_existing_user

            result = service._find_or_create_user(user_info)

            assert result == mock_existing_user
            assert mock_existing_user.oauth_id == 'google_123'
            assert mock_existing_user.auth_provider == 'GOOGLE'

    @patch('application.users.oauth_application_service.db')
    def test_verify_and_login_without_event_bus(self, mock_db):
        """Test verify_and_login without event bus"""
        mock_provider = Mock(spec=OAuthProvider)
        mock_provider.exchange_code_for_token.return_value = {'access_token': 'test_token'}
        mock_provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            provider_id='google_123',
            provider='google',
            email_verified=True
        )

        service = OAuthApplicationService(oauth_provider=mock_provider, event_bus=None)

        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_user_model.query.filter_by.return_value.first.return_value = None

            mock_tenant = Mock()
            mock_tenant.id = 'tenant_test'

            mock_user_instance = Mock()
            mock_user_instance.id = 1
            mock_user_instance.username = 'test@example.com'
            mock_user_instance.tenant_id = 'tenant_test'
            mock_user_model.return_value = mock_user_instance

            with patch('application.users.oauth_application_service.Tenant') as mock_tenant_model:
                mock_tenant_model.return_value = mock_tenant

                result = service.verify_and_login('code123', 'https://callback')

                assert result == mock_user_instance
                mock_db.session.commit.assert_called_once()

    @patch('application.users.oauth_application_service.db')
    def test_find_or_create_user_existing_auth_provider_not_local(self, mock_db):
        """Test _find_or_create_user when existing user has non-LOCAL auth provider"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider)

        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            provider_id='google_123',
            provider='google'
        )

        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_existing_user = Mock()
            mock_existing_user.id = 1
            mock_existing_user.oauth_id = None
            mock_existing_user.auth_provider = 'APPLE'  # Different provider
            mock_user_model.query.filter_by.return_value.first.return_value = mock_existing_user

            result = service._find_or_create_user(user_info)

            assert result == mock_existing_user
            assert mock_existing_user.oauth_id == 'google_123'
            # Should NOT update auth_provider if it's already set to non-LOCAL
            assert mock_existing_user.auth_provider == 'APPLE'

    @patch('application.users.oauth_application_service.db')
    def test_find_or_create_user_new_user_calls_user_constructor(self, mock_db):
        """Test that User constructor is called when creating new user"""
        mock_provider = Mock(spec=OAuthProvider)
        service = OAuthApplicationService(oauth_provider=mock_provider)

        user_info = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            provider_id='google_123',
            provider='google',
            avatar_url='https://avatar.url',
            email_verified=True
        )

        with patch('application.users.oauth_application_service.User') as mock_user_model:
            mock_user_model.query.filter_by.return_value.first.return_value = None

            mock_tenant = Mock()
            mock_tenant.id = 'tenant_test'

            # Make User constructor return a mock instance
            mock_user_instance = Mock()
            mock_user_instance.id = 1
            mock_user_model.return_value = mock_user_instance

            with patch('application.users.oauth_application_service.Tenant') as mock_tenant_model:
                mock_tenant_model.return_value = mock_tenant

                result = service._find_or_create_user(user_info)

                # Verify User constructor was called with correct arguments
                mock_user_model.assert_called_once_with(
                    username='test@example.com',
                    password=None,
                    auth_provider='GOOGLE',
                    oauth_id='google_123',
                    avatar_url='https://avatar.url',
                    email_verified=True,
                    created_via='oauth',
                    role='kullanici',
                    language='tr',
                    tenant_id='tenant_test'
                )
                assert result == mock_user_instance
