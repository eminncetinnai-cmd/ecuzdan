"""Financial Engine — engines/financial_engine.py.

Finansal hesaplama motoru, orkestrasyon ve önbellek katmanı.
Hesaplama mantığı domain/analysis/services/ altındaki servisler tarafından yürütülür;
bu modül önbellek yönetimini (TTL + tenant bazlı) ve geriye dönük uyumlu API arayüzünü sağlar.

Ana Fonksiyonlar:
  get_live_data()                  → Canlı USD/EUR/Altın/Hava durumu (BackgroundService'ten)
  get_financial_analysis()         → KPI hesaplama: likidite, borç oranı, tasarruf, skor
  get_monthly_dashboard_data()     → Dashboard için yıllık-aylık döküm
  get_asset_analysis()             → Varlık portföyü, risk ve likidite analizi
  get_financial_freedom_analysis() → Finansal özgürlük (FIRE) simülasyonu
  invalidate_financial_cache()     → Önbellek temizleme

NOT: Bu dosyaya Flask import ekleme — engine katmanı Flask'tan bağımsız olmalıdır.
"""
import importlib
import logging
import os
import time

from domain.analysis.services.helpers import _apply_tenant, _as_decimal, _safe_percentage
from domain.tenant.context import TenantContext
from shared.cache import CacheService, _get_redis_client
from utils.format_utils import format_date, format_money, parse_date_input, today_display, today_storage

logger = logging.getLogger(__name__)

# Canlı veri önbelleği
LIVE_DATA_CACHE = {
    "data": None,
    "last_fetched": 0,
}

# Finansal analiz önbelleği
FINANCIAL_ANALYSIS_CACHE = {
    "data": {},
    "last_fetched": {},
}

# Aylık dashboard önbelleği
MONTHLY_DASHBOARD_CACHE = {
    "data": {},
    "last_fetched": {},
}

# Varlık analizi önbelleği
ASSET_ANALYSIS_CACHE = {
    "data": {},
    "last_fetched": {},
}

# Finansal özgürlük analizi önbelleği
FREEDOM_ANALYSIS_CACHE = {
    "data": {},
    "last_fetched": {},
}

CACHE_TTL = 300  # 5 dakika önbellek süresi

_LAZY_EXPORTS = {
    "calculate_cash_trend": ("domain.analysis.services.cash_flow_service", "calculate_cash_trend"),
    "calculate_monthly_daily_balance": ("domain.analysis.services.cash_flow_service", "calculate_monthly_daily_balance"),
    "calculate_monthly_dashboard_data": ("domain.analysis.services.cash_flow_service", "calculate_monthly_dashboard_data"),
    "calculate_financial_analysis": ("domain.analysis.services.kpi_analysis_service", "calculate_financial_analysis"),
    "calculate_asset_analysis": ("domain.analysis.services.portfolio_analysis_service", "calculate_asset_analysis"),
    "calculate_financial_freedom_analysis": ("domain.analysis.services.financial_freedom_service", "calculate_financial_freedom_analysis"),
    "_resolve_freedom_assumptions": ("domain.analysis.services.financial_freedom_service", "_resolve_freedom_assumptions"),
    "get_dynamic_return_rate": ("domain.analysis.services.financial_freedom_service", "get_dynamic_return_rate"),
    "_years_to_financial_independence": ("domain.analysis.services.financial_freedom_service", "_years_to_financial_independence"),
    "_criterion_score": ("domain.analysis.services.financial_freedom_service", "_criterion_score"),
    "_status_from_score": ("domain.analysis.services.financial_freedom_service", "_status_from_score"),
    "_determine_freedom_stage": ("domain.analysis.services.financial_freedom_service", "_determine_freedom_stage"),
    "_determine_fire_profile": ("domain.analysis.services.financial_freedom_service", "_determine_fire_profile"),
    "get_empty_freedom_analysis": ("domain.analysis.services.financial_freedom_service", "get_empty_freedom_analysis"),
    "FI_MULTIPLIER": ("domain.analysis.services.financial_freedom_service", "FI_MULTIPLIER"),
    "SAFE_WITHDRAWAL_RATE": ("domain.analysis.services.financial_freedom_service", "SAFE_WITHDRAWAL_RATE"),
    "REAL_RETURN_RATE": ("domain.analysis.services.financial_freedom_service", "REAL_RETURN_RATE"),
    "DEFAULT_EMERGENCY_FUND_MONTHS": ("domain.analysis.services.financial_freedom_service", "DEFAULT_EMERGENCY_FUND_MONTHS"),
}


def __getattr__(name: str):
    if name in _LAZY_EXPORTS:
        module_path, attr_name = _LAZY_EXPORTS[name]
        module = importlib.import_module(module_path)
        val = getattr(module, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def _resolve_tenant_id(tenant_id: str | None = None) -> str | None:
    if tenant_id:
        return tenant_id
    return TenantContext.current()


INSTANCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance"))


def _record_invalidation_timestamp(tenant_id: str | None) -> None:
    """Çoklu worker (Gunicorn) süreçleri arasında önbellek geçersiz kılma zamanını diske işaretler."""
    try:
        os.makedirs(INSTANCE_DIR, exist_ok=True)
        marker_name = f".cache_inv_{tenant_id or 'global'}.ts"
        marker_path = os.path.join(INSTANCE_DIR, marker_name)
        with open(marker_path, "w", encoding="ascii") as f:
            f.write(str(time.time()))
    except Exception as exc:
        logger.debug("Failed to record cache invalidation timestamp: %s", exc)


def _get_invalidation_timestamp(tenant_id: str | None) -> float:
    """Belirtilen tenant için en son disk geçersiz kılma zaman damgasını döndürür."""
    try:
        ts = 0.0
        global_path = os.path.join(INSTANCE_DIR, ".cache_inv_global.ts")
        if os.path.exists(global_path):
            ts = max(ts, os.path.getmtime(global_path))
        if tenant_id:
            tenant_path = os.path.join(INSTANCE_DIR, f".cache_inv_{tenant_id}.ts")
            if os.path.exists(tenant_path):
                ts = max(ts, os.path.getmtime(tenant_path))
        return ts
    except Exception:
        return 0.0


def _is_cache_valid(cache: dict, key: str, tenant_id: str | None) -> bool:
    """Önbellek kaydının geçerli ve taze olup olmadığını denetler."""
    if key not in cache["data"]:
        return False
    cached_time = cache["last_fetched"].get(key, 0)
    current_time = time.time()
    if (current_time - cached_time) >= CACHE_TTL:
        return False
    if cached_time < _get_invalidation_timestamp(tenant_id):
        return False
    return True


def invalidate_financial_cache(tenant_id: str | None = None) -> None:
    """Finansal motor önbelleklerini temizler.

    tenant_id belirtilmişse o tenant'a ait önbellek girdilerini siler.
    tenant_id None ise tüm önbelleği temizler.
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    caches = [
        FINANCIAL_ANALYSIS_CACHE,
        MONTHLY_DASHBOARD_CACHE,
        ASSET_ANALYSIS_CACHE,
        FREEDOM_ANALYSIS_CACHE,
    ]
    for cache in caches:
        if tenant_id is None:
            cache["data"].clear()
            cache["last_fetched"].clear()
        else:
            keys_to_del = [
                k for k in list(cache["data"].keys())
                if k == tenant_id or str(k).startswith(f"{tenant_id}_")
            ]
            for k in keys_to_del:
                cache["data"].pop(k, None)
                cache["last_fetched"].pop(k, None)

    _record_invalidation_timestamp(tenant_id)

    try:
        if tenant_id is None:
            CacheService.clear()
        else:
            CacheService.delete(f"kpi:{tenant_id}")
            CacheService.delete(f"asset:{tenant_id}")
            CacheService.delete(f"monthly:{tenant_id}")
            CacheService.delete(f"freedom:{tenant_id}")
    except Exception:
        pass

    try:
        from domain.analysis.services.strategy_service import invalidate_strategy_cache
        invalidate_strategy_cache()
    except Exception:
        pass


def get_live_data() -> dict:
    """Canlı verileri (hava durumu, döviz, altın) arka plan servisinden getirir.

    Returns:
        dict: {"usd": str, "eur": str, "gold": str, "weather": str, "last_updated": str}
              Hata durumunda tüm değerler "--" döner.
    """
    try:
        from infrastructure.background.background_service import get_background_service
        return get_background_service().get_live_data()
    except Exception as e:
        logger.error(f"Canlı veri servisinden alınamadı: {e}")
        return {"weather": "--°C", "usd": "--", "eur": "--", "gold": "--", "last_updated": ""}


def get_financial_analysis(tenant_id: str | None = None) -> dict:
    """Kapsamlı finansal analiz hesaplamaları yapar.

    Likidite, borç oranı, tasarruf oranı, dayanıklılık ve finansal skor hesaplar.
    Önbellek kullanarak performansı optimize eder.
    """
    tenant_id = _resolve_tenant_id(tenant_id)

    # Önbellek kontrolü (cross-process ve TTL duyarlı)
    if _is_cache_valid(FINANCIAL_ANALYSIS_CACHE, tenant_id, tenant_id):
        return FINANCIAL_ANALYSIS_CACHE["data"][tenant_id]

    if _get_redis_client() is not None:
        try:
            redis_val = CacheService.get(f"kpi:{tenant_id}")
            if redis_val is not None:
                FINANCIAL_ANALYSIS_CACHE["data"][tenant_id] = redis_val
                FINANCIAL_ANALYSIS_CACHE["last_fetched"][tenant_id] = time.time()
                return redis_val
        except Exception:
            pass

    from domain.analysis.services.kpi_analysis_service import calculate_financial_analysis
    result = calculate_financial_analysis(tenant_id)

    # Önbelleğe kaydet
    FINANCIAL_ANALYSIS_CACHE["data"][tenant_id] = result
    FINANCIAL_ANALYSIS_CACHE["last_fetched"][tenant_id] = time.time()
    try:
        CacheService.set(f"kpi:{tenant_id}", result, ttl=CACHE_TTL)
    except Exception:
        pass

    return result


def get_monthly_dashboard_data(year, tenant_id=None):
    """Yıllık aylık dashboard verilerini hesaplar.

    Her ay için gelir, gider, yatırım ve net değer döner.
    Önbellek kullanarak performansı optimize eder.
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    cache_key = f"{tenant_id}_{year}"

    # Önbellek kontrolü (cross-process ve TTL duyarlı)
    if _is_cache_valid(MONTHLY_DASHBOARD_CACHE, cache_key, tenant_id):
        return MONTHLY_DASHBOARD_CACHE["data"][cache_key]

    if _get_redis_client() is not None:
        try:
            redis_val = CacheService.get(f"monthly:{cache_key}")
            if redis_val is not None:
                MONTHLY_DASHBOARD_CACHE["data"][cache_key] = redis_val
                MONTHLY_DASHBOARD_CACHE["last_fetched"][cache_key] = time.time()
                return redis_val
        except Exception:
            pass

    from domain.analysis.services.cash_flow_service import calculate_monthly_dashboard_data
    result = calculate_monthly_dashboard_data(year, tenant_id)

    # Önbelleğe kaydet
    MONTHLY_DASHBOARD_CACHE["data"][cache_key] = result
    MONTHLY_DASHBOARD_CACHE["last_fetched"][cache_key] = time.time()
    try:
        CacheService.set(f"monthly:{cache_key}", result, ttl=CACHE_TTL)
    except Exception:
        pass

    return result


def get_asset_analysis(tenant_id=None):
    """Profesyonel varlık analizi hesaplamaları.

    Portföy performansı, diversification, risk analizi gibi metrikleri döner.
    """
    tenant_id = _resolve_tenant_id(tenant_id)

    # Önbellek kontrolü (cross-process ve TTL duyarlı)
    if _is_cache_valid(ASSET_ANALYSIS_CACHE, tenant_id, tenant_id):
        return ASSET_ANALYSIS_CACHE["data"][tenant_id]

    if _get_redis_client() is not None:
        try:
            redis_val = CacheService.get(f"asset:{tenant_id}")
            if redis_val is not None:
                ASSET_ANALYSIS_CACHE["data"][tenant_id] = redis_val
                ASSET_ANALYSIS_CACHE["last_fetched"][tenant_id] = time.time()
                return redis_val
        except Exception:
            pass

    from domain.analysis.services.portfolio_analysis_service import calculate_asset_analysis
    result = calculate_asset_analysis(tenant_id)

    # Önbelleğe kaydet
    ASSET_ANALYSIS_CACHE["data"][tenant_id] = result
    ASSET_ANALYSIS_CACHE["last_fetched"][tenant_id] = time.time()
    try:
        CacheService.set(f"asset:{tenant_id}", result, ttl=CACHE_TTL)
    except Exception:
        pass

    return result


def get_financial_freedom_analysis(tenant_id=None, preferences=None):
    """Finansal özgürlük analizi — küresel FIRE/FI literatürüne dayalı çok kriterli değerlendirme.

    preferences: UserPreference satırı (opsiyonel). Verilmezse ya da alanları
    boşsa modül sabitleri (Trinity %4, 6 ay acil fon) kullanılır.
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    pref_key = (
        f"{getattr(preferences, 'id', None)}_"
        f"{getattr(preferences, 'safe_withdrawal_rate', None)}_"
        f"{getattr(preferences, 'emergency_fund_target_months', None)}_"
        f"{getattr(preferences, 'target_monthly_passive_income', None)}_"
        f"{getattr(preferences, 'target_retirement_year', None)}"
    ) if preferences else "default"
    cache_key = f"{tenant_id}_{pref_key}"

    # Önbellek kontrolü (cross-process ve TTL duyarlı)
    if _is_cache_valid(FREEDOM_ANALYSIS_CACHE, cache_key, tenant_id):
        return FREEDOM_ANALYSIS_CACHE["data"][cache_key]

    if _get_redis_client() is not None:
        try:
            redis_val = CacheService.get(f"freedom:{cache_key}")
            if redis_val is not None:
                FREEDOM_ANALYSIS_CACHE["data"][cache_key] = redis_val
                FREEDOM_ANALYSIS_CACHE["last_fetched"][cache_key] = time.time()
                return redis_val
        except Exception:
            pass

    from domain.analysis.services.financial_freedom_service import calculate_financial_freedom_analysis
    result = calculate_financial_freedom_analysis(tenant_id, preferences)

    # Önbelleğe kaydet
    FREEDOM_ANALYSIS_CACHE["data"][cache_key] = result
    FREEDOM_ANALYSIS_CACHE["last_fetched"][cache_key] = time.time()
    try:
        CacheService.set(f"freedom:{cache_key}", result, ttl=CACHE_TTL)
    except Exception:
        pass

    return result


# Re-exports for backward compatibility
__all__ = [
    'format_money',
    'format_date',
    'parse_date_input',
    'today_storage',
    'today_display',
    'get_financial_analysis',
    'get_monthly_dashboard_data',
    'get_asset_analysis',
    'get_financial_freedom_analysis',
    'invalidate_financial_cache',
    '_resolve_tenant_id',
    '_apply_tenant',
    '_as_decimal',
    '_safe_percentage',
    'get_live_data',
    'LIVE_DATA_CACHE',
    'FINANCIAL_ANALYSIS_CACHE',
    'MONTHLY_DASHBOARD_CACHE',
    'ASSET_ANALYSIS_CACHE',
    'FREEDOM_ANALYSIS_CACHE',
    'CACHE_TTL',
]
