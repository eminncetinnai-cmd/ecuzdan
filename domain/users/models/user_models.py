import os
from datetime import datetime, timezone

from sqlalchemy import Numeric

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    """Kullanıcı modeli"""
    ADMIN_ROLES = frozenset({'sistem_yoneticisi', 'yonetici'})
    #: Platform sahibinin kullanıcı adı. config.Config.SUPER_ADMIN_USERNAME ile
    #: aynı ortam değişkenini okur; models.py config'i import etmez (erken
    SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'emin')
    SUPER_ADMIN_USERNAMES = frozenset(
        u.strip().lower() for u in os.getenv(
            'SUPER_ADMIN_USERNAMES',
            'emin,eminncetinn@gmail.com,eminncetinn.ai@gmail.com'
        ).split(',') if u.strip()
    )
    __table_args__ = (
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_auth_provider', 'auth_provider'),
        db.Index('idx_user_last_login', 'last_login_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True, index=True)  # Separate email field for OAuth users
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

    # Personal information fields
    gender = db.Column(db.String(10), nullable=True)  # 'male', 'female', 'other', 'prefer_not_to_say'
    birthdate = db.Column(db.Date, nullable=True)
    country = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # Special code for role upgrades
    special_code = db.Column(db.String(50), nullable=True)  # Code used to upgrade role
    special_code_used_at = db.Column(db.DateTime, nullable=True)  # When the code was used
    tenant = db.relationship('Tenant', backref='users')

    @property
    def is_super_admin(self):
        """Süper yönetici: emin kullanıcısı veya tanımlı süper admin e-postaları."""
        if self.username == self.SUPER_ADMIN_USERNAME or (self.username and self.username.lower() in self.SUPER_ADMIN_USERNAMES):
            return True
        if self.email and self.email.lower() in self.SUPER_ADMIN_USERNAMES:
            return True
        return False

    @property
    def is_superadmin(self):
        """is_super_admin alias (şablon uyumluluğu)."""
        return self.is_super_admin

    @property
    def has_full_platform_access(self):
        """Emin düzeyi platform erişimi: gerçek owner, system role veya özel kod."""
        from utils.capabilities import has_full_platform_access

        return has_full_platform_access(self)

    def has_capability(self, capability):
        """Return whether this user can use a canonical capability."""
        from utils.capabilities import has_capability

        return has_capability(self, capability)

    @property
    def has_admin_access(self):
        """Yönetici paneli ve admin işlemlerine tam erişim."""
        return self.has_full_platform_access or self.role in self.ADMIN_ROLES

    @property
    def is_tenant_admin(self):
        """Tenant admin mi"""
        return self.role == 'tenant_admin'

    @property
    def role_labels(self):
        """Arayüzde gösterilecek rol etiketleri."""
        if self.has_full_platform_access:
            return ['Tam Yetki', 'Sistem Yöneticisi', 'Yönetici']

        if self.role == 'sistem_yoneticisi':
            return ['Sistem Yöneticisi']
        if self.role == 'yonetici':
            return ['Yönetici']
        if self.role == 'tenant_admin':
            return ['Tenant Admin']
        return ['Kullanıcı']


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

    user = db.relationship('User', backref=db.backref('preference', uselist=False, lazy='joined'))

    @property
    def target_retirement_year(self):
        """Doğum yılı ve hedef yaştan hedef bağımsızlık yılı."""
        if self.birth_year and self.target_retirement_age:
            return self.birth_year + self.target_retirement_age
        return None

    def __repr__(self):
        return f'<UserPreference user={self.user_id}>'


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
