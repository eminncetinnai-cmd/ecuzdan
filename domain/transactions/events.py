"""Transaction domain events."""

from dataclasses import dataclass
from typing import Optional

from domain.common.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class TransactionCreatedEvent(DomainEvent):
    """Published when a one-time transaction is created."""
    transaction_id: int
    category: str
    amount: float
    status: str
    tenant_id: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class TransactionUpdatedEvent(DomainEvent):
    """Published when a one-time transaction is updated."""
    transaction_id: int
    category: str
    amount: float
    status: str
    tenant_id: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class TransactionDeletedEvent(DomainEvent):
    """Published when a one-time transaction is deleted."""
    transaction_id: int
    tenant_id: Optional[str] = None
