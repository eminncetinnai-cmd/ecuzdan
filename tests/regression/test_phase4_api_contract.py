from __future__ import annotations

from decimal import Decimal

import pytest

from domain.planning.services.occurrence_repository import OccurrenceRepository
from models import (
    LedgerAdjustment,
    LedgerAuditEvent,
    PlanOccurrence,
    RecurringPlan,
    Tenant,
    Transaction,
    User,
    db,
)


def make_paid_transaction(tenant_id="default", amount="1000.0000"):
    transaction = Transaction(
        date="2026-08-20",
        category="Maaş",
        description="Phase 4 API original",
        type="Gelir",
        amount=Decimal(amount),
        status="Ödendi",
        tenant_id=tenant_id,
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction


@pytest.fixture
def authenticated_superadmin_client(client):
    user = User.query.filter_by(username="emin").first()
    with client.session_transaction() as session:
        session["user_id"] = user.id
        session["username"] = user.username
    return client


def make_plan(tenant_id="default"):
    plan = RecurringPlan(
        name="Phase 4 API Maaş Planı",
        category="Maaş",
        flow_type="Gelir",
        amount=Decimal("1000.0000"),
        installments=1,
        payment_day=20,
        start_date="2026-08-20",
        frequency="Aylık",
        plan_type="Taksit",
        status="Aktif",
        tenant_id=tenant_id,
    )
    db.session.add(plan)
    db.session.commit()
    return plan


@pytest.mark.regression
def test_adjustment_api_is_immutable_idempotent_and_audited(app, authenticated_superadmin_client):
    original = make_paid_transaction()
    original_id = original.id
    headers = {
        "Idempotency-Key": "phase4-api-adjustment-0001",
        "X-Request-ID": "phase4-request-0001",
    }
    payload = {
        "amount_delta": "250.0000",
        "reason_code": "amount_error",
        "reason_text": "API test tutar düzeltmesi",
    }

    first = authenticated_superadmin_client.post(
        f"/api/transactions/{original_id}/adjustments",
        json=payload,
        headers=headers,
    )
    second = authenticated_superadmin_client.post(
        f"/api/transactions/{original_id}/adjustments",
        json=payload,
        headers=headers,
    )

    assert first.status_code == 201, first.get_json()
    assert second.status_code == 200, second.get_json()
    assert second.get_json()["idempotency_replayed"] is True
    refreshed_original = db.session.get(Transaction, original_id)
    assert refreshed_original.status == "Ödendi"
    assert refreshed_original.amount == Decimal("1000.0000")
    assert LedgerAdjustment.query.filter_by(tenant_id="default").count() == 1
    assert LedgerAuditEvent.query.filter_by(tenant_id="default").count() == 2


@pytest.mark.regression
def test_occurrence_payment_api_updates_occurrence_and_payment_bridge(app, authenticated_superadmin_client):
    plan = make_plan()
    occurrence = OccurrenceRepository().get_or_create_occurrences(plan, "default")[0]

    listing = authenticated_superadmin_client.get(f"/api/plans/{plan.id}/occurrences")
    paid = authenticated_superadmin_client.post(
        f"/api/occurrences/{occurrence.id}/pay",
        json={"amount": "1000.0000", "payment_date": "2026-08-20", "notes": "API ödeme"},
        headers={"Idempotency-Key": "phase4-api-payment-0001"},
    )

    assert listing.status_code == 200, listing.get_json()
    assert listing.get_json()["data"]["items"][0]["status"] == "scheduled"
    assert paid.status_code == 200, paid.get_json()
    assert paid.get_json()["data"]["occurrence"]["status"] == "paid"
    refreshed_occurrence = db.session.get(PlanOccurrence, occurrence.id)
    assert refreshed_occurrence.status == "paid"
    assert refreshed_occurrence.transaction_id is not None
    assert paid.get_json()["data"]["payment"]["transaction_id"] == refreshed_occurrence.transaction_id


@pytest.mark.regression
def test_transaction_detail_and_adjustment_are_tenant_scoped(app, authenticated_superadmin_client):
    other_tenant = Tenant(id="phase4_other", name="Phase 4 Other")
    db.session.add(other_tenant)
    db.session.commit()
    other_transaction = make_paid_transaction(tenant_id="phase4_other")

    detail = authenticated_superadmin_client.get(f"/api/transactions/{other_transaction.id}")
    adjustment = authenticated_superadmin_client.post(
        f"/api/transactions/{other_transaction.id}/adjustments",
        json={
            "amount_delta": "100.0000",
            "reason_code": "user_request",
            "reason_text": "Tenant izolasyon testi",
        },
        headers={"Idempotency-Key": "phase4-api-cross-tenant-0001"},
    )

    assert detail.status_code == 404
    assert adjustment.status_code == 404
    assert PlanOccurrence.query.filter_by(tenant_id="phase4_other").count() == 0
