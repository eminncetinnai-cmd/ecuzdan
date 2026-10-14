"""Unit tests for LiveRatioProvider domain service."""

from decimal import Decimal

from domain.ratios.data.historical_ratios_data import get_all_ratio_definitions
from domain.ratios.services.live_ratio_provider import LiveRatioProvider


def test_compute_live_ratios_with_mock_quotes():
    provider = LiveRatioProvider()
    mock_quotes = {
        'gold': 2400.0,
        'silver': 30.0,
        'oil': 80.0,
        'copper': 4.5,
        'vix': 28.5,
        'us10y': 4.2,
        'us2y': 3.8,
        'dxy': 104.2,
        'bist100': 9860.0,
        'usdtry': 34.0,
    }

    ratios = provider.compute_live_ratios(mock_quotes)

    assert ratios['gold_silver_ratio'] == Decimal('80.0')
    assert ratios['gold_oil_ratio'] == Decimal('30.0')
    assert ratios['copper_gold_ratio'] == Decimal('1.88')
    assert ratios['vix_index'] == Decimal('28.5')
    assert ratios['us_yield_curve_10y_2y'] == Decimal('0.40')
    assert ratios['dxy_index'] == Decimal('104.2')
    assert ratios['bist_usd_index'] == Decimal('290')


def test_compute_live_ratios_handles_missing_quotes():
    provider = LiveRatioProvider()
    mock_quotes = {
        'gold': 2400.0,
        # silver missing
        'vix': 19.4,
    }

    ratios = provider.compute_live_ratios(mock_quotes)

    assert 'gold_silver_ratio' not in ratios
    assert ratios['vix_index'] == Decimal('19.4')


def test_apply_live_values_to_definitions():
    definitions = get_all_ratio_definitions()
    vix_def = next(d for d in definitions if d.code == 'vix_index')
    orig_val = vix_def.series[-1].value

    live_values = {'vix_index': Decimal('32.8')}
    updated_defs = LiveRatioProvider.apply_live_values_to_definitions(definitions, live_values)

    updated_vix = next(d for d in updated_defs if d.code == 'vix_index')
    assert updated_vix.series[-1].value == Decimal('32.8')
    assert orig_val != Decimal('32.8')


def test_apply_live_values_empty_returns_unchanged():
    definitions = get_all_ratio_definitions()
    res = LiveRatioProvider.apply_live_values_to_definitions(definitions, {})
    assert res == definitions
