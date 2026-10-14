"""Catalog/category service layer."""

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def _parse_budget_limit(raw_value):
    """Normalize a monthly budget without losing monetary precision."""
    if raw_value in (None, ''):
        return None
    try:
        value = Decimal(str(raw_value).strip().replace(',', '.'))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Aylık bütçe geçerli bir sayı olmalıdır.") from exc
    if not value.is_finite() or value < 0:
        raise ValueError("Aylık bütçe sıfır veya daha büyük olmalıdır.")
    return value


class CatalogService:
    def __init__(self, repository=None):
        self.repository = repository

    def page_context(self, tenant_id=None):
        cats = self.repository.list_visible_categories(tenant_id, include_inactive=True)
        metrics = self.repository.get_category_metrics(tenant_id)
        parent_cats = [c for c in cats if getattr(c, 'is_active', True) and not c.parent_id]
        return {
            'cats': cats,
            'parent_cats': parent_cats,
            'metrics': metrics,
            'asset_types': self.repository.list_asset_types(),
            'asset_sectors': self.repository.list_asset_sectors(),
        }

    def add_from_form(self, form, tenant_id=None, user_id=None):
        action = form.get('action')
        if action == 'add_cat':
            name = form.get('name', '').strip()
            category_type = form.get('type', '')
            code = form.get('code', '').strip() or None
            budget_limit = _parse_budget_limit(form.get('budget_limit', None))
            color = form.get('color', '').strip() or None
            icon = form.get('icon', '').strip() or None
            parent_id = form.get('parent_id', None)
            if parent_id is not None and str(parent_id).strip() not in ('', '0'):
                try:
                    parent_id = int(parent_id)
                except ValueError:
                    parent_id = None
            else:
                parent_id = None

            if not name:
                raise ValueError("Kategori adı boş olamaz.")
            if self.repository.category_exists(name, tenant_id):
                raise ValueError("Bu kategori zaten mevcut.")
            self.repository.add_category(
                name=name,
                category_type=category_type,
                tenant_id=tenant_id,
                code=code,
                parent_id=parent_id,
                budget_limit=budget_limit,
                user_id=user_id,
                color=color,
                icon=icon
            )
        elif action == 'update_cat':
            cat_id = form.get('cat_id')
            if not cat_id:
                raise ValueError("Güncellenecek kategori seçilmedi.")
            name = form.get('name', '').strip()
            category_type = form.get('type', '')
            code = form.get('code', '').strip() or None
            color = form.get('color', '').strip() or None
            icon = form.get('icon', '').strip() or None
            budget_present = 'budget_limit' in form
            budget_limit = _parse_budget_limit(form.get('budget_limit', None))
            version = form.get('version', None)
            if version:
                try:
                    version = int(version)
                except ValueError:
                    version = None

            parent_raw = form.get('parent_id', None)
            parent_id = None
            if parent_raw is not None:
                parent_raw = str(parent_raw).strip()
                if parent_raw in ('', '0'):
                    parent_id = 0
                else:
                    try:
                        parent_id = int(parent_raw)
                    except ValueError:
                        parent_id = 0

            if not name:
                raise ValueError("Kategori adı boş olamaz.")
            self.repository.update_category(
                category_id=int(cat_id),
                new_name=name,
                new_type=category_type,
                tenant_id=tenant_id,
                code=code,
                parent_id=parent_id,
                budget_limit=budget_limit,
                budget_limit_provided=budget_present,
                version=version,
                user_id=user_id,
                color=color,
                icon=icon
            )
        elif action == 'add_asset_type':
            name = form.get('asset_type_name', '').strip()
            if not name:
                raise ValueError("Varlık sınıfı adı boş olamaz.")
            if self.repository.asset_type_exists(name):
                raise ValueError("Bu varlık tipi zaten mevcut.")
            self.repository.add_asset_type(name)
        elif action == 'update_asset_type':
            asset_type_id = form.get('asset_type_id')
            name = form.get('asset_type_name', '').strip()
            if not asset_type_id or not name:
                raise ValueError("Güncellenecek varlık sınıfı adı boş olamaz.")
            self.repository.update_asset_type(int(asset_type_id), name)
        elif action == 'add_asset_sector':
            name = form.get('name', '').strip()
            if not name:
                raise ValueError("Sektör adı boş olamaz.")
            if self.repository.asset_sector_exists(name):
                raise ValueError("Bu sektör adı zaten mevcut.")
            self.repository.add_asset_sector(name)
        elif action == 'update_asset_sector':
            sector_id = form.get('asset_sector_id')
            name = form.get('name', '').strip()
            if not sector_id or not name:
                raise ValueError("Güncellenecek sektör adı boş olamaz.")
            self.repository.update_asset_sector(int(sector_id), name)
        else:
            raise ValueError("Geçersiz işlem.")
        self.repository.commit()


    def update_category(self, category_id, name, category_type, tenant_id=None, code=None, parent_id=None, budget_limit=None, budget_limit_provided=False, is_active=True, version=None, user_id=None, color=None, icon=None):
        normalized_budget = _parse_budget_limit(budget_limit) if budget_limit_provided else None
        return self.repository.update_category(
            category_id, name, category_type,
            tenant_id=tenant_id,
            code=code,
            parent_id=parent_id,
            budget_limit=normalized_budget,
            budget_limit_provided=budget_limit_provided,
            is_active=is_active,
            version=version,
            user_id=user_id,
            color=color,
            icon=icon,
        )

    def restore_category(self, category_id, tenant_id=None, user_id=None):
        return self.repository.restore_category(category_id, tenant_id=tenant_id, user_id=user_id)

    def merge_categories(self, source_id, target_id, tenant_id=None, user_id=None):
        return self.repository.merge_categories(source_id, target_id, tenant_id=tenant_id, user_id=user_id)

    def delete_category(self, category_id, tenant_id=None, user_id=None):
        return self.repository.delete_category(category_id, tenant_id=tenant_id, user_id=user_id)

    def update_asset_type(self, asset_type_id, name):
        return self.repository.update_asset_type(asset_type_id, name)

    def delete_asset_type(self, asset_type_id):
        return self.repository.delete_asset_type(asset_type_id)

    def update_asset_sector(self, asset_sector_id, name):
        return self.repository.update_asset_sector(asset_sector_id, name)

    def delete_asset_sector(self, asset_sector_id):
        return self.repository.delete_asset_sector(asset_sector_id)


