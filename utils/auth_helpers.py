"""
Auth Helpers - Authentication ve Authorization Utilities
Flask uygulaması için konsolide edilmiş auth decorator'ları ve yardımcı fonksiyonlar
"""

import logging
from functools import wraps

from flask import flash, g, jsonify, redirect, request, session, url_for

# TenantContext integration
from domain.tenant.context import TenantContext
from infrastructure.i18n import i18n
from models import User, db
from utils.capabilities import Capability, has_capability, has_full_platform_access

logger = logging.getLogger(__name__)


def resolve_from_request() -> str | None:
    """Try common request-based locations for tenant id."""
    try:
        if hasattr(request, 'tenant_id') and request.tenant_id:
            return request.tenant_id
    except Exception:
        pass
    try:
        header = request.headers.get('X-Tenant-ID') if hasattr(request, 'headers') else None
        if header:
            return header
    except Exception:
        pass
    try:
        arg = request.args.get('tenant_id') if hasattr(request, 'args') else None
        if arg:
            return arg
    except Exception:
        pass
    try:
        if g is not None:
            val = getattr(g, 'tenant_id', None)
            if val:
                return val
    except Exception:
        pass
    return None


def login_required(f):
    """
    Oturum zorunluluğu — mevcut implementasyonu bozmadan wrap et
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def require_role(*roles):
    """
    Rol bazlı erişim kontrolü.
    Kullanım: @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    GET ve POST için ayrı decorator KULLANMA — tek decorator yeterli.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))

            user = get_current_user()
            if not user:
                flash(i18n.gettext("ui_auto_fd71ebc8847d"), 'error')
                return redirect(url_for('auth.login'))

            if user.role not in roles and not has_full_platform_access(user):
                flash(i18n.gettext("ui_auto_4ee468fbbd2b"), 'error')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """
    session'dan User nesnesini döndürür, cache'li
    """
    if 'user_id' not in session:
        return None

    # g'de cache'li var mı?
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user

    # DB'den çek
    user = db.session.get(User, session['user_id'])
    if user:
        g.current_user = user
    return user


def set_tenant_context():
    """
    before_request hook için.
    g.tenant_id ve g.current_user'ı set eder. Ayrıca TenantContext'i günceller.
    Returns a Flask response (redirect) if auth cleanup is needed, otherwise None.
    """
    # Clear any previous context first for safety
    try:
        TenantContext.set(None)
    except (AttributeError, RuntimeError):
        pass

    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            g.current_user = user
            g.tenant_id = user.tenant_id
            # Set TenantContext from user
            try:
                TenantContext.set(user.tenant_id)
            except (AttributeError, RuntimeError):
                pass
        else:
            # Kullanıcı silinmiş olabilir. HTML akışında login'e yönlendir; API
            # istemcilerinde redirect yerine makinece işlenebilir 401 dön.
            session.clear()
            if request.endpoint == 'transactions.api_transactions':
                return jsonify({
                    'success': False,
                    'error_code': 'authentication_required',
                    'message': 'Oturum gerekli.',
                }), 401
            flash(i18n.gettext("ui_auto_62da31fe107e"), 'warning')
            return redirect(url_for('auth.login'))

    else:
        # No authenticated user — attempt to resolve tenant from request headers/args/g
        try:
            resolved = resolve_from_request()
            if resolved:
                # Do not modify g (preserve old behavior). Only set TenantContext so background code can use it.
                try:
                    TenantContext.set(resolved)
                except (AttributeError, RuntimeError):
                    pass
        except (AttributeError, KeyError, ValueError):
            # Swallow resolver errors to avoid breaking requests
            pass


def capability_required(*capabilities):
    """Require every named capability for an authenticated request."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))

            user = db.session.get(User, session['user_id'])
            if not user:
                flash(i18n.gettext("ui_auto_fd71ebc8847d"), 'error')
                return redirect(url_for('auth.login'))

            if not all(has_capability(user, capability) for capability in capabilities):
                flash(i18n.gettext("ui_auto_100ea0058791"), 'error')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def superadmin_required(f):
    """Require Emin-level platform access, including redeemed full-access codes."""
    return capability_required(Capability.FULL_PLATFORM_ACCESS)(f)


def tenant_admin_required(f):
    """
    Sistem yöneticisi veya tenant admin için shortcut.
    Canonical rol: 'tenant_admin'  (eskiden 'tenant_yoneticisi' olarak da kullanılıyordu).
    Her ikisi de kabul edilir.
    """
    return require_role('sistem_yoneticisi', 'tenant_admin', 'tenant_yoneticisi')(f)


def normalize_role(role: str) -> str:
    """
    Geriye dönük uyumluluk için eski rol isimlerini canonical forma dönüştürür.
    Canonical rol seti:
        sistem_yoneticisi  → en yetkili, global platform admin
        yonetici           → tenant içi tam yetki
        tenant_admin       → tenant kullanıcı/davet yöneticisi
        kullanici          → standart kullanıcı
    """
    _LEGACY_MAP = {
        'tenant_yoneticisi': 'tenant_admin',   # eski ad → yeni canonical
        'admin':              'yonetici',       # olası karışıklık
    }
    return _LEGACY_MAP.get(role, role)
