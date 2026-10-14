"""Base Domain Event definitions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def utcnow_naive() -> datetime:
    """Helper to return current naive UTC datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events.

    A Domain Event represents something that happened in the domain
    that domain experts care about.
    """
    occurred_on: datetime = field(default_factory=utcnow_naive)

    @property
    def event_name(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging or serialization."""
        return {
            "event_name": self.event_name,
            "occurred_on": self.occurred_on.isoformat(),
            **self._get_payload()
        }

    def _get_payload(self) -> Dict[str, Any]:
        """Subclasses can override to provide specific payload attributes."""
        # Simple default: return all fields except occurred_on
        import dataclasses
        if dataclasses.is_dataclass(self):
            return {
                f.name: getattr(self, f.name)
                for f in dataclasses.fields(self)
                if f.name != 'occurred_on'
            }
        return {}
