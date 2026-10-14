"""Resilient public FX and gold provider chain for local/staging use.

The chain deliberately returns indicative/reference observations only. It never
claims a licensed market-data feed and never writes to the application database.
Provider order is designed to keep the existing doviz.com behaviour while
adding official/public fallbacks before yfinance.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import requests
from bs4 import BeautifulSoup

from shared.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

FX_KEYS = ("usd", "eur", "gold")
GOLD_GRAMS_PER_TROY_OUNCE = Decimal("31.1034768")
DEFAULT_TIMEOUT_SECONDS = 8
DEFAULT_RETRIES = 1
DEFAULT_RETRY_DELAY_SECONDS = 0.25


class ProviderUnavailable(RuntimeError):
    """A provider could not return a usable response."""


class ProviderPayloadError(ProviderUnavailable):
    """A provider responded but did not contain usable quote fields."""


@dataclass(frozen=True)
class ProviderSnapshot:
    source: str
    values: dict[str, Decimal]
    observed_at: str | None
    quality_status: str


@dataclass(frozen=True)
class ResilientLiveQuotes:
    values: dict[str, str]
    provider_by_field: dict[str, str]
    provider_errors: tuple[str, ...]

    @property
    def fallback_used(self) -> bool:
        return any(source != "doviz_com" for source in self.provider_by_field.values())

    def safe_status(self) -> dict[str, Any]:
        """Return source metadata without quote values or exception text."""
        return {
            "provider_by_field": dict(self.provider_by_field),
            "fallback_used": self.fallback_used,
            "provider_error_count": len(self.provider_errors),
            "missing_fields": [key for key in FX_KEYS if self.values.get(key) == "--"],
            "quality_status": "indicative_reference_with_fallbacks",
        }


def _bounded_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(int(os.getenv(name, str(default))), maximum))
    except (TypeError, ValueError):
        return default


def _timeout_seconds() -> int:
    return _bounded_int_env("FX_PROVIDER_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS, 2, 30)


def _retry_count() -> int:
    return _bounded_int_env("FX_PROVIDER_RETRIES", DEFAULT_RETRIES, 0, 3)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip().replace("\u00a0", " ").replace(" ", "")
    if not text or text.casefold() in {"nan", "nat", "none", "null", "infinity", "-infinity"}:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    return parsed


def _format_decimal(value: Decimal | None, key: str | None = None) -> str:
    if value is None or not value.is_finite() or value <= 0:
        return "--"
    if key == "gold":
        return format(round(value, 2).normalize(), "f")
    return format(value.normalize(), "f")


def _response_status(response: Any) -> int:
    try:
        return int(getattr(response, "status_code", 200))
    except (TypeError, ValueError):
        return 200


def _response_text(response: Any) -> str:
    text = getattr(response, "text", "")
    return text if isinstance(text, str) else str(text or "")


_PROVIDER_CIRCUITS: dict[str, CircuitBreaker] = {}
_CIRCUITS_LOCK = threading.Lock()


def get_provider_circuit(name: str) -> CircuitBreaker:
    with _CIRCUITS_LOCK:
        if name not in _PROVIDER_CIRCUITS:
            _PROVIDER_CIRCUITS[name] = CircuitBreaker(
                name=f"fx_provider_{name}",
                failure_threshold=_bounded_int_env("FX_CB_THRESHOLD", 3, 1, 10),
                recovery_timeout=float(_bounded_int_env("FX_CB_TIMEOUT", 60, 5, 300)),
            )
        return _PROVIDER_CIRCUITS[name]


def _request(url: str, provider_name: str) -> Any:
    circuit = get_provider_circuit(provider_name)
    if not circuit.can_execute():
        raise ProviderUnavailable(f"{provider_name}:circuit_open")

    last_error: Exception | None = None
    for attempt in range(_retry_count() + 1):
        try:
            response = requests.get(
                url,
                timeout=_timeout_seconds(),
                headers={"User-Agent": "E-Cuzdan/15 market-data-resilience"},
            )
            status = _response_status(response)
            if status >= 400:
                raise ProviderUnavailable(f"{provider_name}:http_{status}")
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                raise_for_status()
            circuit.record_success()
            return response
        except Exception as exc:  # provider boundary must not break the app
            last_error = exc
            if attempt < _retry_count():
                delay = DEFAULT_RETRY_DELAY_SECONDS * (2 ** attempt)
                time.sleep(delay)
    circuit.record_failure(last_error)
    error_type = type(last_error).__name__ if last_error else "UnknownError"
    raise ProviderUnavailable(f"{provider_name}:{error_type}") from last_error


def _snapshot(source: str, values: dict[str, Decimal], *, quality: str, observed_at: str | None = None) -> ProviderSnapshot:
    usable = {key: value for key, value in values.items() if key in FX_KEYS and _parse_decimal(value) is not None}
    if not usable:
        raise ProviderPayloadError(f"{source}:no_usable_fields")
    return ProviderSnapshot(
        source=source,
        values=usable,
        observed_at=observed_at or _now_iso(),
        quality_status=quality,
    )


class DovizComProvider:
    name = "doviz_com"

    def fetch(self) -> ProviderSnapshot:
        response = _request("https://www.doviz.com", self.name)
        soup = BeautifulSoup(_response_text(response), "html.parser")
        values: dict[str, Decimal] = {}
        mapping = {"USD": "usd", "EUR": "eur", "XAU": "gold"}
        for socket_key, target in mapping.items():
            element = soup.find("span", {"data-socket-key": socket_key})
            parsed = _parse_decimal(element.get_text(" ", strip=True) if element else None)
            if parsed is not None:
                values[target] = parsed
        return _snapshot(self.name, values, quality="scraped_indicative")


class TcmbProvider:
    name = "tcmb_official"

    def fetch(self) -> ProviderSnapshot:
        response = _request("https://www.tcmb.gov.tr/kurlar/today.xml", self.name)
        payload = getattr(response, "content", None)
        if not isinstance(payload, (bytes, bytearray, str)) or not payload:
            payload = _response_text(response)
        try:
            root = ET.fromstring(payload)
        except (ET.ParseError, TypeError, ValueError) as exc:
            raise ProviderPayloadError(f"{self.name}:invalid_xml") from exc

        values: dict[str, Decimal] = {}
        observed_at = root.attrib.get("Tarih") or root.attrib.get("Date")
        for currency in root.iter():
            code = (
                currency.attrib.get("Kod")
                or currency.attrib.get("CurrencyCode")
                or currency.findtext("CurrencyCode")
            )
            if code not in {"USD", "EUR"}:
                continue
            buying = currency.findtext("ForexBuying") or currency.findtext("BanknoteBuying")
            parsed = _parse_decimal(buying)
            if parsed is not None:
                values["usd" if code == "USD" else "eur"] = parsed
        return _snapshot(self.name, values, quality="official_daily_reference", observed_at=observed_at)


class FrankfurterProvider:
    name = "frankfurter_ecb"

    def fetch(self) -> ProviderSnapshot:
        response = _request("https://api.frankfurter.dev/v2/rates?base=USD", self.name)
        try:
            payload = response.json()
        except (AttributeError, ValueError, TypeError) as exc:
            raise ProviderPayloadError(f"{self.name}:invalid_json") from exc

        usd_try: Decimal | None = None
        usd_eur: Decimal | None = None
        observed_at: str | None = None
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and isinstance(payload.get("rates"), list):
            rows = payload["rates"]
        elif isinstance(payload, dict) and isinstance(payload.get("rates"), dict):
            observed_at = str(payload.get("date") or "") or None
            rows = [
                {"quote": quote, "rate": rate, "date": observed_at}
                for quote, rate in payload["rates"].items()
            ]
        else:
            raise ProviderPayloadError(f"{self.name}:unexpected_schema")

        for row in rows:
            if not isinstance(row, dict):
                continue
            observed_at = observed_at or str(row.get("date") or "") or None
            quote = str(row.get("quote") or row.get("currency") or "").upper()
            parsed = _parse_decimal(row.get("rate"))
            if quote == "TRY":
                usd_try = parsed
            elif quote == "EUR":
                usd_eur = parsed

        values: dict[str, Decimal] = {}
        if usd_try is not None:
            values["usd"] = usd_try
        if usd_try is not None and usd_eur is not None:
            eur_try = usd_try / usd_eur
            if _parse_decimal(eur_try) is not None:
                values["eur"] = eur_try
        return _snapshot(self.name, values, quality="official_daily_reference", observed_at=observed_at)


class GoldApiProvider:
    name = "gold_api"

    def fetch(self, usd_try: Decimal | None) -> ProviderSnapshot:
        response = _request("https://api.gold-api.com/price/XAU", self.name)
        try:
            payload = response.json()
        except (AttributeError, ValueError, TypeError) as exc:
            raise ProviderPayloadError(f"{self.name}:invalid_json") from exc
        if not isinstance(payload, dict):
            raise ProviderPayloadError(f"{self.name}:unexpected_schema")
        price_usd_oz = _parse_decimal(payload.get("price") or payload.get("value"))
        if price_usd_oz is None or usd_try is None:
            raise ProviderPayloadError(f"{self.name}:missing_conversion_rate")
        gold_try_gram = price_usd_oz * usd_try / GOLD_GRAMS_PER_TROY_OUNCE
        observed_at = str(payload.get("updatedAt") or payload.get("timestamp") or "") or None
        return _snapshot(
            self.name,
            {"gold": gold_try_gram},
            quality="real_time_indicative_provider",
            observed_at=observed_at,
        )


def _yfinance_values(missing: set[str], usd_try: Decimal | None = None) -> dict[str, Decimal]:
    if not missing:
        return {}
    circuit = get_provider_circuit("yfinance")
    if not circuit.can_execute():
        raise ProviderUnavailable("yfinance:circuit_open")
    try:
        import yfinance as yf
    except ImportError as exc:
        circuit.record_failure(exc)
        raise ProviderUnavailable("yfinance:ImportError") from exc

    tickers: list[str] = []
    if "usd" in missing or ("gold" in missing and usd_try is None):
        tickers.append("USDTRY=X")
    if "eur" in missing:
        tickers.append("EURTRY=X")
    if "gold" in missing:
        tickers.append("GC=F")
    try:
        data = yf.download(tickers, period="1d", progress=False)
        circuit.record_success()
    except Exception as exc:
        circuit.record_failure(exc)
        raise ProviderUnavailable(f"yfinance:{type(exc).__name__}") from exc
    if data is None or data.empty:
        raise ProviderPayloadError("yfinance:empty_payload")

    def close_for(ticker: str) -> Any:
        close = data["Close"] if "Close" in data else None
        if close is None:
            return None
        if hasattr(close, "columns"):
            if ticker in close.columns:
                series = close[ticker]
            else:
                return None
        else:
            series = close
        valid = series.dropna()
        return valid.iloc[-1] if not valid.empty else None

    values: dict[str, Decimal] = {}
    usd = _parse_decimal(close_for("USDTRY=X")) if ("usd" in missing or usd_try is None) else usd_try
    eur = _parse_decimal(close_for("EURTRY=X")) if "eur" in missing else None
    gold_usd_oz = _parse_decimal(close_for("GC=F")) if "gold" in missing else None
    if "usd" in missing and usd is not None:
        values["usd"] = usd
    if eur is not None:
        values["eur"] = eur
    effective_usd = usd or usd_try
    if gold_usd_oz is not None and effective_usd is not None:
        values["gold"] = gold_usd_oz * effective_usd / GOLD_GRAMS_PER_TROY_OUNCE
    return values


def fetch_resilient_live_quotes(*, chain_enabled: bool = True) -> ResilientLiveQuotes:
    """Fetch missing USD/EUR/gold fields through an ordered provider chain."""
    values: dict[str, Decimal] = {}
    provider_by_field: dict[str, str] = {}
    provider_errors: list[str] = []

    providers = (DovizComProvider(), TcmbProvider(), FrankfurterProvider()) if chain_enabled else ()
    for provider in providers:
        if not {"usd", "eur"}.difference(values):
            break
        try:
            snapshot = provider.fetch()
        except ProviderUnavailable as exc:
            provider_errors.append(provider.name)
            logger.warning("Market provider başarısız: %s (%s)", provider.name, type(exc).__name__)
            continue
        for key, value in snapshot.values.items():
            if key not in values:
                values[key] = value
                provider_by_field[key] = snapshot.source

    if "gold" not in values:
        try:
            snapshot = GoldApiProvider().fetch(values.get("usd"))
        except ProviderUnavailable as exc:
            provider_errors.append(GoldApiProvider.name)
            logger.warning("Market provider başarısız: %s (%s)", GoldApiProvider.name, type(exc).__name__)
        else:
            values["gold"] = snapshot.values["gold"]
            provider_by_field["gold"] = snapshot.source

    missing = set(FX_KEYS).difference(values)
    if missing:
        try:
            values.update(_yfinance_values(missing, usd_try=values.get("usd")))
        except ProviderUnavailable as exc:
            provider_errors.append("yfinance")
            logger.warning("Market provider başarısız: yfinance (%s)", type(exc).__name__)
        for key in missing:
            if key in values:
                provider_by_field[key] = "yfinance"

    result = ResilientLiveQuotes(
        values={key: _format_decimal(values.get(key), key) for key in FX_KEYS},
        provider_by_field=provider_by_field,
        provider_errors=tuple(provider_errors),
    )
    if result.fallback_used:
        logger.debug("Döviz/altın çoklu provider fallback zinciri kullanıldı.")
    return result
