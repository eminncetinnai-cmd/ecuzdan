import os
from datetime import datetime, timezone

from shared.db import db
from sqlalchemy import Numeric, JSON


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

class User(db.Model):
    """Kullanıcı modeli"""
    ADMIN_ROLES = frozenset({'sistem_yoneticisi', 'yonetici'})
    #: Platform sahibinin kullanıcı adı. config.Config.SUPER_ADMIN_USERNAME ile
    #: aynı ortam değişkenini okur; models.py config'i import etmez (erken
    #: yükleme sırası / döngü riski), bu yüzden değer doğrudan ortamdan alınır.
    SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'emin')
    __table_args__ = (
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_auth_provider', 'auth_provider'),
        db.Index('idx_user_last_login', 'last_login_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)  # Nullable for OAuth users
    
    # OAuth / Provider fields
    auth_provider = db.Column(db.String(20), default='LOCAL', nullable=False)
    oauth_id = db.Column(db.String(100), nullable=True, unique=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_via = db.Column(db.String(50), default='web', nullable=False)

    password_changed_at = db.Column(db.DateTime, nullable=True)
    last_session_id = db.Column(db.String(64), nullable=True)
    role = db.Column(db.String(20), default='kullanici', nullable=False)  # 'sistem_yoneticisi', 'yonetici', 'tenant_admin', 'kullanici'
    profile_image = db.Column(db.String(200), nullable=True)  # Profil resmi dosya yolu veya URL'si
    language = db.Column(db.String(5), default='tr', nullable=False)
    base_currency = db.Column(db.String(3), nullable=True)  # Phase 5: User-specific base currency override
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    tenant = db.relationship('Tenant', backref='users')

    @property
    def is_super_admin(self):
        """Süper yönetici: emin kullanıcısı."""
        return self.username == self.SUPER_ADMIN_USERNAME

    @property
    def has_admin_access(self):
        """Yönetici paneli ve admin işlemlerine tam erişim."""
        return self.is_super_admin or self.role in self.ADMIN_ROLES

    @property
    def is_tenant_admin(self):
        """Tenant admin mi"""
        return self.role == 'tenant_admin'

    @property
    def role_labels(self):
        """Arayüzde gösterilecek rol etiketleri."""
        if self.is_super_admin:
            return ['Tam Yetki', 'Sistem Yöneticisi', 'Yönetici']
        if self.role == 'sistem_yoneticisi':
            return ['Sistem Yöneticisi']
        if self.role == 'yonetici':
            return ['Yönetici']
        if self.role == 'tenant_admin':
            return ['Tenant Admin']
        return ['Kullanıcı']


from domain.portfolio.models import Asset


class CategoryAssetTypeMapping(db.Model):
    """Kategori ve varlık tipi arasındaki ilişki

    Phase 16: Category-AssetType mapping for automatic categorization
    """
    __tablename__ = 'category_asset_type_mapping'
    __table_args__ = (
        db.Index('idx_cat_asset_type_category', 'category_id'),
        db.Index('idx_cat_asset_type_asset_type', 'asset_type_id'),
        db.UniqueConstraint('category_id', 'asset_type_id', name='uq_category_asset_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    asset_type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)  # Varsayılan eşleşme
    weight = db.Column(Numeric(19, 4), default=1.0, nullable=False)  # Ağırlık katsayısı
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True, index=True)

    category = db.relationship('Category', backref='asset_type_mappings')
    asset_type = db.relationship('AssetType', backref='category_mappings')
    tenant = db.relationship('Tenant', backref='category_asset_type_mappings')

class Tag(db.Model):
    """Esnek etiketleme sistemi

    Phase 16: Tag system for flexible categorization
    """
    __tablename__ = 'tag'
    __table_args__ = (
        db.Index('idx_tag_name', 'name'),
        db.Index('idx_tag_type', 'type'),
        db.Index('idx_tag_tenant', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=True)  # 'category', 'asset', 'transaction', 'recurring_plan'
    color = db.Column(db.String(7), nullable=True)  # UI rengi #RRGGBB
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    tenant = db.relationship('Tenant', backref='tags')

class EntityTag(db.Model):
    """Varlık etiket ilişkileri

    Phase 16: Entity-Tag relationship for flexible tagging
    """
    __tablename__ = 'entity_tag'
    __table_args__ = (
        db.Index('idx_entity_tag_entity', 'entity_type', 'entity_id'),
        db.Index('idx_entity_tag_tag', 'tag_id'),
        db.UniqueConstraint('entity_type', 'entity_id', 'tag_id', name='uq_entity_tag'),
    )

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20), nullable=False)  # 'category', 'asset', 'transaction', 'recurring_plan'
    entity_id = db.Column(db.Integer, nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)

    tag = db.relationship('Tag', backref='entities')

class UserProgress(db.Model):
    """Kullanıcı eğitim ilerleme takibi

    Phase 17: Financial Education Progress Tracking
    """
    __tablename__ = 'user_progress'
    __table_args__ = (
        db.Index('idx_user_progress_user', 'user_id'),
        db.Index('idx_user_progress_topic', 'topic'),
        db.Index('idx_user_progress_tenant', 'tenant_id'),
        db.UniqueConstraint('user_id', 'topic', name='uq_user_progress_topic'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False)  # Topic identifier (e.g., 'income_expenses')
    phase = db.Column(db.String(50), nullable=False)  # Phase identifier (e.g., 'beginner')
    completed = db.Column(db.Boolean, default=False, nullable=False)
    progress_percent = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    last_accessed_at = db.Column(db.DateTime, default=utcnow_naive)
    completed_at = db.Column(db.DateTime, nullable=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    user = db.relationship('User', backref='progress_records')
    tenant = db.relationship('Tenant', backref='user_progress')

class QuizAttempt(db.Model):
    """Quiz deneme kayıtları

    Phase 17: Financial Education Quiz System
    """
    __tablename__ = 'quiz_attempt'
    __table_args__ = (
        db.Index('idx_quiz_attempt_user', 'user_id'),
        db.Index('idx_quiz_attempt_difficulty', 'difficulty'),
        db.Index('idx_quiz_attempt_tenant', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    score = db.Column(db.Integer, nullable=False)  # 0-100
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=utcnow_naive)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    user = db.relationship('User', backref='quiz_attempts')
    tenant = db.relationship('Tenant', backref='quiz_attempts')

class UserAchievement(db.Model):
    """Kullanıcı başarıları ve rozetleri

    Phase 17: Gamification System
    """
    __tablename__ = 'user_achievement'
    __table_args__ = (
        db.Index('idx_user_achievement_user', 'user_id'),
        db.Index('idx_user_achievement_type', 'achievement_type'),
        db.Index('idx_user_achievement_tenant', 'tenant_id'),
        db.UniqueConstraint('user_id', 'achievement_type', name='uq_user_achievement'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    achievement_type = db.Column(db.String(50), nullable=False)  # 'first_steps', 'quiz_master', 'week_streak', 'graduate'
    earned_at = db.Column(db.DateTime, default=utcnow_naive)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    user = db.relationship('User', backref='achievements')
    tenant = db.relationship('Tenant', backref='user_achievements')

class QuizQuestion(db.Model):
    """Quiz soruları

    Phase 17: Financial Education Quiz System
    """
    __tablename__ = 'quiz_question'
    __table_args__ = (
        db.Index('idx_quiz_question_difficulty', 'difficulty'),
        db.Index('idx_quiz_question_topic', 'topic'),
        db.Index('idx_quiz_question_tenant', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"}
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    explanation = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    topic = db.Column(db.String(100), nullable=False)  # 'income_expenses', 'compound_interest', etc.
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    tenant = db.relationship('Tenant', backref='quiz_questions')

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
    installment_number = db.Column(db.Integer, nullable=True)
    source_id = db.Column(db.Integer)
    source_type = db.Column(db.String(20))

    # Transfer-specific fields (for Phase 2: Cash Flow vs Net Worth separation)
    transfer_from = db.Column(db.String(50), nullable=True)  # Source account for transfers
    transfer_to = db.Column(db.String(50), nullable=True)    # Destination account for transfers
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    tenant = db.relationship('Tenant', backref='transactions')

    # Soft delete fields
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    @property
    def origin(self):
        if self.source_type == 'plan':
            return 'Planlı'
        if self.source_type == 'asset':
            asset = db.session.get(Asset, self.source_id) if self.source_id else None
            if asset and asset.tenant_id == self.tenant_id and asset.type:
                return f'{asset.type} Alımı'
            return 'Varlık Alımı'
        if self.source_type == 'asset_sale':
            return 'Varlık Satışı'
        if self.source_type == 'manual':
            return 'Manuel'
        return 'Tek seferlik'

    @property
    def ledger_layer(self):
        """Pozisyon/Olay ayrımı: işlemler nakit olay katmanıdır."""
        return 'nakit_olay'

class RecurringPlan(db.Model):
    """Düzenli gelir/gider şablonu (pozisyon katmanı); her ay için Transaction üretir."""
    __tablename__ = 'recurring_plan'
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

    plan = db.relationship('RecurringPlan', backref='payments')
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    transaction = db.relationship('Transaction', backref='payments', lazy='joined')
    tenant = db.relationship('Tenant', backref='payments')

class StrategySettings(db.Model):
    """Strateji Planı için dinamik ayarlar"""
    __tablename__ = 'strategy_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)

    # Monte Carlo Parametreleri
    mc_expected_return = db.Column(Numeric(19, 4), default=0.15)  # %15 beklenen yıllık getiri
    mc_volatility = db.Column(Numeric(19, 4), default=0.20)  # %20 yıllık volatilite
    mc_years = db.Column(db.Integer, default=30)  # 30 yıl simülasyon
    mc_simulations = db.Column(db.Integer, default=10000)  # 10.000 simülasyon
    mc_scenario = db.Column(db.String(20), default='balanced')  # 'conservative', 'balanced', 'aggressive'

    # Enflasyon Ayarları
    annual_inflation = db.Column(Numeric(19, 4), default=0.40)  # %40 yıllık enflasyon (Türkiye)
    inflation_source = db.Column(db.String(50), default='manual')  # 'manual', 'api', 'fixed'

    # Anomali Tespiti Ayarları
    anomaly_sigma_threshold = db.Column(Numeric(19, 4), default=2.0)  # 2 sigma = %95 güven
    anomaly_min_samples = db.Column(db.Integer, default=3)  # Minimum 3 veri noktası

    # Kova Stratejisi Ayarları
    bucket_emergency_pct = db.Column(Numeric(19, 4), default=0.20)  # %20 acil durum
    bucket_short_term_pct = db.Column(Numeric(19, 4), default=0.30)  # %30 kısa/orta vadeli
    bucket_long_term_pct = db.Column(Numeric(19, 4), default=0.50)  # %50 uzun vadeli

    created_at = db.Column(db.DateTime, default=utcnow_naive)
    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive)

    user = db.relationship('User', backref='strategy_settings')


class UserPreference(db.Model):
    """Kullanıcıya özel finansal hedefler ve analiz varsayımları (Faz 18).

    Bu değerler daha önce engines/*.py içinde sabit olarak gömülüydü.
    Kayıt yoksa motorlar kendi varsayılanlarına düşer; bu yüzden tüm
    alanlar isteğe bağlıdır ve satır tembel (lazy) oluşturulur.
    """
    __tablename__ = 'user_preference'

    #: Güvenli çekim oranı için kabul edilen alt/üst sınır (Trinity literatürü).
    MIN_SAFE_WITHDRAWAL_RATE = 0.02
    MAX_SAFE_WITHDRAWAL_RATE = 0.10

    #: Desteklenen tema seçenekleri.
    THEMES = ('light', 'dark', 'system')

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)

    # FIRE / emeklilik hedefleri
    birth_year = db.Column(db.Integer, nullable=True)
    target_retirement_age = db.Column(db.Integer, nullable=True)
    target_monthly_passive_income = db.Column(Numeric(18, 2), nullable=True)

    # Analiz varsayımları
    emergency_fund_target_months = db.Column(db.Integer, nullable=True)
    safe_withdrawal_rate = db.Column(Numeric(6, 4), nullable=True)   # 0.0400 = %4
    risk_free_rate_mode = db.Column(db.String(10), default='auto', nullable=False)  # 'auto' | 'manual'
    risk_free_rate_manual = db.Column(Numeric(6, 4), nullable=True)  # 0.5000 = %50

    # Görünüm
    theme = db.Column(db.String(10), default='light', nullable=False)  # 'light' | 'dark' | 'system'
    #: Gizlilik modu — ekrandaki tutarları bulanıklaştırır (halka açık ortam).
    privacy_mode = db.Column(db.Boolean, default=False, nullable=False)

    # Bildirim tercihleri (Faz 21)
    notify_budget = db.Column(db.Boolean, default=True, nullable=False)
    notify_payments = db.Column(db.Boolean, default=True, nullable=False)
    #: Ödeme hatırlatıcısının kaç gün önceden çıkacağı.
    payment_reminder_days = db.Column(db.Integer, default=3, nullable=False)

    updated_at = db.Column(db.DateTime, default=utcnow_naive, onupdate=utcnow_naive)

    user = db.relationship('User', backref=db.backref('preference', uselist=False))

    @property
    def target_retirement_year(self):
        """Doğum yılı ve hedef yaştan hedef bağımsızlık yılı."""
        if self.birth_year and self.target_retirement_age:
            return self.birth_year + self.target_retirement_age
        return None

    def __repr__(self):
        return f'<UserPreference user={self.user_id}>'


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
        db.Index('idx_notification_user_read', 'user_id', 'is_read'),
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
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    def mark_sent(self):
        """Mark notification as sent."""
        from datetime import datetime
        self.sent_at = datetime.utcnow()
        self.delivery_status = 'sent'

    def mark_delivered(self):
        """Mark notification as delivered."""
        from datetime import datetime
        self.delivered_at = datetime.utcnow()
        self.delivery_status = 'delivered'

    def mark_read(self):
        """Mark notification as read."""
        from datetime import datetime
        self.read_at = datetime.utcnow()
        self.is_read = True
        self.delivery_status = 'read'

    def mark_failed(self, reason):
        """Mark notification as failed."""
        from datetime import datetime
        self.failed_at = datetime.utcnow()
        self.failure_reason = reason
        self.delivery_status = 'failed'


class TenantInvite(db.Model):
    """Tenant davet modeli - Kullanıcı davet sistemi için"""
    __tablename__ = 'tenant_invite'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), nullable=False)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='kullanici')  # 'kullanici', 'tenant_admin'
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive)

    tenant = db.relationship('Tenant', backref='invites')
    inviter = db.relationship('User', backref='sent_invites')

    @property
    def is_expired(self):
        """Davet süresi dolmuş mu"""
        return utcnow_naive() > self.expires_at

    @property
    def is_used(self):
        """Davet kullanıldı mı"""
        return self.used_at is not None

    @property
    def is_valid(self):
        """Davet geçerli mi"""
        return not self.is_expired and not self.is_used


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


class InvestorProfile(db.Model):
    """Yatırımcı risk profili - 5 boyutlu analiz sonucu"""
    __tablename__ = 'investor_profile'
    __table_args__ = (
        db.Index('idx_investor_profile_tenant', 'tenant_id'),
        db.Index('idx_investor_profile_user', 'user_id'),
        db.Index('idx_investor_profile_date', 'test_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # 5 Boyutlu Skorlar (0-100)
    literacy_score = db.Column(Numeric(19, 4), nullable=False)      # Finansal Okuryazarlık
    capacity_score = db.Column(Numeric(19, 4), nullable=False)      # Risk Kapasitesi
    tolerance_score = db.Column(Numeric(19, 4), nullable=False)     # Risk Toleransı
    behavioral_score = db.Column(Numeric(19, 4), nullable=False)   # Davranışsal Finans
    experience_score = db.Column(Numeric(19, 4), nullable=False)   # Yatırım Deneyimi

    # Nihai Sonuç
    final_risk_level = db.Column(db.String(50), nullable=False)  # 7 sınıf
    confidence_score = db.Column(Numeric(19, 4), nullable=False)        # Güven skoru
    risk_warnings = db.Column(db.Text, nullable=True)            # JSON uyarılar

    # Meta
    test_date = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    validity_date = db.Column(db.DateTime, nullable=True)         # Profil geçerlilik süresi
    profile_version = db.Column(db.String(20), default='1.0', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # İlişkiler
    tenant = db.relationship('Tenant', backref='investor_profiles')
    user = db.relationship('User', backref='investor_profiles')


class InvestorProfileAnswer(db.Model):
    """Profil testi cevapları - detaylı analiz için"""
    __tablename__ = 'investor_profile_answer'
    __table_args__ = (
        db.Index('idx_answer_profile', 'profile_id'),
        db.Index('idx_answer_question', 'question_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('investor_profile.id'), nullable=False)
    question_id = db.Column(db.String(50), nullable=False)  # Soru ID'si
    dimension = db.Column(db.String(50), nullable=False)     # Boyut (literacy, capacity, vb.)
    answer_value = db.Column(db.Integer, nullable=False)     # Cevap puanı
    answer_text = db.Column(db.String(200), nullable=True)   # Cevap metni
    question_version = db.Column(db.String(20), default='1.0')

    profile = db.relationship('InvestorProfile', backref='answers')


class ProfileQuestion(db.Model):
    """Profil soru bankası - JSON tabanlı yapı"""
    __tablename__ = 'profile_question'
    __table_args__ = (
        db.Index('idx_question_dimension', 'dimension'),
        db.Index('idx_question_active', 'is_active'),
    )

    id = db.Column(db.String(50), primary_key=True)  # Soru ID'si
    dimension = db.Column(db.String(50), nullable=False)  # literacy, capacity, tolerance, behavioral, experience
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # multiple_choice, scale, yes_no
    options = db.Column(db.Text, nullable=False)  # JSON: [{"value": 1, "text": "A"}, {"value": 2, "text": "B"}]
    correct_answer = db.Column(db.Integer, nullable=True)  # Okuryazarlık için
    scoring_weights = db.Column(db.Text, nullable=False)  # JSON: puan ağırlıkları
    explanation = db.Column(db.Text, nullable=True)  # Açıklama
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    version = db.Column(db.String(20), default='1.0')
    created_at = db.Column(db.DateTime, default=utcnow_naive)


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


# Re-exports from domain models
from domain.catalog.models.catalog_models import Category, AssetType, AssetSector
from domain.portfolio.models.portfolio_models import Asset, AssetTransaction, AssetUpdate
from domain.ledger.models.ledger_models import Account, JournalEntry, LedgerLine
__all__ = ['Category', 'AssetType', 'AssetSector', 'Asset', 'AssetTransaction', 'AssetUpdate', 'Account', 'JournalEntry', 'LedgerLine']

from infrastructure.database.models.outbox_model import OutboxMessageModel
__all__.append('OutboxMessageModel')
__all__.append('AuditLog')
__all__.append('MonitoringAlertConfig')
