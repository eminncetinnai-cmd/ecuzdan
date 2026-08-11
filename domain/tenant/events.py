"""Tenant domain events."""

from dataclasses import dataclass
from domain.common.events import DomainEvent

@dataclass(frozen=True, kw_only=True)
class TenantCreatedEvent(DomainEvent):
    """Fired when a new tenant is created."""
    tenant_id: str
    name: str

@dataclass(frozen=True, kw_only=True)
class TenantDeletedEvent(DomainEvent):
    """Fired when a tenant is deleted."""
    tenant_id: str
