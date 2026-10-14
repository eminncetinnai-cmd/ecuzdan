"""
Production Stability Integration Test - SRE & QA Verification
Tests critical components 3 times consecutively to ensure stability
"""

from unittest.mock import Mock

import pandas as pd
import pytest

from domain.portfolio.services.investment_performance import get_yearly_performance
from engines.analysis_engine import AnalysisEngine, get_analysis_engine
from market_data_service import get_macro_economic_data


@pytest.mark.slow
class TestProductionStabilityIntegration:
    """Production stability integration test for production readiness verification"""

    def test_investment_performance_service_stability(self):
        """Test investment performance service 3 times consecutively"""
        print("\n=== Investment Performance Service Stability Test ===")

        for i in range(3):
            try:
                result = get_yearly_performance()
                print(f"  Run {i+1}: Success - Data keys: {list(result.keys())}")
                assert result is not None
                assert 'yearly_data' in result
                assert 'inflation_adjusted' in result
                assert 'summary' in result
            except Exception as e:
                print(f"  Run {i+1}: FAILED - {e}")
                raise AssertionError(f"Investment performance service failed on run {i+1}: {e}")

        print("[OK] Investment performance service: 3/3 runs successful")

    def test_analysis_engine_stability(self):
        """Test analysis engine 3 times consecutively"""
        print("\n=== Analysis Engine Stability Test ===")

        # Create mock market data service
        mock_market_service = Mock()
        mock_market_data = {
            'BTC-USD': {
                'name': 'Bitcoin',
                'currency': 'USD',
                'data': pd.DataFrame({
                    'price': [50000, 52000, 51000, 53000, 55000, 54000, 56000, 58000, 57000, 60000] * 30
                })
            }
        }
        mock_market_service.get_all_market_data.return_value = mock_market_data

        for i in range(3):
            try:
                engine = AnalysisEngine(mock_market_service)
                result = engine.run_full_analysis()
                print(f"  Run {i+1}: Success - Data keys: {list(result.keys())}")
                assert result is not None
                assert 'timestamp' in result
                assert 'data_available' in result
                assert result['data_available']
            except Exception as e:
                print(f"  Run {i+1}: FAILED - {e}")
                raise AssertionError(f"Analysis engine failed on run {i+1}: {e}")

        print("[OK] Analysis engine: 3/3 runs successful")

    def test_macro_data_fetching_stability(self):
        """Test macro data fetching service 3 times consecutively"""
        print("\n=== Macro Data Fetching Stability Test ===")

        for i in range(3):
            try:
                result = get_macro_economic_data()
                print(f"  Run {i+1}: Success - Source: {result.get('source', 'unknown')}")
                assert result is not None
                assert 'inflation_rate' in result
                assert 'interest_rate' in result
                assert 'real_return_rate' in result
                assert 'last_updated' in result
                assert 'source' in result
            except Exception as e:
                print(f"  Run {i+1}: FAILED - {e}")
                raise AssertionError(f"Macro data fetching failed on run {i+1}: {e}")

        print("[OK] Macro data fetching: 3/3 runs successful")

    def test_portfolio_analysis_stability(self):
        """Test portfolio analysis 3 times consecutively"""
        print("\n=== Portfolio Analysis Stability Test ===")

        class MockAsset:
            def __init__(self, symbol, name, unit_price, quantity):
                self.symbol = symbol
                self.name = name
                self.unit_price = unit_price
                self.quantity = quantity

        mock_market_service = Mock()
        mock_market_data = {
            'BTC-USD': {
                'name': 'Bitcoin',
                'currency': 'USD',
                'data': pd.DataFrame({
                    'price': [50000, 52000, 51000, 53000, 55000, 54000, 56000, 58000, 57000, 60000] * 30
                })
            }
        }
        mock_market_service.get_all_market_data.return_value = mock_market_data

        mock_portfolio = [MockAsset('BTC', 'Bitcoin', 50000, 0.5)]

        for i in range(3):
            try:
                engine = AnalysisEngine(mock_market_service)
                result = engine.run_full_analysis(user_portfolio=mock_portfolio)
                print(f"  Run {i+1}: Success - Portfolio analysis present: {'portfolio_analysis' in result}")
                assert result is not None
                assert 'portfolio_analysis' in result
                assert result['portfolio_analysis']['total_assets'] == 1
                assert result['portfolio_analysis']['analyzed_assets'] == 1
            except Exception as e:
                print(f"  Run {i+1}: FAILED - {e}")
                raise AssertionError(f"Portfolio analysis failed on run {i+1}: {e}")

        print("[OK] Portfolio analysis: 3/3 runs successful")

    def test_singleton_thread_safety_stability(self):
        """Test singleton thread safety 3 times consecutively"""
        print("\n=== Singleton Thread Safety Stability Test ===")

        mock_market_service = Mock()

        for i in range(3):
            try:
                engine1 = get_analysis_engine(mock_market_service)
                engine2 = get_analysis_engine(mock_market_service)
                print(f"  Run {i+1}: Success - Same instance: {engine1 is engine2}")
                assert engine1 is engine2
            except Exception as e:
                print(f"  Run {i+1}: FAILED - {e}")
                raise AssertionError(f"Singleton failed on run {i+1}: {e}")

        print("[OK] Singleton thread safety: 3/3 runs successful")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

