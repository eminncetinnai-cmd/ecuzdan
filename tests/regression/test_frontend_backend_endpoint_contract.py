from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = PROJECT_ROOT / "templates"
STATIC_JS = PROJECT_ROOT / "static" / "js"


def test_api_client_is_loaded_before_page_scoped_scripts():
    layout = (TEMPLATES / "layout.html").read_text(encoding="utf-8")
    assert layout.count("api-client.js") == 1
    assert layout.index("api-client.js") < layout.index("privacy-mode.js")


def test_api_client_exposes_registry_and_dto_contracts():
    api_client = (STATIC_JS / "api-client.js").read_text(encoding="utf-8")
    for marker in (
        "ECuzdanEndpoints",
        "ECuzdanApi",
        "dto",
        "transactions:",
        "notifications:",
        "profileQuestions:",
        "deleteRead",
        "occurrences",
        "occurrencePay",
        "occurrenceSkip",
        "lineage",
        "adjustments",
        "reversal",
        "adjustmentAudit",
        "transactionsReconciliation",
        "reconciliation",
    ):
        assert marker in api_client


def test_asset_delete_frontend_matches_backend_route():
    for name in ("assets.html", "assets_management.html", "assets_view.html"):
        content = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "/del_asset/" not in content
        assert "ECuzdanEndpoints.assets.delete" in content or "assets.new_asset" in content


def test_plan_delete_frontend_uses_canonical_registry_route():
    content = (TEMPLATES / "plans.html").read_text(encoding="utf-8")
    assert "ECuzdanEndpoints.plans.delete(planId)" in content
    assert "`/plans/${planId}/delete`" not in content


def test_notifications_delete_routes_are_registered():
    from app import app

    rules = {str(rule.rule) for rule in app.url_map.iter_rules()}
    assert "/notifications/delete_read" in rules
    assert "/notifications/<int:notification_id>/delete" in rules


def test_core_pages_use_endpoint_registry():
    checks = {
        "financial_education.html": "ECuzdanEndpoints.education",
        "profile_wizard.html": "ECuzdanEndpoints.profile",
        "transactions_explorer.html": "ECuzdanEndpoints.transactions",
        "transactions.html": "ECuzdanEndpoints.transactions",
        "plans.html": "ECuzdanEndpoints.plans",
        "notifications-page.js": "ECuzdanEndpoints.notifications",
        "monitoring.js": "ECuzdanEndpoints",
    }
    for name, marker in checks.items():
        path = TEMPLATES / name if name.endswith(".html") else STATIC_JS / name
        assert marker in path.read_text(encoding="utf-8")
