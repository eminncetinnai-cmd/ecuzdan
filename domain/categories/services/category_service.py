"""Service layer for category management."""

from typing import Dict, List, Optional, Set

from models import Category
from repositories.category_repository import CategoryRepository, TenantCategoryRepository


class CategoryService:
    """Service for category operations."""

    def __init__(self) -> None:
        self.repository: CategoryRepository = CategoryRepository()
        self.tenant_repository: TenantCategoryRepository = TenantCategoryRepository()

    def get_standard_categories(self) -> List[Category]:
        """Get all standard categories (tenant_id=None)."""
        return self.repository.get_standard_categories()

    def get_category_by_name(self, name: str, tenant_id: Optional[str] = None) -> Optional[Category]:
        """Get category by name, optionally scoped to tenant."""
        return self.repository.find_category_by_name(name, tenant_id)

    def get_category_by_code(self, code: str, tenant_id: Optional[str] = None) -> Optional[Category]:
        """Get category by code, optionally scoped to tenant."""
        return self.repository.find_category_by_code(code, tenant_id)

    def get_categories_by_type(self, category_type: str, tenant_id: Optional[str] = None) -> List[Category]:
        """Get categories by type, optionally scoped to tenant."""
        return self.repository.get_categories_by_type(category_type, tenant_id)

    def get_tenant_categories(self, tenant_id: str) -> List[Category]:
        """Get all categories for a specific tenant (including standard)."""
        return self.tenant_repository.get_categories_for_tenant(tenant_id)

    def get_tenant_specific_categories(self, tenant_id: str) -> List[Category]:
        """Get only tenant-specific categories (excluding standard)."""
        return self.tenant_repository.get_tenant_specific_categories(tenant_id)

    def is_valid_category(self, category_name: str, tenant_id: Optional[str] = None) -> bool:
        """Check if category name is valid (exists in standard or tenant-specific)."""
        if tenant_id:
            return self.tenant_repository.is_valid_category_for_tenant(category_name, tenant_id)
        else:
            # Check only standard categories
            return self.repository.find_category_by_name(category_name, tenant_id=None) is not None

    def is_valid_category_code(self, category_code: str, tenant_id: Optional[str] = None) -> bool:
        """Check if category code is valid (exists in standard or tenant-specific)."""
        if tenant_id:
            category = self.repository.find_category_by_code(category_code, tenant_id)
            if category:
                return True
            # Check standard categories
            return self.repository.find_category_by_code(category_code, tenant_id=None) is not None
        else:
            # Check only standard categories
            return self.repository.find_category_by_code(category_code, tenant_id=None) is not None

    def validate_category_names(
        self,
        category_names: List[str],
        tenant_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Validate multiple category names.

        Returns:
            dict: {
                'valid': list of valid category names,
                'invalid': list of invalid category names,
                'is_valid': boolean (all valid?)
            }
        """
        valid: List[str] = []
        invalid: List[str] = []

        for name in category_names:
            if self.is_valid_category(name, tenant_id):
                valid.append(name)
            else:
                invalid.append(name)

        return {
            'valid': valid,
            'invalid': invalid,
            'is_valid': len(invalid) == 0
        }

    def get_income_categories(self, tenant_id: Optional[str] = None) -> List[Category]:
        """Get all income categories."""
        return self.get_categories_by_type('Gelir', tenant_id)

    def get_expense_categories(self, tenant_id: Optional[str] = None) -> List[Category]:
        """Get all expense categories."""
        return self.get_categories_by_type('Gider', tenant_id)

    def get_investment_categories(self, tenant_id: Optional[str] = None) -> List[Category]:
        """Get all investment categories."""
        return self.get_categories_by_type('Yatırım', tenant_id)

    def get_transfer_categories(self, tenant_id: Optional[str] = None) -> List[Category]:
        """Get all transfer categories."""
        return self.get_categories_by_type('Transfer', tenant_id)

    def get_category_mapping(self, tenant_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get category name to type mapping.

        Returns:
            dict: {category_name: category_type}
        """
        categories = self.get_tenant_categories(tenant_id) if tenant_id else self.get_standard_categories()
        return {cat.name: cat.type for cat in categories}

    def get_standard_category_codes(self) -> Dict[str, Set[str]]:
        """
        Get all standard category codes.

        Returns:
            dict: {category_type: set of category_codes}
        """
        standard_categories = self.get_standard_categories()
        mapping: Dict[str, Set[str]] = {}

        for cat in standard_categories:
            if cat.type not in mapping:
                mapping[cat.type] = set()
            mapping[cat.type].add(cat.code)

        return mapping
