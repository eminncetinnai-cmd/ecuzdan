"""Unit tests for AssetFactory."""

import pytest

from infrastructure.demo.factories.asset_factory import AssetFactory
from models import AssetSector, db
from shared.decimal_precision import to_decimal


@pytest.fixture
def asset_factory():
    """Create an AssetFactory instance for testing."""
    return AssetFactory(tenant_id='test_tenant')


@pytest.fixture
def test_sector(app):
    """Create a test sector for asset creation."""
    sector = AssetSector(name="Test Sector")
    db.session.add(sector)
    db.session.commit()
    yield sector
    db.session.delete(sector)
    db.session.commit()


def test_asset_factory_create_asset_no_sync_cash_param(asset_factory, test_sector, app):
    """Test AssetFactory.create_asset does not pass sync_cash to Asset constructor."""
    with app.app_context():
        # Mock category validation to always return True
        original_is_valid = asset_factory.category_service.is_valid_category
        asset_factory.category_service.is_valid_category = lambda x, y: True

        asset = asset_factory.create_asset(
            asset_type='Hisse Senedi',
            name='Test Asset',
            symbol='TEST',
            value=1000,
            purchase_date='2025-01-01',
            purchase_cost=1000,
            quantity=10,
            unit_price=100,
            currency='TRY',
            risk_level='Orta',
            liquidity='Likit',
            sector_id=test_sector.id,
            description='Test description',
            notes='Test notes',
            is_admin_generated=True
        )

        assert asset is not None
        assert asset.type == 'Hisse Senedi'
        assert asset.name == 'Test Asset'
        assert asset.symbol == 'TEST'
        assert asset.value == to_decimal(1000)
        assert asset.sector_id == test_sector.id
        assert asset.is_admin_generated
        assert asset.tenant_id == 'test_tenant'

        # Asset is not persisted to DB by factory, so no need to delete
        # Restore original method
        asset_factory.category_service.is_valid_category = original_is_valid


def test_asset_factory_create_asset_without_sector_creates_default(asset_factory, app):
    """Test AssetFactory.create_asset creates default sector when sector_id is None."""
    with app.app_context():
        # Mock category validation
        original_is_valid = asset_factory.category_service.is_valid_category
        asset_factory.category_service.is_valid_category = lambda x, y: True

        asset = asset_factory.create_asset(
            asset_type='Hisse Senedi',
            name='Test Asset',
            symbol='TEST',
            value=1000,
            purchase_date='2025-01-01',
            purchase_cost=1000,
            quantity=10,
            unit_price=100,
            currency='TRY',
            risk_level='Orta',
            liquidity='Likit',
            sector_id=None  # Should create default 'Genel' sector
        )

        assert asset is not None
        assert asset.sector_id is not None
        assert asset.sector_id > 0

        # Verify 'Genel' sector was created
        general_sector = AssetSector.query.filter_by(name='Genel').first()
        assert general_sector is not None
        assert asset.sector_id == general_sector.id

        # Clean up sector (asset is not persisted)
        db.session.delete(general_sector)
        db.session.commit()

        asset_factory.category_service.is_valid_category = original_is_valid


def test_asset_factory_get_or_create_sector(asset_factory, app):
    """Test AssetFactory.get_or_create_sector creates sector if not exists."""
    with app.app_context():
        # Get non-existent sector (should create it)
        sector = asset_factory.get_or_create_sector('New Test Sector')

        assert sector is not None
        assert sector.name == 'New Test Sector'

        # Get existing sector (should return same instance)
        sector2 = asset_factory.get_or_create_sector('New Test Sector')

        assert sector.id == sector2.id
        assert sector.name == sector2.name

        db.session.delete(sector)
        db.session.commit()


def test_asset_factory_create_asset_valuation(asset_factory):
    """Test AssetFactory.create_asset_valuation returns correct data structure."""
    valuation_data = asset_factory.create_asset_valuation(
        asset_id=1,
        old_value=1000,
        new_value=1100,
        old_unit_price=100,
        new_unit_price=110,
        update_type='manual',
        notes='Test valuation',
        updated_at='2025-01-01'
    )

    assert valuation_data is not None
    assert valuation_data['asset_id'] == 1
    assert valuation_data['old_value'] == to_decimal(1000)
    assert valuation_data['new_value'] == to_decimal(1100)
    assert valuation_data['old_unit_price'] == to_decimal(100)
    assert valuation_data['new_unit_price'] == to_decimal(110)
    assert valuation_data['update_type'] == 'manual'
    assert valuation_data['notes'] == 'Test valuation'
