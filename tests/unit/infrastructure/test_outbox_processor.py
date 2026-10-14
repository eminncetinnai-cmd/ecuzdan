import io
import json
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest
from flask import Flask

from infrastructure.background.outbox_processor import (
    EVENT_TYPE_REGISTRY,
    OutboxProcessor,
    _resolve_event_class,
)
from infrastructure.database.models.outbox_model import OutboxMessageModel
from shared.db import db


def test_outbox_processor_stop_is_safe_when_logging_stream_is_closed(monkeypatch):
    """OutboxProcessor.stop() should not fail if the logging subsystem is shutting down."""
    dummy_event_bus = object()
    processor = OutboxProcessor(event_bus=dummy_event_bus)

    class DummyThread:
        def is_alive(self):
            return False

        def join(self, timeout=None):
            return None

    processor._thread = DummyThread()

    closed_stream = io.StringIO()
    closed_stream.close()
    handler = logging.StreamHandler(closed_stream)
    logging.root.addHandler(handler)

    try:
        assert processor._logging_available() is False
        processor.stop()
    finally:
        logging.root.removeHandler(handler)


@pytest.mark.unit
def test_resolve_event_class_success():
    """Test _resolve_event_class with valid event type"""
    with patch('importlib.import_module') as mock_import:
        mock_module = MagicMock()
        mock_event_class = Mock()
        mock_module.TransactionCreatedEvent = mock_event_class
        mock_import.return_value = mock_module

        result = _resolve_event_class('TransactionCreatedEvent')

        assert result == mock_event_class


@pytest.mark.unit
def test_resolve_event_class_unknown_type():
    """Test _resolve_event_class with unknown event type"""
    with pytest.raises(ValueError, match="Unknown event type"):
        _resolve_event_class('UnknownEvent')


@pytest.mark.unit
def test_event_type_registry():
    """Test EVENT_TYPE_REGISTRY is defined"""
    assert isinstance(EVENT_TYPE_REGISTRY, dict)
    assert 'TransactionCreatedEvent' in EVENT_TYPE_REGISTRY


@pytest.mark.unit
def test_outbox_processor_initialization():
    """Test OutboxProcessor initialization"""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus)

    assert processor._event_bus == mock_event_bus
    assert processor._app is None
    assert processor._batch_size == 20
    assert processor._thread is None
    assert processor._stop_event is not None


@pytest.mark.unit
def test_outbox_processor_initialization_with_app():
    """Test OutboxProcessor initialization with Flask app"""
    mock_event_bus = Mock()
    mock_app = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus, app=mock_app, batch_size=10)

    assert processor._event_bus == mock_event_bus
    assert processor._app == mock_app
    assert processor._batch_size == 10


@pytest.mark.unit
def test_outbox_processor_start(app):
    """A processor starts when its Flask app is registered with shared SQLAlchemy."""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus, app=app)

    processor.start(interval_seconds=0.01)

    assert processor._thread is not None
    assert processor._thread.is_alive()

    # Clean up
    processor.stop()


@pytest.mark.unit
def test_outbox_processor_start_already_running(app):
    """Test OutboxProcessor start when already running."""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus, app=app)

    processor.start(interval_seconds=0.01)

    # Try to start again - should not create new thread
    original_thread = processor._thread
    processor.start(interval_seconds=1)

    assert processor._thread == original_thread

    # Clean up
    processor.stop()


@pytest.mark.unit
def test_outbox_processor_stop(app):
    """Test OutboxProcessor stop method."""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus, app=app)

    processor.start(interval_seconds=0.01)
    assert processor._thread is not None

    processor.stop()

    assert processor._thread is None


@pytest.mark.unit
def test_outbox_processor_logging_available():
    """Test _logging_available method"""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus)

    # Should return True when logging is available
    result = processor._logging_available()
    assert isinstance(result, bool)


@pytest.mark.unit
def test_outbox_processor_safe_log_info():
    """Test _safe_log_info method"""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus)

    # Should not raise exception
    processor._safe_log_info("Test message")


@pytest.mark.unit
def test_outbox_processor_safe_log_exception():
    """Test _safe_log_exception method"""
    mock_event_bus = Mock()
    processor = OutboxProcessor(event_bus=mock_event_bus)

    # Should not raise exception
    processor._safe_log_exception("Test exception")


@pytest.mark.unit
def test_outbox_processor_start_with_unregistered_app_is_disabled():
    """A worker must reject a Flask app that is not registered with shared SQLAlchemy."""
    processor = OutboxProcessor(event_bus=Mock(), app=Flask(__name__))

    processor.start(interval_seconds=0.01)

    assert processor._thread is None
    assert processor._configuration_warning_emitted is True


def test_outbox_processor_start_without_app_is_disabled():
    """A processor without a Flask app must not start a broken polling thread."""
    processor = OutboxProcessor(event_bus=Mock())

    processor.start(interval_seconds=0.01)

    assert processor._thread is None


@pytest.mark.unit
def test_outbox_processor_process_batch_no_pending(app):
    """An empty outbox is a successful no-op."""
    with app.app_context():
        processor = OutboxProcessor(event_bus=Mock(), app=app)

        assert processor.process_batch() == 0


@pytest.mark.unit
def test_outbox_processor_process_batch_with_messages(app):
    """A valid event is published and marked processed atomically."""
    with app.app_context():
        event_bus = Mock()
        message = OutboxMessageModel(
            id='outbox-test-created',
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

        processor = OutboxProcessor(event_bus=event_bus, app=app)

        assert processor.process_batch() == 1
        db.session.refresh(message)
        assert message.processed_on is not None
        assert message.error is None
        event_bus.publish.assert_called_once()
        assert event_bus.publish.call_args.args[0].transaction_id == 42


@pytest.mark.unit
def test_outbox_processor_process_batch_exception_handling(app):
    """An unknown event is retained with a retryable error marker."""
    with app.app_context():
        message = OutboxMessageModel(
            id='outbox-test-invalid',
            event_type='UnknownEvent',
            payload='{}',
        )
        db.session.add(message)
        db.session.commit()

        processor = OutboxProcessor(event_bus=Mock(), app=app)

        assert processor.process_batch() == 0
        db.session.refresh(message)
        assert message.processed_on is None
        assert 'Unknown event type' in message.error


@pytest.mark.unit
def test_outbox_processor_run_loop(app):
    """The loop executes once and can stop deterministically after a batch."""
    processor = OutboxProcessor(event_bus=Mock(), app=app)

    def process_once():
        processor._stop_event.set()
        return 0

    processor.process_batch = Mock(side_effect=process_once)
    processor._run_loop(interval=0)

    processor.process_batch.assert_called_once()
    assert processor._stop_event.is_set()
