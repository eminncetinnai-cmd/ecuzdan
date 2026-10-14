from sqlalchemy import Numeric

from shared.db import db


class Category(db.Model):
    """Kategori modeli - Gelir, Gider, Yatırım, Transfer kategorileri (v2)

    tenant_id semantiği:
      NULL  → Sistem geneli standart kategori (tüm tenant'lar görür, değiştiremez)
      dolu  → Tenant'a özel kategori (yalnızca sahibi görebilir/değiştirebilir)

    v2 İyileştirmeleri:
    - GL / Hesap Kodu (`code`) ve Hesap Planı Entegrasyonu (`account_id` FK)
    - i18n Çoklu Dil Nesneleri (`names`, `description`)
    - Optimistic Locking (`version`) ve Audit İzleri (`created_by`, `created_at`, `updated_by`, `updated_at`)
    - Vergi Oranı (`tax_rate`) ve Sıralama (`sort_order`)
    """
    __tablename__ = 'category'
    __table_args__ = (
        db.Index('idx_category_tenant_type', 'tenant_id', 'type'),
        db.Index('idx_category_parent', 'parent_id'),
        db.Index('idx_category_path', 'path'),
        db.Index('idx_category_code_tenant', 'code', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), nullable=True)  # GL/Hesap Kodu: Örn. '520.01.001'
    name = db.Column(db.String(100), nullable=False)
    names = db.Column(db.JSON, nullable=True)  # Çoklu dil nesnesi: {"tr": "...", "en": "..."}
    description = db.Column(db.JSON, nullable=True)  # Çoklu dil nesnesi: {"tr": "...", "en": "..."}
    type = db.Column(db.String(20), nullable=False)  # 'Gelir', 'Gider', 'Yatırım', 'Transfer', 'Borç', 'Vergi', 'Komisyon', 'Temettü', 'Faiz', 'Kur Farkı'
    subcategory = db.Column(db.String(50), nullable=True)  # Alt kategori - geriye uyumluluk için (deprecated)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='RESTRICT'), nullable=True)  # Parent kategori
    level = db.Column(db.Integer, default=0, nullable=False)  # Hiyerarşi seviyesi
    path = db.Column(db.String(500), nullable=True)  # Hiyerarşi yolu: "/1/4/7/"
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Muhasebe (Ledger) ve Finans Entegrasyonu
    account_id = db.Column(db.Integer, db.ForeignKey('account.id', ondelete='SET NULL'), nullable=True)
    budget_limit = db.Column(Numeric(19, 4), nullable=True)
    tax_rate = db.Column(Numeric(5, 2), default=0.00, nullable=False)

    # UI Meta Verileri
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(7), nullable=True)

    # Durum & Güvenlik
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=True, index=True)

    # Denetim İzleri (Audit Trail) & Eşzamanlılık
    version = db.Column(db.Integer, default=1, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    # İlişkiler
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', cascade='all, delete-orphan'))
    account = db.relationship('Account', backref='categories')
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])



class AssetType(db.Model):
    """Varlık tipi modeli

    Phase 16: Hierarchical asset types with parent-child relationships
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'), nullable=True)  # Parent varlık tipi (Phase 16)
    level = db.Column(db.Integer, default=0)  # Hiyerarşi seviyesi (Phase 16)
    risk_profile = db.Column(db.String(20), nullable=True)  # 'conservative', 'moderate', 'aggressive', 'speculative' (Phase 16)
    tax_treatment = db.Column(db.String(20), nullable=True)  # 'taxable', 'tax_free', 'deferred' (Phase 16)
    min_holding_period = db.Column(db.Integer, nullable=True)  # Minimum tutma süresi (gün) (Phase 16)
    default_currency = db.Column(db.String(3), default='TRY', nullable=True)  # Varsayılan para birimi (Phase 16)
    liquidity_profile = db.Column(db.String(20), nullable=True)  # 'high', 'medium', 'low' (Phase 16)
    volatility_range = db.Column(db.String(20), nullable=True)  # 'low', 'medium', 'high', 'very_high' (Phase 16)

    parent = db.relationship('AssetType', remote_side=[id], backref='children')


class AssetSector(db.Model):
    """Varlık sektörü modeli

    Phase 16: Hierarchical sectors with parent-child relationships
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('asset_sector.id'), nullable=True)  # Parent sektör (Phase 16)
    level = db.Column(db.Integer, default=0)  # Hiyerarşi seviyesi (Phase 16)
    code = db.Column(db.String(10), nullable=True)  # GICS/ICB kodu (Phase 16)
    region = db.Column(db.String(50), nullable=True)  # Coğrafi bölge (Phase 16)
    regulatory_class = db.Column(db.String(20), nullable=True)  # Regülasyon sınıfı (Phase 16)
    cyclical_type = db.Column(db.String(20), nullable=True)  # 'cyclical', 'defensive', 'growth' (Phase 16)
    beta_range = db.Column(db.String(20), nullable=True)  # 'low', 'medium', 'high' (Phase 16)

    parent = db.relationship('AssetSector', remote_side=[id], backref='children')
