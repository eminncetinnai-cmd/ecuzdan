"""Outbox database service."""

import json
import uuid
from dataclasses import asdict

from domain.common.events import DomainEvent
from infrastructure.database.models.outbox_model import OutboxMessageModel
from shared.db import db


def save_to_outbox(event: DomainEvent) -> None:
    """Save a domain event to the outbox in the current transaction boundary."""
    event_dict = asdict(event)
    payload = json.dumps(event_dict, default=str)

    outbox_msg = OutboxMessageModel(
        id=str(uuid.uuid4()),
        event_type=event.__class__.__name__,
        payload=payload
    )
    db.session.add(outbox_msg)
    # Note: We do NOT commit here. The calling use case is responsible
    # for committing the transaction (e.g., via rollback_session or db.atomic).


def count_pending_outbox_messages() -> int:
    """Return the number of pending outbox messages."""
    return OutboxMessageModel.query.filter_by(processed_on=None).count()
