"""
Recurring Plan Repository — repositories/recurring_plan_repository.py

Periyodik planlar (RecurringPlan), taksitler, abonelikler, ödemeler (Payment)
ve plan gerçekleşmeleri (PlanOccurrence) için read/write repository.
"""

import calendar
from datetime import datetime, timedelta
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import NotFound

import models as _models
from engines.financial_engine import invalidate_financial_cache

from .base import BaseRepository
from .contracts import BaseRepositoryContract


class _ModelLookup:
    def __init__(self, name: str, default):
        self._name = name
        self._default = default

    def _resolve(self):
        import sys
        fin = sys.modules.get('repositories.financial_repository')
        if fin is not None:
            candidate = getattr(fin, self._name, None)
            if candidate is not None:
                return candidate
        return self._default

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)

    def __getitem__(self, item):
        return self._resolve()[item]

    def __bool__(self):
        return bool(self._resolve())

    def __eq__(self, other):
        return self._resolve() == other

    def __hash__(self):
        return hash(self._resolve())


Category = _ModelLookup('Category', getattr(_models, 'Category', None))
Payment = _ModelLookup('Payment', getattr(_models, 'Payment', None))
PlanOccurrence = _ModelLookup('PlanOccurrence', getattr(_models, 'PlanOccurrence', None))
RecurringPlan = _ModelLookup('RecurringPlan', getattr(_models, 'RecurringPlan', None))
Transaction = _ModelLookup('Transaction', getattr(_models, 'Transaction', None))
LedgerAdjustment = _ModelLookup('LedgerAdjustment', getattr(_models, 'LedgerAdjustment', None))
LedgerAuditEvent = _ModelLookup('LedgerAuditEvent', getattr(_models, 'LedgerAuditEvent', None))
LogbookEntry = _ModelLookup('LogbookEntry', getattr(_models, 'LogbookEntry', None))


def _unwrap(model):
    if hasattr(model, '_resolve'):
        return model._resolve()
    return model




class RecurringPlanRepository(BaseRepository, BaseRepositoryContract):
    """
    RecurringPlan ve Payment veri erişim repository'si.
    """

    def _resolve_tenant_id(self, tenant_id: Optional[str] = None) -> str:
        if tenant_id:
            return tenant_id
        try:
            from flask import g
            tenant_id = g.get('tenant_id')
        except Exception:
            tenant_id = None
        if not tenant_id:
            raise RuntimeError("Tenant context bulunamadı.")
        return tenant_id

    @staticmethod
    def _parse_plan_date(value):
        """Parse a persisted plan date without aborting generation on legacy data."""
        if not value:
            return None
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp_payment_day(year, month, payment_day):
        """Return a valid day for the target month."""
        requested_day = max(int(payment_day or 1), 1)
        return min(requested_day, calendar.monthrange(year, month)[1])

    @staticmethod
    def _frequency_months(plan):
        if getattr(plan, 'frequency', None) == '3-Aylık':
            return 3
        if getattr(plan, 'frequency', None) == 'Yıllık':
            return 12
        return 1

    @staticmethod
    def _is_weekly(plan):
        return getattr(plan, 'frequency', None) == 'Haftalık'

    def _first_plan_date(self, plan, anchor_date):
        """Return the first occurrence on or after the plan anchor date."""
        if self._is_weekly(plan):
            return anchor_date

        candidate = anchor_date.replace(
            day=self._clamp_payment_day(anchor_date.year, anchor_date.month, plan.payment_day)
        )
        if candidate < anchor_date:
            candidate = anchor_date + relativedelta(months=self._frequency_months(plan))
            candidate = candidate.replace(
                day=self._clamp_payment_day(candidate.year, candidate.month, plan.payment_day)
            )
        return candidate

    def _next_plan_date(self, plan, current_date):
        """Advance exactly one configured recurrence interval."""
        if self._is_weekly(plan):
            return current_date + timedelta(days=7)

        candidate = current_date + relativedelta(months=self._frequency_months(plan))
        return candidate.replace(
            day=self._clamp_payment_day(candidate.year, candidate.month, plan.payment_day)
        )

    def _plan_occurrences(self, plan, count, skip=0, forward_only=False):
        """Yield occurrences on/after start_date and before optional end_date."""
        if count <= 0:
            return

        start_date = self._parse_plan_date(plan.start_date) or datetime.now().date()
        anchor_date = max(start_date, datetime.now().date()) if forward_only else start_date
        end_date = self._parse_plan_date(plan.end_date)
        current_date = self._first_plan_date(plan, anchor_date)
        for _ in range(max(skip, 0)):
            if end_date and current_date > end_date:
                return
            current_date = self._next_plan_date(plan, current_date)

        for _ in range(min(count, 360)):
            if end_date and current_date > end_date:
                break
            yield current_date
            current_date = self._next_plan_date(plan, current_date)

    @classmethod
    def _plan_transaction_count(cls, plan):
        """Finite plans use installments; rolling plans keep a three-period window."""
        if plan.plan_type in ('Abonelik', 'DCA') or (plan.installments in (0, 9999) and not plan.end_date):
            return 3
        if plan.end_date and (not plan.installments or plan.installments in (0, 9999)):
            start_date = cls._parse_plan_date(plan.start_date) or datetime.now().date()
            end_date = cls._parse_plan_date(plan.end_date)
            if end_date and start_date:
                from validators.request_validators import _calc_installments
                return _calc_installments(start_date, end_date, plan.frequency)
        return max(int(plan.installments or 0), 0)

    def _plan_description(self, plan, index):
        if plan.installments in (0, 9999) and not plan.end_date:
            total = 'Süresiz'
        elif plan.end_date and (not plan.installments or plan.installments in (0, 9999)):
            total = str(self._plan_transaction_count(plan))
        else:
            total = str(plan.installments)
        return f"{plan.name} ({index + 1}/{total})"

    def _create_transactions_from_plan(self, plan):
        plan_note = (plan.note or '').strip() or None
        paid_count = Transaction.query.filter_by(
            source_id=plan.id,
            source_type='plan',
            status='Ödendi',
            tenant_id=plan.tenant_id,
        ).count()
        total_count = self._plan_transaction_count(plan)
        is_rolling_plan = plan.plan_type in ('Abonelik', 'DCA') or plan.installments in (0, 9999)
        pending_count = total_count if is_rolling_plan else max(total_count - paid_count, 0)
        skip_count = 0 if is_rolling_plan else paid_count

        for index, payment_date in enumerate(
            self._plan_occurrences(plan, pending_count, skip=skip_count)
        ):
            installment_number = index + 1 + skip_count
            self.session.add(Transaction(
                date=payment_date.strftime('%Y-%m-%d'),
                category=plan.category,
                description=self._plan_description(plan, installment_number - 1),
                note=plan_note,
                type=plan.flow_type,
                amount=plan.amount,
                status='Bekliyor',
                installment_number=installment_number,
                source_id=plan.id,
                source_type='plan',
                tenant_id=plan.tenant_id,
            ))

    def add_recurring_plan(
        self,
        name,
        category,
        amount,
        installments,
        payment_day,
        note=None,
        start_date=None,
        tenant_id=None,
        plan_type='Taksit',
        end_date=None,
        frequency='Aylık',
        target_asset_id=None,
        status='Aktif'
    ) -> RecurringPlan:
        from flask import g

        tenant_id = tenant_id or g.get('tenant_id')
        cat = Category.query.filter_by(name=category).first()
        if not cat:
            raise ValueError("Geçersiz kategori")

        # DCA için kategori tipi Yatırım olabilir
        if cat.type not in ('Gelir', 'Gider', 'Yatırım'):
            raise ValueError("Plan yalnızca gelir, gider veya yatırım kategorisiyle oluşturulabilir")

        # installments limit kontrolü (Faz 1)
        if installments > 0 and installments > 600:
            raise ValueError("Taksit sayısı 600'ü geçemez. Süresiz plan için 0 girin.")

        plan = RecurringPlan(
            name=name,
            category=category,
            flow_type='Gider' if cat.type == 'Yatırım' else cat.type,
            amount=amount,
            installments=installments,
            payment_day=payment_day,
            start_date=start_date,
            note=(note or '').strip() or None,
            tenant_id=tenant_id,
            plan_type=plan_type,
            end_date=end_date,
            frequency=frequency,
            status=status,
            target_asset_id=target_asset_id
        )
        self.session.add(plan)
        self.session.flush()
        self._create_transactions_from_plan(plan)
        self.commit()
        invalidate_financial_cache(tenant_id)
        return plan

    def generate_rolling_transactions(self, tenant_id=None):
        """Keep three future transactions for active rolling plans."""
        from sqlalchemy import or_

        query = RecurringPlan.query.filter(
            or_(RecurringPlan.installments == 0, RecurringPlan.installments == 9999),
            RecurringPlan.status == 'Aktif',
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        today = datetime.now().date()
        for plan in query.all():
            all_transactions = Transaction.query.filter_by(
                source_id=plan.id,
                source_type='plan',
                tenant_id=plan.tenant_id,
            ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()
            start_date = self._parse_plan_date(plan.start_date) or today
            anchor_date = max(start_date, today)
            end_date = self._parse_plan_date(plan.end_date)
            pending_dates = {
                parsed_date
                for tx in all_transactions
                if tx.status == 'Bekliyor'
                and not getattr(tx, 'is_deleted', False)
                and (parsed_date := self._parse_plan_date(tx.date)) is not None
                and parsed_date >= anchor_date
            }
            if len(pending_dates) >= 3:
                continue

            recorded_dates = [
                parsed_date
                for tx in all_transactions
                if (parsed_date := self._parse_plan_date(tx.date)) is not None
            ]
            last_date = max(recorded_dates) if recorded_dates else None
            last_installment_number = max(
                (tx.installment_number or 0 for tx in all_transactions),
                default=0,
            )

            while len(pending_dates) < 3:
                if last_date is None or last_date < anchor_date:
                    next_date = self._first_plan_date(plan, anchor_date)
                else:
                    next_date = self._next_plan_date(plan, last_date)
                if end_date and next_date > end_date:
                    break

                last_installment_number += 1
                self.session.add(Transaction(
                    date=next_date.strftime('%Y-%m-%d'),
                    category=plan.category,
                    description=self._plan_description(plan, last_installment_number - 1),
                    note=plan.note,
                    type=plan.flow_type,
                    amount=plan.amount,
                    status='Bekliyor',
                    installment_number=last_installment_number,
                    source_id=plan.id,
                    source_type='plan',
                    tenant_id=plan.tenant_id,
                ))
                pending_dates.add(next_date)
                last_date = next_date

        self.session.commit()
        invalidate_financial_cache(tenant_id)

    def create_payment(
        self,
        plan_id: int,
        amount,
        payment_date: str,
        installment_number: int,
        notes: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Payment:
        from flask import g

        tenant_id = tenant_id or g.get('tenant_id')

        if amount <= 0:
            raise ValueError("Ödeme tutarı sıfırdan büyük olmalıdır.")

        plan = self.db.get_or_404(_unwrap(RecurringPlan), plan_id)
        if plan.tenant_id != tenant_id:
            raise ValueError("Plan bulunamadı.")
        is_rolling_plan = plan.plan_type in ('Abonelik', 'DCA') or plan.installments in (0, 9999)
        if installment_number < 1 or (not is_rolling_plan and installment_number > plan.installments):
            raise ValueError("Geçersiz taksit numarası.")

        payment_date_value = self._parse_plan_date(payment_date)
        if payment_date_value is None:
            raise ValueError("Geçersiz ödeme tarihi.")
        plan_start = self._parse_plan_date(plan.start_date)
        if plan_start and payment_date_value < plan_start:
            raise ValueError("Ödeme tarihi plan başlangıç tarihinden önce olamaz.")
        plan_end = self._parse_plan_date(plan.end_date)
        if plan_end and payment_date_value > plan_end:
            raise ValueError("Ödeme tarihi plan bitiş tarihinden sonra olamaz.")

        existing_payment = Payment.query.filter_by(
            plan_id=plan_id,
            installment_number=installment_number,
            tenant_id=tenant_id,
        ).first()
        if existing_payment:
            raise ValueError("Bu taksit için zaten bir ödeme kaydı mevcut.")

        transaction_match = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            installment_number=installment_number,
            tenant_id=tenant_id,
        ).first()

        payment = Payment(
            plan_id=plan_id,
            amount=amount,
            payment_date=payment_date,
            installment_number=installment_number,
            notes=notes,
            tenant_id=tenant_id,
        )
        self.session.add(payment)

        if transaction_match:
            transaction_match.status = 'Ödendi'
            transaction_match.date = payment_date
            transaction_match.amount = amount
            transaction_match.note = (transaction_match.note or '')
            if notes:
                transaction_match.note = f"{transaction_match.note} | Ödeme notu: {notes}" if transaction_match.note else f"Ödeme notu: {notes}"
            self.session.flush()
            payment.transaction_id = transaction_match.id
        else:
            paid_tx = Transaction(
                date=payment_date,
                category=plan.category,
                description=f"{plan.name} ({installment_number}/{plan.installments})",
                type=plan.flow_type,
                amount=amount,
                status='Ödendi',
                note=notes,
                source_id=plan_id,
                source_type='plan',
                installment_number=installment_number,
                tenant_id=tenant_id,
            )
            self.session.add(paid_tx)
            self.session.flush()
            payment.transaction_id = paid_tx.id

        try:
            occ = PlanOccurrence.query.filter_by(
                plan_id=plan_id,
                occurrence_number=installment_number,
                tenant_id=tenant_id,
            ).first()
            if not occ and payment_date:
                occ = PlanOccurrence.query.filter_by(
                    plan_id=plan_id,
                    scheduled_date=str(payment_date),
                    tenant_id=tenant_id,
                ).first()
            if occ:
                occ.status = 'paid'
                occ.transaction_id = payment.transaction_id
                try:
                    occ.paid_at = datetime.fromisoformat(str(payment_date))
                except (ValueError, TypeError):
                    occ.paid_at = _models.utcnow_naive()
            else:
                occ = PlanOccurrence(
                    plan_id=plan_id,
                    occurrence_number=installment_number,
                    scheduled_date=str(payment_date),
                    status='paid',
                    amount=amount,
                    tenant_id=tenant_id,
                    transaction_id=payment.transaction_id,
                    paid_at=datetime.fromisoformat(str(payment_date)) if payment_date else _models.utcnow_naive(),
                )
                self.session.add(occ)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("PlanOccurrence payment sync warning: %s", exc)

        self.commit()
        invalidate_financial_cache(tenant_id)
        return payment

    def update_recurring_plan(
        self,
        plan_id,
        name,
        category,
        amount,
        installments,
        payment_day,
        note=None,
        start_date=None,
        tenant_id=None,
        plan_type=None,
        frequency=None,
        end_date=None,
        target_asset_id=None,
        version=None,
        status=None
    ) -> RecurringPlan:
        tenant_id = self._resolve_tenant_id(tenant_id)
        cat = Category.query.filter_by(name=category).first()
        if not cat:
            raise ValueError("Geçersiz kategori")
        if cat.type not in ('Gelir', 'Gider', 'Yatırım'):
            raise ValueError("Plan yalnızca gelir, gider veya yatırım kategorisiyle güncellenebilir")

        plan = RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()
        if not plan:
            raise NotFound("Plan bulunamadı.")

        if version is not None:
            from domain.transactions.services.financial_ledger import OptimisticConcurrencyError
            if plan.version != version:
                raise OptimisticConcurrencyError("Plan başka bir oturumda güncellendi; en güncel kaydı yükleyip tekrar deneyin.")
        plan.name = name
        plan.category = category
        plan.flow_type = 'Gider' if cat.type == 'Yatırım' else cat.type

        plan.amount = amount
        plan.installments = installments
        if plan_type is not None:
            plan.plan_type = plan_type
        if frequency is not None:
            plan.frequency = frequency
        if status is not None and status in ('Aktif', 'Duraklatıldı', 'Tamamlandı', 'İptal'):
            plan.status = status
        plan.end_date = end_date
        plan.target_asset_id = target_asset_id

        plan.payment_day = payment_day
        plan.start_date = start_date
        plan.note = (note or '').strip() or None

        tx_query = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            status='Bekliyor',
            tenant_id=tenant_id,
        )
        try:
            pending_txs = tx_query.all()
            if isinstance(pending_txs, list) and pending_txs:
                tx_ids = [getattr(t, 'id', None) for t in pending_txs if getattr(t, 'id', None) is not None]
                if tx_ids:
                    LedgerAdjustment.query.filter(
                        (LedgerAdjustment.original_transaction_id.in_(tx_ids))
                        | (LedgerAdjustment.compensating_transaction_id.in_(tx_ids))
                    ).delete(synchronize_session=False)
                    LedgerAuditEvent.query.filter(LedgerAuditEvent.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
                    LogbookEntry.query.filter(LogbookEntry.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
                    PlanOccurrence.query.filter(PlanOccurrence.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
                    Payment.query.filter(Payment.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
        except Exception:
            pass
        tx_query.delete(synchronize_session=False)
        self.session.expire_all()
        if plan.status == 'Aktif':
            self._create_transactions_from_plan(plan)

        self.commit()
        invalidate_financial_cache(tenant_id)
        return plan

    def delete_plan(self, plan_id, tenant_id=None):
        tenant_id = self._resolve_tenant_id(tenant_id)
        plan = RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()
        if not plan:
            return False

        PlanOccurrence.query.filter_by(plan_id=plan_id, tenant_id=tenant_id).delete(synchronize_session=False)
        Payment.query.filter_by(plan_id=plan_id, tenant_id=tenant_id).delete(synchronize_session=False)

        pending_txs = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            status='Bekliyor',
            tenant_id=tenant_id,
        ).all()
        for tx in pending_txs:
            tx.is_deleted = True
            tx.deleted_at = datetime.now()
            tx.deleted_by = None

        paid_txs = Transaction.query.filter_by(
            source_id=plan_id,
            source_type='plan',
            status='Ödendi',
            tenant_id=tenant_id,
        ).all()
        for tx in paid_txs:
            tx.source_id = None
            tx.source_type = None

        self.session.delete(plan)
        self.commit()
        invalidate_financial_cache(tenant_id)

        return {
            'success': True,
            'paid_count': len(paid_txs),
            'pending_count': len(pending_txs),
        }

    def list_recurring_plans(self, flow_type=None, tenant_id=None) -> List[RecurringPlan]:
        query = RecurringPlan.query
        if flow_type:
            query = query.filter_by(flow_type=flow_type)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(RecurringPlan.name).all()

    def get_recurring_plan_for_tenant(self, plan_id, tenant_id) -> Optional[RecurringPlan]:
        return RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()

    def get_plan_transaction_counts(self, plan_id: int, tenant_id: Optional[str] = None) -> dict:
        """Returns paid and pending transaction counts for a plan."""
        tenant_id = self._resolve_tenant_id(tenant_id)
        paid_count = Transaction.query.filter_by(
            source_id=plan_id, source_type='plan', tenant_id=tenant_id, status='Ödendi', is_deleted=False
        ).count()
        pending_count = Transaction.query.filter_by(
            source_id=plan_id, source_type='plan', tenant_id=tenant_id, status='Bekliyor', is_deleted=False
        ).count()
        return {
            'paid_count': paid_count,
            'pending_count': pending_count,
            'has_paid': paid_count > 0,
        }

    def delete_plan_pending_transactions(self, plan_id: int, tenant_id: Optional[str] = None) -> int:
        """Deletes only pending transactions for a plan."""
        tenant_id = self._resolve_tenant_id(tenant_id)
        pending_txs = Transaction.query.filter_by(
            source_id=plan_id, source_type='plan',
            status='Bekliyor', tenant_id=tenant_id
        ).all()
        if not pending_txs:
            return 0
        tx_ids = [t.id for t in pending_txs]
        LedgerAdjustment.query.filter(
            (LedgerAdjustment.original_transaction_id.in_(tx_ids))
            | (LedgerAdjustment.compensating_transaction_id.in_(tx_ids))
        ).delete(synchronize_session=False)
        LedgerAuditEvent.query.filter(LedgerAuditEvent.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
        LogbookEntry.query.filter(LogbookEntry.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
        PlanOccurrence.query.filter(
            PlanOccurrence.transaction_id.in_(tx_ids)
        ).delete(synchronize_session=False)
        Payment.query.filter(
            Payment.transaction_id.in_(tx_ids)
        ).delete(synchronize_session=False)
        deleted = Transaction.query.filter(
            Transaction.id.in_(tx_ids)
        ).delete(synchronize_session=False)
        self.commit()
        invalidate_financial_cache(tenant_id)
        return deleted
