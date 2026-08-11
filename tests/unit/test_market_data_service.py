"""
Unit Tests - Market Data Service
Market data service tests
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from market_data_service import MarketDataService, MARKET_ASSETS, CACHE_TTL


@pytest.mark.unit
def test_market_assets_constant():
    """Test MARKET_ASSETS constant structure"""
    assert isinstance(MARKET_ASSETS, dict)
    assert 'GC=F' in MARKET_ASSETS
    assert 'BTC-USD' in MARKET_ASSETS
    assert 'XU100.IS' in MARKET_ASSETS
    assert MARKET_ASSETS['GC=F']['name'] == 'Altın'
    assert MARKET_ASSETS['BTC-USD']['name'] == 'Bitcoin'
    assert MARKET_ASSETS['XU100.IS']['name'] == 'BIST100'


@pytest.mark.unit
def test_cache_ttl_constant():
    """Test CACHE_TTL constant"""
    assert CACHE_TTL == 3600


@pytest.mark.unit
def test_market_data_service_init():
    """Test MarketDataService initialization"""
    service = MarketDataService()
    assert hasattr(service, '_cache')
    assert hasattr(service, '_cache_timestamps')
    assert service._cache == {}
    assert service._cache_timestamps == {}


@pytest.mark.unit
def test_normalize_to_base_100_none():
    """Test normalize_to_base_100 with None data"""
    service = MarketDataService()
    result = service.normalize_to_base_100(None)
    assert result is None


@pytest.mark.unit
def test_normalize_to_base_100_empty():
    """Test normalize_to_base_100 with empty DataFrame"""
    service = MarketDataService()
    result = service.normalize_to_base_100(pd.DataFrame())
    assert result is None


@pytest.mark.unit
def test_normalize_to_base_100_valid():
    """Test normalize_to_base_100 with valid data"""
    service = MarketDataService()
    data = pd.DataFrame({'price': [100, 110, 120, 130]})
    result = service.normalize_to_base_100(data)
    
    assert result is not None
    assert 'normalized' in result.columns
    assert result['normalized'].iloc[0] == 100  # Base value should be 100


@pytest.mark.unit
def test_get_market_data_with_background_service():
    """Test get_market_data with background service"""
    service = MarketDataService()
    
    with patch('infrastructure.background.background_service.get_background_service') as mock_get_bg:
        mock_bg_service = Mock()
        mock_df = pd.DataFrame({'Close': [100, 110, 120]})
        mock_bg_service.get_market_data.return_value = mock_df
        mock_get_bg.return_value = mock_bg_service
        
        result = service.get_market_data('GC=F')
        
        assert result is not None
        mock_bg_service.get_market_data.assert_called_once_with('GC=F')


@pytest.mark.unit
def test_get_market_data_background_service_fallback():
    """Test get_market_data fallback when background service fails"""
    service = MarketDataService()
    
    with patch('infrastructure.background.background_service.get_background_service') as mock_get_bg:
        mock_get_bg.side_effect = Exception("Background service error")
        
        with patch('market_data_service.yf.download') as mock_download:
            mock_df = pd.DataFrame({'Close': [100, 110, 120]})
            mock_download.return_value = mock_df
            
            result = service.get_market_data('GC=F')
            
            assert result is not None
            assert 'price' in result.columns


@pytest.mark.unit
def test_get_market_data_both_fail():
    """Test get_market_data when both background service and yfinance fail"""
    service = MarketDataService()
    
    with patch('infrastructure.background.background_service.get_background_service') as mock_get_bg:
        mock_get_bg.side_effect = Exception("Background service error")
        
        with patch('market_data_service.yf.download') as mock_download:
            mock_download.side_effect = Exception("yfinance error")
            
            result = service.get_market_data('GC=F')
            
            assert result is None


@pytest.mark.unit
def test_get_all_market_data_with_background_service():
    """Test get_all_market_data with background service"""
    service = MarketDataService()
    
    with patch('infrastructure.background.background_service.get_background_service') as mock_get_bg:
        mock_bg_service = Mock()
        mock_data = {'GC=F': {'data': pd.DataFrame(), 'name': 'Altın', 'currency': 'USD'}}
        mock_bg_service.get_all_market_data.return_value = mock_data
        mock_get_bg.return_value = mock_bg_service
        
        result = service.get_all_market_data()
        
        assert result == mock_data
        mock_bg_service.get_all_market_data.assert_called_once()


@pytest.mark.unit
def test_get_all_market_data_background_service_fallback():
    """Test get_all_market_data fallback when background service fails"""
    service = MarketDataService()
    
    with patch('infrastructure.background.background_service.get_background_service') as mock_get_bg:
        mock_get_bg.side_effect = Exception("Background service error")
        
        with patch.object(service, 'get_market_data') as mock_get_market:
            mock_df = pd.DataFrame({'Close': [100, 110, 120]})
            mock_get_market.return_value = mock_df
            
            result = service.get_all_market_data()
            
            assert result is not None
            assert isinstance(result, dict)


@pytest.mark.unit
def test_market_data_service_logger():
    """Test MarketDataService has logger"""
    import market_data_service as mds
    assert hasattr(mds, 'logger')
    assert mds.logger is not None


@pytest.mark.unit
def test_market_data_service_module_structure():
    """Test market data service module structure"""
    import market_data_service as mds
    
    assert hasattr(mds, 'MarketDataService')
    assert hasattr(mds, 'MARKET_ASSETS')
    assert hasattr(mds, 'CACHE_TTL')
    assert hasattr(mds, 'logging')
    assert hasattr(mds, 'time')
    assert hasattr(mds, 'datetime')
    assert hasattr(mds, 'requests')
    assert hasattr(mds, 'yf')


@pytest.mark.unit
def test_market_assets_structure():
    """Test MARKET_ASSETS has expected structure"""
    for ticker, info in MARKET_ASSETS.items():
        assert 'name' in info
        assert 'currency' in info
        assert isinstance(info['name'], str)
        assert isinstance(info['currency'], str)
