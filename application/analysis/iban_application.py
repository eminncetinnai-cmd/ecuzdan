"""IBAN Application Service for coordinating domain validation and repository persistence."""

from __future__ import annotations

from typing import Any

from application.base import ApplicationService
from domain.analysis.services.iban_service import IbanService
from repositories.iban_repository import IbanRepository


class IbanApplicationService(ApplicationService):
    """Application use case orchestrator for User IBAN management."""

    def __init__(
        self,
        iban_repository: IbanRepository | None = None,
        iban_domain_service: IbanService | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.iban_repository = iban_repository or IbanRepository()
        self.iban_domain_service = iban_domain_service or IbanService()

    def list_ibans(
        self,
        tenant_id: str,
        category: str | None = None,
        search: str | None = None,
    ) -> list[Any]:
        """List IBAN records for tenant."""
        return self.execute(
            lambda: self.iban_repository.list_ibans(tenant_id, category=category, search=search)
        )

    def get_iban(self, iban_id: int, tenant_id: str) -> Any | None:
        """Get single IBAN record."""
        return self.execute(
            lambda: self.iban_repository.get_iban(iban_id, tenant_id)
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
    ) -> Any:
        """Validate and create a new IBAN record."""
        def _action() -> Any:
            clean_iban = self.iban_domain_service.clean_iban(iban)
            is_valid, error = self.iban_domain_service.validate_iban(clean_iban)
            if not is_valid:
                raise ValueError(error)

            resolved_bank = bank_name.strip() if bank_name and bank_name.strip() else None
            if not resolved_bank:
                resolved_bank = self.iban_domain_service.detect_bank_name(clean_iban)

            return self.iban_repository.create_iban(
                tenant_id=tenant_id,
                user_id=user_id,
                title=title,
                iban=clean_iban,
                bank_name=resolved_bank,
                account_holder=account_holder,
                category=category,
                note=note,
                is_favorite=is_favorite,
                easy_address_type=easy_address_type,
                easy_address=easy_address,
            )

        return self.execute(_action)

    def update_iban(
        self,
        iban_id: int,
        tenant_id: str,
        title: str | None = None,
        iban: str | None = None,
        bank_name: str | None = None,
        account_holder: str | None = None,
        category: str | None = None,
        note: str | None = None,
        is_favorite: bool | None = None,
        easy_address_type: str | None = None,
        easy_address: str | None = None,
    ) -> Any | None:
        """Validate and update an existing IBAN record."""
        def _action() -> Any | None:
            fields: dict[str, Any] = {}
            if title is not None:
                fields["title"] = title
            if iban is not None:
                clean_iban = self.iban_domain_service.clean_iban(iban)
                is_valid, error = self.iban_domain_service.validate_iban(clean_iban)
                if not is_valid:
                    raise ValueError(error)
                fields["iban"] = clean_iban
                if not bank_name:
                    fields["bank_name"] = self.iban_domain_service.detect_bank_name(clean_iban)
            if bank_name is not None and "bank_name" not in fields:
                fields["bank_name"] = bank_name
            if account_holder is not None:
                fields["account_holder"] = account_holder
            if category is not None:
                fields["category"] = category
            if note is not None:
                fields["note"] = note
            if is_favorite is not None:
                fields["is_favorite"] = is_favorite
            if easy_address_type is not None:
                fields["easy_address_type"] = easy_address_type
            if easy_address is not None:
                fields["easy_address"] = easy_address

            return self.iban_repository.update_iban(iban_id, tenant_id, **fields)

        return self.execute(_action)

    def toggle_favorite(self, iban_id: int, tenant_id: str) -> Any | None:
        """Toggle favorite status of an IBAN record."""
        return self.execute(
            lambda: self.iban_repository.toggle_favorite(iban_id, tenant_id)
        )

    def delete_iban(self, iban_id: int, tenant_id: str) -> bool:
        """Delete an IBAN record."""
        return self.execute(
            lambda: self.iban_repository.delete_iban(iban_id, tenant_id)
        )
