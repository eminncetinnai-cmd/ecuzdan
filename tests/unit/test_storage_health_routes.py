from unittest.mock import Mock

import pytest
from flask import Blueprint, Flask

from routes.storage_health import register_storage_health_routes, storage_health_bp


@pytest.fixture
def isolated_storage_health_app(tmp_path):
    auth_bp = Blueprint("auth", __name__)

    @auth_bp.get("/login")
    def login():
        return "login"

    app = Flask(
        __name__,
        template_folder=str(tmp_path),
        static_folder=str(tmp_path),
    )
    app.secret_key = "storage-health-route-test"
    app.register_blueprint(auth_bp)
    register_storage_health_routes(storage_health_bp)
    app.register_blueprint(storage_health_bp)
    app.config.update(TESTING=True)
    return app


@pytest.mark.unit
def test_storage_health_routes_are_read_only_and_isolated(isolated_storage_health_app):
    rules = [
        rule
        for rule in isolated_storage_health_app.url_map.iter_rules()
        if rule.rule.startswith("/storage-health")
    ]

    assert {rule.rule for rule in rules} == {
        "/storage-health/",
        "/storage-health/api/overview",
        "/storage-health/api/cleanup",
        "/storage-health/api/db-health",
        "/storage-health/api/tune-up",
        "/storage-health/api/history",
    }


@pytest.mark.unit
def test_storage_health_unauthenticated_requests_redirect_to_login(isolated_storage_health_app):
    with isolated_storage_health_app.test_client() as client:
        page = client.get("/storage-health/")
        overview = client.get("/storage-health/api/overview")

    assert page.status_code in {302, 303}
    assert overview.status_code in {302, 303}
    assert "/login" in page.headers.get("Location", "")
    assert "/login" in overview.headers.get("Location", "")


@pytest.mark.unit
def test_storage_health_authorized_get_returns_standard_read_only_payload(isolated_storage_health_app, monkeypatch):
    class FullAccessUser:
        is_super_admin = True
        role = "sistem_yoneticisi"

    payload = {
        "mode": "OBSERVE_RECOMMEND",
        "read_only": True,
        "execute_available": False,
        "mutation_performed": False,
        "security_log_retention_preview": {
            "decision": "hold",
            "cleanup_eligibility": "never",
            "reason": "security_audit_retention_policy_pending",
            "retention_days": None,
            "mutation_performed": False,
        },
    }
    service = Mock()
    service.get_overview.return_value = payload
    monkeypatch.setattr("utils.auth_helpers.db.session.get", lambda *args, **kwargs: FullAccessUser())
    monkeypatch.setattr("routes.storage_health._get_service", lambda: service)

    with isolated_storage_health_app.test_client() as client:
        with client.session_transaction() as client_session:
            client_session["user_id"] = 1
        response = client.get("/storage-health/api/overview")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["read_only"] is True
    assert body["data"]["execute_available"] is False
    assert body["data"]["mutation_performed"] is False
    preview = body["data"]["security_log_retention_preview"]
    assert preview["decision"] == "hold"
    assert preview["cleanup_eligibility"] == "never"
    assert preview["retention_days"] is None
    assert preview["mutation_performed"] is False
    service.get_overview.assert_called_once_with(refresh=False)


@pytest.mark.unit
def test_storage_health_does_not_expose_state_changing_route(isolated_storage_health_app):
    with isolated_storage_health_app.test_client() as client:
        assert client.post("/storage-health/api/overview").status_code == 405
        assert client.delete("/storage-health/api/overview").status_code == 405
