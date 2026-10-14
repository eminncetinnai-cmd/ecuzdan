from datetime import datetime, timezone

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Notification(db.Model):
    """Uygulama içi bildirim (Faz 21+).

    Teslimat kanalı uygulama içidir; e-posta/push altyapısı yok. Kurallar
    domain/notifications/services/notification_rules.py içinde değerlendirilir.

    dedupe_key: aynı uyarının her değerlendirmede tekrar üretilmesini engeller
    (ör. 'budget:Market:2026-08'). Kullanıcı başına tekildir.

    Delivery tracking: sent_at, delivered_at, read_at, failed_at, failure_reason
    """
    __tablename__ = 'notification'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'dedupe_key', name='uq_notification_user_dedupe'),
        db.Index('idx_notification_user_read_created', 'user_id', 'is_read', 'created_at'),
        db.Index('idx_notification_category', 'category'),
        db.Index('idx_notification_created_at', 'created_at'),
        db.Index('idx_notification_tenant_user', 'tenant_id', 'user_id'),
        db.Index('idx_notification_delivery_status', 'delivery_status'),
        db.Index('idx_notification_priority', 'priority'),
    )

    SEVERITIES = ('info', 'warning', 'danger')
    PRIORITIES = ('low', 'normal', 'high', 'urgent')
    DELIVERY_STATUSES = ('pending', 'sent', 'delivered', 'read', 'failed')

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    category = db.Column(db.String(30), nullable=False)   # 'budget' | 'payment' | 'system' | 'asset'
    severity = db.Column(db.String(10), default='info', nullable=False)
    priority = db.Column(db.String(10), default='normal', nullable=False)
    delivery_status = db.Column(db.String(10), default='pending', nullable=False)

    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(400), nullable=True)
    link = db.Column(db.String(200), nullable=True)

    # Action buttons (JSON): [{"label": "View", "action": "link", "value": "/transactions"}]
    actions = db.Column(db.JSON, nullable=True)

    dedupe_key = db.Column(db.String(160), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # Delivery tracking
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.String(200), nullable=True)

    # Expiration
    expires_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)

    def __repr__(self):
        return f'<Notification {self.category}:{self.dedupe_key}>'

    def is_expired(self):
        """Check if notification is expired."""
        if self.expires_at is None:
            return False
        return utcnow_naive() > self.expires_at

    def mark_sent(self):
        """Mark notification as sent."""
        self.sent_at = utcnow_naive()
        self.delivery_status = 'sent'

    def mark_delivered(self):
        """Mark notification as delivered."""
        self.delivered_at = utcnow_naive()
        self.delivery_status = 'delivered'

    def mark_read(self):
        """Mark notification as read."""
        self.read_at = utcnow_naive()
        self.is_read = True
        self.delivery_status = 'read'

    def mark_failed(self, reason):
        """Mark notification as failed."""
        self.failed_at = utcnow_naive()
        self.failure_reason = reason
        self.delivery_status = 'failed'
