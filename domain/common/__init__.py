"""Common domain models and event structures."""
from .events import DomainEvent
from .event_bus import EventBus

__all__ = ["DomainEvent", "EventBus"]
