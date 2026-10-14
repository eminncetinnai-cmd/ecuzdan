"""Unit tests for the resilient public FX/metals provider chain."""

from types import SimpleNamespace

import pandas as pd
import pytest

from domain.analysis.services import fx_metals_provider as provider


class _Response:
    def __init__(self, *, text="", content=None, json_value=None, status_code=200):
        self.text = text
        self.content = content if content is not None else text.encode("utf-8")
        self._json_value = json_value
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        if isinstance(self._json_value, Exception):
            raise self._json_value
        return self._json_value


@pytest.mark.unit
def test_chain_uses_tcmb_and_gold_api_before_yfinance(monkeypatch):
    tcmb_xml = b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Tarih_Date Tarih=\"27.08.2026\">
  <Currency Kod=\"USD\"><ForexBuying>40.10</ForexBuying></Currency>
  <Currency Kod=\"EUR\"><ForexBuying>46.20</ForexBuying></Currency>
</Tarih_Date>"""

    def fake_get(url, **_kwargs):
        if "doviz.com" in url:
            return _Response(text="<html><body>no socket values</body></html>")
        if "tcmb.gov.tr" in url:
            return _Response(content=tcmb_xml, text=tcmb_xml.decode())
        if "gold-api.com" in url:
            return _Response(json_value={"price": 2000, "updatedAt": "2026-08-27T10:00:00Z"})
        raise AssertionError(f"Unexpected provider URL: {url}")

    monkeypatch.setattr(provider.requests, "get", fake_get)
    monkeypatch.setenv("FX_PROVIDER_RETRIES", "0")
    result = provider.fetch_resilient_live_quotes()

    assert result.values["usd"] == "40.1"
    assert result.values["eur"] == "46.2"
    assert result.values["gold"] != "--"
    assert result.provider_by_field["usd"] == "tcmb_official"
    assert result.provider_by_field["eur"] == "tcmb_official"
    assert result.provider_by_field["gold"] == "gold_api"
    assert result.provider_errors == ("doviz_com",)
    assert result.fallback_used is True


@pytest.mark.unit
def test_frankfurter_v2_schema_is_parsed_without_symbols_parameter(monkeypatch):
    calls = []

    def fake_get(url, **_kwargs):
        calls.append(url)
        if "doviz.com" in url or "tcmb.gov.tr" in url:
            raise RuntimeError("provider unavailable")
        if "frankfurter.dev" in url:
            return _Response(
                json_value=[
                    {"date": "2026-08-27", "base": "USD", "quote": "EUR", "rate": 0.85},
                    {"date": "2026-08-27", "base": "USD", "quote": "TRY", "rate": 40.8},
                ]
            )
        if "gold-api.com" in url:
            return _Response(json_value={"price": 2000})
        raise AssertionError(f"Unexpected provider URL: {url}")

    monkeypatch.setattr(provider.requests, "get", fake_get)
    monkeypatch.setenv("FX_PROVIDER_RETRIES", "0")
    result = provider.fetch_resilient_live_quotes()

    assert "symbols=" not in calls[2]
    assert result.values["usd"] == "40.8"
    assert result.values["eur"] == "48"
    assert result.provider_by_field["usd"] == "frankfurter_ecb"
    assert result.provider_by_field["eur"] == "frankfurter_ecb"


@pytest.mark.unit
def test_chain_uses_yfinance_only_for_remaining_fields(monkeypatch):
    def fake_get(url, **_kwargs):
        if "doviz.com" in url:
            return _Response(
                text=(
                    '<span data-socket-key="USD">40,00</span>'
                    '<span data-socket-key="EUR">45,00</span>'
                    '<span data-socket-key="XAU">--</span>'
                )
            )
        raise RuntimeError("not expected after FX values are complete")

    class _YFinance:
        @staticmethod
        def download(*_args, **_kwargs):
            return pd.DataFrame(
                {"Close": [100.0]},
                index=pd.to_datetime(["2026-08-27"]),
            )

    monkeypatch.setattr(provider.requests, "get", fake_get)
    monkeypatch.setitem(__import__("sys").modules, "yfinance", SimpleNamespace(download=_YFinance.download))
    monkeypatch.setenv("FX_PROVIDER_RETRIES", "0")
    result = provider.fetch_resilient_live_quotes()

    assert result.values["usd"] == "40"
    assert result.values["eur"] == "45"
    assert result.values["gold"] != "--"
    assert result.provider_by_field["usd"] == "doviz_com"
    assert result.provider_by_field["eur"] == "doviz_com"
    assert result.provider_by_field["gold"] == "yfinance"
