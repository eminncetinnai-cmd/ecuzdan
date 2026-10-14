"""
Portföy Hesaplamaları Testleri
Portföy değeri, getirisi, risk dağılımı ve çeşitlendirme testleri
"""


from decimal import Decimal

import pytest
from flask import g

from database import get_total_assets, get_total_debts
from models import Asset, AssetSector, AssetType, Tenant, User, db


class TestPortfolioCalculations:
    """Portföy hesaplamaları test sınıfı"""

    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Test öncesi kurulum"""
        with app.app_context():
            # Test tenant oluştur
            tenant = Tenant(id='test_portfolio', name='Test Portfolio Tenant')
            db.session.add(tenant)
            db.session.commit()

            # Test kullanıcı oluştur
            user = User(
                username='test_portfolio_user',
                password='test123',
                tenant_id=tenant.id
            )
            db.session.add(user)
            db.session.commit()

            # Test varlık tipleri oluştur
            asset_types = ['Hisse Senedi', 'Fon', 'Altın', 'Kripto', 'Gayrimenkul']
            for type_name in asset_types:
                if not AssetType.query.filter_by(name=type_name).first():
                    asset_type = AssetType(name=type_name)
                    db.session.add(asset_type)
            db.session.commit()

            # Test varlık sektörleri oluştur
            sectors = ['Teknoloji', 'Finansal Sistem', 'Emtia & Hammadde', 'Gayrimenkul & Fiziksel Varlıklar']
            for sector_name in sectors:
                if not AssetSector.query.filter_by(name=sector_name).first():
                    sector = AssetSector(name=sector_name)
                    db.session.add(sector)
            db.session.commit()

            self.tenant_id = tenant.id
            self.user_id = user.id

    def test_portfolio_total_value(self, app):
        """Portföy toplam değeri hesaplama testi"""
        with app.app_context():
            # Çeşitli varlık tiplerinden portföy oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Portföy Hisse',
                    value=50000.0,
                    description='Portföy hisse senedi',
                    purchase_date='01/01/2024',
                    purchase_cost=40000.0,
                    quantity=500.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='PORTHISSE',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Altın',
                    name='Portföy Altın',
                    value=30000.0,
                    description='Portföy altın',
                    purchase_date='01/01/2024',
                    purchase_cost=25000.0,
                    quantity=30.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='XAUT',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Fon',
                    name='Portföy Fon',
                    value=20000.0,
                    description='Portföy fon',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=200.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='PORTFON',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=2,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy toplam değeri
            portfolio_value = get_total_assets(self.tenant_id)

            assert portfolio_value == 100000.0, f"Beklenen portföy değeri: 100000.0, Alınan: {portfolio_value}"

    def test_portfolio_weight_returns_decimal(self, app):
        """Portföy ağırlığının Decimal döndürmesini doğrular"""
        with app.app_context():
            asset_type = AssetType.query.filter_by(name='Hisse Senedi').first()
            assert asset_type is not None, "Testte Hisse Senedi varlık tipi bulunamadı"

            asset = Asset(
                type='Hisse Senedi',
                name='Portföy Ağırlık Testi',
                value=1000.0,
                description='Test varlığı',
                purchase_date='01/01/2024',
                purchase_cost=900.0,
                quantity=10.0,
                unit_price=100.0,
                currency='TRY',
                symbol='TEST',
                risk_level='Orta',
                liquidity='Likit',
                sector_id=1,
                tenant_id=self.tenant_id
            )
            db.session.add(asset)
            db.session.commit()

            g.tenant_id = self.tenant_id
            weight = asset.portfolio_weight

            assert isinstance(weight, Decimal)
            assert weight == Decimal("100")

    def test_portfolio_asset_allocation(self, app):
        """Portföy varlık dağılımı hesaplama testi"""
        with app.app_context():
            # Farklı varlık tiplerinden portföy oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Hisse 1',
                    value=40000.0,
                    description='Hisse senedi',
                    purchase_date='01/01/2024',
                    purchase_cost=35000.0,
                    quantity=400.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='HISSE1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Hisse Senedi',
                    name='Hisse 2',
                    value=20000.0,
                    description='Hisse senedi',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=200.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='HISSE2',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Altın',
                    name='Altın',
                    value=20000.0,
                    description='Altın',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=20.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='XAUT',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Kripto',
                    name='Kripto',
                    value=20000.0,
                    description='Kripto',
                    purchase_date='01/01/2024',
                    purchase_cost=15000.0,
                    quantity=2.0,
                    unit_price=10000.0,
                    currency='TRY',
                    symbol='BTC',
                    risk_level='Yüksek',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy toplam değeri
            total_value = get_total_assets(self.tenant_id)
            assert total_value == 100000.0, f"Beklenen toplam değer: 100000.0, Alınan: {total_value}"

            # Varlık tipi bazında dağılım
            stock_value = Asset.query.filter_by(type='Hisse Senedi', tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            gold_value = Asset.query.filter_by(type='Altın', tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            crypto_value = Asset.query.filter_by(type='Kripto', tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0

            assert stock_value == 60000.0, f"Beklenen hisse değeri: 60000.0, Alınan: {stock_value}"
            assert gold_value == 20000.0, f"Beklenen altın değeri: 20000.0, Alınan: {gold_value}"
            assert crypto_value == 20000.0, f"Beklenen kripto değeri: 20000.0, Alınan: {crypto_value}"

            # Yüzdelik dağılım
            stock_allocation = (stock_value / total_value) * 100
            gold_allocation = (gold_value / total_value) * 100
            crypto_allocation = (crypto_value / total_value) * 100

            assert stock_allocation == 60.0, f"Beklenen hisse dağılımı: 60.0%, Alınan: {stock_allocation}%"
            assert gold_allocation == 20.0, f"Beklenen altın dağılımı: 20.0%, Alınan: {gold_allocation}%"
            assert crypto_allocation == 20.0, f"Beklenen kripto dağılımı: 20.0%, Alınan: {crypto_allocation}%"

    def test_portfolio_sector_allocation(self, app):
        """Portföy sektör dağılımı hesaplama testi"""
        with app.app_context():
            # Farklı sektörlerden portföy oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Teknoloji Hisse',
                    value=30000.0,
                    description='Teknoloji hissesi',
                    purchase_date='01/01/2024',
                    purchase_cost=25000.0,
                    quantity=300.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='TECH',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,  # Teknoloji
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Fon',
                    name='Finans Fon',
                    value=30000.0,
                    description='Finans fonu',
                    purchase_date='01/01/2024',
                    purchase_cost=27000.0,
                    quantity=300.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='FINFON',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=2,  # Finansal Sistem
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Altın',
                    name='Altın',
                    value=20000.0,
                    description='Altın',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=20.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='XAUT',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=3,  # Emtia & Hammadde
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Gayrimenkul',
                    name='Gayrimenkul',
                    value=20000.0,
                    description='Gayrimenkul',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=1.0,
                    unit_price=20000.0,
                    currency='TRY',
                    symbol='REALESTATE',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=4,  # Gayrimenkul & Fiziksel Varlıklar
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy toplam değeri
            total_value = get_total_assets(self.tenant_id)
            assert total_value == 100000.0, f"Beklenen toplam değer: 100000.0, Alınan: {total_value}"

            # Sektör bazında dağılım
            tech_value = Asset.query.filter_by(sector_id=1, tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            finance_value = Asset.query.filter_by(sector_id=2, tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            commodity_value = Asset.query.filter_by(sector_id=3, tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            real_estate_value = Asset.query.filter_by(sector_id=4, tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0

            assert tech_value == 30000.0, f"Beklenen teknoloji değeri: 30000.0, Alınan: {tech_value}"
            assert finance_value == 30000.0, f"Beklenen finans değeri: 30000.0, Alınan: {finance_value}"
            assert commodity_value == 20000.0, f"Beklenen emtia değeri: 20000.0, Alınan: {commodity_value}"
            assert real_estate_value == 20000.0, f"Beklenen gayrimenkul değeri: 20000.0, Alınan: {real_estate_value}"

    def test_portfolio_risk_distribution(self, app):
        """Portföy risk dağılımı hesaplama testi"""
        with app.app_context():
            # Farklı risk seviyelerinde portföy oluştur
            assets = [
                Asset(
                    type='Altın',
                    name='Düşük Risk 1',
                    value=30000.0,
                    description='Düşük risk',
                    purchase_date='01/01/2024',
                    purchase_cost=27000.0,
                    quantity=30.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='LOW1',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Fon',
                    name='Düşük Risk 2',
                    value=20000.0,
                    description='Düşük risk',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=200.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='LOW2',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=2,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Hisse Senedi',
                    name='Orta Risk 1',
                    value=30000.0,
                    description='Orta risk',
                    purchase_date='01/01/2024',
                    purchase_cost=25000.0,
                    quantity=300.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='MED1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Kripto',
                    name='Yüksek Risk',
                    value=20000.0,
                    description='Yüksek risk',
                    purchase_date='01/01/2024',
                    purchase_cost=15000.0,
                    quantity=2.0,
                    unit_price=10000.0,
                    currency='TRY',
                    symbol='HIGH1',
                    risk_level='Yüksek',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy toplam değeri
            total_value = get_total_assets(self.tenant_id)
            assert total_value == 100000.0, f"Beklenen toplam değer: 100000.0, Alınan: {total_value}"

            # Risk seviyesi bazında dağılım
            low_risk_value = Asset.query.filter_by(risk_level='Düşük', tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            medium_risk_value = Asset.query.filter_by(risk_level='Orta', tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0
            high_risk_value = Asset.query.filter_by(risk_level='Yüksek', tenant_id=self.tenant_id).with_entities(db.func.sum(Asset.value)).scalar() or 0

            assert low_risk_value == 50000.0, f"Beklenen düşük risk değeri: 50000.0, Alınan: {low_risk_value}"
            assert medium_risk_value == 30000.0, f"Beklenen orta risk değeri: 30000.0, Alınan: {medium_risk_value}"
            assert high_risk_value == 20000.0, f"Beklenen yüksek risk değeri: 20000.0, Alınan: {high_risk_value}"

            # Yüzdelik risk dağılımı
            low_risk_allocation = (low_risk_value / total_value) * 100
            medium_risk_allocation = (medium_risk_value / total_value) * 100
            high_risk_allocation = (high_risk_value / total_value) * 100

            assert low_risk_allocation == 50.0, f"Beklenen düşük risk dağılımı: 50.0%, Alınan: {low_risk_allocation}%"
            assert medium_risk_allocation == 30.0, f"Beklenen orta risk dağılımı: 30.0%, Alınan: {medium_risk_allocation}%"
            assert high_risk_allocation == 20.0, f"Beklenen yüksek risk dağılımı: 20.0%, Alınan: {high_risk_allocation}%"

    def test_portfolio_net_worth(self, app):
        """Portföy net değer hesaplama testi (varlıklar - borçlar)"""
        with app.app_context():
            # Varlıklar oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Net Değer Hisse',
                    value=80000.0,
                    description='Net değer hisse',
                    purchase_date='01/01/2024',
                    purchase_cost=70000.0,
                    quantity=800.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='NETWORTH',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Altın',
                    name='Net Değer Altın',
                    value=20000.0,
                    description='Net değer altın',
                    purchase_date='01/01/2024',
                    purchase_cost=18000.0,
                    quantity=20.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='XAUT',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)

            # Borçlar (RecurringPlan ile temsil edilir)
            from models import RecurringPlan
            debt = RecurringPlan(
                name='Kredi',
                category='Kredi',
                flow_type='Gider',
                amount=2000.0,
                installments=12,
                payment_day=15,
                tenant_id=self.tenant_id
            )
            db.session.add(debt)
            db.session.commit()

            # Toplam varlıklar
            total_assets = get_total_assets(self.tenant_id)
            assert total_assets == 100000.0, f"Beklenen toplam varlık: 100000.0, Alınan: {total_assets}"

            # Toplam borçlar
            total_debts = get_total_debts(self.tenant_id)
            expected_debts = 2000.0 * 12  # amount * installments
            assert total_debts == expected_debts, f"Beklenen toplam borç: {expected_debts}, Alınan: {total_debts}"

            # Net değer
            net_worth = total_assets - total_debts
            expected_net_worth = 100000.0 - expected_debts
            assert net_worth == expected_net_worth, f"Beklenen net değer: {expected_net_worth}, Alınan: {net_worth}"

    def test_portfolio_diversification_ratio(self, app):
        """Portföy çeşitlendirme oranı hesaplama testi"""
        with app.app_context():
            # Çeşitlendirilmiş portföy oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Çeşit 1',
                    value=25000.0,
                    description='Çeşitlendirme 1',
                    purchase_date='01/01/2024',
                    purchase_cost=22000.0,
                    quantity=250.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='DIV1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Fon',
                    name='Çeşit 2',
                    value=25000.0,
                    description='Çeşitlendirme 2',
                    purchase_date='01/01/2024',
                    purchase_cost=22000.0,
                    quantity=250.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='DIV2',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=2,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Altın',
                    name='Çeşit 3',
                    value=25000.0,
                    description='Çeşitlendirme 3',
                    purchase_date='01/01/2024',
                    purchase_cost=22000.0,
                    quantity=25.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='DIV3',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Kripto',
                    name='Çeşit 4',
                    value=25000.0,
                    description='Çeşitlendirme 4',
                    purchase_date='01/01/2024',
                    purchase_cost=20000.0,
                    quantity=2.5,
                    unit_price=10000.0,
                    currency='TRY',
                    symbol='DIV4',
                    risk_level='Yüksek',
                    liquidity='Likit',
                    sector_id=3,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy toplam değeri
            total_value = get_total_assets(self.tenant_id)
            assert total_value == 100000.0, f"Beklenen toplam değer: 100000.0, Alınan: {total_value}"

            # Varlık sayısı
            asset_count = Asset.query.filter_by(tenant_id=self.tenant_id).count()
            assert asset_count == 4, f"Beklenen varlık sayısı: 4, Alınan: {asset_count}"

            # Her bir varlığın portföydeki oranı
            for asset in assets:
                asset_allocation = (asset.value / total_value) * 100
                assert asset_allocation == 25.0, f"Beklenen varlık dağılımı: 25.0%, Alınan: {asset_allocation}%"

            # Çeşitlendirme oranı (her varlık %25'ten az olmamalı)
            is_well_diversified = all((asset.value / total_value) <= 0.30 for asset in assets)
            assert is_well_diversified, "Portföy iyi çeşitlendirilmiş olmalı"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
