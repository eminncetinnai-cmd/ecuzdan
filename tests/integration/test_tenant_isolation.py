"""
Tenant Isolation Tests
Multi-tenant mimarisinde tenant izolasyonunu test eder
"""

from models import Asset, Tenant, Transaction, User, db


def test_tenant_isolation_transactions(app):
    """Farklı tenantların işlemleri izole olmalı"""
    # Tenant 1 oluştur
    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    db.session.add(tenant1)
    db.session.flush()

    # Tenant 2 oluştur
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add(tenant2)
    db.session.flush()

    # Tenant 1 için kullanıcı
    user1 = User(username='user1', password='hash1', tenant_id=tenant1.id)
    db.session.add(user1)

    # Tenant 2 için kullanıcı
    user2 = User(username='user2', password='hash2', tenant_id=tenant2.id)
    db.session.add(user2)
    db.session.commit()

    # Tenant 1 için işlem
    from database import add_transaction
    add_transaction(
        '2025-01-01', 'Maaş', 'Test', 'Gelir', 1000, 'Ödendi', tenant_id=tenant1.id
    )

    # Tenant 2 için işlem
    add_transaction(
        '2025-01-01', 'Maaş', 'Test', 'Gelir', 2000, 'Ödendi', tenant_id=tenant2.id
    )

    # Tenant 1 sadece kendi işlemini görmeli
    txs_tenant1 = Transaction.query.filter_by(tenant_id=tenant1.id).all()
    assert len(txs_tenant1) == 1
    assert txs_tenant1[0].amount == 1000

    # Tenant 2 sadece kendi işlemini görmeli
    txs_tenant2 = Transaction.query.filter_by(tenant_id=tenant2.id).all()
    assert len(txs_tenant2) == 1
    assert txs_tenant2[0].amount == 2000


def test_tenant_isolation_assets(app):
    """Farklı tenantların varlıkları izole olmalı"""
    # Tenant 1 oluştur
    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    db.session.add(tenant1)
    db.session.flush()

    # Tenant 2 oluştur
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add(tenant2)
    db.session.flush()

    # Sector oluştur
    from models import AssetSector
    sector = AssetSector.query.filter_by(name='Teknoloji').first()
    if not sector:
        sector = AssetSector(name='Teknoloji')
        db.session.add(sector)
        db.session.flush()

    # Tenant 1 için varlık
    from database import add_asset
    add_asset(
        type_='Hisse Senedi', name='THYAO', value=10000,
        description='THYAO hissesi', purchase_date='2025-01-01',
        purchase_cost=10000, symbol='THYAO', sector_id=sector.id, tenant_id=tenant1.id
    )

    # Tenant 2 için varlık
    add_asset(
        type_='Hisse Senedi', name='GARAN', value=20000,
        description='GARAN hissesi', purchase_date='2025-01-01',
        purchase_cost=20000, symbol='GARAN', sector_id=sector.id, tenant_id=tenant2.id
    )

    # Tenant 1 sadece kendi varlığını görmeli
    assets_tenant1 = Asset.query.filter_by(tenant_id=tenant1.id).all()
    assert len(assets_tenant1) == 1
    assert assets_tenant1[0].name == 'THYAO'

    # Tenant 2 sadece kendi varlığını görmeli
    assets_tenant2 = Asset.query.filter_by(tenant_id=tenant2.id).all()
    assert len(assets_tenant2) == 1
    assert assets_tenant2[0].name == 'GARAN'


def test_tenant_isolation_users(app):
    """Farklı tenantların kullanıcıları izole olmalı"""
    # Tenant 1 oluştur
    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    db.session.add(tenant1)
    db.session.flush()

    # Tenant 2 oluştur
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add(tenant2)
    db.session.flush()

    # Tenant 1 için 3 kullanıcı
    for i in range(3):
        db.session.add(User(
            username=f'user1_{i}',
            password=f'hash{i}',
            tenant_id=tenant1.id
        ))

    # Tenant 2 için 2 kullanıcı
    for i in range(2):
        db.session.add(User(
            username=f'user2_{i}',
            password=f'hash{i}',
            tenant_id=tenant2.id
        ))
    db.session.commit()

    # Tenant 1 sadece kendi kullanıcılarını görmeli
    users_tenant1 = User.query.filter_by(tenant_id=tenant1.id).all()
    assert len(users_tenant1) == 3

    # Tenant 2 sadece kendi kullanıcılarını görmeli
    users_tenant2 = User.query.filter_by(tenant_id=tenant2.id).all()
    assert len(users_tenant2) == 2


def test_tenant_cross_access_prevention(app):
    """Tenant cross-access engellenmeli"""
    # Tenant 1 oluştur
    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    db.session.add(tenant1)
    db.session.flush()

    # Tenant 2 oluştur
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add(tenant2)
    db.session.flush()

    # Tenant 2 için işlem
    from database import add_transaction
    add_transaction(
        '2025-01-01', 'Maaş', 'Test', 'Gelir', 2000, 'Ödendi', tenant_id=tenant2.id
    )

    # Tenant 1 Tenant 2'nin işlemini görmemeli
    txs_tenant1 = Transaction.query.filter_by(tenant_id=tenant1.id).all()
    assert len(txs_tenant1) == 0

    # Tenant 2'nin işlemi sadece Tenant 2'de görünmeli
    txs_tenant2 = Transaction.query.filter_by(tenant_id=tenant2.id).all()
    assert len(txs_tenant2) == 1
