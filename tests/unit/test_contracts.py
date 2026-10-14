"""
Unit Tests - Repository Contracts
Repository contracts and abstract interfaces tests
"""

import pytest

from repositories.contracts import (
    BaseRepositoryContract,
    CatalogRepositoryContract,
    FinancialRepositoryContract,
    PortfolioRepositoryContract,
    ReadRepositoryContract,
    ReportingRepositoryContract,
    TenantAwareRepositoryContract,
    WriteRepositoryContract,
)


@pytest.mark.unit
def test_contracts_module_imports():
    """Test contracts module can be imported"""
    from repositories.contracts import BaseRepositoryContract
    assert BaseRepositoryContract is not None


@pytest.mark.unit
def test_contracts_module_structure():
    """Test contracts module structure"""
    import repositories.contracts as contracts_module

    # Check for expected classes
    assert hasattr(contracts_module, 'BaseRepositoryContract')
    assert hasattr(contracts_module, 'ReadRepositoryContract')
    assert hasattr(contracts_module, 'WriteRepositoryContract')
    assert hasattr(contracts_module, 'TenantAwareRepositoryContract')
    assert hasattr(contracts_module, 'CatalogRepositoryContract')
    assert hasattr(contracts_module, 'FinancialRepositoryContract')
    assert hasattr(contracts_module, 'ReportingRepositoryContract')
    assert hasattr(contracts_module, 'PortfolioRepositoryContract')


@pytest.mark.unit
def test_base_repository_contract_is_abstract():
    """Test BaseRepositoryContract cannot be instantiated"""
    try:
        BaseRepositoryContract()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        pass  # Expected


@pytest.mark.unit
def test_base_repository_contract_has_required_methods():
    """Test BaseRepositoryContract has required abstract methods"""
    assert hasattr(BaseRepositoryContract, 'get')
    assert hasattr(BaseRepositoryContract, 'add')
    assert hasattr(BaseRepositoryContract, 'delete')
    assert hasattr(BaseRepositoryContract, 'commit')
    assert hasattr(BaseRepositoryContract, 'rollback')


@pytest.mark.unit
def test_base_repository_contract_methods_are_abstract():
    """Test BaseRepositoryContract methods are abstract"""
    from abc import ABCMeta

    # Check that the class is abstract
    assert isinstance(BaseRepositoryContract, ABCMeta)

    # Check that methods are abstract
    assert hasattr(BaseRepositoryContract.get, '__isabstractmethod__')
    assert hasattr(BaseRepositoryContract.add, '__isabstractmethod__')
    assert hasattr(BaseRepositoryContract.delete, '__isabstractmethod__')
    assert hasattr(BaseRepositoryContract.commit, '__isabstractmethod__')
    assert hasattr(BaseRepositoryContract.rollback, '__isabstractmethod__')


@pytest.mark.unit
def test_read_repository_contract_is_protocol():
    """Test ReadRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(ReadRepositoryContract, Protocol)


@pytest.mark.unit
def test_read_repository_contract_has_required_methods():
    """Test ReadRepositoryContract has required methods"""
    assert hasattr(ReadRepositoryContract, 'list')
    assert hasattr(ReadRepositoryContract, 'get')


@pytest.mark.unit
def test_write_repository_contract_is_protocol():
    """Test WriteRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(WriteRepositoryContract, Protocol)


@pytest.mark.unit
def test_write_repository_contract_has_required_methods():
    """Test WriteRepositoryContract has required methods"""
    assert hasattr(WriteRepositoryContract, 'add')
    assert hasattr(WriteRepositoryContract, 'delete')
    assert hasattr(WriteRepositoryContract, 'commit')


@pytest.mark.unit
def test_tenant_aware_repository_contract_is_protocol():
    """Test TenantAwareRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(TenantAwareRepositoryContract, Protocol)


@pytest.mark.unit
def test_tenant_aware_repository_contract_has_required_methods():
    """Test TenantAwareRepositoryContract has required methods"""
    assert hasattr(TenantAwareRepositoryContract, 'list_for_tenant')


@pytest.mark.unit
def test_catalog_repository_contract_is_protocol():
    """Test CatalogRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(CatalogRepositoryContract, Protocol)


@pytest.mark.unit
def test_catalog_repository_contract_has_required_methods():
    """Test CatalogRepositoryContract has required methods"""
    assert hasattr(CatalogRepositoryContract, 'list_visible_categories')
    assert hasattr(CatalogRepositoryContract, 'add_category')
    assert hasattr(CatalogRepositoryContract, 'update_category')
    assert hasattr(CatalogRepositoryContract, 'delete_category')
    assert hasattr(CatalogRepositoryContract, 'update_asset_type')
    assert hasattr(CatalogRepositoryContract, 'delete_asset_type')
    assert hasattr(CatalogRepositoryContract, 'update_asset_sector')
    assert hasattr(CatalogRepositoryContract, 'delete_asset_sector')


@pytest.mark.unit
def test_financial_repository_contract_is_protocol():
    """Test FinancialRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(FinancialRepositoryContract, Protocol)


@pytest.mark.unit
def test_financial_repository_contract_has_required_methods():
    """Test FinancialRepositoryContract has required methods"""
    assert hasattr(FinancialRepositoryContract, 'list_transactions')
    assert hasattr(FinancialRepositoryContract, 'get_transaction')
    assert hasattr(FinancialRepositoryContract, 'add_transaction')
    assert hasattr(FinancialRepositoryContract, 'update_transaction')
    assert hasattr(FinancialRepositoryContract, 'delete_transaction')
    assert hasattr(FinancialRepositoryContract, 'list_recurring_plans')
    assert hasattr(FinancialRepositoryContract, 'get_recurring_plan_for_tenant')
    assert hasattr(FinancialRepositoryContract, 'add_recurring_plan')
    assert hasattr(FinancialRepositoryContract, 'create_payment')
    assert hasattr(FinancialRepositoryContract, 'update_recurring_plan')
    assert hasattr(FinancialRepositoryContract, 'delete_plan')
    assert hasattr(FinancialRepositoryContract, 'list_assets')


@pytest.mark.unit
def test_reporting_repository_contract_is_protocol():
    """Test ReportingRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(ReportingRepositoryContract, Protocol)


@pytest.mark.unit
def test_reporting_repository_contract_has_required_methods():
    """Test ReportingRepositoryContract has required methods"""
    assert hasattr(ReportingRepositoryContract, 'get_monthly_balance')
    assert hasattr(ReportingRepositoryContract, 'get_actual_cash')
    assert hasattr(ReportingRepositoryContract, 'get_total_assets')
    assert hasattr(ReportingRepositoryContract, 'get_total_debts')
    assert hasattr(ReportingRepositoryContract, 'get_transactions_by_date_range')
    assert hasattr(ReportingRepositoryContract, 'get_calendar_month_data')
    assert hasattr(ReportingRepositoryContract, 'get_pending_payments')


@pytest.mark.unit
def test_portfolio_repository_contract_is_protocol():
    """Test PortfolioRepositoryContract is a Protocol"""
    from typing import Protocol

    assert issubclass(PortfolioRepositoryContract, Protocol)


@pytest.mark.unit
def test_portfolio_repository_contract_has_required_methods():
    """Test PortfolioRepositoryContract has required methods"""
    assert hasattr(PortfolioRepositoryContract, 'add_asset')
    assert hasattr(PortfolioRepositoryContract, 'update_asset')
    assert hasattr(PortfolioRepositoryContract, 'delete_asset')
    assert hasattr(PortfolioRepositoryContract, 'log_asset_update')
    assert hasattr(PortfolioRepositoryContract, 'get_asset_update_history')
    assert hasattr(PortfolioRepositoryContract, 'bulk_update_assets')


@pytest.mark.unit
def test_base_repository_contract_inherits_from_abc():
    """Test BaseRepositoryContract inherits from ABC"""
    from abc import ABC

    assert issubclass(BaseRepositoryContract, ABC)


@pytest.mark.unit
def test_contracts_use_typing():
    """Test contracts use typing module imports"""
    import repositories.contracts as contracts_module

    # Check that typing imports are available
    assert hasattr(contracts_module, 'Any')
    assert hasattr(contracts_module, 'List')
    assert hasattr(contracts_module, 'Optional')
    assert hasattr(contracts_module, 'Protocol')


@pytest.mark.unit
def test_contracts_from_abc():
    """Test contracts use abc module imports"""
    import repositories.contracts as contracts_module

    # Check that abc imports are available
    assert hasattr(contracts_module, 'ABC')
    assert hasattr(contracts_module, 'abstractmethod')


@pytest.mark.unit
def test_write_repository_contract_has_commit():
    """Test WriteRepositoryContract has commit method"""
    assert hasattr(WriteRepositoryContract, 'commit')


@pytest.mark.unit
def test_read_repository_contract_list_method():
    """Test ReadRepositoryContract list method has signature"""
    import inspect
    sig = inspect.signature(ReadRepositoryContract.list)
    assert sig is not None


@pytest.mark.unit
def test_read_repository_contract_get_method():
    """Test ReadRepositoryContract get method has signature"""
    import inspect
    sig = inspect.signature(ReadRepositoryContract.get)
    assert sig is not None


@pytest.mark.unit
def test_write_repository_contract_add_method():
    """Test WriteRepositoryContract add method has signature"""
    import inspect
    sig = inspect.signature(WriteRepositoryContract.add)
    assert sig is not None


@pytest.mark.unit
def test_write_repository_contract_delete_method():
    """Test WriteRepositoryContract delete method has signature"""
    import inspect
    sig = inspect.signature(WriteRepositoryContract.delete)
    assert sig is not None


@pytest.mark.unit
def test_tenant_aware_repository_contract_list_for_tenant_method():
    """Test TenantAwareRepositoryContract list_for_tenant method has signature"""
    import inspect
    sig = inspect.signature(TenantAwareRepositoryContract.list_for_tenant)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_list_visible_categories_method():
    """Test CatalogRepositoryContract list_visible_categories method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.list_visible_categories)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_add_category_method():
    """Test CatalogRepositoryContract add_category method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.add_category)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_update_category_method():
    """Test CatalogRepositoryContract update_category method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.update_category)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_delete_category_method():
    """Test CatalogRepositoryContract delete_category method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.delete_category)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_update_asset_type_method():
    """Test CatalogRepositoryContract update_asset_type method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.update_asset_type)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_delete_asset_type_method():
    """Test CatalogRepositoryContract delete_asset_type method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.delete_asset_type)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_update_asset_sector_method():
    """Test CatalogRepositoryContract update_asset_sector method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.update_asset_sector)
    assert sig is not None


@pytest.mark.unit
def test_catalog_repository_contract_delete_asset_sector_method():
    """Test CatalogRepositoryContract delete_asset_sector method has signature"""
    import inspect
    sig = inspect.signature(CatalogRepositoryContract.delete_asset_sector)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_list_transactions_method():
    """Test FinancialRepositoryContract list_transactions method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.list_transactions)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_get_transaction_method():
    """Test FinancialRepositoryContract get_transaction method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.get_transaction)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_add_transaction_method():
    """Test FinancialRepositoryContract add_transaction method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.add_transaction)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_update_transaction_method():
    """Test FinancialRepositoryContract update_transaction method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.update_transaction)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_delete_transaction_method():
    """Test FinancialRepositoryContract delete_transaction method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.delete_transaction)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_list_recurring_plans_method():
    """Test FinancialRepositoryContract list_recurring_plans method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.list_recurring_plans)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_get_recurring_plan_for_tenant_method():
    """Test FinancialRepositoryContract get_recurring_plan_for_tenant method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.get_recurring_plan_for_tenant)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_add_recurring_plan_method():
    """Test FinancialRepositoryContract add_recurring_plan method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.add_recurring_plan)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_create_payment_method():
    """Test FinancialRepositoryContract create_payment method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.create_payment)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_update_recurring_plan_method():
    """Test FinancialRepositoryContract update_recurring_plan method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.update_recurring_plan)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_delete_plan_method():
    """Test FinancialRepositoryContract delete_plan method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.delete_plan)
    assert sig is not None


@pytest.mark.unit
def test_financial_repository_contract_list_assets_method():
    """Test FinancialRepositoryContract list_assets method has signature"""
    import inspect
    sig = inspect.signature(FinancialRepositoryContract.list_assets)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_monthly_balance_method():
    """Test ReportingRepositoryContract get_monthly_balance method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_monthly_balance)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_actual_cash_method():
    """Test ReportingRepositoryContract get_actual_cash method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_actual_cash)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_total_assets_method():
    """Test ReportingRepositoryContract get_total_assets method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_total_assets)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_total_debts_method():
    """Test ReportingRepositoryContract get_total_debts method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_total_debts)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_transactions_by_date_range_method():
    """Test ReportingRepositoryContract get_transactions_by_date_range method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_transactions_by_date_range)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_calendar_month_data_method():
    """Test ReportingRepositoryContract get_calendar_month_data method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_calendar_month_data)
    assert sig is not None


@pytest.mark.unit
def test_reporting_repository_contract_get_pending_payments_method():
    """Test ReportingRepositoryContract get_pending_payments method has signature"""
    import inspect
    sig = inspect.signature(ReportingRepositoryContract.get_pending_payments)
    assert sig is not None


@pytest.mark.unit
def test_portfolio_repository_contract_add_asset_method():
    """Test PortfolioRepositoryContract add_asset method has signature"""
    import inspect
    sig = inspect.signature(PortfolioRepositoryContract.add_asset)
    assert sig is not None


@pytest.mark.unit
def test_portfolio_repository_contract_update_asset_method():
    """Test PortfolioRepositoryContract update_asset method has signature"""
    import inspect
    sig = inspect.signature(PortfolioRepositoryContract.update_asset)
    assert sig is not None


@pytest.mark.unit
def test_portfolio_repository_contract_delete_asset_method():
    """Test PortfolioRepositoryContract delete_asset method has signature"""
    import inspect
    sig = inspect.signature(PortfolioRepositoryContract.delete_asset)
    assert sig is not None


@pytest.mark.unit
def test_portfolio_repository_contract_log_asset_update_method():
    """Test PortfolioRepositoryContract log_asset_update method has signature"""
    import inspect
    sig = inspect.signature(PortfolioRepositoryContract.log_asset_update)
    assert sig is not None


@pytest.mark.unit
def test_portfolio_repository_contract_get_asset_update_history_method():
    """Test PortfolioRepositoryContract get_asset_update_history method has signature"""
    import inspect
    sig = inspect.signature(PortfolioRepositoryContract.get_asset_update_history)
    assert sig is not None


@pytest.mark.unit
def test_portfolio_repository_contract_bulk_update_assets_method():
    """Test PortfolioRepositoryContract bulk_update_assets method has signature"""
    import inspect
    sig = inspect.signature(PortfolioRepositoryContract.bulk_update_assets)
    assert sig is not None
