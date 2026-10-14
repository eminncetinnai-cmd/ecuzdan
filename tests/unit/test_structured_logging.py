"""
Unit Tests - Structured Logging
Structured logging system tests
"""

import json
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.structured_logging import (
    JSONFormatter,
    LogContext,
    StructuredLogger,
    StructuredLogHandler,
    get_structured_logger,
    setup_structured_logging,
)


@pytest.mark.unit
def test_structured_logging_module_imports():
    """Test structured_logging module can be imported"""
    from utils.structured_logging import JSONFormatter, LogContext, StructuredLogger
    assert JSONFormatter is not None
    assert StructuredLogHandler is not None
    assert LogContext is not None
    assert StructuredLogger is not None


@pytest.mark.unit
def test_structured_logging_module_structure():
    """Test structured_logging module structure"""
    import utils.structured_logging as sl_module

    # Check for expected classes and functions
    assert hasattr(sl_module, 'JSONFormatter')
    assert hasattr(sl_module, 'StructuredLogHandler')
    assert hasattr(sl_module, 'LogContext')
    assert hasattr(sl_module, 'StructuredLogger')
    assert hasattr(sl_module, 'get_structured_logger')
    assert hasattr(sl_module, 'setup_structured_logging')


@pytest.mark.unit
def test_json_formatter_initialization():
    """Test JSONFormatter initialization"""
    formatter = JSONFormatter()

    assert formatter.timestamp_format == '%Y-%m-%dT%H:%M:%S.%fZ'


@pytest.mark.unit
def test_json_formatter_custom_timestamp_format():
    """Test JSONFormatter with custom timestamp format"""
    formatter = JSONFormatter(timestamp_format='%Y-%m-%d %H:%M:%S')

    assert formatter.timestamp_format == '%Y-%m-%d %H:%M:%S'


@pytest.mark.unit
def test_json_formatter_format():
    """Test JSONFormatter format method"""
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=10,
        msg='Test message',
        args=(),
        exc_info=None
    )

    result = formatter.format(record)

    assert isinstance(result, str)
    log_data = json.loads(result)
    assert log_data['level'] == 'INFO'
    assert log_data['logger'] == 'test_logger'
    assert log_data['message'] == 'Test message'


@pytest.mark.unit
def test_json_formatter_with_otel_attributes():
    """Test JSONFormatter with OTel attributes"""
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=10,
        msg='Test message',
        args=(),
        exc_info=None
    )
    record.otel_trace_id = 'trace_123'
    record.otel_span_id = 'span_456'

    result = formatter.format(record)
    log_data = json.loads(result)

    assert log_data['trace_id'] == 'trace_123'
    assert log_data['span_id'] == 'span_456'


@pytest.mark.unit
def test_json_formatter_with_exception():
    """JSONFormatter serializes exception type, message and traceback."""
    formatter = JSONFormatter()
    try:
        raise ValueError('format sentinel')
    except ValueError:
        record = logging.LogRecord(
            name='test_logger', level=logging.ERROR, pathname='test.py',
            lineno=10, msg='Failure', args=(), exc_info=None
        )
        record.exc_info = __import__('sys').exc_info()

    payload = json.loads(formatter.format(record))
    assert payload['exception']['type'] == 'ValueError'
    assert payload['exception']['message'] == 'format sentinel'
    assert 'ValueError' in payload['exception']['traceback']


@pytest.mark.unit
def test_json_formatter_with_extra_fields():
    """Test JSONFormatter with extra fields"""
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=10,
        msg='Test message',
        args=(),
        exc_info=None
    )
    record.user_id = '123'
    record.request_id = 'abc'

    result = formatter.format(record)
    log_data = json.loads(result)

    assert log_data['user_id'] != '123'
    assert log_data['user_id'].startswith('user_')
    assert log_data['request_id'] == 'abc'


@pytest.mark.unit
def test_structured_log_handler_initialization():
    """StructuredLogHandler wraps a configured rotating file handler."""
    with patch('logging.handlers.RotatingFileHandler') as handler_class:
        handler = MagicMock()
        handler_class.return_value = handler
        wrapper = StructuredLogHandler('structured.log')

    handler_class.assert_called_once_with(
        'structured.log', maxBytes=10 * 1024 * 1024, backupCount=10, encoding='utf-8'
    )
    handler.setFormatter.assert_called_once()
    assert wrapper.handler is handler


@pytest.mark.unit
def test_structured_log_handler_custom_params():
    """StructuredLogHandler forwards custom rotation settings."""
    with patch('logging.handlers.RotatingFileHandler') as handler_class:
        handler_class.return_value = MagicMock()
        StructuredLogHandler('custom.log', max_bytes=1234, backup_count=2)

    handler_class.assert_called_once_with(
        'custom.log', maxBytes=1234, backupCount=2, encoding='utf-8'
    )


@pytest.mark.unit
def test_structured_log_handler_emit():
    """StructuredLogHandler delegates emit when the wrapped stream is open."""
    with patch('logging.handlers.RotatingFileHandler') as handler_class:
        handler = MagicMock()
        handler.stream = Mock(closed=False)
        handler_class.return_value = handler
        wrapper = StructuredLogHandler('structured.log')
        record = logging.LogRecord('test', logging.INFO, 'test.py', 1, 'message', (), None)
        wrapper.emit(record)

    handler.emit.assert_called_once_with(record)


@pytest.mark.unit
def test_structured_log_handler_emit_exception():
    """Handler errors are routed through handleError without escaping."""
    with patch('logging.handlers.RotatingFileHandler') as handler_class:
        handler = MagicMock()
        handler.stream = Mock(closed=False)
        handler.emit.side_effect = OSError('write sentinel')
        handler_class.return_value = handler
        wrapper = StructuredLogHandler('structured.log')
        wrapper.handleError = Mock()
        record = logging.LogRecord('test', logging.INFO, 'test.py', 1, 'message', (), None)
        wrapper.emit(record)

    wrapper.handleError.assert_called_once_with(record)


@pytest.mark.unit
def test_structured_log_handler_close():
    """StructuredLogHandler closes its wrapped rotating handler."""
    with patch('logging.handlers.RotatingFileHandler') as handler_class:
        handler = MagicMock()
        handler_class.return_value = handler
        wrapper = StructuredLogHandler('structured.log')
        wrapper.close()

    handler.close.assert_called_once()


@pytest.mark.unit
def test_log_context_initialization():
    """Test LogContext initialization"""
    context = LogContext(user_id='123', request_id='abc')

    assert context.context == {'user_id': '123', 'request_id': 'abc'}
    assert context.logger is not None


@pytest.mark.unit
def test_log_context_enter():
    """Test LogContext enter method"""
    context = LogContext(user_id='123')

    with patch('logging.getLogRecordFactory') as mock_get_factory:
        mock_old_factory = Mock()
        mock_get_factory.return_value = mock_old_factory

        with patch('logging.setLogRecordFactory') as mock_set_factory:
            result = context.__enter__()

            assert result is context
            mock_set_factory.assert_called()


@pytest.mark.unit
def test_log_context_exit():
    """Test LogContext exit method"""
    context = LogContext(user_id='123')
    context._old_factory = Mock()

    with patch('logging.setLogRecordFactory') as mock_set_factory:
        result = context.__exit__(None, None, None)

        assert result is False
        mock_set_factory.assert_called_once_with(context._old_factory)


@pytest.mark.unit
def test_log_context_context_manager():
    """Test LogContext as context manager"""
    with patch('logging.getLogRecordFactory'):
        with patch('logging.setLogRecordFactory') as mock_set_factory:
            with LogContext(user_id='123') as ctx:
                assert ctx is not None

            # Should restore old factory
            assert mock_set_factory.call_count == 2


@pytest.mark.unit
def test_structured_logger_initialization():
    """Test StructuredLogger initialization"""
    logger = StructuredLogger('test_logger')

    assert logger.logger is not None
    assert logger.logger.name == 'test_logger'


@pytest.mark.unit
def test_structured_logger_debug():
    """Test StructuredLogger debug method"""
    logger = StructuredLogger('test_logger')

    with patch.object(logger.logger, 'log') as mock_log:
        logger.debug('Debug message', user_id='123')

        mock_log.assert_called_once()


@pytest.mark.unit
def test_structured_logger_info():
    """Test StructuredLogger info method"""
    logger = StructuredLogger('test_logger')

    with patch.object(logger.logger, 'log') as mock_log:
        logger.info('Info message', user_id='123')

        mock_log.assert_called_once()


@pytest.mark.unit
def test_structured_logger_warning():
    """Test StructuredLogger warning method"""
    logger = StructuredLogger('test_logger')

    with patch.object(logger.logger, 'log') as mock_log:
        logger.warning('Warning message', user_id='123')

        mock_log.assert_called_once()


@pytest.mark.unit
def test_structured_logger_error():
    """Test StructuredLogger error method"""
    logger = StructuredLogger('test_logger')

    with patch.object(logger.logger, 'log') as mock_log:
        logger.error('Error message', user_id='123')

        mock_log.assert_called_once()


@pytest.mark.unit
def test_structured_logger_critical():
    """Test StructuredLogger critical method"""
    logger = StructuredLogger('test_logger')

    with patch.object(logger.logger, 'log') as mock_log:
        logger.critical('Critical message', user_id='123')

        mock_log.assert_called_once()


@pytest.mark.unit
def test_structured_logger_exception():
    """Test StructuredLogger exception method"""
    logger = StructuredLogger('test_logger')

    with patch.object(logger.logger, 'log') as mock_log:
        logger.exception('Exception message', user_id='123')

        mock_log.assert_called_once()


@pytest.mark.unit
def test_get_structured_logger():
    """Test get_structured_logger function"""
    logger = get_structured_logger('test_logger')

    assert isinstance(logger, StructuredLogger)
    assert logger.logger.name == 'test_logger'


@pytest.mark.unit
def test_setup_structured_logging():
    """Test setup_structured_logging function"""
    with patch('os.makedirs') as mock_makedirs:
        with patch('utils.structured_logging.StructuredLogHandler') as mock_handler:
            mock_handler_instance = MagicMock()
            mock_handler.return_value = mock_handler_instance

            with patch('logging.getLogger') as mock_get_logger:
                mock_root_logger = Mock()
                mock_get_logger.return_value = mock_root_logger

                handler1, handler2 = setup_structured_logging('/tmp/logs')

                assert handler1 is not None
                assert handler2 is not None
                mock_makedirs.assert_called_once_with('/tmp/logs', exist_ok=True)
