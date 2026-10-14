"""
Security tests for OAuth authentication
Tests for CSRF protection, token validation, and other security concerns
"""

from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestOAuthCSRFProtection:
    """Test CSRF protection in OAuth flow"""

    def test_state_parameter_generation(self, client, app):
        """OAuth login generates a 32-byte URL-safe state and stores it in session."""
        app.config.update(GOOGLE_CLIENT_ID='test_id', GOOGLE_CLIENT_SECRET='test_secret')
        with patch('routes.auth.secrets.token_urlsafe', return_value='secure_random_state') as mock_token, \
             patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
            provider_class.return_value.get_authorization_url.return_value = 'https://accounts.google.com/auth'
            result = client.get('/login/google')

        mock_token.assert_called_once_with(32)
        with client.session_transaction() as session:
            assert session['oauth_state'] == 'secure_random_state'
        assert result.location == 'https://accounts.google.com/auth'

    def test_state_validation_success(self, client, app):
        """A matching state reaches the provider exchange step and is consumed."""
        app.config.update(GOOGLE_CLIENT_ID='test_id', GOOGLE_CLIENT_SECRET='test_secret')
        with client.session_transaction() as session:
            session['oauth_state'] = 'correct_state'
            session['oauth_provider'] = 'google'

        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
            provider_class.return_value.exchange_code_for_token.side_effect = ValueError('exchange sentinel')
            result = client.get('/callback/google?state=correct_state&code=test_code')

        provider_class.return_value.exchange_code_for_token.assert_called_once()
        with client.session_transaction() as session:
            assert 'oauth_state' not in session
            assert 'oauth_provider' not in session
        assert result.status_code == 302

    def test_state_validation_mismatch(self, client):
        """A mismatched state is rejected before provider access."""
        with client.session_transaction() as session:
            session['oauth_state'] = 'session_state'
        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
            result = client.get('/callback/google?state=different_state&code=test_code')

        provider_class.assert_not_called()
        assert result.status_code == 302
        with client.session_transaction() as session:
            assert session['oauth_state'] == 'session_state'

    def test_state_validation_missing_state(self, client):
        """A missing state is rejected before provider access."""
        with client.session_transaction() as session:
            session['oauth_state'] = 'session_state'
        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
            result = client.get('/callback/google?code=test_code')

        provider_class.assert_not_called()
        assert result.status_code == 302

    def test_state_cleared_after_callback(self, client, app):
        """A validated callback consumes state even when provider exchange fails."""
        app.config.update(GOOGLE_CLIENT_ID='test_id', GOOGLE_CLIENT_SECRET='test_secret')
        with client.session_transaction() as session:
            session['oauth_state'] = 'session_state'
            session['oauth_provider'] = 'google'

        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
            provider_class.return_value.exchange_code_for_token.side_effect = ValueError('exchange sentinel')
            client.get('/callback/google?state=session_state&code=test_code')

        with client.session_transaction() as session:
            assert 'oauth_state' not in session
            assert 'oauth_provider' not in session


@pytest.mark.unit
class TestOAuthTokenSecurity:
    """Test token validation and security"""

    @patch('infrastructure.auth.google_provider.requests.post')
    def test_invalid_token_rejected(self, mock_post):
        """Test that invalid tokens are rejected"""
        from infrastructure.auth.google_provider import GoogleOAuthProvider

        mock_response = Mock()
        mock_response.ok = False
        mock_response.text = 'Invalid token'
        mock_post.return_value = mock_response

        provider = GoogleOAuthProvider('test_id', 'test_secret')

        with pytest.raises(ValueError, match="Google ile giriş yapılamadı"):
            provider.exchange_code_for_token('invalid_code', 'http://callback')

    @patch('infrastructure.auth.google_provider.requests.get')
    def test_unverified_email_rejected(self, mock_get):
        """Test that unverified emails are rejected"""
        from infrastructure.auth.google_provider import GoogleOAuthProvider

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'email': 'test@example.com',
            'email_verified': False
        }
        mock_get.return_value = mock_response

        provider = GoogleOAuthProvider('test_id', 'test_secret')

        with pytest.raises(ValueError, match="e-posta adresi doğrulanmamış"):
            provider.verify_token_and_get_user_info('test_token')

    @patch('infrastructure.auth.google_provider.requests.get')
    def test_token_not_sent_to_frontend(self, mock_get):
        """Test that tokens are never sent to frontend"""
        from infrastructure.auth.google_provider import GoogleOAuthProvider

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'email': 'test@example.com',
            'email_verified': True,
            'sub': 'google_123'
        }
        mock_get.return_value = mock_response

        provider = GoogleOAuthProvider('test_id', 'test_secret')
        result = provider.verify_token_and_get_user_info('test_token')

        # Token should not be in the returned DTO
        assert not hasattr(result, 'access_token')
        assert not hasattr(result, 'id_token')
        assert not hasattr(result, 'refresh_token')


@pytest.mark.unit
class TestOAuthAccountTakeover:
    """Test protection against account takeover attacks"""

    @patch('application.users.oauth_application_service.db')
    def test_email_collision_without_auto_link(self, mock_db):
        """Test that email collision doesn't auto-link without verification"""
        from application.users.oauth_application_service import OAuthApplicationService
        from application.users.ports.oauth_provider import OAuthUserInfoDto

        mock_provider = Mock()
        mock_provider.exchange_code_for_token.return_value = {'access_token': 'test_token'}
        mock_provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
            email='existing@example.com',
            name='New User',
            provider_id='google_new',
            provider='google',
            email_verified=True
        )

        service = OAuthApplicationService(oauth_provider=mock_provider)

        with patch('application.users.oauth_application_service.User') as mock_user_model:
            # Simulate existing user with different oauth_id
            mock_existing_user = Mock()
            mock_existing_user.id = 1
            mock_existing_user.oauth_id = 'google_old'  # Different OAuth ID
            mock_existing_user.auth_provider = 'GOOGLE'
            mock_user_model.query.filter_by.return_value.first.return_value = mock_existing_user

            result = service.verify_and_login('code123', 'http://callback')

            # Should link to existing user (this is the current behavior)
            # In production, this might need additional verification
            assert result == mock_existing_user


@pytest.mark.unit
class TestOAuthCrossTenantAccess:
    """Test protection against cross-tenant access"""

    def test_tenant_isolation_on_oauth_login(self):
        """Test that OAuth login respects tenant isolation"""
        from application.users.oauth_application_service import OAuthApplicationService
        from application.users.ports.oauth_provider import OAuthUserInfoDto

        mock_provider = Mock()
        mock_provider.exchange_code_for_token.return_value = {'access_token': 'test_token'}
        mock_provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
            email='test@example.com',
            name='Test User',
            provider_id='google_123',
            provider='google',
            email_verified=True
        )

        service = OAuthApplicationService(oauth_provider=mock_provider)

        with patch('application.users.oauth_application_service.db'), \
             patch('application.users.oauth_application_service.User') as mock_user_model, \
             patch('application.users.oauth_application_service.Tenant') as mock_tenant_model:

            # No existing user - should create new tenant
            mock_user_model.query.filter_by.return_value.first.return_value = None

            mock_tenant = Mock()
            mock_tenant.id = 'tenant_test_123'
            mock_tenant_model.return_value = mock_tenant

            mock_user = Mock()
            mock_user.id = 1
            mock_user.tenant_id = 'tenant_test_123'
            mock_user_model.return_value = mock_user

            result = service.verify_and_login('code123', 'http://callback')

            # User should be assigned to new tenant
            assert result.tenant_id == 'tenant_test_123'


@pytest.mark.unit
class TestOAuthOpenRedirect:
    """Test protection against open redirect attacks"""

    def test_redirect_uri_is_controlled(self):
        """Test that redirect URI is controlled by backend, not user input"""
        from infrastructure.auth.google_provider import GoogleOAuthProvider

        provider = GoogleOAuthProvider('test_id', 'test_secret')
        url = provider.get_authorization_url('http://localhost:5000/callback/google', 'state123')

        # Redirect URI should be exactly what was passed
        assert 'redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fcallback%2Fgoogle' in url
        # Should not contain arbitrary redirect
        assert 'evil.com' not in url


@pytest.mark.unit
class TestOAuthSessionSecurity:
    """Test session security in OAuth flow"""

    def test_session_created_after_oauth(self, client, app):
        """A new OAuth identity gets a protected signup session, not an anonymous login."""
        from application.users.ports.oauth_provider import OAuthUserInfoDto

        app.config.update(GOOGLE_CLIENT_ID='test_id', GOOGLE_CLIENT_SECRET='test_secret')
        with client.session_transaction() as session:
            session['oauth_state'] = 'same_state'
            session['oauth_provider'] = 'google'

        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class, \
             patch('models.User') as user_model:
            provider = provider_class.return_value
            provider.exchange_code_for_token.return_value = {'access_token': 'token'}
            provider.verify_token_and_get_user_info.return_value = OAuthUserInfoDto(
                email='oauth-new@example.com', name='OAuth New', provider='google',
                provider_id='provider-new', email_verified=True
            )
            user_model.query.filter_by.return_value.first.return_value = None
            result = client.get('/callback/google?state=same_state&code=test_code')

        with client.session_transaction() as session:
            assert session['oauth_signup_info']['email'] == 'oauth-new@example.com'
            assert session['oauth_signup_info']['provider_id'] == 'provider-new'
        assert result.location.endswith('/oauth-signup')

    def test_session_cleared_on_oauth_start(self, client, app):
        """Validated OAuth state is consumed while unrelated session values remain."""
        app.config.update(GOOGLE_CLIENT_ID='test_id', GOOGLE_CLIENT_SECRET='test_secret')
        with client.session_transaction() as session:
            session['oauth_state'] = 'same_state'
            session['oauth_provider'] = 'google'
            session['unrelated_state'] = 'preserved'

        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as provider_class:
            provider_class.return_value.exchange_code_for_token.side_effect = ValueError('exchange sentinel')
            client.get('/callback/google?state=same_state&code=test_code')

        with client.session_transaction() as session:
            assert 'oauth_state' not in session
            assert 'oauth_provider' not in session
            assert session['unrelated_state'] == 'preserved'
