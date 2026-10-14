from decimal import Decimal

import pytest

from domain.planning.services.occurrence_repository import OccurrenceRepository
from domain.transactions.services.financial_ledger import (
    LedgerError,
    create_adjustment_transaction,
    create_reversal_transaction,
    mark_occurrence_paid,
)
from models import PlanOccurrence, RecurringPlan, Tenant, Transaction, db


def make_plan(tenant_id="default"):
    plan = RecurringPlan(
        name="Test Maaş Planı",
        category="Maaş",
        flow_type="Gelir",
        amount=Decimal("1000.0000"),
        installments=3,
        payment_day=10,
        start_date="2026-08-19",
        frequency="Aylık",
        plan_type="Taksit",
        status="Aktif",
        tenant_id=tenant_id,
    )
    db.session.add(plan)
    db.session.flush()
    return plan


def make_paid_transaction(description="Orijinal ödeme", amount="1000.0000"):
    transaction = Transaction(
        date="2026-08-20",
        category="Maaş",
        description=description,
        type="Gelir",
        amount=Decimal(amount),
        status="Ödendi",
        tenant_id="default",
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction


@pytest.mark.unit
def test_occurrence_schedule_is_idempotent_and_start_date_anchored(app):
    plan = make_plan()
    repository = OccurrenceRepository()

    first = repository.get_or_create_occurrences(plan, "default")
    second = repository.get_or_create_occurrences(plan, "default")

    assert len(first) == 3
    assert len(second) == 3
    assert [row.occurrence_number for row in second] == [1, 2, 3]
    assert [row.scheduled_date for row in second] == [
        "2026-09-10",
        "2026-10-10",
        "2026-11-10",
    ]
    assert PlanOccurrence.query.filter_by(plan_id=plan.id, tenant_id="default").count() == 3


@pytest.mark.unit
def test_mark_paid_is_idempotent_and_does_not_cross_tenant(app):
    plan = make_plan()
    occurrence = OccurrenceRepository().get_or_create_occurrences(plan, "default")[0]
    transaction = make_paid_transaction()
    repository = OccurrenceRepository()

    paid = repository.mark_paid(occurrence.id, transaction.id, "default")
    retried = repository.mark_paid(occurrence.id, transaction.id, "default")

    assert paid.id == retried.id == occurrence.id
    assert paid.status == "paid"
    assert paid.transaction_id == transaction.id

    other_tenant = Tenant(id="other", name="Other Tenant")
    db.session.add(other_tenant)
    db.session.commit()
    assert repository.list_pending(plan.id, "other") == []
    with pytest.raises(LookupError):
        repository.mark_paid(occurrence.id, transaction.id, "other")

    other_transaction = make_paid_transaction(description="Başka işlem")
    with pytest.raises(LedgerError):
        repository.mark_paid(occurrence.id, other_transaction.id, "default")


@pytest.mark.unit
def test_mark_occurrence_paid_bridges_payment_and_is_idempotent(app):
    plan = make_plan()
    occurrence = OccurrenceRepository().get_or_create_occurrences(plan, "default")[0]
    pending_transaction = Transaction(
        date=occurrence.scheduled_date,
        category=plan.category,
        description="Test Maaş Planı (1/3)",
        type="Gelir",
        amount=plan.amount,
        status="Bekliyor",
        installment_number=1,
        source_id=plan.id,
        source_type="plan",
        tenant_id="default",
    )
    db.session.add(pending_transaction)
    db.session.commit()

    payment = mark_occurrence_paid(
        occurrence.id,
        {
            "amount": Decimal("1000.0000"),
            "payment_date": occurrence.scheduled_date,
            "notes": "İlk ödeme",
        },
        "default",
    )
    retried_payment = mark_occurrence_paid(
        occurrence.id,
        {"amount": Decimal("1000.0000")},
        "default",
    )

    refreshed_occurrence = db.session.get(PlanOccurrence, occurrence.id)
    refreshed_transaction = db.session.get(Transaction, pending_transaction.id)
    assert payment.id == retried_payment.id
    assert refreshed_occurrence.status == "paid"
    assert refreshed_occurrence.transaction_id == pending_transaction.id
    assert refreshed_transaction.status == "Ödendi"


@pytest.mark.unit
def test_mark_skipped_is_idempotent(app):
    plan = make_plan()
    occurrence = OccurrenceRepository().get_or_create_occurrences(plan, "default")[0]
    repository = OccurrenceRepository()

    skipped = repository.mark_skipped(occurrence.id, "default")
    retried = repository.mark_skipped(occurrence.id, "default")

    assert skipped.id == retried.id == occurrence.id
    assert retried.status == "skipped"


@pytest.mark.unit
def test_adjustment_and_reversal_preserve_original_and_are_idempotent(app):
    original = make_paid_transaction()

    adjustment = create_adjustment_transaction(
        original.id,
        Decimal("250.0000"),
        "Tutar farkı",
        "default",
    )
    same_adjustment = create_adjustment_transaction(
        original.id,
        Decimal("250.0000"),
        "Tutar farkı",
        "default",
    )
    reversal = create_reversal_transaction(original.id, "İşlem iptali", "default")
    same_reversal = create_reversal_transaction(original.id, "İşlem iptali", "default")

    db.session.refresh(original)
    assert original.status == "Ödendi"
    assert original.amount == Decimal("1000.0000")
    assert original.is_deleted is False
    assert adjustment.id == same_adjustment.id
    assert adjustment.source_type == "adjustment"
    assert adjustment.amount == Decimal("250.0000")
    assert reversal.id == same_reversal.id
    assert reversal.source_type == "reversal"
    assert reversal.type == "Gider"
    assert reversal.amount == Decimal("1000.0000")


@pytest.mark.unit
def test_paid_transaction_direct_mutation_is_rejected(app):
    from domain.transactions.services.financial_ledger import (
        delete_one_time_transaction,
        update_one_time_transaction,
    )
    from repositories.financial_repository import FinancialRepository

    original = make_paid_transaction()

    with pytest.raises(LedgerError):
        update_one_time_transaction(
            original.id,
            "2026-08-21",
            "Maaş",
            "Değişiklik denemesi",
            Decimal("1200"),
            "Ödendi",
            tenant_id="default",
        )
    with pytest.raises(LedgerError):
        delete_one_time_transaction(original.id, tenant_id="default")
    with pytest.raises(LedgerError):
        FinancialRepository().update_transaction(
            original.id,
            "2026-08-21",
            "Maaş",
            "Repository update denemesi",
            Decimal("1200"),
            "Ödendi",
            tenant_id="default",
        )
    with pytest.raises(LedgerError):
        FinancialRepository().delete_transaction(original.id, tenant_id="default")

    assert db.session.get(Transaction, original.id).is_deleted is False


@pytest.mark.unit
def test_occurrence_sync_transitions_statuses_on_plan_cancellation(app):
    plan = make_plan()
    repository = OccurrenceRepository()
    occurrences = repository.get_or_create_occurrences(plan, "default")
    assert len(occurrences) == 3
    assert all(o.status == "scheduled" for o in occurrences)

    upcoming = repository.list_upcoming("default")
    assert any(o.plan_id == plan.id for o in upcoming)

    # Change plan status to İptal and re-sync
    plan.status = "İptal"
    db.session.commit()
    synced = repository.get_or_create_occurrences(plan, "default")
    assert all(o.status == "cancelled" for o in synced)

    # Upcoming queries exclude cancelled plan
    upcoming_after = repository.list_upcoming("default")
    assert not any(o.plan_id == plan.id for o in upcoming_after)

    # Reactivate plan to Aktif
    plan.status = "Aktif"
    db.session.commit()
    reactivated = repository.get_or_create_occurrences(plan, "default")
    assert any(o.status == "scheduled" for o in reactivated)


@pytest.mark.unit
def test_occurrence_mark_cancelled_is_idempotent(app):
    plan = make_plan()
    repository = OccurrenceRepository()
    occurrence = repository.get_or_create_occurrences(plan, "default")[0]
    cancelled = repository.mark_cancelled(occurrence.id, "default", reason="Test iptal")
    assert cancelled.status == "cancelled"
    assert cancelled.notes == "Test iptal"

    # Idempotent
    retried = repository.mark_cancelled(occurrence.id, "default")
    assert retried.status == "cancelled"


@pytest.mark.unit
def test_occurrence_syncs_with_paid_transactions(app):
    plan = make_plan()
    repository = OccurrenceRepository()
    occurrences = repository.get_or_create_occurrences(plan, "default")
    assert occurrences[0].status == "scheduled"

    tx = Transaction(
        date=occurrences[0].scheduled_date,
        category=plan.category,
        description=f"{plan.name} (1/3)",
        type=plan.flow_type,
        amount=plan.amount,
        status="Ödendi",
        installment_number=1,
        source_id=plan.id,
        source_type="plan",
        tenant_id="default",
    )
    db.session.add(tx)
    db.session.commit()

    synced_count = repository.sync_with_transactions("default", plan.id)
    assert synced_count >= 1

    refreshed = db.session.get(PlanOccurrence, occurrences[0].id)
    assert refreshed.status == "paid"
    assert refreshed.transaction_id == tx.id

    upcoming = repository.list_upcoming("default")
    upcoming_ids = [o.id for o in upcoming]
    assert occurrences[0].id not in upcoming_ids
