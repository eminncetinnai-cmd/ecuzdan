"""
Unit Tests - Background Service
Background Update Service for E-Cüzdan
"""

from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest


@pytest.mark.unit
def test_background_service_class_exists():
    """Test BackgroundService class exists"""
    from infrastructure.background.background_service import BackgroundService
    assert BackgroundService is not None


@pytest.mark.unit
def test_background_service_init():
    """Test BackgroundService initialization"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, '_lock')
            assert hasattr(service, '_live_data')
            assert hasattr(service, '_market_data')
            assert hasattr(service, '_stop_event')
            assert hasattr(service, '_thread')


@pytest.mark.unit
def test_background_service_module_structure():
    """Test background_service module structure"""
    import infrastructure.background.background_service as bg_service_module

    # Check for expected class
    assert hasattr(bg_service_module, 'BackgroundService')

    # Check for expected constants
    assert hasattr(bg_service_module, 'MARKET_ASSETS')
    assert hasattr(bg_service_module, 'LIVE_CACHE_FILE')
    assert hasattr(bg_service_module, 'MARKET_CACHE_FILE')

    # Check for expected functions
    assert hasattr(bg_service_module, 'get_background_service')
    assert hasattr(bg_service_module, 'get_background_service_instance')


@pytest.mark.unit
def test_market_assets_constant():
    """Test MARKET_ASSETS constant structure"""
    from infrastructure.background.background_service import MARKET_ASSETS

    assert isinstance(MARKET_ASSETS, dict)
    assert 'GC=F' in MARKET_ASSETS
    assert 'SI=F' in MARKET_ASSETS
    assert 'CL=F' in MARKET_ASSETS
    assert 'XU100.IS' in MARKET_ASSETS
    assert 'BTC-USD' in MARKET_ASSETS
    assert '^IXIC' in MARKET_ASSETS

    # Check structure of one entry
    assert 'name' in MARKET_ASSETS['GC=F']
    assert 'currency' in MARKET_ASSETS['GC=F']


@pytest.mark.unit
def test_get_live_data_method_exists():
    """Test get_live_data method exists"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, 'get_live_data')
            assert callable(service.get_live_data)


@pytest.mark.unit
def test_get_market_data_method_exists():
    """Test get_market_data method exists"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, 'get_market_data')
            assert callable(service.get_market_data)


@pytest.mark.unit
def test_get_all_market_data_method_exists():
    """Test get_all_market_data method exists"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, 'get_all_market_data')
            assert callable(service.get_all_market_data)


@pytest.mark.unit
def test_start_method_exists():
    """Test start method exists"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, 'start')
            assert callable(service.start)


@pytest.mark.unit
def test_stop_method_exists():
    """Test stop method exists"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, 'stop')
            assert callable(service.stop)


@pytest.mark.unit
def test_update_live_data_replaces_non_finite_quotes_with_missing_marker():
    """Header must not expose NaN or Infinity as financial quote values."""
    from infrastructure.background.background_service import BackgroundService

    def fake_get(url, **_kwargs):
        response = Mock()
        response.status_code = 200
        response.text = '20°C' if 'wttr.in' in url else (
            '<span data-socket-key="USD">nan</span>'
            '<span data-socket-key="EUR">Infinity</span>'
            '<span data-socket-key="XAU">NaN</span>'
        )
        return response

    with patch('infrastructure.background.background_service.os.makedirs'), \
         patch('infrastructure.background.background_service.BackgroundService._load_cache'), \
         patch('infrastructure.background.background_service.requests.get', side_effect=fake_get), \
         patch('infrastructure.background.background_service.yf.download', return_value=pd.DataFrame()):
        service = BackgroundService()
        service._live_data = {
            'weather': '21°C',
            'usd': 'nan',
            'eur': 'Infinity',
            'gold': 'NaN',
            'last_updated': '',
        }
        service._update_live_data()

    assert service._live_data['weather'] == '20°C'
    assert service._live_data['usd'] == '--'
    assert service._live_data['eur'] == '--'
    assert service._live_data['gold'] == '--'


@pytest.mark.unit
def test_get_live_data():
    """Test get_live_data returns live data dict and detects stale data"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._live_data = {"weather": "20°C", "usd": "32.50", "eur": "35.20", "gold": "2000.00", "last_updated": "2024-01-01"}

            result = service.get_live_data()

            assert result['weather'] == "20°C"
            assert result['usd'] == "32.50"
            assert result['eur'] == "35.20"
            assert result['gold'] == "2000.00"
            assert result['is_stale'] is True


@pytest.mark.unit
def test_get_live_data_fresh():
    """Test get_live_data marks recent data as not stale"""
    from datetime import datetime

    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._live_data = {
                "weather": "20°C",
                "usd": "32.50",
                "eur": "35.20",
                "gold": "2000.00",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            result = service.get_live_data()

            assert result['is_stale'] is False


@pytest.mark.unit
def test_get_market_data():
    """Test get_market_data returns None for non-existent ticker"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._market_data = {}

            result = service.get_market_data('NONEXISTENT')

            assert result is None


@pytest.mark.unit
def test_get_all_market_data():
    """Test get_all_market_data returns empty dict when no data"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._market_data = {}

            result = service.get_all_market_data()

            assert result == {}


@pytest.mark.unit
def test_get_background_service_singleton():
    """Test get_background_service returns singleton instance"""
    from infrastructure.background.background_service import BackgroundService, get_background_service

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            instance1 = get_background_service()
            instance2 = get_background_service()

            assert instance1 is instance2
            assert isinstance(instance1, BackgroundService)


@pytest.mark.unit
def test_get_background_service_instance():
    """Test get_background_service_instance returns current instance or None"""
    # Reset the singleton to test the "None" case
    import infrastructure.background.background_service as bg_module
    from infrastructure.background.background_service import (
        get_background_service_instance,
    )
    bg_module._background_service_instance = None

    result = get_background_service_instance()
    assert result is None


@pytest.mark.unit
def test_background_service_stop():
    """Test stop method sets stop event and joins thread"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._stop_event = Mock()
            service._thread = Mock()

            service.stop()

            service._stop_event.set.assert_called_once()
            service._thread.join.assert_called_once_with(timeout=3)


@pytest.mark.unit
def test_background_service_stop_with_exception():
    """Test stop handles thread join exception gracefully"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._stop_event = Mock()
            service._thread = Mock()
            service._thread.join.side_effect = Exception("Thread error")

            # Should not raise exception
            service.stop()

            service._stop_event.set.assert_called_once()


@pytest.mark.unit
def test_background_service_stop_without_thread():
    """Test stop handles None thread gracefully"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._stop_event = Mock()
            service._thread = None

            # Should not raise exception
            service.stop()

            service._stop_event.set.assert_called_once()


@pytest.mark.unit
def test_background_service_start_already_running():
    """Test start does nothing if thread is already running"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            mock_thread = Mock()
            mock_thread.is_alive.return_value = True
            service._thread = mock_thread

            service.start()

            # Should not start a new thread
            mock_thread.is_alive.assert_called_once()


@pytest.mark.unit
def test_save_cache():
    """Test _save_cache writes data to files"""

    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            service._live_data = {"test": "data"}
            service._market_data = {"ticker": {"data": {"index": [], "prices": []}, "name": "Test", "currency": "USD"}}

            mock_open = MagicMock()
            with patch('builtins.open', mock_open):
                service._save_cache()

                # Should have opened both files for writing
                assert mock_open.call_count >= 2


@pytest.mark.unit
def test_load_cache_no_files():
    """Test _load_cache handles missing cache files gracefully"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.os.path.exists', return_value=False):
            service = BackgroundService()

            # Should not raise exception
            assert service._live_data is not None
            assert service._market_data is not None


@pytest.mark.unit
def test_load_cache_with_files():
    """Test _load_cache loads data from existing files"""

    from infrastructure.background.background_service import BackgroundService

    mock_live_data = {"weather": "20°C", "usd": "32.50"}
    mock_market_data = {"GC=F": {"data": {"index": [], "prices": []}, "name": "Gold", "currency": "USD"}}

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                with patch('json.load', side_effect=[mock_live_data, mock_market_data]):
                    service = BackgroundService()

                    assert service._live_data == mock_live_data
                    assert service._market_data == mock_market_data


@pytest.mark.unit
def test_load_cache_with_json_error():
    """Test _load_cache handles JSON decode errors gracefully"""
    import json

    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                with patch('json.load', side_effect=json.JSONDecodeError("test", "", 0)):
                    service = BackgroundService()

                    # Should not raise exception, should use default values
                    assert service._live_data is not None


@pytest.mark.unit
def test_background_service_thread_safety():
    """Test BackgroundService uses thread lock"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, '_lock')
            assert service._lock is not None


@pytest.mark.unit
def test_background_service_initial_live_data():
    """Test BackgroundService initializes with default live data"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert 'weather' in service._live_data
            assert 'usd' in service._live_data
            assert 'eur' in service._live_data
            assert 'gold' in service._live_data
            assert 'last_updated' in service._live_data


@pytest.mark.unit
def test_background_service_initial_market_data():
    """Test BackgroundService initializes with empty market data"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert isinstance(service._market_data, dict)


@pytest.mark.unit
def test_background_service_stop_event():
    """Test BackgroundService uses threading.Event for stop signal"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, '_stop_event')
            assert service._stop_event is not None


@pytest.mark.unit
def test_background_service_thread_attribute():
    """Test BackgroundService has thread attribute"""
    from infrastructure.background.background_service import BackgroundService

    with patch('infrastructure.background.background_service.os.makedirs'):
        with patch('infrastructure.background.background_service.BackgroundService._load_cache'):
            service = BackgroundService()
            assert hasattr(service, '_thread')
            assert service._thread is None  # Initially None


@pytest.mark.unit
def test_background_service_constants_paths():
    """Test cache file path constants"""
    from infrastructure.background.background_service import LIVE_CACHE_FILE, MARKET_CACHE_FILE

    assert 'live_data_cache.json' in LIVE_CACHE_FILE
    assert 'market_data_cache.json' in MARKET_CACHE_FILE


@pytest.mark.unit
def test_background_service_market_assets_structure():
    """Test MARKET_ASSETS has correct structure for all entries"""
    from infrastructure.background.background_service import MARKET_ASSETS

    for ticker, data in MARKET_ASSETS.items():
        assert isinstance(ticker, str)
        assert isinstance(data, dict)
        assert 'name' in data
        assert 'currency' in data
        assert isinstance(data['name'], str)
        assert isinstance(data['currency'], str)
