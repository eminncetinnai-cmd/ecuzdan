"""Unit tests for Gold Tracking (Harem Altın & Bursa Kuyumcular Çarşısı) feature."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from application.analysis.queries.get_gold_tracking_overview import GetGoldTrackingOverviewQuery
from domain.analysis.services.gold_tracking_service import (
    DERIVATIVE_SPECS,
    GoldTrackingService,
    _parse_change_pct,
    fetch_harem_doviz_table,
    fetch_truncgil_fallback,
)


def test_parse_change_pct():
    """Test parsing of Turkish percentage change strings."""
    assert _parse_change_pct("%-0,16") == Decimal("-0.16")
    assert _parse_change_pct("%+1,25") == Decimal("1.25")
    assert _parse_change_pct("0,45") == Decimal("0.45")
    assert _parse_change_pct("") == Decimal("0.00")
    assert _parse_change_pct(None) == Decimal("0.00")


def test_fetch_harem_doviz_table_parses_html():
    """Test Tier 1 Harem Altın HTML table parser with realistic rows."""
    sample_html = """
    <html><body>
    <table>
        <tr><td>Ons Altın</td><td>$4.796,70</td><td>$4.797,30</td><td>%-0,57</td><td>09:44</td></tr>
        <tr><td>Gram Altın</td><td>6.921,16</td><td>6.970,38</td><td>%-0,16</td><td>09:43</td></tr>
        <tr><td>Çeyrek Altın</td><td>11.339,00</td><td>11.425,00</td><td>%-0,19</td><td>09:43</td></tr>
        <tr><td>Eski Çeyrek Altın</td><td>11.130,00</td><td>11.216,00</td><td>%-0,19</td><td>09:43</td></tr>
        <tr><td>22 Ayar Bilezik</td><td>6.327,99</td><td>6.597,65</td><td>%-0,17</td><td>09:43</td></tr>
        <tr><td>Gram Gümüş</td><td>111,64</td><td>115,61</td><td>%-0,82</td><td>09:43</td></tr>
    </table>
    </body></html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = sample_html
    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    parsed = fetch_harem_doviz_table(session=mock_session)

    assert "gram_altin" in parsed
    assert parsed["gram_altin"]["buy"] == Decimal("6921.16")
    assert parsed["gram_altin"]["sell"] == Decimal("6970.38")
    assert parsed["gram_altin"]["change_pct"] == Decimal("-0.16")
    assert parsed["ceyrek_yeni"]["buy"] == Decimal("11339.00")
    assert parsed["ceyrek_eski"]["buy"] == Decimal("11130.00")
    assert parsed["bilezik_22"]["buy"] == Decimal("6327.99")
    assert parsed["gumus_gram"]["sell"] == Decimal("115.61")


def test_fetch_truncgil_fallback_parses_json():
    """Test Tier 2 Truncgil v4 JSON fallback parser."""
    sample_json = {
        "GRA": {"Buying": 6917.87, "Selling": 6980.02, "Change": -0.22},
        "CEYREKALTIN": {"Buying": 11339.0, "Selling": 11425.0, "Change": -0.19},
        "YARIMALTIN": {"Buying": 22678.0, "Selling": 22851.0, "Change": -0.19},
        "TAMALTIN": {"Buying": 45216.0, "Selling": 45549.0, "Change": -0.18},
        "ONS": {"Buying": 4796.7, "Selling": 4797.3, "Change": -0.57},
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_json
    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    parsed = fetch_truncgil_fallback(session=mock_session)

    assert parsed["gram_altin"]["buy"] == Decimal("6917.87")
    assert parsed["ceyrek_yeni"]["sell"] == Decimal("11425.00")
    assert parsed["ons_altin"]["buy"] == Decimal("4796.70")


def test_calibrated_multiplier_fallback_and_bursa_margin_presets():
    """Test Tier 3 calibrated Harem multiplier engine and Bursa margin presets."""
    service = GoldTrackingService()
    mock_fx = MagicMock()
    mock_fx.values = {"gold": "6950.00"}

    with (
        patch("domain.analysis.services.gold_tracking_service.fetch_harem_doviz_table", side_effect=RuntimeError("down")),
        patch("domain.analysis.services.gold_tracking_service.fetch_truncgil_fallback", side_effect=RuntimeError("down")),
        patch(
            "domain.analysis.services.gold_tracking_service.fetch_resilient_live_quotes",
            return_value=mock_fx,
        ),
    ):
        snap_harem = service.get_snapshot(preset_key="bursa_harem", force_refresh=True)
        snap_carsi = service.get_snapshot(preset_key="bursa_carsi", force_refresh=False)
        snap_vitrin = service.get_snapshot(preset_key="bursa_vitrin", force_refresh=False)

    assert len(snap_harem.quotes) == len(DERIVATIVE_SPECS)
    assert snap_harem.source == "calibrated_harem_formula"
    assert snap_harem.fallback_used is True

    # Verify calibrated Yeni Çeyrek is ~1.6383x Gram buy (~11,323 TL)
    ceyrek_harem = next(q for q in snap_harem.quotes if q.code == "ceyrek_yeni")
    assert Decimal("11250") <= ceyrek_harem.buy_price <= Decimal("11450")
    assert ceyrek_harem.sell_price > ceyrek_harem.buy_price

    # Verify Bursa Çarşı preset widens spread (lower buy, higher sell) compared to Harem 0%
    ceyrek_carsi = next(q for q in snap_carsi.quotes if q.code == "ceyrek_yeni")
    ceyrek_vitrin = next(q for q in snap_vitrin.quotes if q.code == "ceyrek_yeni")
    assert ceyrek_carsi.buy_price < ceyrek_harem.buy_price
    assert ceyrek_carsi.sell_price > ceyrek_harem.sell_price
    assert ceyrek_vitrin.buy_price < ceyrek_carsi.buy_price
    assert ceyrek_vitrin.sell_price > ceyrek_carsi.sell_price

    # Verify non-TL quotes (ons_altin) are NOT adjusted by Bursa retail margin
    ons_harem = next(q for q in snap_harem.quotes if q.code == "ons_altin")
    ons_carsi = next(q for q in snap_carsi.quotes if q.code == "ons_altin")
    assert ons_harem.buy_price == ons_carsi.buy_price


def test_get_gold_tracking_overview_query():
    """Test Application Query serialization and spotlight cards."""
    mock_service = GoldTrackingService()
    mock_fx = MagicMock()
    mock_fx.values = {"gold": "6950.00"}

    with (
        patch("domain.analysis.services.gold_tracking_service.fetch_harem_doviz_table", side_effect=RuntimeError("down")),
        patch("domain.analysis.services.gold_tracking_service.fetch_truncgil_fallback", side_effect=RuntimeError("down")),
        patch(
            "domain.analysis.services.gold_tracking_service.fetch_resilient_live_quotes",
            return_value=mock_fx,
        ),
    ):
        query = GetGoldTrackingOverviewQuery(service=mock_service)
        payload = query.execute(preset_key="bursa_harem", force_refresh=True)

    assert "quotes" in payload
    assert "spotlight" in payload
    assert "categories" in payload
    assert "presets" in payload
    assert len(payload["quotes"]) == 17
    assert len(payload["spotlight"]) == 6
    assert payload["preset_key"] == "bursa_harem"


def test_gold_tracking_routes_unauthenticated(client):
    """Test that unauthenticated requests redirect to login."""
    res = client.get("/gold-tracking")
    assert res.status_code in (302, 401)


def test_gold_tracking_routes_authenticated(authenticated_client):
    """Test HTML dashboard and JSON API endpoint with authenticated client."""
    res = authenticated_client.get("/gold-tracking?preset=bursa_carsi")
    assert res.status_code == 200
    assert "Altın Takip" in res.text
    assert "Harem Altın" in res.text
    assert "Kuyumcu Bozdurma" in res.text

    api_res = authenticated_client.get("/gold-tracking/api/quotes?preset=bursa_harem")
    assert api_res.status_code == 200
    json_data = api_res.get_json()
    assert json_data["success"] is True
    assert len(json_data["data"]["quotes"]) == 17
