"""Logging filters for request context and PII redaction."""

from __future__ import annotations

import logging

from utils.log_redaction import redact_message


class RequestContextFilter(logging.Filter):
    """Inject request-scoped correlation fields into log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = '-'
        record.tenant_id = None
        record.user_id = None

        try:
            from flask import g, has_request_context, session

            if has_request_context():
                record.request_id = getattr(g, 'request_id', '-') or '-'
                record.tenant_id = getattr(g, 'tenant_id', None)
                record.user_id = session.get('user_id')
        except Exception:
            pass

        return True


class PIIRedactionFilter(logging.Filter):
    """Redact sensitive values from rendered log messages."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        try:
            rendered = record.getMessage()
            redacted = redact_message(rendered)
            if redacted != rendered:
                record.msg = redacted
                record.args = ()
        except Exception:
            pass
        return True
