"""
Unit Tests - Weighted Average Cost
AssetTransaction tablosu ve weighted average cost hesaplaması için testler
"""


from models import Asset, AssetSector, AssetTransaction, Tenant


def test_weighted_average_cost_single_buy(app):
    """Tek alım işlemi için weighted average cost testi"""
    with app.app_context():
        # Tenant oluştur
        tenant = Tenant(id='test_tenant', name='Test Tenant')
        from models import db
        db.session.add(tenant)
        db.session.commit()

        # Sector oluştur veya mevcut olanı kullan
        sector = AssetSector.query.filter_by(name='Teknoloji').first()
        if not sector:
            sector = AssetSector(name='Teknoloji')
            db.session.add(sector)
            db.session.commit()

        # Asset oluştur
        asset = Asset(
            type='Hisse Senedi',
            name='YKBNK',
            value=50000,
            purchase_date='2023-01-15',
            purchase_cost=45000,
            quantity=1000,
            unit_price=45,
            currency='TRY',
            symbol='YKBNK.E',
            risk_level='Orta',
            liquidity='Yarı-Likit',
            sector_id=sector.id,
            tenant_id='test_tenant'
        )
        db.session.add(asset)
        db.session.commit()

        # AssetTransaction kaydı yoksa eski purchase_cost kullanmalı
        assert asset.weighted_average_cost == 45000

        # Tek alım işlemi ekle
        tx = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=1000,
            unit_price=45,
            total_cost=45000,
            transaction_date='2023-01-15',
            tenant_id='test_tenant'
        )
        db.session.add(tx)
        db.session.commit()

        # Weighted average cost (per-unit) hesaplanmalı
        assert asset.weighted_average_cost == 45.0


def test_weighted_average_cost_multiple_buys(app):
    """Birden fazla alım işlemi için weighted average cost testi"""
    with app.app_context():
        # Tenant oluştur
        tenant = Tenant(id='test_tenant2', name='Test Tenant 2')
        from models import db
        db.session.add(tenant)
        db.session.commit()

        # Sector oluştur veya mevcut olanı kullan
        sector = AssetSector.query.filter_by(name='Teknoloji').first()
        if not sector:
            sector = AssetSector(name='Teknoloji')
            db.session.add(sector)
            db.session.commit()

        # Asset oluştur
        asset = Asset(
            type='Hisse Senedi',
            name='THYAO',
            value=25000,
            purchase_date='2023-01-15',
            purchase_cost=0,
            quantity=0,
            unit_price=0,
            currency='TRY',
            symbol='THYAO.E',
            risk_level='Orta',
            liquidity='Yarı-Likit',
            sector_id=sector.id,
            tenant_id='test_tenant2'
        )
        db.session.add(asset)
        db.session.commit()

        # İlk alım: 10 adet @ 100 TL = 1000 TL
        tx1 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=10,
            unit_price=100,
            total_cost=1000,
            transaction_date='2023-01-15',
            tenant_id='test_tenant2'
        )
        db.session.add(tx1)

        # İkinci alım: 10 adet @ 150 TL = 1500 TL
        tx2 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=10,
            unit_price=150,
            total_cost=1500,
            transaction_date='2023-02-15',
            tenant_id='test_tenant2'
        )
        db.session.add(tx2)
        db.session.commit()

        # Weighted average (per-unit): (1000 + 1500) / 20 = 125 TL
        assert asset.weighted_average_cost == 125.0


def test_weighted_average_cost_with_sell(app):
    """Alım ve satış işlemleri için weighted average cost testi"""
    with app.app_context():
        # Tenant oluştur
        tenant = Tenant(id='test_tenant3', name='Test Tenant 3')
        from models import db
        db.session.add(tenant)
        db.session.commit()

        # Sector oluştur veya mevcut olanı kullan
        sector = AssetSector.query.filter_by(name='Teknoloji').first()
        if not sector:
            sector = AssetSector(name='Teknoloji')
            db.session.add(sector)
            db.session.commit()

        # Asset oluştur
        asset = Asset(
            type='Hisse Senedi',
            name='GARAN',
            value=15000,
            purchase_date='2023-01-15',
            purchase_cost=0,
            quantity=0,
            unit_price=0,
            currency='TRY',
            symbol='GARAN.E',
            risk_level='Orta',
            liquidity='Yarı-Likit',
            sector_id=sector.id,
            tenant_id='test_tenant3'
        )
        db.session.add(asset)
        db.session.commit()

        # İlk alım: 10 adet @ 100 TL = 1000 TL
        tx1 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=10,
            unit_price=100,
            total_cost=1000,
            transaction_date='2023-01-15',
            tenant_id='test_tenant3'
        )
        db.session.add(tx1)

        # İkinci alım: 10 adet @ 150 TL = 1500 TL
        tx2 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=10,
            unit_price=150,
            total_cost=1500,
            transaction_date='2023-02-15',
            tenant_id='test_tenant3'
        )
        db.session.add(tx2)

        # Satış: 5 adet @ 140 TL
        tx3 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='sell',
            quantity=5,
            unit_price=140,
            total_cost=700,
            transaction_date='2023-03-15',
            tenant_id='test_tenant3'
        )
        db.session.add(tx3)
        db.session.commit()

        # Weighted average (per-unit): (1000 + 1500) / 20 = 125 TL
        # Satış sonrası: 15 adet kaldı, per-unit cost hala 125 TL
        assert asset.weighted_average_cost == 125.0


def test_roi_with_weighted_average(app):
    """Weighted average cost kullanarak ROI hesaplama testi"""
    with app.app_context():
        # Tenant oluştur
        tenant = Tenant(id='test_tenant4', name='Test Tenant 4')
        from models import db
        db.session.add(tenant)
        db.session.commit()

        # Sector oluştur veya mevcut olanı kullan
        sector = AssetSector.query.filter_by(name='Teknoloji').first()
        if not sector:
            sector = AssetSector(name='Teknoloji')
            db.session.add(sector)
            db.session.commit()

        # Asset oluştur
        asset = Asset(
            type='Hisse Senedi',
            name='AKBNK',
            value=3000,
            purchase_date='2023-01-15',
            purchase_cost=0,
            quantity=0,
            unit_price=0,
            currency='TRY',
            symbol='AKBNK.E',
            risk_level='Orta',
            liquidity='Yarı-Likit',
            sector_id=sector.id,
            tenant_id='test_tenant4'
        )
        db.session.add(asset)
        db.session.commit()

        # İlk alım: 10 adet @ 100 TL = 1000 TL
        tx1 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=10,
            unit_price=100,
            total_cost=1000,
            transaction_date='2023-01-15',
            tenant_id='test_tenant4'
        )
        db.session.add(tx1)

        # İkinci alım: 10 adet @ 150 TL = 1500 TL
        tx2 = AssetTransaction(
            asset_id=asset.id,
            transaction_type='buy',
            quantity=10,
            unit_price=150,
            total_cost=1500,
            transaction_date='2023-02-15',
            tenant_id='test_tenant4'
        )
        db.session.add(tx2)
        db.session.commit()

        # Güncel değer: 3000 TL
        # Weighted average cost (toplam): 1000 + 1500 = 2500 TL
        # ROI: (3000 - 2500) / 2500 * 100 = 20%
        assert asset.roi == 20.0
        assert asset.total_gain_loss == 500.0
