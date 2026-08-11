"""
Centralized logging configuration for the E-Cüzdan application.
Provides consistent logging format and level control across all modules.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Structured logging import
try:
    from utils.structured_logging import setup_structured_logging, JSONFormatter
    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    STRUCTURED_LOGGING_AVAILABLE = False

# Log sampling import
try:
    from utils.log_sampling import setup_log_sampling
    LOG_SAMPLING_AVAILABLE = True
except ImportError:
    LOG_SAMPLING_AVAILABLE = False


def setup_logging(app=None, level=logging.INFO):
    """
    Configure centralized logging for the application.

    Args:
        app: Flask application instance (optional)
        level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Setup OTel context filter before formatter
    try:
        from infrastructure.observability.log_filter import TraceContextFilter
        otel_filter = TraceContextFilter()
    except ImportError:
        # Fallback filter that just adds zeroes if not available
        class DummyTraceFilter(logging.Filter):
            def filter(self, record):
                record.otel_trace_id = "0" * 32
                record.otel_span_id = "0" * 16
                return True
        otel_filter = DummyTraceFilter()

    # Create a formatter with OTel trace/span IDs
    formatter = logging.Formatter(
        '%(asctime)s [%(otel_trace_id)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Main log file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'e_cuzdan.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    file_handler.addFilter(otel_filter)

    # ERROR and CRITICAL log file handler (separate file)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'e_cuzdan_errors.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(otel_filter)

    # SECURITY log file handler (separate file)
    security_handler = RotatingFileHandler(
        os.path.join(log_dir, 'e_cuzdan_security.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    security_handler.setFormatter(formatter)
    security_handler.setLevel(logging.INFO)
    
    # Security filter to only log security-related messages
    class SecurityFilter(logging.Filter):
        def filter(self, record):
            security_keywords = ['authentication', 'unauthorized', 'security', 'login', 'logout', 'permission', 'access']
            message = record.getMessage().lower()
            return any(keyword in message for keyword in security_keywords)
    
    security_handler.addFilter(SecurityFilter())
    security_handler.addFilter(otel_filter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(otel_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [file_handler, error_handler, security_handler, console_handler]
    root_logger.propagate = False

    # Structured logging setup (opsiyonel)
    if STRUCTURED_LOGGING_AVAILABLE:
        try:
            json_main_handler, json_error_handler = setup_structured_logging(log_dir, level)
            root_logger.addHandler(json_main_handler)
            root_logger.addHandler(json_error_handler)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Structured logging setup failed: {e}")

    # Log sampling setup (opsiyonel)
    if LOG_SAMPLING_AVAILABLE:
        try:
            setup_log_sampling(log_dir)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Log sampling setup failed: {e}")

    # Set specific log levels for external libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('peewee').setLevel(logging.WARNING)      # peewee SQL sorgularını bastır
    logging.getLogger('hpack').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    if app:
        app.logger.handlers = root_logger.handlers
        app.logger.setLevel(level)
        app.logger.propagate = False


def get_logger(name):
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
