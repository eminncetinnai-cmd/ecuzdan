"""Regression tests for the investor profile wizard CSRF contract."""

import pytest


@pytest.mark.integration
def test_profile_wizard_exposes_csrf_meta_and_submit_header(authenticated_client):
    """The wizard must expose the session token and send it on JSON submit."""
    with authenticated_client.session_transaction() as session:
        session['csrf_token'] = 'profile-test-csrf-token'

    response = authenticated_client.get('/profile/start')

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'name="csrf-token" content="profile-test-csrf-token"' in html
    assert "'X-CSRF-Token': document.querySelector('meta[name=\"csrf-token\"]')" in html


@pytest.mark.integration
def test_profile_submit_with_session_token_is_not_rejected_by_csrf(app, authenticated_client):
    """A valid header must pass CSRF middleware before endpoint validation."""
    app.config['TESTING'] = False
    try:
        with authenticated_client.session_transaction() as session:
            session['csrf_token'] = 'profile-test-csrf-token'

        response = authenticated_client.post(
            '/profile/api/submit',
            json={'answers': []},
            headers={'X-CSRF-Token': 'profile-test-csrf-token'},
        )

        assert b'CSRF verification failed' not in response.data
    finally:
        app.config['TESTING'] = True

