from types import SimpleNamespace
from unittest.mock import patch

import pytest
from flask import session

from utils.auth_helpers import login_required, require_role


@pytest.mark.regression
def test_login_required_redirects_anonymous_user(app):
    @login_required
    def protected():
        return "protected"

    with app.test_request_context("/protected"):
        response = protected()

    assert response.status_code == 302
    assert response.location.endswith("/login")


@pytest.mark.regression
def test_login_required_allows_authenticated_session(app):
    @login_required
    def protected():
        return "protected"

    with app.test_request_context("/protected"):
        session["user_id"] = 123
        assert protected() == "protected"


@pytest.mark.regression
def test_require_role_redirects_user_without_required_role(app):
    @require_role("tenant_admin")
    def protected():
        return "protected"

    with app.test_request_context("/protected"):
        session["user_id"] = 123
        with patch(
            "utils.auth_helpers.db.session.get",
            return_value=SimpleNamespace(role="kullanici"),
        ):
            response = protected()

    assert response.status_code == 302
    assert response.location.endswith("/")


@pytest.mark.regression
def test_require_role_allows_required_role(app):
    @require_role("tenant_admin")
    def protected():
        return "protected"

    with app.test_request_context("/protected"):
        session["user_id"] = 123
        with patch(
            "utils.auth_helpers.db.session.get",
            return_value=SimpleNamespace(role="tenant_admin"),
        ):
            assert protected() == "protected"


@pytest.mark.regression
@pytest.mark.parametrize(
    "path",
    ["/transactions", "/plans", "/assets", "/notifications", "/monitoring/"],
)
def test_financial_pages_do_not_allow_anonymous_access(client, path):
    response = client.get(path, follow_redirects=False)

    assert response.status_code in {301, 302, 303, 308, 401, 403}
