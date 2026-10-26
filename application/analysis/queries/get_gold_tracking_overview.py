"""Application use case for building the Gold Tracking (Altın Takip) overview payload."""

from __future__ import annotations

from typing import Any

from domain.analysis.services.gold_tracking_service import (
    MARGIN_PRESETS,
    GoldDerivativeQuote,
    GoldTrackingService,
    GoldTrackingSnapshot,
)


class GetGoldTrackingOverviewQuery:
    """Orchestrates Harem Altın & Bursa Jeweler quotes and serializes payload for UI/API."""

    def __init__(self, service: GoldTrackingService | None = None) -> None:
        self._service = service or GoldTrackingService()

    def execute(
        self,
        preset_key: str = "bursa_harem",
        force_refresh: bool = False,
        allow_network: bool = True,
    ) -> dict[str, Any]:
        snapshot: GoldTrackingSnapshot = self._service.get_snapshot(
            preset_key=preset_key,
            force_refresh=force_refresh,
            allow_network=allow_network,
        )

        serialized_quotes: list[dict[str, Any]] = [
            self._serialize_quote(q) for q in snapshot.quotes
        ]
        by_code: dict[str, dict[str, Any]] = {q["code"]: q for q in serialized_quotes}

        # Spotlight KPIs (Gram 24K, Çeyrek Yeni, Yarım Yeni, Tam Yeni, 22 Ayar Bilezik, Ata Yeni)
        spotlight = {
            "gram_altin": by_code.get("gram_altin"),
            "ceyrek_yeni": by_code.get("ceyrek_yeni"),
            "yarim_yeni": by_code.get("yarim_yeni"),
            "tam_yeni": by_code.get("tam_yeni"),
            "bilezik_22": by_code.get("bilezik_22"),
            "ata_yeni": by_code.get("ata_yeni"),
        }

        categories = [
            {"key": "all", "label": "Tümü", "count": len(serialized_quotes)},
            {
                "key": "sarrafiye_yeni",
                "label": "Yeni Ziynet",
                "count": sum(1 for q in serialized_quotes if q["category"] == "sarrafiye_yeni"),
            },
            {
                "key": "sarrafiye_eski",
                "label": "Eski Ziynet",
                "count": sum(1 for q in serialized_quotes if q["category"] == "sarrafiye_eski"),
            },
            {
                "key": "gram_bilezik",
                "label": "Gram & Bilezik",
                "count": sum(1 for q in serialized_quotes if q["category"] == "gram_bilezik"),
            },
            {
                "key": "global_emtia",
                "label": "Küresel & Külçe",
                "count": sum(1 for q in serialized_quotes if q["category"] == "global_emtia"),
            },
        ]

        presets = [
            {
                "key": k,
                "label": v["label"],
                "short_label": v["short_label"],
                "description": v["description"],
                "buy_adj_pct": float(v["buy_adj_pct"]),
                "sell_adj_pct": float(v["sell_adj_pct"]),
            }
            for k, v in MARGIN_PRESETS.items()
        ]

        return {
            "source": snapshot.source,
            "source_label": snapshot.source_label,
            "fallback_used": snapshot.fallback_used,
            "observed_at_display": snapshot.observed_at_display,
            "is_cache_fresh": snapshot.is_cache_fresh,
            "cache_age_seconds": snapshot.cache_age_seconds,
            "preset_key": snapshot.preset_key,
            "preset_info": {
                "key": snapshot.preset_info["key"],
                "label": snapshot.preset_info["label"],
                "short_label": snapshot.preset_info["short_label"],
                "description": snapshot.preset_info["description"],
                "buy_adj_pct": float(snapshot.preset_info["buy_adj_pct"]),
                "sell_adj_pct": float(snapshot.preset_info["sell_adj_pct"]),
            },
            "presets": presets,
            "categories": categories,
            "spotlight": spotlight,
            "quotes": serialized_quotes,
            "calculable_quotes": [q for q in serialized_quotes if q["is_calculable_tl"]],
        }

    @staticmethod
    def _serialize_quote(q: GoldDerivativeQuote) -> dict[str, Any]:
        return {
            "code": q.code,
            "name": q.name,
            "short_name": q.short_name,
            "category": q.category,
            "category_label": q.category_label,
            "unit": q.unit,
            "purity_label": q.purity_label,
            "has_gram_equivalent": float(q.has_gram_equivalent),
            "base_buy_price": float(q.base_buy_price),
            "base_sell_price": float(q.base_sell_price),
            "buy_price": float(q.buy_price),
            "sell_price": float(q.sell_price),
            "spread_amount": float(q.spread_amount),
            "spread_pct": float(q.spread_pct),
            "change_pct": float(q.change_pct),
            "updated_time": q.updated_time,
            "is_calculable_tl": q.is_calculable_tl,
        }
