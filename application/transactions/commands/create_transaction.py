"""Create transaction command."""

import logging

from flask import g
from sqlalchemy.exc import IntegrityError

from application.base import Command
from application.ports.outbox_port import OutboxPort
from domain.transactions.events import TransactionCreatedEvent
from domain.transactions.services import create_one_time_transaction
from engines.financial_engine import parse_date_input, today_storage
from models import BankAccount, Transaction
from repositories.catalog_repository import CatalogRepository
from shared.db import db
from utils.audit import audit_log


def _find_existing_idempotent_transaction(tenant_id, idempotency_key):
    return db.session.query(Transaction).filter(
        Transaction.tenant_id == tenant_id,
        Transaction.idempotency_key == idempotency_key,
        Transaction.is_deleted.is_(False),
    ).first()

logger = logging.getLogger(__name__)


class CreateTransactionCommand(Command):
    def __init__(
        self,
        catalog_repository: CatalogRepository,
        outbox: OutboxPort | None = None,
    ):
        self.catalog_repository = catalog_repository
        self._outbox = outbox

    def execute(self, dto, tenant_id=None):
        idempotency_key = getattr(dto, "idempotency_key", None)
        tenant_id = tenant_id or g.get("tenant_id")
        if idempotency_key:
            existing = _find_existing_idempotent_transaction(tenant_id, idempotency_key)
            if existing:
                return existing

        bank_account_id = getattr(dto, 'bank_account_id', None)
        if bank_account_id is not None:
            bank_account = BankAccount.query.filter_by(
                id=bank_account_id,
                tenant_id=tenant_id,
                is_active=True,
            ).first()
            if not bank_account:
                raise ValueError('Banka hesabı bulunamadı veya aktif değil.')

        category = self.catalog_repository.find_category_by_name(dto.category, tenant_id)

        if not category:
            raise ValueError("Geçersiz kategori seçildi.")

        parsed_date = parse_date_input(dto.date) if dto.date.strip() else today_storage()

        # Domain logic
        tx = create_one_time_transaction(
            parsed_date,
            category.name,
            dto.description or category.name,
            dto.amount,
            dto.status,
            dto.note,
            idempotency_key=idempotency_key,
            tenant_id=tenant_id,
            bank_account_id=bank_account_id,
        )

        if idempotency_key and getattr(tx, "idempotency_key", None) != idempotency_key:
            try:
                tx.idempotency_key = idempotency_key
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                existing = _find_existing_idempotent_transaction(tenant_id, idempotency_key)
                if existing:
                    return existing
                raise
        audit_log('TRANSACTION_CREATED', user_id=None, username=None, tenant_id=tenant_id, entity_type='transaction', entity_id=tx.id, details={'category': tx.category, 'amount': str(tx.amount), 'type': tx.type})

        # Outbox event
        event = TransactionCreatedEvent(
            transaction_id=tx.id,
            category=category.name,
            amount=dto.amount,
            status=dto.status,
            tenant_id=tenant_id,
        )
        if self._outbox:
            try:
                self._outbox.save(event)
            except Exception as e:
                logger.warning("Outbox write failed for %s: %s", type(event).__name__, e)

        return tx
