"""Repository for User IBAN storage and queries."""

from __future__ import annotations

from typing import Any

from models import UserIban
from repositories.base import TenantScopedRepository


class IbanRepository(TenantScopedRepository):
    """Repository handling persistence for user registered IBAN records."""

    def list_ibans(
        self,
        tenant_id: str,
        category: str | None = None,
        search: str | None = None,
    ) -> list[UserIban]:
        """List all IBANs for a given tenant, with optional category and search filtering."""
        t_id = self.require_tenant_id(tenant_id)
        query = self.query(UserIban).filter(UserIban.tenant_id == t_id)

        if category:
            query = query.filter(UserIban.category == category)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                (UserIban.title.ilike(term))
                | (UserIban.bank_name.ilike(term))
                | (UserIban.account_holder.ilike(term))
                | (UserIban.iban.ilike(term))
                | (UserIban.note.ilike(term))
                | (UserIban.easy_address.ilike(term))
            )

        return query.order_by(
            UserIban.is_favorite.desc(),
            UserIban.category.asc(),
            UserIban.title.asc(),
            UserIban.created_at.desc(),
        ).all()

    def get_iban(self, iban_id: int, tenant_id: str) -> UserIban | None:
        """Fetch a single IBAN record by ID ensuring strict tenant isolation."""
        t_id = self.require_tenant_id(tenant_id)
        return (
            self.query(UserIban)
            .filter(UserIban.id == iban_id, UserIban.tenant_id == t_id)
            .first()
        )

    def create_iban(
        self,
        tenant_id: str,
        user_id: int | None,
        title: str,
        iban: str,
        bank_name: str | None = None,
        account_holder: str | None = None,
        category: str = "kendi_hesabim",
        note: str | None = None,
        is_favorite: bool = False,
        easy_address_type: str | None = None,
        easy_address: str | None = None,
    ) -> UserIban:
        """Create and persist a new IBAN record."""
        t_id = self.require_tenant_id(tenant_id)
        record = UserIban(
            tenant_id=t_id,
            user_id=user_id,
            title=title.strip(),
            iban=iban.strip(),
            bank_name=bank_name.strip() if bank_name else None,
            account_holder=account_holder.strip() if account_holder else None,
            category=category or "kendi_hesabim",
            note=note.strip() if note else None,
            is_favorite=bool(is_favorite),
            easy_address_type=easy_address_type.strip() if easy_address_type else None,
            easy_address=easy_address.strip() if easy_address else None,
        )
        self.add(record)
        self.commit()
        return record

    def update_iban(
        self,
        iban_id: int,
        tenant_id: str,
        **fields: Any,
    ) -> UserIban | None:
        """Update an existing IBAN record."""
        record = self.get_iban(iban_id, tenant_id)
        if not record:
            return None

        allowed_fields = {
            "title",
            "iban",
            "bank_name",
            "account_holder",
            "category",
            "note",
            "is_favorite",
            "easy_address_type",
            "easy_address",
        }
        for key, value in fields.items():
            if key in allowed_fields:
                if isinstance(value, str):
                    setattr(record, key, value.strip() if value.strip() else None)
                elif key == "is_favorite":
                    setattr(record, key, bool(value))
                else:
                    setattr(record, key, value)

        self.commit()
        return record

    def toggle_favorite(self, iban_id: int, tenant_id: str) -> UserIban | None:
        """Toggle favorite / pinned status of an IBAN record."""
        record = self.get_iban(iban_id, tenant_id)
        if not record:
            return None
        record.is_favorite = not bool(record.is_favorite)
        self.commit()
        return record

    def delete_iban(self, iban_id: int, tenant_id: str) -> bool:
        """Delete an IBAN record."""
        record = self.get_iban(iban_id, tenant_id)
        if not record:
            return False

        self.delete(record)
        self.commit()
        return True
