"""Unit Tests - Outbox Processor
Background worker for polling and dispatching outbox events
"""

import json
import logging
from unittest.mock import Mock, patch

import pytest

from infrastructure.background.outbox_processor import (
    EVENT_TYPE_REGISTRY,
    OutboxProcessor,
    _resolve_event_class,
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
def test_outbox_processor_start_without_app_is_disabled():
    """start() refuses to create a database polling thread without Flask app."""
    processor = OutboxProcessor(event_bus=object())

    processor.start(interval_seconds=1)

    assert processor._thread is None
    assert processor._configuration_warning_emitted is True


@pytest.mark.unit
def test_outbox_processor_start_without_app_warns_once():
    """Repeated disabled starts do not create repeated lifecycle state."""
    processor = OutboxProcessor(event_bus=object())

    processor.start(interval_seconds=1)
    processor.start(interval_seconds=1)

    assert processor._thread is None
    assert processor._configuration_warning_emitted is True


@pytest.mark.unit
def test_outbox_processor_stop_without_app():
    """stop() remains safe when start() was disabled."""
    processor = OutboxProcessor(event_bus=object())
    processor.start(interval_seconds=1)
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
    """A misconfigured loop exits without polling the database."""
    processor = OutboxProcessor(event_bus=Mock())
    processor._run_loop(interval=0.01)
    assert processor._thread is None
    assert processor._configuration_warning_emitted is True


@pytest.mark.unit
def test_outbox_processor_run_loop_with_app(app):
    """The loop polls inside app context and stops deterministically after one batch."""
    processor = OutboxProcessor(event_bus=Mock(), app=app)
    processor.process_batch = Mock(side_effect=lambda: processor._stop_event.set())

    processor._run_loop(interval=0.01)

    processor.process_batch.assert_called_once()
    assert processor._stop_event.is_set() is True


@pytest.mark.integration
def test_outbox_processor_process_batch(app):
    """A pending valid outbox message is published and marked processed."""
    from infrastructure.database.models.outbox_model import OutboxMessageModel
    from shared.db import db

    with app.app_context():
        message = OutboxMessageModel(
            id='outbox-unit-created',
            event_type='TransactionCreatedEvent',
            payload=json.dumps({
                'transaction_id': 42,
                'category': 'Maaş',
                'amount': 1000.0,
                'status': 'Ödendi',
                'tenant_id': 'default',
            }),
        )
        db.session.add(message)
        db.session.commit()
        event_bus = Mock()
        processor = OutboxProcessor(event_bus=event_bus, app=app)

        assert processor.process_batch() == 1
        db.session.refresh(message)

    assert message.processed_on is not None
    assert message.error is None
    event_bus.publish.assert_called_once()
    assert event_bus.publish.call_args.args[0].transaction_id == 42
