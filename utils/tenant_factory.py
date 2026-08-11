"""
Tenant-aware model factory.
tenant_id'si olan tüm modeller İÇİN bu fonksiyonlar kullanılmalı.
Doğrudan Model(...) çağrısı yerine bunlar tercih edilir; tenant_id'nin
unutulmasını yapısal olarak imkansız hale getirir.
"""
from domain.tenant.accessor import get_tenant as _get_tenant_from_context
from models import Asset, RecurringPlan, Transaction


def _resolve_tenant_id(explicit_tenant_id=None):
    """
    Öncelik sırası:
    1. Açıkça verilen tenant_id (örn. admin başka tenant için işlem yapıyorsa)
    2. g.tenant_id (normal request akışı — middleware tarafından set edilir)
    Hiçbiri yoksa: AÇIK HATA fırlat (sessizce None geçme — bu bug'ın asıl nedeniydi)
    """
    # Prefer an explicit tenant_id, otherwise fall back to TenantContext-compatible accessor
    tenant_id = explicit_tenant_id or _get_tenant_from_context()
    if not tenant_id:
        raise ValueError(
            "tenant_id belirlenemedi. g.tenant_id set edilmemiş veya "
            "fonksiyon request context dışında (örn. background thread) çağrılmış. "
            "Bu durumda tenant_id parametresi açıkça verilmelidir."
        )
    return tenant_id


def new_transaction(tenant_id=None, **kwargs):
    """Transaction oluştururken tenant_id otomatik/zorunlu atanır."""
    kwargs['tenant_id'] = _resolve_tenant_id(tenant_id)
    return Transaction(**kwargs)


def new_asset(tenant_id=None, **kwargs):
    kwargs['tenant_id'] = _resolve_tenant_id(tenant_id)
    return Asset(**kwargs)


def new_recurring_plan(tenant_id=None, **kwargs):
    kwargs['tenant_id'] = _resolve_tenant_id(tenant_id)
    return RecurringPlan(**kwargs)
