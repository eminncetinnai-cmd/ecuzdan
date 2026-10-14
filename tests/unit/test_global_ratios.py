"""Unit tests for Global Macro & Financial Ratios feature."""

from decimal import Decimal

from application.ratios.queries.get_ratios_dashboard import GetRatiosDashboardQuery
from domain.ratios.data.historical_ratios_data import get_all_ratio_definitions
from domain.ratios.entities.ratio_models import RatioCategory, SignalStatus
from domain.ratios.services.ratio_service import MacroRatioService


class TestGlobalMacroRatios:
    """Unit tests for domain and application layers of global macro ratios."""

    def test_twenty_ratio_definitions_exist(self):
        """Ensure exactly 20 world-renowned ratio definitions are present and valid."""
        definitions = get_all_ratio_definitions()
        assert len(definitions) == 20

        codes = [d.code for d in definitions]
        assert len(set(codes)) == 20, "All ratio codes must be unique"

        for d in definitions:
            assert len(d.series) >= 24, f"Ratio {d.code} must have at least 24 monthly data points"
            assert d.normal_min <= d.normal_max, f"Ratio {d.code} normal_min must be <= normal_max"

    def test_ratio_service_dashboard_calculations(self):
        """Test calculation of MoM, YoY, signals and categories in MacroRatioService."""
        service = MacroRatioService()
        dashboard = service.build_dashboard(range_key="all")

        assert dashboard.total_ratios == 20
        assert dashboard.healthy_count + dashboard.neutral_count + dashboard.elevated_count == 20
        assert len(dashboard.ratios) == 20
        assert "2026" in dashboard.latest_period_display

        # Verify a specific ratio (e.g. buffett_indicator)
        buffett = next(r for r in dashboard.ratios if r.code == "buffett_indicator")
        assert buffett.latest_value == Decimal("195.8")
        assert buffett.unit == "%"
        assert buffett.signal_status == SignalStatus.ELEVATED

    def test_ratio_service_timeframe_filtering(self):
        """Test range key filtering ('6m', '1y', '2y', 'all')."""
        service = MacroRatioService()

        dash_6m = service.build_dashboard(range_key="6m")
        assert len(dash_6m.ratios[0].series) == 6

        dash_1y = service.build_dashboard(range_key="1y")
        assert len(dash_1y.ratios[0].series) == 12

        dash_2y = service.build_dashboard(range_key="2y")
        assert len(dash_2y.ratios[0].series) == 24

    def test_ratio_service_category_filtering(self):
        """Test category filtering."""
        service = MacroRatioService()
        dash_commodities = service.build_dashboard(category_filter=RatioCategory.COMMODITIES.value)
        assert dash_commodities.total_ratios == 4
        for r in dash_commodities.ratios:
            assert r.category == RatioCategory.COMMODITIES

    def test_application_query_payload_formatting(self):
        """Test GetRatiosDashboardQuery formatting for Chart.js and templates."""
        query = GetRatiosDashboardQuery()
        result = query.execute(range_key="1y")

        assert "kpis" in result
        assert "ratios" in result
        assert len(result["ratios"]) == 20
        assert "pulse" in result
        assert "vix" in result["pulse"]
        assert "yield_curve" in result["pulse"]
        assert "category_summaries" in result
        assert len(result["category_summaries"]) == 5
        assert "correlation_matrix" in result
        assert "grid" in result["correlation_matrix"]
        assert "executive_briefing" in result

        first_ratio = result["ratios"][0]
        assert "chart_data" in first_ratio
        assert len(first_ratio["chart_data"]["labels"]) == 12
        assert len(first_ratio["chart_data"]["values"]) == 12
        assert len(first_ratio["chart_data"]["normal_min_line"]) == 12


class TestGlobalRatiosEndpoints:
    """Integration smoke tests for HTTP route dispatches."""

    def test_global_ratios_routes(self, client):
        """Test /global-ratios, /global-ratios/api/data, and /global-ratios/api/export."""
        # Unauthenticated redirects to login
        res = client.get('/global-ratios')
        assert res.status_code == 302
        assert '/login' in res.location

        # With mock session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'admin'
            sess['username'] = 'admin'
            sess['tenant_id'] = 1
            sess['session_id'] = 'test-session-id'

        # Main view
        res_view = client.get('/global-ratios')
        assert res_view.status_code == 200
        assert b"K\xc3\xbcresel Finansal &amp; Makro Rasyolar" in res_view.data or b"K\xc3\xbcresel Finansal & Makro Rasyolar" in res_view.data

        # API data endpoint
        res_api = client.get('/global-ratios/api/data?range=1y')
        assert res_api.status_code == 200
        json_data = res_api.get_json()
        assert json_data['success'] is True
        assert len(json_data['data']['ratios']) == 20

        # Correlation API
        res_corr = client.get('/global-ratios/api/correlation')
        assert res_corr.status_code == 200
        assert res_corr.get_json()['success'] is True

        # Briefing API
        res_brief = client.get('/global-ratios/api/briefing')
        assert res_brief.status_code == 200
        assert res_brief.get_json()['success'] is True

        # Alerts config API
        res_alert = client.post('/global-ratios/api/alerts/config', json={'enabled': True})
        assert res_alert.status_code == 200
        assert res_alert.get_json()['success'] is True

        # Export CSV endpoint
        res_csv = client.get('/global-ratios/api/export')
        assert res_csv.status_code == 200
        assert 'text/csv' in res_csv.content_type
        assert b'buffett_indicator' in res_csv.data
