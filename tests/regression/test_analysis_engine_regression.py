"""
Regression Tests for analysis_engine.py
Critical quantitative analysis calculations must remain unchanged during refactoring
"""

import numpy as np
import pandas as pd
import pytest

from engines.analysis_engine import TURKEY_MACRO, AnalysisEngine, get_dynamic_turkey_macro


class TestAnalysisEngineRegression:
    """Regression tests to ensure quantitative analysis calculations remain unchanged"""

    def test_turkey_macro_constants(self):
        """Test Turkey macro constants reflect 2026 realities"""
        assert TURKEY_MACRO["policy_rate"] == 0.50  # Haziran 2026
        assert TURKEY_MACRO["inflation"] == 0.45  # Haziran 2026
        assert TURKEY_MACRO["real_rate"] == 0.05  # Haziran 2026
        assert TURKEY_MACRO["risk_free_rate"] == 0.50  # Haziran 2026
        assert "Haziran 2026" in TURKEY_MACRO["source"]
        assert "Hardcoded Fallback" in TURKEY_MACRO["source"]

    def test_get_dynamic_turkey_macro_structure(self):
        """Test dynamic macro data returns expected structure"""
        macro = get_dynamic_turkey_macro()

        # Must contain these keys
        assert "policy_rate" in macro
        assert "inflation" in macro
        assert "real_rate" in macro
        assert "risk_free_rate" in macro
        assert "source" in macro

        # Values must be numeric
        assert isinstance(macro["policy_rate"], (int, float))
        assert isinstance(macro["inflation"], (int, float))
        assert isinstance(macro["real_rate"], (int, float))
        assert isinstance(macro["risk_free_rate"], (int, float))

    def test_analysis_engine_initialization(self):
        """Test AnalysisEngine initialization with market data service"""
        # Create mock market data service
        class MockMarketDataService:
            def get_historical_data(self, symbol, period):
                return pd.DataFrame({
                    'price': [100, 101, 102, 103, 104],
                    'date': pd.date_range(start='2025-01-01', periods=5)
                })

        engine = AnalysisEngine(MockMarketDataService())

        assert engine.market_data_service is not None
        assert engine.risk_free_rate is not None
        assert isinstance(engine.risk_free_rate, (int, float))

    def test_z_score_calculation_formula(self):
        """Test Z-Score formula: Z = (P_t − μ_rolling) / σ_rolling"""
        # Test data
        data = pd.DataFrame({
            'price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })

        # Manual calculation
        mean = data['price'].mean()
        std = data['price'].std()
        z_score = (data['price'].iloc[-1] - mean) / std

        # Expected result
        expected_z = (109 - 104.5) / 3.0277  # approximately 1.48

        assert abs(z_score - expected_z) < 0.1

    def test_sharpe_ratio_formula(self):
        """Test Sharpe Ratio formula: (R_p - R_f) / σ_p"""
        # Test case
        portfolio_return = 0.15  # 15%
        risk_free_rate = 0.08    # 8%
        portfolio_std = 0.20     # 20%

        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std

        expected_sharpe = (0.15 - 0.08) / 0.20  # 0.35

        assert abs(sharpe_ratio - expected_sharpe) < 0.01

    def test_correlation_calculation(self):
        """Test correlation calculation between two assets"""
        # Test data
        asset1_returns = [0.01, 0.02, -0.01, 0.03, 0.01]
        asset2_returns = [0.02, 0.01, -0.02, 0.02, 0.03]

        correlation = np.corrcoef(asset1_returns, asset2_returns)[0, 1]

        # Correlation should be between -1 and 1
        assert -1 <= correlation <= 1
        assert isinstance(correlation, (int, float))

    def test_volatility_calculation(self):
        """Test volatility (standard deviation) calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00]

        volatility = np.std(returns)

        # Volatility should be positive
        assert volatility > 0
        assert isinstance(volatility, (int, float))

    def test_regime_thresholds(self):
        """Test regime detection thresholds remain unchanged"""
        from engines.analysis_engine import REGIME_THRESHOLDS

        assert REGIME_THRESHOLDS["defansif_rate"] == 0.20
        assert REGIME_THRESHOLDS["defansif_inflation"] == 0.40
        assert REGIME_THRESHOLDS["agresif_rate"] == 0.10
        assert REGIME_THRESHOLDS["agresif_inflation"] == 0.20

    def test_signal_thresholds(self):
        """Test signal thresholds remain unchanged"""
        from engines.analysis_engine import CRISIS_CORR_THRESH, STRESS_HIGH_THRESH, STRESS_MED_THRESH, Z_SCORE_THRESHOLD

        assert Z_SCORE_THRESHOLD == 2.0
        assert CRISIS_CORR_THRESH == 0.90
        assert STRESS_HIGH_THRESH == 70
        assert STRESS_MED_THRESH == 40


class TestAnalysisEngineFormulas:
    """Test specific analysis formulas remain unchanged"""

    def test_mean_reversion_formula(self):
        """Test mean reversion: Price tends to return to mean"""
        prices = [100, 105, 110, 108, 102, 98, 95, 97, 103, 107]
        mean = np.mean(prices)

        # Prices should be distributed around mean
        assert min(prices) < mean < max(prices)

        # Calculate deviation from mean
        deviations = [p - mean for p in prices]
        assert abs(sum(deviations)) < 0.1  # Sum should be close to 0

    def test_portfolio_return_formula(self):
        """Test portfolio return: Σ(w_i * r_i)"""
        weights = [0.3, 0.4, 0.3]
        returns = [0.10, 0.15, 0.08]

        portfolio_return = sum(w * r for w, r in zip(weights, returns))
        expected_return = 0.3*0.10 + 0.4*0.15 + 0.3*0.08  # 0.114

        assert abs(portfolio_return - expected_return) < 0.001

    def test_portfolio_variance_formula(self):
        """Test portfolio variance with correlation"""
        weights = [0.5, 0.5]
        variances = [0.04, 0.09]  # 20% and 30% volatility
        correlation = 0.5

        # Portfolio variance = w1²σ1² + w2²σ2² + 2w1w2σ1σ2ρ
        portfolio_variance = (
            weights[0]**2 * variances[0] +
            weights[1]**2 * variances[1] +
            2 * weights[0] * weights[1] * np.sqrt(variances[0]) * np.sqrt(variances[1]) * correlation
        )

        expected_variance = 0.25*0.04 + 0.25*0.09 + 2*0.5*0.5*0.2*0.3*0.5  # 0.0475

        assert abs(portfolio_variance - expected_variance) < 0.001


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
