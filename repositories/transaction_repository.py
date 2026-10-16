"""
Transaction Repository — repositories/transaction_repository.py

İşlem (Transaction) tablosu için read/write repository.
İşlem ekleme, listeleme, güncelleme, hızlı ödeme, silme ve
çift kayıt (Dual-Write Immutable Ledger) mekanizmalarını yönetir.
"""

import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound

import models as _models
from engines.financial_engine import invalidate_financial_cache

from .base import BaseRepository
from .contracts import BaseRepositoryContract

logger = logging.getLogger(__name__)


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


Account = _ModelLookup('Account', getattr(_models, 'Account', None))
Category = _ModelLookup('Category', getattr(_models, 'Category', None))
Payment = _ModelLookup('Payment', getattr(_models, 'Payment', None))
PlanOccurrence = _ModelLookup('PlanOccurrence', getattr(_models, 'PlanOccurrence', None))
RecurringPlan = _ModelLookup('RecurringPlan', getattr(_models, 'RecurringPlan', None))
Transaction = _ModelLookup('Transaction', getattr(_models, 'Transaction', None))



class TransactionRepository(BaseRepository, BaseRepositoryContract):
    """
    Transaction veri erişim repository'si.
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

    def transaction_page(
        self,
        page: int = 1,
        per_page: int = 50,
        tenant_id: Optional[str] = None,
        include_deleted: bool = False
    ):
        tenant_id = self._resolve_tenant_id(tenant_id)
        if not include_deleted:
            query = Transaction.query.filter_by(tenant_id=tenant_id, is_deleted=False)
        else:
            query = Transaction.query.filter_by(tenant_id=tenant_id)
        if not hasattr(query, '_mock_return_value') and hasattr(_models.Transaction, 'bank_account'):
            query = query.options(joinedload(_models.Transaction.bank_account))
        return query.order_by(Transaction.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_transaction(
        self,
        transaction_id: int,
        tenant_id: Optional[str] = None,
        include_deleted: bool = False
    ) -> Optional[Transaction]:
        tenant_id = self._resolve_tenant_id(tenant_id)
        if not include_deleted:
            return Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id, is_deleted=False).first()
        return Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()

    def list_transactions(
        self,
        tenant_id: Optional[str] = None,
        order_desc: bool = True,
        include_deleted: bool = False
    ) -> List[Transaction]:
        query = Transaction.query
        if tenant_id:
            if not include_deleted:
                query = query.filter_by(tenant_id=tenant_id, is_deleted=False)
            else:
                query = query.filter_by(tenant_id=tenant_id)
        elif not include_deleted:
            query = query.filter_by(is_deleted=False)
        if not hasattr(query, '_mock_return_value') and hasattr(_models.Transaction, 'bank_account'):
            query = query.options(joinedload(_models.Transaction.bank_account))
        order = Transaction.date.desc() if order_desc else Transaction.date.asc()
        return query.order_by(order).all()

    def add_transaction(
        self,
        date: str,
        category: str,
        description: str,
        type_: str,
        amount,
        status: str,
        note: Optional[str] = None,
        source_id: Optional[int] = None,
        source_type: Optional[str] = None,
        installment_number: Optional[int] = None,
        tenant_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        bank_account_id: Optional[int] = None,
    ) -> Transaction:
        from flask import g


        tenant_id = tenant_id or g.get('tenant_id')
        transaction = Transaction(
            date=date,
            category=category,
            description=(description or '').strip(),
            note=(note or '').strip() or None,
            type=type_,
            amount=amount,
            status=status,
            installment_number=installment_number,
            source_id=source_id,
            source_type=source_type,
            idempotency_key=idempotency_key,
            tenant_id=tenant_id,
            bank_account_id=bank_account_id,
        )
        self.session.add(transaction)
        self.session.flush()

        # Dual-Write for Immutable Ledger
        if status == 'Ödendi' and tenant_id:
            self._record_ledger_dual_write(transaction, tenant_id, amount=amount)

        self.commit()
        invalidate_financial_cache(tenant_id)
        return transaction

    def _record_ledger_dual_write(
        self,
        transaction: Transaction,
        tenant_id: str,
        amount=None,
    ) -> None:
        """Kasa ve kategori hesapları arasında çift taraflı defter kaydı (Immutable Ledger) oluşturur."""
        from domain.ledger.services.ledger_service import LedgerService
        LedgerService.record_dual_write(
            transaction=transaction,
            tenant_id=tenant_id,
            amount=amount,
            session=self.session,
        )

    def update_transaction(
        self,
        transaction_id: int,
        date: str,
        category: str,
        description: str,
        amount,
        status: str,
        note: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Transaction:
        tenant_id = self._resolve_tenant_id(tenant_id)
        transaction = Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()
        if not transaction:
            raise NotFound("İşlem bulunamadı.")
        if transaction.status == 'Ödendi':
            from domain.transactions.services.financial_ledger import LedgerError

            raise LedgerError(
                "Ödenmiş işlem doğrudan güncellenemez. Değişiklik için reversal veya adjustment oluşturun."
            )
        category_obj = Category.query.filter_by(name=category).first()

        if not category_obj:
            raise ValueError("Geçersiz Kategori")

        previous_status = transaction.status
        transaction.date = date
        transaction.category = category
        transaction.description = (description or '').strip()
        transaction.note = (note or '').strip() or None
        transaction.amount = amount
        transaction.status = status
        transaction.type = category_obj.type

        if previous_status != 'Ödendi' and status == 'Ödendi' and tenant_id:
            self._record_ledger_dual_write(transaction, tenant_id, amount=amount)

        if getattr(transaction, 'source_type', None) == 'plan' and getattr(transaction, 'source_id', None):
            try:
                occ_query = PlanOccurrence.query.filter_by(
                    plan_id=transaction.source_id,
                    tenant_id=tenant_id,
                )
                if getattr(transaction, 'installment_number', None) is not None:
                    occ = occ_query.filter_by(occurrence_number=transaction.installment_number).first()
                else:
                    occ = occ_query.filter_by(scheduled_date=str(date)).first()
                if occ:
                    if status == 'Ödendi':
                        occ.status = 'paid'
                        occ.transaction_id = transaction.id
                        if not occ.paid_at:
                            occ.paid_at = _models.utcnow_naive()
                    elif status == 'Bekliyor':
                        occ.status = 'scheduled'
            except Exception as e:
                logger.warning("Failed to sync occurrence on transaction update: %s", e)

        self.commit()
        invalidate_financial_cache(tenant_id)
        return transaction

    def quick_pay_transaction(
        self,
        transaction_id: int,
        tenant_id: Optional[str] = None
    ) -> Transaction:
        """Mark a pending transaction as paid, syncing plan occurrences and payments if applicable."""
        tenant_id = self._resolve_tenant_id(tenant_id)
        transaction = Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id, is_deleted=False).first()
        if not transaction:
            raise NotFound("İşlem bulunamadı.")
        if transaction.status == 'Ödendi':
            return transaction

        transaction.status = 'Ödendi'
        transaction.version = (transaction.version or 1) + 1

        if tenant_id:
            self._record_ledger_dual_write(transaction, tenant_id)

        if getattr(transaction, 'source_type', None) == 'plan' and getattr(transaction, 'source_id', None):
            plan_id = transaction.source_id
            installment_num = getattr(transaction, 'installment_number', None)

            if installment_num:
                existing_payment = Payment.query.filter_by(
                    plan_id=plan_id,
                    installment_number=installment_num,
                    tenant_id=tenant_id,
                ).first()
                if not existing_payment:
                    from datetime import datetime
                    payment = Payment(
                        plan_id=plan_id,
                        amount=transaction.amount,
                        payment_date=transaction.date or datetime.now().date().isoformat(),
                        installment_number=installment_num,
                        notes=transaction.note,
                        tenant_id=tenant_id,
                        transaction_id=transaction.id,
                    )
                    self.session.add(payment)
                elif not existing_payment.transaction_id:
                    existing_payment.transaction_id = transaction.id

            try:
                occ_query = PlanOccurrence.query.filter_by(plan_id=plan_id, tenant_id=tenant_id)
                occ = None
                if installment_num is not None:
                    occ = occ_query.filter_by(occurrence_number=installment_num).first()
                if not occ and transaction.date:
                    occ = occ_query.filter_by(scheduled_date=str(transaction.date)).first()
                if occ:
                    occ.status = 'paid'
                    occ.transaction_id = transaction.id
                    if not occ.paid_at:
                        occ.paid_at = _models.utcnow_naive()
            except Exception as e:
                logger.warning("Failed to sync occurrence on quick pay: %s", e)

            try:
                self.session.flush()
                plan = RecurringPlan.query.filter_by(id=plan_id, tenant_id=tenant_id).first()
                if plan and plan.installments and plan.installments > 0:
                    paid_count = Transaction.query.filter_by(
                        source_id=plan_id,
                        source_type='plan',
                        tenant_id=tenant_id,
                        status='Ödendi',
                        is_deleted=False,
                    ).count()
                    if paid_count >= plan.installments:
                        plan.status = 'Tamamlandı'
            except Exception as e:
                logger.warning("Failed to check plan completion on quick pay: %s", e)

        self.commit()
        invalidate_financial_cache(tenant_id)
        return transaction

    def delete_transaction(self, transaction_id: int, tenant_id: Optional[str] = None) -> None:
        tenant_id = self._resolve_tenant_id(tenant_id)
        transaction = Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()
        if not transaction:
            raise NotFound("İşlem bulunamadı.")
        if transaction.status == 'Ödendi':
            from domain.transactions.services.financial_ledger import LedgerError

            raise LedgerError(
                "Ödenmiş işlem silinemez. Değişiklik için reversal veya adjustment oluşturun."
            )
        self.session.delete(transaction)
        self.commit()
        invalidate_financial_cache(tenant_id)

    def pending_transactions_between(self, start: str, end: str, tenant_id: Optional[str] = None) -> List[Transaction]:
        tenant_id = self._resolve_tenant_id(tenant_id)
        return Transaction.query.filter(
            Transaction.type.in_(['Gider', 'Yatırım']),
            Transaction.status == 'Bekliyor',
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.tenant_id == tenant_id,
            Transaction.is_deleted.is_(False),
        ).order_by(Transaction.date).all()
