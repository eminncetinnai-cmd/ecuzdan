"""Request-scoped correlation ID for distributed log tracing."""

from __future__ import annotations

import logging
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = 'X-Request-ID'


def _generate_request_id() -> str:
    return secrets.token_hex(16)


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
            from flask import g, request

            incoming = request.headers.get(REQUEST_ID_HEADER)
            g.request_id = incoming.strip() if incoming else _generate_request_id()
        except Exception:
            logger.debug("Request ID assignment skipped", exc_info=True)

    @app.after_request
    def _expose_request_id(response):
        try:
            from flask import g, has_request_context

            if has_request_context() and getattr(g, 'request_id', None):
                response.headers[REQUEST_ID_HEADER] = g.request_id
        except Exception:
            logger.debug("Request ID response header skipped", exc_info=True)
        return response
