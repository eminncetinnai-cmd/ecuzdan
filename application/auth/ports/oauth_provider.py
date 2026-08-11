"""Ports and DTOs for OAuth providers."""

import abc
from dataclasses import dataclass
from typing import Optional

@dataclass
class OAuthUserInfoDto:
    provider: str
    oauth_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False

class OAuthProvider(abc.ABC):
    """Port defining the contract for an OAuth authentication provider."""
    
    @abc.abstractmethod
    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Returns the URL to redirect the user to for authentication."""
        pass
        
    @abc.abstractmethod
    def verify_token_and_get_user(self, code: str, redirect_uri: str) -> OAuthUserInfoDto:
        """Exchanges an authorization code for tokens and fetches user info."""
        pass
