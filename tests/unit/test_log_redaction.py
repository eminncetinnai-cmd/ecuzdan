"""Unit tests for log redaction helpers."""

import pytest

from utils.log_redaction import mask_email, mask_identifier, mask_provider_id, redact_message


@pytest.mark.unit
def test_mask_email_standard():
    assert mask_email('user@example.com') == 'u***@example.com'


@pytest.mark.unit
def test_mask_email_empty():
    assert mask_email(None) == 'N/A'
    assert mask_email('') == 'N/A'


@pytest.mark.unit
def test_mask_identifier_stable():
    assert mask_identifier('alice', 'user') == mask_identifier('alice', 'user')
    assert mask_identifier('alice', 'user').startswith('user_')


@pytest.mark.unit
def test_mask_provider_id():
    assert mask_provider_id('1234567890') == '***7890'
    assert mask_provider_id(None) == 'N/A'


@pytest.mark.unit
def test_redact_message_masks_sensitive_kv():
    message = 'Login failed token=abc123 secret=hidden'
    redacted = redact_message(message)
    assert 'abc123' not in redacted
    assert 'hidden' not in redacted
    assert 'token=***' in redacted


@pytest.mark.unit
def test_redact_message_masks_email():
    redacted = redact_message('Registered user user@example.com')
    assert 'user@example.com' not in redacted
    assert 'u***@example.com' in redacted
