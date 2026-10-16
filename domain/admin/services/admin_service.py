"""
Admin and Tenant Service Layer - Separates business logic from view routing.
Provides clean APIs for user management, tenant management, and admin stats.
"""

from datetime import datetime, timedelta, timezone
import logging
import re

from werkzeug.security import generate_password_hash

from models import Tenant, Transaction, User, db

logger = logging.getLogger(__name__)


def get_current_user_service(user_id):
    return db.session.get(User, user_id)


def get_user_or_raise(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise KeyError('Kullanıcı bulunamadı.')
    return user


# ─── USER MANAGEMENT SERVICES ──────────────────────────────────────────

def get_users_for_admin(current_user):
    """
    Returns users list based on admin role and tenant.
    sistem_yoneticisi: all users.
    tenant_yoneticisi: only users from their own tenant.
    """
    if current_user.role == 'sistem_yoneticisi':
        return User.query.order_by(User.id).all()
    else:
        return User.query.filter_by(tenant_id=current_user.tenant_id).order_by(User.id).all()


def create_user_service(current_user, username, password, role, tenant_id):
    """
    Creates a new user with validation and role constraints.
    """
    username = username.strip() if username else ''
    password = password.strip() if password else ''
    role = role.strip() if role else ''
    tenant_id = tenant_id.strip() if tenant_id else ''

    if not username:
        raise ValueError('Kullanıcı adı gereklidir.')

    if len(username) < 3:
        raise ValueError('Kullanıcı adı en az 3 karakter olmalıdır.')

    if not password:
        raise ValueError('Şifre gereklidir.')

    if not role:
        raise ValueError('Rol gereklidir.')

    if not tenant_id:
        raise ValueError('Tenant gereklidir.')

    valid_roles = ['sistem_yoneticisi', 'tenant_yoneticisi', 'kullanici']
    if role not in valid_roles:
        raise ValueError('Geçersiz rol.')

    # tenant_yoneticisi cannot assign sistem_yoneticisi
    if current_user.role == 'tenant_yoneticisi':
        if role == 'sistem_yoneticisi':
            raise ValueError('Tenant yöneticisi sistem yöneticisi atayamaz.')
        # tenant_yoneticisi can only create users in their own tenant
        tenant_id = current_user.tenant_id

    # Check if tenant exists
    tenant = db.session.get(Tenant, tenant_id)
    if not tenant:
        raise ValueError('Tenant bulunamadı.')

    # Check if username exists
    if User.query.filter_by(username=username).first():
        raise ValueError('Bu kullanıcı adı zaten kullanımda.')

    user = User(
        username=username,
        password=generate_password_hash(password),
        role=role,
        tenant_id=tenant_id,
        language='tr'
    )
    db.session.add(user)
    db.session.commit()
    logger.info("User created via service: %s by %s", username, current_user.username)
    return user


def update_user_service(current_user, user_id, username, password, role, tenant_id):
    """
    Updates an existing user.
    """
    target_user = db.session.get(User, user_id)
    if not target_user:
        raise KeyError('Kullanıcı bulunamadı.')

    # Authorization check for tenant_yoneticisi
    if current_user.role == 'tenant_yoneticisi' and target_user.tenant_id != current_user.tenant_id:
        raise PermissionError('Bu kullanıcıyı düzenleme yetkiniz yok.')

    username = username.strip() if username else ''
    password = password.strip() if password else ''
    role = role.strip() if role else ''
    tenant_id = tenant_id.strip() if tenant_id else ''

    if not username:
        raise ValueError('Kullanıcı adı gereklidir.')

    if not role:
        raise ValueError('Rol gereklidir.')

    if not tenant_id:
        raise ValueError('Tenant gereklidir.')

    valid_roles = ['sistem_yoneticisi', 'tenant_yoneticisi', 'kullanici']
    if role not in valid_roles:
        raise ValueError('Geçersiz rol.')

    if current_user.role == 'tenant_yoneticisi':
        if role == 'sistem_yoneticisi':
            raise ValueError('Tenant yöneticisi sistem yöneticisi atayamaz.')
        tenant_id = current_user.tenant_id

    tenant = db.session.get(Tenant, tenant_id)
    if not tenant:
        raise ValueError('Tenant bulunamadı.')

    # Username change check
    if username != target_user.username:
        if User.query.filter_by(username=username).first():
            raise ValueError('Bu kullanıcı adı zaten kullanımda.')
        target_user.username = username

    if password:
        target_user.password = generate_password_hash(password)

    target_user.role = role
    target_user.tenant_id = tenant_id
    db.session.commit()
    logger.info("User updated via service: %s by %s", target_user.username, current_user.username)
    return target_user


def delete_user_service(current_user, user_id):
    """
    Deletes a user.
    """
    target_user = db.session.get(User, user_id)
    if not target_user:
        raise KeyError('Kullanıcı bulunamadı.')

    if target_user.is_super_admin:
        raise ValueError(f'"{User.SUPER_ADMIN_USERNAME}" (platform sahibi) kullanıcısı silinemez.')

    if current_user.id == target_user.id:
        raise ValueError('Kendinizi silemezsiniz.')

    if current_user.role == 'tenant_yoneticisi' and target_user.tenant_id != current_user.tenant_id:
        raise PermissionError('Bu kullanıcıyı silme yetkiniz yok.')

    db.session.delete(target_user)
    db.session.commit()
    logger.info("User deleted via service: %s by %s", target_user.username, current_user.username)
    return True


# ─── TENANT MANAGEMENT SERVICES ────────────────────────────────────────

def get_all_tenants():
    """
    Returns all tenants.
    """
    return Tenant.query.order_by(Tenant.created_at.desc()).all()


def create_tenant_service(tenant_id, name, created_by=None):
    """
    Creates a new tenant.
    """
    name = name.strip() if name else ''
    tenant_id = tenant_id.strip() if tenant_id else ''

    if not name or not tenant_id:
        raise ValueError('Tenant adı ve ID gereklidir.')

    if not re.match(r'^[a-zA-Z0-9_-]+$', tenant_id):
        raise ValueError('Tenant ID sadece harf, rakam, tire ve alt çizgi içerebilir.')

    if len(tenant_id) > 50:
        raise ValueError('Tenant ID en fazla 50 karakter olabilir.')

    if len(name) > 100:
        raise ValueError('Tenant adı en fazla 100 karakter olabilir.')

    if db.session.get(Tenant, tenant_id) or Tenant.query.filter_by(id=tenant_id).first():
        raise ValueError('Bu tenant ID zaten kullanımda.')

    tenant = Tenant(
        id=tenant_id,
        name=name,
        status='active'
    )
    db.session.add(tenant)
    db.session.commit()
    logger.info("Tenant created via service: %s by %s", tenant_id, created_by)
    return tenant


def edit_tenant_service(tenant_id, name, updated_by=None):
    """
    Updates tenant name.
    """
    tenant = db.session.get(Tenant, tenant_id)
    if not tenant:
        raise KeyError('Tenant bulunamadı.')

    name = name.strip() if name else ''
    if not name:
        raise ValueError('Tenant adı gereklidir.')

    if len(name) > 100:
        raise ValueError('Tenant adı en fazla 100 karakter olabilir.')

    tenant.name = name
    db.session.commit()
    logger.info("Tenant updated via service: %s by %s", tenant_id, updated_by)
    return tenant


def update_tenant_status_service(tenant_id, status, updated_by=None):
    """
    Updates status of a tenant.
    """
    tenant = db.session.get(Tenant, tenant_id)
    if not tenant:
        raise KeyError('Tenant bulunamadı.')

    if status == 'deleted' and tenant_id == 'default':
        raise ValueError('Default tenant silinemez.')

    tenant.status = status
    db.session.commit()
    logger.info("Tenant status updated via service: %s to %s by %s", tenant_id, status, updated_by)
    return tenant


# ─── ADMIN STATS SERVICES ──────────────────────────────────────────────

def get_user_stats(current_user):
    """
    Returns user count metrics and distribution for admin dashboard and management.
    sistem_yoneticisi / super_admin: platform-wide statistics.
    tenant_yoneticisi: tenant-scoped statistics.
    """
    is_superadmin = (getattr(current_user, 'role', '') == 'sistem_yoneticisi' or getattr(current_user, 'is_super_admin', False))
    if is_superadmin:
        base_query = User.query
    else:
        tenant_id = getattr(current_user, 'tenant_id', None)
        base_query = User.query.filter_by(tenant_id=tenant_id)

    total_users = base_query.count()
    google_users = base_query.filter(User.auth_provider == 'GOOGLE').count()
    local_users = base_query.filter((User.auth_provider == 'LOCAL') | (User.auth_provider.is_(None))).count()
    admin_users = base_query.filter(User.role.in_(['sistem_yoneticisi', 'tenant_yoneticisi', 'yonetici', 'tenant_admin'])).count()
    standard_users = base_query.filter(User.role == 'kullanici').count()

    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    active_30d = base_query.filter(User.last_login_at >= thirty_days_ago).count()

    recent_objs = base_query.order_by(User.id.desc()).limit(5).all()
    recent_users = [
        {
            'id': u.id,
            'username': u.username,
            'email': u.email or '',
            'role': u.role,
            'auth_provider': u.auth_provider or 'LOCAL',
            'tenant_id': u.tenant_id,
            'last_login_at': u.last_login_at.strftime('%d.%m.%Y %H:%M') if u.last_login_at else '-'
        }
        for u in recent_objs
    ]

    return {
        'total_users': total_users,
        'google_users': google_users,
        'local_users': local_users,
        'admin_users': admin_users,
        'standard_users': standard_users,
        'active_30d': active_30d,
        'recent_users': recent_users,
        'is_superadmin': is_superadmin
    }


def get_admin_dashboard_stats(current_user):
    """
    Generates statistics for admin dashboard.
    """
    user_stats = get_user_stats(current_user)
    is_superadmin = (getattr(current_user, 'role', '') == 'sistem_yoneticisi' or getattr(current_user, 'is_super_admin', False))

    if is_superadmin:
        total_tenants = Tenant.query.count()
        active_tenants = Tenant.query.filter_by(status='active').count()
        total_transactions = Transaction.query.count()

        return {
            'total_users': user_stats['total_users'],
            'user_stats': user_stats,
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'total_transactions': total_transactions,
            'is_superadmin': True
        }
    else:
        tenant_transactions = Transaction.query.filter_by(tenant_id=current_user.tenant_id).count()

        return {
            'total_users': user_stats['total_users'],
            'user_stats': user_stats,
            'total_tenants': 1,
            'active_tenants': 1,
            'total_transactions': tenant_transactions,
            'is_superadmin': False
        }

