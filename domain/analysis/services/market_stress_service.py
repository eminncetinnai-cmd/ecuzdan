"""Market Stress and Multi-Period Correlation Service.

Calculates rolling correlation matrices and correlation-based market stress indices.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CRISIS_CORR_THRESH = 0.90  # Korelasyon > 0.9 → Kriz modu
STRESS_HIGH_THRESH = 70    # Stres endeksi > 70 → Yüksek stres
STRESS_MED_THRESH = 40     # Stres endeksi > 40 → Orta stres


def calculate_correlation_matrix(market_data, periods=None):
    """Çoklu periyot korelasyon matrisi hesapla.

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
                'matrix': corr.round(4).to_dict(),
                'max_correlation': round(max_corr, 4),
                'crisis_mode': max_corr > CRISIS_CORR_THRESH,
            }

        return result if result else None
    except Exception as e:
        logger.error(f"Korelasyon matrisi hesaplama hatası: {e}")
        return None


def calculate_market_stress_index(correlation_matrices):
    """Korelasyon bazlı piyasa stres endeksi (0–100).

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
                'crisis_mode': False,
                'stress_level': 'DÜŞÜK',
            }

        avg = float(np.mean(scores))

        # Final validation of average stress index
        if not np.isfinite(avg):
            logger.warning(f"Average stress index is not finite ({avg}), defaulting to 0")
            avg = 0.0

        return {
            'stress_index': round(avg, 1),
            'crisis_mode': avg > STRESS_HIGH_THRESH,
            'stress_level': (
                'YÜKSEK' if avg > STRESS_HIGH_THRESH else
                'ORTA' if avg > STRESS_MED_THRESH else
                'DÜŞÜK'
            ),
        }
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Piyasa stres endeksi hesaplama hatası (veri yapısı): {e}")
        return None
    except Exception as e:
        logger.error(f"Piyasa stres endeksi hesaplama hatası (beklenmeyen): {e}")
        return None
