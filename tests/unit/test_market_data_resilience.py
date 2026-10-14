"""
Unit tests for Market Data Outage Resilience and Stale-Cache Fallback.
"""
from unittest.mock import Mock, patch
import pytest

from infrastructure.background.background_service import BackgroundService


@pytest.mark.unit
def test_outage_preserves_previous_quotes_and_sets_stale():
    """When market data providers fail, previous quotes must be preserved and flagged as stale."""
    with patch('infrastructure.background.background_service.os.makedirs'), \
         patch('infrastructure.background.background_service.BackgroundService._load_cache'):
        service = BackgroundService()
        # Seed previously successful quotes
        service._live_data = {
            'weather': '19°C',
            'usd': '34.25',
            'eur': '37.10',
            'gold': '2,950.00',
            'last_updated': '2026-10-12 12:00:00',
            'is_stale': False,
        }

        # Simulate provider chain throwing an exception (network outage)
        with patch('infrastructure.background.background_service.fetch_resilient_live_quotes',
                   side_effect=RuntimeError("Connection timeout / DNS failure")), \
             patch('infrastructure.background.background_service.requests.get',
                   side_effect=Exception("Weather API down")):
            service._update_live_data()

        data = service.get_live_data()
        # Previous valid values must be preserved
        assert data['usd'] == '34.25'
        assert data['eur'] == '37.10'
        assert data['gold'] == '2,950.00'
        assert data['weather'] == '19°C'
        # Must be flagged as stale
        assert data['is_stale'] is True
        # Must preserve original last_updated timestamp rather than overwriting with current time
        assert data['last_updated'] == '2026-10-12 12:00:00'


@pytest.mark.unit
def test_recovery_clears_stale_flag():
    """When market data providers recover, is_stale must be reset to False."""
    with patch('infrastructure.background.background_service.os.makedirs'), \
         patch('infrastructure.background.background_service.BackgroundService._load_cache'):
        service = BackgroundService()
        service._live_data = {
            'weather': '19°C',
            'usd': '34.25',
            'eur': '37.10',
            'gold': '2,950.00',
            'last_updated': '2026-10-12 12:00:00',
            'is_stale': True,
        }

        fake_quotes = Mock()
        fake_quotes.values = {'usd': '34.50', 'eur': '37.30', 'gold': '2,980.00'}
        fake_quotes.safe_status.return_value = {
            'provider_by_field': {'usd': 'doviz_com', 'eur': 'doviz_com', 'gold': 'doviz_com'},
            'fallback_used': False,
            'provider_error_count': 0,
            'missing_fields': [],
            'quality_status': 'live',
        }

        weather_res = Mock()
        weather_res.status_code = 200
        weather_res.text = '22°C'

        with patch('infrastructure.background.background_service.fetch_resilient_live_quotes', return_value=fake_quotes), \
             patch('infrastructure.background.background_service.requests.get', return_value=weather_res):
            service._update_live_data()

        data = service.get_live_data()
        assert data['usd'] == '34.50'
        assert data['eur'] == '37.30'
        assert data['gold'] == '2,980.00'
        assert data['weather'] == '22°C'
        assert data['is_stale'] is False


@pytest.mark.unit
def test_live_quotes_api_contains_is_stale_flag(privileged_authenticated_client):
    """The /api/live-quotes endpoint must return is_stale in JSON response."""
    response = privileged_authenticated_client.get('/api/live-quotes')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert 'quotes' in payload
    assert 'is_stale' in payload['quotes']
