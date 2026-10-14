"""Regression coverage for production startup and health contracts."""

import pytest


@pytest.mark.regression
def test_healthz_redacts_database_error_outside_testing(app, client, monkeypatch):
    monkeypatch.setitem(app.config, 'TESTING', False)
    monkeypatch.setitem(app.config, 'FLASK_ENV', 'production')
    monkeypatch.setitem(app.config, 'DB_BOOTSTRAP_READY', False)
    monkeypatch.setitem(app.config, 'DB_BOOTSTRAP_ERROR', 'sensitive connection details')

    response = client.get('/healthz')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'degraded'
    assert payload['database_ready'] is False
    assert payload['database_error'] is None


@pytest.mark.regression
def test_healthz_exposes_database_error_only_in_testing(app, client, monkeypatch):
    monkeypatch.setitem(app.config, 'TESTING', True)
    monkeypatch.setitem(app.config, 'DB_BOOTSTRAP_READY', False)
    monkeypatch.setitem(app.config, 'DB_BOOTSTRAP_ERROR', 'test-only error')

    response = client.get('/healthz')

    assert response.status_code == 200
    assert response.get_json()['database_error'] == 'test-only error'
