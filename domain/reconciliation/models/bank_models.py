from datetime import datetime, timezone

from sqlalchemy import Numeric

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BankAccount(db.Model):
    """Kullanıcının banka/nakit hesabı; muhasebe hesap planından ayrıdır."""
    __tablename__ = 'bank_account'
    __table_args__ = (
        db.Index('idx_bank_account_tenant_active', 'tenant_id', 'is_active'),
        db.Index('idx_bank_account_tenant_currency', 'tenant_id', 'currency'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(100), nullable=True)
    account_type = db.Column(db.String(20), default='checking', nullable=False)
    currency = db.Column(db.String(3), default='TRY', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)

    tenant = db.relationship('Tenant', backref='bank_accounts')
    creator = db.relationship('User', backref='created_bank_accounts')

    def __repr__(self):
        return f'<BankAccount {self.id}: {self.name} {self.currency}>'


class BankStatementSnapshot(db.Model):
    """Kullanıcının belirli tarihte girdiği banka ekstresi kapanış bakiyesi."""
    __tablename__ = 'bank_statement_snapshot'
    __table_args__ = (
        db.UniqueConstraint(
            'bank_account_id', 'as_of', 'currency',
            name='uq_bank_statement_snapshot_account_asof_currency',
        ),
        db.Index('idx_bank_statement_tenant_asof', 'tenant_id', 'as_of'),
        db.Index('idx_bank_statement_account_asof', 'bank_account_id', 'as_of'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=False, index=True)
    as_of = db.Column(db.String(10), nullable=False)
    balance = db.Column(Numeric(19, 4), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    source = db.Column(db.String(20), default='manual', nullable=False)
    note = db.Column(db.String(300), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)

    tenant = db.relationship('Tenant', backref='bank_statement_snapshots')
    bank_account = db.relationship('BankAccount', backref='statement_snapshots')
    creator = db.relationship('User', backref='created_bank_statement_snapshots')
