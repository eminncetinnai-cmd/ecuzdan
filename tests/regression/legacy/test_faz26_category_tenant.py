"""
Faz 2.6 — Kategori Tenant Izolasyonu ve Quick Transfer Testleri
"""

import pytest
from werkzeug.security import generate_password_hash

from database.crud import delete_category, update_category
from domain.transactions.services.financial_ledger import LedgerError, transfer_cash_to_asset
from models import Asset, AssetSector, AssetTransaction, Category, Tenant, Transaction, User, db


@pytest.fixture
def two_tenants(app):
    with app.app_context():
        t_a = Tenant(id='tenant_a26', name='Tenant A')
        t_b = Tenant(id='tenant_b26', name='Tenant B')
        db.session.add_all([t_a, t_b])
        db.session.flush()
        u_a = User(username='user_a26', password=generate_password_hash('x'),
                   role='kullanici', tenant_id='tenant_a26')
        u_b = User(username='user_b26', password=generate_password_hash('x'),
                   role='kullanici', tenant_id='tenant_b26')
        db.session.add_all([u_a, u_b])
        db.session.commit()
        yield {'t_a': t_a, 't_b': t_b}


class TestCategoryTenantIsolation:

    def test_A1_tenant_a_cat_not_visible_to_tenant_b(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='OzelKat_A26', type='Gelir', tenant_id='tenant_a26')
            db.session.add(cat)
            db.session.commit()
            from sqlalchemy import or_
            cats_b = Category.query.filter(
                or_(Category.tenant_id.is_(None), Category.tenant_id == 'tenant_b26')
            ).all()
            assert 'OzelKat_A26' not in [c.name for c in cats_b]

    def test_A2_global_category_visible_to_all(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='GlobalKat_A26', type='Gelir', tenant_id=None)
            db.session.add(cat)
            db.session.commit()
            from sqlalchemy import or_
            for tid in ['tenant_a26', 'tenant_b26']:
                names = [c.name for c in Category.query.filter(
                    or_(Category.tenant_id.is_(None), Category.tenant_id == tid)
                ).all()]
                assert 'GlobalKat_A26' in names, f"Global kategori {tid} icin gorunmuyor"

    def test_A3_cannot_update_other_tenants_category(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='KatB26', type='Gider', tenant_id='tenant_b26')
            db.session.add(cat)
            db.session.commit()
            with pytest.raises(ValueError, match="yetkiniz yok"):
                update_category(cat.id, 'YeniAd', 'Gelir', tenant_id='tenant_a26')

    def test_A4_cannot_delete_other_tenants_category(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='KatB26_del', type='Gider', tenant_id='tenant_b26')
            db.session.add(cat)
            db.session.commit()
            with pytest.raises(ValueError, match="yetkiniz yok"):
                delete_category(cat.id, tenant_id='tenant_a26')

    def test_A5_global_category_cannot_be_deleted(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='Sistem26', type='Gelir', tenant_id=None)
            db.session.add(cat)
            db.session.commit()
            with pytest.raises(ValueError, match="silinemez"):
                delete_category(cat.id, tenant_id='tenant_a26')

    def test_A5b_global_category_cannot_be_updated(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='Sistem26b', type='Gelir', tenant_id=None)
            db.session.add(cat)
            db.session.commit()
            with pytest.raises(ValueError):
                update_category(cat.id, 'YeniAd', 'Gider', tenant_id='tenant_a26')

    def test_A6_tenant_can_update_own_category(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='KatA26_upd', type='Gelir', tenant_id='tenant_a26')
            db.session.add(cat)
            db.session.commit()
            result = update_category(cat.id, 'KatA26_new', 'Gelir', tenant_id='tenant_a26')
            assert result.name == 'KatA26_new'

    def test_A7_tenant_can_delete_own_category(self, app, two_tenants):
        with app.app_context():
            cat = Category(name='KatA26_del', type='Gider', tenant_id='tenant_a26')
            db.session.add(cat)
            db.session.commit()
            assert delete_category(cat.id, tenant_id='tenant_a26') is True
            assert Category.query.filter_by(name='KatA26_del').first() is None


class TestQuickTransferInvariant:

    @pytest.fixture
    def transfer_asset(self, app, two_tenants):
        with app.app_context():
            sector = AssetSector(name='Genel26')
            db.session.add(sector)
            db.session.flush()

            asset = Asset(
                name='TestHisse26', type='Hisse Senedi',
                value=10000.0, quantity=100.0, unit_price=100.0,
                purchase_cost=10000.0, purchase_date='2024-01-01',
                currency='TRY', symbol='THS26', risk_level='Orta', liquidity='Likit',
                sector_id=sector.id, tenant_id='tenant_a26',
            )
            db.session.add(asset)
            db.session.commit()
            yield asset

    def test_B1_transfer_creates_tx_and_asset_tx(self, app, transfer_asset):
        with app.app_context():
            asset = Asset.query.filter_by(name='TestHisse26').first()
            before = Transaction.query.filter_by(source_id=asset.id, type='Yatırım').count()
            transfer_cash_to_asset(asset_id=asset.id, amount=5000.0,
                                   transfer_date='2025-06-01', tenant_id='tenant_a26')
            after = Transaction.query.filter_by(source_id=asset.id, type='Yatırım').count()
            atx = AssetTransaction.query.filter_by(asset_id=asset.id, transaction_type='buy').count()
            assert after >= before + 1
            assert atx >= 1

    def test_B2_transfer_wrong_tenant_raises(self, app, transfer_asset):
        with app.app_context():
            asset = Asset.query.filter_by(name='TestHisse26').first()
            with pytest.raises(LedgerError):
                transfer_cash_to_asset(asset_id=asset.id, amount=1000.0,
                                       transfer_date='2025-06-01', tenant_id='tenant_b26')

    def test_B3_transfer_negative_raises(self, app, transfer_asset):
        with app.app_context():
            asset = Asset.query.filter_by(name='TestHisse26').first()
            with pytest.raises(LedgerError):
                transfer_cash_to_asset(asset_id=asset.id, amount=-100.0,
                                       transfer_date='2025-06-01', tenant_id='tenant_a26')
