"""Unit tests for logging filters."""

import logging

import pytest

from utils.log_filters import PIIRedactionFilter, RequestContextFilter


@pytest.mark.unit
def test_pii_redaction_filter_masks_sensitive_values():
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='OAuth callback token=super-secret-value',
        args=(),
        exc_info=None,
    )

    assert PIIRedactionFilter().filter(record) is True
    assert 'super-secret-value' not in record.msg
    assert 'token=***' in record.msg


@pytest.mark.unit
def test_request_context_filter_defaults_outside_request():
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='hello',
        args=(),
        exc_info=None,
    )

    assert RequestContextFilter().filter(record) is True
    assert record.request_id == '-'
    assert record.tenant_id is None
    assert record.user_id is None


@pytest.mark.unit
def test_request_context_filter_inside_request(app):
    from flask import g

    with app.test_request_context('/healthz', headers={'X-Request-ID': 'req-123'}):
        g.request_id = 'req-123'

        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='hello',
            args=(),
            exc_info=None,
        )

        assert RequestContextFilter().filter(record) is True
        assert record.request_id == 'req-123'
