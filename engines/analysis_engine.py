"""
Analysis Engine — Finansal Strateji ve Analiz Motoru
Kantitatif Piyasa Analizi ve Risk Yönetimi

Akademik Referanslar:
- Sharpe (1966): Riske ayarlı getiri ölçümü
- Markowitz (1952): Modern Portföy Teorisi, korelasyon ve çeşitlendirme
- Lo & MacKinlay (1988): Ortalamaya dönüş (mean reversion) modeli
- Gatev, Goetzmann & Rouwenhorst (2006): Pairs trading / rasyo analizi
- Fama (1970): Etkin piyasalar hipotezi
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Türkiye Makro Sabitleri (Güncel TCMB / TÜİK verileri) ───────────────────
TURKEY_MACRO = {
    "policy_rate":    0.50,   # TCMB politika faizi (%50) — Haziran 2026 (varsayılan)
    "inflation":      0.45,   # TÜFE yıllık (%45) — Haziran 2026 (varsayılan)
    "real_rate":      0.05,   # Reel faiz = politika − enflasyon (varsayılan)
    "risk_free_rate": 0.50,   # Risksiz getiri olarak politika faizi (varsayılan)
    "source":         "TCMB / TÜİK — Haziran 2026 (Hardcoded Fallback)",
}


def get_dynamic_turkey_macro(preferences=None):
    """
    Dinamik Türkiye makro verilerini çeker
    Varsayılan değerler, piyasa verisi varsa güncel değer kullanılır

    preferences: UserPreference satırı (opsiyonel). risk_free_rate_mode
    'manual' ise risksiz getiri kullanıcının girdiği oranla değiştirilir;
    enflasyon ve politika faizi piyasa verisinden gelmeye devam eder.
    """
    macro = TURKEY_MACRO
    try:
        from market_data_service import get_macro_economic_data
        macro_data = get_macro_economic_data()
        if macro_data and 'inflation_rate' in macro_data:
            inflation = macro_data['inflation_rate'] / 100
            interest = macro_data['interest_rate'] / 100
            real = max(0.0, interest - inflation)
            macro = {
                "policy_rate": interest,
                "inflation": inflation,
                "real_rate": real,
                "risk_free_rate": interest,
                "source": macro_data.get('source', 'dynamic'),
            }
    except Exception as e:
        logger.warning(f"Dynamic macro data fetch failed, using default: {e}")

    return _apply_risk_free_override(macro, preferences)


def _apply_risk_free_override(macro, preferences):
    """Kullanıcı manuel risksiz faiz girdiyse makro sözlüğünü kopyalayıp değiştirir."""
    if preferences is None or getattr(preferences, 'risk_free_rate_mode', 'auto') != 'manual':
        return macro
    manual = getattr(preferences, 'risk_free_rate_manual', None)
    if manual is None:
        return macro
    overridden = dict(macro)
    overridden['risk_free_rate'] = float(manual)
    overridden['real_rate'] = max(0.0, float(manual) - overridden.get('inflation', 0.0))
    overridden['source'] = f"{macro.get('source', 'dynamic')} + kullanıcı override"
    return overridden

# ─── Makro Rejim Eşikleri ─────────────────────────────────────────────────────
REGIME_THRESHOLDS = {
    "defansif_rate":      0.20,   # Faiz > %20 → Defansif
    "defansif_inflation": 0.40,   # Enflasyon > %40 → Defansif
    "agresif_rate":       0.10,   # Faiz < %10 → Agresif
    "agresif_inflation":  0.20,   # Enflasyon < %20 → Agresif
}

# ─── Sinyal Eşikleri ─────────────────────────────────────────────────────────
Z_SCORE_THRESHOLD   = 2.0   # ±2σ: Standart ortalamaya dönüş eşiği
CRISIS_CORR_THRESH  = 0.90  # Korelasyon > 0.9 → Kriz modu
STRESS_HIGH_THRESH  = 70    # Stres endeksi > 70 → Yüksek stres
STRESS_MED_THRESH   = 40    # Stres endeksi > 40 → Orta stres


class AnalysisEngine:
    """
    Kantitatif Finansal Analiz Motoru.

    Desteklenen Analizler:
    1. Z-Score tabanlı ortalamaya dönüş sinyalleri
    2. Sharpe Ratio (riske ayarlı getiri)
    3. Korelasyon matrisi (çeşitlendirme analizi)
    4. Piyasa stres endeksi (korelasyon bazlı)
    5. Makro rejim filtresi (faiz + enflasyon)
    6. Fırsat matrisi (çapraz varlık rasyo analizi)
    """

    def __init__(self, market_data_service):
        self.market_data_service = market_data_service
        macro = get_dynamic_turkey_macro()
        self.risk_free_rate = macro["risk_free_rate"]

    # ─── 1. Z-Score ──────────────────────────────────────────────────────────

    def calculate_z_score(self, data, window=252):
        """
        Z-Score hesapla (Ortalamaya Dönüş Modeli).

        Z = (P_t − μ_rolling) / σ_rolling

        Args:
            data   : DataFrame — 'price' sütunu
            window : Hareketli pencere (varsayılan 252 = 1 yıl iş günü)

        Returns:
            pd.Series | None
        """
        try:
            if data is None or data.empty:
                return None
            prices = data['price']
            rolling_mean = prices.rolling(window=window, min_periods=max(1, window // 4)).mean()
            rolling_std  = prices.rolling(window=window, min_periods=max(1, window // 4)).std()

            # Epsilon clipping to prevent division by zero and infinite values
            # When std is 0 (constant prices), clip to minimum epsilon to avoid inf
            epsilon = 1e-6
            rolling_std_clipped = rolling_std.clip(lower=epsilon)

            # Calculate Z-score with protected denominator
            z = (prices - rolling_mean) / rolling_std_clipped

            # If numerator is also zero (price equals mean), set Z-score to 0
            # This handles the case where both price and mean are equal
            z = z.where((prices - rolling_mean).abs() > epsilon, 0)

            return z
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Z-Score hesaplama hatası (veri yapısı): {e}")
            return None
        except Exception as e:
            logger.error(f"Z-Score hesaplama hatası (beklenmeyen): {e}")
            return None

    def calculate_mean_reversion_signal(self, data, window=252, threshold=Z_SCORE_THRESHOLD):
        """
        Ortalamaya dönüş sinyali üret.

        Returns:
            dict: signal, strength, current_z_score, threshold
        """
        try:
            z_series = self.calculate_z_score(data, window)
            if z_series is None or z_series.dropna().empty:
                return None

            current_z = float(z_series.dropna().iloc[-1])

            if current_z > threshold:
                signal   = 'SAT'
                strength = min((current_z - threshold) * 10, 100)
            elif current_z < -threshold:
                signal   = 'AL'
                strength = min((abs(current_z) - threshold) * 10, 100)
            else:
                signal   = 'TUT'
                strength = 0

            return {
                'signal':          signal,
                'strength':        round(strength, 1),
                'current_z_score': round(current_z, 2),
                'threshold':       threshold,
            }
        except Exception as e:
            logger.error(f"Ortalamaya dönüş sinyali hatası: {e}")
            return None

    # ─── 2. Sharpe Ratio ─────────────────────────────────────────────────────

    def calculate_sharpe_ratio(self, data, risk_free_rate=None):
        """
        Yıllıklandırılmış Sharpe Ratio hesapla.

        SR = (R_p − R_f) / σ_p  (yıllıklandırılmış)

        Args:
            data           : DataFrame — 'price' sütunu
            risk_free_rate : Risksiz faiz (varsayılan: TCMB politika faizi)

        Returns:
            float | None
        """
        try:
            if data is None or data.empty or len(data) < 2:
                return None

            rf = risk_free_rate if risk_free_rate is not None else self.risk_free_rate

            returns = data['price'].pct_change().dropna()
            if len(returns) < 2:
                return None

            annual_volatility = returns.std() * np.sqrt(252)

            if annual_volatility == 0:
                return 0.0

            # Try geometric mean for academic standard (more accurate for volatile returns)
            try:
                # Geometric annual return: (1 + r).prod()^(252/n) - 1
                # Check for negative prices or returns that could cause issues
                if (returns <= -1).any():
                    # Returns <= -100% would cause geometric calculation to fail
                    # Fallback to arithmetic mean
                    logger.warning("Returns contain values <= -100%, using arithmetic mean for Sharpe")
                    annual_return = returns.mean() * 252
                else:
                    geometric_factor = (1 + returns).prod()
                    # Ensure geometric_factor is positive and finite
                    if geometric_factor > 0 and np.isfinite(geometric_factor):
                        annual_return = geometric_factor ** (252 / len(returns)) - 1
                    else:
                        # Fallback to arithmetic if geometric calculation fails
                        logger.warning("Geometric calculation failed, using arithmetic mean for Sharpe")
                        annual_return = returns.mean() * 252
            except (ValueError, TypeError, ZeroDivisionError) as geo_error:
                # Fallback to arithmetic mean if geometric calculation raises any exception
                logger.warning(f"Geometric mean calculation failed ({geo_error}), using arithmetic mean")
                annual_return = returns.mean() * 252

            # Validate annual_return is finite
            if not np.isfinite(annual_return):
                logger.warning("Annual return is not finite, using arithmetic mean fallback")
                annual_return = returns.mean() * 252

            sharpe = (annual_return - rf) / annual_volatility

            # Validate final Sharpe ratio is finite
            if not np.isfinite(sharpe):
                logger.warning("Sharpe ratio is not finite, returning 0")
                return 0.0

            return float(sharpe)
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Sharpe Ratio hesaplama hatası (veri yapısı): {e}")
            return None
        except Exception as e:
            logger.error(f"Sharpe Ratio hesaplama hatası (beklenmeyen): {e}")
            return None

    # ─── 3. Korelasyon Matrisi ────────────────────────────────────────────────

    def calculate_correlation_matrix(self, market_data, periods=None):
        """
        Çoklu periyot korelasyon matrisi hesapla.

        Args:
            market_data : dict — get_all_market_data() çıktısı
            periods     : list[int] — gün sayıları (varsayılan: [30, 90, 180])

        Returns:
            dict: {period: {matrix, max_correlation, crisis_mode}}
        """
        if periods is None:
            periods = [30, 90, 180]
        try:
            if not market_data:
                return None

            result = {}
            for period in periods:
                price_data = {}
                for ticker, info in market_data.items():
                    d = info.get('data')
                    if d is not None and len(d) >= period:
                        price_data[ticker] = d['price'].iloc[-period:]

                if len(price_data) < 2:
                    continue

                df = pd.DataFrame(price_data)
                corr = df.corr()

                upper = corr.values[np.triu_indices_from(corr.values, k=1)]
                max_corr = float(upper.max()) if len(upper) > 0 else 0.0

                result[period] = {
                    'matrix':          corr.round(4).to_dict(),
                    'max_correlation': round(max_corr, 4),
                    'crisis_mode':     max_corr > CRISIS_CORR_THRESH,
                }

            return result if result else None
        except Exception as e:
            logger.error(f"Korelasyon matrisi hesaplama hatası: {e}")
            return None

    # ─── 4. Piyasa Stres Endeksi ──────────────────────────────────────────────

    def calculate_market_stress_index(self, correlation_matrices):
        """
        Korelasyon bazlı piyasa stres endeksi (0–100).

        Stres = max(0, (ρ_max − 0.5) × 200)

        Args:
            correlation_matrices : dict — calculate_correlation_matrix() çıktısı

        Returns:
            dict: {stress_index, crisis_mode, stress_level}
        """
        try:
            if not correlation_matrices:
                return None

            scores = []
            for period_data in correlation_matrices.values():
                try:
                    mc = period_data.get('max_correlation', 0)

                    # Validate max_correlation is finite and within valid range
                    if not np.isfinite(mc):
                        logger.warning(f"Invalid max_correlation ({mc}) in period data, skipping")
                        continue

                    # Clip correlation to valid range [-1, 1] to prevent calculation errors
                    mc_clipped = np.clip(mc, -1.0, 1.0)

                    # Calculate stress score
                    stress_score = max(0.0, (mc_clipped - 0.5) * 200)

                    # Validate stress score is finite
                    if np.isfinite(stress_score):
                        scores.append(stress_score)
                    else:
                        logger.warning(f"Invalid stress score ({stress_score}) from correlation {mc_clipped}, skipping")
                except (ValueError, KeyError, TypeError) as period_error:
                    logger.warning(f"Error processing period data (veri yapısı): {period_error}, skipping")
                    continue
                except Exception as period_error:
                    logger.warning(f"Error processing period data (beklenmeyen): {period_error}, skipping")
                    continue

            if not scores:
                logger.warning("No valid stress scores calculated, returning neutral stress")
                return {
                    'stress_index': 0.0,
                    'crisis_mode':  False,
                    'stress_level': 'DÜŞÜK',
                }

            avg = float(np.mean(scores))

            # Final validation of average stress index
            if not np.isfinite(avg):
                logger.warning(f"Average stress index is not finite ({avg}), defaulting to 0")
                avg = 0.0

            return {
                'stress_index': round(avg, 1),
                'crisis_mode':  avg > STRESS_HIGH_THRESH,
                'stress_level': (
                    'YÜKSEK' if avg > STRESS_HIGH_THRESH else
                    'ORTA'   if avg > STRESS_MED_THRESH  else
                    'DÜŞÜK'
                ),
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Piyasa stres endeksi hesaplama hatası (veri yapısı): {e}")
            return None
        except Exception as e:
            logger.error(f"Piyasa stres endeksi hesaplama hatası (beklenmeyen): {e}")
            return None

    # ─── 5. Makro Rejim Filtresi ──────────────────────────────────────────────

    def apply_macro_regime_filter(
        self,
        market_data,
        interest_rate=None,
        inflation_rate=None,
    ):
        """
        Makro rejim filtresi — faiz + enflasyon kombinasyonuna göre.

        Rejimler:
        - DEFANSIF : Yüksek faiz/enflasyon → Altın, emtia öncelikli
        - AGRESIF  : Düşük faiz/enflasyon  → Hisse, kripto öncelikli
        - NÖTR     : Dengeli ortam          → Çeşitlendirilmiş portföy

        Args:
            market_data   : dict — get_all_market_data() çıktısı
            interest_rate : float (varsayılan: TCMB politika faizi)
            inflation_rate: float (varsayılan: TÜİK TÜFE)

        Returns:
            dict: {regime, description, interest_rate, inflation_rate, asset_scores}
        """
        try:
            if not market_data:
                return None

            macro = get_dynamic_turkey_macro()
            ir  = interest_rate  if interest_rate  is not None else macro["policy_rate"]
            inf = inflation_rate if inflation_rate is not None else macro["inflation"]

            thr = REGIME_THRESHOLDS
            if ir > thr["defansif_rate"] or inf > thr["defansif_inflation"]:
                regime          = 'DEFANSIF'
                description     = 'Yüksek enflasyon/faiz rejimi — Altın, emtia ve sabit getirili araçlar öne çıkar'
                priority_assets = ['GC=F', 'SI=F', 'CL=F']
            elif ir < thr["agresif_rate"] and inf < thr["agresif_inflation"]:
                regime          = 'AGRESIF'
                description     = 'Düşük faiz/büyüme rejimi — Hisse senetleri ve kripto varlıklar öne çıkar'
                priority_assets = ['^IXIC', 'BTC-USD', 'XU100.IS']
            else:
                regime          = 'NÖTR'
                description     = 'Dengeli rejim — Çeşitlendirilmiş portföy stratejisi önerilir'
                priority_assets = ['XU100.IS', 'GC=F', 'CL=F']

            asset_scores = {}
            for ticker, info in market_data.items():
                d = info.get('data')
                base = 50
                if ticker in priority_assets:
                    base += 30

                if d is not None and not d.empty:
                    returns = d['price'].pct_change().dropna()
                    if len(returns) > 0:
                        vol = float(returns.std())
                        if regime == 'DEFANSIF':
                            base -= vol * 800   # Düşük volatilite tercih
                        else:
                            base += vol * 400   # Yüksek volatilite kabul

                asset_scores[ticker] = {
                    'name':     info['name'],
                    'score':    round(min(max(base, 0), 100), 1),
                    'priority': ticker in priority_assets,
                }

            return {
                'regime':        regime,
                'description':   description,
                'interest_rate': ir,
                'inflation_rate': inf,
                'asset_scores':  asset_scores,
            }
        except Exception as e:
            logger.error(f"Makro rejim filtresi hatası: {e}")
            return None

    # ─── 6. Fırsat Matrisi ────────────────────────────────────────────────────

    def calculate_relative_strength(self, data1, data2):
        """İki varlık arası fiyat rasyosu."""
        try:
            if data1 is None or data2 is None:
                return None
            if data1.empty or data2.empty:
                return None
            ratio = data1['price'] / data2['price']
            return ratio.dropna()
        except Exception as e:
            logger.error(f"Göreceli güç hesaplama hatası: {e}")
            return None

    def calculate_ratio_signal(self, ratio_data, window=252, threshold=Z_SCORE_THRESHOLD):
        """Rasyo Z-Score sinyali."""
        try:
            if ratio_data is None or len(ratio_data) < 10:
                return None

            med = ratio_data.rolling(window=window, min_periods=10).median()
            std = ratio_data.rolling(window=window, min_periods=10).std()

            cur_ratio  = float(ratio_data.iloc[-1])
            cur_median = float(med.iloc[-1])
            cur_std    = float(std.iloc[-1])

            if cur_std == 0 or np.isnan(cur_std):
                return {'signal': 'TUT', 'strength': 0, 'z_score': 0,
                        'current_ratio': round(cur_ratio, 4),
                        'historical_median': round(cur_median, 4)}

            z = (cur_ratio - cur_median) / cur_std

            if z > threshold:
                signal   = 'SAT'
                strength = min((z - threshold) * 10, 100)
            elif z < -threshold:
                signal   = 'AL'
                strength = min((abs(z) - threshold) * 10, 100)
            else:
                signal   = 'TUT'
                strength = 0

            return {
                'signal':             signal,
                'strength':           round(strength, 1),
                'z_score':            round(z, 2),
                'current_ratio':      round(cur_ratio, 4),
                'historical_median':  round(cur_median, 4),
            }
        except Exception as e:
            logger.error(f"Rasyo sinyali hesaplama hatası: {e}")
            return None

    def generate_opportunity_matrix(self, market_data):
        """
        Çapraz varlık rasyo fırsat matrisi.

        Analiz edilen çiftler:
        - Altın / Gümüş  (GSR — Gold/Silver Ratio)
        - Bitcoin / Nasdaq (Kripto/Hisse ilişkisi)
        - Altın / Petrol  (Emtia dengesi)

        Returns:
            list[dict]
        """
        try:
            if not market_data:
                return None

            pairs = [
                ('GC=F',    'SI=F',   'Altın/Gümüş'),
                ('BTC-USD', '^IXIC',  'Bitcoin/Nasdaq'),
                ('GC=F',    'CL=F',   'Altın/Petrol'),
            ]

            opportunities = []
            for t1, t2, name in pairs:
                if t1 not in market_data or t2 not in market_data:
                    continue

                ratio = self.calculate_relative_strength(
                    market_data[t1]['data'],
                    market_data[t2]['data'],
                )
                if ratio is None:
                    continue

                sig = self.calculate_ratio_signal(ratio)
                if sig:
                    opportunities.append({
                        'ratio_name':    name,
                        'ticker1':       t1,
                        'ticker2':       t2,
                        'signal':        sig['signal'],
                        'strength':      sig['strength'],
                        'z_score':       sig['z_score'],
                        'current_ratio': sig.get('current_ratio', 0),
                    })

            return opportunities if opportunities else None
        except Exception as e:
            logger.error(f"Fırsat matrisi oluşturma hatası: {e}")
            return None

    # ─── 7. Tam Analiz ───────────────────────────────────────────────────────

    def run_full_analysis(self, user_portfolio=None, preferences=None):
        """
        Tüm kantitatif analizleri çalıştır ve sonuçları döndür.

        Args:
            user_portfolio: Optional list of Asset objects for personalized portfolio analysis
            preferences: UserPreference satırı (opsiyonel). Risksiz faiz oranı
                buradan çözülür ve Sharpe hesabına çağrı başına geçilir —
                motor singleton olduğu için ASLA self üzerine yazılmaz.

        Returns:
            dict: {
                timestamp, data_available, risk_free_rate,
                mean_reversion, sharpe_ratios, correlation_matrices,
                market_stress, macro_regime, opportunity_matrix,
                portfolio_analysis (if user_portfolio provided)
            }
        """
        try:
            market_data = self.market_data_service.get_all_market_data()

            if not market_data:
                logger.warning("Piyasa verisi yok — analiz çalıştırılamadı")
                return {
                    'timestamp':      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_available': False,
                    'error':          'Piyasa verisi alınamadı (yfinance bağlantısı kontrol edin)',
                }

            # Kullanıcı override'ı çağrı başına çözülür; singleton state'i kirletilmez.
            request_macro = get_dynamic_turkey_macro(preferences)
            effective_risk_free = request_macro['risk_free_rate']

            results = {
                'timestamp':      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_available': True,
                'risk_free_rate': effective_risk_free,
                'macro_source':   request_macro['source'],
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
                        'name':         info['name'],
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
                'timestamp':      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_available': False,
                'error':          str(e),
            }

    def _analyze_portfolio(self, user_portfolio, market_data):
        """
        Analyze user's portfolio assets against market data.

        Args:
            user_portfolio: List of Asset objects
            market_data: Market data dictionary from get_all_market_data()

        Returns:
            dict: Portfolio analysis with personalized metrics
        """
        portfolio_analysis = {
            'total_assets': len(user_portfolio),
            'analyzed_assets': 0,
            'assets': {}
        }

        for asset in user_portfolio:
            try:
                # Safe attribute access (avoid DetachedInstanceError)
                symbol = getattr(asset, 'symbol', None)
                unit_price = getattr(asset, 'unit_price', None)
                quantity = getattr(asset, 'quantity', 0)
                name = getattr(asset, 'name', symbol)

                if symbol is None:
                    logger.warning("Asset has no symbol, skipping")
                    continue

                # Symbol mapping resilience: try to match with market data
                matched_ticker = self._match_symbol_to_market_data(symbol, market_data)

                if matched_ticker is None:
                    logger.warning(f"Asset symbol '{symbol}' could not be matched to market data, skipping")
                    continue

                # Get market data for matched ticker
                ticker_data = market_data.get(matched_ticker)
                if ticker_data is None:
                    logger.warning(f"No market data found for ticker '{matched_ticker}', skipping")
                    continue

                price_data = ticker_data['data']
                if price_data is None or price_data.empty:
                    logger.warning(f"Empty price data for ticker '{matched_ticker}', skipping")
                    continue

                # Calculate personalized metrics
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
        """
        Match Asset.symbol to market data ticker with resilience.

        Args:
            symbol: Asset.symbol (e.g., 'GARAN', 'BTC')
            market_data: Market data dictionary

        Returns:
            str: Matched ticker or None if no match found
        """
        # Direct match
        if symbol in market_data:
            return symbol

        # Try common suffixes
        suffixes = ['.IS', '.TR']
        for suffix in suffixes:
            if (symbol + suffix) in market_data:
                return symbol + suffix

        # Try prefix (e.g., 'BTC' -> 'BTC-USD')
        prefixes = ['-USD', 'USDT']
        for prefix in prefixes:
            if (symbol + prefix) in market_data:
                return symbol + prefix

        # Try case-insensitive match
        symbol_lower = symbol.lower()
        for ticker in market_data.keys():
            if ticker.lower() == symbol_lower or ticker.lower().startswith(symbol_lower):
                return ticker

        # No match found
        return None


    # ─── 8. Quantitative Feature Backlog (Micro-Functions) ─────────────────────

    def calculate_historical_var(self, returns, confidence_level=0.95):
        """
        Calculate Value at Risk (VaR) using the historical simulation method.

        VaR estimates the maximum potential loss with a given confidence level
        over a specified time horizon based on historical return distribution.

        Args:
            returns: pandas Series or numpy array of historical returns (decimal, not percentage)
            confidence_level: Confidence level for VaR (default: 0.95 for 95% VaR)

        Returns:
            float: VaR as a negative percentage (e.g., -0.05 for -5% VaR)
                   None if insufficient data
        """
        try:
            import numpy as np

            # Convert to numpy array if needed
            if hasattr(returns, 'values'):
                returns = returns.values

            returns = np.array(returns)

            # Validate input
            if len(returns) < 10:
                logger.warning("Insufficient data for VaR calculation (need at least 10 data points)")
                return None

            # Remove NaN values
            returns = returns[~np.isnan(returns)]

            if len(returns) < 10:
                logger.warning("Insufficient valid data for VaR calculation after NaN removal")
                return None

            # Calculate VaR using historical simulation method
            # VaR is the quantile of the return distribution at (1 - confidence_level)
            var = np.percentile(returns, (1 - confidence_level) * 100)

            logger.info(f"Historical VaR ({confidence_level*100}%): {var:.4f}")
            return var

        except Exception as e:
            logger.error(f"Historical VaR calculation error: {e}")
            return None

    def simulate_monte_carlo_path(self, current_price, expected_return, volatility, days=252, simulations=100):
        """
        Generate Monte Carlo simulation for an asset's future price paths based on Geometric Brownian Motion.

        Uses the standard GBM model: dS = μSdt + σSdW
        Where: μ = expected return, σ = volatility, dW = Wiener process

        Args:
            current_price: Current asset price (float)
            expected_return: Expected annual return (decimal, e.g., 0.10 for 10%)
            volatility: Annual volatility (decimal, e.g., 0.20 for 20%)
            days: Number of days to simulate (default: 252 trading days)
            simulations: Number of simulation paths (default: 100)

        Returns:
            dict: {
                'paths': numpy array of shape (simulations, days) with price paths,
                'final_prices': numpy array of final prices for each simulation,
                'mean_final_price': mean of final prices,
                'median_final_price': median of final prices,
                'percentiles': dict with 5th, 25th, 50th, 75th, 95th percentiles
            }
            None if invalid input
        """
        try:
            import numpy as np

            # Validate input
            if current_price <= 0:
                logger.warning("Current price must be positive")
                return None

            if volatility < 0:
                logger.warning("Volatility cannot be negative")
                return None

            if days <= 0 or simulations <= 0:
                logger.warning("Days and simulations must be positive")
                return None

            # Convert annual parameters to daily
            dt = 1 / 252  # Daily time step (assuming 252 trading days per year)
            daily_return = expected_return * dt
            daily_volatility = volatility * np.sqrt(dt)

            # Initialize price paths array
            paths = np.zeros((simulations, days))
            paths[:, 0] = current_price

            # Generate random shocks (Wiener process)
            random_shocks = np.random.standard_normal((simulations, days - 1))

            # Simulate price paths using GBM
            for t in range(1, days):
                # GBM formula: S(t) = S(t-1) * exp((μ - 0.5σ²)dt + σ√dt * Z)
                paths[:, t] = paths[:, t-1] * np.exp(
                    (daily_return - 0.5 * daily_volatility**2) * dt +
                    daily_volatility * random_shocks[:, t-1]
                )

            # Calculate statistics
            final_prices = paths[:, -1]
            mean_final_price = np.mean(final_prices)
            median_final_price = np.median(final_prices)

            percentiles = {
                'p5': np.percentile(final_prices, 5),
                'p25': np.percentile(final_prices, 25),
                'p50': np.percentile(final_prices, 50),
                'p75': np.percentile(final_prices, 75),
                'p95': np.percentile(final_prices, 95)
            }

            logger.info(f"Monte Carlo simulation completed: {simulations} paths over {days} days")
            logger.info(f"Mean final price: {mean_final_price:.2f}, Median: {median_final_price:.2f}")

            return {
                'paths': paths,
                'final_prices': final_prices,
                'mean_final_price': mean_final_price,
                'median_final_price': median_final_price,
                'percentiles': percentiles
            }

        except Exception as e:
            logger.error(f"Monte Carlo simulation error: {e}")
            return None

    def calculate_risk_parity_weights(self, covariance_matrix):
        """
        Calculate inverse-volatility weights as a simplified step towards full Risk Parity / Markowitz optimization.

        Risk Parity aims to allocate capital such that each asset contributes equally to portfolio risk.
        This simplified version uses inverse volatility weighting, which is a common approximation.

        Args:
            covariance_matrix: pandas DataFrame or numpy array of asset returns covariance matrix

        Returns:
            dict: {
                'weights': dict of {asset: weight} for each asset,
                'volatilities': dict of {asset: volatility} for each asset,
                'inverse_volatilities': dict of {asset: inverse_volatility} for each asset
            }
            None if invalid input
        """
        try:
            import numpy as np
            import pandas as pd

            # Convert to DataFrame if needed
            if not isinstance(covariance_matrix, pd.DataFrame):
                if isinstance(covariance_matrix, np.ndarray):
                    covariance_matrix = pd.DataFrame(covariance_matrix)
                else:
                    logger.warning("Covariance matrix must be numpy array or pandas DataFrame")
                    return None

            # Validate input
            if covariance_matrix.empty:
                logger.warning("Covariance matrix is empty")
                return None

            # Extract volatilities (standard deviations) from diagonal
            volatilities = np.sqrt(np.diag(covariance_matrix))

            # Handle zero or negative volatilities
            volatilities[volatilities <= 0] = 1e-10  # Avoid division by zero

            # Calculate inverse volatilities
            inverse_volatilities = 1.0 / volatilities

            # Normalize to get weights (sum to 1)
            weights = inverse_volatilities / np.sum(inverse_volatilities)

            # Get asset names
            asset_names = covariance_matrix.index.tolist()

            # Create result dictionaries
            weights_dict = {asset_names[i]: float(weights[i]) for i in range(len(asset_names))}
            volatilities_dict = {asset_names[i]: float(volatilities[i]) for i in range(len(asset_names))}
            inverse_volatilities_dict = {asset_names[i]: float(inverse_volatilities[i]) for i in range(len(asset_names))}

            logger.info(f"Risk parity weights calculated for {len(asset_names)} assets")
            logger.info(f"Weights: {weights_dict}")

            return {
                'weights': weights_dict,
                'volatilities': volatilities_dict,
                'inverse_volatilities': inverse_volatilities_dict
            }

        except Exception as e:
            logger.error(f"Risk parity weights calculation error: {e}")
            return None


# ─── Singleton ────────────────────────────────────────────────────────────────
import threading

_analysis_engine_instance = None
_analysis_engine_lock = threading.Lock()


def get_analysis_engine(market_data_service):
    """
    Thread-safe Singleton accessor for AnalysisEngine.

    Uses double-checked locking pattern for thread safety with minimal performance impact.

    Args:
        market_data_service: MarketDataService instance

    Returns:
        AnalysisEngine: Singleton instance
    """
    global _analysis_engine_instance
    if _analysis_engine_instance is None:
        with _analysis_engine_lock:
            # Double-check inside lock to prevent race condition
            if _analysis_engine_instance is None:
                _analysis_engine_instance = AnalysisEngine(market_data_service)
    return _analysis_engine_instance
