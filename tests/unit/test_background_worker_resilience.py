"""Unit tests for BackgroundService bounded timeouts and resilient fallbacks."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import requests

from infrastructure.background.background_service import BackgroundService


def test_weather_timeout_fallback():
    """Weather service failure or timeout must fallback to existing cached temperature."""
    service = BackgroundService()
    service._live_data = {"weather": "18°C", "usd": "34.50", "eur": "38.20", "gold": "2900.00", "last_updated": ""}

    with patch("requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        with patch("infrastructure.background.background_service.fetch_resilient_live_quotes") as mock_quotes:
            mock_status = MagicMock()
            mock_status.values = {"usd": "34.50", "eur": "38.20", "gold": "2900.00"}
            mock_status.safe_status.return_value = {"quality_status": "ok"}
            mock_quotes.return_value = mock_status

            service._update_live_data()

    # Cached weather is preserved, not overwritten with error
    assert service.get_live_data()["weather"] == "18°C"


def test_market_data_concurrent_resilience():
    """If one ticker times out or fails, other tickers still succeed and the failed ticker retains cache."""
    service = BackgroundService()
    service._market_data = {
        "GC=F": {
            "data": {"index": ["2026-01-01"], "prices": [2500.0]},
            "name": "Altın",
            "currency": "USD",
        }
    }

    # Create dummy DataFrame for successful ticker
    dummy_df = pd.DataFrame(
        {"Close": [100.0, 105.0]},
        index=pd.to_datetime(["2026-01-01", "2026-02-01"]),
    )

    def mock_download(ticker, *args, **kwargs):
        if ticker == "GC=F":
            raise requests.exceptions.Timeout("Ticker timeout")
        return dummy_df

    with patch("yfinance.download", side_effect=mock_download):
        service._update_market_data()

    all_data = service._market_data
    # GC=F had an error so it should preserve its previous cache
    assert "GC=F" in all_data
    assert all_data["GC=F"]["data"]["prices"] == [2500.0]
    # Other tickers like BTC-USD should have been updated with dummy_df
    assert "BTC-USD" in all_data
    assert all_data["BTC-USD"]["data"]["prices"] == [100.0, 105.0]
