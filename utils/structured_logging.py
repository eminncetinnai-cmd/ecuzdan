"""
Structured Logging - JSON formatında loglama sistemi
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatında log formatter"""
    
    def __init__(self, timestamp_format: str = '%Y-%m-%dT%H:%M:%S.%fZ'):
        super().__init__()
        self.timestamp_format = timestamp_format
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Log kaydını JSON formatına dönüştür
        
        Args:
            record: Log kaydı
            
        Returns:
            JSON formatında string
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).strftime(self.timestamp_format),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
        }
        
        # OTel trace/span ID'leri ekle (varsa)
        if hasattr(record, 'otel_trace_id'):
            log_data['trace_id'] = record.otel_trace_id
        if hasattr(record, 'otel_span_id'):
            log_data['span_id'] = record.otel_span_id
        
        # Exception bilgisi ekle (varsa)
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Extra fields ekle
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message',
                          'asctime', 'otel_trace_id', 'otel_span_id']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class StructuredLogHandler(logging.Handler):
    """Structured log handler - JSON formatında log dosyalarına yazar"""
    
    def __init__(self, filename: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 10):
        super().__init__()
        from logging.handlers import RotatingFileHandler
        
        self.handler = RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        self.handler.setFormatter(JSONFormatter())
    
    def emit(self, record: logging.LogRecord):
        """Log kaydını JSON formatında yaz"""
        try:
            self.handler.emit(record)
        except Exception:
            self.handleError(record)
    
    def close(self):
        """Handler'ı kapat"""
        self.handler.close()


class LogContext:
    """Log context manager - ekstra context bilgileri eklemek için"""
    
    def __init__(self, **context):
        self.context = context
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Context'i log'a ekle"""
        self._old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context'i kaldır"""
        logging.setLogRecordFactory(self._old_factory)
        return False


class StructuredLogger:
    """Structured logger wrapper - kolay kullanım için"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, **context):
        """Context ile log yaz"""
        extra = {}
        for key, value in context.items():
            extra[key] = value
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **context):
        """DEBUG seviyesinde log"""
        self._log(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        """INFO seviyesinde log"""
        self._log(logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """WARNING seviyesinde log"""
        self._log(logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        """ERROR seviyesinde log"""
        self._log(logging.ERROR, message, **context)
    
    def critical(self, message: str, **context):
        """CRITICAL seviyesinde log"""
        self._log(logging.CRITICAL, message, **context)
    
    def exception(self, message: str, **context):
        """Exception ile log"""
        self._log(logging.ERROR, message, exc_info=True, **context)


def get_structured_logger(name: str) -> StructuredLogger:
    """Structured logger instance'ı al"""
    return StructuredLogger(name)


def setup_structured_logging(log_dir: str, level: int = logging.INFO):
    """
    Structured logging sistemini kur
    
    Args:
        log_dir: Log dizini
        level: Log seviyesi
    """
    import os
    
    os.makedirs(log_dir, exist_ok=True)
    
    # JSON log handler'ları
    json_main_handler = StructuredLogHandler(
        os.path.join(log_dir, 'e_cuzdan_structured.log'),
        max_bytes=10 * 1024 * 1024,
        backup_count=10
    )
    json_main_handler.setLevel(level)
    
    json_error_handler = StructuredLogHandler(
        os.path.join(log_dir, 'e_cuzdan_errors_structured.log'),
        max_bytes=5 * 1024 * 1024,
        backup_count=5
    )
    json_error_handler.setLevel(logging.ERROR)
    
    # Root logger'a ekle
    root_logger = logging.getLogger()
    root_logger.addHandler(json_main_handler)
    root_logger.addHandler(json_error_handler)
    
    return json_main_handler, json_error_handler
