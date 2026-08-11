"""Local in-memory event bus implementation."""

import logging
from collections import defaultdict
from typing import Dict, List, Type

from domain.common.event_bus import EventBus, EventHandler
from domain.common.events import DomainEvent

logger = logging.getLogger(__name__)


class LocalEventBus(EventBus):
    """In-memory event bus for synchronous event dispatching."""

    def __init__(self):
        # Maps event type to a list of handler functions
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Unregister a handler from a specific event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed {handler.__name__} from {event_type.__name__}")

    def publish(self, event: DomainEvent) -> None:
        """Dispatch the event to all registered handlers synchronously."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        logger.info(f"Publishing event: {event.event_name}")
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.exception(f"Error handling event {event.event_name} with {handler.__name__}: {e}")
