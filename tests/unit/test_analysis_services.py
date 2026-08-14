"""
Unit tests for analysis services (InflationAnalyzer and RiskAnalyzer)
"""

import pytest
import math
from domain.analysis.services.inflation_analysis import InflationAnalyzer
from domain.analysis.services.risk_analysis import RiskAnalyzer


class TestInflationAnalyzer:
    """Test InflationAnalyzer functionality"""

    def test_calculate_real_return_fisher_equation(self):
        """Test real return calculation using Fisher equation"""
        nominal_return = 15.0  # 15%
        inflation_rate = 40.0  # 40%
        
        real_return = InflationAnalyzer.calculate_real_return(nominal_return, inflation_rate)
        
        # Fisher equation: (1 + 0.15) / (1 + 0.40) - 1 = -0.1786 = -17.86%
        expected = ((1 + 0.15) / (1 + 0.40) - 1) * 100
        assert abs(real_return - expected) < 0.01

    def test_calculate_real_return_positive_inflation(self):
        """Test real return with positive inflation"""
        nominal_return = 50.0  # 50%
        inflation_rate = 40.0  # 40%
        
        real_return = InflationAnalyzer.calculate_real_return(nominal_return, inflation_rate)
        
        # Should be positive since nominal > inflation
        assert real_return > 0
        assert real_return < nominal_return

    def test_calculate_real_return_negative_inflation(self):
        """Test real return with deflation (negative inflation)"""
        nominal_return = 5.0  # 5%
        inflation_rate = -2.0  # -2% (deflation)
        
        real_return = InflationAnalyzer.calculate_real_return(nominal_return, inflation_rate)
        
        # Should be higher than nominal in deflation
        assert real_return > nominal_return

    def test_calculate_purchasing_power(self):
        """Test purchasing power calculation"""
        initial_amount = 1000.0
        inflation_rate = 10.0  # 10%
        years = 1
        
        result = InflationAnalyzer.calculate_purchasing_power(initial_amount, inflation_rate, years)
        
        # After 1 year at 10% inflation: 1000 / 1.10 = 909.09
        expected_final = initial_amount / (1 + inflation_rate / 100)
        assert abs(result['final_amount'] - expected_final) < 0.01
        assert result['initial_amount'] == initial_amount
        assert result['years'] == years
        assert result['inflation_rate'] == inflation_rate

    def test_calculate_purchasing_power_multiple_years(self):
        """Test purchasing power over multiple years"""
        initial_amount = 1000.0
        inflation_rate = 10.0  # 10%
        years = 3
        
        result = InflationAnalyzer.calculate_purchasing_power(initial_amount, inflation_rate, years)
        
        # After 3 years at 10% inflation: 1000 / (1.10)^3 = 751.31
        expected_final = initial_amount / ((1 + inflation_rate / 100) ** years)
        assert abs(result['final_amount'] - expected_final) < 0.01

    def test_get_cumulative_inflation_single_year(self):
        """Test cumulative inflation for single year"""
        start_year = 2025
        end_year = 2025
        country = 'TR'
        
        cumulative = InflationAnalyzer._get_cumulative_inflation(start_year, end_year, country)
        
        # Should return the inflation rate for that year
        assert cumulative == InflationAnalyzer.INFLATION_DATA['TR'][2025]

    def test_get_cumulative_inflation_multiple_years(self):
        """Test cumulative inflation over multiple years"""
        start_year = 2023
        end_year = 2025
        country = 'TR'
        
        cumulative = InflationAnalyzer._get_cumulative_inflation(start_year, end_year, country)
        
        # Should be compounded over the period
        assert cumulative > 0
        assert isinstance(cumulative, float)

    def test_get_cumulative_inflation_unknown_country(self):
        """Test fallback to TR for unknown country"""
        start_year = 2025
        end_year = 2025
        country = 'UNKNOWN'
        
        cumulative = InflationAnalyzer._get_cumulative_inflation(start_year, end_year, country)
        
        # Should fall back to TR data
        assert cumulative == InflationAnalyzer.INFLATION_DATA['TR'][2025]

    def test_interpretate_real_return_positive(self):
        """Test interpretation of positive real return"""
        interpretation = InflationAnalyzer._interpretate_real_return(5.0, 10.0)
        assert "Positive" in interpretation

    def test_interpretate_real_return_negative(self):
        """Test interpretation of negative real return"""
        interpretation = InflationAnalyzer._interpretate_real_return(-10.0, 5.0)
        assert "Negative" in interpretation

    def test_interpretate_real_return_exceptional(self):
        """Test interpretation when real > nominal (deflation)"""
        interpretation = InflationAnalyzer._interpretate_real_return(10.0, 5.0)
        assert "Exceptional" in interpretation


class TestRiskAnalyzer:
    """Test RiskAnalyzer functionality"""

    def test_calculate_volatility(self):
        """Test volatility calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00]
        
        volatility = RiskAnalyzer.calculate_volatility(returns, annualize=False)
        
        # Volatility should be positive
        assert volatility > 0
        assert isinstance(volatility, float)

    def test_calculate_volatility_annualized(self):
        """Test annualized volatility calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01] * 50  # Varying returns
        
        volatility = RiskAnalyzer.calculate_volatility(returns, annualize=True)
        
        # Annualized should be higher than non-annualized
        assert volatility > 0

    def test_calculate_volatility_insufficient_data(self):
        """Test volatility with insufficient data"""
        returns = [0.01]  # Only one data point
        
        volatility = RiskAnalyzer.calculate_volatility(returns)
        
        # Should return 0 for insufficient data
        assert volatility == 0.0

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00]
        risk_free_rate = 0.05
        
        sharpe = RiskAnalyzer.calculate_sharpe_ratio(returns, risk_free_rate)
        
        # Sharpe ratio should be a number
        assert isinstance(sharpe, float)

    def test_calculate_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility"""
        returns = [0.01] * 10  # All same returns = zero volatility
        
        sharpe = RiskAnalyzer.calculate_sharpe_ratio(returns, 0.05)
        
        # Should return 0 when volatility is 0
        assert sharpe == 0.0

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00]
        risk_free_rate = 0.05
        
        sortino = RiskAnalyzer.calculate_sortino_ratio(returns, risk_free_rate)
        
        # Sortino ratio should be a number
        assert isinstance(sortino, float)

    def test_calculate_sortino_ratio_no_downside(self):
        """Test Sortino ratio with no downside risk"""
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]  # All positive
        
        sortino = RiskAnalyzer.calculate_sortino_ratio(returns, 0.05)
        
        # Should return infinity when no downside risk
        assert sortino == float('inf')

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation"""
        prices = [100, 105, 110, 108, 102, 98, 95, 97, 103, 107]
        
        drawdown = RiskAnalyzer.calculate_max_drawdown(prices)
        
        # Should have positive drawdown
        assert drawdown['max_drawdown'] > 0
        assert drawdown['max_drawdown_pct'] > 0
        assert drawdown['peak'] > 0
        assert drawdown['trough'] > 0

    def test_calculate_max_drawdown_insufficient_data(self):
        """Test max drawdown with insufficient data"""
        prices = [100]  # Only one price
        
        drawdown = RiskAnalyzer.calculate_max_drawdown(prices)
        
        # Should return zeros for insufficient data
        assert drawdown['max_drawdown'] == 0
        assert drawdown['max_drawdown_pct'] == 0

    def test_calculate_beta(self):
        """Test Beta calculation"""
        asset_returns = [0.01, 0.02, -0.01, 0.03, 0.01]
        market_returns = [0.02, 0.01, -0.02, 0.02, 0.03]
        
        beta = RiskAnalyzer.calculate_beta(asset_returns, market_returns)
        
        # Beta should be a number
        assert isinstance(beta, float)

    def test_calculate_beta_mismatched_lengths(self):
        """Test Beta with mismatched return lengths"""
        asset_returns = [0.01, 0.02, -0.01]
        market_returns = [0.02, 0.01]
        
        beta = RiskAnalyzer.calculate_beta(asset_returns, market_returns)
        
        # Should return default beta of 1.0
        assert beta == 1.0

    def test_calculate_var(self):
        """Test Value at Risk calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00, -0.05, -0.03]
        
        var_95 = RiskAnalyzer.calculate_var(returns, confidence_level=0.95)
        
        # VaR should be negative (indicating loss)
        assert var_95 < 0
        assert isinstance(var_95, float)

    def test_calculate_cvar(self):
        """Test Conditional VaR calculation"""
        returns = [0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.00, -0.05, -0.03]
        
        cvar_95 = RiskAnalyzer.calculate_cvar(returns, confidence_level=0.95)
        
        # CVaR should be negative (indicating loss)
        assert cvar_95 < 0
        assert isinstance(cvar_95, float)

    def test_calculate_risk_score(self):
        """Test composite risk score calculation"""
        volatility = 25.0  # 25% volatility
        max_drawdown_pct = 15.0  # 15% drawdown
        
        risk_score = RiskAnalyzer._calculate_risk_score(volatility, max_drawdown_pct)
        
        # Risk score should be between 0 and 100
        assert 0 <= risk_score <= 100

    def test_get_risk_level(self):
        """Test risk level classification"""
        assert RiskAnalyzer._get_risk_level(10) == 'Çok Düşük'
        assert RiskAnalyzer._get_risk_level(30) == 'Düşük'
        assert RiskAnalyzer._get_risk_level(50) == 'Orta'
        assert RiskAnalyzer._get_risk_level(70) == 'Yüksek'
        assert RiskAnalyzer._get_risk_level(90) == 'Çok Yüksek'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
