from database.crud import get_actual_cash, get_total_assets
from domain.transactions.services.financial_ledger import (
    create_asset_position,
    create_one_time_transaction,
    delete_asset_position,
    sell_asset_position,
)
from models import AssetSector, Category, Transaction, db


def _get_or_create_standard_category(category_name, category_type):
    """Get or create a standard category for testing."""
    category = Category.query.filter_by(name=category_name, tenant_id=None).first()
    if not category:
        category = Category(name=category_name, type=category_type, tenant_id=None)
        db.session.add(category)
        db.session.commit()
    return category


def _sector_id():
    sector = AssetSector.query.filter_by(name='Teknoloji').first()
    if not sector:
        sector = AssetSector(name='Teknoloji')
        db.session.add(sector)
        db.session.commit()
    return sector.id

def _verify_net_worth(tenant_id, expected_net_worth):
    """Bilanço invariant doğrulaması: Kasa Bakiyesi + Varlık Değeri == Beklenen Net Servet"""
    cash = get_actual_cash(tenant_id)
    assets = get_total_assets(tenant_id)
    net_worth = cash + assets
    assert net_worth == expected_net_worth, f"Bilanço invariant kırıldı! Kasa: {cash}, Varlıklar: {assets}, Net Servet: {net_worth}, Beklenen: {expected_net_worth}"

def test_tenant_balance_invariant_flow(app):
    """
    Kapsamlı Bilanço Denkliği (Invariant) Testi.
    Gelir, Gider, Varlık Alımı, Varlık Satışı ve Varlık Silme senaryolarında
    Net Servet (Kasa + Portföy Değeri) eşitliğinin korunduğunu test eder.
    """
    tenant = 'tenant_invariant'

    # 0. Başlangıç Durumu
    _verify_net_worth(tenant, 0)

    # 1. Gelir Ekleme (+100.000 TL)
    income_cat = _get_or_create_standard_category('Maaş / Ücret Geliri', 'Gelir')
    create_one_time_transaction(
        '2025-01-01', income_cat.name, 'Ocak Maaşı', 100000, 'Ödendi', 'Maaş geliri', tenant_id=tenant
    )
    db.session.commit()
    # Kasa: 100.000, Portföy: 0 => Net Servet: 100.000
    _verify_net_worth(tenant, 100000)

    # 2. Varlık Alımı (30.000 TL Nakit Çıkışı -> 30.000 TL Varlık Girişi)
    asset = create_asset_position(
        type='Hisse Senedi', name='INV_ASSET', value=30000,
        purchase_cost=30000, quantity=300, unit_price=100,
        currency='TRY', symbol='INVA', risk_level='Orta',
        liquidity='Likit', sector_id=_sector_id(),
        tenant_id=tenant,
    )
    db.session.commit()
    # Kasa: 70.000, Portföy: 30.000 => Net Servet: 100.000 (Değişmedi)
    _verify_net_worth(tenant, 100000)

    # 3. Varlık Değerlenme Artışı (Portföy Değeri 30.000 -> 36.000 TL, unit_price 100 -> 120)
    # update_asset_valuation çağrısı yapalım
    from domain.transactions.services.financial_ledger import update_asset_valuation
    update_asset_valuation(
        asset.id,
        type='Hisse Senedi', name='INV_ASSET', value=36000,
        quantity=300, unit_price=120,
        currency='TRY', symbol='INVA', risk_level='Orta',
        tenant_id=tenant
    )
    db.session.commit()
    # Kasa: 70.000, Portföy: 36.000 => Net Servet: 106.000 (+6.000 unrealized gain)
    _verify_net_worth(tenant, 106000)

    # 4. Kısmi Satış Yap (100 adet @ 130 TL = 13.000 TL Nakit Girişi)
    # Satılan miktar için WAC maliyeti = 100 * 100 = 10.000 TL
    # Realized gain = 13.000 - 10.000 = 3.000 TL.
    # Yeni Portföy Değeri = 200 adet * 120 TL = 24.000 TL
    # Yeni Kasa = 70.000 + 13.000 = 83.000 TL
    sell_asset_position(
        asset.id, 100, 130, sale_date='2025-02-01', note='Kısmi satış', tenant_id=tenant
    )
    db.session.commit()
    # Kasa: 83.000, Portföy: 24.000 => Net Servet: 107.000 (106.000 + 1.000 realized ek artış)
    _verify_net_worth(tenant, 107000)

    # 5. Gider Ekleme (-7.000 TL)
    expense_cat = _get_or_create_standard_category('Konut & Kira', 'Gider')
    db.session.add(Transaction(
        date='2025-02-05', category=expense_cat.name, description='Kira gideri', amount=7000, type='Gider', status='Ödendi', tenant_id=tenant
    ))
    db.session.commit()
    # Kasa: 76.000, Portföy: 24.000 => Net Servet: 100.000
    _verify_net_worth(tenant, 100000)

    # 6. Varlığı Tamamen Silme
    # delete_asset_position çağrıldığında:
    # - Varlık silinir (Portföy Değeri: 24.000 -> 0)
    # - Alım nakit çıkış kaydı silinir (Kasa: 76.000 + 30.000 = 106.000)
    # - Satış nakit giriş kaydı korunur (13.000 TL kasada kalır)
    # Beklenen Kasa: 106.000, Beklenen Portföy: 0 => Net Servet: 106.000
    delete_asset_position(asset.id, tenant_id=tenant)
    db.session.commit()
    _verify_net_worth(tenant, 106000)
