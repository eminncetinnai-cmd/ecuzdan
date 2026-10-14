"""
Domain Service for calculating cross-asset correlation matrices among macro ratios.
Pure business logic: zero Flask or DB model dependencies.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from domain.ratios.entities.ratio_models import RatioDefinition


@dataclass(frozen=True)
class CorrelationCell:
    """A single cell in the correlation matrix."""
    row_code: str
    row_name: str
    col_code: str
    col_name: str
    coefficient: float           # Value between -1.0 and 1.0
    strength_label: str          # e.g., 'Güçlü Negatif', 'Nötr / Bağımsız', 'Güçlü Pozitif'
    color_class: str             # e.g., 'corr-pos-high', 'corr-pos-mid', 'corr-neutral', 'corr-neg-mid', 'corr-neg-high'
    description: str             # Financial explanation of this specific pair


@dataclass(frozen=True)
class CorrelationMatrix:
    """Full cross-asset correlation matrix with row/col labels and data cells."""
    labels: List[Tuple[str, str]]             # List of (code, short_name)
    matrix: List[List[CorrelationCell]]       # 2D grid of cells
    period_count: int                         # Number of historical points analyzed
    period_range: str                         # e.g., '2024-01 - 2026-08'


class MacroCorrelationService:
    """Calculates statistical Pearson correlation between historical macro series."""

    CORE_BENCHMARK_CODES = [
        "buffett_indicator",     # Hisse Değerleme
        "vix_index",             # Risk & Korku
        "yield_curve_10y2y",     # Getiri Eğrisi
        "gold_silver_ratio",     # Güvenli Liman
        "copper_gold_ratio",     # Sanayi / Dr. Copper
        "high_yield_spread",     # Kredi Riski
        "dxy_index",             # Dolar Gücü
        "turkey_5y_cds",         # Türkiye Risk Primi
    ]

    SHORT_NAMES: Dict[str, str] = {
        "buffett_indicator": "Buffett İnd.",
        "vix_index": "VIX Volatilite",
        "yield_curve_10y2y": "10Y-2Y Spread",
        "gold_silver_ratio": "Altın / Gümüş",
        "copper_gold_ratio": "Bakır / Altın",
        "high_yield_spread": "Kredi Spreadi",
        "dxy_index": "DXY Dolar",
        "turkey_5y_cds": "Türkiye CDS",
    }

    PAIR_INSIGHTS: Dict[Tuple[str, str], str] = {
        ("buffett_indicator", "vix_index"): "Piyasa aşırı değerlendiğinde VIX baskılanır; piyasa şoklarında ters yönlü keskin sıçrama üretir.",
        ("vix_index", "buffett_indicator"): "Volatilite ile borsa çarpanları ters yönde hareket etme eğilimindedir.",
        ("yield_curve_10y2y", "vix_index"): "Getiri eğrisinin dikleşmesi (un-inversion) resesyon başlangıcında VIX artışıyla çakışır.",
        ("gold_silver_ratio", "copper_gold_ratio"): "Sanayi büyümesi (Bakır) güçlenirken Altın/Gümüş rasyosu düşer (ters korelasyon).",
        ("dxy_index", "gold_silver_ratio"): "Doların küresel güçlenmesi emtialar üzerinde baskı oluşturarak rasyoları etkiler.",
        ("turkey_5y_cds", "dxy_index"): "Küresel dolar sıkılaşması gelişen piyasa ve Türkiye CDS primlerine yukarı yönlü baskı yapar.",
        ("turkey_5y_cds", "vix_index"): "Küresel riskten kaçış dönemlerinde Türkiye CDS primi ile VIX eş anlı yükselir.",
        ("high_yield_spread", "vix_index"): "Şirket temerrüt primleri ile hisse volatilitesi yüksek pozitif korelasyonla el ele gider.",
    }

    def calculate_correlation(self, series_a: Sequence[float], series_b: Sequence[float]) -> float:
        """
        Calculate Pearson correlation coefficient r between two series.
        Returns float between -1.0 and 1.0.
        """
        n = min(len(series_a), len(series_b))
        if n < 3:
            return 0.0

        vals_a = list(series_a[-n:])
        vals_b = list(series_b[-n:])

        mean_a = sum(vals_a) / n
        mean_b = sum(vals_b) / n

        var_a = sum((x - mean_a) ** 2 for x in vals_a)
        var_b = sum((y - mean_b) ** 2 for y in vals_b)

        if var_a <= 1e-9 or var_b <= 1e-9:
            return 0.0

        cov = sum((vals_a[i] - mean_a) * (vals_b[i] - mean_b) for i in range(n))
        denom = math.sqrt(var_a * var_b)

        if denom <= 1e-9:
            return 0.0

        r = cov / denom
        return max(-1.0, min(1.0, round(r, 2)))

    def _get_strength_and_style(self, r: float) -> Tuple[str, str]:
        """Categorize correlation coefficient into financial label and visual class."""
        if r >= 0.70:
            return "Güçlü Pozitif", "corr-pos-high"
        elif r >= 0.30:
            return "Ilımlı Pozitif", "corr-pos-mid"
        elif r > -0.30:
            return "Nötr / Bağımsız", "corr-neutral"
        elif r > -0.70:
            return "Ilımlı Negatif", "corr-neg-mid"
        else:
            return "Güçlü Negatif", "corr-neg-high"

    def _get_pair_description(self, code_a: str, code_b: str, r: float, name_a: str, name_b: str) -> str:
        """Get intuitive financial takeaway for a given pair."""
        if code_a == code_b:
            return f"{name_a} kendisiyle tam birebir korelasyona sahiptir (1.00)."

        custom = self.PAIR_INSIGHTS.get((code_a, code_b)) or self.PAIR_INSIGHTS.get((code_b, code_a))
        if custom:
            return custom

        if r >= 0.50:
            return f"{name_a} yükseldiğinde {name_b} genellikle eş yönlü yükselme eğilimindedir ({r:+.2f})."
        elif r <= -0.50:
            return f"{name_a} ile {name_b} ters yönlü hareket eder; doğal bir risk dengeleme (hedge) ilişkisi sunar ({r:+.2f})."
        else:
            return f"{name_a} ile {name_b} arasında doğrusal bağımlılık zayıftır ({r:+.2f}); bağımsız dinamiklerle fiyatlanırlar."

    def build_matrix(
        self,
        ratios: Sequence[RatioDefinition],
        selected_codes: Optional[List[str]] = None
    ) -> CorrelationMatrix:
        """
        Builds the 2D correlation matrix for the specified (or default benchmark) ratios.
        """
        target_codes = selected_codes or self.CORE_BENCHMARK_CODES
        ratio_map = {r.code: r for r in ratios if r.code in target_codes}

        valid_codes = [c for c in target_codes if c in ratio_map]
        labels: List[Tuple[str, str]] = [
            (c, self.SHORT_NAMES.get(c, ratio_map[c].name[:14]))
            for c in valid_codes
        ]

        series_data: Dict[str, List[float]] = {}
        period_count = 0
        date_start = ""
        date_end = ""

        for c in valid_codes:
            pts = ratio_map[c].series
            if pts:
                period_count = max(period_count, len(pts))
                if not date_start:
                    date_start = pts[0].date
                date_end = pts[-1].date
                series_data[c] = [float(p.value) for p in pts]
            else:
                series_data[c] = []

        grid: List[List[CorrelationCell]] = []
        for i, code_row in enumerate(valid_codes):
            row_cells: List[CorrelationCell] = []
            name_row = self.SHORT_NAMES.get(code_row, ratio_map[code_row].name)
            for j, code_col in enumerate(valid_codes):
                name_col = self.SHORT_NAMES.get(code_col, ratio_map[code_col].name)
                if i == j:
                    r = 1.00
                else:
                    r = self.calculate_correlation(series_data.get(code_row, []), series_data.get(code_col, []))

                strength, css_class = self._get_strength_and_style(r)
                desc = self._get_pair_description(code_row, code_col, r, name_row, name_col)

                row_cells.append(
                    CorrelationCell(
                        row_code=code_row,
                        row_name=name_row,
                        col_code=code_col,
                        col_name=name_col,
                        coefficient=r,
                        strength_label=strength,
                        color_class=css_class,
                        description=desc,
                    )
                )
            grid.append(row_cells)

        period_range_str = f"{date_start} – {date_end}" if date_start and date_end else "Son 24 Ay"
        return CorrelationMatrix(
            labels=labels,
            matrix=grid,
            period_count=period_count,
            period_range=period_range_str,
        )
