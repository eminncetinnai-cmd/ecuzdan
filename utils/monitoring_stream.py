"""Bounded Server-Sent Events fan-out for authenticated monitoring clients."""

from __future__ import annotations

import json
import logging
import queue
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional

from utils.log_redaction import redact_message

MAX_SUBSCRIBERS = 32
QUEUE_SIZE = 256


class MonitoringStream:
    def __init__(self, max_subscribers: int = MAX_SUBSCRIBERS) -> None:
        self._subscribers: set[queue.Queue] = set()
        self._lock = threading.Lock()
        self._max_subscribers = max_subscribers

    def subscribe(self) -> Optional[queue.Queue]:
        with self._lock:
            if len(self._subscribers) >= self._max_subscribers:
                return None
            channel: queue.Queue = queue.Queue(maxsize=QUEUE_SIZE)
            self._subscribers.add(channel)
            return channel

    def unsubscribe(self, channel: queue.Queue) -> None:
        with self._lock:
            self._subscribers.discard(channel)

    def publish(self, record: logging.LogRecord) -> None:
        trace_id = getattr(record, 'otel_trace_id', None)
        if trace_id == '0' * 32:
            trace_id = None
        span_id = getattr(record, 'otel_span_id', None)
        if span_id == '0' * 16:
            span_id = None

        exception_type = None
        exception_message = None
        if record.exc_info and record.exc_info[0] is not None:
            exception_type = record.exc_info[0].__name__
            exception_message = redact_message(str(record.exc_info[1]))

        payload: Dict[str, Any] = {
            'timestamp': self._format_timestamp(record),
            'level': record.levelname.upper(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': redact_message(record.getMessage()),
            'request_id': getattr(record, 'request_id', None),
            'trace_id': trace_id,
            'span_id': span_id,
            'category': self._category_for(record),
            'exception_type': exception_type,
            'exception_message': exception_message,
        }
        with self._lock:
            channels = tuple(self._subscribers)
        for channel in channels:
            try:
                channel.put_nowait(payload)
            except queue.Full:
                try:
                    channel.get_nowait()
                    channel.put_nowait(payload)
                except (queue.Empty, queue.Full):
                    continue

    def stream(self, channel: queue.Queue) -> Iterator[str]:
        try:
            yield 'event: ready\ndata: {"status":"connected"}\n\n'
            while True:
                try:
                    payload = channel.get(timeout=15)
                    yield f'event: log\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'
                except queue.Empty:
                    yield 'event: heartbeat\ndata: {}\n\n'
        finally:
            self.unsubscribe(channel)

    @staticmethod
    def _category_for(record: logging.LogRecord) -> str:
        message = record.getMessage().lower()
        logger_name = record.name.lower()
        security_markers = (
            'authentication', 'unauthorized', 'access denied', 'permission denied',
            'csrf', 'rate limit', 'ratelimit', 'security', 'token replay',
        )
        if logger_name.startswith(('security', 'audit')) or any(
            marker in message for marker in security_markers
        ):
            return 'security'
        if record.levelno >= logging.ERROR:
            return 'error'
        if record.levelno >= logging.WARNING:
            return 'warning'
        return 'application'

    @staticmethod
    def _format_timestamp(record: logging.LogRecord) -> str:
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec='seconds')


monitoring_stream = MonitoringStream()


class MonitoringSSEHandler(logging.Handler):
    """Publish application records without changing existing handlers."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            monitoring_stream.publish(record)
        except Exception:
            self.handleError(record)
