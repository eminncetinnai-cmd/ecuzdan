"""Repository for category management."""

from typing import List, Optional

from models import Category

from .base import BaseRepository, TenantScopedRepository


class CategoryRepository(BaseRepository):
    """Repository for category operations."""

    def get_category(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        return self.get(Category, category_id)

    def find_category_by_name(self, name: str, tenant_id: Optional[str] = None) -> Optional[Category]:
        """Find category by name, optionally scoped to tenant."""
        query = self.session.query(Category).filter_by(name=name)
        if tenant_id is not None:
            query = query.filter_by(tenant_id=tenant_id)
        else:
            # Get standard categories (tenant_id=None)
            query = query.filter_by(tenant_id=None)
        return query.first()

    def find_category_by_code(self, code: str, tenant_id: Optional[str] = None) -> Optional[Category]:
        """Find category by code, optionally scoped to tenant."""
        query = self.session.query(Category).filter_by(code=code)
        if tenant_id is not None:
            query = query.filter_by(tenant_id=tenant_id)
        else:
            # Get standard categories (tenant_id=None)
            query = query.filter_by(tenant_id=None)
        return query.first()

    def get_standard_categories(self) -> List[Category]:
        """Get all standard categories (tenant_id=None)."""
        return self.session.query(Category).filter_by(tenant_id=None).all()

    def get_categories_by_type(self, category_type: str, tenant_id: Optional[str] = None) -> List[Category]:
        """Get categories by type, optionally scoped to tenant."""
        query = self.session.query(Category).filter_by(type=category_type)
        if tenant_id is not None:
            query = query.filter_by(tenant_id=tenant_id)
        else:
            # Get standard categories (tenant_id=None)
            query = query.filter_by(tenant_id=None)
        return query.all()

    def get_tenant_categories(self, tenant_id: str) -> List[Category]:
        """Get all categories for a specific tenant."""
        return self.session.query(Category).filter_by(tenant_id=tenant_id).all()

    def add_category(self, **fields) -> Category:
        """Add a new category."""
        return self.add(Category(**fields))

    def delete_category(self, category: Category) -> None:
        """Delete a category."""
        self.delete(category)

    def is_category_name_exists(self, name: str, tenant_id: Optional[str] = None, exclude_id: Optional[int] = None) -> bool:
        """Check if category name exists, optionally excluding a specific ID."""
        query = self.session.query(Category).filter_by(name=name)
        if tenant_id is not None:
            query = query.filter_by(tenant_id=tenant_id)
        else:
            query = query.filter_by(tenant_id=None)

        if exclude_id:
            query = query.filter(Category.id != exclude_id)

        return query.first() is not None

    def is_category_code_exists(self, code: str, tenant_id: Optional[str] = None, exclude_id: Optional[int] = None) -> bool:
        """Check if category code exists, optionally excluding a specific ID."""
        query = self.session.query(Category).filter_by(code=code)
        if tenant_id is not None:
            query = query.filter_by(tenant_id=tenant_id)
        else:
            query = query.filter_by(tenant_id=None)

        if exclude_id:
            query = query.filter(Category.id != exclude_id)

        return query.first() is not None


class TenantCategoryRepository(TenantScopedRepository):
    """Tenant-scoped category repository."""

    def get_categories_for_tenant(self, tenant_id: Optional[str] = None) -> List[Category]:
        """Get all categories for a tenant (including standard categories)."""
        tenant_id = self.require_tenant_id(tenant_id)

        # Get both tenant-specific and standard categories
        tenant_categories = self.session.query(Category).filter_by(tenant_id=tenant_id).all()
        standard_categories = self.session.query(Category).filter_by(tenant_id=None).all()

        return tenant_categories + standard_categories

    def get_tenant_specific_categories(self, tenant_id: str) -> List[Category]:
        """Get only tenant-specific categories (excluding standard)."""
        tenant_id = self.require_tenant_id(tenant_id)
        return self.session.query(Category).filter_by(tenant_id=tenant_id).all()

    def find_category_for_tenant(self, name: str, tenant_id: Optional[str] = None) -> Optional[Category]:
        """Find category by name for tenant (checks tenant-specific first, then standard)."""
        tenant_id = self.require_tenant_id(tenant_id)

        # First check tenant-specific
        category = self.session.query(Category).filter_by(name=name, tenant_id=tenant_id).first()
        if category:
            return category

        # Then check standard categories
        return self.session.query(Category).filter_by(name=name, tenant_id=None).first()

    def is_valid_category_for_tenant(self, category_name: str, tenant_id: Optional[str] = None) -> bool:
        """Check if category name is valid for tenant (exists in tenant-specific or standard)."""
        category = self.find_category_for_tenant(category_name, tenant_id)
        return category is not None
