"""Request-scoped correlation ID for distributed log tracing."""

from __future__ import annotations

import logging
import re
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = 'X-Request-ID'


def _generate_request_id() -> str:
    return secrets.token_hex(16)


def _sanitize_request_id(value: str | None) -> str:
    candidate = (value or "").strip()
    if len(candidate) <= 64 and re.fullmatch(r"[A-Za-z0-9._:-]+", candidate):
        return candidate
    return _generate_request_id()


def get_request_id() -> Optional[str]:
    """Return the current request ID when inside a Flask request context."""
    try:
        from flask import g, has_request_context

        if has_request_context():
            return getattr(g, 'request_id', None)
    except Exception:
        pass
    return None


def register_request_context(app) -> None:
    """Attach a per-request correlation ID to Flask `g` and response headers."""

    @app.before_request
    def _assign_request_id():
        try:
            import time

            from flask import g, request

            incoming = request.headers.get(REQUEST_ID_HEADER)
            g.request_id = _sanitize_request_id(incoming)
            g.request_start_time = time.perf_counter()
        except Exception:
            logger.debug("Request ID assignment skipped", exc_info=True)

    @app.after_request
    def _expose_request_id(response):
        try:
            import time

            from flask import g, has_request_context

            if has_request_context() and getattr(g, 'request_id', None):
                response.headers[REQUEST_ID_HEADER] = g.request_id
            if has_request_context() and getattr(g, 'request_start_time', None):
                duration_ms = (time.perf_counter() - g.request_start_time) * 1000
                response.headers['Server-Timing'] = f"app;dur={duration_ms:.2f}"
        except Exception:
            logger.debug("Request ID response header skipped", exc_info=True)
        return response
