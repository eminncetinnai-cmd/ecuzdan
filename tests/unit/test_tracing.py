"""
Unit tests for the optional OpenTelemetry tracing integration.

The application deliberately supports both runtime modes: OpenTelemetry may be
installed and enabled, or it may be absent and the tracing API must remain a
safe no-op.  These tests mock the provider boundary so they never require a
running collector or an environment flag.
"""

import builtins
import logging
import os
from unittest.mock import Mock, patch

import pytest

from infrastructure.observability import tracing


@pytest.fixture(autouse=True)
def reset_tracing_state():
    """Keep global provider state isolated between tests."""
    previous_provider = tracing._TRACER_PROVIDER
    tracing._TRACER_PROVIDER = None
    yield
    tracing._TRACER_PROVIDER = previous_provider


@pytest.fixture
def otel_runtime():
    """Provide deterministic provider dependencies for the OTel code path."""
    provider = Mock(name='tracer_provider')
    resource = Mock(name='resource')
    trace_api = Mock(name='trace_api')
    resource_class = Mock(name='Resource')
    resource_class.create.return_value = resource
    provider_class = Mock(name='TracerProvider')

    patches = (
        patch.object(tracing, '_OTEL_AVAILABLE', True),
        patch.object(tracing, 'Resource', resource_class),
        patch.object(tracing, 'TracerProvider', provider_class),
        patch.object(tracing, 'trace', trace_api),
    )
    for active_patch in patches:
        active_patch.start()
    provider_class.return_value = provider
    try:
        yield {
            'provider': provider,
            'resource': resource,
            'resource_class': resource_class,
            'provider_class': provider_class,
            'trace': trace_api,
        }
    finally:
        for active_patch in reversed(patches):
            active_patch.stop()


@pytest.mark.unit
def test_tracing_module_imports():
    """Tracing public functions are importable in every runtime mode."""
    assert callable(tracing.setup_tracing)
    assert callable(tracing.get_tracer)


@pytest.mark.unit
def test_tracing_module_structure():
    """The module exposes the provider state used by the startup lifecycle."""
    assert hasattr(tracing, '_TRACER_PROVIDER')
    assert hasattr(tracing, '_OTEL_AVAILABLE')


@pytest.mark.unit
def test_setup_tracing_noop_when_otel_unavailable():
    """Missing OTel dependencies produce a stable no-op provider."""
    noop_provider = Mock(name='noop_provider')
    with patch.object(tracing, '_OTEL_AVAILABLE', False), \
         patch.object(tracing, 'TracerProvider', return_value=noop_provider):
        result = tracing.setup_tracing(service_name='test_service')

    assert result is noop_provider
    assert tracing._TRACER_PROVIDER is noop_provider


@pytest.mark.unit
def test_setup_tracing_initial(otel_runtime):
    """Initial setup creates a provider with the documented resource metadata."""
    result = tracing.setup_tracing(service_name='test_service')

    assert result is otel_runtime['provider']
    otel_runtime['resource_class'].create.assert_called_once_with({
        'service.name': 'test_service',
        'service.version': '15.0',
    })
    otel_runtime['provider_class'].assert_called_once_with(resource=otel_runtime['resource'])
    otel_runtime['trace'].set_tracer_provider.assert_called_once_with(otel_runtime['provider'])


@pytest.mark.unit
def test_setup_tracing_subsequent_call(otel_runtime):
    """Subsequent setup calls return the existing provider without rebuilding it."""
    first = tracing.setup_tracing(service_name='first')
    second = tracing.setup_tracing(service_name='second')

    assert second is first
    otel_runtime['provider_class'].assert_called_once_with(resource=otel_runtime['resource'])


@pytest.mark.unit
def test_setup_tracing_with_console(otel_runtime):
    """The explicit console flag attaches a simple console span processor."""
    console_exporter = Mock(name='console_exporter')
    simple_processor = Mock(name='simple_processor')
    with patch.object(tracing, 'ConsoleSpanExporter', return_value=console_exporter), \
         patch.object(tracing, 'SimpleSpanProcessor', return_value=simple_processor) as processor_class:
        result = tracing.setup_tracing(service_name='test_service', console=True)

    assert result is otel_runtime['provider']
    processor_class.assert_called_once_with(console_exporter)
    otel_runtime['provider'].add_span_processor.assert_called_once_with(simple_processor)


@pytest.mark.unit
def test_setup_tracing_no_exporter(otel_runtime):
    """No endpoint and no console flag leave the provider without exporters."""
    with patch.dict(os.environ, {'OTEL_EXPORTER_OTLP_ENDPOINT': '', 'OTEL_CONSOLE_EXPORTER': ''}, clear=True):
        result = tracing.setup_tracing(service_name='test_service')

    assert result is otel_runtime['provider']
    otel_runtime['provider'].add_span_processor.assert_not_called()


@pytest.mark.unit
def test_setup_tracing_with_otlp_import_error(otel_runtime):
    """A missing OTLP exporter falls back to the console processor."""
    console_exporter = Mock(name='fallback_console_exporter')
    simple_processor = Mock(name='fallback_simple_processor')
    real_import = builtins.__import__

    def import_without_otlp(name, *args, **kwargs):
        if name.startswith('opentelemetry.exporter.otlp.proto.grpc.trace_exporter'):
            raise ImportError('OTLP exporter unavailable for test')
        return real_import(name, *args, **kwargs)

    with patch.object(tracing, 'ConsoleSpanExporter', return_value=console_exporter), \
         patch.object(tracing, 'SimpleSpanProcessor', return_value=simple_processor) as processor_class, \
         patch('builtins.__import__', side_effect=import_without_otlp):
        result = tracing.setup_tracing(service_name='test_service', otlp_endpoint='localhost:4317')

    assert result is otel_runtime['provider']
    processor_class.assert_called_once_with(console_exporter)
    otel_runtime['provider'].add_span_processor.assert_called_once_with(simple_processor)


@pytest.mark.unit
def test_setup_tracing_console_env_var(otel_runtime):
    """OTEL_CONSOLE_EXPORTER enables console export without an explicit argument."""
    console_exporter = Mock(name='env_console_exporter')
    simple_processor = Mock(name='env_simple_processor')
    with patch.dict(os.environ, {'OTEL_CONSOLE_EXPORTER': 'true'}, clear=True), \
         patch.object(tracing, 'ConsoleSpanExporter', return_value=console_exporter), \
         patch.object(tracing, 'SimpleSpanProcessor', return_value=simple_processor) as processor_class:
        tracing.setup_tracing(service_name='test_service')

    processor_class.assert_called_once_with(console_exporter)
    otel_runtime['provider'].add_span_processor.assert_called_once_with(simple_processor)


@pytest.mark.unit
def test_get_tracer_otel_runtime(otel_runtime):
    """OTel runtime delegates named tracer creation to the trace API."""
    tracer = Mock(name='tracer')
    otel_runtime['trace'].get_tracer.return_value = tracer

    result = tracing.get_tracer('test_module')

    assert result is tracer
    otel_runtime['trace'].get_tracer.assert_called_once_with('test_module')


@pytest.mark.unit
def test_get_tracer_noop_runtime():
    """No-OTel runtime still exposes a usable span context manager."""
    with patch.object(tracing, '_OTEL_AVAILABLE', False):
        tracer = tracing.get_tracer('test_module')
        with tracer.start_as_current_span('operation') as span:
            assert span.set_attribute('key', 'value') is None


@pytest.mark.unit
def test_setup_tracing_logs_noop_mode(caplog):
    """No-op setup remains observable without treating absence as an error."""
    with patch.object(tracing, '_OTEL_AVAILABLE', False), \
         patch.object(tracing, 'TracerProvider', return_value=Mock()):
        with caplog.at_level(logging.INFO, logger='infrastructure.observability.tracing'):
            tracing.setup_tracing()

    assert any('tracing is disabled' in record.message for record in caplog.records)
