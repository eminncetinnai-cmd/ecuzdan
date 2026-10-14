from sqlalchemy import Numeric

from shared.db import db


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
