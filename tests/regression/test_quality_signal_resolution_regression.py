"""Regression tests for resolved quality-signal noise and fallback behavior."""

import logging

import pytest
import requests

from domain.portfolio.services import investment_performance
from infrastructure.background import background_service as background_module
from infrastructure.background.background_service import BackgroundService
from infrastructure.backup.encryption import BackupEncryptionService
from utils import profile_image


@pytest.mark.regression
def test_wrong_backup_password_does_not_emit_error_log(caplog):
    """Expected AES-GCM authentication failures remain below production error."""
    service = BackupEncryptionService()
    encrypted = service.encrypt_backup(b"quality-signal-test", "correct")

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ValueError, match="Şifre doğrulaması başarısız"):
            service.decrypt_backup(encrypted, "wrong")

    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.regression
def test_profile_image_provider_failure_is_warning(caplog, monkeypatch):
    """Missing OAuth assets use the documented None fallback without an error."""
    def fail_request(*args, **kwargs):
        raise requests.HTTPError("404 Client Error")

    monkeypatch.setattr(profile_image.requests, "get", fail_request)

    with caplog.at_level(logging.DEBUG):
        assert profile_image.download_profile_image("https://oauth.example/avatar.jpg") is None

    assert any(record.levelno == logging.WARNING for record in caplog.records)
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.regression
def test_market_provider_failure_is_warning_and_preserves_cache(caplog, monkeypatch):
    """A provider outage must retain the cache and not be reported as app error."""
    monkeypatch.setattr(
        background_module,
        "MARKET_ASSETS",
        {"GC=F": {"name": "Altın", "currency": "USD"}},
    )
    monkeypatch.setattr(
        background_module.yf,
        "download",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
    )
    service = BackgroundService()
    service._market_data = {
        "GC=F": {
            "data": {"index": ["2026-01-01"], "prices": [100.0]},
            "name": "Altın",
            "currency": "USD",
        }
    }

    with caplog.at_level(logging.DEBUG):
        service._update_market_data()

    assert service.get_market_data("GC=F") is not None
    assert any(record.levelno == logging.WARNING for record in caplog.records)
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.regression
def test_investment_performance_outside_context_is_debug(caplog):
    """The graceful empty result outside Flask context is diagnostic, not warning."""
    with caplog.at_level(logging.DEBUG):
        result = investment_performance.get_yearly_performance()

    assert result["yearly_data"] == {}
    assert any(record.levelno == logging.DEBUG for record in caplog.records)
    assert not [record for record in caplog.records if record.levelno >= logging.WARNING]


@pytest.mark.regression
def test_favicon_route_returns_success(client):
    """Browsers receive an explicit favicon response instead of a 404."""
    response = client.get("/favicon.ico", follow_redirects=True)

    assert response.status_code == 200


__all__ = [
    "test_wrong_backup_password_does_not_emit_error_log",
    "test_profile_image_provider_failure_is_warning",
    "test_market_provider_failure_is_warning_and_preserves_cache",
    "test_investment_performance_outside_context_is_debug",
    "test_favicon_route_returns_success",
]
