"""
Unit tests for Google OAuth provider
"""

from unittest.mock import Mock, patch

import pytest

from application.users.ports.oauth_provider import OAuthUserInfoDto
from infrastructure.auth.google_provider import GoogleOAuthProvider


@pytest.mark.unit
class TestGoogleOAuthProvider:
    """Test GoogleOAuthProvider"""

    def test_initialization(self):
        """Test provider initialization"""
        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        assert provider.client_id == 'test_client_id'
        assert provider.client_secret == 'test_client_secret'
        assert provider.auth_url == "https://accounts.google.com/o/oauth2/v2/auth"
        assert provider.token_url == "https://oauth2.googleapis.com/token"
        assert provider.userinfo_url == "https://www.googleapis.com/oauth2/v3/userinfo"

    def test_get_authorization_url(self):
        """Test authorization URL generation"""
        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        url = provider.get_authorization_url(
            redirect_uri='https://example.com/callback',
            state='test_state'
        )

        assert 'https://accounts.google.com/o/oauth2/v2/auth' in url
        assert 'client_id=test_client_id' in url
        assert 'redirect_uri=https%3A%2F%2Fexample.com%2Fcallback' in url
        assert 'response_type=code' in url
        assert 'scope=openid+email+profile' in url
        assert 'state=test_state' in url
        assert 'access_type=offline' in url
        assert 'prompt=consent' in url

    @patch('infrastructure.auth.google_provider.requests.post')
    def test_exchange_code_for_token_success(self, mock_post):
        """Test successful token exchange"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'id_token': 'test_id_token',
            'refresh_token': 'test_refresh_token'
        }
        mock_post.return_value = mock_response

        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        result = provider.exchange_code_for_token(
            code='test_code',
            redirect_uri='https://example.com/callback'
        )

        assert result['access_token'] == 'test_access_token'
        assert result['id_token'] == 'test_id_token'
        mock_post.assert_called_once_with(
            'https://oauth2.googleapis.com/token',
            data={
                'code': 'test_code',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'redirect_uri': 'https://example.com/callback',
                'grant_type': 'authorization_code'
            }
        )

    @patch('infrastructure.auth.google_provider.requests.post')
    def test_exchange_code_for_token_failure(self, mock_post):
        """Test token exchange failure"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.text = 'Invalid code'
        mock_post.return_value = mock_response

        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        with pytest.raises(ValueError, match="Google ile giriş yapılamadı"):
            provider.exchange_code_for_token(
                code='invalid_code',
                redirect_uri='https://example.com/callback'
            )

    @patch('infrastructure.auth.google_provider.requests.get')
    def test_verify_token_and_get_user_info_success(self, mock_get):
        """Test successful user info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'https://avatar.url',
            'sub': 'google_123',
            'email_verified': True
        }
        mock_get.return_value = mock_response

        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        result = provider.verify_token_and_get_user_info('test_token')

        assert isinstance(result, OAuthUserInfoDto)
        assert result.email == 'test@example.com'
        assert result.name == 'Test User'
        assert result.given_name == 'Test'
        assert result.family_name == 'User'
        assert result.avatar_url == 'https://avatar.url'
        assert result.provider_id == 'google_123'
        assert result.provider == 'google'
        assert result.email_verified is True
        mock_get.assert_called_once_with(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': 'Bearer test_token'}
        )

    @patch('infrastructure.auth.google_provider.requests.get')
    def test_verify_token_and_get_user_info_unverified_email(self, mock_get):
        """Test user info retrieval with unverified email"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'email_verified': False
        }
        mock_get.return_value = mock_response

        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        with pytest.raises(ValueError, match="e-posta adresi doğrulanmamış"):
            provider.verify_token_and_get_user_info('test_token')

    @patch('infrastructure.auth.google_provider.requests.get')
    def test_verify_token_and_get_user_info_failure(self, mock_get):
        """Test user info retrieval failure"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.text = 'Invalid token'
        mock_get.return_value = mock_response

        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        with pytest.raises(ValueError, match="Kullanıcı bilgileri alınamadı"):
            provider.verify_token_and_get_user_info('invalid_token')

    def test_get_provider_name(self):
        """Test provider name"""
        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        assert provider.get_provider_name() == 'google'

    def test_requires_client_secret(self):
        """Test that provider requires client secret"""
        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        assert provider.requires_client_secret is True

    @patch('infrastructure.auth.google_provider.requests.get')
    def test_verify_token_and_get_user_info_missing_fields(self, mock_get):
        """Test user info retrieval with missing optional fields"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'sub': 'google_123',
            'email_verified': True
        }
        mock_get.return_value = mock_response

        provider = GoogleOAuthProvider(
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        result = provider.verify_token_and_get_user_info('test_token')

        assert result.email == 'test@example.com'
        assert result.name == 'Test User'
        assert result.given_name is None
        assert result.family_name is None
        assert result.avatar_url is None
        assert result.provider_id == 'google_123'
