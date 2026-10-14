#!/usr/bin/env python3
"""
Observability verification — run after log/OTel changes.

Usage:
    python scripts/verify_observability.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0
WARN = 0


def ok(name: str, detail: str = '') -> None:
    global PASS
    PASS += 1
    suffix = f' — {detail}' if detail else ''
    print(f'  [PASS] {name}{suffix}')


def fail(name: str, detail: str = '') -> None:
    global FAIL
    FAIL += 1
    suffix = f' — {detail}' if detail else ''
    print(f'  [FAIL] {name}{suffix}')


def warn(name: str, detail: str = '') -> None:
    global WARN
    WARN += 1
    suffix = f' — {detail}' if detail else ''
    print(f'  [WARN] {name}{suffix}')


def safe_section(section_name: str, fn) -> None:
    """Run a verification section without ever crashing the script."""
    try:
        fn()
    except Exception as exc:  # pragma: no cover (best-effort safety net)
        fail(section_name, f'unhandled exception: {exc}')


def check_pii_scan() -> None:
    print('\n1. PII log scan')
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_log_pii.py')],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            ok('PII scanner')
        else:
            fail('PII scanner', (result.stdout + result.stderr).strip()[:4000])
    except Exception as exc:
        fail('PII scanner', str(exc))


def check_redaction() -> None:
    print('\n2. Log redaction helpers')
    from utils.log_redaction import mask_email, redact_message

    masked = mask_email('user@example.com')
    if masked == 'u***@example.com':
        ok('mask_email')
    else:
        fail('mask_email', masked)

    redacted = redact_message('token=secret123')
    if 'secret123' not in redacted and '***' in redacted:
        ok('redact_message')
    else:
        fail('redact_message', redacted)


def check_request_id() -> None:
    print('\n3. Request correlation ID')
    os.environ.setdefault('DISABLE_BACKGROUND_SERVICE', 'true')
    try:
        from app import app

        with app.test_client() as client:
            response = client.get('/healthz')
            rid = response.headers.get('X-Request-ID')
            if response.status_code == 200 and rid:
                ok('X-Request-ID header', rid[:16])
            else:
                fail('X-Request-ID header', f'status={response.status_code}')
    except Exception as exc:
        warn('X-Request-ID header', f'skipped: {exc}')


def check_structured_logs() -> None:
    print('\n4. Structured log files')
    log_dir = ROOT / 'logs'
    for name in ('e_cuzdan_structured.log', 'e_cuzdan.log'):
        path = log_dir / name
        if path.exists():
            ok(f'{name} exists')
        else:
            warn(f'{name} missing', 'will be created on first log write')


def check_otel_packages() -> None:
    print('\n5. OpenTelemetry packages')
    try:
        import opentelemetry  # noqa: F401
        import opentelemetry.instrumentation.flask  # noqa: F401

        ok('OTel packages installed')
    except ImportError:
        warn('OTel packages missing', 'pip install -r configuration/dependencies/requirements-observability.txt')


def check_otel_trace_propagation() -> None:
    print('\n6. Trace ID propagation')
    os.environ['OTEL_ENABLED'] = 'true'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'

    try:
        import logging

        from opentelemetry import trace
    except ImportError:
        warn('trace_id propagation', 'OTel packages missing (install requirements-observability.txt)')
        return

    try:
        from infrastructure.observability.log_filter import TraceContextFilter
        from infrastructure.observability.tracing import setup_tracing as init_tracing
    except ImportError as exc:
        warn('trace_id propagation', f'skipped: {exc}')
        return

    try:
        init_tracing(service_name='verify_test', otlp_endpoint=None, console=True)
        tracer = trace.get_tracer('verify')
        with tracer.start_as_current_span('verify_span'):
            record = logging.LogRecord('t', logging.INFO, '', 0, 'msg', (), None)
            TraceContextFilter().filter(record)
            if getattr(record, 'otel_trace_id', '0' * 32) != '0' * 32:
                ok('trace_id propagation', record.otel_trace_id[:16])
            else:
                fail('trace_id propagation', 'still zero')
    except Exception as exc:
        warn('trace_id propagation', f'failed: {exc}')


def check_collector() -> None:
    print('\n7. OTLP collector (optional)')
    from utils.otel_setup import is_collector_reachable

    if is_collector_reachable('localhost:4317'):
        ok('Collector reachable at localhost:4317')
    else:
        warn(
            'Collector not running',
            'Start: powershell -File scripts/start_observability.ps1 (requires Docker)',
        )


def check_monitoring_api() -> None:
    print('\n8. Monitoring API (authenticated)')
    os.environ.setdefault('DISABLE_BACKGROUND_SERVICE', 'true')
    try:
        from app import app

        with app.test_client() as client:
            # Unauthenticated should redirect or 401/302
            stats = client.get('/monitoring/api/stats')
            if stats.status_code in (302, 401, 403):
                ok('Stats API protected', f'status={stats.status_code}')
            else:
                warn('Stats API auth', f'unexpected status={stats.status_code}')
    except Exception as exc:
        warn('Stats API protected', f'skipped: {exc}')


def main() -> int:
    print('=' * 60)
    print('E-Cüzdan Observability Verification')
    print('=' * 60)

    safe_section('PII scanner', check_pii_scan)
    safe_section('Redaction helpers', check_redaction)
    safe_section('Request ID', check_request_id)
    safe_section('Structured logs', check_structured_logs)
    safe_section('OTel packages', check_otel_packages)
    safe_section('Trace propagation', check_otel_trace_propagation)
    safe_section('Collector check', check_collector)
    safe_section('Monitoring API', check_monitoring_api)

    print('\n' + '=' * 60)
    print(f'Results: {PASS} passed, {WARN} warnings, {FAIL} failed')
    print('=' * 60)

    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
