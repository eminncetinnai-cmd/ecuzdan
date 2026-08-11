"""Repositories for category and catalog lookups."""

from models import Asset, AssetSector, AssetType, Category, Transaction, db

from utils.ref_cache import get_cached
from .base import BaseRepository
from .contracts import BaseRepositoryContract, CatalogRepositoryContract


# ---------------------------------------------------------------------------
# GL Kodu Üretim Mantığı — Türk Muhasebe Standartları (TDMS) + IFRS Uyumlu
# ---------------------------------------------------------------------------
# Hesap Grubu Aralıkları:
#   Gelir   (Revenue)    → GLR-6xxx  (600-699 muhasebe hesap grubu)
#   Gider   (Expense)    → GDR-7xxx  (700-799 muhasebe hesap grubu)
#   Yatırım (Investment) → YTR-1xxx  (100-199 Varlık/Bilanço hesap grubu)
# ---------------------------------------------------------------------------
def _generate_gl_code(category_type: str, category_id: int) -> str:
    """TDMS/IFRS uyumlu GL kodu üretir.

    Prefix + hesap grubu numarası formatında üretilir:
      GLR-6001, GLR-6002 … (Gelir)
      GDR-7001, GDR-7002 … (Gider)
      YTR-1001, YTR-1002 … (Yatırım)
    """
    if category_type == 'Gelir':
        base = 6000
        prefix = 'GLR'
    elif category_type == 'Gider':
        base = 7000
        prefix = 'GDR'
    else:  # Yatırım
        base = 1000
        prefix = 'YTR'

    return f"{prefix}-{base + category_id}"


class CatalogRepository(BaseRepository, BaseRepositoryContract, CatalogRepositoryContract):
    """CatalogRepository implements the repository contracts defined in repositories/contracts.py.

    This is a non-invasive change: public API and SQLAlchemy queries are not modified.
    Adding the contract as a base class documents the intended interface and enables
    static typing / runtime checks in future refactors.
    """
    def visible_categories_query(self, tenant_id=None):
        query = Category.query
        if tenant_id:
            query = query.filter(
                db.or_(Category.tenant_id.is_(None), Category.tenant_id == tenant_id)
            )
        return query

    def list_visible_categories(self, tenant_id=None):
        categories = get_cached('categories', lambda: Category.query.order_by(Category.type, Category.name).all())
        if tenant_id:
            return [cat for cat in categories if cat.tenant_id is None or cat.tenant_id == tenant_id]
        return categories

    def list_categories_by_type(self, category_type, tenant_id=None):
        return self.visible_categories_query(tenant_id).filter_by(type=category_type).all()

    def find_category_by_name(self, name, tenant_id=None):
        query = Category.query.filter_by(name=name)
        if tenant_id:
            query = query.filter(
                db.or_(Category.tenant_id.is_(None), Category.tenant_id == tenant_id)
            )
        return query.first()

    def category_exists(self, name, tenant_id=None):
        return self.find_category_by_name(name, tenant_id) is not None

    def add_category(self, name, category_type, tenant_id=None, code=None, parent_id=None, budget_limit=None, user_id=None):
        from utils.ref_cache import invalidate
        cat = Category(
            name=name,
            type=category_type,
            tenant_id=tenant_id,
            code=code,
            parent_id=parent_id,
            budget_limit=budget_limit,
            created_by=user_id,
            updated_by=user_id,
            version=1
        )
        saved = self.add(cat)
        self.commit()
        if not saved.code:
            saved.code = _generate_gl_code(category_type, saved.id)
        saved.path = f"/{saved.id}/" if not parent_id else f"/{parent_id}/{saved.id}/"
        self.commit()
        invalidate('categories')

        # AuditLog tetikle
        try:
            from models import AuditLog
            audit = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action='CATEGORY_CREATED',
                entity_type='category',
                entity_id=str(saved.id),
                details=f"Kategori '{saved.name}' ({saved.code}) oluşturuldu."
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            pass

        return saved

    def update_category(self, category_id, new_name, new_type, tenant_id=None, code=None, parent_id=None, budget_limit=None, is_active=True, version=None, user_id=None):
        from utils.ref_cache import invalidate
        category = db.session.get(Category, category_id)
        if not category:
            return None
        if category.tenant_id is None:
            raise ValueError("Sistem kategorileri düzenlenemez. Kendi özel kategorinizi oluşturun.")
        if tenant_id and category.tenant_id != tenant_id:
            raise ValueError("Bu kategoriyi düzenleme yetkiniz yok.")
        
        # Optimistic Locking Kontrolü
        if version is not None and category.version != version:
            raise ValueError("Çakışma Hatası: Kategori başka bir kullanıcı tarafından güncellenmiş. Lütfen sayfayı yenileyin.")

        old_name = category.name
        category.name = new_name
        category.type = new_type
        if code is not None:
            category.code = code
        if parent_id is not None:
            category.parent_id = parent_id
            category.path = f"/{parent_id}/{category.id}/" if parent_id else f"/{category.id}/"
        if budget_limit is not None:
            category.budget_limit = budget_limit
        category.is_active = is_active
        category.version = (category.version or 1) + 1
        category.updated_by = user_id

        self.commit()
        invalidate('categories')

        # AuditLog Tetikle
        try:
            from models import AuditLog
            audit = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action='CATEGORY_UPDATED',
                entity_type='category',
                entity_id=str(category.id),
                details=f"Kategori '{old_name}' -> '{new_name}' güncellendi (Versiyon: {category.version})."
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            pass

        return category

    def delete_category(self, category_id, tenant_id=None, user_id=None):
        from utils.ref_cache import invalidate
        category = db.session.get(Category, category_id)
        if not category:
            return False
        if category.tenant_id is None:
            raise ValueError("Sistem kategorileri silinemez.")
        if tenant_id and category.tenant_id != tenant_id:
            raise ValueError("Bu kategoriyi silme yetkiniz yok.")
        transactions_using = Transaction.query.filter_by(category=category.name).count()
        if transactions_using > 0:
            # Soft Delete (Archiving) fallback if referenced
            category.is_active = False
            self.commit()
            invalidate('categories')
            return True
        
        cat_name = category.name
        cat_id = category.id
        self.delete(category)
        self.commit()
        invalidate('categories')

        # AuditLog Tetikle
        try:
            from models import AuditLog
            audit = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action='CATEGORY_DELETED',
                entity_type='category',
                entity_id=str(cat_id),
                details=f"Kategori '{cat_name}' silindi."
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            pass

        return True

    def list_asset_types(self):
        return AssetType.query.all()

    def asset_type_exists(self, name):
        return AssetType.query.filter_by(name=name).first() is not None

    def add_asset_type(self, name):
        return self.add(AssetType(name=name))

    def list_asset_sectors(self):
        return AssetSector.query.all()

    def asset_sector_exists(self, name):
        return AssetSector.query.filter_by(name=name).first() is not None

    def add_asset_sector(self, name):
        return self.add(AssetSector(name=name))


    def update_asset_type(self, asset_type_id, new_name):
        from utils.ref_cache import invalidate
        asset_type = db.session.get(AssetType, asset_type_id)
        if asset_type:
            asset_type.name = new_name
            self.commit()
            invalidate('asset_types')
            return asset_type
        return None

    def delete_asset_type(self, asset_type_id):
        from utils.ref_cache import invalidate
        asset_type = db.session.get(AssetType, asset_type_id)
        if asset_type:
            assets_using = Asset.query.filter_by(type=asset_type.name).count()
            if assets_using > 0:
                raise ValueError(f"Bu varlık tipi {assets_using} varlık tarafından kullanılıyor. Önce varlıkları güncelleyin.")
            self.delete(asset_type)
            self.commit()
            invalidate('asset_types')
            return True
        return False

    def update_asset_sector(self, asset_sector_id, new_name):
        from utils.ref_cache import invalidate
        asset_sector = db.session.get(AssetSector, asset_sector_id)
        if asset_sector:
            asset_sector.name = new_name
            self.commit()
            invalidate('asset_sectors')
            return asset_sector
        return None

    def delete_asset_sector(self, asset_sector_id):
        from utils.ref_cache import invalidate
        asset_sector = db.session.get(AssetSector, asset_sector_id)
        if asset_sector:
            assets_using = Asset.query.filter_by(sector_id=asset_sector_id).count()
            if assets_using > 0:
                raise ValueError(f"Bu sektör {assets_using} varlık tarafından kullanılıyor. Önce varlıkları güncelleyin.")
            self.delete(asset_sector)
            self.commit()
            invalidate('asset_sectors')
            return True
        return False
