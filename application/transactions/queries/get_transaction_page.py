"""Get transaction page query."""

from application.base import Query
from repositories.catalog_repository import CatalogRepository
from repositories.financial_repository import FinancialRepository


class GetTransactionPageQuery(Query):
    def __init__(
        self,
        financial_repository: FinancialRepository,
        catalog_repository: CatalogRepository,
    ):
        self.financial_repository = financial_repository
        self.catalog_repository = catalog_repository

    def execute(self, page=1, tenant_id=None, edit_id=None, per_page=1000):
        return {
            'last_t': self.financial_repository.transaction_page(page=page, per_page=per_page, tenant_id=tenant_id),
            'cats': self.catalog_repository.list_visible_categories(tenant_id),
            'edit_tx': self.financial_repository.get_transaction(edit_id, tenant_id=tenant_id) if edit_id else None,
        }
