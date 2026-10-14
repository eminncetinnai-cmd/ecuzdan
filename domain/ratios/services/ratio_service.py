"""
Domain Service for World-Renowned Macro and Financial Market Ratios.
Pure business logic: calculation of MoM/YoY changes, threshold evaluations, signal statuses, and timeframe filtering.
No Flask or DB dependencies.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

from domain.ratios.data.historical_ratios_data import get_all_ratio_definitions
from domain.ratios.entities.ratio_models import (
    EvaluatedRatio,
    MonthlyRatioPoint,
    RatioDefinition,
    RatiosDashboardDTO,
    SignalStatus,
)


class MacroRatioService:
    """Service for macro ratio evaluation, statistical indicators and timeline transformations."""

    def __init__(self, definitions: Optional[List[RatioDefinition]] = None) -> None:
        self._definitions = definitions or get_all_ratio_definitions()

    def build_dashboard(self, range_key: str = "all", category_filter: Optional[str] = None) -> RatiosDashboardDTO:
        """Build a fully evaluated and filtered dashboard DTO."""
        evaluated_ratios: List[EvaluatedRatio] = []

        healthy_count = 0
        neutral_count = 0
        elevated_count = 0

        categories = [
            "Tümü (20 Rasyo)",
            "🏛️ Değerleme & Makro",
            "🪙 Emtialar & Altın",
            "📈 Tahvil & Getiri Eğrisi",
            "⚡ Risk & Volatilite",
            "🇹🇷 Türkiye & Gelişen Piyasalar"
        ]

        for defn in self._definitions:
            if category_filter and category_filter != "all" and defn.category.value != category_filter:
                continue

            # Calculate MoM and YoY for points
            enriched_series = self._enrich_series(defn.series)
            filtered_series = self._filter_by_range(enriched_series, range_key)

            if not filtered_series:
                continue

            latest_pt = filtered_series[-1]
            signal_status, signal_label = self._evaluate_signal(latest_pt.value, defn)

            if signal_status == SignalStatus.HEALTHY:
                healthy_count += 1
            elif signal_status == SignalStatus.NEUTRAL:
                neutral_count += 1
            else:
                elevated_count += 1

            evaluated_ratios.append(
                EvaluatedRatio(
                    code=defn.code,
                    name=defn.name,
                    category=defn.category,
                    category_name=defn.category_name,
                    unit=defn.unit,
                    description=defn.description,
                    normal_min=defn.normal_min,
                    normal_max=defn.normal_max,
                    latest_date=latest_pt.date,
                    latest_display_date=latest_pt.display_date,
                    latest_value=latest_pt.value,
                    mom_change_pct=latest_pt.mom_change_pct,
                    yoy_change_pct=latest_pt.yoy_change_pct,
                    signal_status=signal_status,
                    signal_label=signal_label,
                    icon_emoji=defn.icon_emoji,
                    chart_color=defn.chart_color,
                    series=filtered_series,
                )
            )

        latest_period = evaluated_ratios[0].latest_display_date if evaluated_ratios else "Ağustos 2026"

        return RatiosDashboardDTO(
            total_ratios=len(evaluated_ratios),
            healthy_count=healthy_count,
            neutral_count=neutral_count,
            elevated_count=elevated_count,
            categories=categories,
            ratios=evaluated_ratios,
            latest_period_display=latest_period,
        )

    def _enrich_series(self, series: List[MonthlyRatioPoint]) -> List[MonthlyRatioPoint]:
        """Compute MoM and YoY change percentages for all historical points."""
        enriched: List[MonthlyRatioPoint] = []

        for i, pt in enumerate(series):
            # MoM change
            mom_change = Decimal('0')
            if i > 0:
                prev_val = series[i - 1].value
                if prev_val != Decimal('0'):
                    mom_change = ((pt.value - prev_val) / abs(prev_val) * Decimal('100')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            # YoY change (12 months prior)
            yoy_change = Decimal('0')
            if i >= 12:
                year_ago_val = series[i - 12].value
                if year_ago_val != Decimal('0'):
                    yoy_change = ((pt.value - year_ago_val) / abs(year_ago_val) * Decimal('100')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            enriched.append(
                MonthlyRatioPoint(
                    date=pt.date,
                    display_date=pt.display_date,
                    value=pt.value,
                    mom_change_pct=mom_change,
                    yoy_change_pct=yoy_change,
                )
            )

        return enriched

    def _filter_by_range(self, series: List[MonthlyRatioPoint], range_key: str) -> List[MonthlyRatioPoint]:
        """Filter series based on range key ('6m', '1y', '2y', 'all')."""
        if not series:
            return []

        key = range_key.strip().lower()
        if key == "6m":
            return series[-6:] if len(series) >= 6 else series
        elif key == "1y":
            return series[-12:] if len(series) >= 12 else series
        elif key == "2y":
            return series[-24:] if len(series) >= 24 else series
        return series

    def _evaluate_signal(self, val: Decimal, defn: RatioDefinition) -> tuple[SignalStatus, str]:
        """Evaluate ratio health against historical normal bounds."""
        min_bound = defn.normal_min
        max_bound = defn.normal_max

        # Check if inside normal range
        if min_bound <= val <= max_bound:
            return SignalStatus.HEALTHY, "🟢 Normal / Dengeli"

        # Tolerance buffer 15%
        buffer_min = min_bound - (abs(min_bound) * Decimal('0.20')) if min_bound != 0 else Decimal('-0.5')
        buffer_max = max_bound + (abs(max_bound) * Decimal('0.20')) if max_bound != 0 else Decimal('+0.5')

        if buffer_min <= val <= buffer_max:
            return SignalStatus.NEUTRAL, "🟡 Eşik Seviyesinde"

        return SignalStatus.ELEVATED, "🔴 Aşırı / Riskli"
