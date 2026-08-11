"""Unit Tests - Outbox Processor
Background worker for polling and dispatching outbox events
"""

import pytest
import logging
import threading
from unittest.mock import patch
from infrastructure.background.outbox_processor import (
    OutboxProcessor,
    _resolve_event_class,
    EVENT_TYPE_REGISTRY,
)


@pytest.mark.unit
def test_resolve_event_class_known_type():
    """Test _resolve_event_class with known event type"""
    event_type = 'TransactionCreatedEvent'
    result = _resolve_event_class(event_type)
    assert result is not None


@pytest.mark.unit
def test_resolve_event_class_unknown_type_raises():
    """Test _resolve_event_class with unknown event type raises ValueError"""
    with pytest.raises(ValueError, match="Unknown event type"):
        _resolve_event_class('UnknownEvent')


@pytest.mark.unit
def test_outbox_processor_init():
    """Test OutboxProcessor initialization"""
    mock_event_bus = object()
    processor = OutboxProcessor(mock_event_bus)
    assert processor._event_bus is mock_event_bus
    assert processor._app is None
    assert processor._batch_size == 20
    assert processor._thread is None
    assert processor._stop_event is not None


@pytest.mark.unit
def test_outbox_processor_init_with_app():
    """Test OutboxProcessor initialization with Flask app"""
    mock_event_bus = object()
    mock_app = object()
    processor = OutboxProcessor(mock_event_bus, app=mock_app, batch_size=50)
    assert processor._event_bus is mock_event_bus
    assert processor._app is mock_app
    assert processor._batch_size == 50


@pytest.mark.unit
def test_outbox_processor_logging_available_with_handlers():
    """Test _logging_available returns True when handlers are active"""
    processor = OutboxProcessor(object())
    
    # Add a mock handler
    mock_handler = logging.StreamHandler()
    logging.root.addHandler(mock_handler)
    
    result = processor._logging_available()
    assert result is True
    
    # Clean up
    logging.root.removeHandler(mock_handler)


@pytest.mark.unit
def test_outbox_processor_logging_available_no_handlers():
    """Test _logging_available returns False when no handlers"""
    processor = OutboxProcessor(object())
    
    # Clear all handlers temporarily
    original_handlers = logging.root.handlers[:]
    logging.root.handlers.clear()
    
    result = processor._logging_available()
    assert result is False
    
    # Restore handlers
    logging.root.handlers.extend(original_handlers)


@pytest.mark.unit
def test_outbox_processor_logging_available_closed_stream():
    """Test _logging_available returns False when handler stream is closed"""
    processor = OutboxProcessor(object())
    
    # Add a handler with closed stream
    mock_handler = logging.StreamHandler()
    mock_handler.stream = type('obj', (object,), {'closed': True})()
    logging.root.addHandler(mock_handler)
    
    result = processor._logging_available()
    assert result is False
    
    # Clean up
    logging.root.removeHandler(mock_handler)


@pytest.mark.unit
def test_outbox_processor_safe_log_info():
    """Test _safe_log_info logs when logging is available"""
    processor = OutboxProcessor(object())
    
    # Add a handler
    mock_handler = logging.StreamHandler()
    logging.root.addHandler(mock_handler)
    
    # Should not raise exception
    processor._safe_log_info("Test message %s", "arg")
    
    # Clean up
    logging.root.removeHandler(mock_handler)


@pytest.mark.unit
def test_outbox_processor_safe_log_info_no_logging():
    """Test _safe_log_info silently fails when logging unavailable"""
    processor = OutboxProcessor(object())
    
    # Clear handlers
    original_handlers = logging.root.handlers[:]
    logging.root.handlers.clear()
    
    # Should not raise exception
    processor._safe_log_info("Test message")
    
    # Restore handlers
    logging.root.handlers.extend(original_handlers)


@pytest.mark.unit
def test_outbox_processor_safe_log_exception():
    """Test _safe_log_exception logs when logging is available"""
    processor = OutboxProcessor(object())
    
    # Add a handler
    mock_handler = logging.StreamHandler()
    logging.root.addHandler(mock_handler)
    
    # Should not raise exception
    processor._safe_log_exception("Test exception")
    
    # Clean up
    logging.root.removeHandler(mock_handler)


@pytest.mark.unit
def test_outbox_processor_safe_log_exception_no_logging():
    """Test _safe_log_exception silently fails when logging unavailable"""
    processor = OutboxProcessor(object())
    
    # Clear handlers
    original_handlers = logging.root.handlers[:]
    logging.root.handlers.clear()
    
    # Should not raise exception
    processor._safe_log_exception("Test exception")
    
    # Restore handlers
    logging.root.handlers.extend(original_handlers)


@pytest.mark.unit
def test_outbox_processor_start_creates_thread():
    """Test start creates and starts daemon thread"""
    mock_event_bus = object()
    processor = OutboxProcessor(mock_event_bus)
    
    processor.start(interval_seconds=1)
    
    assert processor._thread is not None
    assert processor._thread.is_alive()
    assert processor._thread.daemon is True
    
    # Stop the thread
    processor.stop()


@pytest.mark.unit
def test_outbox_processor_start_idempotent():
    """Test start is idempotent - doesn't create multiple threads"""
    mock_event_bus = object()
    processor = OutboxProcessor(mock_event_bus)
    
    processor.start(interval_seconds=1)
    first_thread = processor._thread
    
    processor.start(interval_seconds=1)
    second_thread = processor._thread
    
    assert first_thread is second_thread
    
    processor.stop()


@pytest.mark.unit
def test_outbox_processor_stop():
    """Test stop signals thread to stop and waits"""
    mock_event_bus = object()
    processor = OutboxProcessor(mock_event_bus)
    
    processor.start(interval_seconds=1)
    assert processor._thread is not None
    
    processor.stop()
    assert processor._thread is None


@pytest.mark.unit
def test_outbox_processor_stop_without_start():
    """Test stop without start doesn't raise error"""
    mock_event_bus = object()
    processor = OutboxProcessor(mock_event_bus)
    
    # Should not raise exception
    processor.stop()


@pytest.mark.unit
def test_event_type_registry():
    """Test EVENT_TYPE_REGISTRY has expected entries"""
    assert 'TransactionCreatedEvent' in EVENT_TYPE_REGISTRY
    assert 'TransactionUpdatedEvent' in EVENT_TYPE_REGISTRY
    assert 'TransactionDeletedEvent' in EVENT_TYPE_REGISTRY


@pytest.mark.unit
def test_outbox_processor_safe_log_info_exception_in_logger():
    """Test _safe_log_info handles logger exceptions gracefully"""
    processor = OutboxProcessor(object())
    
    # Add a handler
    mock_handler = logging.StreamHandler()
    logging.root.addHandler(mock_handler)
    
    # Patch logger.info to raise an exception
    import infrastructure.background.outbox_processor as processor_module
    with patch.object(processor_module.logger, 'info', side_effect=Exception('Logger error')):
        # Should not raise exception
        processor._safe_log_info("Test message")
    
    # Clean up
    logging.root.removeHandler(mock_handler)


@pytest.mark.unit
def test_outbox_processor_safe_log_exception_exception_in_logger():
    """Test _safe_log_exception handles logger exceptions gracefully"""
    processor = OutboxProcessor(object())
    
    # Add a handler
    mock_handler = logging.StreamHandler()
    logging.root.addHandler(mock_handler)
    
    # Patch logger.exception to raise an exception
    import infrastructure.background.outbox_processor as processor_module
    with patch.object(processor_module.logger, 'exception', side_effect=Exception('Logger error')):
        # Should not raise exception
        processor._safe_log_exception("Test exception")
    
    # Clean up
    logging.root.removeHandler(mock_handler)


@pytest.mark.unit
def test_outbox_processor_run_loop_without_app():
    """Test _run_loop calls process_batch when no app provided - skipped due to database dependency"""
    pytest.skip("Requires database mocking for process_batch")


@pytest.mark.unit
def test_outbox_processor_run_loop_with_app():
    """Test _run_loop uses app context when app provided - skipped due to Flask context"""
    pytest.skip("Requires Flask app context for testing")


@pytest.mark.unit
def test_outbox_processor_process_batch():
    """Test process_batch processes pending messages - skipped due to database dependency"""
    pytest.skip("Requires database mocking for process_batch")
