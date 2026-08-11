"""Create transaction command."""

import logging

from application.base import Command
from application.ports.outbox_port import OutboxPort
from domain.transactions.events import TransactionCreatedEvent
from domain.transactions.services import create_one_time_transaction
from engines.financial_engine import parse_date_input, today_storage
from repositories.catalog_repository import CatalogRepository

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
            tenant_id=tenant_id,
        )

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
