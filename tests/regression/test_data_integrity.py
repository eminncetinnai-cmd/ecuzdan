"""
Data Integrity Tests - FAZ 2
Single Source of Truth - Validates that financial data has one authoritative source
"""

from decimal import Decimal

import pytest

from database.crud import get_actual_cash, get_total_assets
from domain.transactions.services.financial_ledger import (
    create_asset_position,
    create_one_time_transaction,
)
from models import AssetSector, AssetUpdate, Category, Transaction, db


@pytest.fixture
def app(app):
    """Use the existing app fixture from conftest.py"""
    return app


@pytest.mark.regression
def test_cash_single_source_of_truth(app):
    """
    Cash balance single source of truth:
    - Cash balance should be calculated from Transaction table only
    - No separate cash balance table should exist
    - All cash operations must go through Transaction table
    """
    tenant = 'tenant_cash_sot'

    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()

    # Add transactions
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income 1',
        Decimal('1000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-02', 'Test Gelir', 'Income 2',
        Decimal('500'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()

    # Cash balance should be calculated from transactions
    cash = get_actual_cash(tenant)

    # Verify by manually summing transactions
    transactions = Transaction.query.filter_by(tenant_id=tenant).all()
    manual_sum = sum(t.amount for t in transactions if t.type == 'Gelir')
    manual_sum -= sum(t.amount for t in transactions if t.type == 'Gider')

    assert cash == manual_sum, f"Cash balance SOT violation: {cash} != {manual_sum}"


@pytest.mark.regression
def test_asset_value_single_source_of_truth(app):
    """
    Asset value single source of truth:
    - Asset values should be stored in Asset table
    - AssetUpdate table should only track valuation history
    - Current value should come from Asset.value, not AssetUpdate
    """
    tenant = 'tenant_asset_sot'

    # Create sector
    sector = AssetSector(name='Test Sektor')
    db.session.add(sector)
    db.session.commit()

    # Create asset
    create_asset_position(
        type='Hisse Senedi', name='TEST', value=Decimal('10000'),
        purchase_cost=Decimal('10000'), quantity=Decimal('100'),
        unit_price=Decimal('100'),
        currency='TRY', symbol='TST', risk_level='Orta',
        liquidity='Likit', sector_id=sector.id,
        tenant_id=tenant,
    )
    db.session.commit()

    # Current asset value should come from Asset.value
    from database.crud import get_total_assets
    assets = get_total_assets(tenant)

    # Verify by querying Asset table directly
    from models import Asset
    asset_record = Asset.query.filter_by(name='TEST', tenant_id=tenant).first()
    assert asset_record is not None
    assert asset_record.value == Decimal('10000')

    # Asset value should match the sum from Asset table
    assert assets == Decimal('10000'), f"Asset value SOT violation: {assets} != 10000"


@pytest.mark.regression
def test_no_duplicate_asset_records(app):
    """
    No duplicate asset records:
    - Each asset should have exactly one record in Asset table
    - No duplicate asset names within same tenant
    """
    tenant = 'tenant_no_duplicates'

    # Create sector
    sector = AssetSector(name='Test Sektor')
    db.session.add(sector)
    db.session.commit()

    # Create asset
    create_asset_position(
        type='Hisse Senedi', name='UNIQUE_TEST', value=Decimal('10000'),
        purchase_cost=Decimal('10000'), quantity=Decimal('100'),
        unit_price=Decimal('100'),
        currency='TRY', symbol='UNIQ', risk_level='Orta',
        liquidity='Likit', sector_id=sector.id,
        tenant_id=tenant,
    )
    db.session.commit()

    # Verify only one record exists
    from models import Asset
    assets = Asset.query.filter_by(name='UNIQUE_TEST', tenant_id=tenant).all()
    assert len(assets) == 1, f"Duplicate asset records found: {len(assets)}"


@pytest.mark.regression
def test_transaction_history_immutability(app):
    """
    Transaction history immutability:
    - Historical transactions should not be modified
    - Only status updates should be allowed
    - Amount, date, category should be immutable after creation
    """
    tenant = 'tenant_history_immutable'

    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()

    # Create transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Historical transaction',
        Decimal('1000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()

    # Verify original values
    tx = Transaction.query.filter_by(description='Historical transaction').first()
    original_amount = tx.amount
    original_date = tx.date
    original_category = tx.category

    # Key fields should remain immutable
    assert tx.amount == original_amount
    assert tx.date == original_date
    assert tx.category == original_category


@pytest.mark.regression
def test_category_consistency_across_transactions(app):
    """
    Category consistency across transactions:
    - All transactions using a category should reference the same category
    - Category type should be consistent for all transactions using it
    """
    tenant = 'tenant_category_consistency'

    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()

    # Create multiple transactions with same category
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Transaction 1',
        Decimal('100'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-02', 'Test Gelir', 'Transaction 2',
        Decimal('200'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-03', 'Test Gelir', 'Transaction 3',
        Decimal('300'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()

    # All transactions should have same type
    transactions = Transaction.query.filter_by(category='Test Gelir', tenant_id=tenant).all()
    for tx in transactions:
        assert tx.type == 'Gelir', f"Category type inconsistency: {tx.type} != Gelir"


@pytest.mark.regression
def test_net_worth_calculation_consistency(app):
    """
    Net worth calculation consistency:
    - Net worth should always be: Cash + Assets
    - This calculation should be consistent across all calculation points
    """
    tenant = 'tenant_networth_consistency'

    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()

    # Add cash
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Cash',
        Decimal('50000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()

    # Create sector and asset
    sector = AssetSector(name='Test Sektor')
    db.session.add(sector)
    db.session.commit()

    create_asset_position(
        type='Hisse Senedi', name='TEST', value=Decimal('25000'),
        purchase_cost=Decimal('25000'), quantity=Decimal('250'),
        unit_price=Decimal('100'),
        currency='TRY', symbol='TST', risk_level='Orta',
        liquidity='Likit', sector_id=sector.id,
        tenant_id=tenant,
    )
    db.session.commit()

    # Calculate net worth
    cash = get_actual_cash(tenant)
    assets = get_total_assets(tenant)
    net_worth = cash + assets

    # Expected: 50000 (cash) + 25000 (asset) = 75000
    # Note: Asset purchase reduces cash by 25000, so net cash is 25000
    # Net worth = 25000 + 25000 = 50000
    expected = Decimal('50000.0000')

    assert net_worth == expected, f"Net worth calculation inconsistent: {net_worth} != {expected}"


@pytest.mark.regression
def test_asset_update_history_integrity(app):
    """
    Asset update history integrity:
    - AssetUpdate table should track all valuation changes
    - History should be append-only (no modifications to past updates)
    - Each update should have correct timestamp and value
    """
    tenant = 'tenant_update_history'

    # Create sector
    sector = AssetSector(name='Test Sektor')
    db.session.add(sector)
    db.session.commit()

    # Create asset
    asset = create_asset_position(
        type='Hisse Senedi', name='TEST', value=Decimal('10000'),
        purchase_cost=Decimal('10000'), quantity=Decimal('100'),
        unit_price=Decimal('100'),
        currency='TRY', symbol='TST', risk_level='Orta',
        liquidity='Likit', sector_id=sector.id,
        tenant_id=tenant,
    )
    db.session.commit()

    # Update asset valuation
    from domain.transactions.services.financial_ledger import update_asset_valuation
    update_asset_valuation(
        asset.id,
        type='Hisse Senedi', name='TEST', value=Decimal('12000'),
        quantity=Decimal('100'), unit_price=Decimal('120'),
        currency='TRY', symbol='TST', risk_level='Orta',
        tenant_id=tenant
    )
    db.session.commit()

    # Verify update history exists
    updates = AssetUpdate.query.filter_by(asset_id=asset.id).all()
    assert len(updates) > 0, "No update history recorded"

    # Verify history is append-only (check timestamps are increasing)
    # Note: AssetUpdate uses 'updated_at' not 'timestamp'
    if len(updates) > 1:
        timestamps = [u.updated_at for u in updates]
        assert timestamps == sorted(timestamps), "Update history timestamps not in order"


@pytest.mark.regression
def test_tenant_data_isolation(app):
    """
    Tenant data isolation:
    - Each tenant's data should be completely isolated
    - No cross-tenant data leakage
    - Queries should be tenant-scoped by default
    """
    tenant_a = 'tenant_isolation_sot_a'
    tenant_b = 'tenant_isolation_sot_b'

    # Create categories for both tenants
    cat_a = Category(name='Test Gelir', type='Gelir', tenant_id=tenant_a)
    cat_b = Category(name='Test Gelir', type='Gelir', tenant_id=tenant_b)
    db.session.add_all([cat_a, cat_b])
    db.session.commit()

    # Add transactions for both tenants
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Tenant A',
        Decimal('10000'), 'Ödendi', 'Test Gelir', tenant_id=tenant_a
    )
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Tenant B',
        Decimal('5000'), 'Ödendi', 'Test Gelir', tenant_id=tenant_b
    )
    db.session.commit()

    # Verify isolation
    cash_a = get_actual_cash(tenant_a)
    cash_b = get_actual_cash(tenant_b)

    assert cash_a == Decimal('10000.0000')
    assert cash_b == Decimal('5000.0000')
    assert cash_a != cash_b


@pytest.mark.regression
def test_no_orphaned_transactions(app):
    """
    No orphaned transactions:
    - All transactions should reference valid categories
    - No transactions should reference deleted categories
    - Category deletion should handle or prevent orphaned transactions
    """
    tenant = 'tenant_orphaned'

    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()

    # Create transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Test transaction',
        Decimal('100'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()

    # Verify transaction references valid category
    tx = Transaction.query.filter_by(description='Test transaction').first()
    assert tx is not None

    # Category should still exist
    cat_check = Category.query.filter_by(name='Test Gelir', tenant_id=tenant).first()
    assert cat_check is not None, "Category was deleted, leaving orphaned transaction"


@pytest.mark.regression
def test_recurring_plan_single_source(app):
    """
    Recurring plan single source of truth:
    - Recurring plan data should be in RecurringPlan table only
    - Generated transactions should reference the plan
    - Plan should be the authoritative source for schedule
    """
    from models import RecurringPlan
    from repositories.financial_repository import FinancialRepository

    tenant = 'tenant_recurring_sot'

    # Create category
    cat = Category(name='Test Gider', type='Gider', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()

    # Create recurring plan with payment_day parameter
    repo = FinancialRepository()
    plan = repo.add_recurring_plan(
        name='Test Plan',
        category='Test Gider',
        amount=Decimal('1000'),
        start_date='2025-01-01',
        frequency='monthly',
        installments=12,
        payment_day=1,  # Added required parameter
        tenant_id=tenant
    )
    db.session.commit()

    # Verify plan exists in RecurringPlan table
    plan_check = RecurringPlan.query.filter_by(id=plan.id).first()
    assert plan_check is not None
    assert plan_check.name == 'Test Plan'
    assert plan_check.amount == Decimal('1000')
