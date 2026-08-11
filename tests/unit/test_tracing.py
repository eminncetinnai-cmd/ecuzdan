"""
Unit Tests - Tracing
OpenTelemetry tracer provider setup tests
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
def test_tracing_module_imports():
    """Test tracing module can be imported"""
    try:
        from infrastructure.observability.tracing import setup_tracing, get_tracer
        assert setup_tracing is not None
        assert get_tracer is not None
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_tracing_module_structure():
    """Test tracing module structure"""
    try:
        import infrastructure.observability.tracing as tracing_module
        
        # Check for expected functions
        assert hasattr(tracing_module, 'setup_tracing')
        assert hasattr(tracing_module, 'get_tracer')
        assert hasattr(tracing_module, '_TRACER_PROVIDER')
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_initial():
    """Test setup_tracing initial call"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        # Reset global state
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        with patch('infrastructure.observability.tracing.trace') as mock_trace:
            mock_provider = Mock()
            mock_trace.set_tracer_provider.return_value = None
            
            with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                mock_provider_class.return_value = mock_provider
                
                with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                    mock_resource.create.return_value = Mock()
                    
                    result = setup_tracing(service_name="test_service")
                    
                    assert result == mock_provider
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_subsequent_call():
    """Test setup_tracing returns existing provider on subsequent calls"""
    try:
        from infrastructure.observability.tracing import setup_tracing
        
        import infrastructure.observability.tracing as tracing_module
        mock_existing = Mock()
        tracing_module._TRACER_PROVIDER = mock_existing
        
        result = setup_tracing(service_name="test_service")
        
        assert result == mock_existing
        
        # Reset
        tracing_module._TRACER_PROVIDER = None
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_with_console():
    """Test setup_tracing with console flag"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        with patch('infrastructure.observability.tracing.trace') as mock_trace:
            mock_provider = Mock()
            mock_trace.set_tracer_provider.return_value = None
            
            with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                mock_provider_class.return_value = mock_provider
                
                with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                    mock_resource.create.return_value = Mock()
                    
                    with patch('infrastructure.observability.tracing.ConsoleSpanExporter') as mock_exporter:
                        with patch('infrastructure.observability.tracing.SimpleSpanProcessor') as mock_processor:
                            result = setup_tracing(service_name="test_service", console=True)
                            
                            assert result == mock_provider
                            assert mock_provider.add_span_processor.called
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_no_exporter():
    """Test setup_tracing with no exporter configured"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        # Ensure no env vars
        with patch.dict(os.environ, {'OTEL_EXPORTER_OTLP_ENDPOINT': '', 'OTEL_CONSOLE_EXPORTER': ''}, clear=True):
            with patch('infrastructure.observability.tracing.trace') as mock_trace:
                mock_provider = Mock()
                mock_trace.set_tracer_provider.return_value = None
                
                with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                    mock_provider_class.return_value = mock_provider
                    
                    with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                        mock_resource.create.return_value = Mock()
                        
                        result = setup_tracing(service_name="test_service")
                        
                        assert result == mock_provider
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_get_tracer():
    """Test get_tracer function"""
    try:
        from infrastructure.observability.tracing import get_tracer
        
        with patch('infrastructure.observability.tracing.trace') as mock_trace:
            mock_tracer = Mock()
            mock_trace.get_tracer.return_value = mock_tracer
            
            result = get_tracer("test_module")
            
            assert result == mock_tracer
            mock_trace.get_tracer.assert_called_once_with("test_module")
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_default_service_name():
    """Test setup_tracing with default service name"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        with patch('infrastructure.observability.tracing.trace') as mock_trace:
            mock_provider = Mock()
            mock_trace.set_tracer_provider.return_value = None
            
            with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                mock_provider_class.return_value = mock_provider
                
                with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                    mock_resource.create.return_value = Mock()
                    
                    result = setup_tracing()
                    
                    assert result == mock_provider
                    mock_resource.create.assert_called_once()
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_with_otlp_endpoint():
    """Test setup_tracing with OTLP endpoint"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        with patch('infrastructure.observability.tracing.trace') as mock_trace:
            mock_provider = Mock()
            mock_trace.set_tracer_provider.return_value = None
            
            with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                mock_provider_class.return_value = mock_provider
                
                with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                    mock_resource.create.return_value = Mock()
                    
                    # Mock OTLP exporter import
                    with patch('infrastructure.observability.tracing.OTLPSpanExporter') as mock_exporter:
                        with patch('infrastructure.observability.tracing.BatchSpanProcessor') as mock_processor:
                            result = setup_tracing(service_name="test_service", otlp_endpoint="localhost:4317")
                            
                            assert result == mock_provider
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_otlp_import_error():
    """Test setup_tracing handles OTLP import error"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        with patch('infrastructure.observability.tracing.trace') as mock_trace:
            mock_provider = Mock()
            mock_trace.set_tracer_provider.return_value = None
            
            with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                mock_provider_class.return_value = mock_provider
                
                with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                    mock_resource.create.return_value = Mock()
                    
                    with patch.dict(os.environ, {'OTEL_EXPORTER_OTLP_ENDPOINT': 'localhost:4317'}):
                        # Simulate ImportError for OTLP exporter
                        with patch('infrastructure.observability.tracing.ConsoleSpanExporter') as mock_exporter:
                            with patch('infrastructure.observability.tracing.SimpleSpanProcessor') as mock_processor:
                                import sys
                                import builtins
                                real_import = builtins.__import__
                                
                                def mock_import(name, *args, **kwargs):
                                    if 'opentelemetry.exporter.otlp.proto.grpc.trace_exporter' in name:
                                        raise ImportError("Not installed")
                                    return real_import(name, *args, **kwargs)
                                
                                with patch('builtins.__import__', side_effect=mock_import):
                                    result = setup_tracing(service_name="test_service")
                                    
                                    assert result == mock_provider
    except ImportError:
        pytest.skip("opentelemetry not installed")


@pytest.mark.unit
def test_setup_tracing_console_env_var():
    """Test setup_tracing with OTEL_CONSOLE_EXPORTER env var"""
    try:
        from infrastructure.observability.tracing import setup_tracing, _TRACER_PROVIDER
        
        import infrastructure.observability.tracing as tracing_module
        tracing_module._TRACER_PROVIDER = None
        
        with patch.dict(os.environ, {'OTEL_CONSOLE_EXPORTER': '1'}, clear=True):
            with patch('infrastructure.observability.tracing.trace') as mock_trace:
                mock_provider = Mock()
                mock_trace.set_tracer_provider.return_value = None
                
                with patch('infrastructure.observability.tracing.TracerProvider') as mock_provider_class:
                    mock_provider_class.return_value = mock_provider
                    
                    with patch('infrastructure.observability.tracing.Resource') as mock_resource:
                        mock_resource.create.return_value = Mock()
                        
                        with patch('infrastructure.observability.tracing.ConsoleSpanExporter') as mock_exporter:
                            with patch('infrastructure.observability.tracing.SimpleSpanProcessor') as mock_processor:
                                result = setup_tracing(service_name="test_service")
                                
                                assert result == mock_provider
    except ImportError:
        pytest.skip("opentelemetry not installed")
