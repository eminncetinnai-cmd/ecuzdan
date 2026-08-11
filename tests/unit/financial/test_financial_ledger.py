"""
Unit Tests - Financial Ledger Service
Birleşik defter mimarisi testleri
"""

import pytest

from database import create_payment
from domain.transactions.services.financial_ledger import (
    LedgerError,
    create_asset_position,
    create_one_time_transaction,
    create_recurring_plan,
    delete_asset_position,
    delete_one_time_transaction,
    delete_recurring_plan,
    get_asset_ledger_summary,
    sell_asset_position,
    update_asset_valuation,
    update_one_time_transaction,
)
from models import Asset, AssetSector, AssetTransaction, AssetUpdate, Category, RecurringPlan, Transaction, db


def _sector_id():
    return AssetSector.query.filter_by(name='Teknoloji').first().id


def test_create_asset_with_cash_link(app):
    asset = create_asset_position(
        type='Hisse Senedi',
        name='THYAO',
        value=10000,
        purchase_cost=10000,
        quantity=100,
        unit_price=100,
        currency='TRY',
        symbol='THYAO',
        risk_level='Orta',
        liquidity='Likit',
        sector_id=_sector_id(),
        sync_cash=True,
        tenant_id='default',
    )
    assert asset.id is not None
    assert asset.has_cash_link is True

    tx = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    assert tx is not None
    assert tx.type == 'Yatırım'
    assert tx.origin == 'Hisse Senedi Alımı'

    updates = AssetUpdate.query.filter_by(asset_id=asset.id).all()
    assert len(updates) == 1
    assert updates[0].update_type == 'initial'


def test_asset_purchase_reduces_cash_balance(app):
    # Kategori izole oluşturulur
    cat_maas = Category.query.filter_by(name='Maaş', type='Gelir').first()
    if not cat_maas:
        db.session.add(Category(name='Maaş', type='Gelir'))
        db.session.commit()

    create_one_time_transaction(
        '2025-06-01', 'Maaş', 'Nakit başlangıcı', 100000, 'Ödendi', 'Başlangıç nakit', tenant_id='default'
    )
    asset = create_asset_position(
        type='Fon',
        name='Yatırım Fonu',
        value=60000,
        purchase_cost=60000,
        quantity=60000,
        unit_price=1,
        currency='TRY',
        symbol='YATIRIM',
        risk_level='Orta',
        liquidity='Likit',
        sector_id=_sector_id(),
        sync_cash=True,
        tenant_id='default',
    )

    total_cash = sum(
        t.amount if t.type == 'Gelir' else -t.amount
        for t in Transaction.query.filter_by(tenant_id='default', status='Ödendi').all()
    )

    assert total_cash == 40000
    tx = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    assert tx is not None
    assert tx.amount == 60000
    assert tx.type == 'Yatırım'
    assert tx.category == 'Yatırıma Aktarılan'
    assert tx.description == 'Fon Alımı — Yatırım Fonu'
    assert tx.origin == 'Fon Alımı'


def test_asset_purchase_uses_matching_asset_type_category_when_it_exists(app):
    db.session.add(Category(name='Altın', type='Yatırım'))
    db.session.add(Category(name='Fon', type='Yatırım'))
    db.session.commit()

    asset = create_asset_position(
        type='Fon',
        name='TLY-Tera Yatırım',
        value=500000,
        purchase_cost=500000,
        quantity=500000,
        unit_price=1,
        currency='TRY',
        symbol='TLY',
        risk_level='Orta',
        liquidity='Likit',
        sector_id=_sector_id(),
        sync_cash=True,
        tenant_id='default',
    )

    tx = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    assert tx is not None
    assert tx.category == 'Fon'
    assert tx.description == 'Fon Alımı — TLY-Tera Yatırım'
    assert tx.note == 'fon alımı: TLY-Tera Yatırım'
    assert tx.origin == 'Fon Alımı'





def test_create_asset_rolls_back_when_cash_link_creation_fails(app, monkeypatch):
    import domain.transactions.services.financial_ledger as ledger

    def _boom(*args, **kwargs):
        raise RuntimeError('nakit-kopru-hatasi')

    monkeypatch.setattr(ledger, '_create_purchase_transaction', _boom)

    with pytest.raises(RuntimeError):
        ledger.create_asset_position(
            type='Hisse Senedi',
            name='ROLLBACK',
            value=7000,
            purchase_cost=7000,
            quantity=70,
            unit_price=100,
            currency='TRY',
            symbol='ROLLBACK',
            risk_level='Orta',
            liquidity='Likit',
            sector_id=_sector_id(),
            sync_cash=True,
            tenant_id='default',
        )
    db.session.rollback()

    asset = Asset.query.filter_by(name='ROLLBACK', tenant_id='default').first()
    assert asset is None
    assert AssetUpdate.query.join(Asset, AssetUpdate.asset_id == Asset.id).filter(Asset.name == 'ROLLBACK').count() == 0


def test_update_asset_creates_valuation_event(app):
    asset = create_asset_position(
        type='Hisse Senedi', name='SISE', value=1000,
        purchase_cost=1000, quantity=10, unit_price=100,
        currency='TRY', symbol='SISE', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(),
        tenant_id='default',
    )
    update_asset_valuation(
        asset.id,
        type='Hisse Senedi', name='SISE', value=1200,
        quantity=10, unit_price=120,
        currency='TRY', symbol='SISE', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(),
        tenant_id='default',
    )
    refreshed = db.session.get(Asset, asset.id)
    assert refreshed.value == 1200
    assert AssetUpdate.query.filter_by(asset_id=asset.id).count() == 2


def test_delete_asset_cleans_ledger(app):
    asset = create_asset_position(
        type='Hisse Senedi', name='EREGL', value=3000,
        purchase_cost=3000, quantity=30, unit_price=100,
        currency='TRY', symbol='EREGL', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(), sync_cash=True,
        tenant_id='default',
    )
    asset_id = asset.id
    assert delete_asset_position(asset_id, tenant_id='default') is True
    assert db.session.get(Asset, asset_id) is None
    assert AssetUpdate.query.filter_by(asset_id=asset_id).count() == 0
    assert AssetTransaction.query.filter_by(asset_id=asset_id).count() == 0
    assert Transaction.query.filter_by(source_id=asset_id, source_type='asset').count() == 0


def test_delete_asset_after_sales(app):
    asset = create_asset_position(
        type='Hisse Senedi', name='SATILMIŞ', value=2000,
        purchase_cost=2000, quantity=20, unit_price=100,
        currency='TRY', symbol='SATILMIS', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(), sync_cash=True,
        tenant_id='default',
    )
    sell_asset_position(asset.id, 5, 110, sale_date='2025-07-01', note='Kısmi satış', tenant_id='default')
    assert AssetTransaction.query.filter_by(asset_id=asset.id).count() == 2
    assert Transaction.query.filter_by(source_id=asset.id, source_type='asset_sale').count() == 1

    sale_tx = Transaction.query.filter_by(source_id=asset.id, source_type='asset_sale').first()
    sale_tx_id = sale_tx.id

    assert delete_asset_position(asset.id, tenant_id='default') is True
    assert db.session.get(Asset, asset.id) is None
    assert AssetTransaction.query.filter_by(asset_id=asset.id).count() == 0
    assert AssetUpdate.query.filter_by(asset_id=asset.id).count() == 0

    # Asset alım nakit çıkışı silindi
    assert Transaction.query.filter_by(source_id=asset.id, source_type='asset').count() == 0

    # Satış nakit girişi (Transaction) KALMALI ama bağı koparılmalı
    reloaded_sale_tx = db.session.get(Transaction, sale_tx_id)
    assert reloaded_sale_tx is not None
    assert reloaded_sale_tx.source_id is None
    assert reloaded_sale_tx.source_type is None


def test_create_one_time_transaction(app):
    tx = create_one_time_transaction(
        '2025-03-01', 'Maaş', 'Mart maaşı', 25000, 'Ödendi', 'test', tenant_id='default'
    )
    assert tx.origin == 'Manuel'
    assert tx.source_type == 'manual'


def test_create_recurring_plan_generates_transactions(app):
    plan = create_recurring_plan('Maaş Planı', 'Maaş', 20000, 3, 1, 'test plan', tenant_id='default')
    txs = Transaction.query.filter_by(source_id=plan.id, source_type='plan').all()
    assert len(txs) == 3
    assert all(t.origin == 'Planlı' for t in txs)


def test_create_payment_links_to_plan_transaction(app):
    plan = create_recurring_plan('Kredi Planı', 'Kredi', 5000, 4, 15, 'aylık kredi', tenant_id='default')
    payment = create_payment(plan.id, 5000, '2025-07-15', 1, 'ilk taksit', tenant_id='default')

    assert payment.id is not None
    assert payment.transaction_id is not None
    assert payment.installment_number == 1
    assert payment.amount == 5000

    tx = db.session.get(Transaction, payment.transaction_id)
    assert tx is not None
    assert tx.source_type == 'plan'
    assert tx.source_id == plan.id
    assert tx.installment_number == 1
    assert tx.status == 'Ödendi'
    assert 'ilk taksit' in (tx.note or '')


def test_delete_recurring_plan(app):
    plan = create_recurring_plan('Kira Planı', 'Kira', 5000, 2, 5, tenant_id='default')
    plan_id = plan.id
    result = delete_recurring_plan(plan_id, tenant_id='default')
    assert isinstance(result, dict)
    assert result.get('success') is True
    assert db.session.get(RecurringPlan, plan_id) is None
    assert Transaction.query.filter_by(source_id=plan_id).count() == 0


def test_delete_one_time_blocks_linked(app):
    asset = create_asset_position(
        type='Hisse Senedi', name='LINK', value=1000,
        purchase_cost=1000, quantity=1, unit_price=1000,
        currency='TRY', symbol='LINK', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(), sync_cash=True,
        tenant_id='default',
    )
    tx = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    try:
        delete_one_time_transaction(tx.id, tenant_id='default')
        assert False, 'Should raise LedgerError'
    except LedgerError:
        pass


def test_update_one_time_blocks_linked(app):
    asset = create_asset_position(
        type='Hisse Senedi', name='UPLINK', value=1500,
        purchase_cost=1500, quantity=1, unit_price=1500,
        currency='TRY', symbol='UPLINK', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(), sync_cash=True,
        tenant_id='default',
    )
    tx = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    try:
        update_one_time_transaction(
            tx.id, '2025-01-10', 'Yatırıma Aktarılan', 'Elle düzenleme',
            999, 'Ödendi', 'test', tenant_id='default'
        )
        assert False, 'Should raise LedgerError'
    except LedgerError:
        pass


def test_get_asset_ledger_summary(app):
    asset = create_asset_position(
        type='Hisse Senedi', name='SUM', value=2000,
        purchase_cost=2000, quantity=2, unit_price=1000,
        currency='TRY', symbol='SUM', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(), sync_cash=True,
        tenant_id='default',
    )
    summary = get_asset_ledger_summary(asset.id, tenant_id='default')
    assert summary['has_cash_link'] is True
    assert summary['valuation_count'] == 1
    assert summary['cash_amount'] == 2000


def test_balance_sheet_invariant_maintained(app):
    """
    Bilanço Invariant Testi:
    Nakit Girişleri (Gelir) - Nakit Çıkışları (Gider + Varlık Alımı) = Güncel Nakit (Transaction tablosunda status='Ödendi' toplamı)
    Varlık alımları ve satışları sonrası toplam nakit ile toplam portföy maliyeti dengesinin korunması.
    """
    from domain.transactions.services.financial_ledger import create_one_time_transaction

    # 1. Başlangıç Nakit
    create_one_time_transaction(
        '2025-01-01', 'Maaş', 'Ocak Maaşı', 100000, 'Ödendi', 'Initial', tenant_id='default'
    )

    # 2. Varlık Alımı (50.000 TL Nakit Çıkışı)
    asset1 = create_asset_position(
        type='Hisse Senedi', name='INVAR1', value=50000,
        purchase_cost=50000, quantity=500, unit_price=100,
        currency='TRY', symbol='INVAR1', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(), sync_cash=True,
        tenant_id='default',
    )

    # 3. Kısmi Satış (100 adet @ 120 TL = 12.000 TL Nakit Girişi)
    sell_asset_position(asset1.id, 100, 120, sale_date='2025-02-01', note='Kar realizasyonu', tenant_id='default')

    # 4. Gider (5.000 TL Nakit Çıkışı)
    Category.query.filter_by(name='Kira').first()
    db.session.add(Transaction(
        date='2025-02-05', category='Kira', description='Şubat Kirası', amount=5000, type='Gider', status='Ödendi', tenant_id='default'
    ))
    db.session.commit()

    # 5. Başka bir varlık alımı (Nakit etkilenmeli)
    create_asset_position(
        type='Altın', name='INVAR2', value=20000,
        purchase_cost=20000, quantity=10, unit_price=2000,
        currency='TRY', symbol='INVAR2', risk_level='Düşük',
        liquidity='Likit', sector_id=_sector_id(),
        tenant_id='default',
    )

    db.session.commit()

    # Hesaplama
    transactions = Transaction.query.filter_by(tenant_id='default', status='Ödendi').all()
    for t in transactions:
        print(f"TX: {t.type} | {t.amount} | {t.category} | {t.source_type}")
    total_cash = sum(t.amount if t.type == 'Gelir' else -t.amount for t in transactions)

    # Beklenen nakit: 100.000 (Maaş) - 50.000 (Alım1) + 12.000 (Satış1) - 5.000 (Kira) - 20.000 (Alım2) = 37.000
    assert total_cash == 37000

    # Kasa denklik kontrolü
    gelirler = sum(t.amount for t in transactions if t.type == 'Gelir')
    giderler = sum(t.amount for t in transactions if t.type in ('Gider', 'Yatırım'))
    assert (gelirler - giderler) == total_cash


def test_delete_asset_preserves_realized_cash(app):
    """
    Regresyon Testi: Varlık silindiğinde, o varlığın geçmişteki
    satışlarından (realized) elde edilen nakit girişi kaydı (asset_sale) kasada korunmalıdır.
    """
    # 1. Varlık Oluştur
    asset = create_asset_position(
        type='Hisse Senedi', name='EREGL_TEST', value=10000,
        purchase_cost=10000, quantity=100, unit_price=100,
        currency='TRY', symbol='EREGLT', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(),
        tenant_id='default',
    )

    # 2. Kısmi Satış Yap (50 adet @ 120 TL = 6.000 TL Nakit Girişi)
    sell_asset_position(
        asset.id, 50, 120, sale_date='2025-06-01', note='Kısmi kâr realizasyonu', tenant_id='default'
    )

    # Satış transaction'ını doğrula
    sale_tx = Transaction.query.filter_by(tenant_id='default', source_type='asset_sale').first()
    assert sale_tx is not None
    assert sale_tx.amount == 6000
    assert sale_tx.type == 'Gelir'

    # 3. Varlığı Sil
    delete_asset_position(asset.id, tenant_id='default')

    # Varlığın silindiğini doğrula
    assert db.session.get(Asset, asset.id) is None

    # Satış transaction'ının KORUNDUĞUNU, fakat kaynak bağlarının koptuğunu (orphan olmadığını) doğrula
    refreshed_sale_tx = db.session.get(Transaction, sale_tx.id)
    assert refreshed_sale_tx is not None
    assert refreshed_sale_tx.amount == 6000
    assert refreshed_sale_tx.source_id is None
    assert refreshed_sale_tx.source_type is None


