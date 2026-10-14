from unittest.mock import Mock

import pytest
from werkzeug.security import generate_password_hash

from domain.users.services.special_code_service import get_special_code_service
from models import User, db
from utils.capabilities import Capability


def _login_as(client, user_id, username):
    user = db.session.get(User, user_id)
    session_id = getattr(user, 'last_session_id', None) or 'test_sess'
    if user and not user.last_session_id:
        user.last_session_id = session_id
        db.session.commit()
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['username'] = username
        sess['session_id'] = session_id


@pytest.mark.integration
def test_special_code_upgrades_user_and_persists_all_capabilities(app, client):
    holder = User(
        username='code-holder',
        password=generate_password_hash('holder-pass'),
        role='kullanici',
        tenant_id='default',
    )
    db.session.add(holder)
    db.session.commit()
    holder_id = holder.id

    _login_as(client, holder_id, holder.username)
    response = client.post(
        '/settings',
        data={'action': 'apply_special_code', 'special_code': 'emincetin10'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    refreshed = db.session.get(User, holder_id)
    assert refreshed.role == 'sistem_yoneticisi'
    assert refreshed.special_code == get_special_code_service().code_fingerprint('emincetin10')
    assert refreshed.special_code_used_at is not None
    assert refreshed.has_capability(Capability.MONITORING_VIEW) is True
    assert refreshed.has_capability(Capability.DEMO_DATA_WRITE) is True
    assert refreshed.has_capability(Capability.PLATFORM_BACKUP) is True


@pytest.mark.integration
def test_special_code_max_uses_is_enforced_after_redemption(app, client):
    holder = User(
        username='first-code-holder',
        password=generate_password_hash('holder-pass'),
        role='kullanici',
        tenant_id='default',
    )
    db.session.add(holder)
    db.session.commit()
    holder_id = holder.id
    _login_as(client, holder_id, holder.username)

    first = client.post(
        '/settings',
        data={'action': 'apply_special_code', 'special_code': 'emincetin10'},
        follow_redirects=True,
    )
    assert first.status_code == 200

    validation = get_special_code_service().validate_code('emincetin10', 999, 'default')
    assert validation['valid'] is False
    assert 'kullanım' in validation['error']


@pytest.mark.integration
def test_standard_user_cannot_access_monitoring_or_full_backup(authenticated_client):
    monitoring = authenticated_client.get('/monitoring/api/stats')
    backup = authenticated_client.get('/export_db_json')

    assert monitoring.status_code == 302
    assert backup.status_code == 302


@pytest.mark.integration
def test_redeemed_code_user_can_access_monitoring_and_backup(
    privileged_authenticated_client, monkeypatch
):
    monkeypatch.setattr(
        'routes.export.export_service.export_database_json',
        Mock(return_value='{"backup": "test"}'),
    )

    monitoring = privileged_authenticated_client.get('/monitoring/api/stats')
    backup = privileged_authenticated_client.get('/export_db_json')

    assert monitoring.status_code == 200
    assert backup.status_code == 200
    assert backup.json == {'backup': 'test'}


@pytest.mark.integration
def test_standard_user_cannot_execute_advanced_demo_action(authenticated_client, monkeypatch):
    generator = Mock()
    monkeypatch.setattr('routes.settings.generate_advanced_demo_data', generator)

    response = authenticated_client.post(
        '/settings',
        data={'action': 'admin_advanced_fill', 'admin_pass': 'testpass'},
        follow_redirects=True,
    )

    assert response.status_code == 200
    generator.assert_not_called()


@pytest.mark.integration
def test_monitoring_navigation_is_hidden_for_standard_user_and_visible_for_code_user(
    client, test_user
):
    u_id = test_user.id
    u_name = test_user.username
    _login_as(client, u_id, u_name)
    standard_html = client.get('/settings').get_data(as_text=True)

    privileged = db.session.get(User, u_id)
    privileged.role = 'sistem_yoneticisi'
    privileged.special_code = get_special_code_service().code_fingerprint('emincetin10')
    from datetime import datetime
    privileged.special_code_used_at = datetime(2026, 8, 19)
    db.session.commit()
    _login_as(client, u_id, u_name)
    privileged_html = client.get('/settings').get_data(as_text=True)

    assert 'href="/monitoring' not in standard_html
    assert 'href="/monitoring' in privileged_html
