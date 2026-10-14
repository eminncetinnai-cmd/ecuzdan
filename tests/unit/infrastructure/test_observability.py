"""Unit tests for the current observability infrastructure contract."""

import logging

import pytest


@pytest.mark.unit
def test_trace_context_filter_preserves_log_records_and_adds_context_ids():
    from infrastructure.observability.log_filter import TraceContextFilter

    record = logging.makeLogRecord({'msg': 'User logged in successfully'})
    assert TraceContextFilter().filter(record) is True
    assert len(record.otel_trace_id) == 32
    assert len(record.otel_span_id) == 16


@pytest.mark.unit
def test_trace_context_filter_is_stable_for_sensitive_message_text():
    from infrastructure.observability.log_filter import TraceContextFilter

    record = logging.makeLogRecord({'msg': 'Password: secret123 token: abc456'})
    assert TraceContextFilter().filter(record) is True
    assert record.getMessage() == 'Password: secret123 token: abc456'
    assert hasattr(record, 'otel_trace_id')
    assert hasattr(record, 'otel_span_id')


@pytest.mark.unit
def test_tracing_initialization_is_import_safe():
    from infrastructure.observability.tracing import setup_tracing

    provider = setup_tracing(service_name='e_cuzdan_test')

    assert provider is not None


@pytest.mark.unit
def test_tracer_context_manager_and_attributes_work():
    from infrastructure.observability.tracing import get_tracer, setup_tracing

    setup_tracing(service_name='e_cuzdan_test')
    tracer = get_tracer('tests.observability')

    with tracer.start_as_current_span('test_operation') as span:
        span.set_attribute('test.key', 'test.value')


@pytest.mark.unit
def test_tracer_fallback_is_callable_when_optional_backend_is_unavailable():
    from infrastructure.observability.tracing import get_tracer

    tracer = get_tracer('tests.observability.fallback')
    with tracer.start_as_current_span('fallback_operation'):
        assert True
