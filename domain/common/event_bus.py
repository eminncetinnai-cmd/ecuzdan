"""Event Bus interface."""

import abc
from typing import Callable, Any, Type
from .events import DomainEvent

EventHandler = Callable[[DomainEvent], Any]


class EventBus(abc.ABC):
    """Abstract Event Bus interface.
    
    Implementations of this interface should handle the actual
    routing and delivery of events to their subscribers.
    """

    @abc.abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all interested subscribers.
        
        Args:
            event: The DomainEvent instance to publish.
        """
        pass

    @abc.abstractmethod
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type.
        
        Args:
            event_type: The class of the event to subscribe to.
            handler: A callable that will be invoked when the event is published.
        """
        pass

    @abc.abstractmethod
    def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type.
        
        Args:
            event_type: The class of the event to unsubscribe from.
            handler: The callable that was previously subscribed.
        """
        pass
