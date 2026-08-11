"""SQLAlchemy adapter for OutboxPort.

This is the infrastructure-layer implementation of the application-layer
OutboxPort.  It persists domain events to the ``outbox_messages`` table
using the shared SQLAlchemy session so the write participates in the
caller's existing transaction boundary.
"""

import json
import uuid
from dataclasses import asdict

from application.ports.outbox_port import OutboxPort
from domain.common.events import DomainEvent
from infrastructure.database.models.outbox_model import OutboxMessageModel
from shared.db import db


class SqlAlchemyOutboxAdapter(OutboxPort):
    """Persist events into the ``outbox_messages`` table."""

    def save(self, event: DomainEvent) -> None:
        """Write the event as an OutboxMessageModel row.

        The caller is responsible for committing the session.
        """
        event_dict = asdict(event)
        payload = json.dumps(event_dict, default=str)

        outbox_msg = OutboxMessageModel(
            id=str(uuid.uuid4()),
            event_type=event.__class__.__name__,
            payload=payload,
        )
        db.session.add(outbox_msg)
        # NOTE: No commit here — the use-case or UoW commits.
