"""Update transaction command."""

import logging

from flask import g

from application.base import Command
from application.ports.outbox_port import OutboxPort
from domain.transactions.events import TransactionUpdatedEvent
from domain.transactions.services import OptimisticConcurrencyError, update_one_time_transaction
from engines.financial_engine import parse_date_input, today_storage
from models import BankAccount, Transaction
from repositories.catalog_repository import CatalogRepository
from utils.audit import audit_log

logger = logging.getLogger(__name__)


class UpdateTransactionCommand(Command):
    def __init__(
        self,
        catalog_repository: CatalogRepository,
        outbox: OutboxPort | None = None,
    ):
        self.catalog_repository = catalog_repository
        self._outbox = outbox

    def execute(self, tx_id, dto, tenant_id=None):
        tenant_id = tenant_id or g.get("tenant_id")
        bank_account_id = getattr(dto, 'bank_account_id', None)

        if bank_account_id is not None:
            bank_account = BankAccount.query.filter_by(
                id=bank_account_id,
                tenant_id=tenant_id,
                is_active=True,
            ).first()
            if not bank_account:
                raise ValueError('Banka hesabı bulunamadı veya aktif değil.')

        expected_version = getattr(dto, "version", None)
        if expected_version is not None:
            tx_check = Transaction.query.filter_by(id=tx_id, tenant_id=tenant_id, is_deleted=False).first()
            if not tx_check or tx_check.version != expected_version:
                raise OptimisticConcurrencyError("İşlem başka bir oturumda güncellendi; en güncel kaydı yükleyip tekrar deneyin.")
        category = self.catalog_repository.find_category_by_name(dto.category, tenant_id)
        if not category:
            raise ValueError("Geçersiz kategori seçildi.")
        parsed_date = parse_date_input(dto.date) if dto.date.strip() else today_storage()

        # Domain logic
        tx = update_one_time_transaction(
            tx_id,
            parsed_date,
            category.name,
            dto.description or category.name,
            dto.amount,
            dto.status,
            dto.note,
            tenant_id=tenant_id,
            bank_account_id=bank_account_id,
        )

        audit_log('TRANSACTION_UPDATED', user_id=None, username=None, tenant_id=tenant_id, entity_type='transaction', entity_id=tx.id, details={'category': tx.category, 'amount': str(tx.amount), 'type': tx.type})

        # Outbox event
        event = TransactionUpdatedEvent(
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
