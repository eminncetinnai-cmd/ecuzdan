"""Integration tests for demo data generation from settings page."""

import pytest
from infrastructure.demo.demo_data_orchestrator import generate_advanced_demo_data
from models import User, Transaction, Asset, RecurringPlan, db


@pytest.fixture
def test_user(app):
    """Create a test user for demo data generation."""
    user = User(
        username='test_demo_user',
        email='test_demo@example.com',
        tenant_id='test_tenant'
    )
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


def test_generate_advanced_demo_data_success(test_user):
    """Test demo data generation from settings page succeeds without errors."""
    # Clear any existing demo data
    Transaction.query.filter_by(tenant_id=test_user.tenant_id).delete()
    Asset.query.filter_by(tenant_id=test_user.tenant_id).delete()
    RecurringPlan.query.filter_by(tenant_id=test_user.tenant_id).delete()
    db.session.commit()
    
    # Generate demo data
    stats = generate_advanced_demo_data(
        user_id=test_user.id,
        start_year=2025,
        end_year=2025
    )
    
    # Verify statistics
    assert stats is not None
    assert stats['transactions'] > 0, "Should generate transactions"
    assert stats['recurring_plans'] > 0, "Should generate recurring plans"
    assert stats['assets'] > 0, "Should generate assets"
    assert stats['asset_valuations'] > 0, "Should generate asset valuations"
    
    # Verify data was actually created
    transactions = Transaction.query.filter_by(tenant_id=test_user.tenant_id).all()
    assert len(transactions) > 0, "Transactions should exist in database"
    
    assets = Asset.query.filter_by(tenant_id=test_user.tenant_id).all()
    assert len(assets) > 0, "Assets should exist in database"
    
    plans = RecurringPlan.query.filter_by(tenant_id=test_user.tenant_id).all()
    assert len(plans) > 0, "Recurring plans should exist in database"
    
    # Cleanup
    Transaction.query.filter_by(tenant_id=test_user.tenant_id).delete()
    Asset.query.filter_by(tenant_id=test_user.tenant_id).delete()
    RecurringPlan.query.filter_by(tenant_id=test_user.tenant_id).delete()
    db.session.commit()


def test_generate_advanced_demo_data_no_sync_cash_error(test_user):
    """Test demo data generation does not raise sync_cash TypeError."""
    # This test specifically checks for the sync_cash error that was fixed
    try:
        stats = generate_advanced_demo_data(
            user_id=test_user.id,
            start_year=2025,
            end_year=2025
        )
        assert stats is not None
    except TypeError as e:
        if "sync_cash" in str(e):
            pytest.fail(f"sync_cash error should not occur: {e}")
        raise


def test_generate_advanced_demo_data_assets_have_sectors(test_user):
    """Test all generated assets have valid sector_id (required field)."""
    # Clear existing data
    Asset.query.filter_by(tenant_id=test_user.tenant_id).delete()
    db.session.commit()
    
    # Generate demo data
    stats = generate_advanced_demo_data(
        user_id=test_user.id,
        start_year=2025,
        end_year=2025
    )
    
    # Verify all assets have sector_id
    assets = Asset.query.filter_by(tenant_id=test_user.tenant_id).all()
    for asset in assets:
        assert asset.sector_id is not None, f"Asset {asset.name} should have sector_id"
        assert asset.sector_id > 0, f"Asset {asset.name} should have valid sector_id"
    
    # Cleanup
    Asset.query.filter_by(tenant_id=test_user.tenant_id).delete()
    db.session.commit()
