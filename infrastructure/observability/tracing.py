"""OpenTelemetry tracer provider setup.

Usage:
    from infrastructure.observability.tracing import setup_tracing, get_tracer

    setup_tracing(service_name="e_cuzdan", otlp_endpoint=None)  # console exporter by default
    tracer = get_tracer("my.module")
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("key", "value")
        ...

If OTLP_ENDPOINT env var is set, traces are exported to the given gRPC endpoint
(e.g. Jaeger via OTLP). Otherwise a simple ConsoleSpanExporter is used in dev mode,
and a no-op tracer in test mode.
"""

import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

logger = logging.getLogger(__name__)

_TRACER_PROVIDER: TracerProvider | None = None


def setup_tracing(
    service_name: str = "e_cuzdan",
    otlp_endpoint: str | None = None,
    console: bool = False,
) -> TracerProvider:
    """Initialise the global TracerProvider.

    Call once at application startup (app.py).  Subsequent calls are no-ops.

    Args:
        service_name: OTel `service.name` resource attribute.
        otlp_endpoint: Optional gRPC OTLP endpoint, e.g. "localhost:4317".
                       Falls back to OTEL_EXPORTER_OTLP_ENDPOINT env var.
        console: Force ConsoleSpanExporter even if OTLP is configured (dev mode).

    Returns:
        The configured TracerProvider.
    """
    global _TRACER_PROVIDER
    if _TRACER_PROVIDER is not None:
        return _TRACER_PROVIDER

    resource = Resource.create({"service.name": service_name, "service.version": "15.0"})
    provider = TracerProvider(resource=resource)

    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if endpoint and not console:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry: OTLP exporter → %s", endpoint)
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-otlp-proto-grpc not installed. "
                "Falling back to console exporter. "
                "Run: pip install opentelemetry-exporter-otlp-proto-grpc"
            )
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif console or os.getenv("OTEL_CONSOLE_EXPORTER", "").lower() in ("1", "true"):
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry: ConsoleSpanExporter enabled.")
    else:
        # Silent / no-op in production with no endpoint configured
        logger.info("OpenTelemetry: no exporter configured — traces discarded (no-op).")

    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER = provider
    return provider


def get_tracer(name: str) -> trace.Tracer:
    """Return a named tracer from the global provider (or no-op if not set up)."""
    return trace.get_tracer(name)
