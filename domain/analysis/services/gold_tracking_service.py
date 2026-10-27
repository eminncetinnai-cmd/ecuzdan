"""Resilient Harem Altın & Bursa Jeweler Bazaar live gold derivatives service.

Provides real-time buy/sell/spread observations for Turkish gold derivatives
(Gram 24K, 22K Bracelet, 14K Bracelet, Quarter/Half/Full/Ata/Gremse New & Old,
Silver, Ounce, USD/KG, EUR/KG) using a 3-tier fallback chain:
  1. Harem Altın live feed via altin.doviz.com/harem
  2. Truncgil v4 JSON API fallback
  3. Calibrated Harem Altın multiplier engine backed by fx_metals_provider

Pure domain service: never imports Flask or SQLAlchemy models.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import requests
from bs4 import BeautifulSoup

from domain.analysis.services.fx_metals_provider import (
    _parse_decimal,
    fetch_resilient_live_quotes,
    get_provider_circuit,
)

logger = logging.getLogger(__name__)

HAREM_DOVIZ_URL = "https://altin.doviz.com/harem"
TRUNCGIL_V4_URL = "https://finans.truncgil.com/v4/today.json"
CACHE_TTL_SECONDS = 300.0
REQUEST_TIMEOUT_SECONDS = 6

_BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
_INSTANCE_DIR = os.path.join(_BASE_DIR, "instance")
GOLD_TRACKING_CACHE_FILE = os.path.join(_INSTANCE_DIR, "gold_tracking_cache.json")
LIVE_DATA_CACHE_FILE = os.path.join(_INSTANCE_DIR, "live_data_cache.json")


@dataclass(frozen=True)
class DerivativeSpec:
    """Static metadata and Harem Altın calibrated fallback multipliers for each item."""

    code: str
    harem_label: str
    name: str
    short_name: str
    category: str
    category_label: str
    unit: str
    purity_label: str
    has_gram_equivalent: Decimal
    fallback_buy_ratio: Decimal
    fallback_sell_ratio: Decimal
    is_calculable_tl: bool = True


# Calibrated directly against live Harem Altın quotes:
# Gram Altın (24K) is 1.0000x reference.
DERIVATIVE_SPECS: tuple[DerivativeSpec, ...] = (
    DerivativeSpec(
        code="gram_altin",
        harem_label="Gram Altın",
        name="Gram Altın (24 Ayar Has)",
        short_name="Gram (24K)",
        category="gram_bilezik",
        category_label="Gram & Bilezik",
        unit="TRY",
        purity_label="24 Ayar (995 Milyem)",
        has_gram_equivalent=Decimal("1.0000"),
        fallback_buy_ratio=Decimal("1.0000"),
        fallback_sell_ratio=Decimal("1.0000"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="bilezik_22",
        harem_label="22 Ayar Bilezik",
        name="22 Ayar Bilezik (Gram)",
        short_name="22 Ayar Bilezik",
        category="gram_bilezik",
        category_label="Gram & Bilezik",
        unit="TRY",
        purity_label="22 Ayar (916 Milyem)",
        has_gram_equivalent=Decimal("0.9160"),
        fallback_buy_ratio=Decimal("0.9143"),
        fallback_sell_ratio=Decimal("0.9341"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="bilezik_14",
        harem_label="14 Ayar Bilezik",
        name="14 Ayar Altın (Gram)",
        short_name="14 Ayar Altın",
        category="gram_bilezik",
        category_label="Gram & Bilezik",
        unit="TRY",
        purity_label="14 Ayar (585 Milyem)",
        has_gram_equivalent=Decimal("0.5850"),
        fallback_buy_ratio=Decimal("0.5487"),
        fallback_sell_ratio=Decimal("0.7253"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="ceyrek_yeni",
        harem_label="Çeyrek Altın",
        name="Çeyrek Altın (Yeni Tarihli)",
        short_name="Çeyrek (Yeni)",
        category="sarrafiye_yeni",
        category_label="Yeni Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 1,75 gr",
        has_gram_equivalent=Decimal("1.6065"),
        fallback_buy_ratio=Decimal("1.6383"),
        fallback_sell_ratio=Decimal("1.6298"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="yarim_yeni",
        harem_label="Yarım Altın",
        name="Yarım Altın (Yeni Tarihli)",
        short_name="Yarım (Yeni)",
        category="sarrafiye_yeni",
        category_label="Yeni Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 3,50 gr",
        has_gram_equivalent=Decimal("3.2130"),
        fallback_buy_ratio=Decimal("3.2764"),
        fallback_sell_ratio=Decimal("3.2587"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="tam_yeni",
        harem_label="Tam Altın",
        name="Tam / Ziynet Altın (Yeni)",
        short_name="Tam Altın (Yeni)",
        category="sarrafiye_yeni",
        category_label="Yeni Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 7,01 gr",
        has_gram_equivalent=Decimal("6.4260"),
        fallback_buy_ratio=Decimal("6.5326"),
        fallback_sell_ratio=Decimal("6.4967"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="ata_yeni",
        harem_label="Ata Altın",
        name="Ata / Cumhuriyet Altını (Yeni)",
        short_name="Ata Lira (Yeni)",
        category="sarrafiye_yeni",
        category_label="Yeni Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 7,216 gr",
        has_gram_equivalent=Decimal("6.6170"),
        fallback_buy_ratio=Decimal("6.6231"),
        fallback_sell_ratio=Decimal("6.6132"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="gremse_yeni",
        harem_label="Gremse Altın",
        name="Gremse Altın (2,5'luk Yeni)",
        short_name="Gremse (Yeni)",
        category="sarrafiye_yeni",
        category_label="Yeni Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 17,54 gr",
        has_gram_equivalent=Decimal("16.0650"),
        fallback_buy_ratio=Decimal("16.2111"),
        fallback_sell_ratio=Decimal("16.1693"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="ceyrek_eski",
        harem_label="Eski Çeyrek Altın",
        name="Eski Çeyrek Altın",
        short_name="Çeyrek (Eski)",
        category="sarrafiye_eski",
        category_label="Eski Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 1,75 gr",
        has_gram_equivalent=Decimal("1.6065"),
        fallback_buy_ratio=Decimal("1.6081"),
        fallback_sell_ratio=Decimal("1.6010"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="yarim_eski",
        harem_label="Eski Yarım Altın",
        name="Eski Yarım Altın",
        short_name="Yarım (Eski)",
        category="sarrafiye_eski",
        category_label="Eski Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 3,50 gr",
        has_gram_equivalent=Decimal("3.2130"),
        fallback_buy_ratio=Decimal("3.2160"),
        fallback_sell_ratio=Decimal("3.1970"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="tam_eski",
        harem_label="Eski Tam Altın",
        name="Eski Tam / Ziynet Altın",
        short_name="Tam Altın (Eski)",
        category="sarrafiye_eski",
        category_label="Eski Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 7,01 gr",
        has_gram_equivalent=Decimal("6.4260"),
        fallback_buy_ratio=Decimal("6.4422"),
        fallback_sell_ratio=Decimal("6.4039"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="ata_eski",
        harem_label="Eski Ata Altın",
        name="Eski Ata / Cumhuriyet Altını",
        short_name="Ata Lira (Eski)",
        category="sarrafiye_eski",
        category_label="Eski Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 7,216 gr",
        has_gram_equivalent=Decimal("6.6170"),
        fallback_buy_ratio=Decimal("6.6281"),
        fallback_sell_ratio=Decimal("6.5982"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="gremse_eski",
        harem_label="Eski Gremse Altın",
        name="Eski Gremse Altın (2,5'luk)",
        short_name="Gremse (Eski)",
        category="sarrafiye_eski",
        category_label="Eski Tarihli Ziynet",
        unit="TRY",
        purity_label="22 Ayar · 17,54 gr",
        has_gram_equivalent=Decimal("16.0650"),
        fallback_buy_ratio=Decimal("16.0301"),
        fallback_sell_ratio=Decimal("16.0197"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="gumus_gram",
        harem_label="Gram Gümüş",
        name="Gram Gümüş (999 Saf)",
        short_name="Gram Gümüş",
        category="global_emtia",
        category_label="Küresel & Külçe",
        unit="TRY",
        purity_label="999 Milyem (1 gr)",
        has_gram_equivalent=Decimal("0.0130"),
        fallback_buy_ratio=Decimal("0.0127"),
        fallback_sell_ratio=Decimal("0.0137"),
        is_calculable_tl=True,
    ),
    DerivativeSpec(
        code="ons_altin",
        harem_label="Ons Altın",
        name="Ons Altın (XAU/USD)",
        short_name="Ons Altın ($)",
        category="global_emtia",
        category_label="Küresel & Külçe",
        unit="USD",
        purity_label="31,1035 gr Has",
        has_gram_equivalent=Decimal("31.1035"),
        fallback_buy_ratio=Decimal("0.6265"),
        fallback_sell_ratio=Decimal("0.6185"),
        is_calculable_tl=False,
    ),
    DerivativeSpec(
        code="usd_kg",
        harem_label="USD/KG",
        name="Külçe Altın (USD / KG)",
        short_name="USD / KG",
        category="global_emtia",
        category_label="Küresel & Külçe",
        unit="USD",
        purity_label="1.000 gr · 995 Has",
        has_gram_equivalent=Decimal("995.0000"),
        fallback_buy_ratio=Decimal("20.0920"),
        fallback_sell_ratio=Decimal("19.8950"),
        is_calculable_tl=False,
    ),
    DerivativeSpec(
        code="eur_kg",
        harem_label="EUR/KG",
        name="Külçe Altın (EUR / KG)",
        short_name="EUR / KG",
        category="global_emtia",
        category_label="Küresel & Külçe",
        unit="EUR",
        purity_label="1.000 gr · 995 Has",
        has_gram_equivalent=Decimal("995.0000"),
        fallback_buy_ratio=Decimal("17.9350"),
        fallback_sell_ratio=Decimal("17.7890"),
        is_calculable_tl=False,
    ),
)

SPEC_BY_LABEL: dict[str, DerivativeSpec] = {spec.harem_label.casefold(): spec for spec in DERIVATIVE_SPECS}
SPEC_BY_CODE: dict[str, DerivativeSpec] = {spec.code: spec for spec in DERIVATIVE_SPECS}

# Bursa Jeweler Margin Presets (buy adjustment %, sell adjustment %)
MARGIN_PRESETS: dict[str, dict[str, Any]] = {
    "bursa_harem": {
        "key": "bursa_harem",
        "label": "Harem Altın Birebir (Bursa Referans)",
        "short_label": "Harem Altın (0%)",
        "description": "Bursa kuyumcularının baz aldığı canlı Harem Altın ekran fiyatları (Ek marj: %0,0)",
        "buy_adj_pct": Decimal("0.00"),
        "sell_adj_pct": Decimal("0.00"),
    },
    "bursa_carsi": {
        "key": "bursa_carsi",
        "label": "Bursa Kapalıçarşı Tezgâh Ortalaması",
        "short_label": "Bursa Çarşı (±%0,4)",
        "description": "Bursa Kapalıçarşı fiziki sarrafiye tezgâh ortalaması (Alış: %-0,35 / Satış: %+0,45)",
        "buy_adj_pct": Decimal("-0.35"),
        "sell_adj_pct": Decimal("0.45"),
    },
    "bursa_vitrin": {
        "key": "bursa_vitrin",
        "label": "Cadde / Perakende Kuyumcu Vitrin",
        "short_label": "Perakende Vitrin (±%0,9)",
        "description": "İlçe/cadde kuyumcuları ortalama perakende vitrin marjı (Alış: %-0,75 / Satış: %+1,10)",
        "buy_adj_pct": Decimal("-0.75"),
        "sell_adj_pct": Decimal("1.10"),
    },
}


@dataclass(frozen=True)
class GoldDerivativeQuote:
    """Single gold derivative buy/sell/spread observation."""

    code: str
    name: str
    short_name: str
    category: str
    category_label: str
    unit: str
    purity_label: str
    has_gram_equivalent: Decimal
    base_buy_price: Decimal
    base_sell_price: Decimal
    buy_price: Decimal
    sell_price: Decimal
    spread_amount: Decimal
    spread_pct: Decimal
    change_pct: Decimal
    updated_time: str
    is_calculable_tl: bool


@dataclass(frozen=True)
class GoldTrackingSnapshot:
    """Complete snapshot returned by GoldTrackingService."""

    quotes: tuple[GoldDerivativeQuote, ...]
    source: str
    source_label: str
    fallback_used: bool
    observed_at_display: str
    preset_key: str
    preset_info: dict[str, Any]
    is_cache_fresh: bool = True
    cache_age_seconds: float = 0.0


_CACHE_LOCK = threading.Lock()
_CACHED_RAW_QUOTES: dict[str, Any] | None = None
_CACHED_AT_MONOTONIC: float = 0.0


def _quantize_2dp(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_change_pct(raw: str | None) -> Decimal:
    if not raw:
        return Decimal("0.00")
    cleaned = raw.replace("%", "").replace("+", "").strip()
    sign = Decimal("-1") if cleaned.startswith("-") else Decimal("1")
    cleaned = cleaned.lstrip("-").strip()
    parsed = _parse_decimal(cleaned)
    if parsed is None:
        return Decimal("0.00")
    return _quantize_2dp(parsed * sign)


def fetch_harem_doviz_table(session: Any = None) -> dict[str, dict[str, Any]]:
    """Scrape live Harem Altın table from altin.doviz.com/harem."""
    http = session or requests
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    response = http.get(HAREM_DOVIZ_URL, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    if getattr(response, "status_code", 200) >= 400:
        raise RuntimeError(f"Harem table HTTP {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    results: dict[str, dict[str, Any]] = {}

    for tr in soup.select("table tr"):
        cols = [td.get_text(" ", strip=True) for td in tr.find_all(["th", "td"])]
        if len(cols) < 4:
            continue
        label = cols[0].strip()
        if not label or label.casefold() in {"", "alış", "satış"}:
            continue
        spec = SPEC_BY_LABEL.get(label.casefold())
        if spec is None:
            continue
        buy_val = _parse_decimal(cols[1])
        sell_val = _parse_decimal(cols[2])
        if buy_val is None or sell_val is None:
            continue
        change_val = _parse_change_pct(cols[3] if len(cols) > 3 else "0")
        time_str = cols[4].strip() if len(cols) > 4 and cols[4].strip() else datetime.now().strftime("%H:%M")
        results[spec.code] = {
            "buy": _quantize_2dp(buy_val),
            "sell": _quantize_2dp(sell_val),
            "change_pct": change_val,
            "time": time_str,
        }

    if "gram_altin" not in results or "ceyrek_yeni" not in results:
        raise RuntimeError("Harem table missing core gold rows")

    return results


def fetch_truncgil_fallback(session: Any = None) -> dict[str, dict[str, Any]]:
    """Fetch fallback gold derivative prices from Truncgil v4 JSON API."""
    http = session or requests
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    response = http.get(TRUNCGIL_V4_URL, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    if getattr(response, "status_code", 200) >= 400:
        raise RuntimeError(f"Truncgil HTTP {response.status_code}")

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid Truncgil JSON payload")

    mapping = {
        "GRA": "gram_altin",
        "CEYREKALTIN": "ceyrek_yeni",
        "YARIMALTIN": "yarim_yeni",
        "TAMALTIN": "tam_yeni",
        "ATAALTIN": "ata_yeni",
        "GREMSEALTIN": "gremse_yeni",
        "YIA": "bilezik_22",
        "ODA": "bilezik_14",
        "GUMUS": "gumus_gram",
        "ONS": "ons_altin",
    }
    now_hm = datetime.now().strftime("%H:%M")
    results: dict[str, dict[str, Any]] = {}
    for t_key, code in mapping.items():
        node = payload.get(t_key)
        if not isinstance(node, dict):
            continue
        buy_val = _parse_decimal(node.get("Buying"))
        sell_val = _parse_decimal(node.get("Selling"))
        change_val = _parse_decimal(node.get("Change")) or Decimal("0.00")
        if buy_val and sell_val:
            results[code] = {
                "buy": _quantize_2dp(buy_val),
                "sell": _quantize_2dp(sell_val),
                "change_pct": _quantize_2dp(change_val),
                "time": now_hm,
            }

    if "gram_altin" not in results:
        raise RuntimeError("Truncgil payload missing GRA")
    return results


def _build_full_raw_map(
    partial: dict[str, dict[str, Any]],
    fallback_gram_buy: Decimal,
    fallback_gram_sell: Decimal,
) -> dict[str, dict[str, Any]]:
    """Ensure every DerivativeSpec has a valid entry, filling missing ones via calibrated Harem ratios."""
    gram_entry = partial.get("gram_altin")
    base_buy = gram_entry["buy"] if gram_entry else fallback_gram_buy
    base_sell = gram_entry["sell"] if gram_entry else fallback_gram_sell
    now_hm = datetime.now().strftime("%H:%M")

    complete: dict[str, dict[str, Any]] = {}
    for spec in DERIVATIVE_SPECS:
        existing = partial.get(spec.code)
        if existing is not None:
            complete[spec.code] = existing
        else:
            calc_buy = _quantize_2dp(base_buy * spec.fallback_buy_ratio)
            calc_sell = _quantize_2dp(base_sell * spec.fallback_sell_ratio)
            if calc_sell <= calc_buy:
                calc_sell = _quantize_2dp(calc_buy * Decimal("1.008"))
            complete[spec.code] = {
                "buy": calc_buy,
                "sell": calc_sell,
                "change_pct": gram_entry["change_pct"] if gram_entry else Decimal("0.00"),
                "time": gram_entry["time"] if gram_entry else now_hm,
            }
    return complete


def _save_disk_cache(bundle: dict[str, Any], cache_path: str | None = None) -> None:
    """Persist gold tracking raw quotes bundle to disk for instant cold-start loading."""
    target_path = cache_path or GOLD_TRACKING_CACHE_FILE
    if cache_path is None and "PYTEST_CURRENT_TEST" in os.environ:
        return
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        serialized_quotes: dict[str, dict[str, str]] = {}
        for code, item in bundle.get("quotes", {}).items():
            serialized_quotes[code] = {
                "buy": str(item["buy"]),
                "sell": str(item["sell"]),
                "change_pct": str(item.get("change_pct", Decimal("0.00"))),
                "time": str(item.get("time", "")),
            }
        payload = {
            "quotes": serialized_quotes,
            "source": bundle.get("source", "harem_altin_live"),
            "source_label": bundle.get("source_label", "Harem Altın Canlı (Bursa Referans)"),
            "fallback_used": bool(bundle.get("fallback_used", False)),
            "observed_at_display": bundle.get("observed_at_display", ""),
            "cached_at_epoch": time.time(),
        }
        with open(target_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.debug("Gold tracking disk cache write skipped: %s", exc)


def _load_disk_cache(cache_path: str | None = None) -> tuple[dict[str, Any] | None, float]:
    """Load persisted gold tracking raw quotes from disk, returning (bundle, age_seconds)."""
    target_path = cache_path or GOLD_TRACKING_CACHE_FILE
    if not os.path.exists(target_path):
        return None, float("inf")
    try:
        with open(target_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict) or not isinstance(payload.get("quotes"), dict):
            return None, float("inf")

        partial: dict[str, dict[str, Any]] = {}
        for code, item in payload["quotes"].items():
            if not isinstance(item, dict):
                continue
            buy_val = _parse_decimal(item.get("buy"))
            sell_val = _parse_decimal(item.get("sell"))
            if buy_val is None or sell_val is None:
                continue
            partial[code] = {
                "buy": _quantize_2dp(buy_val),
                "sell": _quantize_2dp(sell_val),
                "change_pct": _quantize_2dp(_parse_decimal(item.get("change_pct")) or Decimal("0.00")),
                "time": str(item.get("time") or "09:00"),
            }

        if "gram_altin" not in partial:
            return None, float("inf")

        gram_buy = partial["gram_altin"]["buy"]
        gram_sell = partial["gram_altin"]["sell"]
        complete = _build_full_raw_map(partial, gram_buy, gram_sell)
        cached_at_epoch = float(payload.get("cached_at_epoch") or os.path.getmtime(target_path))
        age_seconds = max(0.0, time.time() - cached_at_epoch)

        bundle = {
            "quotes": complete,
            "source": str(payload.get("source") or "harem_altin_cache"),
            "source_label": str(payload.get("source_label") or "Harem Altın Canlı (Bursa Referans)"),
            "fallback_used": bool(payload.get("fallback_used", False)),
            "observed_at_display": str(
                payload.get("observed_at_display") or datetime.now().strftime("%d.%m.%Y %H:%M")
            ),
        }
        return bundle, age_seconds
    except Exception as exc:
        logger.debug("Gold tracking disk cache read skipped: %s", exc)
        return None, float("inf")


def _build_instant_offline_bundle() -> dict[str, Any]:
    """Build an instant (<1ms) calibrated gold snapshot from local live_data_cache.json without network."""
    raw_gold = Decimal("6894.70")
    if os.path.exists(LIVE_DATA_CACHE_FILE):
        try:
            with open(LIVE_DATA_CACHE_FILE, "r", encoding="utf-8") as fh:
                live_payload = json.load(fh)
            if isinstance(live_payload, dict):
                parsed = _parse_decimal(live_payload.get("gold"))
                if parsed and parsed > Decimal("100"):
                    raw_gold = parsed
        except Exception:
            pass

    gram_buy = _quantize_2dp(raw_gold * Decimal("0.9945"))
    gram_sell = _quantize_2dp(raw_gold * Decimal("1.0075"))
    now_hm = datetime.now().strftime("%H:%M")
    partial_fallback = {
        "gram_altin": {
            "buy": gram_buy,
            "sell": gram_sell,
            "change_pct": Decimal("0.00"),
            "time": now_hm,
        }
    }
    complete = _build_full_raw_map(partial_fallback, gram_buy, gram_sell)
    return {
        "quotes": complete,
        "source": "calibrated_harem_formula",
        "source_label": "Harem Altın Katsayı Motoru (Önbellek)",
        "fallback_used": True,
        "observed_at_display": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }


class GoldTrackingService:
    """Domain service for Harem Altın & Bursa Jeweler gold derivative prices."""

    def get_snapshot(
        self,
        preset_key: str = "bursa_harem",
        force_refresh: bool = False,
        session: Any = None,
        allow_network: bool = True,
    ) -> GoldTrackingSnapshot:
        preset = MARGIN_PRESETS.get(preset_key, MARGIN_PRESETS["bursa_harem"])
        actual_preset_key = preset["key"]

        raw_bundle = self._get_or_fetch_raw_quotes(
            force_refresh=force_refresh,
            session=session,
            allow_network=allow_network,
        )
        raw_quotes: dict[str, dict[str, Any]] = raw_bundle["quotes"]
        source: str = raw_bundle["source"]
        source_label: str = raw_bundle["source_label"]
        fallback_used: bool = raw_bundle["fallback_used"]
        observed_at_display: str = raw_bundle["observed_at_display"]
        with _CACHE_LOCK:
            cache_age = max(0.0, time.monotonic() - _CACHED_AT_MONOTONIC) if _CACHED_AT_MONOTONIC > 0 else CACHE_TTL_SECONDS
        is_cache_fresh = (cache_age < CACHE_TTL_SECONDS) and not fallback_used

        buy_mult = Decimal("1") + (Decimal(str(preset["buy_adj_pct"])) / Decimal("100"))
        sell_mult = Decimal("1") + (Decimal(str(preset["sell_adj_pct"])) / Decimal("100"))

        quotes_list: list[GoldDerivativeQuote] = []
        for spec in DERIVATIVE_SPECS:
            item = raw_quotes[spec.code]
            base_buy: Decimal = item["buy"]
            base_sell: Decimal = item["sell"]

            # Apply Bursa jeweler margin only to physical TL items
            if spec.is_calculable_tl:
                adj_buy = _quantize_2dp(base_buy * buy_mult)
                adj_sell = _quantize_2dp(base_sell * sell_mult)
            else:
                adj_buy = base_buy
                adj_sell = base_sell

            spread_amt = _quantize_2dp(max(Decimal("0.00"), adj_sell - adj_buy))
            spread_pct = (
                _quantize_2dp((spread_amt / adj_buy) * Decimal("100"))
                if adj_buy > 0
                else Decimal("0.00")
            )

            quotes_list.append(
                GoldDerivativeQuote(
                    code=spec.code,
                    name=spec.name,
                    short_name=spec.short_name,
                    category=spec.category,
                    category_label=spec.category_label,
                    unit=spec.unit,
                    purity_label=spec.purity_label,
                    has_gram_equivalent=spec.has_gram_equivalent,
                    base_buy_price=base_buy,
                    base_sell_price=base_sell,
                    buy_price=adj_buy,
                    sell_price=adj_sell,
                    spread_amount=spread_amt,
                    spread_pct=spread_pct,
                    change_pct=item["change_pct"],
                    updated_time=item["time"],
                    is_calculable_tl=spec.is_calculable_tl,
                )
            )

        return GoldTrackingSnapshot(
            quotes=tuple(quotes_list),
            source=source,
            source_label=source_label,
            fallback_used=fallback_used,
            observed_at_display=observed_at_display,
            preset_key=actual_preset_key,
            preset_info=preset,
            is_cache_fresh=is_cache_fresh,
            cache_age_seconds=round(cache_age, 1),
        )

    def _get_or_fetch_raw_quotes(
        self,
        force_refresh: bool = False,
        session: Any = None,
        allow_network: bool = True,
    ) -> dict[str, Any]:
        global _CACHED_RAW_QUOTES, _CACHED_AT_MONOTONIC

        now_mono = time.monotonic()
        with _CACHE_LOCK:
            if _CACHED_RAW_QUOTES is None and (not force_refresh or not allow_network):
                disk_bundle, disk_age = _load_disk_cache()
                if disk_bundle is not None:
                    _CACHED_RAW_QUOTES = disk_bundle
                    _CACHED_AT_MONOTONIC = max(0.0, now_mono - disk_age)

            if (
                not force_refresh
                and _CACHED_RAW_QUOTES is not None
                and (now_mono - _CACHED_AT_MONOTONIC) < CACHE_TTL_SECONDS
            ):
                return _CACHED_RAW_QUOTES

            if not allow_network:
                if _CACHED_RAW_QUOTES is not None:
                    return _CACHED_RAW_QUOTES
                instant_bundle = _build_instant_offline_bundle()
                _CACHED_RAW_QUOTES = instant_bundle
                _CACHED_AT_MONOTONIC = 0.0
                return instant_bundle

        # Tier 1: Harem Altın live table
        harem_circuit = get_provider_circuit("harem_doviz_table")
        if harem_circuit.can_execute():
            try:
                partial = fetch_harem_doviz_table(session=session)
                harem_circuit.record_success()
                gram_buy = partial["gram_altin"]["buy"]
                gram_sell = partial["gram_altin"]["sell"]
                complete = _build_full_raw_map(partial, gram_buy, gram_sell)
                bundle = {
                    "quotes": complete,
                    "source": "harem_altin_live",
                    "source_label": "Harem Altın Canlı (Bursa Referans)",
                    "fallback_used": False,
                    "observed_at_display": datetime.now().strftime("%d.%m.%Y %H:%M"),
                }
                with _CACHE_LOCK:
                    _CACHED_RAW_QUOTES = bundle
                    _CACHED_AT_MONOTONIC = time.monotonic()
                _save_disk_cache(bundle)
                return bundle
            except Exception as exc:
                harem_circuit.record_failure()
                logger.warning("Tier 1 Harem Altın table fetch failed: %s", exc)

        # Tier 2: Truncgil v4 JSON fallback
        truncgil_circuit = get_provider_circuit("truncgil_gold_v4")
        if truncgil_circuit.can_execute():
            try:
                partial = fetch_truncgil_fallback(session=session)
                truncgil_circuit.record_success()
                gram_buy = partial["gram_altin"]["buy"]
                gram_sell = partial["gram_altin"]["sell"]
                complete = _build_full_raw_map(partial, gram_buy, gram_sell)
                bundle = {
                    "quotes": complete,
                    "source": "truncgil_kapalicarsi",
                    "source_label": "Kapalıçarşı Serbest Piyasa (Harem Katsayılı)",
                    "fallback_used": True,
                    "observed_at_display": datetime.now().strftime("%d.%m.%Y %H:%M"),
                }
                with _CACHE_LOCK:
                    _CACHED_RAW_QUOTES = bundle
                    _CACHED_AT_MONOTONIC = time.monotonic()
                _save_disk_cache(bundle)
                return bundle
            except Exception as exc:
                truncgil_circuit.record_failure()
                logger.warning("Tier 2 Truncgil gold fetch failed: %s", exc)

        # Tier 3: Resilient fx_metals_provider + Harem Altın calibrated formula
        base_quotes = fetch_resilient_live_quotes(session=session)
        raw_gold = _parse_decimal(base_quotes.values.get("gold")) or Decimal("6400.00")
        gram_buy = _quantize_2dp(raw_gold * Decimal("0.9945"))
        gram_sell = _quantize_2dp(raw_gold * Decimal("1.0075"))
        now_hm = datetime.now().strftime("%H:%M")
        partial_fallback = {
            "gram_altin": {
                "buy": gram_buy,
                "sell": gram_sell,
                "change_pct": Decimal("0.00"),
                "time": now_hm,
            }
        }
        complete = _build_full_raw_map(partial_fallback, gram_buy, gram_sell)
        bundle = {
            "quotes": complete,
            "source": "calibrated_harem_formula",
            "source_label": "Harem Altın Katsayı Motoru (Yedek Mod)",
            "fallback_used": True,
            "observed_at_display": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
        with _CACHE_LOCK:
            _CACHED_RAW_QUOTES = bundle
            _CACHED_AT_MONOTONIC = time.monotonic()
        return bundle
