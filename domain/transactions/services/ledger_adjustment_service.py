"""Immutable transaction adjustments, reversals, lineage, and occurrence settlement."""

from hashlib import sha256

from sqlalchemy.exc import IntegrityError

from domain.transactions.constants import (
    IMMUTABLE_REASON_CODE_OTHER,
    LEDGER_ADJUSTMENT_KIND_ADJUSTMENT,
    LEDGER_ADJUSTMENT_KIND_REVERSAL,
    LEDGER_ADJUSTMENT_STATUS_APPLIED,
    LEDGER_ADJUSTMENT_STATUS_REQUESTED,
    SOURCE_TYPE_ADJUSTMENT,
    SOURCE_TYPE_PLAN,
    SOURCE_TYPE_REVERSAL,
    TRANSACTION_STATUS_PAID,
    TRANSACTION_STATUS_PENDING,
    TRANSACTION_TYPE_EXPENSE,
    TRANSACTION_TYPE_INCOME,
    TRANSACTION_TYPE_INVESTMENT,
)
from domain.transactions.exceptions import LedgerError
from models import (
    LedgerAdjustment,
    LedgerAuditEvent,
    Payment,
    PlanOccurrence,
    RecurringPlan,
    Transaction,
    db,
    utcnow_naive,
)
from shared.decimal_precision import to_decimal

from .helpers import _resolve_tenant_id


def _opposite_cash_type(transaction_type):
    """Return the cash-flow type required to compensate a transaction."""
    if transaction_type == TRANSACTION_TYPE_INCOME:
        return TRANSACTION_TYPE_EXPENSE
    if transaction_type in (TRANSACTION_TYPE_EXPENSE, TRANSACTION_TYPE_INVESTMENT):
        return TRANSACTION_TYPE_INCOME
    raise LedgerError("Transfer işlemleri için adjustment/reversal henüz desteklenmiyor.")


def _require_paid_transaction(transaction_id, tenant_id):
    query = Transaction.query.filter(
        Transaction.id == transaction_id,
        Transaction.tenant_id == tenant_id,
        Transaction.is_deleted.is_(False),
    )
    transaction = query.first()
    if transaction is None:
        raise LedgerError("İşlem bulunamadı veya yetkisiz erişim.")
    if transaction.status != TRANSACTION_STATUS_PAID:
        raise LedgerError("Sadece ödenmiş işlemler adjustment/reversal ile değiştirilebilir.")
    return transaction


def _current_actor_id():
    try:
        from utils.auth_helpers import get_current_user
        user = get_current_user()
        return getattr(user, 'id', None)
    except Exception:
        return None


def _current_request_id():
    try:
        from utils.request_context import get_request_id
        return get_request_id()
    except Exception:
        return None


def _record_ledger_audit(
    adjustment,
    event_type,
    tenant_id,
    *,
    transaction_id=None,
    payload=None,
):
    """Append one immutable audit event in the same DB transaction."""
    event = LedgerAuditEvent(
        tenant_id=tenant_id,
        adjustment_id=adjustment.id if adjustment else None,
        transaction_id=transaction_id,
        event_type=event_type,
        actor_user_id=_current_actor_id(),
        correlation_id=adjustment.correlation_id if adjustment else 'ledger-system',
        request_id=_current_request_id(),
        payload=payload,
    )
    db.session.add(event)
    return event


def _immutable_idempotency_key(kind, original_id, reason, amount_delta=None):
    raw = f"phase3:{kind}:{original_id}:{amount_delta or ''}:{reason.strip()}"
    return sha256(raw.encode('utf-8')).hexdigest()[:64]


def _revert_plan_links_on_reversal(original, tenant_id):
    """When a paid transaction is reversed back to pending, reset linked occurrences and payments."""
    # 1. Reset any linked PlanOccurrence
    occ = PlanOccurrence.query.filter_by(
        transaction_id=original.id,
        tenant_id=tenant_id,
    ).first()
    if not occ and getattr(original, 'source_type', None) == SOURCE_TYPE_PLAN and getattr(original, 'source_id', None):
        occ_query = PlanOccurrence.query.filter_by(
            plan_id=original.source_id,
            tenant_id=tenant_id,
        )
        if getattr(original, 'installment_number', None) is not None:
            occ = occ_query.filter_by(occurrence_number=original.installment_number).first()
        if not occ and original.date:
            occ = occ_query.filter_by(scheduled_date=str(original.date)).first()

    if occ:
        occ.status = 'scheduled'
        occ.paid_at = None
        occ.transaction_id = original.id

    # 2. Delete any Payment created for this transaction
    Payment.query.filter_by(
        transaction_id=original.id,
        tenant_id=tenant_id,
    ).delete()

    if getattr(original, 'source_type', None) == SOURCE_TYPE_PLAN and getattr(original, 'source_id', None):
        if getattr(original, 'installment_number', None) is not None:
            Payment.query.filter_by(
                plan_id=original.source_id,
                installment_number=original.installment_number,
                tenant_id=tenant_id,
            ).delete()

        # 3. Check RecurringPlan status (if completed, restore to Aktif)
        plan = RecurringPlan.query.filter_by(
            id=original.source_id,
            tenant_id=tenant_id,
        ).first()
        if plan and plan.installments and plan.installments > 0:
            paid_count = Transaction.query.filter_by(
                source_id=plan.id,
                source_type=SOURCE_TYPE_PLAN,
                tenant_id=tenant_id,
                status=TRANSACTION_STATUS_PAID,
                is_deleted=False,
            ).count()
            if plan.status == 'Tamamlandı' and paid_count < plan.installments:
                plan.status = 'Aktif'


def _create_compensating_transaction(
    original_tx_id,
    amount_delta,
    reason,
    tenant_id,
    *,
    source_type,
    kind,
    reason_code=IMMUTABLE_REASON_CODE_OTHER,
    metadata=None,
    idempotency_key=None,
):
    tenant_id = _resolve_tenant_id(tenant_id)
    if not tenant_id:
        raise LedgerError("Tenant context bulunamadı.")
    reason = (reason or '').strip()
    if not reason:
        raise LedgerError("Adjustment/reversal nedeni zorunludur.")
    reason_code = (reason_code or IMMUTABLE_REASON_CODE_OTHER).strip()[:50]

    original = _require_paid_transaction(original_tx_id, tenant_id)
    delta = to_decimal(amount_delta)
    if delta == 0:
        raise LedgerError("Adjustment tutarı sıfır olamaz.")
    if kind == LEDGER_ADJUSTMENT_KIND_REVERSAL and delta != -to_decimal(original.amount):
        raise LedgerError("Reversal tutarı orijinal işlem tutarının tam tersi olmalıdır.")

    idempotency_key = (
        (idempotency_key or '').strip()[:64]
        or _immutable_idempotency_key(kind, original.id, reason, delta)
    )
    existing_adjustment = LedgerAdjustment.query.filter_by(
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
    ).first()
    if existing_adjustment and existing_adjustment.compensating_transaction_id:
        return db.session.get(Transaction, existing_adjustment.compensating_transaction_id)

    existing = Transaction.query.filter_by(
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
    ).first()
    if existing:
        if existing_adjustment is None:
            existing_adjustment = LedgerAdjustment(
                tenant_id=tenant_id,
                original_transaction_id=original.id,
                compensating_transaction_id=existing.id,
                kind=kind,
                status=LEDGER_ADJUSTMENT_STATUS_APPLIED,
                amount_delta=delta,
                original_amount_snapshot=to_decimal(original.amount),
                original_type_snapshot=original.type,
                original_category_snapshot=original.category,
                original_date_snapshot=original.date,
                original_version=original.version,
                reason_code=reason_code,
                reason_text=reason,
                requested_by=_current_actor_id(),
                requested_at=utcnow_naive(),
                applied_at=utcnow_naive(),
                idempotency_key=idempotency_key,
                correlation_id=(_current_request_id() or idempotency_key)[:64],
                metadata_json=metadata,
            )
            db.session.add(existing_adjustment)
            _record_ledger_audit(existing_adjustment, LEDGER_ADJUSTMENT_STATUS_APPLIED, tenant_id, transaction_id=existing.id)
            if kind == LEDGER_ADJUSTMENT_KIND_REVERSAL:
                original.status = TRANSACTION_STATUS_PENDING
                original.version = (original.version or 1) + 1
                existing.is_deleted = True
                _revert_plan_links_on_reversal(original, tenant_id)
            db.session.commit()
            try:
                from engines.financial_engine import invalidate_financial_cache
                invalidate_financial_cache(tenant_id)
            except Exception:
                pass
        return existing

    adjustment_type = original.type if delta > 0 else _opposite_cash_type(original.type)
    amount = abs(delta)
    digest = idempotency_key[:8]
    description = f"{kind.title()} — {original.description or original.category} [{digest}]"[:100]
    note = f"Orijinal işlem: #{original.id} | Neden: {reason}"[:200]
    compensating = Transaction(
        date=original.date,
        category=original.category,
        description=description,
        note=note,
        type=adjustment_type,
        amount=amount,
        status=TRANSACTION_STATUS_PAID,
        source_id=original.id,
        source_type=source_type,
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
    )
    adjustment = LedgerAdjustment(
        tenant_id=tenant_id,
        original_transaction_id=original.id,
        kind=kind,
        status=LEDGER_ADJUSTMENT_STATUS_REQUESTED,
        amount_delta=delta,
        original_amount_snapshot=to_decimal(original.amount),
        original_type_snapshot=original.type,
        original_category_snapshot=original.category,
        original_date_snapshot=original.date,
        original_version=original.version,
        reason_code=reason_code,
        reason_text=reason,
        requested_by=_current_actor_id(),
        idempotency_key=idempotency_key,
        correlation_id=(_current_request_id() or idempotency_key)[:64],
        metadata_json=metadata,
    )
    db.session.add(compensating)
    db.session.add(adjustment)
    try:
        db.session.flush()
        _record_ledger_audit(adjustment, LEDGER_ADJUSTMENT_STATUS_REQUESTED, tenant_id, transaction_id=original.id)
        adjustment.compensating_transaction_id = compensating.id
        adjustment.status = LEDGER_ADJUSTMENT_STATUS_APPLIED
        adjustment.applied_at = utcnow_naive()
        db.session.flush()
        _record_ledger_audit(adjustment, LEDGER_ADJUSTMENT_STATUS_APPLIED, tenant_id, transaction_id=compensating.id)

        if kind == LEDGER_ADJUSTMENT_KIND_REVERSAL:
            original.status = TRANSACTION_STATUS_PENDING
            original.version = (original.version or 1) + 1
            compensating.is_deleted = True
            compensating.note = f"Ters kayıt dengeleme kaydı: #{original.id} | Neden: {reason}"[:200]
            _revert_plan_links_on_reversal(original, tenant_id)

        db.session.commit()
        try:
            from engines.financial_engine import invalidate_financial_cache
            invalidate_financial_cache(tenant_id)
        except Exception:
            pass
    except IntegrityError as exc:
        db.session.rollback()
        replay = LedgerAdjustment.query.filter_by(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        ).first()
        if replay and replay.compensating_transaction_id:
            return db.session.get(Transaction, replay.compensating_transaction_id)
        raise LedgerError("Adjustment/reversal aynı anda başka bir işlem tarafından uygulandı.") from exc
    return compensating


def create_adjustment_transaction(
    original_tx_id,
    amount_delta,
    reason,
    tenant_id=None,
    *,
    reason_code=IMMUTABLE_REASON_CODE_OTHER,
    metadata=None,
    idempotency_key=None,
):
    """Create a signed compensating transaction; never mutate the original."""
    return _create_compensating_transaction(
        original_tx_id,
        amount_delta,
        reason,
        tenant_id,
        source_type=SOURCE_TYPE_ADJUSTMENT,
        kind=LEDGER_ADJUSTMENT_KIND_ADJUSTMENT,
        reason_code=reason_code,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )


def create_reversal_transaction(
    original_tx_id,
    reason,
    tenant_id=None,
    *,
    reason_code=IMMUTABLE_REASON_CODE_OTHER,
    metadata=None,
    idempotency_key=None,
):
    """Create a full compensating transaction for a paid transaction."""
    tenant_id = _resolve_tenant_id(tenant_id)
    if idempotency_key:
        existing_adjustment = LedgerAdjustment.query.filter_by(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key.strip()[:64],
        ).first()
        if existing_adjustment and existing_adjustment.compensating_transaction_id:
            return db.session.get(Transaction, existing_adjustment.compensating_transaction_id)

    original = Transaction.query.filter(
        Transaction.id == original_tx_id,
        Transaction.tenant_id == tenant_id,
        Transaction.is_deleted.is_(False),
    ).first()
    if original is None:
        raise LedgerError("İşlem bulunamadı veya yetkisiz erişim.")

    if original.status != TRANSACTION_STATUS_PAID:
        # Check if already reversed (idempotent replay)
        existing_rev = LedgerAdjustment.query.filter_by(
            tenant_id=tenant_id,
            original_transaction_id=original.id,
            kind=LEDGER_ADJUSTMENT_KIND_REVERSAL,
        ).first()
        if existing_rev and existing_rev.compensating_transaction_id:
            return db.session.get(Transaction, existing_rev.compensating_transaction_id)
        raise LedgerError("Sadece ödenmiş işlemler adjustment/reversal ile değiştirilebilir.")

    return _create_compensating_transaction(
        original_tx_id,
        -to_decimal(original.amount),
        reason,
        tenant_id,
        source_type=SOURCE_TYPE_REVERSAL,
        kind=LEDGER_ADJUSTMENT_KIND_REVERSAL,
        reason_code=reason_code,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )


def get_transaction_lineage(transaction_id, tenant_id=None):
    """Return original transaction lineage without crossing tenant boundaries."""
    tenant_id = _resolve_tenant_id(tenant_id)
    if not tenant_id:
        raise LedgerError("Tenant context bulunamadı.")
    original = Transaction.query.filter(
        Transaction.id == transaction_id,
        Transaction.tenant_id == tenant_id,
        Transaction.is_deleted.is_(False),
    ).first()
    if original is None:
        raise LookupError("Transaction bulunamadı.")

    occurrence = PlanOccurrence.query.filter_by(
        transaction_id=original.id,
        tenant_id=tenant_id,
    ).first()
    payments = Payment.query.filter_by(
        transaction_id=original.id,
        tenant_id=tenant_id,
    ).all()
    adjustments = LedgerAdjustment.query.filter(
        LedgerAdjustment.tenant_id == tenant_id,
        LedgerAdjustment.original_transaction_id == original.id,
    ).order_by(LedgerAdjustment.created_at.asc()).all()
    adjustment_ids = [item.id for item in adjustments]
    audit_query = LedgerAuditEvent.query.filter(
        LedgerAuditEvent.tenant_id == tenant_id,
    )
    if adjustment_ids:
        audit_query = audit_query.filter(
            (LedgerAuditEvent.transaction_id == original.id)
            | LedgerAuditEvent.adjustment_id.in_(adjustment_ids)
        )
    else:
        audit_query = audit_query.filter(LedgerAuditEvent.transaction_id == original.id)

    return {
        'original': original,
        'occurrence': occurrence,
        'payments': payments,
        'adjustments': adjustments,
        'audit_events': audit_query.order_by(LedgerAuditEvent.occurred_at.asc()).all(),
    }


def get_adjustment_audit(adjustment_id, tenant_id=None):
    """Return append-only audit events for one tenant-scoped adjustment."""
    tenant_id = _resolve_tenant_id(tenant_id)
    if not tenant_id:
        raise LedgerError("Tenant context bulunamadı.")
    adjustment = LedgerAdjustment.query.filter_by(
        id=adjustment_id,
        tenant_id=tenant_id,
    ).first()
    if adjustment is None:
        raise LookupError("Adjustment bulunamadı.")
    return adjustment, LedgerAuditEvent.query.filter_by(
        adjustment_id=adjustment.id,
        tenant_id=tenant_id,
    ).order_by(LedgerAuditEvent.occurred_at.asc()).all()


def _payment_value(payment_dto, field, default=None):
    if isinstance(payment_dto, dict):
        return payment_dto.get(field, default)
    return getattr(payment_dto, field, default)


def mark_occurrence_paid(occurrence_id, payment_dto, tenant_id=None):
    """Settle an occurrence through the legacy Payment bridge, idempotently.

    ``Payment`` remains the compatibility bridge for current reports and UI;
    ``PlanOccurrence`` becomes the authoritative lifecycle row. The operation
    can be retried safely after a partial failure because the payment lookup
    uses ``plan_id + installment_number + tenant_id``.
    """
    from domain.planning.services.occurrence_repository import OccurrenceRepository

    tenant_id = tenant_id or _resolve_tenant_id()
    if not tenant_id:
        raise LedgerError("Tenant context bulunamadı.")

    occurrence = PlanOccurrence.query.filter_by(
        id=occurrence_id,
        tenant_id=tenant_id,
    ).first()
    if occurrence is None:
        raise LookupError("Occurrence bulunamadı.")

    if occurrence.status == 'paid':
        payment = Payment.query.filter_by(
            plan_id=occurrence.plan_id,
            installment_number=occurrence.occurrence_number,
            tenant_id=tenant_id,
        ).first()
        if payment and payment.transaction_id == occurrence.transaction_id:
            return payment
        raise LedgerError("Occurrence paid durumda fakat Payment bağlantısı tutarsız.")
    if occurrence.status != 'scheduled':
        raise LedgerError("Sadece scheduled occurrence paid durumuna geçirilebilir.")

    plan = RecurringPlan.query.filter_by(
        id=occurrence.plan_id,
        tenant_id=tenant_id,
    ).first()
    if plan is None:
        raise LedgerError("Occurrence planı bulunamadı veya tenant uyuşmazlığı var.")

    amount = to_decimal(_payment_value(payment_dto, 'amount', occurrence.amount or plan.amount))
    payment_date = _payment_value(payment_dto, 'payment_date', occurrence.scheduled_date)
    notes = _payment_value(payment_dto, 'notes')
    if amount <= 0:
        raise LedgerError("Ödeme tutarı sıfırdan büyük olmalıdır.")

    existing_payment = Payment.query.filter_by(
        plan_id=plan.id,
        installment_number=occurrence.occurrence_number,
        tenant_id=tenant_id,
    ).first()
    if existing_payment:
        if existing_payment.transaction_id is None:
            raise LedgerError("Mevcut Payment kaydının transaction bağlantısı eksik.")
        payment = existing_payment
    else:
        from repositories.financial_repository import FinancialRepository

        payment = FinancialRepository().create_payment(
            plan.id,
            amount,
            payment_date,
            occurrence.occurrence_number,
            notes=notes,
            tenant_id=tenant_id,
        )
        if getattr(plan, 'plan_type', None) == 'DCA' and getattr(plan, 'target_asset_id', None):
            from domain.transactions.services.ledger_position_service import transfer_cash_to_asset

            transfer_cash_to_asset(plan.target_asset_id, amount, payment_date, tenant_id, skip_cash_tx=True)

    if payment.transaction_id is None:
        raise LedgerError("Ödeme transaction bağlantısı oluşturulamadı.")
    OccurrenceRepository().mark_paid(
        occurrence.id,
        payment.transaction_id,
        tenant_id,
    )
    return payment
