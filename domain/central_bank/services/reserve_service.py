"""Domain service for Central Bank Reserves calculations and trend analysis.

Pure business logic layer — completely decoupled from Flask, DB, and UI templates.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

from ..data.historical_reserves import (
    GLOBAL_CENTRAL_BANKS_RAW,
    TCMB_RAW_MONTHLY_SERIES,
    TURKISH_MONTHS,
)
from ..entities.reserve_models import (
    GlobalCentralBankReserve,
    MonthlyReservePoint,
    ReservesKPIs,
    ReservesOverviewDTO,
)


def _to_decimal(val: str | float | int | Decimal) -> Decimal:
    """Safely convert any numeric representation to Decimal."""
    clean = str(val).replace('+', '').strip()
    return Decimal(clean)


def _round_2dp(val: Decimal) -> Decimal:
    """Round Decimal to 2 decimal places."""
    return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _round_1dp(val: Decimal) -> Decimal:
    """Round Decimal to 1 decimal place."""
    return val.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


class CentralBankReserveService:
    """Calculates and manages central bank monthly reserves and global comparisons."""

    def __init__(
        self,
        raw_series: Optional[List[dict]] = None,
        global_banks_raw: Optional[List[dict]] = None,
    ) -> None:
        self._raw_series = raw_series if raw_series is not None else TCMB_RAW_MONTHLY_SERIES
        self._global_banks_raw = global_banks_raw if global_banks_raw is not None else GLOBAL_CENTRAL_BANKS_RAW
        self._processed_series: List[MonthlyReservePoint] = self._process_series()
        self._processed_global_banks: List[GlobalCentralBankReserve] = self._process_global_banks()

    def _process_series(self) -> List[MonthlyReservePoint]:
        """Convert raw series into typed MonthlyReservePoint entities with calculated metrics."""
        points: List[MonthlyReservePoint] = []

        for i, row in enumerate(self._raw_series):
            date_str = str(row["date"])
            year, month = date_str.split("-")
            month_name = TURKISH_MONTHS.get(month, month)
            display_date = f"{month_name} {year}"

            gross_total = _to_decimal(row["gross_total"])
            gross_fx = _to_decimal(row["gross_fx"])
            gold_usd = _to_decimal(row["gold_usd"])
            gold_tonnes = _to_decimal(row["gold_tonnes"])
            net_reserves = _to_decimal(row["net_reserves"])
            net_ex_swap = _to_decimal(row["net_ex_swap"])

            # Gold share in gross reserves %
            gold_share = (
                _round_1dp((gold_usd / gross_total) * Decimal("100"))
                if gross_total > 0
                else Decimal("0.0")
            )

            # MoM change in gross total %
            mom_change = Decimal("0.0")
            if i > 0:
                prev_gross = _to_decimal(self._raw_series[i - 1]["gross_total"])
                if prev_gross > 0:
                    mom_change = _round_2dp(
                        ((gross_total - prev_gross) / prev_gross) * Decimal("100")
                    )

            # YoY change in gross total %
            yoy_change = Decimal("0.0")
            if i >= 12:
                yoy_prev_gross = _to_decimal(self._raw_series[i - 12]["gross_total"])
                if yoy_prev_gross > 0:
                    yoy_change = _round_2dp(
                        ((gross_total - yoy_prev_gross) / yoy_prev_gross) * Decimal("100")
                    )

            points.append(
                MonthlyReservePoint(
                    date=date_str,
                    display_date=display_date,
                    gross_total_usd_billion=gross_total,
                    gross_fx_usd_billion=gross_fx,
                    gold_usd_billion=gold_usd,
                    gold_tonnes=gold_tonnes,
                    net_reserves_usd_billion=net_reserves,
                    net_reserves_ex_swap_usd_billion=net_ex_swap,
                    mom_change_gross_pct=mom_change,
                    yoy_change_gross_pct=yoy_change,
                    gold_share_pct=gold_share,
                )
            )

        return points

    def _process_global_banks(self) -> List[GlobalCentralBankReserve]:
        """Convert raw global data into typed GlobalCentralBankReserve entities."""
        banks: List[GlobalCentralBankReserve] = []
        for row in self._global_banks_raw:
            banks.append(
                GlobalCentralBankReserve(
                    country_code=str(row["country_code"]),
                    country_name=str(row["country_name"]),
                    central_bank_name=str(row["central_bank_name"]),
                    flag_emoji=str(row["flag_emoji"]),
                    total_reserves_usd_billion=_to_decimal(row["total_reserves"]),
                    gold_tonnes=_to_decimal(row["gold_tonnes"]),
                    gold_usd_billion=_to_decimal(row["gold_usd"]),
                    gold_share_pct=_to_decimal(row["gold_share_pct"]),
                    fx_reserves_usd_billion=_to_decimal(row["fx_reserves"]),
                    net_change_1y_tonnes=_to_decimal(row["net_change_1y_tonnes"]),
                    rank=int(row["rank"]),
                    note=row.get("note"),
                )
            )
        return banks

    def get_filtered_series(self, range_key: str = "all") -> List[MonthlyReservePoint]:
        """Filter monthly series by period key ('6m', '1y', '2y', 'all')."""
        if not self._processed_series:
            return []

        clean_key = (range_key or "all").lower().strip()
        if clean_key == "6m":
            return self._processed_series[-6:]
        elif clean_key == "1y":
            return self._processed_series[-12:]
        elif clean_key == "2y":
            return self._processed_series[-24:]
        return list(self._processed_series)

    def calculate_kpis(self) -> ReservesKPIs:
        """Compute key summary KPIs from the latest available month and historical comparisons."""
        if not self._processed_series:
            return ReservesKPIs(
                latest_date_display="--",
                latest_gross_total=Decimal("0.0"),
                latest_gross_fx=Decimal("0.0"),
                latest_gold_usd=Decimal("0.0"),
                latest_gold_tonnes=Decimal("0.0"),
                latest_net_ex_swap=Decimal("0.0"),
                latest_gold_share_pct=Decimal("0.0"),
                gross_mom_pct=Decimal("0.0"),
                gross_yoy_pct=Decimal("0.0"),
                net_ex_swap_mom_change_usd=Decimal("0.0"),
                gold_tonnes_1y_change=Decimal("0.0"),
            )

        latest = self._processed_series[-1]
        prev = self._processed_series[-2] if len(self._processed_series) >= 2 else latest
        yoy_prev = self._processed_series[-13] if len(self._processed_series) >= 13 else self._processed_series[0]

        gross_mom_usd = _round_2dp(latest.gross_total_usd_billion - prev.gross_total_usd_billion)
        gold_mom_tonnes = _round_1dp(latest.gold_tonnes - prev.gold_tonnes)
        net_ex_swap_mom = _round_2dp(
            latest.net_reserves_ex_swap_usd_billion - prev.net_reserves_ex_swap_usd_billion
        )
        gold_tonnes_1y = _round_1dp(latest.gold_tonnes - yoy_prev.gold_tonnes)

        return ReservesKPIs(
            latest_date_display=latest.display_date,
            latest_gross_total=latest.gross_total_usd_billion,
            latest_gross_fx=latest.gross_fx_usd_billion,
            latest_gold_usd=latest.gold_usd_billion,
            latest_gold_tonnes=latest.gold_tonnes,
            latest_net_ex_swap=latest.net_reserves_ex_swap_usd_billion,
            latest_gold_share_pct=latest.gold_share_pct,
            gross_mom_pct=latest.mom_change_gross_pct,
            gross_yoy_pct=latest.yoy_change_gross_pct,
            net_ex_swap_mom_change_usd=net_ex_swap_mom,
            gold_tonnes_1y_change=gold_tonnes_1y,
            prev_gross_total=prev.gross_total_usd_billion,
            prev_gross_fx=prev.gross_fx_usd_billion,
            prev_gold_usd=prev.gold_usd_billion,
            prev_gold_tonnes=prev.gold_tonnes,
            prev_net_ex_swap=prev.net_reserves_ex_swap_usd_billion,
            prev_date_display=prev.display_date,
            gross_mom_change_usd=gross_mom_usd,
            gold_mom_change_tonnes=gold_mom_tonnes,
        )

    def get_global_banks(self) -> List[GlobalCentralBankReserve]:
        """Return the global central banks dataset sorted by rank."""
        return list(self._processed_global_banks)

    def build_overview(self, range_key: str = "all") -> ReservesOverviewDTO:
        """Construct full overview DTO ready for application presentation."""
        filtered_series = self.get_filtered_series(range_key)
        kpis = self.calculate_kpis()
        global_banks = self.get_global_banks()

        return ReservesOverviewDTO(
            kpis=kpis,
            monthly_series=filtered_series,
            global_banks=global_banks,
            selected_range=range_key,
            total_months_available=len(self._processed_series),
        )
