"""Analysis Engine — Finansal Strateji ve Analiz Motoru.

Kantitatif Piyasa Analizi ve Risk Yönetimi Orkestrasyon Katmanı.
Temel algoritmalar domain/analysis/services/ altındaki saf servisler tarafından sağlanır.

Akademik Referanslar:
- Sharpe (1966): Riske ayarlı getiri ölçümü
- Markowitz (1952): Modern Portföy Teorisi, korelasyon ve çeşitlendirme
- Lo & MacKinlay (1988): Ortalamaya dönüş (mean reversion) modeli
- Gatev, Goetzmann & Rouwenhorst (2006): Pairs trading / rasyo analizi
- Fama (1970): Etkin piyasalar hipotezi
"""
import logging
import threading
from datetime import datetime

from domain.analysis.services.macro_regime_service import (
    REGIME_THRESHOLDS,
    TURKEY_MACRO,
    _apply_risk_free_override,
    get_dynamic_turkey_macro,
)
from domain.analysis.services.macro_regime_service import (
    apply_macro_regime_filter as _apply_macro_regime_filter,
)
from domain.analysis.services.macro_regime_service import (
    generate_opportunity_matrix as _generate_opportunity_matrix,
)
from domain.analysis.services.market_stress_service import (
    CRISIS_CORR_THRESH,
    STRESS_HIGH_THRESH,
    STRESS_MED_THRESH,
)
from domain.analysis.services.market_stress_service import (
    calculate_correlation_matrix as _calculate_correlation_matrix,
)
from domain.analysis.services.market_stress_service import (
    calculate_market_stress_index as _calculate_market_stress_index,
)
from domain.analysis.services.quantitative_risk_service import (
    calculate_historical_var as _calculate_historical_var,
)
from domain.analysis.services.quantitative_risk_service import (
    calculate_risk_parity_weights as _calculate_risk_parity_weights,
)
from domain.analysis.services.quantitative_risk_service import (
    simulate_monte_carlo_path as _simulate_monte_carlo_path,
)
from domain.analysis.services.quantitative_signals import (
    Z_SCORE_THRESHOLD,
)
from domain.analysis.services.quantitative_signals import (
    calculate_mean_reversion_signal as _calculate_mean_reversion_signal,
)
from domain.analysis.services.quantitative_signals import (
    calculate_ratio_signal as _calculate_ratio_signal,
)
from domain.analysis.services.quantitative_signals import (
    calculate_relative_strength as _calculate_relative_strength,
)
from domain.analysis.services.quantitative_signals import (
    calculate_sharpe_ratio as _calculate_sharpe_ratio,
)
from domain.analysis.services.quantitative_signals import (
    calculate_z_score as _calculate_z_score,
)

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Kantitatif Finansal Analiz Motoru.

    Desteklenen Analizler:
    1. Z-Score tabanlı ortalamaya dönüş sinyalleri
    2. Sharpe Ratio (riske ayarlı getiri)
    3. Korelasyon matrisi (çeşitlendirme analizi)
    4. Piyasa stres endeksi (korelasyon bazlı)
    5. Makro rejim filtresi (faiz + enflasyon)
    6. Fırsat matrisi (çapraz varlık rasyo analizi)
    7. Historical VaR ve Monte Carlo simülasyonları
    """

    def __init__(self, market_data_service):
        self.market_data_service = market_data_service
        macro = get_dynamic_turkey_macro()
        self.risk_free_rate = macro["risk_free_rate"]

    # ─── 1. Z-Score & Sinyaller ──────────────────────────────────────────────

    def calculate_z_score(self, data, window=252):
        return _calculate_z_score(data, window=window)

    def calculate_mean_reversion_signal(self, data, window=252, threshold=Z_SCORE_THRESHOLD):
        return _calculate_mean_reversion_signal(data, window=window, threshold=threshold)

    # ─── 2. Sharpe Ratio ─────────────────────────────────────────────────────

    def calculate_sharpe_ratio(self, data, risk_free_rate=None):
        rf = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        return _calculate_sharpe_ratio(data, risk_free_rate=rf)

    # ─── 3. Korelasyon Matrisi ────────────────────────────────────────────────

    def calculate_correlation_matrix(self, market_data, periods=None):
        return _calculate_correlation_matrix(market_data, periods=periods)

    # ─── 4. Piyasa Stres Endeksi ──────────────────────────────────────────────

    def calculate_market_stress_index(self, correlation_matrices):
        return _calculate_market_stress_index(correlation_matrices)

    # ─── 5. Makro Rejim Filtresi ──────────────────────────────────────────────

    def apply_macro_regime_filter(
        self,
        market_data,
        interest_rate=None,
        inflation_rate=None,
    ):
        return _apply_macro_regime_filter(
            market_data,
            interest_rate=interest_rate,
            inflation_rate=inflation_rate,
        )

    # ─── 6. Fırsat Matrisi ────────────────────────────────────────────────────

    def calculate_relative_strength(self, data1, data2):
        return _calculate_relative_strength(data1, data2)

    def calculate_ratio_signal(self, ratio_data, window=252, threshold=Z_SCORE_THRESHOLD):
        return _calculate_ratio_signal(ratio_data, window=window, threshold=threshold)

    def generate_opportunity_matrix(self, market_data):
        return _generate_opportunity_matrix(market_data)

    # ─── 7. Kantitatif Risk & Simülasyon ──────────────────────────────────────

    def calculate_historical_var(self, returns, confidence_level=0.95):
        return _calculate_historical_var(returns, confidence_level=confidence_level)

    def simulate_monte_carlo_path(self, current_price, expected_return, volatility, days=252, simulations=100):
        return _simulate_monte_carlo_path(
            current_price=current_price,
            expected_return=expected_return,
            volatility=volatility,
            days=days,
            simulations=simulations,
        )

    def calculate_risk_parity_weights(self, covariance_matrix):
        return _calculate_risk_parity_weights(covariance_matrix)

    # ─── 8. Tam Analiz & Portföy Eşleme ───────────────────────────────────────

    def run_full_analysis(self, user_portfolio=None, preferences=None):
        """Tüm kantitatif analizleri çalıştır ve sonuçları döndür."""
        try:
            market_data = self.market_data_service.get_all_market_data()

            if not market_data:
                logger.warning("Piyasa verisi yok — analiz çalıştırılamadı")
                return {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_available': False,
                    'error': 'Piyasa verisi alınamadı (yfinance bağlantısı kontrol edin)',
                }

            # Kullanıcı override'ı çağrı başına çözülür; singleton state'i kirletilmez.
            request_macro = get_dynamic_turkey_macro(preferences)
            effective_risk_free = request_macro['risk_free_rate']

            results = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_available': True,
                'risk_free_rate': effective_risk_free,
                'macro_source': request_macro['source'],
            }

            # 1 — Ortalamaya Dönüş Sinyalleri
            mr_signals = {}
            for ticker, info in market_data.items():
                sig = self.calculate_mean_reversion_signal(info['data'])
                if sig:
                    mr_signals[ticker] = {'name': info['name'], **sig}
            results['mean_reversion'] = mr_signals if mr_signals else None

            # 2 — Sharpe Ratio
            sharpe_ratios = {}
            for ticker, info in market_data.items():
                sr = self.calculate_sharpe_ratio(info['data'], risk_free_rate=effective_risk_free)
                if sr is not None:
                    sharpe_ratios[ticker] = {
                        'name': info['name'],
                        'sharpe_ratio': round(sr, 2),
                    }
            results['sharpe_ratios'] = sharpe_ratios if sharpe_ratios else None

            # 3 — Korelasyon Matrisi
            corr = self.calculate_correlation_matrix(market_data)
            results['correlation_matrices'] = corr

            # 4 — Piyasa Stres Endeksi
            results['market_stress'] = (
                self.calculate_market_stress_index(corr) if corr else None
            )

            # 5 — Makro Rejim Filtresi
            results['macro_regime'] = self.apply_macro_regime_filter(market_data)

            # 6 — Fırsat Matrisi
            results['opportunity_matrix'] = self.generate_opportunity_matrix(market_data)

            # 7 — Portfolio Analysis (if user_portfolio provided)
            if user_portfolio is not None:
                results['portfolio_analysis'] = self._analyze_portfolio(user_portfolio, market_data)

            return results

        except Exception as e:
            logger.error(f"Tam analiz çalıştırma hatası: {e}")
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_available': False,
                'error': str(e),
            }

    def _analyze_portfolio(self, user_portfolio, market_data):
        """Analyze user's portfolio assets against market data."""
        portfolio_analysis = {
            'total_assets': len(user_portfolio),
            'analyzed_assets': 0,
            'assets': {},
        }

        for asset in user_portfolio:
            try:
                symbol = getattr(asset, 'symbol', None)
                unit_price = getattr(asset, 'unit_price', None)
                quantity = getattr(asset, 'quantity', 0)
                name = getattr(asset, 'name', symbol)

                if symbol is None:
                    logger.warning("Asset has no symbol, skipping")
                    continue

                matched_ticker = self._match_symbol_to_market_data(symbol, market_data)

                if matched_ticker is None:
                    logger.warning(f"Asset symbol '{symbol}' could not be matched to market data, skipping")
                    continue

                ticker_data = market_data.get(matched_ticker)
                if ticker_data is None:
                    logger.warning(f"No market data found for ticker '{matched_ticker}', skipping")
                    continue

                price_data = ticker_data['data']
                if price_data is None or price_data.empty:
                    logger.warning(f"Empty price data for ticker '{matched_ticker}', skipping")
                    continue

                asset_analysis = {
                    'name': name,
                    'symbol': symbol,
                    'matched_ticker': matched_ticker,
                    'quantity': quantity,
                    'unit_price': unit_price,
                }

                # 1. Personal Z-Score Signal
                z_score_signal = self.calculate_mean_reversion_signal(price_data)
                if z_score_signal:
                    asset_analysis['z_score_signal'] = {
                        'signal': z_score_signal['signal'],
                        'strength': z_score_signal['strength'],
                        'current_z_score': z_score_signal['current_z_score'],
                        'threshold': z_score_signal['threshold'],
                    }

                # 2. Asset Sharpe Ratio
                sharpe_ratio = self.calculate_sharpe_ratio(price_data)
                if sharpe_ratio is not None:
                    asset_analysis['sharpe_ratio'] = round(sharpe_ratio, 2)

                # 3. Profit/Loss Context (ROI)
                current_price = price_data['price'].iloc[-1]
                if unit_price and unit_price > 0:
                    roi = ((current_price - unit_price) / unit_price) * 100
                    asset_analysis['current_price'] = round(current_price, 2)
                    asset_analysis['roi_percent'] = round(roi, 2)
                    asset_analysis['profit_loss'] = round((current_price - unit_price) * quantity, 2)
                    asset_analysis['total_value'] = round(current_price * quantity, 2)
                else:
                    asset_analysis['current_price'] = round(current_price, 2)
                    asset_analysis['roi_percent'] = None
                    asset_analysis['profit_loss'] = None
                    asset_analysis['total_value'] = None

                portfolio_analysis['assets'][symbol] = asset_analysis
                portfolio_analysis['analyzed_assets'] += 1

            except (AttributeError, KeyError, IndexError) as e:
                logger.error(f"Error analyzing asset: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error analyzing asset: {e}")
                continue

        return portfolio_analysis

    def _match_symbol_to_market_data(self, symbol, market_data):
        """Match Asset.symbol to market data ticker with resilience."""
        if symbol in market_data:
            return symbol

        suffixes = ['.IS', '.TR']
        for suffix in suffixes:
            if (symbol + suffix) in market_data:
                return symbol + suffix

        prefixes = ['-USD', 'USDT']
        for prefix in prefixes:
            if (symbol + prefix) in market_data:
                return symbol + prefix

        symbol_lower = symbol.lower()
        for ticker in market_data.keys():
            if ticker.lower() == symbol_lower or ticker.lower().startswith(symbol_lower):
                return ticker

        return None


# ─── Singleton ────────────────────────────────────────────────────────────────

_analysis_engine_instance = None
_analysis_engine_lock = threading.Lock()


def get_analysis_engine(market_data_service):
    """Thread-safe Singleton accessor for AnalysisEngine."""
    global _analysis_engine_instance
    if _analysis_engine_instance is None:
        with _analysis_engine_lock:
            if _analysis_engine_instance is None:
                _analysis_engine_instance = AnalysisEngine(market_data_service)
    return _analysis_engine_instance


__all__ = [
    'AnalysisEngine',
    'get_analysis_engine',
    'TURKEY_MACRO',
    'REGIME_THRESHOLDS',
    'Z_SCORE_THRESHOLD',
    'CRISIS_CORR_THRESH',
    'STRESS_HIGH_THRESH',
    'STRESS_MED_THRESH',
    'get_dynamic_turkey_macro',
    '_apply_risk_free_override',
]
