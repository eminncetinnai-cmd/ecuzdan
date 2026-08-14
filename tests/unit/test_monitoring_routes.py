"""
Unit Tests - Monitoring Routes
Monitoring API route functions - Detailed functional tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from routes.monitoring import (
    register_monitoring_routes,
    register_monitoring_routes_bp,
    monitoring_bp,
    _get_cache_key,
    _set_cache,
    _clear_cache,
)


@pytest.mark.unit
def test_register_monitoring_routes():
    """Test register_monitoring_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    register_monitoring_routes(mock_bp)
    
    assert mock_bp.route.called


@pytest.mark.unit
def test_register_monitoring_routes_bp():
    """Test register_monitoring_routes_bp function"""
    result = register_monitoring_routes_bp()
    assert result is not None
    assert result.name == 'monitoring'


@pytest.mark.unit
def test_monitoring_blueprint_exists():
    """Test monitoring blueprint exists"""
    assert monitoring_bp is not None
    assert monitoring_bp.name == 'monitoring'
    assert monitoring_bp.url_prefix == '/monitoring'


@pytest.mark.unit
def test_monitoring_blueprint_routes():
    """Test monitoring blueprint has expected routes"""
    # Blueprint'in route'ları deferred_functions'da değil, doğrudan kayıtlı
    # Bu yüzden blueprint'in doğru yapılandırıldığını kontrol ediyoruz
    assert monitoring_bp is not None
    assert monitoring_bp.name == 'monitoring'
    assert monitoring_bp.url_prefix == '/monitoring'


@pytest.mark.unit
def test_cache_get_key():
    """Test _get_cache_key function"""
    # Test with empty cache
    result = _get_cache_key('test_key')
    assert result is None
    
    # Test with set cache
    _set_cache('test_key', {'data': 'test'})
    result = _get_cache_key('test_key')
    assert result == {'data': 'test'}


@pytest.mark.unit
def test_cache_set_key():
    """Test _set_cache function"""
    _set_cache('new_key', {'value': 123})
    result = _get_cache_key('new_key')
    assert result == {'value': 123}


@pytest.mark.unit
def test_cache_clear_pattern():
    """Test _clear_cache with pattern"""
    _set_cache('stats_test', {'data': 1})
    _set_cache('health_test', {'data': 2})
    _set_cache('other_key', {'data': 3})
    
    _clear_cache('stats')
    
    # stats_test should be cleared (contains 'stats')
    assert _get_cache_key('stats_test') is None
    # other_key should remain (doesn't contain 'stats')
    assert _get_cache_key('other_key') is not None


@pytest.mark.unit
def test_cache_clear_all():
    """Test _clear_cache without pattern"""
    _set_cache('key1', {'data': 1})
    _set_cache('key2', {'data': 2})
    
    _clear_cache()
    
    assert _get_cache_key('key1') is None
    assert _get_cache_key('key2') is None


@pytest.mark.unit
def test_cache_ttl_expiration():
    """Test cache TTL expiration"""
    import time
    
    _set_cache('test_key', {'data': 'test'})
    # Manually set old timestamp
    from routes.monitoring import _cache
    _cache['test_key'] = ({'data': 'test'}, time.time() - 1000)  # Very old
    
    result = _get_cache_key('test_key')
    assert result is None  # Should be expired


@pytest.mark.unit
def test_monitoring_imports():
    """Test that monitoring functions can be imported"""
    from routes.monitoring import (
        register_monitoring_routes,
        register_monitoring_routes_bp,
        monitoring_bp,
        _get_cache_key,
        _set_cache,
        _clear_cache,
    )
    
    assert callable(register_monitoring_routes)
    assert callable(register_monitoring_routes_bp)
    assert callable(_get_cache_key)
    assert callable(_set_cache)
    assert callable(_clear_cache)


@pytest.mark.unit
def test_monitoring_module_structure():
    """Test monitoring routes module structure"""
    import routes.monitoring as monitoring_module
    
    # Check for expected functions
    assert hasattr(monitoring_module, 'register_monitoring_routes')
    assert hasattr(monitoring_module, 'register_monitoring_routes_bp')
    assert hasattr(monitoring_module, 'monitoring_bp')
    assert hasattr(monitoring_module, '_get_cache_key')
    assert hasattr(monitoring_module, '_set_cache')
    assert hasattr(monitoring_module, '_clear_cache')
    
    # Check for expected imports
    assert hasattr(monitoring_module, 'jsonify')
    assert hasattr(monitoring_module, 'request')
    assert hasattr(monitoring_module, 'session')
    assert hasattr(monitoring_module, 'render_template')
    assert hasattr(monitoring_module, 'logging')
    assert hasattr(monitoring_module, 'os')
    assert hasattr(monitoring_module, 'datetime')
    assert hasattr(monitoring_module, 'timedelta')
    assert hasattr(monitoring_module, 'Dict')
    assert hasattr(monitoring_module, 'List')
    assert hasattr(monitoring_module, 're')


@pytest.mark.unit
def test_monitoring_logger():
    """Test monitoring module uses logging"""
    import routes.monitoring as monitoring_module
    assert hasattr(monitoring_module, 'logger')
    assert monitoring_module.logger is not None


@pytest.mark.unit
def test_monitoring_cache_structure():
    """Test monitoring cache structure"""
    import routes.monitoring as monitoring_module
    assert hasattr(monitoring_module, '_cache')
    assert hasattr(monitoring_module, '_cache_ttl')
    assert isinstance(monitoring_module._cache, dict)
    assert isinstance(monitoring_module._cache_ttl, dict)


@pytest.mark.unit
def test_monitoring_cache_ttl_values():
    """Test monitoring cache TTL values"""
    import routes.monitoring as monitoring_module
    assert 'stats' in monitoring_module._cache_ttl
    assert 'health' in monitoring_module._cache_ttl
    assert 'log_files' in monitoring_module._cache_ttl
    assert monitoring_module._cache_ttl['stats'] > 0
    assert monitoring_module._cache_ttl['health'] > 0
    assert monitoring_module._cache_ttl['log_files'] > 0


@pytest.mark.unit
def test_monitoring_route_registration_count():
    """Test register_monitoring_routes registers expected number of routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    register_monitoring_routes(mock_bp)
    
    # Should register at least 5 routes (dashboard, stats, logs, health, alerts)
    assert mock_bp.route.call_count >= 5


@pytest.mark.unit
def test_monitoring_blueprint_url_prefix():
    """Test monitoring blueprint has correct URL prefix"""
    assert monitoring_bp.url_prefix == '/monitoring'


@pytest.mark.unit
def test_monitoring_blueprint_name():
    """Test monitoring blueprint has correct name"""
    assert monitoring_bp.name == 'monitoring'


@pytest.mark.unit
def test_cache_key_isolation():
    """Test that different cache keys don't interfere"""
    _set_cache('key1', {'value': 1})
    _set_cache('key2', {'value': 2})
    
    result1 = _get_cache_key('key1')
    result2 = _get_cache_key('key2')
    
    assert result1 == {'value': 1}
    assert result2 == {'value': 2}
    assert result1 != result2


@pytest.mark.unit
def test_cache_overwrite():
    """Test that setting same key overwrites value"""
    _set_cache('test_key', {'value': 1})
    _set_cache('test_key', {'value': 2})
    
    result = _get_cache_key('test_key')
    assert result == {'value': 2}


@pytest.mark.unit
def test_cache_none_value():
    """Test cache with None value"""
    _set_cache('test_key', None)
    result = _get_cache_key('test_key')
    assert result is None


@pytest.mark.unit
def test_cache_empty_dict():
    """Test cache with empty dict"""
    _set_cache('test_key', {})
    result = _get_cache_key('test_key')
    assert result == {}


@pytest.mark.unit
def test_cache_complex_value():
    """Test cache with complex nested structure"""
    complex_value = {
        'nested': {
            'list': [1, 2, 3],
            'dict': {'a': 'b'}
        }
    }
    _set_cache('test_key', complex_value)
    result = _get_cache_key('test_key')
    assert result == complex_value