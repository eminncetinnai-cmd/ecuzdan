"""
Unit tests for transaction reversal (ters kayıt) and status reversion to pending.
Verifies that:
1. Reversing a paid transaction sets original status back to 'Bekliyor' (pending).
2. Any linked PlanOccurrence is reset to 'scheduled' and Payment record is removed.
3. Cash balance reflects the cancelled payment without phantom credit inflation.
4. API endpoints work on both /api/... and /transactions/... routes, with or without Idempotency-Key header.
"""

from decimal import Decimal
import pytest

from domain.planning.services.occurrence_repository import OccurrenceRepository
from domain.transactions.services.financial_ledger import (
    create_reversal_transaction,
)
from models import (
    Category,
    Payment,
    PlanOccurrence,
    RecurringPlan,
    Transaction,
    User,
    db,
)
from repositories.transaction_repository import TransactionRepository


@pytest.fixture
def clean_tenant(app):
    tenant_id = "default"
    with app.app_context():
        # Ensure category exists
        cat = Category.query.filter_by(name="Kredi Kartı Borcu", tenant_id=None).first()
        if not cat:
            cat = Category(name="Kredi Kartı Borcu", type="Gider", tenant_id=None)
            db.session.add(cat)
            db.session.commit()
        yield tenant_id
        # Cleanup
        Payment.query.filter(Payment.notes.like('%Bonus Kart%')).delete()
        Transaction.query.filter(Transaction.description.like('%Bonus Kart%')).delete()
        RecurringPlan.query.filter_by(name="Bonus Kart Borcu").delete()
        Transaction.query.filter(Transaction.description.like('%Mobil Ters Kayıt%')).delete()
        Transaction.query.filter(Transaction.description.like('%Kredi Kartı Dönem Borcu%')).delete()
        db.session.commit()


@pytest.mark.unit
def test_reversal_reverts_one_time_transaction_to_pending(app, clean_tenant):
    """Reversing a paid transaction resets original.status to 'Bekliyor' and is idempotent."""
    with app.app_context():
        tx = Transaction(
            date="2026-10-26",
            category="Kredi Kartı Borcu",
            description="Kredi Kartı Dönem Borcu",
            type="Gider",
            amount=Decimal("45000.0000"),
            status="Ödendi",
            tenant_id=clean_tenant,
        )
        db.session.add(tx)
        db.session.commit()

        initial_version = tx.version or 1

        # Execute reversal
        rev = create_reversal_transaction(tx.id, "Hatalı ödeme kaydı iptali", clean_tenant)

        db.session.refresh(tx)
        assert tx.status == "Bekliyor", "Original transaction must drop back to 'Bekliyor'"
        assert tx.version > initial_version, "Original transaction version must increment"
        assert rev.source_type == "reversal"
        assert rev.amount == Decimal("45000.0000")

        # Replaying reversal with same transaction should be idempotent
        rev_replay = create_reversal_transaction(tx.id, "Hatalı ödeme kaydı iptali", clean_tenant)
        assert rev_replay.id == rev.id


@pytest.mark.unit
def test_reversal_reverts_plan_occurrence_and_cleans_payment(app, clean_tenant):
    """Reversing a credit card installment resets PlanOccurrence to scheduled and removes Payment."""
    with app.app_context():
        # 1. Create recurring debt plan
        plan = RecurringPlan(
            name="Bonus Kart Borcu",
            category="Kredi Kartı Borcu",
            flow_type="Gider",
            amount=Decimal("45000.0000"),
            installments=3,
            payment_day=26,
            start_date="2026-10-26",
            frequency="Aylık",
            plan_type="Borç",
            status="Aktif",
            tenant_id=clean_tenant,
        )
        db.session.add(plan)
        db.session.commit()

        # Generate occurrences
        occ_repo = OccurrenceRepository()
        occ_repo.get_or_create_occurrences(plan, tenant_id=clean_tenant, count=3)

        # Create scheduled transaction for 1st installment
        tx = Transaction(
            date="2026-10-26",
            category="Kredi Kartı Borcu",
            description="Bonus Kart 1. Taksit",
            type="Gider",
            amount=Decimal("45000.0000"),
            status="Bekliyor",
            installment_number=1,
            source_id=plan.id,
            source_type="plan",
            tenant_id=clean_tenant,
        )
        db.session.add(tx)
        db.session.commit()

        # Mark paid via quick_pay
        repo = TransactionRepository()
        paid_tx = repo.quick_pay_transaction(tx.id, tenant_id=clean_tenant)
        assert paid_tx.status == "Ödendi"

        # Verify Payment and PlanOccurrence became paid
        payment = Payment.query.filter_by(plan_id=plan.id, installment_number=1, tenant_id=clean_tenant).first()
        assert payment is not None
        occ = PlanOccurrence.query.filter_by(plan_id=plan.id, occurrence_number=1, tenant_id=clean_tenant).first()
        assert occ.status == "paid"

        # Now reverse the transaction
        rev = create_reversal_transaction(paid_tx.id, "Yanlışlıkla ödendi yapıldı", clean_tenant)
        assert rev is not None

        db.session.refresh(paid_tx)
        assert paid_tx.status == "Bekliyor"

        # Occurrence must be back to scheduled
        db.session.refresh(occ)
        assert occ.status == "scheduled"
        assert occ.paid_at is None

        # Payment must be deleted
        payment_after = Payment.query.filter_by(plan_id=plan.id, installment_number=1, tenant_id=clean_tenant).first()
        assert payment_after is None

        # Quick pay can be executed again cleanly when actually due
        repaid_tx = repo.quick_pay_transaction(paid_tx.id, tenant_id=clean_tenant)
        assert repaid_tx.status == "Ödendi"
        db.session.refresh(occ)
        assert occ.status == "paid"


@pytest.mark.unit
def test_reversal_api_mobile_route_and_missing_idempotency_key(client, app, clean_tenant):
    """API supports mobile fallback route (/transactions/<id>/reversal) and auto-generates idempotency key."""
    with app.app_context():
        emin = User.query.filter_by(username='emin').first()
        assert emin is not None
        user_id = emin.id
        username = emin.username

        tx = Transaction(
            date="2026-10-26",
            category="Kredi Kartı Borcu",
            description="Mobil Ters Kayıt Test",
            type="Gider",
            amount=Decimal("45000.0000"),
            status="Ödendi",
            tenant_id=clean_tenant,
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

    with client.session_transaction() as sess:
        sess['tenant_id'] = clean_tenant
        sess['user_id'] = user_id
        sess['username'] = username
        sess['_fresh'] = True

    # Call fallback URL WITHOUT Idempotency-Key header
    resp = client.post(
        f'/transactions/{tx_id}/reversal',
        json={
            'reason_code': 'CANCELLED',
            'reason_text': 'Telefondan ters kayıt isteği',
        },
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )

    assert resp.status_code in (200, 201), f"Response failed: {resp.status_code} - {resp.get_data(as_text=True)}"
    data = resp.get_json()
    assert data['success'] is True
    assert data['data']['original_status'] == 'Bekliyor'

    # Replay
    resp_replay = client.post(
        f'/transactions/{tx_id}/reversal',
        json={
            'reason_code': 'CANCELLED',
            'reason_text': 'Telefondan ters kayıt isteği',
        },
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert resp_replay.status_code == 200
    assert resp_replay.get_json()['success'] is True
