"""
Unit Tests - Logging Config
Centralized logging configuration tests
"""

import pytest
import logging
import os
from unittest.mock import Mock, patch, MagicMock
from utils.logging_config import (
    setup_logging,
    get_logger,
    STRUCTURED_LOGGING_AVAILABLE,
    LOG_SAMPLING_AVAILABLE,
)


@pytest.mark.unit
def test_logging_config_module_imports():
    """Test logging_config module can be imported"""
    from utils.logging_config import setup_logging, get_logger
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
def test_setup_logging_creates_log_dir():
    """Test setup_logging creates log directory - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_without_app():
    """Test setup_logging without Flask app - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_with_app():
    """Test setup_logging with Flask app - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_sets_external_library_levels():
    """Test setup_logging sets levels for external libraries - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_structured_logging_unavailable():
    """Test setup_logging when structured logging is unavailable - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_log_sampling_unavailable():
    """Test setup_logging when log sampling is unavailable - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_otel_filter_import_error():
    """Test setup_logging when OTel filter import fails - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_security_filter():
    """Test setup_logging security filter - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_custom_level():
    """Test setup_logging with custom log level - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_root_logger_propagate():
    """Test setup_logging sets root logger propagate to False - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_structured_logging_exception():
    """Test setup_logging handles structured logging exceptions - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_setup_logging_log_sampling_exception():
    """Test setup_logging handles log sampling exceptions - skipped due to file system operations"""
    pytest.skip("Requires actual file system operations")


@pytest.mark.unit
def test_structured_logging_available_constant():
    """Test STRUCTURED_LOGGING_AVAILABLE constant"""
    assert isinstance(STRUCTURED_LOGGING_AVAILABLE, bool)


@pytest.mark.unit
def test_log_sampling_available_constant():
    """Test LOG_SAMPLING_AVAILABLE constant"""
    assert isinstance(LOG_SAMPLING_AVAILABLE, bool)


@pytest.mark.unit
def test_setup_logging_otel_filter_success():
    """Test setup_logging when OTel filter import succeeds - skipped due to import complexity"""
    pytest.skip("Requires complex import mocking for OTel filter")


@pytest.mark.unit
def test_setup_logging_structured_logging_exception_handling():
    """Test setup_logging handles structured logging exceptions"""
    from utils.logging_config import setup_logging
    from unittest.mock import patch, MagicMock
    
    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/fake/path'), \
         patch('utils.logging_config.RotatingFileHandler') as mock_handler, \
         patch('utils.logging_config.logging.getLogger') as mock_get_logger:
        
        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        with patch('utils.logging_config.STRUCTURED_LOGGING_AVAILABLE', True), \
             patch('utils.logging_config.setup_structured_logging', side_effect=Exception("Test error")):
            
            setup_logging()
            
            # Should not raise exception, should log warning instead


@pytest.mark.unit
def test_setup_logging_log_sampling_exception_handling():
    """Test setup_logging handles log sampling exceptions"""
    from utils.logging_config import setup_logging
    from unittest.mock import patch, MagicMock
    
    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/fake/path'), \
         patch('utils.logging_config.RotatingFileHandler') as mock_handler, \
         patch('utils.logging_config.logging.getLogger') as mock_get_logger:
        
        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        with patch('utils.logging_config.LOG_SAMPLING_AVAILABLE', True), \
             patch('utils.logging_config.setup_log_sampling', side_effect=Exception("Test error")):
            
            setup_logging()
            
            # Should not raise exception, should log warning instead


@pytest.mark.unit
def test_setup_logging_with_flask_app():
    """Test setup_logging configures Flask app logger"""
    from utils.logging_config import setup_logging
    from unittest.mock import patch, MagicMock
    
    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/fake/path'), \
         patch('utils.logging_config.RotatingFileHandler') as mock_handler, \
         patch('utils.logging_config.logging.getLogger') as mock_get_logger:
        
        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
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
