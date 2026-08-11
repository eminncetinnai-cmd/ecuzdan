"""
Circuit Breaker Tests for Macro Data Fetching
Tests for zero-downtime graceful degradation and cache poisoning prevention
"""

from unittest.mock import patch

import pytest
import requests

from engines.analysis_engine import TURKEY_MACRO, get_dynamic_turkey_macro


class TestCircuitBreaker:
    """Test circuit breaker pattern for macro data fetching"""

    def test_timeout_returns_static_fallback(self):
        """Test that timeout during external API fetch returns 2026 static fallback"""
        # Mock the market_data_service.get_macro_economic_data to raise timeout
        with patch('market_data_service.get_macro_economic_data') as mock_get_macro:
            # Simulate a timeout exception
            mock_get_macro.side_effect = requests.exceptions.Timeout("Connection timeout")

            # Call get_dynamic_turkey_macro - should catch exception and return TURKEY_MACRO
            result = get_dynamic_turkey_macro()

            # Verify it returns the 2026 static fallback
            assert result is not None
            assert result["policy_rate"] == TURKEY_MACRO["policy_rate"]
            assert result["inflation"] == TURKEY_MACRO["inflation"]
            assert result["real_rate"] == TURKEY_MACRO["real_rate"]
            assert result["risk_free_rate"] == TURKEY_MACRO["risk_free_rate"]
            assert "Hardcoded Fallback" in result["source"]

    def test_request_exception_returns_static_fallback(self):
        """Test that RequestException during external API fetch returns 2026 static fallback"""
        with patch('market_data_service.get_macro_economic_data') as mock_get_macro:
            # Simulate a connection error
            mock_get_macro.side_effect = requests.exceptions.ConnectionError("DNS resolution failed")

            result = get_dynamic_turkey_macro()

            # Verify it returns the 2026 static fallback
            assert result is not None
            assert result["policy_rate"] == TURKEY_MACRO["policy_rate"]
            assert result["inflation"] == TURKEY_MACRO["inflation"]

    def test_none_response_returns_static_fallback(self):
        """Test that None response from external API fetch returns 2026 static fallback"""
        with patch('market_data_service.get_macro_economic_data') as mock_get_macro:
            # Simulate external service returning None
            mock_get_macro.return_value = None

            result = get_dynamic_turkey_macro()

            # Verify it returns the 2026 static fallback
            assert result is not None
            assert result["policy_rate"] == TURKEY_MACRO["policy_rate"]
            assert result["inflation"] == TURKEY_MACRO["inflation"]

    def test_successful_external_fetch_uses_dynamic_data(self):
        """Test that successful external fetch uses dynamic data instead of static fallback"""
        with patch('market_data_service.get_macro_economic_data') as mock_get_macro:
            # Simulate successful external fetch
            mock_get_macro.return_value = {
                'inflation_rate': 42.0,
                'interest_rate': 48.0,
                'real_return_rate': 6.0,
                'last_updated': '2026-06-16 12:00:00',
                'source': 'evds_api'
            }

            result = get_dynamic_turkey_macro()

            # Verify it uses the dynamic data, not the static fallback
            assert result is not None
            assert result["policy_rate"] == 0.48  # 48% converted to decimal
            assert result["inflation"] == 0.42  # 42% converted to decimal
            assert result["source"] == 'evds_api'

    def test_cache_poisoning_prevention(self):
        """Test that cache poisoning is prevented when external fetch fails"""
        import time

        from market_data_service import MACRO_CACHE, MACRO_CACHE_TTL

        # Set up a valid cache but make it EXPIRED to trigger external fetch attempt
        MACRO_CACHE["data"] = {
            'inflation_rate': 40.0,
            'interest_rate': 45.0,
            'real_return_rate': 5.0,
            'last_updated': '2026-06-15 10:00:00',
            'source': 'evds_api'
        }
        MACRO_CACHE["last_fetched"] = time.time() - (MACRO_CACHE_TTL + 100)  # EXPIRED (beyond TTL)

        # Mock external fetch to fail
        with patch('market_data_service._fetch_macro_from_evds') as mock_evds, \
             patch('market_data_service._fetch_macro_from_investing') as mock_investing, \
             patch('market_data_service._fetch_macro_from_tcmb') as mock_tcmb:

            mock_evds.return_value = (None, None)
            mock_investing.return_value = (None, None)
            mock_tcmb.return_value = (None, None)

            # Call get_macro_economic_data
            from market_data_service import get_macro_economic_data
            result = get_macro_economic_data()

            # Verify it uses cache fallback (since all external sources failed)
            assert result['source'] == 'cache_fallback'
            assert result['interest_rate'] == 45.0  # From cache
            assert result['inflation_rate'] == 40.0  # From cache

            # Verify cache was NOT updated (cache poisoning prevention)
            # The cache timestamp should still be the old one
            assert MACRO_CACHE["last_fetched"] < time.time() - 50  # Still old timestamp


class TestStaticFallbackValues:
    """Test that 2026 static fallback values are correct"""

    def test_turkey_macro_2026_values(self):
        """Test that TURKEY_MACRO has correct 2026 values"""
        assert TURKEY_MACRO["policy_rate"] == 0.50
        assert TURKEY_MACRO["inflation"] == 0.45
        assert TURKEY_MACRO["real_rate"] == 0.05
        assert TURKEY_MACRO["risk_free_rate"] == 0.50
        assert "Haziran 2026" in TURKEY_MACRO["source"]
        assert "Hardcoded Fallback" in TURKEY_MACRO["source"]

    def test_real_rate_calculation(self):
        """Test that real_rate is correctly calculated as policy_rate - inflation"""
        expected_real = TURKEY_MACRO["policy_rate"] - TURKEY_MACRO["inflation"]
        assert abs(TURKEY_MACRO["real_rate"] - expected_real) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
