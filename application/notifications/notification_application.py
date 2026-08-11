"""NotificationApplicationService (Faz 21)."""

from application.base import ApplicationService


class NotificationApplicationService(ApplicationService):
    def __init__(self, notification_service=None, **kwargs):
        super().__init__(**kwargs)
        self.notification_service = notification_service

    def refresh(self, user, preferences=None):
        return self.execute(lambda: self.notification_service.refresh(user, preferences))

    def list_for_user(self, user_id):
        return self.execute(lambda: self.notification_service.list_for_user(user_id))

    def unread_count(self, user_id):
        return self.execute(lambda: self.notification_service.unread_count(user_id))

    def mark_read(self, user_id, notification_id):
        return self.execute(lambda: self.notification_service.mark_read(user_id, notification_id))

    def mark_all_read(self, user_id):
        return self.execute(lambda: self.notification_service.mark_all_read(user_id))

    def delete(self, user_id, notification_id):
        return self.execute(lambda: self.notification_service.delete(user_id, notification_id))

    def delete_read(self, user_id):
        return self.execute(lambda: self.notification_service.delete_read(user_id))

    def delete_expired(self, user_id):
        return self.execute(lambda: self.notification_service.delete_expired(user_id))

    def mark_sent(self, notification_id):
        return self.execute(lambda: self.notification_service.mark_sent(notification_id))

    def mark_delivered(self, notification_id):
        return self.execute(lambda: self.notification_service.mark_delivered(notification_id))

    def mark_failed(self, notification_id, reason):
        return self.execute(lambda: self.notification_service.mark_failed(notification_id, reason))

    def list_by_priority(self, user_id, priority=None, limit=30):
        return self.execute(lambda: self.notification_service.repository.list_by_priority(user_id, priority, limit))

    def list_by_delivery_status(self, user_id, status=None, limit=30):
        return self.execute(lambda: self.notification_service.repository.list_by_delivery_status(user_id, status, limit))
