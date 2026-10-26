"""Application use case for retrieving central bank reserves analytics and charts."""

from typing import Any, Dict

from domain.central_bank.entities.reserve_models import ReservesOverviewDTO
from domain.central_bank.services.reserve_service import CentralBankReserveService


class GetReservesOverviewQuery:
    """Orchestrates central bank reserve analytics, KPI extraction, and chart payload formatting."""

    _default_service: CentralBankReserveService | None = None
    _result_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, service: CentralBankReserveService | None = None) -> None:
        self._custom_service = service is not None
        if service is not None:
            self._service = service
        else:
            if GetReservesOverviewQuery._default_service is None:
                GetReservesOverviewQuery._default_service = CentralBankReserveService()
            self._service = GetReservesOverviewQuery._default_service

    def execute(self, range_key: str = "all") -> Dict[str, Any]:
        """Execute the query and return a structured payload for templates and JSON APIs."""
        clean_key = (range_key or "all").strip().lower()
        if not self._custom_service and clean_key in GetReservesOverviewQuery._result_cache:
            return GetReservesOverviewQuery._result_cache[clean_key]

        overview: ReservesOverviewDTO = self._service.build_overview(range_key)

        # Prepare TCMB historical Chart.js payload
        tcmb_labels = [p.display_date for p in overview.monthly_series]
        tcmb_dates = [p.date for p in overview.monthly_series]
        tcmb_gross_total = [float(p.gross_total_usd_billion) for p in overview.monthly_series]
        tcmb_gross_fx = [float(p.gross_fx_usd_billion) for p in overview.monthly_series]
        tcmb_gold_usd = [float(p.gold_usd_billion) for p in overview.monthly_series]
        tcmb_gold_tonnes = [float(p.gold_tonnes) for p in overview.monthly_series]
        tcmb_net_reserves = [float(p.net_reserves_usd_billion) for p in overview.monthly_series]
        tcmb_net_ex_swap = [float(p.net_reserves_ex_swap_usd_billion) for p in overview.monthly_series]
        tcmb_gold_share = [float(p.gold_share_pct) for p in overview.monthly_series]

        # Prepare Global Comparisons Chart.js payload (Top 10 sorted by gold)
        sorted_by_gold = sorted(overview.global_banks, key=lambda x: x.gold_tonnes, reverse=True)
        global_labels = [f"{b.flag_emoji} {b.country_name}" for b in sorted_by_gold]
        global_gold_tonnes = [float(b.gold_tonnes) for b in sorted_by_gold]
        global_gold_share = [float(b.gold_share_pct) for b in sorted_by_gold]
        global_gold_usd = [float(b.gold_usd_billion) for b in sorted_by_gold]
        global_total_reserves = [float(b.total_reserves_usd_billion) for b in sorted_by_gold]
        global_fx_reserves = [float(b.fx_reserves_usd_billion) for b in sorted_by_gold]

        # Spotlight specific key central banks (USA, China, Turkey)
        spotlight = {}
        for b in overview.global_banks:
            if b.country_code in ("US", "CN", "TR"):
                spotlight[b.country_code.lower()] = {
                    "rank": b.rank,
                    "country_name": b.country_name,
                    "flag_emoji": b.flag_emoji,
                    "central_bank_name": b.central_bank_name,
                    "total_reserves": float(b.total_reserves_usd_billion),
                    "gold_tonnes": float(b.gold_tonnes),
                    "gold_usd": float(b.gold_usd_billion),
                    "gold_share_pct": float(b.gold_share_pct),
                    "net_change_1y_tonnes": float(b.net_change_1y_tonnes),
                    "note": b.note,
                }

        result = {
            "kpis": {
                "latest_date_display": overview.kpis.latest_date_display,
                "latest_gross_total": float(overview.kpis.latest_gross_total),
                "latest_gross_fx": float(overview.kpis.latest_gross_fx),
                "latest_gold_usd": float(overview.kpis.latest_gold_usd),
                "latest_gold_tonnes": float(overview.kpis.latest_gold_tonnes),
                "latest_net_ex_swap": float(overview.kpis.latest_net_ex_swap),
                "latest_gold_share_pct": float(overview.kpis.latest_gold_share_pct),
                "gross_mom_pct": float(overview.kpis.gross_mom_pct),
                "gross_yoy_pct": float(overview.kpis.gross_yoy_pct),
                "net_ex_swap_mom_change_usd": float(overview.kpis.net_ex_swap_mom_change_usd),
                "gold_tonnes_1y_change": float(overview.kpis.gold_tonnes_1y_change),
                "prev_gross_total": float(overview.kpis.prev_gross_total),
                "prev_gross_fx": float(overview.kpis.prev_gross_fx),
                "prev_gold_usd": float(overview.kpis.prev_gold_usd),
                "prev_gold_tonnes": float(overview.kpis.prev_gold_tonnes),
                "prev_net_ex_swap": float(overview.kpis.prev_net_ex_swap),
                "prev_date_display": overview.kpis.prev_date_display,
                "gross_mom_change_usd": float(overview.kpis.gross_mom_change_usd),
                "gold_mom_change_tonnes": float(overview.kpis.gold_mom_change_tonnes),
            },
            "spotlight": spotlight,
            "charts": {
                "tcmb": {
                    "labels": tcmb_labels,
                    "dates": tcmb_dates,
                    "gross_total": tcmb_gross_total,
                    "gross_fx": tcmb_gross_fx,
                    "gold_usd": tcmb_gold_usd,
                    "gold_tonnes": tcmb_gold_tonnes,
                    "net_reserves": tcmb_net_reserves,
                    "net_ex_swap": tcmb_net_ex_swap,
                    "gold_share_pct": tcmb_gold_share,
                },
                "global_gold": {
                    "labels": global_labels,
                    "gold_tonnes": global_gold_tonnes,
                    "gold_share_pct": global_gold_share,
                    "gold_usd": global_gold_usd,
                },
                "global_reserves": {
                    "labels": global_labels,
                    "total_reserves": global_total_reserves,
                    "fx_reserves": global_fx_reserves,
                    "gold_usd": global_gold_usd,
                },
            },
            "monthly_table": [
                {
                    "date": p.date,
                    "display_date": p.display_date,
                    "gross_total": float(p.gross_total_usd_billion),
                    "gross_fx": float(p.gross_fx_usd_billion),
                    "gold_usd": float(p.gold_usd_billion),
                    "gold_tonnes": float(p.gold_tonnes),
                    "net_reserves": float(p.net_reserves_usd_billion),
                    "net_ex_swap": float(p.net_reserves_ex_swap_usd_billion),
                    "mom_change": float(p.mom_change_gross_pct),
                    "yoy_change": float(p.yoy_change_gross_pct),
                    "gold_share": float(p.gold_share_pct),
                }
                for p in reversed(overview.monthly_series)
            ],
            "global_table": [
                {
                    "rank": b.rank,
                    "country_code": b.country_code,
                    "country_name": b.country_name,
                    "central_bank_name": b.central_bank_name,
                    "flag_emoji": b.flag_emoji,
                    "total_reserves": float(b.total_reserves_usd_billion),
                    "gold_tonnes": float(b.gold_tonnes),
                    "gold_usd": float(b.gold_usd_billion),
                    "gold_share_pct": float(b.gold_share_pct),
                    "fx_reserves": float(b.fx_reserves_usd_billion),
                    "net_change_1y_tonnes": float(b.net_change_1y_tonnes),
                    "note": b.note,
                }
                for b in overview.global_banks
            ],
            "selected_range": overview.selected_range,
            "total_months_available": overview.total_months_available,
        }
        if not self._custom_service:
            GetReservesOverviewQuery._result_cache[clean_key] = result
        return result
