"""
Unit Tests - Ref Cache
Reference data caching for rarely changing lists
"""

import pytest
import time
import threading
from utils.ref_cache import (
    get_cached,
    invalidate,
    invalidate_all,
    _cache,
    _lock,
    _TTL_SECONDS,
)


@pytest.mark.unit
def test_get_cached_cache_miss():
    """Test get_cached with cache miss"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    result = get_cached('test_key', loader_fn)
    
    assert result == "loaded_value"
    assert call_count == 1


@pytest.mark.unit
def test_get_cached_cache_hit():
    """Test get_cached with cache hit"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # First call - cache miss
    result1 = get_cached('test_key', loader_fn)
    assert result1 == "loaded_value"
    assert call_count == 1
    
    # Second call - cache hit
    result2 = get_cached('test_key', loader_fn)
    assert result2 == "loaded_value"
    assert call_count == 1  # Should not call loader again


@pytest.mark.unit
def test_get_cached_ttl_expiration():
    """Test get_cached with TTL expiration"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # First call
    result1 = get_cached('test_key', loader_fn, ttl=1)
    assert result1 == "loaded_value"
    assert call_count == 1
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Second call after TTL - should reload
    result2 = get_cached('test_key', loader_fn, ttl=1)
    assert result2 == "loaded_value"
    assert call_count == 2


@pytest.mark.unit
def test_get_cached_custom_ttl():
    """Test get_cached with custom TTL"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # Use custom TTL of 2 seconds
    result = get_cached('test_key', loader_fn, ttl=2)
    
    assert result == "loaded_value"
    assert call_count == 1


@pytest.mark.unit
def test_invalidate():
    """Test invalidate specific key"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # Load cache
    result1 = get_cached('test_key', loader_fn)
    assert result1 == "loaded_value"
    assert call_count == 1
    
    # Invalidate
    invalidate('test_key')
    
    # Should reload after invalidate
    result2 = get_cached('test_key', loader_fn)
    assert result2 == "loaded_value"
    assert call_count == 2


@pytest.mark.unit
def test_invalidate_nonexistent_key():
    """Test invalidate with nonexistent key (should not error)"""
    # Should not raise exception
    invalidate('nonexistent_key')


@pytest.mark.unit
def test_invalidate_all():
    """Test invalidate_all clears all cache"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # Load multiple keys
    get_cached('key1', loader_fn)
    get_cached('key2', loader_fn)
    assert call_count == 2
    
    # Invalidate all
    invalidate_all()
    
    # Should reload after invalidate_all
    get_cached('key1', loader_fn)
    get_cached('key2', loader_fn)
    assert call_count == 4


@pytest.mark.unit
def test_ref_cache_imports():
    """Test that ref_cache functions can be imported"""
    from utils.ref_cache import (
        get_cached,
        invalidate,
        invalidate_all,
    )
    
    assert callable(get_cached)
    assert callable(invalidate)
    assert callable(invalidate_all)


@pytest.mark.unit
def test_ref_cache_module_structure():
    """Test ref_cache module structure"""
    import utils.ref_cache as ref_cache_module
    
    # Check for expected functions
    assert hasattr(ref_cache_module, 'get_cached')
    assert hasattr(ref_cache_module, 'invalidate')
    assert hasattr(ref_cache_module, 'invalidate_all')
    
    # Check for expected imports
    assert hasattr(ref_cache_module, 'threading')
    assert hasattr(ref_cache_module, 'time')


@pytest.mark.unit
def test_ref_cache_constants():
    """Test ref_cache module constants"""
    from utils.ref_cache import _TTL_SECONDS
    
    assert _TTL_SECONDS == 300  # 5 minutes


@pytest.mark.unit
def test_ref_cache_lock_exists():
    """Test ref_cache has lock for thread safety"""
    from utils.ref_cache import _lock
    
    assert isinstance(_lock, threading.Lock)


@pytest.mark.unit
def test_ref_cache_cache_dict_exists():
    """Test ref_cache has cache dictionary"""
    from utils.ref_cache import _cache
    
    assert isinstance(_cache, dict)


@pytest.mark.unit
def test_ref_cache_module_has_required_imports():
    """Test ref_cache module has required imports"""
    import utils.ref_cache as ref_cache_module
    
    # Standard library imports
    assert hasattr(ref_cache_module, 'threading')
    assert hasattr(ref_cache_module, 'time')


@pytest.mark.unit
def test_get_cached_different_keys():
    """Test get_cached with different keys"""
    invalidate_all()  # Clear cache first
    
    def loader_fn1():
        return "value1"
    
    def loader_fn2():
        return "value2"
    
    result1 = get_cached('key1', loader_fn1)
    result2 = get_cached('key2', loader_fn2)
    
    assert result1 == "value1"
    assert result2 == "value2"


@pytest.mark.unit
def test_get_cached_none_value():
    """Test get_cached with None value from loader"""
    invalidate_all()  # Clear cache first
    
    def loader_fn():
        return None
    
    result = get_cached('test_key', loader_fn)
    
    assert result is None


@pytest.mark.unit
def test_get_cached_complex_value():
    """Test get_cached with complex value (dict, list)"""
    invalidate_all()  # Clear cache first
    
    def loader_fn():
        return {'key': 'value', 'list': [1, 2, 3]}
    
    result = get_cached('test_key', loader_fn)
    
    assert result == {'key': 'value', 'list': [1, 2, 3]}


@pytest.mark.unit
def test_get_cached_zero_ttl():
    """Test get_cached with zero TTL (always reloads)"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # With zero TTL, should always reload
    result1 = get_cached('test_key', loader_fn, ttl=0)
    assert call_count == 1
    
    result2 = get_cached('test_key', loader_fn, ttl=0)
    assert call_count == 2


@pytest.mark.unit
def test_invalidate_all_empty_cache():
    """Test invalidate_all on empty cache (should not error)"""
    invalidate_all()  # Clear cache first
    invalidate_all()  # Should not raise exception


@pytest.mark.unit
def test_thread_safety_basic():
    """Test basic thread safety with concurrent access"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        time.sleep(0.01)  # Simulate slow operation
        return "loaded_value"
    
    threads = []
    results = []
    
    def worker():
        result = get_cached('test_key', loader_fn)
        results.append(result)
    
    # Create multiple threads
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # All should get the same value
    assert all(r == "loaded_value" for r in results)


@pytest.mark.unit
def test_get_cached_default_ttl():
    """Test get_cached uses default TTL when not specified"""
    invalidate_all()  # Clear cache first
    
    call_count = 0
    def loader_fn():
        nonlocal call_count
        call_count += 1
        return "loaded_value"
    
    # Use default TTL
    result = get_cached('test_key', loader_fn)
    
    assert result == "loaded_value"
    assert call_count == 1
