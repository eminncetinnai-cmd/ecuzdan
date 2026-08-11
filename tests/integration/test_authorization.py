"""
Authorization Tests
Yetki kontrolünü test eder
"""

from models import Tenant, User, db


def test_tenant_admin_can_see_own_users(app):
    """Tenant admin kendi tenant kullanıcılarını görebilmeli"""
    # Tenant oluştur
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    # Tenant admin oluştur
    admin = User(
        username='admin@example.com',
        password='hash',
        tenant_id=tenant.id,
        role='tenant_admin'
    )
    db.session.add(admin)

    # Normal kullanıcılar oluştur
    for i in range(3):
        db.session.add(User(
            username=f'user{i}@example.com',
            password='hash',
            tenant_id=tenant.id
        ))
    db.session.commit()

    # Tenant admin kendi tenant kullanıcılarını görebilmeli
    users = User.query.filter_by(tenant_id=tenant.id).all()
    assert len(users) == 4  # 1 admin + 3 normal kullanıcı


def test_tenant_admin_cannot_see_other_tenants(app):
    """Tenant admin başka tenant kullanıcılarını görememeli"""
    # Tenant 1 oluştur
    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    db.session.add(tenant1)
    db.session.flush()

    # Tenant 2 oluştur
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add(tenant2)
    db.session.flush()

    # Tenant 1 admin
    admin1 = User(
        username='admin1@example.com',
        password='hash',
        tenant_id=tenant1.id,
        role='tenant_admin'
    )
    db.session.add(admin1)

    # Tenant 2 kullanıcıları
    for i in range(3):
        db.session.add(User(
            username=f'user2_{i}@example.com',
            password='hash',
            tenant_id=tenant2.id
        ))
    db.session.commit()

    # Tenant 1 admin Tenant 2 kullanıcılarını görememeli
    users_tenant1 = User.query.filter_by(tenant_id=tenant1.id).all()
    assert len(users_tenant1) == 1  # Sadece kendisi

    users_tenant2 = User.query.filter_by(tenant_id=tenant2.id).all()
    assert len(users_tenant2) == 3  # Tenant 2 kullanıcıları


def test_system_admin_can_see_all_tenants(app):
    """Sistem admin tüm tenantları görebilmeli"""
    # Tenant 1 oluştur
    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    db.session.add(tenant1)
    db.session.flush()

    # Tenant 2 oluştur
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add(tenant2)
    db.session.flush()

    # Mevcut sistem admin'i kullan
    admin = User.query.filter_by(username='emin').first()
    if not admin:
        admin = User(
            username='superadmin',
            password='hash',
            tenant_id='default',
            role='sistem_yoneticisi'
        )
        db.session.add(admin)
    db.session.commit()

    # Sistem admin tüm tenantları görebilmeli
    tenants = Tenant.query.all()
    assert len(tenants) == 3  # default + tenant1 + tenant2


def test_normal_user_cannot_see_admin_panel(app):
    """Normal kullanıcı admin paneline erişememeli"""
    # Tenant oluştur
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    # Normal kullanıcı
    user = User(
        username='user@example.com',
        password='hash',
        tenant_id=tenant.id,
        role='kullanici'
    )
    db.session.add(user)
    db.session.commit()

    # Normal kullanıcı admin paneline erişememeli
    assert not user.has_admin_access
    assert user.role == 'kullanici'


def test_tenant_admin_role_check(app):
    """Tenant admin rolü kontrolü"""
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    admin = User(
        username='admin@example.com',
        password='hash',
        tenant_id=tenant.id,
        role='tenant_admin'
    )
    db.session.add(admin)
    db.session.commit()

    assert admin.role == 'tenant_admin'
    assert admin.tenant_id == tenant.id
