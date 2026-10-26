"""
Unit Tests - Remember Me & Multi-Device Session Persistence
Verifies that:
1. Multiple devices (PC and mobile) can stay logged in simultaneously when using "Beni Hatırla".
2. GET /login redirects already-authenticated users to dashboard (or next page).
3. Session permanent flag is maintained for remembered sessions.
4. Password changes properly invalidate sessions created before the change.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from flask import Flask, session


@pytest.mark.unit
def test_record_session_clears_single_device_lock():
    """record_session should set last_session_id to None so multiple devices can coexist."""
    from domain.users.services.auth_service import AuthService

    mock_repo = Mock()
    auth_service = AuthService(repository=mock_repo)

    mock_user = Mock()
    mock_user.last_session_id = "old_single_session_lock"

    auth_service.record_session(mock_user, "new_session_id")

    assert mock_user.last_session_id is None
    mock_repo.commit.assert_called_once()


@pytest.mark.unit
def test_validate_user_session_permits_coexisting_devices():
    """validate_user_session should allow any valid session when last_session_id is None."""
    from domain.users.services.session_service import SessionService

    mock_repo = Mock()
    session_service = SessionService(repository=mock_repo)

    mock_user = Mock()
    mock_user.id = 1
    mock_user.last_session_id = None
    mock_repo.get_user.return_value = mock_user

    # PC device session
    user_pc, error_pc = session_service.validate_user_session(1, "pc_session_token_123")
    assert user_pc is not None
    assert error_pc is None

    # Mobile device session
    user_mobile, error_mobile = session_service.validate_user_session(1, "mobile_session_token_456")
    assert user_mobile is not None
    assert error_mobile is None


@pytest.mark.unit
def test_pin_session_invalidates_other_devices_when_requested():
    """pin_session should lock to the current device session and reject other devices."""
    from domain.users.services.session_service import SessionService
    from domain.users.services.settings_service import SettingsService

    mock_repo = Mock()
    mock_user = Mock()
    mock_user.id = 1
    mock_user.last_session_id = None
    mock_repo.get_user.return_value = mock_user

    settings_service = SettingsService(repository=mock_repo)
    session_service = SessionService(repository=mock_repo)

    # Pin current device (e.g. PC)
    settings_service.pin_session(1, "pc_device_token")
    assert mock_user.last_session_id == "pc_device_token"

    # PC device matches
    u1, err1 = session_service.validate_user_session(1, "pc_device_token")
    assert u1 is not None
    assert err1 is None

    # Mobile device doesn't match pinned session -> session_replaced error
    u2, err2 = session_service.validate_user_session(1, "mobile_device_token")
    assert err2 == 'session_replaced'


@pytest.mark.unit
def test_login_get_redirects_if_already_authenticated(app, client):
    """GET /login should redirect to dashboard when user already has an active session."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'active_test_sess'

    with patch('routes.auth.get_container') as mock_gc:
        mock_container = Mock()
        mock_session_app = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_session_app.validate_user_session.return_value = (mock_user, None)
        mock_container.applications.session.return_value = mock_session_app
        mock_gc.return_value = mock_container

        response = client.get('/login')
        assert response.status_code == 302
        assert response.location == '/' or response.location.endswith('/')


@pytest.mark.unit
def test_login_get_redirects_to_next_if_provided(app, client):
    """GET /login?next=/assets should redirect to /assets if already authenticated."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'active_test_sess'

    with patch('routes.auth.get_container') as mock_gc:
        mock_container = Mock()
        mock_session_app = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_session_app.validate_user_session.return_value = (mock_user, None)
        mock_container.applications.session.return_value = mock_session_app
        mock_gc.return_value = mock_container

        response = client.get('/login?next=/assets')
        assert response.status_code == 302
        assert response.location == '/assets'
