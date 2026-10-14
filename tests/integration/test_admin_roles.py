"""Integration tests for canonical administrator role capabilities."""

from werkzeug.security import generate_password_hash

from models import User


def test_emin_super_admin(app):
    """The canonical system administrator retains all expected role capabilities."""
    emin = User(
        username='emin',
        password=generate_password_hash('1'),
        role='sistem_yoneticisi',
    )

    assert emin.is_super_admin is True
    assert emin.has_admin_access is True
    assert 'Tam Yetki' in emin.role_labels
    assert 'Sistem Yöneticisi' in emin.role_labels
    assert 'Yönetici' in emin.role_labels
