"""Log filter that injects OpenTelemetry trace_id and span_id into every log record.

Usage (add once at logging setup):
    import logging
    from infrastructure.observability.log_filter import TraceContextFilter

    for handler in logging.root.handlers:
        handler.addFilter(TraceContextFilter())

After this, every log record emitted within an active span will carry:
    %(otel_trace_id)s  — 32-hex trace id
    %(otel_span_id)s   — 16-hex span id

Formatters should include these fields, e.g.:
    "%(asctime)s [%(otel_trace_id)s] %(levelname)s %(name)s: %(message)s"
"""

import logging

from opentelemetry import trace


class TraceContextFilter(logging.Filter):
    """Injects current OTel trace context into each log record."""

    _ZERO_TRACE = "0" * 32
    _ZERO_SPAN = "0" * 16

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        span = trace.get_current_span()
        ctx = span.get_span_context()

        if ctx and ctx.is_valid:
            record.otel_trace_id = format(ctx.trace_id, "032x")
            record.otel_span_id = format(ctx.span_id, "016x")
        else:
            record.otel_trace_id = self._ZERO_TRACE
            record.otel_span_id = self._ZERO_SPAN

        return True
