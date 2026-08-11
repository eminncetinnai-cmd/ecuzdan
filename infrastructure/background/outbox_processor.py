"""Outbox Processor — polls the outbox table and dispatches events.

This background worker reads unprocessed OutboxMessage rows, deserialises
the event payload, looks up the concrete DomainEvent class, and publishes
each event through the configured EventBus.  After successful dispatch the
row is marked as processed; on failure the error is recorded for later
inspection / retry.

Usage:
    processor = OutboxProcessor(event_bus, app)
    processor.start(interval_seconds=5)
"""

import importlib
import json
import logging
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Registry: event_type string → fully-qualified class path
# Keeps the processor decoupled from individual domain modules.
EVENT_TYPE_REGISTRY: dict[str, str] = {
    'TransactionCreatedEvent': 'domain.transactions.events.TransactionCreatedEvent',
    'TransactionUpdatedEvent': 'domain.transactions.events.TransactionUpdatedEvent',
    'TransactionDeletedEvent': 'domain.transactions.events.TransactionDeletedEvent',
}


def _resolve_event_class(event_type: str):
    """Dynamically import and return the DomainEvent class."""
    fqn = EVENT_TYPE_REGISTRY.get(event_type)
    if not fqn:
        raise ValueError(f"Unknown event type: {event_type}")
    module_path, class_name = fqn.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


class OutboxProcessor:
    """Background thread that drains the outbox table."""

    def __init__(self, event_bus, app=None, batch_size: int = 20):
        self._event_bus = event_bus
        self._app = app  # Flask app for application context
        self._batch_size = batch_size
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # ── public API ───────────────────────────────────────────────────

    def start(self, interval_seconds: int = 5):
        """Start polling in a daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(interval_seconds,),
            daemon=True,
            name='outbox-processor',
        )
        self._thread.start()
        self._safe_log_info("OutboxProcessor started (interval=%ds)", interval_seconds)

    def stop(self):
        """Signal the background thread to stop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

        self._safe_log_info("OutboxProcessor stopped.")

    def _logging_available(self) -> bool:
        """Return True if logging handlers are still active and writable."""
        handlers = list(logging.getLogger().handlers) + list(logging.root.handlers)
        if not handlers:
            return False
        for handler in handlers:
            stream = getattr(handler, 'stream', None)
            if stream is not None and getattr(stream, 'closed', False):
                return False
        return True

    def _safe_log_info(self, msg: str, *args, **kwargs) -> None:
        """Log info safely only when the logging subsystem is still active."""
        if self._logging_available():
            try:
                logger.info(msg, *args, **kwargs)
            except Exception:
                pass

    def _safe_log_exception(self, msg: str, *args, **kwargs) -> None:
        """Log exceptions safely only when the logging subsystem is still active."""
        if self._logging_available():
            try:
                logger.exception(msg, *args, **kwargs)
            except Exception:
                pass

    def process_batch(self):
        """Process one batch of pending outbox messages.

        Returns the number of messages successfully dispatched.
        """
        from infrastructure.database.models.outbox_model import OutboxMessageModel
        from shared.db import db

        pending = (
            OutboxMessageModel.query
            .filter_by(processed_on=None)
            .order_by(OutboxMessageModel.occurred_on.asc())
            .limit(self._batch_size)
            .all()
        )

        if not pending:
            return 0

        dispatched = 0
        for msg in pending:
            try:
                event_cls = _resolve_event_class(msg.event_type)
                payload = json.loads(msg.payload)
                # Remove 'occurred_on' from payload if present — it's metadata
                payload.pop('occurred_on', None)
                event = event_cls(**payload)

                self._event_bus.publish(event)

                msg.processed_on = datetime.now(timezone.utc).replace(tzinfo=None)
                msg.error = None
                dispatched += 1
            except Exception as e:
                msg.error = str(e)
                self._safe_log_exception("Failed to dispatch outbox message %s: %s", msg.id, e)

        db.session.commit()
        if dispatched:
            self._safe_log_info("OutboxProcessor dispatched %d event(s).", dispatched)
        return dispatched

    # ── internals ────────────────────────────────────────────────────

    def _run_loop(self, interval: int):
        """Polling loop executed in the daemon thread."""
        while not self._stop_event.is_set():
            try:
                if self._app:
                    with self._app.app_context():
                        self.process_batch()
                else:
                    self.process_batch()
            except Exception:
                self._safe_log_exception("OutboxProcessor error during poll cycle.")
            self._stop_event.wait(interval)
