"""Safe OpenTelemetry setup — opt-in via OTEL_ENABLED env var."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_DEV_OTLP_ENDPOINT = 'localhost:4317'
COLLECTOR_CHECK_TIMEOUT_SEC = 1.0


def is_otel_enabled() -> bool:
    return os.getenv('OTEL_ENABLED', 'false').lower() in ('1', 'true', 'yes')


def get_otlp_endpoint() -> str | None:
    """Return configured OTLP endpoint, with a dev-friendly default when enabled."""
    endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    if endpoint:
        return endpoint.strip()

    if not is_otel_enabled():
        return None

    flask_env = os.getenv('FLASK_ENV', 'production').lower()
    if flask_env in ('development', 'dev', 'testing'):
        return DEFAULT_DEV_OTLP_ENDPOINT

    return None


def is_collector_reachable(endpoint: str, timeout: float = COLLECTOR_CHECK_TIMEOUT_SEC) -> bool:
    """Quick TCP check — avoids OTLP export retry spam when collector is down."""
    if not endpoint:
        return False
    try:
        import socket

        host, _, port_str = endpoint.partition(':')
        port = int(port_str or '4317')
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def setup_tracing(service_name: str = 'e_cuzdan') -> bool:
    """Initialize tracer provider when OTEL is enabled. Returns True on success."""
    if not is_otel_enabled():
        logger.debug('OpenTelemetry disabled (set OTEL_ENABLED=true to enable).')
        return False

    endpoint = get_otlp_endpoint()
    use_console = os.getenv('OTEL_CONSOLE_EXPORTER', '').lower() in ('1', 'true', 'yes')

    if endpoint and not use_console and not is_collector_reachable(endpoint):
        logger.warning(
            'OTLP collector unreachable at %s — using console exporter. '
            'Start stack: powershell -File scripts/start_observability.ps1',
            endpoint,
        )
        use_console = True
        endpoint = None
    elif endpoint:
        os.environ.setdefault('OTEL_EXPORTER_OTLP_ENDPOINT', endpoint)

    try:
        from infrastructure.observability.tracing import setup_tracing as init_tracing

        init_tracing(service_name=service_name, otlp_endpoint=endpoint, console=use_console)
        logger.info(
            'OpenTelemetry tracer initialized for service=%s mode=%s',
            service_name,
            'console' if use_console else f'otlp:{endpoint}',
        )
        return True
    except Exception as exc:
        logger.info('OpenTelemetry tracer setup skipped: %s', exc)
        return False


def instrument_flask_app(app) -> bool:
    """Instrument Flask app when OTEL packages are available."""
    if not is_otel_enabled():
        return False

    try:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument_app(app)
        logger.info('OpenTelemetry Flask instrumentation applied.')
        return True
    except ImportError:
        logger.info(
            'opentelemetry-instrumentation-flask not installed. '
            'Install configuration/dependencies/requirements-observability.txt to enable tracing.'
        )
        return False
    except Exception as exc:
        logger.warning('OpenTelemetry Flask instrumentation failed: %s', exc)
        return False

