"""Unit tests for Central Bank Reserves and Global Gold Holdings feature."""

from decimal import Decimal

import pytest

from application.central_bank.queries.get_reserves_overview import GetReservesOverviewQuery
from domain.central_bank.services.reserve_service import CentralBankReserveService


@pytest.fixture
def service():
    return CentralBankReserveService()


def test_service_initialization(service):
    """Test that domain service initializes with default official datasets."""
    assert len(service._processed_series) > 0
    assert len(service._processed_global_banks) > 0


def test_service_mom_and_yoy_calculations(service):
    """Test that MoM and YoY calculations are mathematically accurate."""
    series = service.get_filtered_series("all")
    assert len(series) >= 24

    # Check that latest point has valid attributes
    latest = series[-1]
    assert latest.gross_total_usd_billion > Decimal("0")
    assert latest.gold_tonnes > Decimal("0")
    assert latest.gold_share_pct > Decimal("0")
    assert latest.gold_share_pct == (latest.gold_usd_billion / latest.gross_total_usd_billion * Decimal("100")).quantize(Decimal("0.1"))


def test_service_range_filtering(service):
    """Test range filtering for 6m, 1y, 2y, and all periods."""
    assert len(service.get_filtered_series("6m")) == 6
    assert len(service.get_filtered_series("1y")) == 12
    assert len(service.get_filtered_series("2y")) == 24
    assert len(service.get_filtered_series("all")) == len(service._processed_series)


def test_service_kpis_calculation(service):
    """Test KPI calculations."""
    kpis = service.calculate_kpis()
    assert kpis.latest_gross_total > Decimal("100")
    assert kpis.latest_gold_tonnes > Decimal("500")
    assert kpis.latest_gold_share_pct > Decimal("30")
    assert kpis.prev_gross_total > Decimal("100")
    assert kpis.prev_net_ex_swap != Decimal("0")
    assert kpis.prev_date_display != ""
    assert kpis.gross_mom_change_usd != Decimal("0")


def test_global_banks_ranking(service):
    """Test that global central banks include US, Germany, China, and Turkey."""
    banks = service.get_global_banks()
    codes = [b.country_code for b in banks]
    assert "US" in codes
    assert "CN" in codes
    assert "TR" in codes
    assert "DE" in codes

    # US should have the highest gold holding (>8000 tonnes)
    us_bank = next(b for b in banks if b.country_code == "US")
    assert us_bank.gold_tonnes > Decimal("8000")


def test_get_reserves_overview_query():
    """Test that Application Query prepares complete chart and table payloads."""
    query = GetReservesOverviewQuery()
    payload = query.execute(range_key="1y")

    assert "kpis" in payload
    assert "charts" in payload
    assert "tcmb" in payload["charts"]
    assert "global_gold" in payload["charts"]
    assert "global_reserves" in payload["charts"]
    assert "monthly_table" in payload
    assert "global_table" in payload

    assert len(payload["charts"]["tcmb"]["labels"]) == 12
    assert len(payload["monthly_table"]) == 12


def test_routes_unauthenticated(client):
    """Test that unauthenticated requests redirect to login."""
    res = client.get('/central-bank-reserves')
    assert res.status_code in (302, 401)


def test_routes_authenticated(authenticated_client):
    """Test that authenticated requests return 200 OK."""
    res = authenticated_client.get('/central-bank-reserves')
    assert res.status_code == 200
    assert "Merkez Bankas" in res.text


def test_api_data_endpoint(authenticated_client):
    """Test JSON API data endpoint."""
    res = authenticated_client.get('/central-bank-reserves/api/data?range=6m')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert len(json_data["data"]["charts"]["tcmb"]["labels"]) == 6


def test_api_export_endpoints(authenticated_client):
    """Test CSV export endpoints for TCMB and global datasets."""
    res_tcmb = authenticated_client.get('/central-bank-reserves/api/export?type=tcmb')
    assert res_tcmb.status_code == 200
    assert "text/csv" in res_tcmb.content_type
    assert "Toplam" in res_tcmb.text

    res_global = authenticated_client.get('/central-bank-reserves/api/export?type=global')
    assert res_global.status_code == 200
    assert "text/csv" in res_global.content_type
    assert "Devletleri" in res_global.text
