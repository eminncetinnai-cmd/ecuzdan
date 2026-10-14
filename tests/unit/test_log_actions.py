"""
Unit Tests - Log Actions
Log Action System - Log sınıflandırma ve otomatik aksiyon sistemi
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from utils.log_actions import LogAction, LogActionConfig, LogCategory, LogClassifier, LogSeverity, get_log_classifier


@pytest.mark.unit
def test_log_severity_enum():
    """Test LogSeverity enum values"""
    assert LogSeverity.CRITICAL.value == "CRITICAL"
    assert LogSeverity.ERROR.value == "ERROR"
    assert LogSeverity.WARNING.value == "WARNING"
    assert LogSeverity.INFO.value == "INFO"
    assert LogSeverity.DEBUG.value == "DEBUG"


@pytest.mark.unit
def test_log_category_enum():
    """Test LogCategory enum values"""
    assert LogCategory.SECURITY.value == "SECURITY"
    assert LogCategory.DATABASE.value == "DATABASE"
    assert LogCategory.PERFORMANCE.value == "PERFORMANCE"
    assert LogCategory.BUSINESS.value == "BUSINESS"
    assert LogCategory.SYSTEM.value == "SYSTEM"


@pytest.mark.unit
def test_log_action_dataclass():
    """Test LogAction dataclass"""
    action = LogAction(
        action_type="test_action",
        priority=5,
        cooldown_minutes=30,
        enabled=True
    )
    assert action.action_type == "test_action"
    assert action.priority == 5
    assert action.cooldown_minutes == 30
    assert action.enabled is True


@pytest.mark.unit
def test_log_action_dataclass_defaults():
    """Test LogAction dataclass with defaults"""
    action = LogAction(action_type="test_action", priority=5)
    assert action.cooldown_minutes == 60
    assert action.enabled is True


@pytest.mark.unit
def test_log_action_config_init():
    """Test LogActionConfig initialization"""
    config = LogActionConfig()
    assert config.actions is not None
    assert config.action_history is not None
    assert config.action_handlers is not None


@pytest.mark.unit
def test_log_action_config_default_actions():
    """Test LogActionConfig default actions"""
    config = LogActionConfig()
    assert LogSeverity.CRITICAL in config.actions
    assert LogSeverity.ERROR in config.actions
    assert LogSeverity.WARNING in config.actions
    assert LogCategory.SECURITY in config.actions


@pytest.mark.unit
def test_get_actions_for_log_severity():
    """Test get_actions_for_log with severity only"""
    config = LogActionConfig()
    actions = config.get_actions_for_log(LogSeverity.CRITICAL)
    assert len(actions) > 0
    assert all(a.enabled for a in actions)


@pytest.mark.unit
def test_get_actions_for_log_category():
    """Test get_actions_for_log with category"""
    config = LogActionConfig()
    actions = config.get_actions_for_log(LogSeverity.INFO, LogCategory.SECURITY)
    assert len(actions) > 0


@pytest.mark.unit
def test_get_actions_for_log_priority_sorting():
    """Test get_actions_for_log sorts by priority"""
    config = LogActionConfig()
    actions = config.get_actions_for_log(LogSeverity.CRITICAL)
    priorities = [a.priority for a in actions]
    assert priorities == sorted(priorities)


@pytest.mark.unit
def test_can_execute_action_no_history():
    """Test can_execute_action when no history exists"""
    config = LogActionConfig()
    action = LogAction("test_action", 5, 30)
    assert config.can_execute_action(action) is True


@pytest.mark.unit
def test_can_execute_action_within_cooldown():
    """Test can_execute_action within cooldown period"""
    config = LogActionConfig()
    action = LogAction("test_action", 5, 30)

    action_key = f"{action.action_type}_{action.priority}"
    config.action_history[action_key] = datetime.now()

    assert config.can_execute_action(action) is False


@pytest.mark.unit
def test_can_execute_action_after_cooldown():
    """Test can_execute_action after cooldown period"""
    config = LogActionConfig()
    action = LogAction("test_action", 5, 1)

    action_key = f"{action.action_type}_{action.priority}"
    config.action_history[action_key] = datetime.now() - timedelta(minutes=2)

    assert config.can_execute_action(action) is True


@pytest.mark.unit
def test_execute_action_disabled():
    """Test execute_action with disabled action"""
    config = LogActionConfig()
    action = LogAction("test_action", 5, 30, enabled=False)
    log_data = {"message": "test"}

    # Should not execute if disabled
    config.execute_action(action, log_data)
    # No exception should be raised


@pytest.mark.unit
def test_execute_action_within_cooldown():
    """Test execute_action within cooldown period"""
    config = LogActionConfig()
    action = LogAction("test_action", 5, 30)

    action_key = f"{action.action_type}_{action.priority}"
    config.action_history[action_key] = datetime.now()

    log_data = {"message": "test"}
    config.execute_action(action, log_data)
    # Should not execute due to cooldown


@pytest.mark.unit
def test_execute_action_no_handler():
    """Test execute_action with no handler"""
    config = LogActionConfig()
    action = LogAction("nonexistent_action", 5, 30, enabled=True)
    log_data = {"message": "test"}

    config.execute_action(action, log_data)
    # Should not raise exception


@pytest.mark.unit
def test_log_to_db_handler():
    """Test _log_to_db handler"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "ERROR"}

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config._log_to_db(log_data)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_immediate_notification_handler():
    """Test _immediate_notification handler"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "CRITICAL"}

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config._immediate_notification(log_data)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_create_ticket_handler():
    """Test _create_ticket handler"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "ERROR"}

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config._create_ticket(log_data)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_monitoring_dashboard_handler():
    """Test _monitoring_dashboard handler"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "WARNING"}

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config._monitoring_dashboard(log_data)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_security_team_alert_handler():
    """Test _security_team_alert handler"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "CRITICAL"}

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config._security_team_alert(log_data)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_audit_log_handler():
    """Test _audit_log handler"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "INFO"}

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config._audit_log(log_data)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_email_alert_handler_critical():
    """Test _email_alert handler for CRITICAL severity"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "CRITICAL", "category": "SECURITY"}

    with patch('utils.email_alerts.get_email_alert_system') as mock_get_email:
        mock_email_system = Mock()
        mock_get_email.return_value = mock_email_system

        config._email_alert(log_data)
        mock_email_system.send_critical_alert.assert_called_once()


@pytest.mark.unit
def test_email_alert_handler_error():
    """Test _email_alert handler for ERROR severity"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "ERROR", "category": "DATABASE"}

    with patch('utils.email_alerts.get_email_alert_system') as mock_get_email:
        mock_email_system = Mock()
        mock_get_email.return_value = mock_email_system

        config._email_alert(log_data)
        mock_email_system.send_error_alert.assert_called_once()


@pytest.mark.unit
def test_email_alert_handler_warning():
    """Test _email_alert handler for WARNING severity"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "WARNING", "category": "SYSTEM"}

    with patch('utils.email_alerts.get_email_alert_system') as mock_get_email:
        mock_email_system = Mock()
        mock_get_email.return_value = mock_email_system

        config._email_alert(log_data)
        mock_email_system.send_warning_alert.assert_called_once()


@pytest.mark.unit
def test_email_alert_handler_import_error():
    """Test _email_alert handler with import error"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "CRITICAL"}

    with patch('utils.email_alerts.get_email_alert_system', side_effect=ImportError):
        with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            config._email_alert(log_data)
            mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_log_classifier_init():
    """Test LogClassifier initialization"""
    classifier = LogClassifier()
    assert classifier.action_config is not None
    assert isinstance(classifier.action_config, LogActionConfig)


@pytest.mark.unit
def test_log_classifier_patterns():
    """Test LogClassifier patterns"""
    classifier = LogClassifier()
    assert LogCategory.SECURITY in classifier.PATTERNS
    assert LogCategory.DATABASE in classifier.PATTERNS
    assert LogCategory.PERFORMANCE in classifier.PATTERNS
    assert LogCategory.BUSINESS in classifier.PATTERNS


@pytest.mark.unit
def test_classify_log_valid_severity():
    """Test classify_log with valid severity"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("test message", "ERROR")
    assert severity == LogSeverity.ERROR


@pytest.mark.unit
def test_classify_log_invalid_severity():
    """Test classify_log with invalid severity"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("test message", "INVALID")
    assert severity == LogSeverity.INFO


@pytest.mark.unit
def test_classify_log_security_pattern():
    """Test classify_log detects security pattern"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("authentication failed attempt", "ERROR")
    assert category == LogCategory.SECURITY


@pytest.mark.unit
def test_classify_log_database_pattern():
    """Test classify_log detects database pattern"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("database connection failed", "ERROR")
    assert category == LogCategory.DATABASE


@pytest.mark.unit
def test_classify_log_performance_pattern():
    """Test classify_log detects performance pattern"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("slow query detected", "WARNING")
    assert category == LogCategory.PERFORMANCE


@pytest.mark.unit
def test_classify_log_business_pattern():
    """Test classify_log detects business pattern"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("payment failed", "ERROR")
    assert category == LogCategory.BUSINESS


@pytest.mark.unit
def test_classify_log_default_category():
    """Test classify_log defaults to SYSTEM category"""
    classifier = LogClassifier()
    severity, category = classifier.classify_log("generic log message", "INFO")
    assert category == LogCategory.SYSTEM


@pytest.mark.unit
def test_detect_category_case_insensitive():
    """Test _detect_category is case insensitive"""
    classifier = LogClassifier()
    category = classifier._detect_category("AUTHENTICATION FAILED")
    assert category == LogCategory.SECURITY


@pytest.mark.unit
def test_process_log():
    """Test process_log method"""
    classifier = LogClassifier()

    with patch.object(classifier.action_config, 'execute_action') as mock_execute:
        classifier.process_log("test message", "ERROR")
        assert mock_execute.called


@pytest.mark.unit
def test_get_log_classifier_singleton():
    """Test get_log_classifier returns singleton"""
    classifier1 = get_log_classifier()
    classifier2 = get_log_classifier()
    assert classifier1 is classifier2


@pytest.mark.unit
def test_get_log_classifier_instance():
    """Test get_log_classifier returns LogClassifier instance"""
    classifier = get_log_classifier()
    assert isinstance(classifier, LogClassifier)


@pytest.mark.unit
def test_execute_action_success_updates_history():
    """Test execute_action updates action history on success"""
    config = LogActionConfig()
    action = LogAction("log_to_db", 5, 30, enabled=True)
    log_data = {"message": "test", "severity": "ERROR"}

    action_key = f"{action.action_type}_{action.priority}"

    with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        config.execute_action(action, log_data)

        # Verify action history was updated
        assert action_key in config.action_history
        assert isinstance(config.action_history[action_key], datetime)


@pytest.mark.unit
def test_execute_action_handler_exception():
    """Test execute_action handles handler exceptions"""
    config = LogActionConfig()
    action = LogAction("log_to_db", 5, 30, enabled=True)
    log_data = {"message": "test", "severity": "ERROR"}

    # Patch the handler in the action_handlers dict
    original_handler = config.action_handlers['log_to_db']
    config.action_handlers['log_to_db'] = Mock(side_effect=Exception("Handler error"))

    try:
        with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            config.execute_action(action, log_data)

            # Verify error was logged
            mock_logger.error.assert_called_once()
    finally:
        # Restore original handler
        config.action_handlers['log_to_db'] = original_handler


@pytest.mark.unit
def test_email_alert_handler_general_exception():
    """Test _email_alert handler with general exception"""
    config = LogActionConfig()
    log_data = {"message": "test", "severity": "CRITICAL"}

    with patch('utils.email_alerts.get_email_alert_system') as mock_get_email:
        mock_email_system = Mock()
        mock_email_system.send_critical_alert.side_effect = Exception("Email error")
        mock_get_email.return_value = mock_email_system

        with patch('utils.log_actions.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            config._email_alert(log_data)

            # Verify error was logged
            mock_logger.error.assert_called_once()
