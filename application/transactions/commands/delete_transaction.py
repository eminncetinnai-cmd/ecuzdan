"""Delete transaction command."""

import logging

from application.base import Command
from application.ports.outbox_port import OutboxPort
from domain.transactions.events import TransactionDeletedEvent
from domain.transactions.services import delete_one_time_transaction

logger = logging.getLogger(__name__)


class DeleteTransactionCommand(Command):
    def __init__(
        self,
        outbox: OutboxPort | None = None,
    ):
        self._outbox = outbox

    def execute(self, tx_id, tenant_id=None):
        # Domain logic
        result = delete_one_time_transaction(tx_id, tenant_id=tenant_id)

        # Outbox event
        event = TransactionDeletedEvent(
            transaction_id=tx_id,
            tenant_id=tenant_id,
        )
        if self._outbox:
            try:
                self._outbox.save(event)
            except Exception as e:
                logger.warning("Outbox write failed for %s: %s", type(event).__name__, e)

        return result
