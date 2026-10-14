from datetime import datetime, timezone

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Tenant(db.Model):
    """Kiracı (Tenant) modeli - Multi-tenant mimarisi için"""
    __tablename__ = 'tenant'
    __table_args__ = (
        db.Index('idx_tenant_status', 'status'),
        db.Index('idx_tenant_created_at', 'created_at'),
    )

    id = db.Column(db.String(50), primary_key=True)  # tenant_id
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow_naive)
    status = db.Column(db.String(20), default='active')  # 'active', 'suspended', 'deleted'
    base_currency = db.Column(db.String(3), default='TRY', nullable=False)  # Phase 5: Base currency

    def __repr__(self):
        return f'<Tenant {self.id}: {self.name}>'
