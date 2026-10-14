"""User domain events."""

from dataclasses import dataclass

from domain.common.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class UserCreatedEvent(DomainEvent):
    """Fired when a new user is registered."""
    user_id: int
    username: str
    tenant_id: str

@dataclass(frozen=True, kw_only=True)
class UserLoggedInEvent(DomainEvent):
    """Fired when a user successfully logs in."""
    user_id: int
    session_id: str
    via_provider: str = 'LOCAL'

@dataclass(frozen=True, kw_only=True)
class OAuthAccountLinkedEvent(DomainEvent):
    """Fired when an existing user account is linked to an OAuth provider."""
    user_id: int
    provider: str
    oauth_id: str


@dataclass(frozen=True, kw_only=True)
class UserLanguageChangedEvent(DomainEvent):
    """Fired when a user changes their language."""
    user_id: int
    language: str
