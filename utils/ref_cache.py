"""
Referans veri önbellekleme.
AssetType, AssetSector, Category gibi nadiren değişen listeler için.
Thread-safe, process-scoped in-memory cache.
"""
import threading
import time

_lock = threading.Lock()
_cache: dict = {}
_TTL_SECONDS = 300  # 5 dakika (bu değerler değiştirilmeyecek)


def get_cached(key: str, loader_fn, ttl: int = _TTL_SECONDS):
    """
    key için önbellekte varsa döndür, yoksa loader_fn çağır ve önbelleğe al.

    Kullanım:
        categories = get_cached('categories', lambda: Category.query.all())
    """
    with _lock:
        entry = _cache.get(key)
        if entry and (time.monotonic() - entry['ts']) < ttl:
            return entry['data']

    data = loader_fn()

    with _lock:
        _cache[key] = {'data': data, 'ts': time.monotonic()}

    return data


def invalidate(key: str):
    """Belirli bir cache key'ini geçersiz kılar (admin değişikliklerinden sonra çağır)."""
    with _lock:
        _cache.pop(key, None)


def invalidate_all():
    """Tüm cache'i temizler."""
    with _lock:
        _cache.clear()
