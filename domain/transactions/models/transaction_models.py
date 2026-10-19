import sys
from datetime import datetime, timezone

from sqlalchemy import JSON, Numeric

from domain.transactions.constants import (
    LEDGER_LAYER_CASH_EVENT,
    SOURCE_TYPE_ADJUSTMENT,
    SOURCE_TYPE_ASSET,
    SOURCE_TYPE_ASSET_SALE,
    SOURCE_TYPE_MANUAL,
    SOURCE_TYPE_PLAN,
    SOURCE_TYPE_REVERSAL,
)
from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Transaction(db.Model):
    """
    Tüm nakit hareketleri (tek tablo).
    - Tek seferlik: source_type boş
    - Planlı: source_type='plan', source_id=RecurringPlan.id
    """
    __tablename__ = 'transaction'
    __table_args__ = (
        db.Index('idx_transaction_date', 'date'),
        db.Index('idx_transaction_type', 'type'),
        db.Index('idx_transaction_status', 'status'),
        db.Index('idx_transaction_type_status', 'type', 'status'),
        db.Index('idx_transaction_date_type', 'date', 'type'),
        db.Index('idx_transaction_tenant_id', 'tenant_id'),
        db.Index('idx_transaction_category', 'category'),
        db.Index('idx_transaction_is_deleted', 'is_deleted'),
        db.Index('idx_transaction_tenant_date', 'tenant_id', 'date'),
        db.Index('idx_transaction_tenant_del_date', 'tenant_id', 'is_deleted', 'date'),
        db.Index('idx_transaction_tenant_status_date', 'tenant_id', 'is_deleted', 'status', 'date'),
        db.Index('idx_transaction_tenant_status_type', 'tenant_id', 'is_deleted', 'status', 'type'),
        db.Index('idx_transaction_tenant_category', 'tenant_id', 'is_deleted', 'category'),
        db.Index('idx_transaction_tenant_source', 'tenant_id', 'source_type', 'source_id'),
        db.UniqueConstraint('tenant_id', 'date', 'category', 'description', 'amount', name='uq_transaction_dedup'),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100))
    note = db.Column(db.String(200))
    is_admin_generated = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(10), nullable=False)  # 'Gelir', 'Gider', 'Yatırım', 'Transfer'
    status = db.Column(db.String(20), nullable=False)  # 'Ödendi', 'Bekliyor'
    amount = db.Column(Numeric(19, 4), nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    __mapper_args__ = {
        'version_id_col': version,
    }
    idempotency_key = db.Column(db.String(64), nullable=True)
    installment_number = db.Column(db.Integer, nullable=True)
    source_id = db.Column(db.Integer)
    source_type = db.Column(db.String(20))
    # Nullable for backward compatibility: legacy transactions are not
    # silently assigned to a bank account.
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=True, index=True)

    # Transfer-specific fields (for Phase 2: Cash Flow vs Net Worth separation)
    transfer_from = db.Column(db.String(50), nullable=True)  # Source account for transfers
    transfer_to = db.Column(db.String(50), nullable=True)    # Destination account for transfers
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    tenant = db.relationship('Tenant', backref='transactions')
    bank_account = db.relationship('BankAccount', backref='transactions')

    # Soft delete fields
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    @property
    def origin(self):
        if self.source_type == SOURCE_TYPE_PLAN:
            return 'Planlı'
        if self.source_type == SOURCE_TYPE_ASSET:
            if not self.source_id:
                return 'Varlık Alımı'
            asset_type = None
            try:
                flask_mod = sys.modules.get('flask')
                if flask_mod and getattr(flask_mod, 'has_request_context', lambda: False)():
                    g = getattr(flask_mod, 'g')
                    cache = getattr(g, '_asset_type_cache', None)
                    if cache is None:
                        cache = {}
                        g._asset_type_cache = cache
                    cache_key = (self.tenant_id, self.source_id)
                    if cache_key in cache:
                        asset_type = cache[cache_key]
                    else:
                        from domain.portfolio.models.portfolio_models import Asset
                        asset = db.session.get(Asset, self.source_id)
                        if asset and asset.tenant_id == self.tenant_id:
                            asset_type = asset.type
                        cache[cache_key] = asset_type
                else:
                    from domain.portfolio.models.portfolio_models import Asset
                    asset = db.session.get(Asset, self.source_id)
                    if asset and asset.tenant_id == self.tenant_id:
                        asset_type = asset.type
            except Exception:
                from domain.portfolio.models.portfolio_models import Asset
                asset = db.session.get(Asset, self.source_id)
                if asset and asset.tenant_id == self.tenant_id:
                    asset_type = asset.type
            if asset_type:
                return f'{asset_type} Alımı'
            return 'Varlık Alımı'
        if self.source_type == SOURCE_TYPE_ASSET_SALE:
            return 'Varlık Satışı'
        if self.source_type == SOURCE_TYPE_MANUAL:
            return 'Manuel'
        if self.source_type == SOURCE_TYPE_ADJUSTMENT:
            return 'Düzeltme'
        if self.source_type == SOURCE_TYPE_REVERSAL:
            return 'Ters kayıt'
        return 'Tek seferlik'

    @property
    def ledger_layer(self):
        """Pozisyon/Olay ayrımı: işlemler nakit olay katmanıdır."""
        return LEDGER_LAYER_CASH_EVENT


class RecurringPlan(db.Model):
    """Düzenli gelir/gider şablonu (pozisyon katmanı); her ay için Transaction üretir."""
    __tablename__ = 'recurring_plan'
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    __mapper_args__ = {
        'version_id_col': version,
    }
    __table_args__ = (
        db.Index('idx_recurring_plan_flow_type', 'flow_type'),
        db.Index('idx_recurring_plan_name', 'name'),
        db.Index('idx_recurring_plan_tenant_id', 'tenant_id'),
        db.Index('idx_recurring_plan_status', 'status'),
        db.Index('idx_recurring_plan_plan_type', 'plan_type'),
        db.Index('idx_recurring_plan_tenant_status', 'tenant_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    flow_type = db.Column(db.String(10), nullable=False)  # 'Gelir' veya 'Gider'
    amount = db.Column(Numeric(19, 4), nullable=False)
    installments = db.Column(db.Integer, nullable=False)
    payment_day = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD formatında başlangıç tarihi
    note = db.Column(db.String(200))
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    tenant = db.relationship('Tenant', backref='recurring_plans')
    is_admin_generated = db.Column(db.Boolean, default=False, nullable=False)  # Demo data flag

    # Faz 1: Yeni Plan Tipleri ve Genişletmeler
    plan_type = db.Column(db.String(20), default='Taksit', nullable=False)  # Taksit, Abonelik, DCA, Kira
    end_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD
    frequency = db.Column(db.String(20), default='Aylık', nullable=False)  # Aylık, Yıllık vs.
    status = db.Column(db.String(20), default='Aktif', nullable=False)  # Aktif, Tamamlandı, İptal
    target_asset_id = db.Column(db.Integer, db.ForeignKey('asset.id', use_alter=True), nullable=True)  # DCA için hedef varlık
    target_asset = db.relationship('Asset', foreign_keys=[target_asset_id], backref='dca_plans')

    @property
    def ledger_layer(self):
        return 'nakit_pozisyon'

    @property
    def origin(self):
        return 'Planlı'

    @property
    def months_remaining(self):
        from domain.planning.models.plan_contracts import CanonicalPlan
        try:
            return CanonicalPlan.from_model(self).months_remaining
        except Exception:
            return None

    @property
    def remaining_total_amount(self):
        from domain.planning.models.plan_contracts import CanonicalPlan
        try:
            return CanonicalPlan.from_model(self).remaining_total_amount
        except Exception:
            return None

    @property
    def payment_countdown(self):
        from domain.planning.models.plan_contracts import CanonicalPlan
        try:
            return CanonicalPlan.from_model(self).payment_countdown
        except Exception:
            return None

    @property
    def is_completed(self):
        from domain.planning.models.plan_contracts import CanonicalPlan
        try:
            return CanonicalPlan.from_model(self).is_completed
        except Exception:
            return self.status == 'Tamamlandı'


class Payment(db.Model):
    """
    Ödeme takibi - RecurringPlan için ödenmiş taksitleri kaydeder
    Borç hesaplaması için kritik: ödenmiş taksitler toplam borçtan düşülür
    """
    __tablename__ = 'payment'
    __table_args__ = (
        db.Index('idx_payment_plan_id', 'plan_id'),
        db.Index('idx_payment_date', 'payment_date'),
        db.Index('idx_payment_tenant_id', 'tenant_id'),
        db.Index('idx_payment_transaction_id', 'transaction_id'),
        db.Index('idx_payment_tenant_date', 'tenant_id', 'payment_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('recurring_plan.id'), nullable=False)
    amount = db.Column(Numeric(19, 4), nullable=False)  # Ödenen tutar
    payment_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD formatında ödeme tarihi
    installment_number = db.Column(db.Integer, nullable=False)  # Kaçıncı taksit
    notes = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    plan = db.relationship('RecurringPlan', backref=db.backref('payments', cascade='all, delete-orphan'))
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    transaction = db.relationship('Transaction', backref='payments', lazy='joined')
    tenant = db.relationship('Tenant', backref='payments')


class PlanOccurrence(db.Model):
    """Bir planın beklenen tek bir dönemini ve yaşam döngüsünü temsil eder.

    ``Payment`` geriye dönük uyumluluk için korunur; bu tablo plan takvimini,
    ödeme durumunu ve işlem bağlantısını ayrı bir aggregate olarak tutar.
    Durum değerleri API/DB sözleşmesinde İngilizce ve sabittir: scheduled,
    paid, skipped veya cancelled.
    """

    __tablename__ = 'plan_occurrence'
    __table_args__ = (
        db.UniqueConstraint(
            'plan_id',
            'occurrence_number',
            name='uq_plan_occurrence_plan_num',
        ),
        db.CheckConstraint(
            "status IN ('scheduled', 'paid', 'skipped', 'cancelled')",
            name='ck_plan_occurrence_status',
        ),
        db.Index('idx_plan_occurrence_plan_id', 'plan_id'),
        db.Index('idx_plan_occurrence_tenant_id', 'tenant_id'),
        db.Index('idx_plan_occurrence_status', 'status'),
        db.Index('idx_plan_occurrence_scheduled_date', 'scheduled_date'),
        db.Index(
            'idx_plan_occurrence_tenant_status_date',
            'tenant_id',
            'status',
            'scheduled_date',
        ),
    )

    STATUSES = frozenset({'scheduled', 'paid', 'skipped', 'cancelled'})

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey('recurring_plan.id'),
        nullable=False,
    )
    occurrence_number = db.Column(db.Integer, nullable=False)  # 1-based
    scheduled_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    status = db.Column(db.String(20), default='scheduled', nullable=False)
    amount = db.Column(Numeric(19, 4), nullable=True)
    transaction_id = db.Column(
        db.Integer,
        db.ForeignKey('transaction.id'),
        nullable=True,
    )
    paid_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(200), nullable=True)
    tenant_id = db.Column(
        db.String(50),
        db.ForeignKey('tenant.id'),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=False,
    )

    plan = db.relationship('RecurringPlan', backref=db.backref('occurrences', cascade='all, delete-orphan'))
    transaction = db.relationship(
        'Transaction',
        backref='plan_occurrences',
        lazy='joined',
    )
    tenant = db.relationship('Tenant', backref='plan_occurrences')


class LedgerAdjustment(db.Model):
    """Paid transaction için adjustment/reversal iş ve denetim kaydı."""

    __tablename__ = 'ledger_adjustment'
    __table_args__ = (
        db.UniqueConstraint(
            'tenant_id',
            'idempotency_key',
            name='uq_ledger_adjustment_tenant_idempotency',
        ),
        db.CheckConstraint(
            "kind IN ('adjustment', 'reversal')",
            name='ck_ledger_adjustment_kind',
        ),
        db.CheckConstraint(
            "status IN ('requested', 'applied', 'failed', 'voided')",
            name='ck_ledger_adjustment_status',
        ),
        db.CheckConstraint(
            'amount_delta <> 0',
            name='ck_ledger_adjustment_nonzero_delta',
        ),
        db.CheckConstraint(
            "kind != 'reversal' OR amount_delta = -original_amount_snapshot",
            name='ck_ledger_adjustment_reversal_delta',
        ),
        db.Index(
            'idx_ledger_adjustment_original',
            'tenant_id',
            'original_transaction_id',
            'created_at',
        ),
        db.Index(
            'idx_ledger_adjustment_status',
            'tenant_id',
            'status',
            'created_at',
        ),
        db.Index(
            'idx_ledger_adjustment_correlation',
            'tenant_id',
            'correlation_id',
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(
        db.String(50),
        db.ForeignKey('tenant.id', ondelete='RESTRICT'),
        nullable=False,
    )
    original_transaction_id = db.Column(
        db.Integer,
        db.ForeignKey('transaction.id', ondelete='RESTRICT'),
        nullable=False,
    )
    compensating_transaction_id = db.Column(
        db.Integer,
        db.ForeignKey('transaction.id', ondelete='RESTRICT'),
        nullable=True,
        unique=True,
    )
    kind = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='requested', nullable=False)
    amount_delta = db.Column(Numeric(19, 4), nullable=False)
    original_amount_snapshot = db.Column(Numeric(19, 4), nullable=False)
    original_type_snapshot = db.Column(db.String(10), nullable=False)
    original_category_snapshot = db.Column(db.String(50), nullable=False)
    original_date_snapshot = db.Column(db.String(10), nullable=False)
    original_version = db.Column(db.Integer, nullable=False)
    reason_code = db.Column(db.String(50), nullable=False)
    reason_text = db.Column(db.String(1000), nullable=False)
    requested_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='RESTRICT'),
        nullable=True,
    )
    approved_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='RESTRICT'),
        nullable=True,
    )
    requested_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    applied_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    failure_code = db.Column(db.String(50), nullable=True)
    failure_message = db.Column(db.String(1000), nullable=True)
    idempotency_key = db.Column(db.String(64), nullable=False)
    correlation_id = db.Column(db.String(64), nullable=False)
    metadata_json = db.Column('metadata', JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=False,
    )

    tenant = db.relationship('Tenant', backref='ledger_adjustments')
    original_transaction = db.relationship(
        'Transaction',
        foreign_keys=[original_transaction_id],
        backref='ledger_adjustments_as_original',
    )
    compensating_transaction = db.relationship(
        'Transaction',
        foreign_keys=[compensating_transaction_id],
        backref='ledger_adjustment_result',
    )
    requested_user = db.relationship(
        'User',
        foreign_keys=[requested_by],
        backref='requested_ledger_adjustments',
    )
    approved_user = db.relationship(
        'User',
        foreign_keys=[approved_by],
        backref='approved_ledger_adjustments',
    )


class LedgerAuditEvent(db.Model):
    """Append-only adjustment/reversal audit olayı."""

    __tablename__ = 'ledger_audit_event'
    __table_args__ = (
        db.Index(
            'idx_ledger_audit_event_adjustment',
            'tenant_id',
            'adjustment_id',
            'occurred_at',
        ),
        db.Index(
            'idx_ledger_audit_event_transaction',
            'tenant_id',
            'transaction_id',
            'occurred_at',
        ),
        db.Index(
            'idx_ledger_audit_event_correlation',
            'tenant_id',
            'correlation_id',
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(
        db.String(50),
        db.ForeignKey('tenant.id', ondelete='RESTRICT'),
        nullable=False,
    )
    adjustment_id = db.Column(
        db.Integer,
        db.ForeignKey('ledger_adjustment.id', ondelete='RESTRICT'),
        nullable=True,
    )
    transaction_id = db.Column(
        db.Integer,
        db.ForeignKey('transaction.id', ondelete='RESTRICT'),
        nullable=True,
    )
    event_type = db.Column(db.String(50), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='RESTRICT'),
        nullable=True,
    )
    correlation_id = db.Column(db.String(64), nullable=False)
    request_id = db.Column(db.String(64), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    payload = db.Column(JSON, nullable=True)
    occurred_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    previous_hash = db.Column(db.String(64), nullable=True)
    event_hash = db.Column(db.String(64), nullable=True)

    tenant = db.relationship('Tenant', backref='ledger_audit_events')
    adjustment = db.relationship(
        'LedgerAdjustment',
        backref='audit_events',
    )
    transaction = db.relationship(
        'Transaction',
        backref='ledger_audit_events',
    )
    actor_user = db.relationship('User', backref='ledger_audit_events')


class LogbookEntry(db.Model):
    """Finansal Seyir Defteri - Kullanıcı finansal karar ve notları"""
    __tablename__ = 'logbook_entry'
    __table_args__ = (
        db.Index('idx_logbook_entry_date', 'entry_date'),
        db.Index('idx_logbook_entry_category', 'category'),
        db.Index('idx_logbook_entry_tenant_id', 'tenant_id'),
        db.Index('idx_logbook_entry_date_tenant', 'entry_date', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Temel alanlar
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    entry_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD formatında

    # Kategorizasyon
    category = db.Column(db.String(50), nullable=False, default='Finansal')  # 'Finansal', 'Yatırım', 'Ödeme', 'Kilometre Taşı', 'Fikir'
    sentiment = db.Column(db.String(20), nullable=False, default='Nötr')  # 'Boğa', 'Ayı', 'Nötr'

    # İlişkilendirme (opsiyonel)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)

    # Durum yönetimi
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    # Zaman damgaları
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive, nullable=False)

    # İlişkiler
    tenant = db.relationship('Tenant', backref='logbook_entries')
    user = db.relationship('User', backref='logbook_entries')
    asset = db.relationship('Asset', backref='logbook_entries', lazy='joined')
    transaction = db.relationship('Transaction', backref='logbook_entries', lazy='joined')

    @property
    def category_emoji(self):
        """Kategori için emoji"""
        emojis = {
            'Finansal': '💰',
            'Yatırım': '📈',
            'Ödeme': '💳',
            'Kilometre Taşı': '🎯',
            'Fikir': '💡'
        }
        return emojis.get(self.category, '📝')

    @property
    def sentiment_emoji(self):
        """Sentiment için emoji"""
        emojis = {
            'Boğa': '🐂',
            'Ayı': '🐻',
            'Nötr': '😐'
        }
        return emojis.get(self.sentiment, '😐')

    @property
    def content_preview(self):
        """İçerik önizlemesi (100 karakter)"""
        if len(self.content) > 100:
            return self.content[:97] + '...'
        return self.content
