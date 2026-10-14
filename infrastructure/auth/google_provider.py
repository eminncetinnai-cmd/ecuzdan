"""Infrastructure layer implementation of Google OAuth provider.

This file contains the Google-specific OAuth implementation including:
- Google SDK integration
- HTTP calls to Google OAuth endpoints
- Token verification and user info extraction

IMPORTANT: This is the ONLY place where Google SDK/HTTP code should live.
No Google-specific code should leak into domain or application layers.
"""

import logging
from urllib.parse import urlencode

import requests

from application.users.ports.oauth_provider import OAuthProvider, OAuthUserInfoDto

logger = logging.getLogger(__name__)


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider implementation

    This class implements the OAuthProvider interface for Google OAuth 2.0.
    It handles the complete OAuth flow including authorization, token exchange,
    and user information retrieval.
    """

    def __init__(self, client_id: str, client_secret: str):
        """Initialize Google OAuth provider

        Args:
            client_id: Google OAuth client ID from Google Cloud Console
            client_secret: Google OAuth client secret from Google Cloud Console
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate Google OAuth authorization URL

        Args:
            redirect_uri: Callback URL after authorization
            state: CSRF protection state parameter

        Returns:
            Full Google authorization URL
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect_uri used in authorization

        Returns:
            Dictionary with token information (access_token, id_token, etc.)

        Raises:
            ValueError: If token exchange fails
        """
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        response = requests.post(self.token_url, data=data)
        if not response.ok:
            logger.error(f"Failed to exchange code for token: HTTP {response.status_code}")
            raise ValueError("Google ile giriş yapılamadı: Geçersiz doğrulama kodu.")

        return response.json()

    def verify_token_and_get_user_info(self, token: str) -> OAuthUserInfoDto:
        """Verify token and extract user information

        This method:
        - Uses the access token to fetch user info from Google
        - Validates email_verified status
        - Normalizes user information into OAuthUserInfoDto

        Args:
            token: Access token from Google

        Returns:
            OAuthUserInfoDto with normalized user information

        Raises:
            ValueError: If token is invalid or email not verified
        """
        headers = {'Authorization': f'Bearer {token}'}
        userinfo_response = requests.get(self.userinfo_url, headers=headers)

        if not userinfo_response.ok:
            logger.error(f"Failed to fetch user info: {userinfo_response.text}")
            raise ValueError("Kullanıcı bilgileri alınamadı.")

        user_data = userinfo_response.json()

        # Security check: email must be verified
        if not user_data.get('email_verified', False):
            raise ValueError(
                "Google hesabınızın e-posta adresi doğrulanmamış. "
                "Lütfen önce e-posta adresinizi doğrulayın."
            )

        return OAuthUserInfoDto(
            email=user_data.get('email', ''),
            name=user_data.get('name', ''),
            given_name=user_data.get('given_name'),
            family_name=user_data.get('family_name'),
            avatar_url=user_data.get('picture'),
            provider_id=user_data.get('sub', ''),
            provider='google',
            email_verified=user_data.get('email_verified', False)
        )

    def get_provider_name(self) -> str:
        """Return provider name"""
        return 'google'

    @property
    def requires_client_secret(self) -> bool:
        """Google OAuth requires client secret"""
        return True
