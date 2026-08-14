"""Unit tests for log alert monitor."""

import os
from datetime import datetime
from unittest.mock import patch

import pytest

from utils.log_alert_monitor import LogAlertMonitor


@pytest.mark.unit
def test_log_alert_monitor_disabled_by_default():
    monitor = LogAlertMonitor()
    result = monitor.evaluate()
    assert result['enabled'] is False
    assert result['counts'] == {}


@pytest.mark.unit
def test_log_alert_monitor_evaluate_counts(tmp_path):
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    log_file = log_dir / 'e_cuzdan_errors.log'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file.write_text(
        f'{now} [0] [-] ERROR [test] first error\n'
        f'{now} [0] [-] CRITICAL [test] critical issue\n',
        encoding='utf-8',
    )

    monitor = LogAlertMonitor()
    monitor.enabled = True
    monitor.log_dir = str(log_dir)
    monitor.error_log_file = str(log_file)
    monitor.main_log_file = str(log_dir / 'missing.log')

    result = monitor.evaluate()
    assert result['counts']['ERROR'] == 1
    assert result['counts']['CRITICAL'] == 1
    assert result['breached']['critical'] is True


@pytest.mark.unit
def test_log_alert_monitor_check_sends_notification(tmp_path):
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    log_file = log_dir / 'e_cuzdan_errors.log'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [f'{now} [0] [-] ERROR [test] error {i}\n' for i in range(12)]
    log_file.write_text(''.join(lines), encoding='utf-8')

    monitor = LogAlertMonitor()
    monitor.enabled = True
    monitor.error_threshold = 10
    monitor.log_dir = str(log_dir)
    monitor.error_log_file = str(log_file)
    monitor.main_log_file = str(log_dir / 'missing.log')

    with patch.object(monitor, '_notify') as mock_notify:
        result = monitor.check()
        assert 'error' in result['alerts_triggered']
        mock_notify.assert_called_once()


@pytest.mark.unit
def test_is_otel_enabled_default_false(monkeypatch):
    monkeypatch.delenv('OTEL_ENABLED', raising=False)
    from utils.otel_setup import is_otel_enabled

    assert is_otel_enabled() is False


@pytest.mark.unit
def test_get_otlp_endpoint_dev_default(monkeypatch):
    monkeypatch.setenv('OTEL_ENABLED', 'true')
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
    from utils.otel_setup import get_otlp_endpoint

    assert get_otlp_endpoint() == 'localhost:4317'


@pytest.mark.unit
def test_get_otlp_endpoint_explicit(monkeypatch):
    monkeypatch.setenv('OTEL_ENABLED', 'true')
    monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'collector:4317')
    from utils.otel_setup import get_otlp_endpoint

    assert get_otlp_endpoint() == 'collector:4317'


@pytest.mark.unit
def test_is_collector_reachable_false(monkeypatch):
    from utils.otel_setup import is_collector_reachable

    assert is_collector_reachable('127.0.0.1:1') is False


@pytest.mark.unit
def test_setup_tracing_fallback_when_collector_down(monkeypatch):
    monkeypatch.setenv('OTEL_ENABLED', 'true')
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.delenv('OTEL_CONSOLE_EXPORTER', raising=False)
    monkeypatch.setattr('utils.otel_setup.is_collector_reachable', lambda _endpoint: False)

    from infrastructure.observability import tracing as tracing_module
    tracing_module._TRACER_PROVIDER = None

    from utils.otel_setup import setup_tracing

    assert setup_tracing('test_service') is True
