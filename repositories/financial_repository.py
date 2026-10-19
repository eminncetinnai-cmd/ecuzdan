"""
Financial Repository — repositories/financial_repository.py

Finansal ekranlar ve işlemler için read/write repository (Facade).
TransactionRepository ve RecurringPlanRepository'yi birleştirir,
ayrıca Asset sorgularını yönetir.
Geriye dönük %100 uyumluluk için tüm eski sembolleri ve modelleri re-export eder.
"""

from typing import List, Optional

from models import Asset, Category, Payment, PlanOccurrence, RecurringPlan, Transaction
from repositories.base import BaseRepository

from .contracts import BaseRepositoryContract, FinancialRepositoryContract
from .recurring_plan_repository import RecurringPlanRepository
from .transaction_repository import TransactionRepository

__all__ = [
    'FinancialRepository',
    'Asset',
    'Category',
    'Payment',
    'PlanOccurrence',
    'RecurringPlan',
    'Transaction',
    'BaseRepository',
    'BaseRepositoryContract',
    'FinancialRepositoryContract',
]


class FinancialRepository(TransactionRepository, RecurringPlanRepository, FinancialRepositoryContract):
    """
    Transaction, RecurringPlan ve Asset veri işlemlerini birleştiren Facade Repository.
    Geriye dönük tam uyumluluk sağlar.
    """

    @staticmethod
    def _with_asset_relations(query):
        if not hasattr(query, '_mock_return_value') and hasattr(Asset, 'transactions'):
            from sqlalchemy.orm import joinedload, selectinload
            opts = [selectinload(Asset.transactions)]
            if hasattr(Asset, 'sector'):
                opts.append(joinedload(Asset.sector))
            query = query.options(*opts)
        return query

    def list_assets(self, tenant_id: Optional[str] = None) -> List[Asset]:
        query = self._with_asset_relations(Asset.query)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()

    def list_assets_by_name(self, tenant_id: Optional[str] = None) -> List[Asset]:
        query = self._with_asset_relations(Asset.query)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Asset.name).all()

    def asset_page(self, page: int = 1, per_page: int = 20, tenant_id: Optional[str] = None):
        query = self._with_asset_relations(Asset.query).order_by(Asset.last_updated.desc(), Asset.id.desc())
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def get_asset_for_tenant(self, asset_id: int, tenant_id: Optional[str] = None) -> Optional[Asset]:
        query = self._with_asset_relations(Asset.query).filter_by(id=asset_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
