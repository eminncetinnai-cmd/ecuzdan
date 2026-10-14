from decimal import Decimal
from types import SimpleNamespace

from domain.portfolio.services.asset_service import AssetService


class FakeFinancialRepository:
    def __init__(self, assets):
        self.assets = assets
        self.received_tenant_id = None

    def list_assets(self, tenant_id=None):
        self.received_tenant_id = tenant_id
        return self.assets


class UnusedCatalogRepository:
    pass


def _asset(*, value, currency, is_closed=False, last_updated=None):
    return SimpleNamespace(
        value=value,
        currency=currency,
        is_closed=is_closed,
        last_updated=last_updated,
    )


def test_portfolio_snapshot_is_tenant_scoped_and_keeps_currencies_separate():
    repository = FakeFinancialRepository([
        _asset(value=Decimal("100.00"), currency="TRY", last_updated="2026-08-23"),
        _asset(value=Decimal("20.50"), currency="USD", last_updated="2026-08-24"),
        _asset(value=Decimal("999.00"), currency="TRY", is_closed=True, last_updated="2026-08-25"),
    ])
    service = AssetService(financial_repository=repository, catalog_repository=UnusedCatalogRepository())

    snapshot = service.portfolio_snapshot_context("tenant-a")

    assert repository.received_tenant_id == "tenant-a"
    assert snapshot == {
        "asset_count": 2,
        "closed_asset_count": 1,
        "currency_count": 2,
        "currency_totals": {"TRY": "100.00", "USD": "20.50"},
        "last_valuation_date": "2026-08-24",
        "valuation_basis": "persisted_asset_value",
        "market_marked": False,
    }


def test_portfolio_snapshot_handles_empty_assets_without_fabricating_value():
    repository = FakeFinancialRepository([])
    service = AssetService(financial_repository=repository, catalog_repository=UnusedCatalogRepository())

    snapshot = service.portfolio_snapshot_context("tenant-empty")

    assert snapshot["asset_count"] == 0
    assert snapshot["closed_asset_count"] == 0
    assert snapshot["currency_count"] == 0
    assert snapshot["currency_totals"] == {}
    assert snapshot["last_valuation_date"] is None
    assert snapshot["market_marked"] is False
