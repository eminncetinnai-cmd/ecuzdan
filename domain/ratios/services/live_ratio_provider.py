"""
Live Market Ratio Provider — domain/ratios/services/live_ratio_provider.py
Fetches live market asset quotes and computes real-time ratios for key market indicators.
Pure domain logic: No Flask or DB dependencies. Resilient fail-safe fallback.
"""

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Tickers queried for live macro ratios
LIVE_RATIO_TICKERS = {
    'gold': 'GC=F',
    'silver': 'SI=F',
    'oil': 'CL=F',
    'copper': 'HG=F',
    'vix': '^VIX',
    'us10y': '^TNX',
    'us2y': '^IRX',  # short-term treasury proxy or 2y
    'dxy': 'DX-Y.NYB',
    'bist100': 'XU100.IS',
    'usdtry': 'USDTRY=X',
}


def _round_dec(val: float, scale: int = 2) -> Decimal:
    """Convert float to quantized Decimal safely."""
    fmt = '0.' + '0' * scale if scale > 0 else '0'
    return Decimal(str(round(val, scale))).quantize(Decimal(fmt), rounding=ROUND_HALF_UP)


class LiveRatioProvider:
    """Fetches real-time market quotes and computes live values for macro ratios."""

    def __init__(self, yf_client=None) -> None:
        self._yf = yf_client

    def _get_yf(self):
        if self._yf is not None:
            return self._yf
        import yfinance as yf
        return yf

    def fetch_live_quotes(self) -> Dict[str, float]:
        """Fetch latest close or regularMarketPrice for macro tickers."""
        quotes: Dict[str, float] = {}
        try:
            yf = self._get_yf()
            tickers_list = list(LIVE_RATIO_TICKERS.values())
            data = yf.download(tickers_list, period="5d", interval="1d", progress=False, group_by='ticker')

            for key, symbol in LIVE_RATIO_TICKERS.items():
                try:
                    if symbol in data and not data[symbol].empty:
                        series = data[symbol]['Close'].dropna()
                        if not series.empty:
                            quotes[key] = float(series.iloc[-1])
                except Exception as e:
                    logger.debug("Failed extracting price for %s: %s", symbol, e)
        except Exception as e:
            logger.warning("Live market ratio batch download failed: %s", e)

        return quotes

    def compute_live_ratios(self, quotes: Optional[Dict[str, float]] = None) -> Dict[str, Decimal]:
        """Calculate live values for macro ratios based on fetched prices."""
        if quotes is None:
            quotes = self.fetch_live_quotes()

        live_ratios: Dict[str, Decimal] = {}

        # 1. Altın / Gümüş Rasyosu (Gold / Silver)
        if quotes.get('gold') and quotes.get('silver') and quotes['silver'] > 0:
            live_ratios['gold_silver_ratio'] = _round_dec(quotes['gold'] / quotes['silver'], 1)

        # 2. Altın / Petrol Rasyosu (Gold / Oil)
        if quotes.get('gold') and quotes.get('oil') and quotes['oil'] > 0:
            live_ratios['gold_oil_ratio'] = _round_dec(quotes['gold'] / quotes['oil'], 1)

        # 3. Bakır / Altın Rasyosu (Copper / Gold)
        if quotes.get('copper') and quotes.get('gold') and quotes['gold'] > 0:
            live_ratios['copper_gold_ratio'] = _round_dec((quotes['copper'] * 1000) / quotes['gold'], 2)

        # 4. VIX Volatilite Endeksi
        if quotes.get('vix') and quotes['vix'] > 0:
            live_ratios['vix_index'] = _round_dec(quotes['vix'], 1)

        # 5. ABD 10Y - 2Y Getiri Eğrisi (Yield Curve)
        if quotes.get('us10y') and quotes.get('us2y'):
            spread = quotes['us10y'] - quotes['us2y']
            live_ratios['us_yield_curve_10y_2y'] = _round_dec(spread, 2)

        # 6. Dolar Endeksi (DXY)
        if quotes.get('dxy') and quotes['dxy'] > 0:
            live_ratios['dxy_index'] = _round_dec(quotes['dxy'], 1)

        # 7. BIST 100 Dolar Bazlı Endeks (BIST / USD)
        if quotes.get('bist100') and quotes.get('usdtry') and quotes['usdtry'] > 0:
            live_ratios['bist_usd_index'] = _round_dec(quotes['bist100'] / quotes['usdtry'], 0)

        return live_ratios

    @staticmethod
    def apply_live_values_to_definitions(
        definitions: List,
        live_values: Dict[str, Decimal]
    ) -> List:
        """
        Updates the final point of each definition's series with the live calculated value.
        Preserves immutability by creating fresh RatioDefinition instances.
        """
        from domain.ratios.entities.ratio_models import MonthlyRatioPoint, RatioDefinition

        if not live_values:
            return definitions

        updated_defs = []
        for d in definitions:
            if d.code in live_values and d.series:
                new_val = live_values[d.code]
                orig_last = d.series[-1]
                updated_last = MonthlyRatioPoint(
                    date=orig_last.date,
                    display_date=orig_last.display_date,
                    value=new_val,
                    mom_change_pct=orig_last.mom_change_pct,
                    yoy_change_pct=orig_last.yoy_change_pct
                )
                new_series = list(d.series[:-1]) + [updated_last]
                updated_defs.append(
                    RatioDefinition(
                        code=d.code,
                        name=d.name,
                        category=d.category,
                        category_name=d.category_name,
                        unit=d.unit,
                        description=d.description,
                        normal_min=d.normal_min,
                        normal_max=d.normal_max,
                        series=new_series,
                        icon_emoji=d.icon_emoji,
                        chart_color=d.chart_color
                    )
                )
            else:
                updated_defs.append(d)

        return updated_defs
