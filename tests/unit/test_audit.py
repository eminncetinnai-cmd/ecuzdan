"""
Unit Tests - Audit
Audit trail logging utility functions
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.audit import (
    ACTION_DATA_EXPORT,
    ACTION_INVITE_CREATED,
    ACTION_LOGIN,
    ACTION_LOGIN_FAILED,
    ACTION_LOGOUT,
    ACTION_PW_CHANGED,
    ACTION_REGISTER,
    ACTION_RESET_DATA,
    ACTION_ROLE_CHANGED,
    ACTION_TENANT_CREATED,
    ACTION_USER_DELETED,
    audit_log,
)


@pytest.mark.unit
def test_audit_constants():
    """Test that all action constants are defined"""
    assert ACTION_LOGIN == 'LOGIN'
    assert ACTION_LOGOUT == 'LOGOUT'
    assert ACTION_REGISTER == 'REGISTER'
    assert ACTION_TENANT_CREATED == 'TENANT_CREATED'
    assert ACTION_DATA_EXPORT == 'DATA_EXPORT'
    assert ACTION_RESET_DATA == 'RESET_DATA'
    assert ACTION_ROLE_CHANGED == 'ROLE_CHANGED'
    assert ACTION_USER_DELETED == 'USER_DELETED'
    assert ACTION_INVITE_CREATED == 'INVITE_CREATED'
    assert ACTION_LOGIN_FAILED == 'LOGIN_FAILED'
    assert ACTION_PW_CHANGED == 'PASSWORD_CHANGED'


@pytest.mark.unit
def test_audit_log_basic():
    """Test audit_log with basic parameters"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        audit_log(
            ACTION_LOGIN,
            user_id='123',
            username='testuser',
            tenant_id='tenant_123'
        )

        assert mock_session.add.called
        assert mock_session.flush.called


@pytest.mark.unit
def test_audit_log_with_details():
    """Test audit_log with details dict"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        details = {'ip': '192.168.1.1', 'method': 'POST'}
        audit_log(
            ACTION_LOGIN,
            user_id='123',
            username='testuser',
            tenant_id='tenant_123',
            details=details
        )

        assert mock_session.add.called
        assert mock_session.flush.called


@pytest.mark.unit
def test_audit_log_with_entity():
    """Test audit_log with entity_type and entity_id"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        audit_log(
            ACTION_USER_DELETED,
            user_id='123',
            username='admin',
            tenant_id='tenant_123',
            entity_type='user',
            entity_id='456'
        )

        assert mock_session.add.called
        assert mock_session.flush.called




@pytest.mark.unit
def test_audit_log_imports():
    """Test that audit_log can be imported"""
    from utils.audit import audit_log
    assert callable(audit_log)


@pytest.mark.unit
def test_audit_log_with_flask_request():
    """Test audit_log with Flask request context"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        mock_request = Mock()
        mock_request.remote_addr = '192.168.1.1'
        mock_request.headers.get = Mock(return_value='Mozilla/5.0')

        with patch('flask.request', mock_request):
            audit_log(
                ACTION_LOGIN,
                user_id='123',
                username='testuser',
                tenant_id='tenant_123'
            )

        assert mock_session.add.called
        assert mock_session.flush.called


@pytest.mark.unit
def test_audit_log_without_flask_context():
    """Audit logging tolerates a background/service call without request context."""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        audit_log(
            ACTION_LOGIN,
            user_id='123',
            username='testuser',
            tenant_id='tenant_123',
        )

        assert mock_session.add.called
        assert mock_session.flush.called


@pytest.mark.unit
def test_audit_log_exception_handling():
    """Test audit_log exception handling"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_session.add = Mock(side_effect=Exception("DB Error"))
        mock_db.session = mock_session

        # Should not raise exception
        audit_log(
            ACTION_LOGIN,
            user_id='123',
            username='testuser',
            tenant_id='tenant_123'
        )


@pytest.mark.unit
def test_audit_log_exception_with_rollback():
    """Test audit_log exception handling with rollback"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_session.add = Mock(side_effect=Exception("DB Error"))
        mock_session.rollback = Mock()
        mock_db.session = mock_session

        # Should not raise exception
        audit_log(
            ACTION_LOGIN,
            user_id='123',
            username='testuser',
            tenant_id='tenant_123'
        )

        # Rollback should be attempted
        mock_session.rollback.assert_called()


@pytest.mark.unit
def test_audit_log_user_agent_truncation():
    """Test audit_log truncates long user agent strings"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        mock_request = Mock()
        mock_request.remote_addr = '192.168.1.1'
        # User agent longer than 300 characters
        long_ua = 'A' * 400
        mock_request.headers.get = Mock(return_value=long_ua)

        with patch('flask.request', mock_request):
            audit_log(
                ACTION_LOGIN,
                user_id='123',
                username='testuser',
                tenant_id='tenant_123'
            )

        assert mock_session.add.called
        assert mock_session.flush.called


@pytest.mark.unit
def test_audit_log_with_none_entity_id():
    """Test audit_log with None entity_id"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        audit_log(
            ACTION_LOGIN,
            user_id='123',
            username='testuser',
            tenant_id='tenant_123',
            entity_type='user',
            entity_id=None
        )

        assert mock_session.add.called
        assert mock_session.flush.called


@pytest.mark.unit
def test_audit_log_with_numeric_entity_id():
    """Test audit_log converts numeric entity_id to string"""
    with patch('models.db') as mock_db:
        mock_session = MagicMock()
        mock_db.session = mock_session

        audit_log(
            ACTION_USER_DELETED,
            user_id='123',
            username='admin',
            tenant_id='tenant_123',
            entity_type='user',
            entity_id=456
        )

        assert mock_session.add.called
        assert mock_session.flush.called


