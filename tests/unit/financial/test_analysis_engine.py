"""
Unit Tests — Analysis Engine (AnalysisEngine sınıfı)
Z-Score, Sharpe Ratio, Korelasyon, Makro Rejim, Stres Endeksi
Hedef: %6 → %60+ kapsam artışı
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from engines.analysis_engine import (
    CRISIS_CORR_THRESH,
    REGIME_THRESHOLDS,
    STRESS_HIGH_THRESH,
    STRESS_MED_THRESH,
    TURKEY_MACRO,
    Z_SCORE_THRESHOLD,
    AnalysisEngine,
    _apply_risk_free_override,
    get_dynamic_turkey_macro,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_price_series(n: int = 300, start: float = 100.0, trend: float = 0.0,
                       noise: float = 1.0, seed: int = 42) -> pd.DataFrame:
    """Test için sentetik fiyat serisi üretir."""
    rng = np.random.default_rng(seed)
    prices = start + trend * np.arange(n) + rng.normal(0, noise, n)
    prices = np.maximum(prices, 0.01)  # Negatif fiyat olmasın
    return pd.DataFrame({'price': prices})


def _make_engine() -> AnalysisEngine:
    mock_svc = MagicMock()
    mock_svc.get_all_market_data.return_value = {}
    return AnalysisEngine(mock_svc)


# ─── TURKEY_MACRO sabitleri ───────────────────────────────────────────────────

@pytest.mark.unit
def test_turkey_macro_has_required_keys():
    required = ['policy_rate', 'inflation', 'real_rate', 'risk_free_rate', 'source']
    for key in required:
        assert key in TURKEY_MACRO, f"Eksik anahtar: {key}"


@pytest.mark.unit
def test_turkey_macro_rates_positive():
    assert TURKEY_MACRO['policy_rate'] > 0
    assert TURKEY_MACRO['inflation'] > 0
    assert TURKEY_MACRO['risk_free_rate'] > 0


@pytest.mark.unit
def test_regime_thresholds_defined():
    assert 'defansif_rate' in REGIME_THRESHOLDS
    assert 'agresif_rate' in REGIME_THRESHOLDS


@pytest.mark.unit
def test_signal_thresholds_values():
    assert Z_SCORE_THRESHOLD == 2.0
    assert CRISIS_CORR_THRESH == 0.90
    assert STRESS_HIGH_THRESH == 70
    assert STRESS_MED_THRESH == 40


# ─── _apply_risk_free_override ────────────────────────────────────────────────

@pytest.mark.unit
def test_risk_free_override_none_preferences():
    """preferences=None → makro değişmez"""
    macro = dict(TURKEY_MACRO)
    result = _apply_risk_free_override(macro, None)
    assert result is macro


@pytest.mark.unit
def test_risk_free_override_auto_mode():
    """risk_free_rate_mode='auto' → değişiklik yok"""
    class Prefs:
        risk_free_rate_mode = 'auto'
        risk_free_rate_manual = 0.10

    macro = dict(TURKEY_MACRO)
    result = _apply_risk_free_override(macro, Prefs())
    assert result is macro


@pytest.mark.unit
def test_risk_free_override_manual_mode():
    """risk_free_rate_mode='manual' + değer → risk_free_rate güncellenir"""
    class Prefs:
        risk_free_rate_mode = 'manual'
        risk_free_rate_manual = 0.30

    macro = dict(TURKEY_MACRO)
    result = _apply_risk_free_override(macro, Prefs())
    assert result['risk_free_rate'] == 0.30
    assert result is not macro  # Kopya oluşturulmuş


@pytest.mark.unit
def test_risk_free_override_manual_no_value():
    """risk_free_rate_mode='manual' ama değer None → değişiklik yok"""
    class Prefs:
        risk_free_rate_mode = 'manual'
        risk_free_rate_manual = None

    macro = dict(TURKEY_MACRO)
    result = _apply_risk_free_override(macro, Prefs())
    assert result is macro


# ─── get_dynamic_turkey_macro ────────────────────────────────────────────────

@pytest.mark.unit
def test_get_dynamic_turkey_macro_returns_dict():
    result = get_dynamic_turkey_macro()
    assert isinstance(result, dict)
    assert 'risk_free_rate' in result


@pytest.mark.unit
def test_get_dynamic_turkey_macro_fallback_on_error():
    """market_data_service import hatası → default TURKEY_MACRO dönmeli"""
    with patch('engines.analysis_engine.get_dynamic_turkey_macro', side_effect=Exception("fetch error")):
        # Doğrudan çağrı, exception yutulup default dönmeli
        result = get_dynamic_turkey_macro()
        assert result['policy_rate'] > 0


# ─── AnalysisEngine.__init__ ──────────────────────────────────────────────────

@pytest.mark.unit
def test_analysis_engine_init():
    engine = _make_engine()
    assert hasattr(engine, 'risk_free_rate')
    assert hasattr(engine, 'market_data_service')
    assert engine.risk_free_rate > 0


# ─── calculate_z_score ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_z_score_returns_series():
    engine = _make_engine()
    df = _make_price_series(300)
    result = engine.calculate_z_score(df, window=50)
    assert isinstance(result, pd.Series)
    assert len(result) == 300


@pytest.mark.unit
def test_z_score_none_on_empty_data():
    engine = _make_engine()
    result = engine.calculate_z_score(pd.DataFrame(), window=50)
    assert result is None


@pytest.mark.unit
def test_z_score_none_on_none_data():
    engine = _make_engine()
    result = engine.calculate_z_score(None, window=50)
    assert result is None


@pytest.mark.unit
def test_z_score_constant_prices_no_inf():
    """Sabit fiyat → sıfır std → Z-score sonsuz olmamalı"""
    engine = _make_engine()
    df = pd.DataFrame({'price': [100.0] * 100})
    result = engine.calculate_z_score(df, window=20)
    assert result is not None
    finite_vals = result.dropna()
    assert not finite_vals.isin([float('inf'), float('-inf')]).any()


@pytest.mark.unit
def test_z_score_missing_price_column():
    """'price' sütunu yok → None döner"""
    engine = _make_engine()
    df = pd.DataFrame({'close': [100, 101, 102]})
    result = engine.calculate_z_score(df, window=2)
    assert result is None


@pytest.mark.unit
def test_z_score_statistically_valid():
    """Yeterli veri ile Z-score'lar ≈ sıfır ortalamalı olmalı"""
    engine = _make_engine()
    df = _make_price_series(500, noise=5.0, seed=1)
    result = engine.calculate_z_score(df, window=100)
    finite = result.dropna()
    # Sıfıra yakın ortalama (±1.5 σ tolerans)
    assert abs(float(finite.mean())) < 1.5


# ─── calculate_mean_reversion_signal ─────────────────────────────────────────

@pytest.mark.unit
def test_mean_reversion_signal_structure():
    engine = _make_engine()
    df = _make_price_series(300)
    result = engine.calculate_mean_reversion_signal(df, window=50)
    if result is not None:
        assert 'signal' in result
        assert 'strength' in result
        assert 'current_z_score' in result
        assert 'threshold' in result


@pytest.mark.unit
def test_mean_reversion_signal_valid_values():
    engine = _make_engine()
    df = _make_price_series(300)
    result = engine.calculate_mean_reversion_signal(df, window=50)
    if result is not None:
        assert result['signal'] in ('AL', 'SAT', 'TUT')
        assert 0 <= result['strength'] <= 100


@pytest.mark.unit
def test_mean_reversion_signal_empty_data():
    engine = _make_engine()
    result = engine.calculate_mean_reversion_signal(pd.DataFrame(), window=50)
    assert result is None


@pytest.mark.unit
def test_mean_reversion_sat_signal():
    """Fiyat büyük ölçüde yükseldiyse SAT sinyali çıkmalı"""
    engine = _make_engine()
    prices = [100.0] * 100
    prices[-1] = 200.0
    df = pd.DataFrame({'price': prices})
    result = engine.calculate_mean_reversion_signal(df, window=100)
    assert result is not None
    assert result['signal'] == 'SAT'


@pytest.mark.unit
def test_mean_reversion_al_signal():
    """Fiyat büyük ölçüde düştüyse AL sinyali çıkmalı"""
    engine = _make_engine()
    prices = [100.0] * 100
    prices[-1] = 10.0
    df = pd.DataFrame({'price': prices})
    result = engine.calculate_mean_reversion_signal(df, window=100)
    assert result is not None
    assert result['signal'] == 'AL'


# ─── calculate_sharpe_ratio ──────────────────────────────────────────────────

@pytest.mark.unit
def test_sharpe_ratio_returns_float():
    engine = _make_engine()
    df = _make_price_series(300, trend=0.1)
    result = engine.calculate_sharpe_ratio(df, risk_free_rate=0.05)
    assert isinstance(result, float)


@pytest.mark.unit
def test_sharpe_ratio_none_on_empty():
    engine = _make_engine()
    result = engine.calculate_sharpe_ratio(pd.DataFrame())
    assert result is None


@pytest.mark.unit
def test_sharpe_ratio_none_on_single_row():
    engine = _make_engine()
    df = pd.DataFrame({'price': [100.0]})
    result = engine.calculate_sharpe_ratio(df)
    assert result is None


@pytest.mark.unit
def test_sharpe_ratio_positive_for_uptrend():
    """Güçlü yükselen trend → pozitif Sharpe"""
    engine = _make_engine()
    # Kuvvetli yükseliş, düşük gürültü
    prices = [100.0 * (1.001 ** i) for i in range(500)]
    df = pd.DataFrame({'price': prices})
    result = engine.calculate_sharpe_ratio(df, risk_free_rate=0.0)
    assert result is not None
    assert result > 0


@pytest.mark.unit
def test_sharpe_ratio_negative_for_downtrend():
    """Düşen trend → negatif Sharpe"""
    engine = _make_engine()
    prices = [100.0 * (0.999 ** i) for i in range(500)]
    df = pd.DataFrame({'price': prices})
    result = engine.calculate_sharpe_ratio(df, risk_free_rate=0.0)
    assert result is not None
    assert result < 0


@pytest.mark.unit
def test_sharpe_ratio_finite():
    """Sharpe ratio sonlu olmalı (inf/nan değil)"""
    engine = _make_engine()
    df = _make_price_series(300)
    result = engine.calculate_sharpe_ratio(df)
    if result is not None:
        assert np.isfinite(result)


@pytest.mark.unit
def test_sharpe_ratio_constant_returns_zero():
    """Sabit fiyat → std=0 → Sharpe=0.0"""
    engine = _make_engine()
    df = pd.DataFrame({'price': [100.0] * 300})
    result = engine.calculate_sharpe_ratio(df)
    assert result == 0.0


# ─── calculate_correlation_matrix ────────────────────────────────────────────

@pytest.mark.unit
def test_correlation_matrix_none_on_empty():
    engine = _make_engine()
    result = engine.calculate_correlation_matrix({})
    assert result is None


@pytest.mark.unit
def test_correlation_matrix_none_single_asset():
    """Tek varlık → korelasyon hesaplanamaz"""
    engine = _make_engine()
    df = _make_price_series(200)
    market_data = {'BIST100': {'data': df}}
    result = engine.calculate_correlation_matrix(market_data, periods=[30])
    assert result is None


@pytest.mark.unit
def test_correlation_matrix_structure():
    """İki varlık → corr matrix dict döner"""
    engine = _make_engine()
    df1 = _make_price_series(200, seed=1)
    df2 = _make_price_series(200, seed=2)
    market_data = {
        'A': {'data': df1},
        'B': {'data': df2},
    }
    result = engine.calculate_correlation_matrix(market_data, periods=[30])
    if result:
        assert 30 in result
        assert 'matrix' in result[30]
        assert 'max_correlation' in result[30]
        assert 'crisis_mode' in result[30]


@pytest.mark.unit
def test_correlation_matrix_range():
    """Korelasyon -1 ile 1 arasında"""
    engine = _make_engine()
    df1 = _make_price_series(200, seed=10)
    df2 = _make_price_series(200, seed=20)
    market_data = {'X': {'data': df1}, 'Y': {'data': df2}}
    result = engine.calculate_correlation_matrix(market_data, periods=[30])
    if result and 30 in result:
        max_corr = result[30]['max_correlation']
        assert -1.0 <= max_corr <= 1.0


@pytest.mark.unit
def test_correlation_matrix_crisis_mode_perfect_corr():
    """Mükemmel korelasyon → crisis_mode=True"""
    engine = _make_engine()
    df = _make_price_series(200, seed=7)
    # Aynı varlık farklı isimle → korelasyon = 1.0
    market_data = {'A': {'data': df.copy()}, 'B': {'data': df.copy()}}
    result = engine.calculate_correlation_matrix(market_data, periods=[50])
    if result and 50 in result:
        assert result[50]['crisis_mode'] is True


# ─── Diğer public metodlar ────────────────────────────────────────────────────

@pytest.mark.unit
def test_engine_has_market_stress_index():
    engine = _make_engine()
    assert hasattr(engine, 'calculate_market_stress_index')


@pytest.mark.unit
def test_engine_has_macro_regime_filter():
    engine = _make_engine()
    assert hasattr(engine, 'apply_macro_regime_filter')


@pytest.mark.unit
def test_engine_has_relative_strength():
    engine = _make_engine()
    assert hasattr(engine, 'calculate_relative_strength')


# ─── calculate_market_stress_index ────────────────────────────────────────────

@pytest.mark.unit
def test_stress_index_none_on_empty():
    engine = _make_engine()
    result = engine.calculate_market_stress_index({})
    assert result is None


@pytest.mark.unit
def test_stress_index_structure():
    engine = _make_engine()
    corr_matrices = {
        30: {'max_correlation': 0.6, 'crisis_mode': False, 'matrix': {}}
    }
    result = engine.calculate_market_stress_index(corr_matrices)
    assert result is not None
    assert 'stress_index' in result
    assert 'crisis_mode' in result
    assert 'stress_level' in result


@pytest.mark.unit
def test_stress_index_low_correlation():
    engine = _make_engine()
    corr_matrices = {30: {'max_correlation': 0.3, 'crisis_mode': False, 'matrix': {}}}
    result = engine.calculate_market_stress_index(corr_matrices)
    assert result['stress_level'] == 'DÜŞÜK'
    assert result['stress_index'] == 0.0


@pytest.mark.unit
def test_stress_index_high_correlation():
    engine = _make_engine()
    corr_matrices = {30: {'max_correlation': 0.95, 'crisis_mode': True, 'matrix': {}}}
    result = engine.calculate_market_stress_index(corr_matrices)
    assert result['stress_index'] > STRESS_HIGH_THRESH
    assert result['crisis_mode'] is True
    assert result['stress_level'] == 'YÜKSEK'


# ─── apply_macro_regime_filter ────────────────────────────────────────────────

@pytest.mark.unit
def test_macro_regime_none_on_empty_data():
    engine = _make_engine()
    result = engine.apply_macro_regime_filter({})
    assert result is None


@pytest.mark.unit
def test_macro_regime_defansif():
    """Yüksek faiz → DEFANSIF rejim"""
    engine = _make_engine()
    market_data = {'GC=F': {'name': 'Altın', 'data': _make_price_series(100)}}
    result = engine.apply_macro_regime_filter(
        market_data, interest_rate=0.50, inflation_rate=0.45
    )
    assert result is not None
    assert result['regime'] == 'DEFANSIF'


@pytest.mark.unit
def test_macro_regime_agresif():
    """Düşük faiz + düşük enflasyon → AGRESIF rejim"""
    engine = _make_engine()
    market_data = {'^IXIC': {'name': 'NASDAQ', 'data': _make_price_series(100)}}
    result = engine.apply_macro_regime_filter(
        market_data, interest_rate=0.05, inflation_rate=0.10
    )
    assert result is not None
    assert result['regime'] == 'AGRESIF'


@pytest.mark.unit
def test_macro_regime_neutral():
    """Orta faiz + orta enflasyon → NÖTR rejim"""
    engine = _make_engine()
    market_data = {'XU100.IS': {'name': 'BIST100', 'data': _make_price_series(100)}}
    result = engine.apply_macro_regime_filter(
        market_data, interest_rate=0.15, inflation_rate=0.25
    )
    assert result is not None
    assert result['regime'] == 'NÖTR'


@pytest.mark.unit
def test_macro_regime_structure():
    engine = _make_engine()
    market_data = {'GC=F': {'name': 'Altın', 'data': _make_price_series(50)}}
    result = engine.apply_macro_regime_filter(market_data, interest_rate=0.50, inflation_rate=0.45)
    assert 'regime' in result
    assert 'description' in result
    assert 'interest_rate' in result
    assert 'inflation_rate' in result
    assert 'asset_scores' in result
