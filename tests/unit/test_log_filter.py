"""
Unit Tests - Log Filter
Log filter that injects OpenTelemetry trace_id and span_id into log records
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock

pytest.importorskip("opentelemetry", reason="opentelemetry module not installed")

from infrastructure.observability.log_filter import TraceContextFilter


@pytest.mark.unit
def test_trace_context_filter_imports():
    """Test that TraceContextFilter can be imported"""
    from infrastructure.observability.log_filter import TraceContextFilter
    
    assert TraceContextFilter is not None


@pytest.mark.unit
def test_trace_context_filter_module_structure():
    """Test log_filter module structure"""
    import infrastructure.observability.log_filter as log_filter_module
    
    # Check for expected class
    assert hasattr(log_filter_module, 'TraceContextFilter')
    
    # Check for expected imports
    assert hasattr(log_filter_module, 'logging')
    assert hasattr(log_filter_module, 'trace')


@pytest.mark.unit
def test_trace_context_filter_init():
    """Test TraceContextFilter initialization"""
    filter_obj = TraceContextFilter()
    
    assert filter_obj is not None
    assert filter_obj._ZERO_TRACE == "0" * 32
    assert filter_obj._ZERO_SPAN == "0" * 16


@pytest.mark.unit
def test_trace_context_filter_with_valid_span():
    """Test filter with valid span context"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_ctx = Mock()
    mock_ctx.is_valid = True
    mock_ctx.trace_id = 1234567890123456789012345678901234
    mock_ctx.span_id = 1234567890123456
    mock_span.get_span_context.return_value = mock_ctx
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'otel_trace_id')
        assert hasattr(record, 'otel_span_id')
        assert record.otel_trace_id == format(1234567890123456789012345678901234, "032x")
        assert record.otel_span_id == format(1234567890123456, "016x")


@pytest.mark.unit
def test_trace_context_filter_with_invalid_span():
    """Test filter with invalid span context"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_ctx = Mock()
    mock_ctx.is_valid = False
    mock_span.get_span_context.return_value = mock_ctx
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.otel_trace_id == "0" * 32
        assert record.otel_span_id == "0" * 16


@pytest.mark.unit
def test_trace_context_filter_with_no_span():
    """Test filter with no span context"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_span.get_span_context.return_value = None
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.otel_trace_id == "0" * 32
        assert record.otel_span_id == "0" * 16


@pytest.mark.unit
def test_trace_context_filter_zero_constants():
    """Test zero trace and span constants"""
    filter_obj = TraceContextFilter()
    
    assert filter_obj._ZERO_TRACE == "00000000000000000000000000000000"
    assert filter_obj._ZERO_SPAN == "0000000000000000"


@pytest.mark.unit
def test_trace_context_filter_extends_logging_filter():
    """Test TraceContextFilter extends logging.Filter"""
    from infrastructure.observability.log_filter import TraceContextFilter
    from logging import Filter
    
    assert issubclass(TraceContextFilter, Filter)


@pytest.mark.unit
def test_trace_context_filter_module_has_required_imports():
    """Test log_filter module has required imports"""
    import infrastructure.observability.log_filter as log_filter_module
    
    # Standard library imports
    assert hasattr(log_filter_module, 'logging')
    
    # Custom imports
    assert hasattr(log_filter_module, 'trace')


@pytest.mark.unit
def test_trace_context_filter_with_zero_trace_id():
    """Test filter with zero trace_id"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_ctx = Mock()
    mock_ctx.is_valid = True
    mock_ctx.trace_id = 0
    mock_ctx.span_id = 1234567890123456
    mock_span.get_span_context.return_value = mock_ctx
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.otel_trace_id == format(0, "032x")


@pytest.mark.unit
def test_trace_context_filter_with_zero_span_id():
    """Test filter with zero span_id"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_ctx = Mock()
    mock_ctx.is_valid = True
    mock_ctx.trace_id = 1234567890123456789012345678901234
    mock_ctx.span_id = 0
    mock_span.get_span_context.return_value = mock_ctx
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.otel_span_id == format(0, "016x")


@pytest.mark.unit
def test_trace_context_filter_multiple_records():
    """Test filter with multiple log records"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_ctx = Mock()
    mock_ctx.is_valid = True
    mock_ctx.trace_id = 1234567890123456789012345678901234
    mock_ctx.span_id = 1234567890123456
    mock_span.get_span_context.return_value = mock_ctx
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        for i in range(3):
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg=f'test message {i}',
                args=(),
                exc_info=None
            )
            
            result = filter_obj.filter(record)
            
            assert result is True
            assert record.otel_trace_id == format(1234567890123456789012345678901234, "032x")
            assert record.otel_span_id == format(1234567890123456, "016x")


@pytest.mark.unit
def test_trace_context_filter_different_log_levels():
    """Test filter with different log levels"""
    filter_obj = TraceContextFilter()
    
    mock_span = Mock()
    mock_ctx = Mock()
    mock_ctx.is_valid = True
    mock_ctx.trace_id = 1234567890123456789012345678901234
    mock_ctx.span_id = 1234567890123456
    mock_span.get_span_context.return_value = mock_ctx
    
    with patch('infrastructure.observability.log_filter.trace.get_current_span') as mock_get_span:
        mock_get_span.return_value = mock_span
        
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=1,
                msg='test message',
                args=(),
                exc_info=None
            )
            
            result = filter_obj.filter(record)
            
            assert result is True
            assert hasattr(record, 'otel_trace_id')
            assert hasattr(record, 'otel_span_id')
