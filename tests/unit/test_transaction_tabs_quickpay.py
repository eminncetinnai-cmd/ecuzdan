from decimal import Decimal

import pytest

from models import Payment, PlanOccurrence, RecurringPlan, Transaction, db
from repositories.financial_repository import FinancialRepository


@pytest.mark.unit
def test_quick_pay_transaction_standalone(app):
    """Test quick paying a standalone pending transaction."""
    with app.app_context():
        repo = FinancialRepository()
        tx = Transaction(
            date="2026-09-24",
            category="Yemek",
            description="Öğle Yemeği",
            type="Gider",
            amount=Decimal("150.00"),
            status="Bekliyor",
            tenant_id="default",
            source_type="manual",
        )
        db.session.add(tx)
        db.session.commit()

        updated_tx = repo.quick_pay_transaction(tx.id, tenant_id="default")
        assert updated_tx.status == "Ödendi"
        assert updated_tx.version > 1

        # Idempotent call
        same_tx = repo.quick_pay_transaction(tx.id, tenant_id="default")
        assert same_tx.status == "Ödendi"


@pytest.mark.unit
def test_quick_pay_transaction_linked_to_plan(app):
    """Test quick paying a transaction linked to a recurring plan syncs occurrence & payment."""
    with app.app_context():
        repo = FinancialRepository()
        plan = RecurringPlan(
            name="İnternet Aboneliği",
            category="Faturalar",
            flow_type="Gider",
            amount=Decimal("300.00"),
            installments=2,
            payment_day=15,
            start_date="2026-09-15",
            frequency="Aylık",
            plan_type="Taksit",
            status="Aktif",
            tenant_id="default",
        )
        db.session.add(plan)
        db.session.flush()

        occ1 = PlanOccurrence(
            plan_id=plan.id,
            occurrence_number=1,
            scheduled_date="2026-09-15",
            status="scheduled",
            amount=Decimal("300.00"),
            tenant_id="default",
        )
        occ2 = PlanOccurrence(
            plan_id=plan.id,
            occurrence_number=2,
            scheduled_date="2026-10-15",
            status="scheduled",
            amount=Decimal("300.00"),
            tenant_id="default",
        )
        db.session.add_all([occ1, occ2])

        tx1 = Transaction(
            date="2026-09-15",
            category="Faturalar",
            description="İnternet Aboneliği (1/2)",
            type="Gider",
            amount=Decimal("300.00"),
            status="Bekliyor",
            installment_number=1,
            source_id=plan.id,
            source_type="plan",
            tenant_id="default",
        )
        tx2 = Transaction(
            date="2026-10-15",
            category="Faturalar",
            description="İnternet Aboneliği (2/2)",
            type="Gider",
            amount=Decimal("300.00"),
            status="Bekliyor",
            installment_number=2,
            source_id=plan.id,
            source_type="plan",
            tenant_id="default",
        )
        db.session.add_all([tx1, tx2])
        db.session.commit()

        # Pay installment 1
        paid_tx1 = repo.quick_pay_transaction(tx1.id, tenant_id="default")
        assert paid_tx1.status == "Ödendi"

        # Check occ1 is paid
        db.session.refresh(occ1)
        assert occ1.status == "paid"
        assert occ1.transaction_id == tx1.id
        assert occ1.paid_at is not None

        # Check payment record was created
        payment1 = Payment.query.filter_by(plan_id=plan.id, installment_number=1).first()
        assert payment1 is not None
        assert payment1.transaction_id == tx1.id

        # Plan should still be active because installment 2 is pending
        db.session.refresh(plan)
        assert plan.status == "Aktif"

        # Now pay installment 2
        paid_tx2 = repo.quick_pay_transaction(tx2.id, tenant_id="default")
        assert paid_tx2.status == "Ödendi"

        # Plan should now be marked Tamamlandı
        db.session.refresh(plan)
        assert plan.status == "Tamamlandı"


@pytest.mark.unit
def test_quick_pay_endpoint(authenticated_client):
    """Test POST /transactions/<id>/quick-pay HTTP route."""
    tx = Transaction(
        date="2026-09-24",
        category="Ulaşım",
        description="Metro Kartı",
        type="Gider",
        amount=Decimal("50.00"),
        status="Bekliyor",
        tenant_id="default",
        source_type="manual",
    )
    db.session.add(tx)
    db.session.commit()

    response = authenticated_client.post(
        f"/transactions/{tx.id}/quick-pay",
        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "Ödendi"

    persisted_tx = db.session.get(Transaction, tx.id)
    assert persisted_tx is not None
    assert persisted_tx.status == "Ödendi"
