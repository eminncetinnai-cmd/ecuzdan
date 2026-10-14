"""
Repository contracts and abstract interfaces for Phase 4.

These are non-invasive interface definitions used to standardize repository responsibilities
and provide a clear contract for future refactorings. Implementations remain unchanged.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol


class BaseRepositoryContract(ABC):
    """Minimal contract for concrete repositories that wrap a DB/session."""

    @abstractmethod
    def get(self, model: Any, obj_id: Any) -> Any:
        pass

    @abstractmethod
    def add(self, entity: Any) -> Any:
        pass

    @abstractmethod
    def delete(self, entity: Any) -> None:
        pass

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass


class ReadRepositoryContract(Protocol):
    """Protocol for read/query focused repositories."""

    def list(self, *args, **kwargs) -> List[Any]:
        ...

    def get(self, *args, **kwargs) -> Any:
        ...


class WriteRepositoryContract(Protocol):
    """Protocol for write-focused repositories."""

    def add(self, *args, **kwargs) -> Any:
        ...

    def delete(self, *args, **kwargs) -> None:
        ...

    def commit(self) -> None:
        ...


class TenantAwareRepositoryContract(Protocol):
    """Repository that supports tenant-scoped queries via tenant_id parameter."""

    def list_for_tenant(self, tenant_id: Optional[str], *args, **kwargs) -> List[Any]:
        ...


# Domain-specific small contracts for discovery/documentation only (non-binding)
class CatalogRepositoryContract(Protocol):
    def list_visible_categories(self, tenant_id: Optional[str] = None) -> List[Any]:
        ...

    def add_category(self, name: str, category_type: str, tenant_id: Optional[str] = None) -> Any:
        ...

    def update_category(self, category_id: Any, new_name: str, new_type: str, tenant_id: Optional[str] = None) -> Any:
        ...

    def delete_category(self, category_id: Any, tenant_id: Optional[str] = None) -> bool:
        ...

    def restore_category(self, category_id: Any, tenant_id: Optional[str] = None) -> bool:
        ...

    def merge_categories(self, source_id: Any, target_id: Any, tenant_id: Optional[str] = None) -> Any:
        ...

    def get_category_metrics(self, tenant_id: Optional[str] = None) -> Any:
        ...

    def update_asset_type(self, asset_type_id: Any, new_name: str) -> Any:
        ...

    def delete_asset_type(self, asset_type_id: Any) -> bool:
        ...

    def update_asset_sector(self, asset_sector_id: Any, new_name: str) -> Any:
        ...

    def delete_asset_sector(self, asset_sector_id: Any) -> bool:
        ...


class FinancialRepositoryContract(Protocol):
    def list_transactions(self, tenant_id: Optional[str] = None, **kwargs) -> List[Any]:
        ...

    def get_transaction(self, transaction_id: Any) -> Any:
        ...

    def add_transaction(
        self,
        date: str,
        category: str,
        description: str,
        type_: str,
        amount: float,
        status: str,
        note: Optional[str] = None,
        source_id: Optional[Any] = None,
        source_type: Optional[str] = None,
        installment_number: Optional[int] = None,
        tenant_id: Optional[str] = None,
        bank_account_id: Optional[int] = None,

    ) -> Any:
        ...

    def update_transaction(
        self,
        transaction_id: Any,
        date: str,
        category: str,
        description: str,
        amount: float,
        status: str,
        note: Optional[str] = None,
    ) -> Any:
        ...

    def delete_transaction(self, transaction_id: Any) -> None:
        ...

    def list_recurring_plans(self, flow_type: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Any]:
        ...

    def get_recurring_plan_for_tenant(self, plan_id: Any, tenant_id: Optional[str]) -> Any:
        ...

    def add_recurring_plan(
        self,
        name: str,
        category: str,
        amount: float,
        installments: int,
        payment_day: int,
        note: Optional[str] = None,
        start_date: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        ...

    def create_payment(
        self,
        plan_id: Any,
        amount: float,
        payment_date: str,
        installment_number: int,
        notes: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        ...

    def update_recurring_plan(
        self,
        plan_id: Any,
        name: str,
        category: str,
        amount: float,
        installments: int,
        payment_day: int,
        note: Optional[str] = None,
        start_date: Optional[str] = None,
    ) -> Any:
        ...

    def delete_plan(self, plan_id: Any, tenant_id: Optional[str] = None) -> Any:
        ...

    def list_assets(self, tenant_id: Optional[str] = None) -> List[Any]:
        ...


class ReportingRepositoryContract(Protocol):
    def get_monthly_balance(self, year: int, month: int, tenant_id: Optional[str] = None) -> Any:
        ...

    def get_actual_cash(self, tenant_id: Optional[str] = None) -> Any:
        ...

    def get_total_assets(self, tenant_id: Optional[str] = None) -> Any:
        ...

    def get_total_debts(self, tenant_id: Optional[str] = None) -> Any:
        ...

    def get_transactions_by_date_range(self, start_date: str, end_date: str, tenant_id: Optional[str] = None) -> List[Any]:
        ...

    def get_calendar_month_data(self, year: int, month: int, tenant_id: Optional[str] = None) -> Any:
        ...

    def get_pending_payments(self, start_date: str, end_date: str, tenant_id: Optional[str] = None) -> List[Any]:
        ...


class PortfolioRepositoryContract(Protocol):
    """Protocol for portfolio and asset-level persistence operations."""

    def add_asset(
        self,
        type_: str,
        name: str,
        value: float,
        description: str,
        purchase_date=None,
        purchase_cost: float = 0.0,
        quantity: float = 1.0,
        unit_price: float = 0.0,
        currency: str = 'TRY',
        symbol=None,
        risk_level: str = 'Orta',
        liquidity: str = 'Likit',
        sector_id=None,
        notes=None,
        tenant_id=None,
    ) -> Any:
        ...

    def update_asset(
        self,
        asset_id: Any,
        type_: str,
        name: str,
        value: float,
        description: str,
        purchase_date=None,
        purchase_cost: float = 0.0,
        quantity: float = 1.0,
        unit_price: float = 0.0,
        currency: str = 'TRY',
        symbol=None,
        risk_level: str = 'Orta',
        liquidity: str = 'Likit',
        sector_id=None,
        notes=None,
    ) -> Any:
        ...

    def delete_asset(self, asset_id: Any) -> Any:
        ...

    def log_asset_update(
        self,
        asset_id: Any,
        old_value: float,
        new_value: float,
        old_unit_price=None,
        new_unit_price=None,
        update_type: str = 'manual',
        update_source=None,
        notes=None,
        user_id=None,
        auto_commit: bool = True,
    ) -> Any:
        ...

    def get_asset_update_history(self, asset_id: Any, limit: int = 50) -> List[Any]:
        ...

    def bulk_update_assets(self, asset_ids, new_unit_prices, user_id=None, notes=None) -> List[Any]:
        ...


# End of contracts module
