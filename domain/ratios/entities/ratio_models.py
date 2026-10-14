"""Domain entities and value objects for Macro & Financial Market Ratios."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List


class RatioCategory(str, Enum):
    """Categories of world-renowned financial and macroeconomic ratios."""
    VALUATION_MACRO = "VALUATION_MACRO"
    COMMODITIES = "COMMODITIES"
    YIELD_CURVE_CREDIT = "YIELD_CURVE_CREDIT"
    VOLATILITY_SENTIMENT = "VOLATILITY_SENTIMENT"
    TURKEY_EM = "TURKEY_EM"


class SignalStatus(str, Enum):
    """Health / evaluation signal status for a ratio compared to historical norms."""
    HEALTHY = "HEALTHY"      # 🟢 Normal / Healthy / Fairly Valued
    NEUTRAL = "NEUTRAL"      # 🟡 Warning / Near Historical Threshold
    ELEVATED = "ELEVATED"    # 🔴 Stretched / High Risk / Extremes


@dataclass(frozen=True)
class MonthlyRatioPoint:
    """A single monthly historical observation of a ratio."""
    date: str                  # Format: YYYY-MM (e.g., '2026-08')
    display_date: str          # Format: 'Ağu 2026'
    value: Decimal             # Numerical ratio value
    mom_change_pct: Decimal = Decimal('0')   # Month-over-Month change %
    yoy_change_pct: Decimal = Decimal('0')   # Year-over-Year change %


@dataclass(frozen=True)
class RatioDefinition:
    """Complete metadata, reference thresholds and historical series for a ratio."""
    code: str                  # Unique key (e.g. 'buffett_indicator')
    name: str                  # Display name (e.g. 'Buffett Indicator')
    category: RatioCategory    # Group category
    category_name: str         # Turkish display name for category
    unit: str                  # e.g., '%', 'x', 'bps', 'Puan', 'Varil'
    description: str           # Short explanation of what the ratio measures
    normal_min: Decimal        # Benchmark normal lower bound
    normal_max: Decimal        # Benchmark normal upper bound
    series: List[MonthlyRatioPoint] = field(default_factory=list)
    icon_emoji: str = "📊"
    chart_color: str = "#4f46e5"


@dataclass(frozen=True)
class EvaluatedRatio:
    """A ratio evaluated with latest value, signal status, and historical stats."""
    code: str
    name: str
    category: RatioCategory
    category_name: str
    unit: str
    description: str
    normal_min: Decimal
    normal_max: Decimal
    latest_date: str
    latest_display_date: str
    latest_value: Decimal
    mom_change_pct: Decimal
    yoy_change_pct: Decimal
    signal_status: SignalStatus
    signal_label: str
    icon_emoji: str
    chart_color: str
    series: List[MonthlyRatioPoint]


@dataclass(frozen=True)
class RatiosDashboardDTO:
    """Top-level aggregate DTO for the global ratios dashboard."""
    total_ratios: int
    healthy_count: int
    neutral_count: int
    elevated_count: int
    categories: List[str]
    ratios: List[EvaluatedRatio]
    latest_period_display: str
