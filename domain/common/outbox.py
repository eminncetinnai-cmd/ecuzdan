"""Outbox pattern domain models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(kw_only=True)
class OutboxMessage:
    """Represents a domain event stored in the outbox for guaranteed delivery."""

    id: str
    event_type: str
    payload: str  # JSON serialized event data
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    processed_on: Optional[datetime] = None
    error: Optional[str] = None
