from datetime import datetime, timezone

from sqlalchemy import JSON

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BackupMetadata(db.Model):
    """Yedek meta verisi

    Phase 17: Backup versioning and metadata tracking
    """
    __tablename__ = 'backup_metadata'
    __table_args__ = (
        db.Index('idx_backup_metadata_tenant', 'tenant_id'),
        db.Index('idx_backup_metadata_user', 'user_id'),
        db.Index('idx_backup_metadata_timestamp', 'backup_timestamp'),
    )

    id = db.Column(db.Integer, primary_key=True)
    schema_version = db.Column(db.String(20), nullable=False)  # "v16.0"
    backup_timestamp = db.Column(db.DateTime, nullable=False)
    checksum = db.Column(db.String(64), nullable=False)  # SHA-256
    encrypted = db.Column(db.Boolean, default=False, nullable=False)
    compression = db.Column(db.String(20), nullable=True)  # 'gzip', 'zstd', 'lz4', None
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    record_counts = db.Column(db.JSON, nullable=True)  # {"users": 2, "transactions": 89, ...}
    backup_type = db.Column(db.String(20), default='full', nullable=False)  # 'full', 'incremental'
    status = db.Column(db.String(20), default='completed', nullable=False)  # 'completed', 'failed', 'in_progress'
    file_path = db.Column(db.String(500), nullable=True)  # Local storage path
    cloud_storage_key = db.Column(db.String(500), nullable=True)  # Cloud storage key
    notes = db.Column(db.String(500), nullable=True)

    tenant = db.relationship('Tenant', backref='backup_metadata')
    user = db.relationship('User', backref='backup_metadata')


class AuditLog(db.Model):
    """
    Güvenlik ve uyumluluk için append-only denetim kaydı.

    Uygulama kodu bu tabloyu yalnızca INSERT edebilir; UPDATE/DELETE yasak.
    Sorgulanabilir audit trail: LOGIN, LOGOUT, REGISTER, DATA_EXPORT,
    RESET_DATA, ROLE_CHANGED, USER_DELETED, INVITE_CREATED, TENANT_CREATED
    """
    __tablename__ = 'audit_log'
    __table_args__ = (
        db.Index('idx_audit_log_tenant',    'tenant_id'),
        db.Index('idx_audit_log_user',      'user_id'),
        db.Index('idx_audit_log_action',    'action'),
        db.Index('idx_audit_log_timestamp', 'timestamp'),
    )

    id          = db.Column(db.Integer,     primary_key=True)
    # Kim yaptı
    tenant_id   = db.Column(db.String(50),  db.ForeignKey('tenant.id'), nullable=True,  index=True)
    user_id     = db.Column(db.Integer,     db.ForeignKey('user.id'),   nullable=True,  index=True)
    username    = db.Column(db.String(100), nullable=True)   # Snapshot — kullanıcı silinse de kalır
    # Ne yaptı
    action      = db.Column(db.String(50),  nullable=False)  # LOGIN, LOGOUT, REGISTER …
    entity_type = db.Column(db.String(50),  nullable=True)   # 'user', 'transaction', 'tenant' …
    entity_id   = db.Column(db.String(50),  nullable=True)   # İlgili kaydın ID'si
    details     = db.Column(db.Text,        nullable=True)   # JSON ek bilgi
    # Nereden yaptı
    ip_address  = db.Column(db.String(45),  nullable=True)   # IPv4 veya IPv6
    user_agent  = db.Column(db.String(300), nullable=True)
    # Zaman
    timestamp   = db.Column(db.DateTime,    nullable=False, default=utcnow_naive, index=True)

    tenant = db.relationship('Tenant', backref='audit_logs')
    user   = db.relationship('User',   backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.username} @ {self.timestamp}>'


class MonitoringAlertConfig(db.Model):
    """Monitoring alert configuration model"""
    __tablename__ = 'monitoring_alert_config'
    __table_args__ = (
        db.Index('idx_alert_config_user', 'user_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True, index=True)

    # Email alert settings
    email_alerts_enabled = db.Column(db.Boolean, default=False, nullable=False)
    smtp_server = db.Column(db.String(255), nullable=True)
    smtp_port = db.Column(db.Integer, nullable=True)
    smtp_username = db.Column(db.String(255), nullable=True)
    smtp_password = db.Column(db.String(255), nullable=True)
    from_email = db.Column(db.String(255), nullable=True)
    to_emails = db.Column(JSON, nullable=True)  # List of email addresses

    # Alert thresholds
    alert_thresholds = db.Column(JSON, nullable=True)  # JSON object with thresholds

    # Timestamps
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive, nullable=False)

    user = db.relationship('User', backref='alert_configs')
    tenant = db.relationship('Tenant', backref='alert_configs')

    def __repr__(self):
        return f'<MonitoringAlertConfig user_id={self.user_id} email_enabled={self.email_alerts_enabled}>'
