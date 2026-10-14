"""
Unit Tests - Reset Admin
Admin password reset utility tests
"""

from unittest.mock import Mock, patch

import pytest
from werkzeug.security import check_password_hash

from utils.reset_admin import validate_password


@pytest.mark.unit
def test_validate_password_valid():
    """Test validate_password with valid password"""
    result, message = validate_password("Password123")
    assert result is True
    assert "geçerli" in message.lower()


@pytest.mark.unit
def test_validate_password_too_short():
    """Test validate_password with password too short"""
    result, message = validate_password("Pass1")
    assert result is False
    assert "8 karakter" in message


@pytest.mark.unit
def test_validate_password_no_digit():
    """Test validate_password with no digit"""
    result, message = validate_password("Password")
    assert result is False
    assert "rakam" in message


@pytest.mark.unit
def test_validate_password_no_uppercase():
    """Test validate_password with no uppercase"""
    result, message = validate_password("password123")
    assert result is False
    assert "büyük harf" in message


@pytest.mark.unit
def test_validate_password_exactly_8_chars():
    """Test validate_password with exactly 8 characters"""
    result, message = validate_password("Pass1234")
    assert result is True


@pytest.mark.unit
def test_validate_password_with_special_chars():
    """Test validate_password with special characters"""
    result, message = validate_password("Pass!123")
    assert result is True


@pytest.mark.unit
def test_validate_password_empty():
    """Test validate_password with empty password"""
    result, message = validate_password("")
    assert result is False


@pytest.mark.unit
def test_validate_password_only_digits():
    """Test validate_password with only digits"""
    result, message = validate_password("12345678")
    assert result is False


@pytest.mark.unit
def test_validate_password_only_uppercase():
    """Test validate_password with only uppercase"""
    result, message = validate_password("PASSWORD")
    assert result is False


@pytest.mark.unit
def test_validate_password_only_lowercase():
    """Test validate_password with only lowercase"""
    result, message = validate_password("password")
    assert result is False


@pytest.mark.unit
def test_validate_password_very_long():
    """Test validate_password with very long password"""
    result, message = validate_password("VeryLongPassword123456789")
    assert result is True


@pytest.mark.unit
def test_validate_password_turkish_chars():
    """Test validate_password with Turkish characters - requires ASCII uppercase"""
    result, message = validate_password("Şifre123")
    # Turkish 'Ş' is not ASCII uppercase, so it fails the uppercase check
    assert result is False


@pytest.mark.unit
def test_reset_admin_module_imports():
    """Test reset_admin module can be imported"""
    from utils.reset_admin import reset_admin_password, validate_password
    assert validate_password is not None
    assert reset_admin_password is not None


@pytest.mark.unit
def test_reset_admin_module_structure():
    """Test reset_admin module structure"""
    import utils.reset_admin as reset_admin_module

    # Check for expected functions
    assert hasattr(reset_admin_module, 'validate_password')
    assert hasattr(reset_admin_module, 'reset_admin_password')

    # Check for expected imports
    assert hasattr(reset_admin_module, 'getpass')
    assert hasattr(reset_admin_module, 're')
    assert hasattr(reset_admin_module, 'generate_password_hash')


@pytest.mark.unit
def test_reset_admin_imports():
    """Test reset_admin has required imports"""
    import utils.reset_admin as reset_admin_module

    assert hasattr(reset_admin_module, 'getpass')
    assert hasattr(reset_admin_module, 're')
    assert hasattr(reset_admin_module, 'generate_password_hash')
    assert hasattr(reset_admin_module, 'app')
    assert hasattr(reset_admin_module, 'User')
    assert hasattr(reset_admin_module, 'db')


@pytest.mark.unit
def test_reset_admin_password_function():
    """Test reset_admin_password function exists and is callable"""
    from utils.reset_admin import reset_admin_password
    assert callable(reset_admin_password)


@pytest.mark.unit
def test_reset_admin_reset_password(app):
    """Password reset updates a selected admin without touching a real database."""
    from utils.reset_admin import reset_admin_password

    admin_user = Mock(username='emin', role='admin', tenant_id='default')
    admin_user.password_changed_at = None
    with patch('utils.reset_admin.app', app), \
         patch('utils.reset_admin.User') as user_model, \
         patch('utils.reset_admin.db') as db_mock, \
         patch('utils.reset_admin.getpass.getpass', side_effect=['ValidPass1', 'ValidPass1']):
        user_model.query.filter_by.return_value.first.return_value = admin_user

        assert reset_admin_password() is True

    assert check_password_hash(admin_user.password, 'ValidPass1')
    db_mock.session.commit.assert_called_once()


@pytest.mark.unit
def test_validate_password_return_types():
    """Test validate_password returns tuple of (bool, str)"""
    result = validate_password("Test123")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], str)


@pytest.mark.unit
def test_validate_password_case_sensitive():
    """Test validate_password is case sensitive for uppercase check"""
    result, message = validate_password("password123")
    assert result is False
    assert "büyük harf" in message


@pytest.mark.unit
def test_validate_password_multiple_digits():
    """Test validate_password with multiple digits"""
    result, message = validate_password("Password12345")
    assert result is True


@pytest.mark.unit
def test_validate_password_multiple_uppercase():
    """Test validate_password with multiple uppercase letters"""
    result, message = validate_password("PASSword123")
    assert result is True
