"""Asynchronous local in-memory event bus implementation."""

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Type

from domain.common.event_bus import EventBus, EventHandler
from domain.common.events import DomainEvent

logger = logging.getLogger(__name__)


class AsyncLocalEventBus(EventBus):
    """In-memory event bus for asynchronous event dispatching using a thread pool.

    Simulates a message broker like RabbitMQ by dispatching handlers in the background.
    """

    def __init__(self, max_workers: int = 4):
        # Maps event type to a list of handler functions
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = defaultdict(list)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AsyncEventBus")

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
        """Dispatch the event to all registered handlers asynchronously."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"No handlers registered for event: {event.event_name}")
            return

        logger.info(f"Async publishing event: {event.event_name} to {len(handlers)} handlers")

        # Trace the dispatch as a child span
        try:
            from opentelemetry import trace as otel_trace
            tracer = otel_trace.get_tracer("infrastructure.events.async_local_event_bus")
            with tracer.start_as_current_span(
                f"event.publish/{event.event_name}",
                attributes={"event.type": event.event_name, "event.handlers": len(handlers)},
            ):
                for handler in handlers:
                    self._executor.submit(self._run_handler, handler, event)
        except Exception:
            # Tracing must never break event delivery
            for handler in handlers:
                self._executor.submit(self._run_handler, handler, event)

    def _run_handler(self, handler: EventHandler, event: DomainEvent) -> None:
        """Execute a handler and catch any exceptions so they don't crash the worker thread."""
        try:
            handler(event)
        except Exception as e:
            logger.exception(f"Error handling event {event.event_name} with {handler.__name__}: {e}")

    def shutdown(self, wait=True):
        """Shut down the thread pool."""
        self._executor.shutdown(wait=wait)
