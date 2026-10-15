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


@pytest.mark.unit
def test_cold_start_unfetched_data_returns_indicative_rates_with_stale_flag():
    """On cold start before any network fetch, get_live_data must return indicative rates rather than --."""
    with patch('infrastructure.background.background_service.os.makedirs'), \
         patch('infrastructure.background.background_service.BackgroundService._load_cache'):
        service = BackgroundService()
        data = service.get_live_data()
        assert data['usd'] != '--'
        assert data['eur'] != '--'
        assert data['gold'] != '--'
        assert data['weather'] != '--'
        assert data['weather'] != '--°C'
        assert data['is_stale'] is True


@pytest.mark.unit
def test_truncgil_provider_parses_usd_eur_gold():
    """Truncgil provider must parse USD, EUR, and GRA into Decimal values."""
    from domain.analysis.services.fx_metals_provider import TruncgilProvider

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "Update_Date": "2026-10-15 13:00:00",
        "USD": {"Buying": 49.30, "Selling": 49.45},
        "EUR": {"Buying": 55.40, "Selling": 55.60},
        "GRA": {"Buying": 6600.00, "Selling": 6610.50},
    }

    from decimal import Decimal
    with patch('domain.analysis.services.fx_metals_provider._request', return_value=mock_resp):
        snapshot = TruncgilProvider().fetch()
        assert snapshot.source == "truncgil"
        assert snapshot.values["usd"] == Decimal("49.45")
        assert snapshot.values["eur"] == Decimal("55.60")
        assert snapshot.values["gold"] == Decimal("6610.50")


@pytest.mark.unit
def test_open_er_api_provider_parses_usd_eur():
    """OpenErApi provider must parse USD/TRY and calculate EUR/TRY."""
    from decimal import Decimal
    from domain.analysis.services.fx_metals_provider import OpenErApiProvider

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": "success",
        "rates": {"TRY": 49.50, "EUR": 0.89},
        "time_last_update_utc": "Thu, 15 Oct 2026 00:00:00 +0000",
    }

    with patch('domain.analysis.services.fx_metals_provider._request', return_value=mock_resp):
        snapshot = OpenErApiProvider().fetch()
        assert snapshot.source == "open_er_api"
        assert snapshot.values["usd"] == Decimal("49.50")
        # EUR/TRY = 49.50 / 0.89 =~ 55.6179
        assert float(snapshot.values["eur"]) > 55.0


@pytest.mark.unit
def test_fetch_weather_open_meteo_success():
    """_fetch_weather must prioritize Open-Meteo and format temperature with sign and degree."""
    with patch('infrastructure.background.background_service.os.makedirs'), \
         patch('infrastructure.background.background_service.BackgroundService._load_cache'):
        service = BackgroundService()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"current": {"temperature_2m": 16.4}}

        with patch('infrastructure.background.background_service.requests.get', return_value=mock_resp):
            weather = service._fetch_weather()
            assert weather == "+16°C"


@pytest.mark.unit
def test_single_instance_or_render_enables_web_background_service(monkeypatch):
    """In Render or single instance containers, Config must default background ownership to web."""
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.delenv("BACKGROUND_WORKER_OWNER", raising=False)
    monkeypatch.delenv("BACKGROUND_SERVICE_ENABLED", raising=False)

    from config import Config
    cfg = Config()
    assert cfg.BACKGROUND_WORKER_OWNER == "web"
    assert cfg.BACKGROUND_SERVICE_ENABLED is True
