from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from typing import Any, Optional

EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
SENSITIVE_KV_PATTERN = re.compile(
    r'(?i)\b(password|token|secret|api[_-]?key|csrf|authorization|cookie|session(?:[_-]?id)?|access[_-]?token|refresh[_-]?token)\s*[:=]\s*(?:"[^"]*"|\'[^\']*\'|[^\s,;]+)'
)
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b', re.IGNORECASE)
CARD_PATTERN = re.compile(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)')
PHONE_PATTERN = re.compile(r'(?<!\w)(?:\+|00|0)\d[\d\s().-]{7,}\d(?!\w)')

SENSITIVE_FIELD_TOKENS = (
    'password', 'passwd', 'token', 'secret', 'api_key', 'apikey', 'csrf',
    'authorization', 'cookie', 'session', 'access_key', 'refresh_key',
)
IDENTIFIER_FIELD_TOKENS = (
    'user_id', 'tenant_id', 'account_id', 'transaction_id', 'portfolio_id',
    'provider_id', 'customer_id', 'client_id', 'reference_id', 'request_id',
)


def _hash8(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:8]


def mask_email(email: Optional[str]) -> str:
    """Return a log-safe email representation."""
    if not email:
        return 'N/A'
    email = str(email).strip()
    if '@' not in email:
        return f'user_{_hash8(email)}'
    local, domain = email.split('@', 1)
    local_masked = f'{local[0]}***' if local else '***'
    return f'{local_masked}@{domain}'


def mask_identifier(value: Optional[str], prefix: str = 'id') -> str:
    """Return a stable hashed identifier for logs."""
    if not value:
        return 'N/A'
    return f'{prefix}_{_hash8(str(value))}'


def mask_provider_id(provider_id: Optional[str]) -> str:
    """Return a log-safe OAuth provider id."""
    if not provider_id:
        return 'N/A'
    provider_id = str(provider_id)
    if len(provider_id) <= 4:
        return '****'
    return f'***{provider_id[-4:]}'


def mask_phone(value: Optional[str]) -> str:
    """Mask a phone value while retaining only a minimal suffix."""
    if not value:
        return 'N/A'
    digits = re.sub(r'\D', '', str(value))
    return f'phone_***{digits[-2:]}' if len(digits) >= 2 else 'phone_***'


def mask_iban(value: Optional[str]) -> str:
    """Mask an IBAN while retaining only the final four characters."""
    if not value:
        return 'N/A'
    compact = re.sub(r'\s+', '', str(value))
    return f'iban_***{compact[-4:]}' if len(compact) >= 4 else 'iban_***'


def mask_card(value: Optional[str]) -> str:
    """Mask a payment-card-like value while retaining only the final four digits."""
    if not value:
        return 'N/A'
    digits = re.sub(r'\D', '', str(value))
    return f'card_***{digits[-4:]}' if len(digits) >= 4 else 'card_***'


def redact_message(message: str) -> str:
    """Apply conservative, deterministic redaction to free-form log text."""
    if not message:
        return message

    redacted = SENSITIVE_KV_PATTERN.sub(lambda match: f'{match.group(1)}=***', str(message))
    redacted = IBAN_PATTERN.sub(lambda match: mask_iban(match.group(0)), redacted)
    redacted = CARD_PATTERN.sub(lambda match: mask_card(match.group(0)), redacted)
    redacted = PHONE_PATTERN.sub(lambda match: mask_phone(match.group(0)), redacted)
    return EMAIL_PATTERN.sub(lambda match: mask_email(match.group(0)), redacted)


def redact_value(value: Any, field_name: str = '') -> Any:
    """Recursively redact structured log values according to their field name."""
    normalized = field_name.lower().replace('-', '_').replace('.', '_')

    if isinstance(value, Mapping):
        return {key: redact_value(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item, field_name) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item, field_name) for item in value)
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if 'email' in normalized:
        return mask_email(str(value))
    if 'phone' in normalized or 'mobile' in normalized:
        return mask_phone(str(value))
    if 'iban' in normalized:
        return mask_iban(str(value))
    if 'card' in normalized or 'pan' in normalized:
        return mask_card(str(value))
    if 'provider_id' in normalized:
        return mask_provider_id(str(value))
    if any(token in normalized for token in SENSITIVE_FIELD_TOKENS):
        return '***'
    if any(token in normalized for token in IDENTIFIER_FIELD_TOKENS) and normalized not in {'request_id'}:
        prefix = normalized.rsplit('_', 1)[0] or 'id'
        return mask_identifier(str(value), prefix)
    return redact_message(str(value))


def redact_log_record(record: Any) -> Any:
    """Redact a LogRecord in place for all file, console, JSON and stream handlers."""
    rendered = record.getMessage()
    record.msg = redact_message(rendered)
    record.args = ()

    reserved = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
        'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process', 'message', 'asctime', 'otel_trace_id',
        'otel_span_id', '_pii_redacted',
    }
    for key, value in list(record.__dict__.items()):
        if key in reserved or key.startswith('_'):
            continue
        setattr(record, key, redact_value(value, key))

    if record.exc_info and record.exc_info[1] is not None:
        record.redacted_exception_message = redact_message(str(record.exc_info[1]))
    record._pii_redacted = True
    return record
