"""Portfolio domain events."""

from dataclasses import dataclass
from domain.common.events import DomainEvent

@dataclass(frozen=True, kw_only=True)
class AssetAddedEvent(DomainEvent):
    """Fired when an asset is added to a portfolio."""
    asset_id: int
    asset_symbol: str
    tenant_id: str

@dataclass(frozen=True, kw_only=True)
class AssetUpdatedEvent(DomainEvent):
    """Fired when an asset is updated."""
    asset_id: int
    asset_symbol: str
    tenant_id: str

@dataclass(frozen=True, kw_only=True)
class AssetRemovedEvent(DomainEvent):
    """Fired when an asset is removed from a portfolio."""
    asset_id: int
    tenant_id: str
