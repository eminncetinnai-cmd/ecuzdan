"""Transaction event handlers."""

import logging
from domain.transactions.events import TransactionCreatedEvent, TransactionUpdatedEvent, TransactionDeletedEvent

logger = logging.getLogger(__name__)


def handle_transaction_created(event: TransactionCreatedEvent):
    """Handle side effects when a transaction is created."""
    logger.info(f"Side-effect processing for created transaction: {event.transaction_id} (Category: {event.category}, Amount: {event.amount})")
    # In a real system, we could clear caches, update analytical models, 
    # or notify other bounded contexts via RabbitMQ/Kafka here.


def handle_transaction_updated(event: TransactionUpdatedEvent):
    """Handle side effects when a transaction is updated."""
    logger.info(f"Side-effect processing for updated transaction: {event.transaction_id}")


def handle_transaction_deleted(event: TransactionDeletedEvent):
    """Handle side effects when a transaction is deleted."""
    logger.info(f"Side-effect processing for deleted transaction: {event.transaction_id}")


def register_handlers(event_bus):
    """Register all transaction handlers with the provided event bus."""
    event_bus.subscribe(TransactionCreatedEvent, handle_transaction_created)
    event_bus.subscribe(TransactionUpdatedEvent, handle_transaction_updated)
    event_bus.subscribe(TransactionDeletedEvent, handle_transaction_deleted)
    logger.debug("Registered transaction event handlers.")
