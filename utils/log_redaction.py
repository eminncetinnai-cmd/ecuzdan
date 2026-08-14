"""Log redaction helpers — mask PII in log messages only (no business logic impact)."""

from __future__ import annotations

import hashlib
import re
from typing import Optional

EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
SENSITIVE_KV_PATTERN = re.compile(
    r'(?i)(password|token|secret|api[_-]?key|csrf|authorization)\s*[:=]\s*[^\s,;]+'
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


def redact_message(message: str) -> str:
    """Best-effort redaction for free-form log message text."""
    if not message:
        return message

    redacted = SENSITIVE_KV_PATTERN.sub(r'\1=***', message)
    return EMAIL_PATTERN.sub(lambda match: mask_email(match.group(0)), redacted)
