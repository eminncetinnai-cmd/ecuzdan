"""Integration tests for demo data generation from the settings flow."""

import pytest
from werkzeug.security import generate_password_hash

from infrastructure.demo.demo_data_orchestrator import generate_advanced_demo_data
from models import Asset, Category, RecurringPlan, Transaction, User, db


@pytest.fixture
def test_user(app):
    """Create and remove an isolated user for demo generation tests."""
    user = User(
        username='test_demo_user',
        email='test_demo@example.com',
        password=generate_password_hash('test123'),
        role='kullanici',
        tenant_id='default',
    )
    db.session.add(user)
    db.session.commit()
    yield user
    Transaction.query.filter_by(tenant_id=user.tenant_id).delete()
    Asset.query.filter_by(tenant_id=user.tenant_id).delete()
    RecurringPlan.query.filter_by(tenant_id=user.tenant_id).delete()
    db.session.delete(user)
    db.session.commit()


@pytest.fixture
def standard_categories(app):
    """Seed the standard categories required by the orchestrator."""
    from scripts.seed_standard_categories import STANDARD_CATEGORIES

    Category.query.filter_by(tenant_id=None).delete()
    for code, name, type_, sort_order, budget_limit in STANDARD_CATEGORIES:
        db.session.add(
            Category(
                code=code,
                name=name,
                type=type_,
                sort_order=sort_order,
                is_active=True,
                tenant_id=None,
                level=0,
                path='/',
                budget_limit=budget_limit,
            )
        )
    db.session.commit()
    yield
    Category.query.filter_by(tenant_id=None).delete()
    db.session.commit()


def _assert_generation_stats(stats):
    assert {'transactions', 'recurring_plans', 'assets', 'asset_valuations'} <= set(stats)
    assert all(isinstance(stats[key], int) and stats[key] >= 0 for key in stats)


@pytest.mark.integration
def test_generate_advanced_demo_data_success(test_user, standard_categories):
    stats = generate_advanced_demo_data(test_user.id, start_year=2025, end_year=2027)

    _assert_generation_stats(stats)
    assert Transaction.query.filter_by(tenant_id=test_user.tenant_id).count() > 0


@pytest.mark.integration
def test_generate_advanced_demo_data_no_sync_cash_error(test_user, standard_categories):
    stats = generate_advanced_demo_data(test_user.id, start_year=2025, end_year=2027)

    _assert_generation_stats(stats)


@pytest.mark.integration
def test_generate_advanced_demo_data_assets_have_sectors(test_user, standard_categories):
    stats = generate_advanced_demo_data(test_user.id, start_year=2025, end_year=2027)

    _assert_generation_stats(stats)
    assets = Asset.query.filter_by(tenant_id=test_user.tenant_id).all()
    assert all(asset.sector_id is not None for asset in assets)
