"""Asset constructor parameter validation tests."""

import pytest

from models import Asset, AssetSector
from shared.decimal_precision import to_decimal


def test_asset_constructor_valid_params(app):
    """Test Asset constructor with valid parameters."""
    with app.app_context():
        # Create a test sector
        sector = AssetSector(name="Test Sector")
        from models import db
        db.session.add(sector)
        db.session.flush()

        valid_params = {
            'type': 'Hisse Senedi',
            'name': 'Test Asset',
            'value': to_decimal(1000),
            'purchase_date': '2025-01-01',
            'purchase_cost': to_decimal(1000),
            'quantity': to_decimal(10),
            'unit_price': to_decimal(100),
            'currency': 'TRY',
            'symbol': 'TEST',
            'risk_level': 'Orta',
            'liquidity': 'Likit',
            'sector_id': sector.id,
            'tenant_id': 'default'
        }

        asset = Asset(**valid_params)

        assert asset.type == 'Hisse Senedi'
        assert asset.name == 'Test Asset'
        assert asset.value == to_decimal(1000)
        assert asset.sector_id == sector.id
        assert asset.tenant_id == 'default'

        db.session.rollback()


def test_asset_constructor_invalid_sync_cash_param(app):
    """Test Asset constructor rejects sync_cash parameter (not in model)."""
    with app.app_context():
        sector = AssetSector(name="Test Sector")
        from models import db
        db.session.add(sector)
        db.session.flush()

        valid_params = {
            'type': 'Hisse Senedi',
            'name': 'Test Asset',
            'value': to_decimal(1000),
            'purchase_date': '2025-01-01',
            'purchase_cost': to_decimal(1000),
            'quantity': to_decimal(10),
            'unit_price': to_decimal(100),
            'currency': 'TRY',
            'symbol': 'TEST',
            'risk_level': 'Orta',
            'liquidity': 'Likit',
            'sector_id': sector.id,
            'tenant_id': 'default'
        }

        # Add invalid parameter
        invalid_params = valid_params.copy()
        invalid_params['sync_cash'] = False  # This parameter doesn't exist in Asset model

        with pytest.raises(TypeError) as exc_info:
            Asset(**invalid_params)

        assert "sync_cash" in str(exc_info.value)
        assert "invalid keyword argument" in str(exc_info.value)

        db.session.rollback()


def test_asset_constructor_missing_required_params(app):
    """Test Asset constructor allows missing params but database validation catches them."""
    with app.app_context():
        # SQLAlchemy allows object creation with missing required params
        # Database validation will catch it on commit
        asset = Asset(
            type='Hisse Senedi',
            name='Test Asset',
            value=to_decimal(1000),
            purchase_date='2025-01-01',
            purchase_cost=to_decimal(1000),
            quantity=to_decimal(10),
            unit_price=to_decimal(100),
            currency='TRY',
            symbol='TEST',
            risk_level='Orta',
            liquidity='Likit',
            tenant_id='default'
            # sector_id is missing (required in DB)
        )

        # Object creation succeeds, but DB commit will fail
        from models import db
        db.session.add(asset)

        with pytest.raises(Exception):  # Will fail on commit due to NOT NULL constraint
            db.session.commit()

        db.session.rollback()


def test_asset_constructor_all_model_fields(app):
    """Test Asset constructor accepts all fields defined in the model."""
    with app.app_context():
        sector = AssetSector(name="Test Sector")
        from models import db
        db.session.add(sector)
        db.session.flush()

        all_params = {
            'type': 'Hisse Senedi',
            'name': 'Test Asset',
            'value': to_decimal(1000),
            'description': 'Test description',
            'purchase_date': '2025-01-01',
            'purchase_cost': to_decimal(1000),
            'quantity': to_decimal(10),
            'unit_price': to_decimal(100),
            'currency': 'TRY',
            'symbol': 'TEST',
            'risk_level': 'Orta',
            'liquidity': 'Likit',
            'sector_id': sector.id,
            'notes': 'Test notes',
            'monthly_rent': to_decimal(500),
            'is_admin_generated': True,
            'last_updated': '2025-01-01',
            'tenant_id': 'default'
        }

        asset = Asset(**all_params)

        assert asset.description == 'Test description'
        assert asset.notes == 'Test notes'
        assert asset.monthly_rent == to_decimal(500)
        assert asset.is_admin_generated
        assert asset.last_updated == '2025-01-01'

        db.session.rollback()
