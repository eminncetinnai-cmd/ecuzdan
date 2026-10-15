"""Repositories for category and catalog lookups."""

from sqlalchemy.orm import joinedload

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

    def list_visible_categories(self, tenant_id=None, include_inactive=False):
        categories = get_cached('categories', lambda: Category.query.options(joinedload(Category.parent)).order_by(Category.type, Category.name).all())
        if not include_inactive:
            categories = [cat for cat in categories if getattr(cat, 'is_active', True) is not False]
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

    def add_category(self, name, category_type, tenant_id=None, code=None, parent_id=None, budget_limit=None, user_id=None, color=None, icon=None):
        from utils.ref_cache import invalidate
        cat = Category(
            name=name,
            type=category_type,
            tenant_id=tenant_id,
            code=code,
            parent_id=parent_id,
            budget_limit=budget_limit,
            color=color,
            icon=icon,
            created_by=user_id,
            updated_by=user_id,
            version=1
        )
        saved = self.add(cat)
        self.commit()
        if not saved.code:
            saved.code = _generate_gl_code(category_type, saved.id)
        saved.path = f"/{saved.id}/" if not parent_id else f"/{parent_id}/{saved.id}/"
        saved.level = 0 if not parent_id else 1
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

    def update_category(self, category_id, new_name, new_type, tenant_id=None, code=None, parent_id=None, budget_limit=None, budget_limit_provided=False, is_active=True, version=None, user_id=None, color=None, icon=None):
        from utils.ref_cache import invalidate
        category = db.session.get(Category, category_id)
        if not category:
            return None
        is_standard = category.tenant_id is None
        if not is_standard and tenant_id and category.tenant_id != tenant_id:
            raise ValueError("Bu kategoriyi düzenleme yetkiniz yok.")
        if is_standard:
            core_changed = (
                new_name != category.name
                or new_type != category.type
                or (code is not None and code != category.code)
                or (parent_id is not None and parent_id != category.parent_id)
                or is_active is not True
            )
            if core_changed:
                raise ValueError("Sistem kategorileri düzenlenemez; standart kategorinin çekirdek alanları korunur ve yalnızca aylık bütçe güncellenebilir.")
            if not budget_limit_provided:
                raise ValueError("Standart kategorilerde yalnızca aylık bütçe alanı güncellenebilir.")

        # Optimistic Locking Kontrolü
        if version is not None and category.version != version:
            raise ValueError("Çakışma Hatası: Kategori başka bir kullanıcı tarafından güncellenmiş. Lütfen sayfayı yenileyin.")

        old_name = category.name
        old_budget_limit = category.budget_limit
        if not is_standard:
            category.name = new_name
            category.type = new_type
            if old_name != new_name:
                try:
                    from models import RecurringPlan, Transaction
                    effective_tenant_id = category.tenant_id or tenant_id
                    tx_filters = {'category': old_name}
                    plan_filters = {'category': old_name}
                    if effective_tenant_id is not None:
                        tx_filters['tenant_id'] = effective_tenant_id
                        plan_filters['tenant_id'] = effective_tenant_id
                    Transaction.query.filter_by(**tx_filters).update({'category': new_name}, synchronize_session=False)
                    RecurringPlan.query.filter_by(**plan_filters).update({'category': new_name}, synchronize_session=False)
                except Exception:
                    pass
        if not is_standard:
            if color is not None:
                category.color = color or None
            if icon is not None:
                category.icon = icon or None
        if code is not None:
            category.code = code
        if parent_id is not None:
            category.parent_id = parent_id if parent_id != 0 else None
            category.path = f"/{parent_id}/{category.id}/" if category.parent_id else f"/{category.id}/"
            category.level = 0 if not category.parent_id else 1
        if budget_limit_provided:
            category.budget_limit = budget_limit
        if not is_standard:
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
                action='CATEGORY_BUDGET_UPDATED' if is_standard else 'CATEGORY_UPDATED',
                entity_type='category',
                entity_id=str(category.id),
                details=(
                    f"Standart kategori '{category.name}' aylık bütçesi "
                    f"{old_budget_limit} -> {category.budget_limit} olarak güncellendi."
                    if is_standard else
                    f"Kategori '{old_name}' -> '{new_name}' güncellendi (Versiyon: {category.version})."
                )
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

        filter_kwargs = {'category': category.name}
        effective_tenant_id = category.tenant_id or tenant_id
        if effective_tenant_id is not None:
            filter_kwargs['tenant_id'] = effective_tenant_id

        transactions_using = Transaction.query.filter_by(**filter_kwargs).count()
        plans_using = 0
        try:
            from models import RecurringPlan
            plans_using = RecurringPlan.query.filter_by(**filter_kwargs).count()
        except Exception:
            pass

        if transactions_using > 0 or plans_using > 0:
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

    def restore_category(self, category_id, tenant_id=None, user_id=None):
        from utils.ref_cache import invalidate
        category = db.session.get(Category, category_id)
        if not category:
            return False
        if category.tenant_id is None:
            raise ValueError("Sistem kategorileri bu şekilde geri yüklenemez.")
        if tenant_id and category.tenant_id != tenant_id:
            raise ValueError("Bu kategoriyi geri yükleme yetkiniz yok.")

        category.is_active = True
        self.commit()
        invalidate('categories')

        try:
            from models import AuditLog
            audit = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action='CATEGORY_RESTORED',
                entity_type='category',
                entity_id=str(category.id),
                details=f"Arşivlenen kategori '{category.name}' geri yüklendi."
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            pass

        return True

    def merge_categories(self, source_id, target_id, tenant_id=None, user_id=None):
        from utils.ref_cache import invalidate
        if source_id == target_id:
            raise ValueError("Kaynak ve hedef kategori aynı olamaz.")

        source = db.session.get(Category, source_id)
        target = db.session.get(Category, target_id)
        if not source or not target:
            raise ValueError("Kaynak veya hedef kategori bulunamadı.")

        if source.tenant_id is None:
            raise ValueError("Sistem kategorileri kaynak kategori olarak birleştirilemez.")
        if tenant_id and source.tenant_id != tenant_id:
            raise ValueError("Kaynak kategoriyi birleştirme yetkiniz yok.")
        if target.tenant_id is not None and tenant_id and target.tenant_id != tenant_id:
            raise ValueError("Hedef kategoriye erişim yetkiniz yok.")
        if not target.is_active:
            raise ValueError("Hedef kategori aktif değil.")

        from models import RecurringPlan, Transaction
        effective_tenant_id = source.tenant_id or tenant_id

        tx_filter = {'category': source.name}
        plan_filter = {'category': source.name}
        if effective_tenant_id is not None:
            tx_filter['tenant_id'] = effective_tenant_id
            plan_filter['tenant_id'] = effective_tenant_id

        tx_count = Transaction.query.filter_by(**tx_filter).update({'category': target.name}, synchronize_session=False)
        plan_count = RecurringPlan.query.filter_by(**plan_filter).update({'category': target.name}, synchronize_session=False)

        # Kaynak kategoriyi arşivle
        source.is_active = False
        self.commit()
        invalidate('categories')

        try:
            from models import AuditLog
            audit = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action='CATEGORY_MERGED',
                entity_type='category',
                entity_id=str(source.id),
                details=f"'{source.name}' kategorisi '{target.name}' ile birleştirildi ({tx_count} işlem, {plan_count} plan aktarıldı)."
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            pass

        return {'tx_count': tx_count, 'plan_count': plan_count}

    def get_category_metrics(self, tenant_id=None):
        from datetime import datetime

        from models import Transaction
        current_month = datetime.now().strftime('%Y-%m')

        metrics = {}
        try:
            # 1. Toplam işlem sayısı ve hacim
            q1 = db.session.query(
                Transaction.category,
                db.func.count(Transaction.id).label('tx_count'),
                db.func.sum(Transaction.amount).label('total_amount')
            )
            if tenant_id:
                q1 = q1.filter(Transaction.tenant_id == tenant_id)
            for row in q1.group_by(Transaction.category).all():
                metrics[row.category] = {
                    'tx_count': row.tx_count or 0,
                    'total_amount': float(row.total_amount or 0),
                    'month_spent': 0.0
                }

            # 2. Cari ay harcaması (Gider)
            q2 = db.session.query(
                Transaction.category,
                db.func.sum(Transaction.amount).label('month_spent')
            ).filter(
                Transaction.type == 'Gider',
                Transaction.date.like(f"{current_month}%")
            )
            if tenant_id:
                q2 = q2.filter(Transaction.tenant_id == tenant_id)
            for row in q2.group_by(Transaction.category).all():
                if row.category not in metrics:
                    metrics[row.category] = {'tx_count': 0, 'total_amount': 0.0, 'month_spent': 0.0}
                metrics[row.category]['month_spent'] = float(row.month_spent or 0)
        except Exception:
            pass

        return metrics

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
