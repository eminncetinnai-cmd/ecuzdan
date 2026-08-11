"""OAuth Provider Port - Authentication Provider Framework (Phase 11)

This port defines the interface for OAuth providers (Google, Apple, Microsoft, etc.)
following the Open-Closed Principle - new providers can be added without modifying
existing code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class OAuthUserInfoDto:
    """Data Transfer Object for OAuth user information
    
    This DTO contains normalized user information from OAuth providers.
    It's used to transfer data between infrastructure and application layers.
    """
    email: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider_id: str = ""  # Unique ID from the provider (e.g., Google subject)
    provider: str = ""  # Provider name (e.g., 'google', 'apple')
    email_verified: bool = False


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers
    
    This interface defines the contract that all OAuth providers must implement.
    It ensures that the application layer can work with any provider without
    knowing implementation details.
    
    Implementation rules:
    - Provider-specific SDKs and HTTP calls MUST live in infrastructure layer
    - This port only defines the interface
    - All providers must return OAuthUserInfoDto with normalized data
    """
    
    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate the OAuth authorization URL
        
        Args:
            redirect_uri: The callback URL after authorization
            state: CSRF protection state parameter
            
        Returns:
            The full authorization URL to redirect the user to
        """
        pass
    
    @abstractmethod
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token
        
        Args:
            code: The authorization code from the callback
            redirect_uri: The same redirect_uri used in authorization
            
        Returns:
            Dictionary containing token information (access_token, id_token, etc.)
        """
        pass
    
    @abstractmethod
    def verify_token_and_get_user_info(self, token: str) -> OAuthUserInfoDto:
        """Verify the token and extract user information
        
        This method must:
        - Verify the token signature and issuer
        - Validate the audience (aud) claim
        - Check email_verified status
        - Extract and normalize user information
        
        Args:
            token: The ID token or access token to verify
            
        Returns:
            OAuthUserInfoDto with normalized user information
            
        Raises:
            ValueError: If token is invalid, expired, or email not verified
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'google', 'apple')"""
        pass
    
    @property
    @abstractmethod
    def requires_client_secret(self) -> bool:
        """Whether this provider requires a client secret for token exchange"""
        pass
