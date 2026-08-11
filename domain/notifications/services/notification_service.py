"""Bildirim servisi (Faz 21)."""

import logging

from .notification_rules import evaluate_all

logger = logging.getLogger(__name__)

#: Zil açıldığında listelenecek en fazla bildirim.
LIST_LIMIT = 30


class NotificationService:
    def __init__(self, repository=None):
        self.repository = repository

    def refresh(self, user, preferences=None):
        """
        Kuralları çalıştırır ve YENİ bildirimleri kaydeder.

        dedupe_key zaten varsa kayıt oluşturulmaz — böylece her sayfa
        yenilemesinde aynı uyarı çoğalmaz. Kullanıcının okuduğu bir uyarı
        koşul sürse bile tekrar "okunmadı" yapılmaz; bilinçli tercih:
        aksi halde kapatılamayan bir bildirim olurdu.
        """
        if not user:
            return 0
        drafts = evaluate_all(user.tenant_id, preferences=preferences)
        if not drafts:
            return 0

        existing = self.repository.existing_keys(user.id, [d['dedupe_key'] for d in drafts])
        created = 0
        for draft in drafts:
            if draft['dedupe_key'] in existing:
                continue
            self.repository.add_notification(
                user_id=user.id,
                tenant_id=user.tenant_id,
                **draft,
            )
            created += 1
        if created:
            self.repository.commit()
        return created

    def list_for_user(self, user_id, limit=LIST_LIMIT):
        return self.repository.list_notifications(user_id, limit=limit)

    def unread_count(self, user_id):
        return self.repository.unread_count(user_id)

    def mark_read(self, user_id, notification_id):
        notification = self.repository.get_notification(notification_id)
        if not notification or notification.user_id != user_id:
            raise PermissionError('Bu bildirime erişiminiz yok.')
        notification.mark_read()
        self.repository.commit()
        return notification

    def mark_all_read(self, user_id):
        count = self.repository.mark_all_read(user_id)
        self.repository.commit()
        return count

    def delete(self, user_id, notification_id):
        notification = self.repository.get_notification(notification_id)
        if not notification or notification.user_id != user_id:
            raise PermissionError('Bu bildirime erişiminiz yok.')
        self.repository.delete(notification)
        self.repository.commit()
        return notification

    def delete_read(self, user_id):
        count = self.repository.delete_read(user_id)
        self.repository.commit()
        return count

    def delete_expired(self, user_id):
        """Delete expired notifications for user."""
        count = self.repository.delete_expired(user_id)
        self.repository.commit()
        return count

    def mark_sent(self, notification_id):
        """Mark notification as sent."""
        notification = self.repository.get_notification(notification_id)
        if notification:
            notification.mark_sent()
            self.repository.commit()
        return notification

    def mark_delivered(self, notification_id):
        """Mark notification as delivered."""
        notification = self.repository.get_notification(notification_id)
        if notification:
            notification.mark_delivered()
            self.repository.commit()
        return notification

    def mark_failed(self, notification_id, reason):
        """Mark notification as failed."""
        notification = self.repository.get_notification(notification_id)
        if notification:
            notification.mark_failed(reason)
            self.repository.commit()
        return notification
