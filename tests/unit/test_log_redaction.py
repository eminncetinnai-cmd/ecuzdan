"""Unit tests for log redaction helpers."""

import logging

import pytest

from utils.log_filters import PIIRedactionFilter
from utils.log_redaction import (
    mask_email,
    mask_identifier,
    mask_provider_id,
    redact_message,
    redact_value,
)


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


@pytest.mark.unit
def test_redact_message_masks_iban_card_and_phone():
    message = 'iban=TR330006100519786457841326 card=4111111111111111 phone=+90 555 123 45 67'
    redacted = redact_message(message)
    assert 'TR330006100519786457841326' not in redacted
    assert '4111111111111111' not in redacted
    assert '+90 555 123 45 67' not in redacted
    assert 'iban_***1326' in redacted
    assert 'card_***1111' in redacted
    assert 'phone_***67' in redacted


@pytest.mark.unit
def test_redact_value_recursively_masks_sensitive_and_identifier_fields():
    value = {
        'authorization': 'Bearer raw-token',
        'account_id': 'raw-account',
        'contact': {'email': 'user@example.com'},
        'items': [{'card_number': '4111111111111111'}],
    }
    redacted = redact_value(value)
    assert redacted['authorization'] == '***'
    assert redacted['account_id'].startswith('account_')
    assert redacted['contact']['email'] == 'u***@example.com'
    assert redacted['items'][0]['card_number'] == 'card_***1111'


@pytest.mark.unit
def test_pii_redaction_filter_masks_log_record_extra_fields():
    record = logging.LogRecord('security.audit', logging.WARNING, 'test.py', 1, 'token=raw-token', (), None)
    record.token = 'raw-token'
    record.user_id = 'raw-user'
    PIIRedactionFilter().filter(record)
    assert record.getMessage() == 'token=***'
    assert record.token == '***'
    assert record.user_id.startswith('user_')
