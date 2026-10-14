"""
E-Cüzdan Hibrit ve Dağıtık Önbellekleme Adaptörü (shared/cache.py).

Hem yerel (in-memory) hem de kurumsal / dağıtık (Redis) arka uçları
aynı arayüz altında şeffafça destekler.

- Yerel Mod: Thread-safe in-memory sözlük (varsayılan)
- Kurumsal/Bulut Mod: REDIS_URL veya RATELIMIT_STORAGE_URI tanımlı olduğunda Redis üzerinden çalışır
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

_local_lock = threading.Lock()
_local_cache: dict[str, dict[str, Any]] = {}
_redis_client = None
_redis_initialized = False


def _get_redis_client():
    global _redis_client, _redis_initialized
    if _redis_initialized:
        return _redis_client

    _redis_initialized = True
    redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_REDIS_URL")
    if not redis_url:
        ratelimit_uri = os.getenv("RATELIMIT_STORAGE_URI", "")
        if ratelimit_uri.startswith("redis://") or ratelimit_uri.startswith("rediss://"):
            redis_url = ratelimit_uri

    if redis_url:
        try:
            import redis
            _redis_client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
            _redis_client.ping()
            logger.info("Dağıtık önbellek (Redis) başarıyla bağlandı: %s", redis_url)
        except Exception as exc:
            logger.warning("Redis önbellek bağlantısı başarısız, bellek içi önbelleğe dönülüyor: %s", exc)
            _redis_client = None
    return _redis_client


class CacheService:
    """Evrensel önbellekleme servisi."""

    @staticmethod
    def get(key: str) -> Any:
        client = _get_redis_client()
        if client:
            try:
                raw = client.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception as exc:
                logger.debug("Redis get hatası (%s): %s", key, exc)

        with _local_lock:
            entry = _local_cache.get(key)
            if entry and (time.monotonic() - entry["ts"]) < entry["ttl"]:
                return entry["data"]
            elif entry:
                _local_cache.pop(key, None)
        return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> None:
        client = _get_redis_client()
        if client:
            try:
                client.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception as exc:
                logger.debug("Redis set hatası (%s): %s", key, exc)

        with _local_lock:
            _local_cache[key] = {
                "data": value,
                "ts": time.monotonic(),
                "ttl": ttl,
            }

    @classmethod
    def get_or_set(cls, key: str, loader_fn: Callable[[], Any], ttl: int = 300) -> Any:
        cached_val = cls.get(key)
        if cached_val is not None:
            return cached_val

        data = loader_fn()
        cls.set(key, data, ttl=ttl)
        return data

    @staticmethod
    def delete(key: str) -> None:
        client = _get_redis_client()
        if client:
            try:
                client.delete(key)
            except Exception:
                pass

        with _local_lock:
            _local_cache.pop(key, None)

    @staticmethod
    def clear() -> None:
        client = _get_redis_client()
        if client:
            try:
                client.flushdb()
            except Exception:
                pass

        with _local_lock:
            _local_cache.clear()


# Modül düzeyinde pratik yardımcılar
cache_get = CacheService.get
cache_set = CacheService.set
cache_get_or_set = CacheService.get_or_set
cache_delete = CacheService.delete
cache_clear = CacheService.clear
