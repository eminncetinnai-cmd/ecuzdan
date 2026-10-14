from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import g

from domain.reporting.services.dashboard_service import DashboardService
from routes.dashboard import _dashboard_currency_context
from shared.currency_precision import get_currency_symbol


class FakeFinancialRepository:
    def __init__(self, transactions_by_tenant=None, assets_by_tenant=None):
        self.transactions_by_tenant = transactions_by_tenant or {}
        self.assets_by_tenant = assets_by_tenant or {}
        self.transaction_calls: list[str | None] = []
        self.asset_calls: list[str | None] = []

    def list_transactions(self, tenant_id=None):
        self.transaction_calls.append(tenant_id)
        return list(self.transactions_by_tenant.get(tenant_id, []))

    def list_assets(self, tenant_id=None):
        self.asset_calls.append(tenant_id)
        return list(self.assets_by_tenant.get(tenant_id, []))


class FakeCatalogRepository:
    def __init__(self, categories_by_tenant=None):
        self.categories_by_tenant = categories_by_tenant or {}
        self.calls: list[str | None] = []

    def list_visible_categories(self, tenant_id=None):
        self.calls.append(tenant_id)
        return list(self.categories_by_tenant.get(tenant_id, []))


def make_transaction(
    date,
    type_,
    amount,
    status="Ödendi",
    tenant_id="tenant-a",
    category="Maaş",
    origin="Manuel",
):
    return SimpleNamespace(
        date=date,
        type=type_,
        amount=Decimal(str(amount)),
        status=status,
        tenant_id=tenant_id,
        category=category,
        origin=origin,
        description=f"{type_} test",
        transfer_from="Nakit" if type_ == "Transfer" else None,
        transfer_to="Yatırım" if type_ == "Transfer" else None,
    )


def make_asset(type_, value, tenant_id="tenant-a", is_closed=False):
    return SimpleNamespace(
        type=type_,
        value=Decimal(str(value)),
        tenant_id=tenant_id,
        is_closed=is_closed,
    )


@pytest.mark.unit
@pytest.mark.financial
def test_dashboard_context_is_tenant_scoped_and_aggregates_open_assets():
    now = datetime(2026, 8, 25)
    tenant_a_transactions = [
        make_transaction("2026-08-01", "Gelir", 1000, category="Maaş"),
        make_transaction("2026-08-02", "Gider", 200, category="Kira"),
        make_transaction("2026-08-03", "Yatırım", 100, category="Yatırım"),
        make_transaction("2026-08-04", "Transfer", 500, category="Transfer"),
        make_transaction("2026-08-26", "Gider", 50, status="Bekliyor", category="Kira"),
        make_transaction("2026-08-27", "Yatırım", 30, status="Bekliyor", category="Yatırım"),
    ]
    tenant_b_transactions = [
        make_transaction("2026-08-01", "Gelir", 999999, tenant_id="tenant-b")
    ]
    repository = FakeFinancialRepository(
        transactions_by_tenant={
            "tenant-a": tenant_a_transactions,
            "tenant-b": tenant_b_transactions,
        },
        assets_by_tenant={
            "tenant-a": [
                make_asset("Hisse Senedi", 1000),
                make_asset("Hisse Senedi", 500),
                make_asset("Altın", 999, is_closed=True),
            ],
            "tenant-b": [make_asset("Altın", 9000, tenant_id="tenant-b")],
        },
    )
    catalog = FakeCatalogRepository({"tenant-a": []})
    service = DashboardService(repository, catalog)

    context = service.index_context("tenant-a", now=now)

    # 1000 - 200 - 100; Transfer 500 is excluded from cash flow.
    assert context["today_cash"] == Decimal("700")
    assert context["paid_investment_transfers"] == Decimal("100")
    assert context["pending_investment_transfers"] == Decimal("30")
    assert context["pending_year_cash"] == Decimal("-80")
    assert context["investment_ratio"] == Decimal("10.00")

    # Only open assets from tenant-a are included in total and type breakdown.
    assert context["total_asset_value"] == Decimal("1500")
    assert context["net_worth"] == Decimal("2200")
    assert context["open_asset_count"] == 2
    assert context["asset_labels"] == '["Hisse Senedi"]'
    assert context["asset_values"] == "[1500.0]"
    assert context["cash_pct"] == 31.8
    assert context["investment_pct"] == 68.2

    assert len(context["week_labels"].strip("[]").split(",")) == 7
    assert len(context["week_data"].strip("[]").split(",")) == 7
    assert len(context["month_labels"].strip("[]").split(",")) == 7
    assert len(context["month_data"].strip("[]").split(",")) == 7
    assert repository.transaction_calls == ["tenant-a"]
    assert repository.asset_calls == ["tenant-a"]
    assert catalog.calls == ["tenant-a"]


@pytest.mark.unit
@pytest.mark.financial
@pytest.mark.parametrize(
    ("transactions", "expected_cash", "expected_net_worth"),
    [
        ([], Decimal("0"), Decimal("0")),
        (
            [make_transaction("2026-02-01", "Gider", 100)],
            Decimal("-100"),
            Decimal("-100"),
        ),
    ],
)
def test_dashboard_context_handles_zero_and_negative_net_worth(
    transactions, expected_cash, expected_net_worth
):
    repository = FakeFinancialRepository(
        transactions_by_tenant={"tenant-a": transactions},
        assets_by_tenant={"tenant-a": []},
    )
    service = DashboardService(repository, FakeCatalogRepository({"tenant-a": []}))

    context = service.index_context("tenant-a", now=datetime(2026, 2, 10))

    assert context["today_cash"] == expected_cash
    assert context["net_worth"] == expected_net_worth
    assert context["total_asset_value"] == Decimal("0")
    assert context["cash_pct"] == 0.0
    assert context["investment_pct"] == 0.0
    assert len(context["week_labels"].strip("[]").split(",")) == 7
    assert len(context["week_data"].strip("[]").split(",")) == 7
    assert len(context["month_labels"].strip("[]").split(",")) == 19
    assert len(context["month_data"].strip("[]").split(",")) == 19


@pytest.mark.unit
def test_dashboard_currency_context_prioritizes_user_then_tenant_then_try(app):
    with app.app_context():
        g.current_user = SimpleNamespace(
            base_currency="USD",
            tenant=SimpleNamespace(base_currency="EUR"),
        )
        user_context = _dashboard_currency_context()
        assert user_context["dashboard_currency_code"] == "USD"
        assert user_context["dashboard_currency_symbol"] == get_currency_symbol("USD")

        g.current_user = SimpleNamespace(
            base_currency=None,
            tenant=SimpleNamespace(base_currency="EUR"),
        )
        tenant_context = _dashboard_currency_context()
        assert tenant_context["dashboard_currency_code"] == "EUR"
        assert tenant_context["dashboard_currency_symbol"] == get_currency_symbol("EUR")

        g.current_user = SimpleNamespace(base_currency=None, tenant=None)
        fallback_context = _dashboard_currency_context()
        assert fallback_context["dashboard_currency_code"] == "TRY"
        assert fallback_context["dashboard_currency_symbol"] == get_currency_symbol("TRY")
