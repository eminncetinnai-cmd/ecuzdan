"""
Unit Tests for shared/cache.py - Universal Hybrid Cache Adapter.
"""
import time
import pytest

from shared.cache import (
    CacheService,
    cache_get,
    cache_set,
    cache_get_or_set,
    cache_delete,
    cache_clear,
)


@pytest.fixture(autouse=True)
def clean_cache():
    CacheService.clear()
    yield
    CacheService.clear()


@pytest.mark.unit
def test_cache_set_and_get():
    CacheService.set("k1", {"number": 42, "text": "hello"})
    val = CacheService.get("k1")
    assert val == {"number": 42, "text": "hello"}


@pytest.mark.unit
def test_cache_miss_returns_none():
    val = CacheService.get("non_existent_key")
    assert val is None


@pytest.mark.unit
def test_cache_ttl_expiration():
    CacheService.set("short_lived", "value", ttl=1)
    assert CacheService.get("short_lived") == "value"
    time.sleep(1.1)
    assert CacheService.get("short_lived") is None


@pytest.mark.unit
def test_cache_delete():
    CacheService.set("to_delete", "active")
    assert CacheService.get("to_delete") == "active"
    CacheService.delete("to_delete")
    assert CacheService.get("to_delete") is None


@pytest.mark.unit
def test_cache_clear():
    CacheService.set("k1", 1)
    CacheService.set("k2", 2)
    CacheService.clear()
    assert CacheService.get("k1") is None
    assert CacheService.get("k2") is None


@pytest.mark.unit
def test_cache_get_or_set():
    calls = 0

    def compute():
        nonlocal calls
        calls += 1
        return "computed_result"

    res1 = CacheService.get_or_set("calc_key", compute, ttl=10)
    assert res1 == "computed_result"
    assert calls == 1

    res2 = CacheService.get_or_set("calc_key", compute, ttl=10)
    assert res2 == "computed_result"
    assert calls == 1  # Loader function should not be executed again


@pytest.mark.unit
def test_module_level_helpers():
    cache_set("h1", "val", ttl=5)
    assert cache_get("h1") == "val"
    cache_delete("h1")
    assert cache_get("h1") is None
