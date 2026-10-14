from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from flask import session

from utils.auth_helpers import capability_required
from utils.capabilities import Capability, has_capability, has_full_platform_access


@pytest.mark.unit
def test_system_role_has_full_platform_capabilities():
    user = SimpleNamespace(
        username='system-user',
        role='sistem_yoneticisi',
        is_super_admin=False,
        special_code=None,
        special_code_used_at=None,
    )

    assert has_full_platform_access(user) is True
    assert has_capability(user, Capability.MONITORING_VIEW) is True
    assert has_capability(user, Capability.PLATFORM_BACKUP) is True


@pytest.mark.unit
def test_redeemed_full_access_code_inherits_capabilities_without_role_upgrade():
    user = SimpleNamespace(
        username='code-user',
        role='kullanici',
        is_super_admin=False,
        special_code='emincetin10',
        special_code_used_at=datetime(2026, 8, 19),
    )

    assert has_full_platform_access(user) is True
    assert has_capability(user, Capability.DEMO_DATA_WRITE) is True
    assert has_capability(user, Capability.MONITORING_VIEW) is True


@pytest.mark.unit
def test_standard_user_does_not_have_privileged_capabilities():
    user = SimpleNamespace(
        username='standard-user',
        role='kullanici',
        is_super_admin=False,
        special_code=None,
        special_code_used_at=None,
    )

    assert has_full_platform_access(user) is False
    assert has_capability(user, Capability.MONITORING_VIEW) is False
    assert has_capability(user, Capability.DEMO_DATA_WRITE) is False


@pytest.mark.unit
def test_capability_required_denies_standard_user(app):
    @capability_required(Capability.MONITORING_VIEW)
    def protected():
        return 'protected'

    with app.test_request_context('/protected'):
        session['user_id'] = 10
        user = SimpleNamespace(
            role='kullanici',
            is_super_admin=False,
            special_code=None,
            special_code_used_at=None,
        )
        with patch('utils.auth_helpers.db.session.get', return_value=user):
            response = protected()

    assert response.status_code == 302
    assert response.location.endswith('/')


@pytest.mark.unit
def test_capability_required_allows_redeemed_code_user(app):
    @capability_required(Capability.MONITORING_VIEW)
    def protected():
        return 'protected'

    with app.test_request_context('/protected'):
        session['user_id'] = 11
        user = SimpleNamespace(
            role='kullanici',
            is_super_admin=False,
            special_code='emincetin10',
            special_code_used_at=datetime(2026, 8, 19),
        )
        with patch('utils.auth_helpers.db.session.get', return_value=user):
            assert protected() == 'protected'
