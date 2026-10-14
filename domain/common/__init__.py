"""Common domain models and event structures."""
from .event_bus import EventBus
from .events import DomainEvent

__all__ = ["DomainEvent", "EventBus"]
