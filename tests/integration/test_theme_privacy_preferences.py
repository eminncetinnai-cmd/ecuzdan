"""Regression tests for persistent theme and privacy preferences."""

from models import UserPreference


def _csrf(client):
    with client.session_transaction() as session:
        return session.get("csrf_token", "")


def test_theme_preference_endpoint_persists(authenticated_client, test_user):
    response = authenticated_client.post(
        "/save_theme_preference",
        data={"theme": "dark", "csrf_token": _csrf(authenticated_client)},
    )

    assert response.status_code == 200
    assert response.get_json() == {"success": True, "theme": "dark"}
    preference = UserPreference.query.filter_by(user_id=test_user.id).first()
    assert preference is not None
    assert preference.theme == "dark"


def test_privacy_toggle_endpoint_honors_explicit_state(authenticated_client, test_user):
    response = authenticated_client.post(
        "/toggle_privacy_mode",
        data={"privacy_mode": "on", "csrf_token": _csrf(authenticated_client)},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert response.get_json()["privacy_mode"] is True
    preference = UserPreference.query.filter_by(user_id=test_user.id).first()
    assert preference is not None
    assert preference.privacy_mode is True


def test_layout_renders_canonical_light_and_privacy_attributes(authenticated_client):
    response = authenticated_client.get("/settings")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'data-user-theme="light"' in body
    assert 'data-privacy-mode="false"' in body
    assert "data-privacy-control" in body
    assert "privacy-mode-preference-card" in body


def test_settings_privacy_form_persists_true_state(authenticated_client):
    response = authenticated_client.post(
        "/settings",
        data={
            "action": "set_privacy_mode",
            "privacy_mode": "on",
            "csrf_token": _csrf(authenticated_client),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'data-privacy-mode="true"' in body
    assert "privacy-mode-preference-card" in body
