"""
Unit Tests - Models
User, Category, Asset, Transaction modelleri için testler
"""

from werkzeug.security import check_password_hash, generate_password_hash

from models import Asset, AssetSector, AssetType, Category, RecurringPlan, Transaction, User


def test_user_model(app):
    user = User(
        username='demo',
        password=generate_password_hash('testpass'),
        role='kullanici',
    )
    assert user.username == 'demo'
    assert user.role == 'kullanici'
    assert check_password_hash(user.password, 'testpass')


def test_user_model_admin(app):
    user = User(
        username='mgr',
        password=generate_password_hash('adminpass'),
        role='yonetici',
    )
    assert user.role == 'yonetici'
    assert user.has_admin_access is True
    assert user.is_super_admin is False


def test_emin_full_admin(app):
    emin = User(username='emin', password=generate_password_hash('1'), role='sistem_yoneticisi')
    assert emin.has_admin_access is True
    assert emin.is_super_admin is True
    assert len(emin.role_labels) == 3


def test_category_model(app):
    category = Category(name='Maaş', type='Gelir')
    assert category.name == 'Maaş'
    assert category.type == 'Gelir'


def test_asset_type_model(app):
    asset_type = AssetType(name='Hisse Senedi')
    assert asset_type.name == 'Hisse Senedi'


def test_asset_sector_model(app):
    asset_sector = AssetSector(name='Teknoloji')
    assert asset_sector.name == 'Teknoloji'


def test_transaction_model(app):
    transaction = Transaction(
        date='2025-01-01',
        category='Maaş',
        description='Ocak Maaşı',
        type='Gelir',
        amount=50000,
        status='Ödendi',
    )
    assert transaction.origin == 'Tek seferlik'
    assert transaction.ledger_layer == 'nakit_olay'


def test_transaction_origin_plan(app):
    tx = Transaction(
        date='2025-02-01',
        category='Kira',
        type='Gider',
        amount=5000,
        status='Bekliyor',
        source_id=1,
        source_type='plan',
    )
    assert tx.origin == 'Planlı'


def test_transaction_origin_asset(app):
    tx = Transaction(
        date='2025-02-01',
        category='Yatırıma Aktarılan',
        type='Yatırım',
        amount=10000,
        status='Ödendi',
        source_id=5,
        source_type='asset',
    )
    assert tx.origin == 'Varlık Alımı'


def test_recurring_plan_model(app):
    plan = RecurringPlan(
        name='Kredi',
        category='Kredi',
        flow_type='Gider',
        amount=5000,
        installments=24,
        payment_day=5,
    )
    assert plan.origin == 'Planlı'
    assert plan.ledger_layer == 'nakit_pozisyon'


def test_asset_model(app):
    asset = Asset(
        type='Hisse Senedi',
        name='YKBNK',
        value=50000,
        description='Yapı Kredi Bankası',
        purchase_date='2023-01-15',
        purchase_cost=45000,
        quantity=1000,
        unit_price=45,
        currency='TRY',
        symbol='YKBNK.E',
        risk_level='Orta',
        liquidity='Yarı-Likit',
        sector_id=1,
    )
    assert asset.origin == 'Manuel'
    assert asset.ledger_layer == 'varlik_pozisyon'
