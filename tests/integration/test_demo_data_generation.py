"""Integration tests for demo data generation from the settings flow."""

import pytest
from werkzeug.security import generate_password_hash

from infrastructure.demo.admin_demo_data import clear_admin_demo_data
from infrastructure.demo.demo_data_orchestrator import generate_advanced_demo_data
from models import (
    Asset,
    BankAccount,
    BankStatementSnapshot,
    Category,
    LedgerAdjustment,
    PlanOccurrence,
    RecurringPlan,
    Transaction,
    User,
    db,
)


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
    clear_admin_demo_data(tenant_id=user.tenant_id)
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
    assert {'transactions', 'recurring_plans', 'assets', 'asset_valuations', 'bank_accounts'} <= set(stats)
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


@pytest.mark.integration
def test_generate_advanced_demo_data_comprehensive_conditions(test_user, standard_categories):
    """Verify all required financial conditions: accounts, statuses, transfers, soft-delete, reversals, closed assets."""
    stats = generate_advanced_demo_data(test_user.id, start_year=2025, end_year=2027)
    _assert_generation_stats(stats)

    tenant_id = test_user.tenant_id

    # 1. Bank accounts & statement snapshot
    bank_accounts = BankAccount.query.filter_by(tenant_id=tenant_id).all()
    assert len(bank_accounts) >= 4
    account_types = {ba.account_type for ba in bank_accounts}
    assert {'checking', 'credit_card', 'investment', 'cash'} <= account_types

    snapshot = BankStatementSnapshot.query.filter_by(tenant_id=tenant_id).first()
    assert snapshot is not None

    # 2. Transactions linked to bank accounts
    tx_with_account = Transaction.query.filter(
        Transaction.tenant_id == tenant_id,
        Transaction.bank_account_id.isnot(None),
    ).count()
    assert tx_with_account > 0

    # 3. Statuses: Ödendi, Bekliyor, Gecikti
    statuses = {
        tx.status
        for tx in Transaction.query.filter_by(tenant_id=tenant_id).all()
    }
    assert 'Ödendi' in statuses
    assert 'Bekliyor' in statuses
    assert 'Gecikti' in statuses

    # 4. Virman / Transfer transactions
    transfers = Transaction.query.filter_by(tenant_id=tenant_id, type='Transfer').all()
    assert len(transfers) > 0
    assert any(t.transfer_from and t.transfer_to for t in transfers)

    # 5. Soft-deleted transaction
    soft_deleted = Transaction.query.filter_by(tenant_id=tenant_id, is_deleted=True).first()
    assert soft_deleted is not None
    assert soft_deleted.deleted_at is not None

    # 6. Reversals (Ters Kayıt) & Adjustments (Düzeltme)
    reversals = Transaction.query.filter_by(tenant_id=tenant_id, source_type='reversal').all()
    assert len(reversals) > 0
    adjustments = Transaction.query.filter_by(tenant_id=tenant_id, source_type='adjustment').all()
    assert len(adjustments) > 0

    ledger_adjs = LedgerAdjustment.query.filter_by(tenant_id=tenant_id).all()
    adj_kinds = {la.kind for la in ledger_adjs}
    assert 'reversal' in adj_kinds
    assert 'adjustment' in adj_kinds

    # 7. Asset sales and closed asset
    closed_assets = Asset.query.filter_by(tenant_id=tenant_id, is_closed=True).all()
    assert len(closed_assets) > 0
    sale_txs = Transaction.query.filter_by(tenant_id=tenant_id, source_type='asset_sale').all()
    assert len(sale_txs) > 0

    # 8. Plan occurrences: paid, scheduled, skipped
    occurrences = PlanOccurrence.query.filter_by(tenant_id=tenant_id).all()
    assert len(occurrences) > 0
    occ_statuses = {occ.status for occ in occurrences}
    assert 'paid' in occ_statuses
    assert 'scheduled' in occ_statuses
    assert 'skipped' in occ_statuses

    # 9. Clear demo data cleans up all records cleanly
    clear_stats = clear_admin_demo_data(tenant_id=tenant_id)
    assert clear_stats['transactions'] > 0
    assert Transaction.query.filter_by(tenant_id=tenant_id).count() == 0
    assert Asset.query.filter_by(tenant_id=tenant_id).count() == 0
    assert RecurringPlan.query.filter_by(tenant_id=tenant_id).count() == 0
    assert BankAccount.query.filter_by(tenant_id=tenant_id).count() == 0
    assert BankStatementSnapshot.query.filter_by(tenant_id=tenant_id).count() == 0
    assert LedgerAdjustment.query.filter_by(tenant_id=tenant_id).count() == 0


@pytest.mark.integration
def test_reset_financial_data_for_tenant_cleans_bank_accounts_and_snapshots(test_user, standard_categories):
    """Verify that UserRepository.reset_financial_data_for_tenant cleanly purges bank accounts and snapshots."""
    from repositories.user_repository import UserRepository

    tenant_id = test_user.tenant_id
    generate_advanced_demo_data(test_user.id, start_year=2025, end_year=2027)

    assert BankAccount.query.filter_by(tenant_id=tenant_id).count() >= 4
    assert BankStatementSnapshot.query.filter_by(tenant_id=tenant_id).count() >= 1
    assert Transaction.query.filter_by(tenant_id=tenant_id).count() > 0

    repo = UserRepository(database=db)
    repo.reset_financial_data_for_tenant(tenant_id)
    db.session.commit()

    assert BankAccount.query.filter_by(tenant_id=tenant_id).count() == 0
    assert BankStatementSnapshot.query.filter_by(tenant_id=tenant_id).count() == 0
    assert Transaction.query.filter_by(tenant_id=tenant_id).count() == 0
    assert Asset.query.filter_by(tenant_id=tenant_id).count() == 0
    assert RecurringPlan.query.filter_by(tenant_id=tenant_id).count() == 0
