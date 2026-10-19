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

    def execute(self, page=1, tenant_id=None, edit_id=None, per_page=100):
        last_t = self.financial_repository.transaction_page(page=page, per_page=per_page, tenant_id=tenant_id)
        cats = self.catalog_repository.list_visible_categories(tenant_id)
        edit_tx = self.financial_repository.get_transaction(edit_id, tenant_id=tenant_id) if edit_id else None

        plan_names = {}
        tx_summary = None
        if not hasattr(self.financial_repository, '_mock_name'):
            tx_items = getattr(last_t, 'items', None) or []
            plan_ids = {
                t.source_id for t in tx_items
                if getattr(t, 'source_type', None) == 'plan' and getattr(t, 'source_id', None)
            }
            if plan_ids and tenant_id and hasattr(self.financial_repository, 'get_plan_names_by_ids'):
                try:
                    plan_names = self.financial_repository.get_plan_names_by_ids(plan_ids, tenant_id=tenant_id)
                except Exception:
                    plan_names = {}

            total_rows = getattr(last_t, 'total', 0) or 0
            if (
                isinstance(total_rows, int)
                and total_rows > len(tx_items)
                and tenant_id
                and hasattr(self.financial_repository, 'get_transaction_summary_aggregates')
            ):
                try:
                    tx_summary = self.financial_repository.get_transaction_summary_aggregates(tenant_id=tenant_id)
                except Exception:
                    tx_summary = None

        return {
            'last_t': last_t,
            'cats': cats,
            'edit_tx': edit_tx,
            'plan_names': plan_names,
            'tx_summary': tx_summary,
        }
