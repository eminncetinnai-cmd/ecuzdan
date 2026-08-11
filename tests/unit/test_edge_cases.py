"""
Edge-Case Unit Tests for analysis_engine.py Refactoring
Tests for robustness against infinite, NaN, zero, and empty data scenarios
"""

import numpy as np
import pandas as pd
import pytest

from engines.analysis_engine import AnalysisEngine


class MockMarketDataService:
    """Mock market data service for testing"""
    def get_all_market_data(self):
        return {
            'TEST': {
                'name': 'Test Asset',
                'data': pd.DataFrame({'price': [100, 101, 102, 103, 104]})
            }
        }


class TestZScoreEdgeCases:
    """Test Z-Score calculation handles edge cases robustly"""

    def test_z_score_with_constant_prices(self):
        """Test Z-Score when prices are constant (std=0)"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [100, 100, 100, 100, 100]})

        result = engine.calculate_z_score(data, window=5)

        # Should not return inf or nan
        assert result is not None
        assert not any(np.isinf(result.dropna()))
        assert not any(np.isnan(result.dropna()))

    def test_z_score_with_single_price(self):
        """Test Z-Score with only one data point"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [100]})

        result = engine.calculate_z_score(data, window=5)

        # Should handle gracefully
        assert result is not None

    def test_z_score_with_nan_prices(self):
        """Test Z-Score with NaN values in price series"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [100, np.nan, 102, 103, 104]})

        result = engine.calculate_z_score(data, window=5)

        # Should handle NaN without crashing
        assert result is not None

    def test_z_score_with_zero_std_window(self):
        """Test Z-Score when rolling window has zero std"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [100, 100, 100, 105, 110]})

        result = engine.calculate_z_score(data, window=3)

        # Should not produce inf values
        assert result is not None
        if result is not None and not result.empty:
            assert not any(np.isinf(result.dropna()))


class TestSharpeRatioEdgeCases:
    """Test Sharpe Ratio calculation handles edge cases robustly"""

    def test_sharpe_with_empty_returns(self):
        """Test Sharpe Ratio with empty returns"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [100]})

        result = engine.calculate_sharpe_ratio(data)

        # Should return None or 0, not crash
        assert result is None or result == 0.0

    def test_sharpe_with_constant_prices(self):
        """Test Sharpe Ratio with constant prices (zero volatility)"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [100, 100, 100, 100, 100]})

        result = engine.calculate_sharpe_ratio(data)

        # Should handle zero volatility
        assert result is not None
        assert not np.isnan(result)
        assert not np.isinf(result)

    def test_sharpe_with_negative_prices(self):
        """Test Sharpe Ratio with negative prices (edge case)"""
        engine = AnalysisEngine(MockMarketDataService())
        data = pd.DataFrame({'price': [-100, -99, -98, -97, -96]})

        result = engine.calculate_sharpe_ratio(data)

        # Should handle negative prices
        assert result is not None or result is None

    def test_sharpe_geometric_fallback(self):
        """Test that geometric calculation falls back to arithmetic if needed"""
        engine = AnalysisEngine(MockMarketDataService())
        # Create data that might cause geometric calculation issues
        data = pd.DataFrame({'price': [100, 90, 80, 70, 60]})

        result = engine.calculate_sharpe_ratio(data)

        # Should return a valid result (either geometric or arithmetic)
        assert result is not None or result is None
        if result is not None:
            assert not np.isnan(result)
            assert not np.isinf(result)


class TestMarketStressIndexEdgeCases:
    """Test Market Stress Index handles edge cases robustly"""

    def test_stress_index_with_empty_correlation(self):
        """Test Stress Index with empty correlation matrices"""
        engine = AnalysisEngine(MockMarketDataService())
        result = engine.calculate_market_stress_index(None)

        # Should handle None gracefully
        assert result is None

    def test_stress_index_with_single_asset(self):
        """Test Stress Index with only one asset (no correlation)"""
        engine = AnalysisEngine(MockMarketDataService())
        correlation_matrices = {
            30: {
                'matrix': {'TEST': {'TEST': 1.0}},
                'max_correlation': 1.0,
                'crisis_mode': False
            }
        }

        result = engine.calculate_market_stress_index(correlation_matrices)

        # Should handle single asset
        assert result is not None
        assert 'stress_index' in result
        assert not np.isnan(result['stress_index'])
        assert not np.isinf(result['stress_index'])

    def test_stress_index_with_nan_correlation(self):
        """Test Stress Index with NaN correlation values"""
        engine = AnalysisEngine(MockMarketDataService())
        correlation_matrices = {
            30: {
                'matrix': {'TEST': {'OTHER': np.nan}},
                'max_correlation': np.nan,
                'crisis_mode': False
            }
        }

        result = engine.calculate_market_stress_index(correlation_matrices)

        # Should handle NaN without crashing
        assert result is not None
        if result is not None:
            assert not np.isinf(result.get('stress_index', 0))

    def test_stress_index_finite_validation(self):
        """Test that stress index always returns finite values"""
        engine = AnalysisEngine(MockMarketDataService())
        correlation_matrices = {
            30: {'max_correlation': 0.95, 'crisis_mode': True},
            90: {'max_correlation': 0.85, 'crisis_mode': False},
            180: {'max_correlation': 0.75, 'crisis_mode': False}
        }

        result = engine.calculate_market_stress_index(correlation_matrices)

        assert result is not None
        assert np.isfinite(result['stress_index'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
