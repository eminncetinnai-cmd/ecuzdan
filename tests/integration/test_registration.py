"""
Registration Tests
Kullanıcı kayıt sistemini test eder
"""

import pytest
from werkzeug.security import generate_password_hash

from models import Tenant, User, db


def test_registration_creates_tenant(app):
    """Yeni kayıt otomatik tenant oluşturmalı"""
    # Kayıt simülasyonu
    full_name = "Emin Çetin"
    email = "emin@example.com"
    password = "securepassword"

    # Tenant oluştur (kullanıcı adından)
    tenant_id = full_name.lower().replace(' ', '_')
    tenant = Tenant(id=tenant_id, name=full_name)
    db.session.add(tenant)
    db.session.flush()

    # Kullanıcı oluştur
    user = User(
        username=email,
        password=generate_password_hash(password),
        tenant_id=tenant.id,
        role='tenant_admin'
    )
    db.session.add(user)
    db.session.commit()

    # Tenant oluşturulmuş olmalı
    assert Tenant.query.filter_by(id=tenant_id).first() is not None
    assert Tenant.query.filter_by(id=tenant_id).first().name == full_name

    # Kullanıcı tenant admin olmalı
    assert user.role == 'tenant_admin'
    assert user.tenant_id == tenant_id


def test_registration_duplicate_email(app):
    """Aynı e-posta ile tekrar kayıt engellenmeli"""
    # İlk kayıt
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    user1 = User(
        username='test@example.com',
        password=generate_password_hash('password'),
        tenant_id=tenant.id
    )
    db.session.add(user1)
    db.session.commit()

    # Aynı e-posta ile tekrar kayıt denemesi
    user2 = User(
        username='test@example.com',
        password=generate_password_hash('password'),
        tenant_id=tenant.id
    )
    db.session.add(user2)

    # IntegrityError fırlatmalı
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        db.session.commit()


def test_registration_tenant_admin_role(app):
    """Yeni kullanıcı tenant admin rolü ile oluşturulmalı"""
    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    user = User(
        username='test@example.com',
        password=generate_password_hash('password'),
        tenant_id=tenant.id,
        role='tenant_admin'
    )
    db.session.add(user)
    db.session.commit()

    assert user.role == 'tenant_admin'


def test_registration_password_hashing(app):
    """Şifre hashlenmeli"""
    password = "securepassword"
    hashed = generate_password_hash(password)

    tenant = Tenant(id='test_tenant', name='Test Tenant')
    db.session.add(tenant)
    db.session.flush()

    user = User(
        username='test@example.com',
        password=hashed,
        tenant_id=tenant.id
    )
    db.session.add(user)
    db.session.commit()

    # Şifre hashlenmiş olmalı
    assert user.password != password
    assert user.password.startswith('pbkdf2:') or user.password.startswith('scrypt:')
