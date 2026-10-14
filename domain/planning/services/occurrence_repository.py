"""Persistence operations for the plan occurrence lifecycle.

The repository deliberately does not create or mutate legacy ``Transaction``
rows while synchronising a schedule.  It only materialises the deterministic
plan calendar in ``plan_occurrence`` and leaves payment settlement to the
ledger service.
"""

from __future__ import annotations

from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from domain.planning.models import CanonicalPlan
from domain.planning.services.occurrence_service import OccurrenceCalculator
from domain.transactions.services.financial_ledger import LedgerError
from models import PlanOccurrence, RecurringPlan, Transaction, utcnow_naive
from repositories.base import TenantScopedRepository


class OccurrenceRepository(TenantScopedRepository):
    """Tenant-isolated persistence boundary for plan occurrences."""

    VALID_STATUSES = PlanOccurrence.STATUSES

    def _get_plan(self, plan, tenant_id):
        if plan is None or getattr(plan, "tenant_id", None) != tenant_id:
            raise PermissionError("Plan bulunamadı veya yetkisiz erişim.")
        return plan

    @staticmethod
    def _validate_occurrence_number(occurrence_number: int) -> int:
        try:
            number = int(occurrence_number)
        except (TypeError, ValueError) as exc:
            raise LedgerError("Geçersiz occurrence numarası.") from exc
        if number < 1:
            raise LedgerError("Occurrence numarası 1 veya daha büyük olmalıdır.")
        return number

    @staticmethod
    def _validate_scheduled_date(scheduled_date: str) -> str:
        try:
            parsed = date.fromisoformat(str(scheduled_date))
        except (TypeError, ValueError) as exc:
            raise LedgerError("Occurrence tarihi YYYY-MM-DD formatında olmalıdır.") from exc
        return parsed.isoformat()

    def get_or_create_occurrences(self, plan, tenant_id=None, count=None, until_date=None, horizon_months=3):
        """Materialise the deterministic schedule without deleting history.

        Existing ``paid``, ``skipped`` and ``cancelled`` rows are immutable from
        a schedule synchronisation perspective.  Only ``scheduled`` rows may
        receive a refreshed date/expected amount when the plan is edited.
        """
        tenant_id = self.require_tenant_id(tenant_id)
        plan = self._get_plan(plan, tenant_id)

        plan_status = getattr(plan, "status", "Aktif")
        if hasattr(plan_status, "value"):
            plan_status = plan_status.value

        if plan_status in ("İptal", "Tamamlandı"):
            self.session.query(PlanOccurrence).filter(
                PlanOccurrence.plan_id == plan.id,
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status == "scheduled",
            ).update({"status": "cancelled"}, synchronize_session="fetch")
            self.session.commit()
            return self.list_for_plan(plan.id, tenant_id)

        if plan_status == "Duraklatıldı":
            self.session.query(PlanOccurrence).filter(
                PlanOccurrence.plan_id == plan.id,
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status == "scheduled",
            ).update({"status": "skipped"}, synchronize_session="fetch")
            self.session.commit()
            return self.list_for_plan(plan.id, tenant_id)

        if plan_status == "Aktif":
            today_iso = date.today().isoformat()
            self.session.query(PlanOccurrence).filter(
                PlanOccurrence.plan_id == plan.id,
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status.in_(["cancelled", "skipped"]),
                PlanOccurrence.transaction_id.is_(None),
                PlanOccurrence.paid_at.is_(None),
                PlanOccurrence.scheduled_date >= today_iso,
            ).update({"status": "scheduled"}, synchronize_session="fetch")
            self.session.flush()

        canonical = CanonicalPlan.from_model(plan)
        generated = OccurrenceCalculator.generate(
            canonical, count=count, until_date=until_date, horizon_months=horizon_months
        )

        existing_rows = {
            row.occurrence_number: row
            for row in self.session.query(PlanOccurrence)
            .filter(
                PlanOccurrence.plan_id == plan.id,
                PlanOccurrence.tenant_id == tenant_id,
            )
            .all()
        }
        plan_transactions = (
            self.session.query(Transaction)
            .filter(
                Transaction.source_id == plan.id,
                Transaction.source_type == "plan",
                Transaction.tenant_id == tenant_id,
                Transaction.is_deleted.is_(False),
            )
            .all()
        )
        tx_by_inst = {tx.installment_number: tx for tx in plan_transactions if tx.installment_number is not None}
        tx_by_date = {str(tx.date): tx for tx in plan_transactions if tx.date}

        result = []
        for expected in generated:
            occurrence_number = self._validate_occurrence_number(expected.occurrence_number)
            scheduled_date = self._validate_scheduled_date(expected.scheduled_date)
            matching_tx = tx_by_inst.get(occurrence_number) or tx_by_date.get(scheduled_date)
            is_tx_paid = bool(matching_tx and matching_tx.status == "Ödendi")

            row = existing_rows.get(occurrence_number)
            if row is None:
                row = PlanOccurrence(
                    plan_id=plan.id,
                    occurrence_number=occurrence_number,
                    scheduled_date=scheduled_date,
                    status="paid" if is_tx_paid else "scheduled",
                    amount=plan.amount,
                    tenant_id=tenant_id,
                    transaction_id=matching_tx.id if matching_tx else None,
                    paid_at=datetime.fromisoformat(str(matching_tx.date)) if is_tx_paid and matching_tx.date else None,
                )
                try:
                    # A savepoint makes a concurrent unique-key race recoverable
                    # without rolling back unrelated work in the outer session.
                    with self.session.begin_nested():
                        self.session.add(row)
                        self.session.flush()
                except IntegrityError:
                    row = (
                        self.session.query(PlanOccurrence)
                        .filter_by(
                            plan_id=plan.id,
                            occurrence_number=occurrence_number,
                            tenant_id=tenant_id,
                        )
                        .one()
                    )
                existing_rows[occurrence_number] = row
            elif row.status == "scheduled":
                row.scheduled_date = scheduled_date
                row.amount = plan.amount
                if is_tx_paid:
                    row.status = "paid"
                    row.transaction_id = matching_tx.id
                    if not row.paid_at and matching_tx.date:
                        try:
                            row.paid_at = datetime.fromisoformat(str(matching_tx.date))
                        except (ValueError, TypeError):
                            row.paid_at = utcnow_naive()
            elif row.status == "paid" and not row.transaction_id and matching_tx:
                row.transaction_id = matching_tx.id
            result.append(row)

        generated_numbers = {expected.occurrence_number for expected in generated}
        for num, row in existing_rows.items():
            if num not in generated_numbers and row.status == "scheduled":
                row.status = "cancelled"
                row.notes = "Taksit sayısı güncellendiği için iptal edildi."

        self.session.commit()
        return result

    def get_for_tenant(self, occurrence_id, tenant_id=None):
        tenant_id = self.require_tenant_id(tenant_id)
        return (
            self.session.query(PlanOccurrence)
            .filter(
                PlanOccurrence.id == occurrence_id,
                PlanOccurrence.tenant_id == tenant_id,
            )
            .first()
        )

    def mark_paid(self, occurrence_id, transaction_id, tenant_id=None):
        """Transition one scheduled occurrence to paid, idempotently."""
        tenant_id = self.require_tenant_id(tenant_id)
        occurrence = self.get_for_tenant(occurrence_id, tenant_id)
        if occurrence is None:
            raise LookupError("Occurrence bulunamadı.")
        if not transaction_id:
            raise LedgerError("Paid occurrence için transaction bağlantısı zorunludur.")

        if occurrence.status == "paid":
            if occurrence.transaction_id == transaction_id:
                return occurrence
            raise LedgerError("Occurrence farklı bir transaction ile zaten ödenmiş.")
        if occurrence.status != "scheduled":
            raise LedgerError("Sadece scheduled occurrence paid durumuna geçirilebilir.")

        occurrence.status = "paid"
        occurrence.transaction_id = transaction_id
        occurrence.paid_at = utcnow_naive()
        self.session.commit()
        return occurrence

    def mark_skipped(self, occurrence_id, tenant_id=None, reason=None):
        """Transition one scheduled occurrence to skipped, idempotently."""
        tenant_id = self.require_tenant_id(tenant_id)
        occurrence = self.get_for_tenant(occurrence_id, tenant_id)
        if occurrence is None:
            raise LookupError("Occurrence bulunamadı.")
        if occurrence.status == "skipped":
            return occurrence
        if occurrence.status != "scheduled":
            raise LedgerError("Sadece scheduled occurrence skipped durumuna geçirilebilir.")

        reason = (reason or "").strip() or None
        occurrence.status = "skipped"
        if reason:
            occurrence.notes = reason[:200]
        self.session.commit()
        return occurrence

    def mark_cancelled(self, occurrence_id, tenant_id=None, reason=None):
        """Transition one scheduled occurrence to cancelled, idempotently."""
        tenant_id = self.require_tenant_id(tenant_id)
        occurrence = self.get_for_tenant(occurrence_id, tenant_id)
        if occurrence is None:
            raise LookupError("Occurrence bulunamadı.")
        if occurrence.status == "cancelled":
            return occurrence
        if occurrence.status != "scheduled":
            raise LedgerError("Sadece scheduled occurrence cancelled durumuna geçirilebilir.")

        reason = (reason or "").strip() or None
        occurrence.status = "cancelled"
        if reason:
            occurrence.notes = reason[:200]
        self.session.commit()
        return occurrence

    def list_for_plan(self, plan_id, tenant_id=None, status=None):
        """Return all occurrences for one tenant-scoped plan in stable order."""
        tenant_id = self.require_tenant_id(tenant_id)
        query = self.session.query(PlanOccurrence).filter(
            PlanOccurrence.plan_id == plan_id,
            PlanOccurrence.tenant_id == tenant_id,
        )
        if status:
            if status not in self.VALID_STATUSES:
                raise LedgerError("Geçersiz occurrence durumu.")
            query = query.filter(PlanOccurrence.status == status)
        return query.order_by(PlanOccurrence.occurrence_number.asc()).all()

    def list_pending(self, plan_id, tenant_id=None):
        """Return only scheduled rows inside the requested tenant boundary."""
        tenant_id = self.require_tenant_id(tenant_id)
        return (
            self.session.query(PlanOccurrence)
            .filter(
                PlanOccurrence.plan_id == plan_id,
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status == "scheduled",
            )
            .order_by(PlanOccurrence.occurrence_number.asc())
            .all()
        )

    def sync_with_transactions(self, tenant_id=None, plan_id=None):
        """Synchronize PlanOccurrence statuses with actual Transaction records."""
        tenant_id = self.require_tenant_id(tenant_id)
        query = (
            self.session.query(PlanOccurrence)
            .filter(
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status == "scheduled",
            )
        )
        if plan_id:
            query = query.filter(PlanOccurrence.plan_id == plan_id)

        scheduled_occurrences = query.all()
        if not scheduled_occurrences:
            return 0

        plan_ids = {occ.plan_id for occ in scheduled_occurrences}
        transactions = (
            self.session.query(Transaction)
            .filter(
                Transaction.tenant_id == tenant_id,
                Transaction.source_type == "plan",
                Transaction.source_id.in_(plan_ids),
                Transaction.is_deleted.is_(False),
                Transaction.status == "Ödendi",
            )
            .all()
        )

        tx_by_inst = {}
        tx_by_date = {}
        for tx in transactions:
            if tx.installment_number is not None:
                tx_by_inst[(tx.source_id, tx.installment_number)] = tx
            if tx.date:
                tx_by_date[(tx.source_id, str(tx.date))] = tx

        updated_count = 0
        for occ in scheduled_occurrences:
            tx = tx_by_inst.get((occ.plan_id, occ.occurrence_number)) or tx_by_date.get((occ.plan_id, str(occ.scheduled_date)))
            if tx:
                occ.status = "paid"
                occ.transaction_id = tx.id
                if not occ.paid_at and tx.date:
                    try:
                        occ.paid_at = datetime.fromisoformat(str(tx.date))
                    except (ValueError, TypeError):
                        occ.paid_at = utcnow_naive()
                updated_count += 1

        if updated_count > 0:
            self.session.commit()
        return updated_count

    def ensure_rolling_occurrences_for_active_plans(self, tenant_id=None) -> int:
        """Ensure active indefinite/rolling plans maintain a future occurrence horizon."""
        tenant_id = self.require_tenant_id(tenant_id)
        active_rolling_plans = (
            self.session.query(RecurringPlan)
            .filter(
                RecurringPlan.tenant_id == tenant_id,
                RecurringPlan.status == "Aktif",
                or_(
                    RecurringPlan.installments.in_([0, 9999]),
                    RecurringPlan.plan_type.in_(["Abonelik", "DCA"]),
                ),
            )
            .all()
        )
        if not active_rolling_plans:
            return 0

        target_horizon = (date.today() + relativedelta(months=2)).isoformat()
        updated_count = 0
        for plan in active_rolling_plans:
            has_future = (
                self.session.query(PlanOccurrence.id)
                .filter(
                    PlanOccurrence.plan_id == plan.id,
                    PlanOccurrence.tenant_id == tenant_id,
                    PlanOccurrence.scheduled_date >= target_horizon,
                    PlanOccurrence.status.in_(["scheduled", "paid"]),
                )
                .first()
            )
            if not has_future:
                self.get_or_create_occurrences(plan, tenant_id=tenant_id)
                updated_count += 1
        return updated_count

    def list_upcoming(self, tenant_id=None, from_date=None, through_date=None, limit=8):
        """Return scheduled occurrences in a bounded window without mutations."""
        tenant_id = self.require_tenant_id(tenant_id)
        start = from_date or date.today()
        start_date = start.isoformat()
        end_date = through_date.isoformat() if through_date else None
        try:
            safe_limit = min(max(int(limit), 1), 50)
        except (TypeError, ValueError):
            safe_limit = 8

        paid_tx_subquery = (
            self.session.query(Transaction.id)
            .filter(
                Transaction.tenant_id == tenant_id,
                Transaction.source_type == "plan",
                Transaction.source_id == PlanOccurrence.plan_id,
                Transaction.status == "Ödendi",
                Transaction.is_deleted.is_(False),
                (Transaction.installment_number == PlanOccurrence.occurrence_number)
                | (
                    Transaction.installment_number.is_(None)
                    & (Transaction.date == PlanOccurrence.scheduled_date)
                ),
            )
            .exists()
        )

        query = (
            self.session.query(PlanOccurrence)
            .join(RecurringPlan, PlanOccurrence.plan_id == RecurringPlan.id)
            .filter(
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status == "scheduled",
                PlanOccurrence.scheduled_date >= start_date,
                RecurringPlan.status == "Aktif",
                ~paid_tx_subquery,
            )
        )
        if end_date:
            query = query.filter(PlanOccurrence.scheduled_date <= end_date)
        return query.order_by(
            PlanOccurrence.scheduled_date.asc(),
            PlanOccurrence.id.asc(),
        ).limit(safe_limit).all()

    def count_upcoming_for_tenant(self, tenant_id=None, from_date=None, through_date=None):
        """Count scheduled occurrences in a bounded tenant-scoped window."""
        tenant_id = self.require_tenant_id(tenant_id)
        start = from_date or date.today()
        start_date = start.isoformat()
        end_date = through_date.isoformat() if through_date else None

        paid_tx_subquery = (
            self.session.query(Transaction.id)
            .filter(
                Transaction.tenant_id == tenant_id,
                Transaction.source_type == "plan",
                Transaction.source_id == PlanOccurrence.plan_id,
                Transaction.status == "Ödendi",
                Transaction.is_deleted.is_(False),
                (Transaction.installment_number == PlanOccurrence.occurrence_number)
                | (
                    Transaction.installment_number.is_(None)
                    & (Transaction.date == PlanOccurrence.scheduled_date)
                ),
            )
            .exists()
        )

        query = (
            self.session.query(PlanOccurrence)
            .join(RecurringPlan, PlanOccurrence.plan_id == RecurringPlan.id)
            .filter(
                PlanOccurrence.tenant_id == tenant_id,
                PlanOccurrence.status == "scheduled",
                PlanOccurrence.scheduled_date >= start_date,
                RecurringPlan.status == "Aktif",
                ~paid_tx_subquery,
            )
        )
        if end_date:
            query = query.filter(PlanOccurrence.scheduled_date <= end_date)
        return query.count()
