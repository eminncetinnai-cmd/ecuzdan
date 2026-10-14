"""
Unit Tests - Logging Config
Centralized logging configuration tests
"""

import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.logging_config import (
    LOG_SAMPLING_AVAILABLE,
    STRUCTURED_LOGGING_AVAILABLE,
    NonDeletingRotatingFileHandler,
    get_logger,
    setup_logging,
)


@pytest.fixture
def logging_mocks():
    """Isolate setup_logging from real files and global logger handlers."""
    with patch('utils.logging_config.os.makedirs') as makedirs, \
         patch('utils.logging_config.RotatingFileHandler') as handler_class, \
         patch('utils.logging_config.NonDeletingRotatingFileHandler') as security_handler_class, \
         patch('utils.logging_config.logging.getLogger') as get_logger, \
         patch('utils.logging_config.STRUCTURED_LOGGING_AVAILABLE', False), \
         patch('utils.logging_config.LOG_SAMPLING_AVAILABLE', False):
        root_logger = MagicMock()
        handler = MagicMock()
        handler_class.return_value = handler
        security_handler_class.return_value = handler
        get_logger.return_value = root_logger
        yield {
            'makedirs': makedirs,
            'handler_class': handler_class,
            'security_handler_class': security_handler_class,
            'handler': handler,
            'get_logger': get_logger,
            'root_logger': root_logger,
        }


@pytest.mark.unit
def test_security_handler_rollover_does_not_delete_existing_backups():
    """Security rotation creates a new backup without enforcing a deletion count."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir) / 'security.log'
        older = Path(f'{base}.older')
        older.write_text('older security fixture', encoding='utf-8')
        handler = NonDeletingRotatingFileHandler(str(base), maxBytes=1, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        try:
            assert handler.handle(logging.LogRecord('security', logging.INFO, __file__, 1, 'new fixture', (), None))
        finally:
            handler.close()
        backups = [path for path in Path(temp_dir).iterdir() if path.name.startswith('security.log.')]
        assert older.exists()
        assert len(backups) == 2
        assert all(path.stat().st_size >= 0 for path in backups)


@pytest.mark.unit
def test_logging_config_module_imports():
    """Test logging_config module can be imported"""
    from utils.logging_config import get_logger
    assert setup_logging is not None
    assert get_logger is not None


@pytest.mark.unit
def test_logging_config_module_structure():
    """Test logging_config module structure"""
    import utils.logging_config as lc_module

    # Check for expected functions and constants
    assert hasattr(lc_module, 'setup_logging')
    assert hasattr(lc_module, 'get_logger')
    assert hasattr(lc_module, 'STRUCTURED_LOGGING_AVAILABLE')
    assert hasattr(lc_module, 'LOG_SAMPLING_AVAILABLE')


@pytest.mark.unit
def test_get_logger():
    """Test get_logger function"""
    logger = get_logger('test_logger')

    assert logger is not None
    assert logger.name == 'test_logger'


@pytest.mark.unit
def test_get_logger_default():
    """Test get_logger with default name"""
    logger = get_logger(__name__)

    assert logger is not None


@pytest.mark.unit
def test_setup_logging_creates_log_dir(logging_mocks):
    """setup_logging creates the configured project log directory."""
    setup_logging()
    logging_mocks['makedirs'].assert_called_once()
    assert logging_mocks['handler_class'].call_count == 2
    assert logging_mocks['security_handler_class'].call_count == 1
    security_call = logging_mocks['security_handler_class'].call_args
    assert security_call.args[0].endswith('e_cuzdan_security.log')
    assert security_call.kwargs == {
        'maxBytes': 5 * 1024 * 1024,
        'encoding': 'utf-8',
    }


@pytest.mark.unit
def test_setup_logging_without_app(logging_mocks):
    """setup_logging configures the root logger without an app object."""
    setup_logging()
    assert logging_mocks['root_logger'].setLevel.called
    assert logging_mocks['root_logger'].propagate is False


@pytest.mark.unit
def test_setup_logging_with_app(logging_mocks):
    """setup_logging attaches the same handlers to the Flask app logger."""
    app = MagicMock()
    app.logger = MagicMock()
    setup_logging(app=app)
    assert app.logger.handlers == logging_mocks['root_logger'].handlers
    assert app.logger.propagate is False


@pytest.mark.unit
def test_setup_logging_sets_external_library_levels(logging_mocks):
    """setup_logging applies warning/critical levels to noisy dependencies."""
    setup_logging()
    get_logger_mock = logging_mocks['get_logger']
    get_logger_mock.assert_any_call('werkzeug')
    get_logger_mock.assert_any_call('urllib3')
    get_logger_mock.assert_any_call('yfinance')


@pytest.mark.unit
def test_setup_logging_structured_logging_unavailable(logging_mocks):
    """setup_logging succeeds when structured logging is not installed."""
    with patch('utils.logging_config.STRUCTURED_LOGGING_AVAILABLE', False):
        setup_logging()
    assert logging_mocks['root_logger'].handlers


@pytest.mark.unit
def test_setup_logging_log_sampling_unavailable(logging_mocks):
    """setup_logging succeeds when log sampling is not installed."""
    with patch('utils.logging_config.LOG_SAMPLING_AVAILABLE', False):
        setup_logging()
    assert logging_mocks['root_logger'].handlers


@pytest.mark.unit
def test_setup_logging_otel_filter_import_error(logging_mocks):
    """setup_logging falls back to a zero-id filter if OTel filter import fails."""
    with patch.dict(sys.modules, {'infrastructure.observability.log_filter': None}):
        setup_logging()
    assert logging_mocks['handler'].addFilter.call_count >= 3


@pytest.mark.unit
def test_setup_logging_security_filter(logging_mocks):
    """setup_logging attaches a dedicated security filter to the handlers."""
    setup_logging()
    assert logging_mocks['handler'].addFilter.call_count >= 4


@pytest.mark.unit
def test_setup_logging_custom_level(logging_mocks):
    """Custom level is propagated to the main rotating handler and root logger."""
    setup_logging(level=logging.DEBUG)
    assert any(
        call.args == (logging.DEBUG,)
        for call in logging_mocks['root_logger'].setLevel.call_args_list
    )
    assert any(call.args == (logging.DEBUG,) for call in logging_mocks['handler'].setLevel.call_args_list)


@pytest.mark.unit
def test_setup_logging_root_logger_propagate(logging_mocks):
    """setup_logging disables root propagation to prevent duplicate records."""
    setup_logging()
    assert logging_mocks['root_logger'].propagate is False


@pytest.mark.unit
def test_setup_logging_structured_logging_exception(logging_mocks):
    """Structured logging errors do not abort application logging setup."""
    with patch('utils.logging_config.STRUCTURED_LOGGING_AVAILABLE', True), \
         patch('utils.logging_config.setup_structured_logging', side_effect=Exception('Test error')):
        setup_logging()
    assert logging_mocks['root_logger'].handlers


@pytest.mark.unit
def test_setup_logging_log_sampling_exception(logging_mocks):
    """Log sampling errors do not abort application logging setup."""
    with patch('utils.logging_config.LOG_SAMPLING_AVAILABLE', True), \
         patch('utils.logging_config.setup_log_sampling', side_effect=Exception('Test error')):
        setup_logging()
    assert logging_mocks['root_logger'].handlers


@pytest.mark.unit
def test_structured_logging_available_constant():
    """Test STRUCTURED_LOGGING_AVAILABLE constant"""
    assert isinstance(STRUCTURED_LOGGING_AVAILABLE, bool)


@pytest.mark.unit
def test_log_sampling_available_constant():
    """Test LOG_SAMPLING_AVAILABLE constant"""
    assert isinstance(LOG_SAMPLING_AVAILABLE, bool)


@pytest.mark.unit
def test_setup_logging_otel_filter_success(logging_mocks):
    """setup_logging uses the available TraceContextFilter implementation."""
    with patch('infrastructure.observability.log_filter.TraceContextFilter') as filter_class:
        setup_logging()
    filter_class.assert_called_once_with()


@pytest.mark.unit
def test_setup_logging_structured_logging_exception_handling():
    """Test setup_logging handles structured logging exceptions"""

    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/fake/path'), \
         patch('utils.logging_config.RotatingFileHandler') as mock_handler, \
         patch('utils.logging_config.NonDeletingRotatingFileHandler') as mock_security_handler, \
         patch('utils.logging_config.logging.getLogger') as mock_get_logger:

        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
        mock_security_handler.return_value = mock_handler_instance
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger

        with patch('utils.logging_config.STRUCTURED_LOGGING_AVAILABLE', True), \
             patch('utils.logging_config.setup_structured_logging', side_effect=Exception("Test error")):

            setup_logging()

            # Should not raise exception, should log warning instead


@pytest.mark.unit
def test_setup_logging_log_sampling_exception_handling():
    """Test setup_logging handles log sampling exceptions"""

    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/fake/path'), \
         patch('utils.logging_config.RotatingFileHandler') as mock_handler, \
         patch('utils.logging_config.NonDeletingRotatingFileHandler') as mock_security_handler, \
         patch('utils.logging_config.logging.getLogger') as mock_get_logger:

        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
        mock_security_handler.return_value = mock_handler_instance
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger

        with patch('utils.logging_config.LOG_SAMPLING_AVAILABLE', True), \
             patch('utils.logging_config.setup_log_sampling', side_effect=Exception("Test error")):

            setup_logging()

            # Should not raise exception, should log warning instead


@pytest.mark.unit
def test_setup_logging_with_flask_app():
    """Test setup_logging configures Flask app logger"""

    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/fake/path'), \
         patch('utils.logging_config.RotatingFileHandler') as mock_handler, \
         patch('utils.logging_config.NonDeletingRotatingFileHandler') as mock_security_handler, \
         patch('utils.logging_config.logging.getLogger') as mock_get_logger:

        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
        mock_security_handler.return_value = mock_handler_instance
        mock_root_logger = MagicMock()
        mock_root_logger.handlers = []
        mock_get_logger.return_value = mock_root_logger

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        setup_logging(app=mock_app)

        # Verify app logger is configured
        assert mock_app.logger.handlers == mock_root_logger.handlers
        mock_app.logger.setLevel.assert_called()
        assert mock_app.logger.propagate is False
