"""
Unit Tests — Transaction and Recurring Plan Repositories
repositories/transaction_repository.py ve repositories/recurring_plan_repository.py metodlarını test eder.
"""

import pytest

from models import Category, db
from repositories.recurring_plan_repository import RecurringPlanRepository
from repositories.transaction_repository import TransactionRepository


@pytest.fixture
def tx_repo(app):
    return TransactionRepository(database=db)


@pytest.fixture
def plan_repo(app):
    return RecurringPlanRepository(database=db)


@pytest.mark.unit
def test_transaction_repository_crud(tx_repo, app):
    tenant = 'tx-test-tenant-1'

    # Ensure Category exists
    cat = Category.query.filter_by(name='Maaş Test').first()
    if not cat:
        cat = Category(name='Maaş Test', type='Gelir')
        db.session.add(cat)
        db.session.commit()

    # Add transaction
    tx = tx_repo.add_transaction(
        date='2026-09-01',
        category='Maaş Test',
        description='Aylık Maaş',
        type_='Gelir',
        amount=50000,
        status='Bekliyor',
        tenant_id=tenant,
    )
    assert tx.id is not None
    assert tx.amount == 50000
    assert tx.status == 'Bekliyor'

    # Get transaction
    fetched = tx_repo.get_transaction(tx.id, tenant_id=tenant)
    assert fetched is not None
    assert fetched.description == 'Aylık Maaş'

    # Quick pay
    paid_tx = tx_repo.quick_pay_transaction(tx.id, tenant_id=tenant)
    assert paid_tx.status == 'Ödendi'

    # List transactions
    tx_list = tx_repo.list_transactions(tenant_id=tenant)
    assert len(tx_list) >= 1

    # Pagination
    page = tx_repo.transaction_page(page=1, per_page=10, tenant_id=tenant)
    assert page.total >= 1


@pytest.mark.unit
def test_recurring_plan_repository_crud(plan_repo, app):
    tenant = 'plan-test-tenant-1'

    # Ensure Category exists
    cat = Category.query.filter_by(name='Kira Test').first()
    if not cat:
        cat = Category(name='Kira Test', type='Gider')
        db.session.add(cat)
        db.session.commit()

    # Add recurring plan
    plan = plan_repo.add_recurring_plan(
        name='Ofis Kirası Test',
        category='Kira Test',
        amount=25000,
        installments=12,
        payment_day=5,
        start_date='2026-09-01',
        tenant_id=tenant,
        plan_type='Taksit',
    )
    assert plan.id is not None
    assert plan.name == 'Ofis Kirası Test'
    assert plan.installments == 12

    # Get recurring plan
    fetched_plan = plan_repo.get_recurring_plan_for_tenant(plan.id, tenant_id=tenant)
    assert fetched_plan is not None
    assert fetched_plan.amount == 25000

    # List recurring plans
    plans = plan_repo.list_recurring_plans(tenant_id=tenant)
    assert len(plans) >= 1

    # Create payment
    payment = plan_repo.create_payment(
        plan_id=plan.id,
        amount=25000,
        payment_date='2026-09-05',
        installment_number=1,
        notes='1. Taksit Ödemesi',
        tenant_id=tenant,
    )
    assert payment.id is not None
    assert payment.amount == 25000

    # Delete plan
    del_result = plan_repo.delete_plan(plan.id, tenant_id=tenant)
    assert del_result['success'] is True
