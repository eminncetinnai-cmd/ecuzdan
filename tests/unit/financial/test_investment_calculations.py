"""
Yatırım Hesaplamaları Testleri
Varlık değeri, getirisi, portföy değeri, getirisi ve risk analizi testleri
"""


import pytest

from database import get_total_assets
from models import Asset, AssetSector, AssetType, Tenant, User, db


class TestInvestmentCalculations:
    """Yatırım hesaplamaları test sınıfı"""

    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Test öncesi kurulum"""
        with app.app_context():
            # Test tenant oluştur
            tenant = Tenant(id='test_investment', name='Test Investment Tenant')
            db.session.add(tenant)
            db.session.commit()

            # Test kullanıcı oluştur
            user = User(
                username='test_investment_user',
                password='test123',
                tenant_id=tenant.id
            )
            db.session.add(user)
            db.session.commit()

            # Test varlık tipleri oluştur
            asset_types = ['Hisse Senedi', 'Fon', 'Altın', 'Kripto']
            for type_name in asset_types:
                if not AssetType.query.filter_by(name=type_name).first():
                    asset_type = AssetType(name=type_name)
                    db.session.add(asset_type)
            db.session.commit()

            # Test varlık sektörleri oluştur
            if not AssetSector.query.filter_by(name='Teknoloji').first():
                sector = AssetSector(name='Teknoloji')
                db.session.add(sector)
            db.session.commit()

            self.tenant_id = tenant.id
            self.user_id = user.id

    def test_asset_value_calculation(self, app):
        """Varlık değeri hesaplama testi"""
        with app.app_context():
            # Test varlıkları oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Test Hisse 1',
                    value=10000.0,
                    description='Test hisse senedi',
                    purchase_date='01/01/2024',
                    purchase_cost=8000.0,
                    quantity=100.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='TEST1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Altın',
                    name='Test Altın',
                    value=5000.0,
                    description='Test altın',
                    purchase_date='01/01/2024',
                    purchase_cost=4000.0,
                    quantity=10.0,
                    unit_price=500.0,
                    currency='TRY',
                    symbol='XAUT',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Toplam varlık değerini hesapla
            total_assets = get_total_assets(self.tenant_id)

            assert total_assets == 15000.0, f"Beklenen toplam varlık: 15000.0, Alınan: {total_assets}"

    def test_asset_roi_calculation(self, app):
        """Varlık getirisi (ROI) hesaplama testi"""
        with app.app_context():
            # Test varlığı oluştur
            asset = Asset(
                type='Hisse Senedi',
                name='Test Hisse ROI',
                value=12000.0,
                description='Test hisse senedi ROI',
                purchase_date='01/01/2024',
                purchase_cost=10000.0,
                quantity=100.0,
                unit_price=120.0,
                currency='TRY',
                symbol='TESTROI',
                risk_level='Orta',
                liquidity='Likit',
                sector_id=1,
                tenant_id=self.tenant_id
            )
            db.session.add(asset)
            db.session.commit()

            # ROI hesaplama: (mevcut değer - maliyet) / maliyet * 100
            calculated_roi = ((float(asset.value) - float(asset.purchase_cost)) / float(asset.purchase_cost)) * 100
            expected_roi = 20.0
            assert abs(calculated_roi - expected_roi) < 0.1, f"ROI hesaplama hatası: Beklenen {expected_roi}, Alınan {calculated_roi}"

    def test_portfolio_value_calculation(self, app):
        """Portföy değeri hesaplama testi"""
        with app.app_context():
            # Çoklu varlık oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Portföy Hisse 1',
                    value=25000.0,
                    description='Portföy hisse senedi 1',
                    purchase_date='01/01/2024',
                    purchase_cost=20000.0,
                    quantity=250.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='PORT1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Fon',
                    name='Portföy Fon',
                    value=15000.0,
                    description='Portföy fon',
                    purchase_date='01/01/2024',
                    purchase_cost=12000.0,
                    quantity=150.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='PORTFON',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Kripto',
                    name='Portföy Kripto',
                    value=10000.0,
                    description='Portföy kripto',
                    purchase_date='01/01/2024',
                    purchase_cost=8000.0,
                    quantity=1.0,
                    unit_price=10000.0,
                    currency='TRY',
                    symbol='BTC',
                    risk_level='Yüksek',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy değerini hesapla
            portfolio_value = get_total_assets(self.tenant_id)

            assert portfolio_value == 50000.0, f"Beklenen portföy değeri: 50000.0, Alınan: {portfolio_value}"

    def test_portfolio_return_calculation(self, app):
        """Portföy getirisi hesaplama testi"""
        with app.app_context():
            # Portföy varlıkları oluştur
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Portföy Hisse',
                    value=30000.0,
                    description='Portföy hisse',
                    purchase_date='01/01/2024',
                    purchase_cost=25000.0,
                    quantity=300.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='PORT2',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
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
                    symbol='PORTFON2',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Portföy toplam değeri
            total_value = get_total_assets(self.tenant_id)
            assert total_value == 50000.0, f"Beklenen toplam değer: 50000.0, Alınan: {total_value}"

            # Portföy toplam maliyeti
            total_cost = sum(float(asset.purchase_cost) for asset in assets)
            assert total_cost == 43000.0, f"Beklenen toplam maliyet: 43000.0, Alınan: {total_cost}"

            # Portföy toplam getirisi
            portfolio_return = ((float(total_value) - total_cost) / total_cost) * 100
            expected_return = ((50000.0 - 43000.0) / 43000.0) * 100
            assert abs(portfolio_return - expected_return) < 0.1, "Portföy getirisi hesaplama hatası"

    def test_risk_level_classification(self, app):
        """Risk seviyesi sınıflandırma testi"""
        with app.app_context():
            # Farklı risk seviyelerinde varlıklar oluştur
            assets = [
                Asset(
                    type='Altın',
                    name='Düşük Risk Varlık',
                    value=10000.0,
                    description='Düşük risk',
                    purchase_date='01/01/2024',
                    purchase_cost=9000.0,
                    quantity=10.0,
                    unit_price=1000.0,
                    currency='TRY',
                    symbol='XAUT',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Hisse Senedi',
                    name='Orta Risk Varlık',
                    value=15000.0,
                    description='Orta risk',
                    purchase_date='01/01/2024',
                    purchase_cost=12000.0,
                    quantity=150.0,
                    unit_price=100.0,
                    currency='TRY',
                    symbol='RISK1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                ),
                Asset(
                    type='Kripto',
                    name='Yüksek Risk Varlık',
                    value=5000.0,
                    description='Yüksek risk',
                    purchase_date='01/01/2024',
                    purchase_cost=4000.0,
                    quantity=1.0,
                    unit_price=5000.0,
                    currency='TRY',
                    symbol='BTC',
                    risk_level='Yüksek',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=self.tenant_id
                )
            ]
            for asset in assets:
                db.session.add(asset)
            db.session.commit()

            # Risk seviyelerini kontrol et
            low_risk_assets = Asset.query.filter_by(risk_level='Düşük', tenant_id=self.tenant_id).count()
            medium_risk_assets = Asset.query.filter_by(risk_level='Orta', tenant_id=self.tenant_id).count()
            high_risk_assets = Asset.query.filter_by(risk_level='Yüksek', tenant_id=self.tenant_id).count()

            assert low_risk_assets == 1, f"Beklenen düşük risk varlık sayısı: 1, Alınan: {low_risk_assets}"
            assert medium_risk_assets == 1, f"Beklenen orta risk varlık sayısı: 1, Alınan: {medium_risk_assets}"
            assert high_risk_assets == 1, f"Beklenen yüksek risk varlık sayısı: 1, Alınan: {high_risk_assets}"

    def test_tenant_isolation(self, app):
        """Tenant bazlı yatırım izolasyonu testi"""
        with app.app_context():
            # İkinci tenant oluştur
            tenant2 = Tenant(id='test_investment_2', name='Test Investment Tenant 2')
            db.session.add(tenant2)
            db.session.commit()

            # Tenant 1 için varlık
            asset1 = Asset(
                type='Hisse Senedi',
                name='Tenant 1 Hisse',
                value=20000.0,
                description='Tenant 1 hisse',
                purchase_date='01/01/2024',
                purchase_cost=15000.0,
                quantity=200.0,
                unit_price=100.0,
                currency='TRY',
                symbol='T1HISSE',
                risk_level='Orta',
                liquidity='Likit',
                sector_id=1,
                tenant_id=self.tenant_id
            )
            db.session.add(asset1)

            # Tenant 2 için varlık
            asset2 = Asset(
                type='Hisse Senedi',
                name='Tenant 2 Hisse',
                value=30000.0,
                description='Tenant 2 hisse',
                purchase_date='01/01/2024',
                purchase_cost=25000.0,
                quantity=300.0,
                unit_price=100.0,
                currency='TRY',
                symbol='T2HISSE',
                risk_level='Orta',
                liquidity='Likit',
                sector_id=1,
                tenant_id=tenant2.id
            )
            db.session.add(asset2)
            db.session.commit()

            # Tenant 1 varlık değeri
            assets1 = get_total_assets(self.tenant_id)

            # Tenant 2 varlık değeri
            assets2 = get_total_assets(tenant2.id)

            assert assets1 == 20000.0, f"Tenant 1 beklenen varlık: 20000.0, Alınan: {assets1}"
            assert assets2 == 30000.0, f"Tenant 2 beklenen varlık: 30000.0, Alınan: {assets2}"
            assert assets1 != assets2, "Tenant varlık değerleri farklı olmalı"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
