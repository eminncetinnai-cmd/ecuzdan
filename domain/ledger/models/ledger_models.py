from datetime import datetime, timezone
from shared.db import db
from sqlalchemy import Numeric, Index

def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Account(db.Model):
    """
    Hesap Planı (Chart of Accounts)
    Her kullanıcının kendi hesapları vardır. (Nakit, Kredi Kartı, Market Gideri, Maaş Geliri)
    """
    __tablename__ = 'account'
    __table_args__ = (
        Index('idx_account_tenant', 'tenant_id'),
        Index('idx_account_type', 'type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False) # 'Asset', 'Liability', 'Equity', 'Revenue', 'Expense'
    currency = db.Column(db.String(3), default='TRY', nullable=False)
    
    # Hierarchical chart of accounts
    parent_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    parent = db.relationship('Account', remote_side=[id], backref='children')
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow_naive)

    tenant = db.relationship('Tenant', backref='accounts')

    def __repr__(self):
        return f"<Account {self.id} {self.type}: {self.name}>"

class JournalEntry(db.Model):
    """
    Yevmiye Fişi (Header)
    Bir işlemin metadata'sını ve şifreleme zincirini tutar.
    """
    __tablename__ = 'journal_entry'
    __table_args__ = (
        Index('idx_je_tenant', 'tenant_id'),
        Index('idx_je_date', 'date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD
    description = db.Column(db.String(200), nullable=True)
    
    # Hashing for Immutable Ledger
    hash = db.Column(db.String(64), nullable=False, unique=True)
    previous_hash = db.Column(db.String(64), nullable=True) # None for the genesis block

    created_at = db.Column(db.DateTime, default=utcnow_naive)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Status (e.g. 'Posted', 'Reversed')
    status = db.Column(db.String(20), default='Posted', nullable=False)
    
    tenant = db.relationship('Tenant', backref='journal_entries')

    def __repr__(self):
        return f"<JournalEntry {self.id} on {self.date}>"

class LedgerLine(db.Model):
    """
    Defter Satırı (Lines)
    Bir yevmiye fişindeki borç/alacak kaydı.
    """
    __tablename__ = 'ledger_line'
    __table_args__ = (
        Index('idx_ll_journal', 'journal_entry_id'),
        Index('idx_ll_account', 'account_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entry.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    
    # Financial Fields
    debit = db.Column(Numeric(19, 4), default=0.0000, nullable=False)
    credit = db.Column(Numeric(19, 4), default=0.0000, nullable=False)
    currency = db.Column(db.String(3), default='TRY', nullable=False)

    journal_entry = db.relationship('JournalEntry', backref='lines')
    account = db.relationship('Account', backref='ledger_lines')

    def __repr__(self):
        return f"<LedgerLine {self.id} Account:{self.account_id} D:{self.debit} C:{self.credit}>"
