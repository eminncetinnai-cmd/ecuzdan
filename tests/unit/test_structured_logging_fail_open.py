"""Regression tests for fail-open structured logging behavior."""

import logging
from unittest.mock import patch

import pytest

from utils.structured_logging import StructuredLogger, StructuredLogHandler


@pytest.mark.unit
def test_structured_logger_exception_passes_exception_info():
    """exception() forwards real exception information to logging."""
    logger = StructuredLogger("test_logger")
    with patch.object(logger.logger, "log") as mock_log:
        logger.exception("Exception message", user_id="123")

    mock_log.assert_called_once()
    kwargs = mock_log.call_args.kwargs
    assert kwargs["exc_info"] is True
    assert kwargs["extra"]["user_id"] == "123"


@pytest.mark.unit
def test_structured_log_handler_emit_is_fail_open(tmp_path):
    """A sink write failure must not escape as an application exception."""
    handler = StructuredLogHandler(str(tmp_path / "structured.log"))
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="sink failure should be contained",
        args=(),
        exc_info=None,
    )

    with patch.object(handler.handler, "emit", side_effect=OSError("disk full")):
        handler.emit(record)

    handler.close()
