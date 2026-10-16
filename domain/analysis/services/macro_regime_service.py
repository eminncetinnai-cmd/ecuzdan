"""Macro Regime and Opportunity Matrix Service.

Analyzes macroeconomic regimes (Defensive, Aggressive, Neutral) and cross-asset relative opportunities.
"""
import logging

from domain.analysis.services.quantitative_signals import calculate_ratio_signal, calculate_relative_strength

logger = logging.getLogger(__name__)

# ─── Türkiye Makro Sabitleri (Güncel TCMB / TÜİK verileri) ───────────────────
TURKEY_MACRO = {
    "policy_rate": 0.50,   # TCMB politika faizi (%50) — Haziran 2026 (varsayılan)
    "inflation": 0.45,   # TÜFE yıllık (%45) — Haziran 2026 (varsayılan)
    "real_rate": 0.05,   # Reel faiz = politika − enflasyon (varsayılan)
    "risk_free_rate": 0.50,   # Risksiz getiri olarak politika faizi (varsayılan)
    "source": "TCMB / TÜİK — Haziran 2026 (Hardcoded Fallback)",
}

# ─── Makro Rejim Eşikleri ─────────────────────────────────────────────────────
REGIME_THRESHOLDS = {
    "defansif_rate": 0.20,   # Faiz > %20 → Defansif
    "defansif_inflation": 0.40,   # Enflasyon > %40 → Defansif
    "agresif_rate": 0.10,   # Faiz < %10 → Agresif
    "agresif_inflation": 0.20,   # Enflasyon < %20 → Agresif
}


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


def get_dynamic_turkey_macro(preferences=None):
    """Dinamik Türkiye makro verilerini çeker.

    Varsayılan değerler, piyasa verisi varsa güncel değer kullanılır.

    preferences: UserPreference satırı (opsiyonel). risk_free_rate_mode
    'manual' ise risksiz getiri kullanıcının girdiği oranla değiştirilir;
    enflasyon ve politika faizi piyasa verisinden gelmeye devam eder.
    """
    macro = TURKEY_MACRO
    try:
        from market_data_service import get_macro_economic_data
        try:
            macro_data = get_macro_economic_data(allow_network=False)
        except TypeError:
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


def apply_macro_regime_filter(
    market_data,
    interest_rate=None,
    inflation_rate=None,
):
    """Makro rejim filtresi — faiz + enflasyon kombinasyonuna göre.

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
        ir = interest_rate if interest_rate is not None else macro["policy_rate"]
        inf = inflation_rate if inflation_rate is not None else macro["inflation"]

        thr = REGIME_THRESHOLDS
        if ir > thr["defansif_rate"] or inf > thr["defansif_inflation"]:
            regime = 'DEFANSIF'
            description = 'Yüksek enflasyon/faiz rejimi — Altın, emtia ve sabit getirili araçlar öne çıkar'
            priority_assets = ['GC=F', 'SI=F', 'CL=F']
        elif ir < thr["agresif_rate"] and inf < thr["agresif_inflation"]:
            regime = 'AGRESIF'
            description = 'Düşük faiz/büyüme rejimi — Hisse senetleri ve kripto varlıklar öne çıkar'
            priority_assets = ['^IXIC', 'BTC-USD', 'XU100.IS']
        else:
            regime = 'NÖTR'
            description = 'Dengeli rejim — Çeşitlendirilmiş portföy stratejisi önerilir'
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
                'name': info['name'],
                'score': round(min(max(base, 0), 100), 1),
                'priority': ticker in priority_assets,
            }

        return {
            'regime': regime,
            'description': description,
            'interest_rate': ir,
            'inflation_rate': inf,
            'asset_scores': asset_scores,
        }
    except Exception as e:
        logger.error(f"Makro rejim filtresi hatası: {e}")
        return None


def generate_opportunity_matrix(market_data):
    """Çapraz varlık rasyo fırsat matrisi.

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
            ('GC=F', 'SI=F', 'Altın/Gümüş'),
            ('BTC-USD', '^IXIC', 'Bitcoin/Nasdaq'),
            ('GC=F', 'CL=F', 'Altın/Petrol'),
        ]

        opportunities = []
        for t1, t2, name in pairs:
            if t1 not in market_data or t2 not in market_data:
                continue

            ratio = calculate_relative_strength(
                market_data[t1]['data'],
                market_data[t2]['data'],
            )
            if ratio is None:
                continue

            sig = calculate_ratio_signal(ratio)
            if sig:
                opportunities.append({
                    'ratio_name': name,
                    'ticker1': t1,
                    'ticker2': t2,
                    'signal': sig['signal'],
                    'strength': sig['strength'],
                    'z_score': sig['z_score'],
                    'current_ratio': sig.get('current_ratio', 0),
                })

        return opportunities if opportunities else None
    except Exception as e:
        logger.error(f"Fırsat matrisi oluşturma hatası: {e}")
        return None
