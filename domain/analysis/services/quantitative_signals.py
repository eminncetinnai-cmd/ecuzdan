"""Quantitative Signals and Ratios Service.

Provides Z-score mean reversion, Sharpe ratio, and relative strength signal calculations.

Academic references:
- Sharpe (1966): Mutual Fund Performance (Risk-adjusted return)
- Lo & MacKinlay (1988): Stock Market Prices Do Not Follow Random Walks (Mean reversion)
- Gatev, Goetzmann & Rouwenhorst (2006): Pairs Trading (Ratio analysis)
"""
import logging

import numpy as np

logger = logging.getLogger(__name__)

Z_SCORE_THRESHOLD = 2.0  # ±2σ: Standart ortalamaya dönüş eşiği


def calculate_z_score(data, window=252):
    """Z-Score hesapla (Ortalamaya Dönüş Modeli).

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
        rolling_std = prices.rolling(window=window, min_periods=max(1, window // 4)).std()

        # Epsilon clipping to prevent division by zero and infinite values
        epsilon = 1e-6
        rolling_std_clipped = rolling_std.clip(lower=epsilon)

        # Calculate Z-score with protected denominator
        z = (prices - rolling_mean) / rolling_std_clipped

        # If numerator is also zero (price equals mean), set Z-score to 0
        z = z.where((prices - rolling_mean).abs() > epsilon, 0)

        return z
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Z-Score hesaplama hatası (veri yapısı): {e}")
        return None
    except Exception as e:
        logger.error(f"Z-Score hesaplama hatası (beklenmeyen): {e}")
        return None


def calculate_mean_reversion_signal(data, window=252, threshold=Z_SCORE_THRESHOLD):
    """Ortalamaya dönüş sinyali üret.

    Returns:
        dict: signal, strength, current_z_score, threshold
    """
    try:
        z_series = calculate_z_score(data, window)
        if z_series is None or z_series.dropna().empty:
            return None

        current_z = float(z_series.dropna().iloc[-1])

        if current_z > threshold:
            signal = 'SAT'
            strength = min((current_z - threshold) * 10, 100)
        elif current_z < -threshold:
            signal = 'AL'
            strength = min((abs(current_z) - threshold) * 10, 100)
        else:
            signal = 'TUT'
            strength = 0

        return {
            'signal': signal,
            'strength': round(strength, 1),
            'current_z_score': round(current_z, 2),
            'threshold': threshold,
        }
    except Exception as e:
        logger.error(f"Ortalamaya dönüş sinyali hatası: {e}")
        return None


def calculate_sharpe_ratio(data, risk_free_rate=0.50):
    """Yıllıklandırılmış Sharpe Ratio hesapla.

    SR = (R_p − R_f) / σ_p  (yıllıklandırılmış)

    Args:
        data           : DataFrame — 'price' sütunu
        risk_free_rate : Risksiz faiz (varsayılan: 0.50)

    Returns:
        float | None
    """
    try:
        if data is None or data.empty or len(data) < 2:
            return None

        rf = risk_free_rate if risk_free_rate is not None else 0.50

        returns = data['price'].pct_change().dropna()
        if len(returns) < 2:
            return None

        annual_volatility = returns.std() * np.sqrt(252)

        if annual_volatility == 0:
            return 0.0

        # Try geometric mean for academic standard (more accurate for volatile returns)
        try:
            if (returns <= -1).any():
                logger.warning("Returns contain values <= -100%, using arithmetic mean for Sharpe")
                annual_return = returns.mean() * 252
            else:
                geometric_factor = (1 + returns).prod()
                if geometric_factor > 0 and np.isfinite(geometric_factor):
                    annual_return = geometric_factor ** (252 / len(returns)) - 1
                else:
                    logger.warning("Geometric calculation failed, using arithmetic mean for Sharpe")
                    annual_return = returns.mean() * 252
        except (ValueError, TypeError, ZeroDivisionError) as geo_error:
            logger.warning(f"Geometric mean calculation failed ({geo_error}), using arithmetic mean")
            annual_return = returns.mean() * 252

        if not np.isfinite(annual_return):
            logger.warning("Annual return is not finite, using arithmetic mean fallback")
            annual_return = returns.mean() * 252

        sharpe = (annual_return - rf) / annual_volatility

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


def calculate_relative_strength(data1, data2):
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


def calculate_ratio_signal(ratio_data, window=252, threshold=Z_SCORE_THRESHOLD):
    """Rasyo Z-Score sinyali."""
    try:
        if ratio_data is None or len(ratio_data) < 10:
            return None

        med = ratio_data.rolling(window=window, min_periods=10).median()
        std = ratio_data.rolling(window=window, min_periods=10).std()

        cur_ratio = float(ratio_data.iloc[-1])
        cur_median = float(med.iloc[-1])
        cur_std = float(std.iloc[-1])

        if cur_std == 0 or np.isnan(cur_std):
            return {
                'signal': 'TUT',
                'strength': 0,
                'z_score': 0,
                'current_ratio': round(cur_ratio, 4),
                'historical_median': round(cur_median, 4),
            }

        z = (cur_ratio - cur_median) / cur_std

        if z > threshold:
            signal = 'SAT'
            strength = min((z - threshold) * 10, 100)
        elif z < -threshold:
            signal = 'AL'
            strength = min((abs(z) - threshold) * 10, 100)
        else:
            signal = 'TUT'
            strength = 0

        return {
            'signal': signal,
            'strength': round(strength, 1),
            'z_score': round(z, 2),
            'current_ratio': round(cur_ratio, 4),
            'historical_median': round(cur_median, 4),
        }
    except Exception as e:
        logger.error(f"Rasyo sinyali hesaplama hatası: {e}")
        return None
