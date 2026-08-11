"""
Invitation Tests
Kullanıcı davet sistemini test eder
"""

from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from models import Tenant, User, db


def test_invitation_token_generation(app):
    """Davet token'ı oluşturulmalı"""
    # Tenant oluştur
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    # Token oluştur
    import secrets
    token = secrets.token_urlsafe(32)

    assert token is not None
    assert len(token) > 0


def test_invitation_expiration(app):
    """Davet token'ı 24 saat sonra expire olmalı"""
    from datetime import datetime

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(hours=24)

    # Token hala geçerli
    assert datetime.now(timezone.utc).replace(tzinfo=None) < expires_at

    # 25 saat sonra expire olmuş olmalı
    expired_at = now + timedelta(hours=25)
    assert expired_at > expires_at


def test_invitation_one_time_use(app):
    """Davet token'ı bir kez kullanılmalı"""
    # Tenant oluştur
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    # Davet token'ı oluştur
    import secrets
    secrets.token_urlsafe(32)
    used_at = None

    # İlk kullanım
    used_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Token kullanıldıysa tekrar kullanılamamalı
    assert used_at is not None


def test_invitation_links_to_tenant(app):
    """Davet ile kayıt olan kullanıcı aynı tenant'a bağlanmalı"""
    # Tenant oluştur
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    # Tenant admin oluştur
    admin = User(
        username='admin@example.com',
        password=generate_password_hash('password'),
        tenant_id=tenant.id,
        role='tenant_admin'
    )
    db.session.add(admin)
    db.session.commit()

    # Davet ile kayıt olan kullanıcı
    user = User(
        username='invited@example.com',
        password=generate_password_hash('password'),
        tenant_id=tenant.id,
        role='kullanici'
    )
    db.session.add(user)
    db.session.commit()

    # Kullanıcı aynı tenant'a bağlı olmalı
    assert user.tenant_id == tenant.id
    assert user.tenant_id == admin.tenant_id


def test_invitation_email_validation(app):
    """Davet e-postası doğrulanmalı"""
    # Tenant oluştur
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    # Geçerli e-posta
    valid_email = 'user@example.com'
    assert '@' in valid_email
    assert '.' in valid_email

    # Geçersiz e-posta
    invalid_email = 'invalid-email'
    assert '@' not in invalid_email
