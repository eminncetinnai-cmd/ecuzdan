"""SQLAlchemy model for the Outbox pattern."""

from datetime import datetime, timezone

from shared.db import db


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class OutboxMessageModel(db.Model):
    __tablename__ = 'outbox_messages'

    id = db.Column(db.String(36), primary_key=True)
    event_type = db.Column(db.String(128), nullable=False)
    payload = db.Column(db.Text, nullable=False)  # JSON serialized data
    occurred_on = db.Column(db.DateTime, nullable=False, default=utcnow_naive)
    processed_on = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<OutboxMessage {self.id} type={self.event_type} processed={self.processed_on is not None}>"
