"""Admin demo veri üretici testleri - DEPRECATED

This test file is deprecated. The new demo data architecture uses
DemoDataOrchestrator instead of the old admin_demo_data functions.
See tests/integration/demo/test_demo_data_orchestrator.py for the new tests.
"""

import pytest

from werkzeug.security import generate_password_hash

from models import User


def test_emin_super_admin(app):
    """Test super admin role."""
    emin = User(username='emin', password=generate_password_hash('1'), role='sistem_yoneticisi')
    assert emin.is_super_admin is True
    assert emin.has_admin_access is True
    assert 'Tam Yetki' in emin.role_labels
    assert 'Sistem Yöneticisi' in emin.role_labels
    assert 'Yönetici' in emin.role_labels


@pytest.mark.skip(reason="Old admin_demo_data functions deprecated. Use DemoDataOrchestrator instead.")
def test_generate_admin_demo_data(app):
    """Test old admin demo data generation - DEPRECATED."""
    pass


@pytest.mark.skip(reason="Old admin_demo_data functions deprecated. Use DemoDataOrchestrator instead.")
def test_clear_admin_demo_data(app):
    """Test old admin demo data cleanup - DEPRECATED."""
    pass
