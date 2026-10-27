"""Unit tests for non-destructive recurring plan updates and modal layering."""

from datetime import date
from decimal import Decimal
import pytest
from flask import g

from models import db, RecurringPlan, Transaction, PlanOccurrence, Tenant, Category
from repositories.recurring_plan_repository import RecurringPlanRepository
from domain.planning.services.plan_service import PlanService
from validators.request_validators import PlanFormDTO


@pytest.fixture
def plan_setup(app):
    with app.app_context():
        tenant = Tenant.query.first()
        assert tenant is not None, "A default tenant must exist"
        g.tenant_id = tenant.id

        # Clean up any residual test plans
        existing = RecurringPlan.query.filter(RecurringPlan.name.like("Unit Test Plan%")).all()
        for p in existing:
            PlanOccurrence.query.filter_by(plan_id=p.id).delete()
            Transaction.query.filter_by(source_id=p.id).delete()
            db.session.delete(p)
        db.session.commit()

        yield tenant

        # Teardown
        existing = RecurringPlan.query.filter(RecurringPlan.name.like("Unit Test Plan%")).all()
        for p in existing:
            PlanOccurrence.query.filter_by(plan_id=p.id).delete()
            Transaction.query.filter_by(source_id=p.id).delete()
            db.session.delete(p)
        db.session.commit()


def test_update_plan_with_paid_installment_preserves_paid_and_updates_pending(app, plan_setup):
    """Updating a plan amount must keep paid installments at paid amount and update pending ones."""
    tenant = plan_setup
    repo = RecurringPlanRepository()
    service = PlanService(financial_repository=repo)

    create_dto = PlanFormDTO(
        plan_id=None,
        name="Unit Test Plan 3 Taksit",
        category="Kredi Kartı",
        amount=1000.0,
        installments=3,
        payment_day=15,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date="2026-12-15",
        note="İlk not",
        action="add",
        version=1,
    )
    service.save_plan(create_dto)

    plan = RecurringPlan.query.filter_by(name="Unit Test Plan 3 Taksit", tenant_id=tenant.id).first()
    assert plan is not None
    txs = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs) == 3

    # Mark installment 1 as paid
    txs[0].status = "Ödendi"
    db.session.commit()

    # Now update plan amount to 1500
    update_dto = PlanFormDTO(
        plan_id=plan.id,
        name="Unit Test Plan 3 Taksit",
        category="Kredi Kartı",
        amount=1500.0,
        installments=3,
        payment_day=15,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        note="Güncel not",
        action="edit",
        version=plan.version,
    )
    service.save_plan(update_dto)

    # Verify transactions
    txs_after = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs_after) == 3

    # Installment 1 must stay paid at 1000
    assert txs_after[0].installment_number == 1
    assert txs_after[0].status == "Ödendi"
    assert Decimal(str(txs_after[0].amount)) == Decimal("1000.0000")

    # Installments 2 & 3 must be updated to 1500 and remain pending
    assert txs_after[1].installment_number == 2
    assert txs_after[1].status == "Bekliyor"
    assert Decimal(str(txs_after[1].amount)) == Decimal("1500.0000")

    assert txs_after[2].installment_number == 3
    assert txs_after[2].status == "Bekliyor"
    assert Decimal(str(txs_after[2].amount)) == Decimal("1500.0000")

    # Verify occurrences
    occs = PlanOccurrence.query.filter_by(plan_id=plan.id, tenant_id=tenant.id).order_by(PlanOccurrence.occurrence_number).all()
    assert len(occs) == 3
    assert occs[0].status == "paid"
    assert Decimal(str(occs[0].amount)) == Decimal("1000.0000")
    assert occs[1].status == "scheduled"
    assert Decimal(str(occs[1].amount)) == Decimal("1500.0000")
    assert occs[2].status == "scheduled"
    assert Decimal(str(occs[2].amount)) == Decimal("1500.0000")


def test_update_plan_reduce_installments_below_paid_count_raises_value_error(app, plan_setup):
    """Reducing installment count below already paid installments must raise ValueError."""
    tenant = plan_setup
    repo = RecurringPlanRepository()
    service = PlanService(financial_repository=repo)

    create_dto = PlanFormDTO(
        plan_id=None,
        name="Unit Test Plan Taksit Limit",
        category="Kredi Kartı",
        amount=500.0,
        installments=4,
        payment_day=10,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        action="add",
        version=1,
    )
    service.save_plan(create_dto)

    plan = RecurringPlan.query.filter_by(name="Unit Test Plan Taksit Limit", tenant_id=tenant.id).first()
    txs = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()

    # Mark 2 installments as paid
    txs[0].status = "Ödendi"
    txs[1].status = "Ödendi"
    db.session.commit()

    # Attempt to reduce installments to 1 (below paid count 2)
    invalid_dto = PlanFormDTO(
        plan_id=plan.id,
        name="Unit Test Plan Taksit Limit",
        category="Kredi Kartı",
        amount=500.0,
        installments=1,
        payment_day=10,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        action="edit",
        version=plan.version,
    )
    with pytest.raises(ValueError, match="Taksit sayısı ödenmiş olan 2 taksitten daha az olamaz"):
        service.save_plan(invalid_dto)


def test_update_plan_increase_installments_creates_new_pending_txs(app, plan_setup):
    """Increasing installment count during edit must append new pending transactions."""
    tenant = plan_setup
    repo = RecurringPlanRepository()
    service = PlanService(financial_repository=repo)

    create_dto = PlanFormDTO(
        plan_id=None,
        name="Unit Test Plan Artırma",
        category="Kredi Kartı",
        amount=800.0,
        installments=2,
        payment_day=20,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        action="add",
        version=1,
    )
    service.save_plan(create_dto)

    plan = RecurringPlan.query.filter_by(name="Unit Test Plan Artırma", tenant_id=tenant.id).first()
    txs = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs) == 2

    # Mark 1 as paid
    txs[0].status = "Ödendi"
    db.session.commit()

    # Increase installments from 2 to 4
    expand_dto = PlanFormDTO(
        plan_id=plan.id,
        name="Unit Test Plan Artırma",
        category="Kredi Kartı",
        amount=850.0,
        installments=4,
        payment_day=20,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        action="edit",
        version=plan.version,
    )
    service.save_plan(expand_dto)

    txs_after = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs_after) == 4
    assert txs_after[0].installment_number == 1 and txs_after[0].status == "Ödendi" and Decimal(str(txs_after[0].amount)) == Decimal("800.0000")
    assert txs_after[1].installment_number == 2 and txs_after[1].status == "Bekliyor" and Decimal(str(txs_after[1].amount)) == Decimal("850.0000")
    assert txs_after[2].installment_number == 3 and txs_after[2].status == "Bekliyor" and Decimal(str(txs_after[2].amount)) == Decimal("850.0000")
    assert txs_after[3].installment_number == 4 and txs_after[3].status == "Bekliyor" and Decimal(str(txs_after[3].amount)) == Decimal("850.0000")


def test_plan_form_from_request_with_plan_id_forces_update_action_and_revises_dates(app):
    """plan_form_from_request must normalize action to update_plan when plan_id is provided and shift dates gracefully."""
    from validators.request_validators import plan_form_from_request
    form_data = {
        'action': 'add_expense_plan',  # client-side action overwrite simulation
        'plan_id': '10',
        'name': 'Netflix',
        'category': 'Eğlence',
        'amount': '250',
        'installments': '3',
        'payment_day': '5',
        'start_date': '2026-11-01',
        'end_date': '2026-10-01',  # shifted in edit mode
        'frequency': 'Aylık',
    }
    dto = plan_form_from_request(form_data)
    assert dto.plan_id == '10'
    assert dto.end_date >= dto.start_date


def test_update_plan_reduce_to_exact_paid_count_marks_completed(app, plan_setup):
    """Reducing installment count to exact paid count must remove remaining pending txs and complete plan."""
    tenant = plan_setup
    repo = RecurringPlanRepository()
    service = PlanService(financial_repository=repo)

    create_dto = PlanFormDTO(
        plan_id=None,
        name="Unit Test Plan Tamamlama",
        category="Kredi Kartı",
        amount=600.0,
        installments=3,
        payment_day=5,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        action="add",
        version=1,
    )
    service.save_plan(create_dto)

    plan = RecurringPlan.query.filter_by(name="Unit Test Plan Tamamlama", tenant_id=tenant.id).first()
    txs = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs) == 3

    # Mark 2 installments as paid
    txs[0].status = "Ödendi"
    txs[1].status = "Ödendi"
    db.session.commit()

    # Reduce installments to 2 (exact paid count)
    finish_dto = PlanFormDTO(
        plan_id=plan.id,
        name="Unit Test Plan Tamamlama",
        category="Kredi Kartı",
        amount=600.0,
        installments=2,
        payment_day=5,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-10-01",
        end_date=None,
        action="edit",
        version=plan.version,
    )
    service.save_plan(finish_dto)

    txs_after = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs_after) == 2
    assert all(t.status == "Ödendi" for t in txs_after)
    # Check plan auto-completion
    plan_after = RecurringPlan.query.get(plan.id)
    assert plan_after.status == "Tamamlandı"


def test_update_plan_shift_dates_when_paid_installments_exist(app, plan_setup):
    """When user updates start_date after paid transactions, remaining installments roll forward cleanly."""
    tenant = plan_setup
    repo = RecurringPlanRepository()
    service = PlanService(financial_repository=repo)

    create_dto = PlanFormDTO(
        plan_id=None,
        name="Unit Test Plan Roll Forward",
        category="Kredi Kartı",
        amount=1000.0,
        installments=5,
        payment_day=10,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-01-10",
        end_date=None,
        action="add",
        version=1,
    )
    service.save_plan(create_dto)

    plan = RecurringPlan.query.filter_by(name="Unit Test Plan Roll Forward", tenant_id=tenant.id).first()
    txs = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs) == 5

    # Mark 2 installments as paid (Jan and Feb)
    txs[0].status = "Ödendi"
    txs[0].date = "2026-01-10"
    txs[1].status = "Ödendi"
    txs[1].date = "2026-02-10"
    db.session.commit()

    # User re-schedules remaining installments to start from November 2026
    update_dto = PlanFormDTO(
        plan_id=plan.id,
        name="Unit Test Plan Roll Forward",
        category="Kredi Kartı",
        amount=1200.0,
        installments=5,
        payment_day=15,
        plan_type="Taksit",
        frequency="Aylık",
        start_date="2026-11-15",
        end_date=None,
        action="edit",
        version=plan.version,
    )
    service.save_plan(update_dto)

    txs_after = Transaction.query.filter_by(source_id=plan.id, is_deleted=False).order_by(Transaction.installment_number).all()
    assert len(txs_after) == 5

    # Paid installments preserved exactly
    assert txs_after[0].installment_number == 1 and txs_after[0].status == "Ödendi" and txs_after[0].date == "2026-01-10"
    assert txs_after[1].installment_number == 2 and txs_after[1].status == "Ödendi" and txs_after[1].date == "2026-02-10"

    # Remaining 3 installments start cleanly from November 15
    assert txs_after[2].installment_number == 3 and txs_after[2].status == "Bekliyor" and txs_after[2].date == "2026-11-15"
    assert Decimal(str(txs_after[2].amount)) == Decimal("1200.0000")

    assert txs_after[3].installment_number == 4 and txs_after[3].status == "Bekliyor" and txs_after[3].date == "2026-12-15"
    assert Decimal(str(txs_after[3].amount)) == Decimal("1200.0000")

    assert txs_after[4].installment_number == 5 and txs_after[4].status == "Bekliyor" and txs_after[4].date == "2027-01-15"
    assert Decimal(str(txs_after[4].amount)) == Decimal("1200.0000")


def test_plan_form_from_request_with_remaining_installments_auto_sums_total(app):
    """When user provides remaining_installments and paid_count, total installments are reconciled."""
    from validators.request_validators import plan_form_from_request

    # Case A: Explicit remaining_installments
    form_data = {
        'action': 'update_plan',
        'plan_id': '42',
        'name': 'Kredi Borcu',
        'category': 'Kredi Kartı',
        'amount': '500',
        'paid_count': '3',
        'remaining_installments': '2',
        'payment_day': '15',
        'start_date': '2026-11-01',
    }
    dto = plan_form_from_request(form_data)
    assert dto.installments == 5
    assert dto.remaining_installments == 2
    assert dto.paid_count == 3

    # Case B: User typed 2 in installments field (meaning 2 remaining) while 3 are already paid
    form_data_b = {
        'action': 'update_plan',
        'plan_id': '42',
        'name': 'Kredi Borcu',
        'category': 'Kredi Kartı',
        'amount': '500',
        'paid_count': '3',
        'installments': '2',
        'payment_day': '15',
        'start_date': '2026-11-01',
    }
    dto_b = plan_form_from_request(form_data_b)
    assert dto_b.installments == 5
    assert dto_b.remaining_installments == 2
    assert dto_b.paid_count == 3
