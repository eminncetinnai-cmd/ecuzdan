"""Repository for in-app notifications (Faz 21)."""

from models import Notification

from .base import BaseRepository


class NotificationRepository(BaseRepository):
    def add_notification(self, **fields):
        return self.add(Notification(**fields))

    def get_notification(self, notification_id):
        return self.get(Notification, notification_id)

    def existing_keys(self, user_id, dedupe_keys):
        """Verilen anahtarlardan hangileri bu kullanıcıda zaten var."""
        if not dedupe_keys:
            return set()
        rows = (
            self.session.query(Notification.dedupe_key)
            .filter(Notification.user_id == user_id, Notification.dedupe_key.in_(dedupe_keys))
            .all()
        )
        return {row[0] for row in rows}

    def list_notifications(self, user_id, limit=30):
        return (
            self.session.query(Notification)
            .filter_by(user_id=user_id)
            .order_by(Notification.is_read, Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def unread_count(self, user_id):
        return self.session.query(Notification).filter_by(user_id=user_id, is_read=False).count()

    def mark_all_read(self, user_id):
        return (
            self.session.query(Notification)
            .filter_by(user_id=user_id, is_read=False)
            .update({'is_read': True}, synchronize_session=False)
        )

    def delete_read(self, user_id):
        return (
            self.session.query(Notification)
            .filter_by(user_id=user_id, is_read=True)
            .delete(synchronize_session=False)
        )

    def delete_expired(self, user_id):
        """Delete expired notifications for user."""
        from datetime import datetime
        return (
            self.session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.expires_at < datetime.utcnow()
            )
            .delete(synchronize_session=False)
        )

    def list_by_priority(self, user_id, priority=None, limit=30):
        """List notifications by priority."""
        from models import db
        query = self.session.query(Notification).filter_by(user_id=user_id)
        if priority:
            query = query.filter_by(priority=priority)
        return (
            query.order_by(
                # Priority order: urgent > high > normal > low
                db.case(
                    (Notification.priority == 'urgent', 1),
                    (Notification.priority == 'high', 2),
                    (Notification.priority == 'normal', 3),
                    (Notification.priority == 'low', 4),
                    else_=5
                ),
                Notification.is_read,
                Notification.created_at.desc()
            )
            .limit(limit)
            .all()
        )

    def list_by_delivery_status(self, user_id, status=None, limit=30):
        """List notifications by delivery status."""
        query = self.session.query(Notification).filter_by(user_id=user_id)
        if status:
            query = query.filter_by(delivery_status=status)
        return (
            query.order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
