import logging

import pytest

from utils.monitoring_stream import MonitoringStream


@pytest.mark.unit
def test_sse_payload_preserves_log_context_and_category():
    stream = MonitoringStream(max_subscribers=1)
    channel = stream.subscribe()
    assert channel is not None

    record = logging.LogRecord(
        name='routes.auth',
        level=logging.ERROR,
        pathname=__file__,
        lineno=42,
        msg='Login failed for user@example.com',
        args=(),
        exc_info=None,
    )
    record.request_id = 'req-123'
    record.otel_trace_id = 'abc123'
    record.otel_span_id = 'def456'

    stream.publish(record)
    payload = channel.get_nowait()

    assert payload['level'] == 'ERROR'
    assert payload['logger'] == 'routes.auth'
    assert payload['module'] == 'test_monitoring_stream'
    assert payload['request_id'] == 'req-123'
    assert payload['trace_id'] == 'abc123'
    assert payload['span_id'] == 'def456'
    assert payload['category'] == 'error'
    assert 'user@example.com' not in payload['message']

    stream.unsubscribe(channel)


@pytest.mark.unit
def test_sse_subscriber_limit_is_bounded():
    stream = MonitoringStream(max_subscribers=1)
    first = stream.subscribe()
    second = stream.subscribe()

    assert first is not None
    assert second is None
    stream.unsubscribe(first)
