"""Application query for Global Macro & Financial Ratios Dashboard."""

from typing import Any, Dict, List, Optional

from domain.ratios.entities.ratio_models import RatiosDashboardDTO
from domain.ratios.services.ratio_service import MacroRatioService


class GetRatiosDashboardQuery:
    """Orchestrates ratio dashboard data, Chart.js payload formatting, and table matrix extraction."""

    # Class-level cache of updated definitions if live sync occurred
    _cached_definitions: Optional[List] = None
    _result_cache: Dict[Any, Dict[str, Any]] = {}

    def __init__(self, service: Optional[MacroRatioService] = None, live_provider=None) -> None:
        if service is not None:
            self._service = service
        else:
            if GetRatiosDashboardQuery._cached_definitions is None:
                from domain.ratios.data.historical_ratios_data import get_all_ratio_definitions

                GetRatiosDashboardQuery._cached_definitions = get_all_ratio_definitions()
            self._service = MacroRatioService(definitions=GetRatiosDashboardQuery._cached_definitions)
        self._live_provider = live_provider

    def sync_live_market_data(self) -> Dict[str, Any]:
        """Fetch live quotes and update definitions with real-time market calculations."""
        from domain.ratios.data.historical_ratios_data import get_all_ratio_definitions
        from domain.ratios.services.live_ratio_provider import LiveRatioProvider

        provider = self._live_provider or LiveRatioProvider()
        live_values = provider.compute_live_ratios()
        if live_values:
            base_definitions = get_all_ratio_definitions()
            updated_definitions = provider.apply_live_values_to_definitions(base_definitions, live_values)
            GetRatiosDashboardQuery._cached_definitions = updated_definitions
            GetRatiosDashboardQuery._result_cache.clear()
            self._service = MacroRatioService(definitions=updated_definitions)

        return {
            "synced_count": len(live_values),
            "live_values": {k: float(v) for k, v in live_values.items()}
        }

    def execute(self, range_key: str = "all", category_filter: Optional[str] = None) -> Dict[str, Any]:
        """Execute the query and return a structured dictionary for templates and API responses."""
        defs_ref = getattr(self._service, "_definitions", None)
        cache_key = (id(defs_ref) if defs_ref is not None else None, range_key, category_filter)
        if defs_ref is not None and cache_key in GetRatiosDashboardQuery._result_cache:
            return GetRatiosDashboardQuery._result_cache[cache_key]

        dashboard: RatiosDashboardDTO = self._service.build_dashboard(
            range_key=range_key,
            category_filter=category_filter
        )

        ratios_payload: List[Dict[str, Any]] = []

        for r in dashboard.ratios:
            labels = [p.display_date for p in r.series]
            dates = [p.date for p in r.series]
            values = [float(p.value) for p in r.series]
            mom_changes = [float(p.mom_change_pct) for p in r.series]
            yoy_changes = [float(p.yoy_change_pct) for p in r.series]

            # Reference bands for chart annotations / dashed guides
            normal_min_line = [float(r.normal_min) for _ in r.series]
            normal_max_line = [float(r.normal_max) for _ in r.series]

            ratios_payload.append({
                "code": r.code,
                "name": r.name,
                "category": r.category.value,
                "category_name": r.category_name,
                "unit": r.unit,
                "description": r.description,
                "normal_min": float(r.normal_min),
                "normal_max": float(r.normal_max),
                "latest_date": r.latest_date,
                "latest_display_date": r.latest_display_date,
                "latest_value": float(r.latest_value),
                "mom_change_pct": float(r.mom_change_pct),
                "yoy_change_pct": float(r.yoy_change_pct),
                "signal_status": r.signal_status.value,
                "signal_label": r.signal_label,
                "icon_emoji": r.icon_emoji,
                "chart_color": r.chart_color,
                "chart_data": {
                    "labels": labels,
                    "dates": dates,
                    "values": values,
                    "mom_changes": mom_changes,
                    "yoy_changes": yoy_changes,
                    "normal_min_line": normal_min_line,
                    "normal_max_line": normal_max_line,
                }
            })

        # Extract 5 Market Pulse key indicators for instant terminal decision-making
        pulse_keys = {
            "vix": "vix_index",
            "yield_curve": "yield_curve_10y2y",
            "gold_silver": "gold_silver_ratio",
            "buffett": "buffett_indicator",
            "turkey_cds": "turkey_5y_cds",
            "bist_usd": "bist100_usd"
        }
        pulse_map = {}
        for r in ratios_payload:
            for pkey, rcode in pulse_keys.items():
                if r["code"] == rcode:
                    pulse_map[pkey] = r

        # Build category macro climate heatmap summaries
        category_meta = [
            ("VALUATION_MACRO", "Değerleme & Makro"),
            ("COMMODITIES", "Emtialar & Altın"),
            ("YIELD_CURVE_CREDIT", "Tahvil & Getiri Eğrisi"),
            ("VOLATILITY_SENTIMENT", "Risk & Volatilite"),
            ("TURKEY_EM", "Türkiye & EM"),
        ]
        category_summaries = []
        for cat_code, cat_name in category_meta:
            cat_ratios = [r for r in ratios_payload if r["category"] == cat_code]
            if cat_ratios:
                h_c = sum(1 for r in cat_ratios if r["signal_status"] == "HEALTHY")
                n_c = sum(1 for r in cat_ratios if r["signal_status"] == "NEUTRAL")
                e_c = sum(1 for r in cat_ratios if r["signal_status"] == "ELEVATED")

                if e_c >= 2:
                    climate = "ELEVATED"
                    climate_label = "Aşırı / Yüksek Risk"
                elif e_c == 1 or n_c >= 2:
                    climate = "NEUTRAL"
                    climate_label = "Eşik / İzlenmeli"
                else:
                    climate = "HEALTHY"
                    climate_label = "Dengeli / Sağlıklı"

                category_summaries.append({
                    "code": cat_code,
                    "name": cat_name,
                    "total": len(cat_ratios),
                    "healthy_count": h_c,
                    "neutral_count": n_c,
                    "elevated_count": e_c,
                    "climate": climate,
                    "climate_label": climate_label,
                    "ratios": cat_ratios
                })

        # Build Cross-Asset Macro Correlation Matrix
        from domain.ratios.services.macro_correlation_service import MacroCorrelationService
        corr_service = MacroCorrelationService()
        corr_matrix_obj = corr_service.build_matrix(self._service._definitions)

        corr_matrix_payload = {
            "labels": [{"code": l[0], "name": l[1]} for l in corr_matrix_obj.labels],
            "period_count": corr_matrix_obj.period_count,
            "period_range": corr_matrix_obj.period_range,
            "grid": [
                [
                    {
                        "row_code": cell.row_code,
                        "row_name": cell.row_name,
                        "col_code": cell.col_code,
                        "col_name": cell.col_name,
                        "coefficient": cell.coefficient,
                        "strength_label": cell.strength_label,
                        "color_class": cell.color_class,
                        "description": cell.description,
                    }
                    for cell in row
                ]
                for row in corr_matrix_obj.matrix
            ]
        }

        # Build Executive Briefing Takeaway
        high_risk_ratios = [r["name"] for r in ratios_payload if r["signal_status"] == "ELEVATED"]
        healthy_ratios = [r["name"] for r in ratios_payload if r["signal_status"] == "HEALTHY"]

        executive_briefing = {
            "period": dashboard.latest_period_display,
            "healthy_count": dashboard.healthy_count,
            "neutral_count": dashboard.neutral_count,
            "elevated_count": dashboard.elevated_count,
            "headline": "Küresel Varlık Piyasaları Makro İklim & Risk Değerlendirmesi",
            "market_stance": "Dengeli / Seçici İyimserlik (Seçici Büyüme & Gergin Değerleme)",
            "key_risks": high_risk_ratios[:3],
            "key_anchors": healthy_ratios[:3],
            "vix_status": pulse_map.get("vix", {}).get("signal_label", "Sakin"),
            "cds_status": pulse_map.get("turkey_cds", {}).get("signal_label", "İyileşiyor"),
        }

        result = {
            "kpis": {
                "total_ratios": dashboard.total_ratios,
                "healthy_count": dashboard.healthy_count,
                "neutral_count": dashboard.neutral_count,
                "elevated_count": dashboard.elevated_count,
                "latest_period_display": dashboard.latest_period_display,
            },
            "pulse": pulse_map,
            "category_summaries": category_summaries,
            "categories": dashboard.categories,
            "ratios": ratios_payload,
            "correlation_matrix": corr_matrix_payload,
            "executive_briefing": executive_briefing,
            "selected_range": range_key,
        }
        if defs_ref is not None:
            GetRatiosDashboardQuery._result_cache[cache_key] = result
        return result
