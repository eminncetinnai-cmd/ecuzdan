"""Domain entities and data models for Central Bank Reserves and Global Gold Holdings.

Pure domain layer with zero external framework/database dependencies.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class MonthlyReservePoint:
    """Represents a single monthly reserve observation for a central bank."""
    date: str  # YYYY-MM format, e.g. "2026-08"
    display_date: str  # E.g. "Ağustos 2026"
    gross_total_usd_billion: Decimal
    gross_fx_usd_billion: Decimal
    gold_usd_billion: Decimal
    gold_tonnes: Decimal
    net_reserves_usd_billion: Decimal
    net_reserves_ex_swap_usd_billion: Decimal
    mom_change_gross_pct: Decimal = Decimal('0.0')
    yoy_change_gross_pct: Decimal = Decimal('0.0')
    gold_share_pct: Decimal = Decimal('0.0')


@dataclass(frozen=True)
class GlobalCentralBankReserve:
    """Represents central bank total reserves and gold holdings for a country."""
    country_code: str
    country_name: str
    central_bank_name: str
    flag_emoji: str
    total_reserves_usd_billion: Decimal
    gold_tonnes: Decimal
    gold_usd_billion: Decimal
    gold_share_pct: Decimal
    fx_reserves_usd_billion: Decimal
    net_change_1y_tonnes: Decimal
    rank: int
    note: Optional[str] = None


@dataclass
class ReservesKPIs:
    """KPI summary values for the latest available reporting period."""
    latest_date_display: str
    latest_gross_total: Decimal
    latest_gross_fx: Decimal
    latest_gold_usd: Decimal
    latest_gold_tonnes: Decimal
    latest_net_ex_swap: Decimal
    latest_gold_share_pct: Decimal
    gross_mom_pct: Decimal
    gross_yoy_pct: Decimal
    net_ex_swap_mom_change_usd: Decimal
    gold_tonnes_1y_change: Decimal
    prev_gross_total: Decimal = Decimal('0.0')
    prev_gross_fx: Decimal = Decimal('0.0')
    prev_gold_usd: Decimal = Decimal('0.0')
    prev_gold_tonnes: Decimal = Decimal('0.0')
    prev_net_ex_swap: Decimal = Decimal('0.0')
    prev_date_display: str = ""
    gross_mom_change_usd: Decimal = Decimal('0.0')
    gold_mom_change_tonnes: Decimal = Decimal('0.0')


@dataclass
class ReservesOverviewDTO:
    """Aggregated DTO for central bank reserves presentation and analytics."""
    kpis: ReservesKPIs
    monthly_series: List[MonthlyReservePoint] = field(default_factory=list)
    global_banks: List[GlobalCentralBankReserve] = field(default_factory=list)
    selected_range: str = "all"
    total_months_available: int = 0
