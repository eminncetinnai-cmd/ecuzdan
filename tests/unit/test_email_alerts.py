"""
Unit Tests - Email Alerts
Email Alert System - Log uyarıları için email gönderme sistemi tests
"""

from unittest.mock import MagicMock, patch

import pytest

from utils.email_alerts import (
    EmailAlertConfig,
    EmailAlertSystem,
    get_email_alert_system,
    setup_email_alerts,
)


@pytest.mark.unit
def test_email_alerts_module_imports():
    """Test email_alerts module can be imported"""
    from utils.email_alerts import EmailAlertConfig, EmailAlertSystem
    assert EmailAlertConfig is not None
    assert EmailAlertSystem is not None


@pytest.mark.unit
def test_email_alerts_module_structure():
    """Test email_alerts module structure"""
    import utils.email_alerts as alerts_module

    # Check for expected classes and functions
    assert hasattr(alerts_module, 'EmailAlertConfig')
    assert hasattr(alerts_module, 'EmailAlertSystem')
    assert hasattr(alerts_module, 'get_email_alert_system')
    assert hasattr(alerts_module, 'setup_email_alerts')


@pytest.mark.unit
def test_email_alert_config_initialization():
    """Test EmailAlertConfig initialization"""
    config = EmailAlertConfig()

    assert config.smtp_server is None
    assert config.smtp_port == 587
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.from_email is None
    assert config.to_emails == []
    assert config.enabled is False


@pytest.mark.unit
def test_email_alert_config_load_from_config():
    """Test EmailAlertConfig load_from_config"""
    config = EmailAlertConfig()
    config_dict = {
        'SMTP_SERVER': 'smtp.example.com',
        'SMTP_PORT': 465,
        'SMTP_USERNAME': 'user@example.com',
        'SMTP_PASSWORD': 'password',
        'FROM_EMAIL': 'noreply@example.com',
        'TO_EMAILS': ['admin@example.com', 'dev@example.com'],
        'EMAIL_ALERTS_ENABLED': True,
    }

    config.load_from_config(config_dict)

    assert config.smtp_server == 'smtp.example.com'
    assert config.smtp_port == 465
    assert config.smtp_username == 'user@example.com'
    assert config.smtp_password == 'password'
    assert config.from_email == 'noreply@example.com'
    assert config.to_emails == ['admin@example.com', 'dev@example.com']
    assert config.enabled is True


@pytest.mark.unit
def test_email_alert_config_load_from_config_defaults():
    """Test EmailAlertConfig load_from_config with defaults"""
    config = EmailAlertConfig()
    config_dict = {
        'SMTP_SERVER': 'smtp.example.com',
    }

    config.load_from_config(config_dict)

    assert config.smtp_server == 'smtp.example.com'
    assert config.smtp_port == 587  # default
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.from_email is None
    assert config.to_emails == []  # default
    assert config.enabled is False  # default


@pytest.mark.unit
def test_email_alert_system_initialization():
    """Test EmailAlertSystem initialization"""
    system = EmailAlertSystem()

    assert system.config is not None
    assert system.config.enabled is False
    assert system.logger is not None


@pytest.mark.unit
def test_email_alert_system_initialization_with_config():
    """Test EmailAlertSystem initialization with config"""
    config = EmailAlertConfig()
    config.enabled = True
    system = EmailAlertSystem(config)

    assert system.config is config
    assert system.config.enabled is True


@pytest.mark.unit
def test_send_alert_disabled():
    """Test send_alert when disabled"""
    config = EmailAlertConfig()
    config.enabled = False
    system = EmailAlertSystem(config)

    # Should not raise error, just log warning
    system.send_alert("Test Subject", "Test Message")


@pytest.mark.unit
def test_send_alert_no_recipients():
    """Test send_alert with no recipients"""
    config = EmailAlertConfig()
    config.enabled = True
    config.to_emails = []
    system = EmailAlertSystem(config)

    # Should not raise error, just log warning
    system.send_alert("Test Subject", "Test Message")


@pytest.mark.unit
def test_send_alert_success():
    """Test send_alert success"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com']

    system = EmailAlertSystem(config)

    with patch('utils.email_alerts.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        system.send_alert("Test Subject", "Test Message", "HIGH")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('user@example.com', 'password')
        mock_server.send_message.assert_called_once()


@pytest.mark.unit
def test_send_alert_exception_handling():
    """Test send_alert exception handling"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com']

    system = EmailAlertSystem(config)

    with patch('utils.email_alerts.smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP Error")

        # Should not raise error, just log error
        system.send_alert("Test Subject", "Test Message")


@pytest.mark.unit
def test_send_critical_alert():
    """Test send_critical_alert"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com']

    system = EmailAlertSystem(config)

    with patch.object(system, 'send_alert') as mock_send:
        system.send_critical_alert("Test Subject", "Test Message")

        mock_send.assert_called_once_with("Test Subject", "Test Message", 'CRITICAL')


@pytest.mark.unit
def test_send_error_alert():
    """Test send_error_alert"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com']

    system = EmailAlertSystem(config)

    with patch.object(system, 'send_alert') as mock_send:
        system.send_error_alert("Test Subject", "Test Message")

        mock_send.assert_called_once_with("Test Subject", "Test Message", 'HIGH')


@pytest.mark.unit
def test_send_warning_alert():
    """Test send_warning_alert"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com']

    system = EmailAlertSystem(config)

    with patch.object(system, 'send_alert') as mock_send:
        system.send_warning_alert("Test Subject", "Test Message")

        mock_send.assert_called_once_with("Test Subject", "Test Message", 'MEDIUM')


@pytest.mark.unit
def test_send_info_alert():
    """Test send_info_alert"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com']

    system = EmailAlertSystem(config)

    with patch.object(system, 'send_alert') as mock_send:
        system.send_info_alert("Test Subject", "Test Message")

        mock_send.assert_called_once_with("Test Subject", "Test Message", 'LOW')


@pytest.mark.unit
def test_get_email_alert_system_singleton():
    """Test get_email_alert_system returns singleton"""
    system1 = get_email_alert_system()
    system2 = get_email_alert_system()

    assert system1 is system2


@pytest.mark.unit
def test_setup_email_alerts():
    """Test setup_email_alerts"""
    config_dict = {
        'SMTP_SERVER': 'smtp.example.com',
        'SMTP_PORT': 465,
        'SMTP_USERNAME': 'user@example.com',
        'SMTP_PASSWORD': 'password',
        'FROM_EMAIL': 'noreply@example.com',
        'TO_EMAILS': ['admin@example.com'],
        'EMAIL_ALERTS_ENABLED': True,
    }

    system = setup_email_alerts(config_dict)

    assert system.config.smtp_server == 'smtp.example.com'
    assert system.config.smtp_port == 465
    assert system.config.enabled is True


@pytest.mark.unit
def test_setup_email_alerts_singleton():
    """Test setup_email_alerts sets global singleton"""
    config_dict = {
        'SMTP_SERVER': 'smtp.example.com',
        'EMAIL_ALERTS_ENABLED': True,
    }

    system1 = setup_email_alerts(config_dict)
    system2 = get_email_alert_system()

    assert system1 is system2


@pytest.mark.unit
def test_send_alert_multiple_recipients():
    """Test send_alert with multiple recipients"""
    config = EmailAlertConfig()
    config.enabled = True
    config.smtp_server = 'smtp.example.com'
    config.smtp_port = 587
    config.smtp_username = 'user@example.com'
    config.smtp_password = 'password'
    config.from_email = 'noreply@example.com'
    config.to_emails = ['admin@example.com', 'dev@example.com', 'ops@example.com']

    system = EmailAlertSystem(config)

    with patch('utils.email_alerts.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        system.send_alert("Test Subject", "Test Message")

        # Verify send_message was called
        mock_server.send_message.assert_called_once()
