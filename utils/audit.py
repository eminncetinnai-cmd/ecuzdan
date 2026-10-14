"""
Audit Trail yardımcı modülü.

Kullanım (herhangi bir route veya service içinde):
    from utils.audit import audit_log
    audit_log('LOGIN', user_id=user.id, username=user.username, tenant_id=user.tenant_id)

Kurallar:
    - Bu fonksiyon SADECE INSERT yapar; hiçbir zaman AuditLog güncellenmez/silinmez.
    - Hata durumunda sessizce devam eder — audit hatası asıl iş akışını durdurmamalı.
    - ip_address ve user_agent Flask request context'ten otomatik alınır.
"""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Kayıt altına alınacak canonical action adları
ACTION_LOGIN          = 'LOGIN'
ACTION_LOGOUT         = 'LOGOUT'
ACTION_REGISTER       = 'REGISTER'
ACTION_TENANT_CREATED = 'TENANT_CREATED'
ACTION_DATA_EXPORT    = 'DATA_EXPORT'
ACTION_RESET_DATA     = 'RESET_DATA'
ACTION_ROLE_CHANGED   = 'ROLE_CHANGED'
ACTION_USER_DELETED   = 'USER_DELETED'
ACTION_INVITE_CREATED = 'INVITE_CREATED'
ACTION_LOGIN_FAILED   = 'LOGIN_FAILED'
ACTION_PW_CHANGED     = 'PASSWORD_CHANGED'
ACTION_SPECIAL_CODE_APPLIED = 'SPECIAL_CODE_APPLIED'
ACTION_SPECIAL_CODE_FAILED  = 'SPECIAL_CODE_FAILED'
ACTION_CAPABILITY_DENIED    = 'CAPABILITY_DENIED'


def audit_log(
    action: str,
    *,
    user_id=None,
    username: str = None,
    tenant_id: str = None,
    entity_type: str = None,
    entity_id=None,
    details: dict = None,
) -> None:
    """
    Denetim kaydı yazar. Hata durumunda exception fırlatmaz.

    Args:
        action:      Canonical action adı (ACTION_* sabitlerinden biri kullanılmalı).
        user_id:     İşlemi yapan kullanıcının DB id'si.
        username:    Snapshot olarak saklanır (kullanıcı silinse bile kalır).
        tenant_id:   Tenant izolasyonu için.
        entity_type: Etkilenen kayıt türü ('user', 'transaction', 'tenant' …).
        entity_id:   Etkilenen kaydın id'si.
        details:     Ek bilgi dict'i — JSON olarak saklanır.
    """
    try:
        from models import AuditLog, db

        ip_address = None
        user_agent = None
        try:
            from flask import request as req
            ip_address = req.remote_addr
            ua = req.headers.get('User-Agent', '')
            user_agent = ua[:300] if ua else None
        except RuntimeError:
            pass  # Flask request context dışında

        entry = AuditLog(
            action=action,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.session.add(entry)
        db.session.flush()   # ID al ama commit'i caller'a bırak

    except Exception as exc:
        logger.warning("audit_log yazılamadı (action=%s): %s", action, exc)
        try:
            from models import db
            db.session.rollback()
        except Exception:
            pass
