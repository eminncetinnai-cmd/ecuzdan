"""
Unit Tests - Notifications Routes
Notification routes unit tests
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from routes.notifications import _serialize


@pytest.mark.unit
def test_serialize_notification():
    """Test _serialize function with complete notification"""
    mock_notification = Mock()
    mock_notification.id = 1
    mock_notification.category = 'alert'
    mock_notification.severity = 'high'
    mock_notification.title = 'Test Alert'
    mock_notification.body = 'Test body'
    mock_notification.link = '/test'
    mock_notification.is_read = False
    mock_notification.created_at = datetime(2024, 1, 15, 10, 30)

    result = _serialize(mock_notification)

    assert result['id'] == 1
    assert result['category'] == 'alert'
    assert result['severity'] == 'high'
    assert result['title'] == 'Test Alert'
    assert result['body'] == 'Test body'
    assert result['link'] == '/test'
    assert result['is_read'] is False
    assert result['created_at'] == '15/01/2024 10:30'


@pytest.mark.unit
def test_serialize_notification_read():
    """Test _serialize function with read notification"""
    mock_notification = Mock()
    mock_notification.id = 2
    mock_notification.category = 'info'
    mock_notification.severity = 'low'
    mock_notification.title = 'Info'
    mock_notification.body = 'Info body'
    mock_notification.link = None
    mock_notification.is_read = True
    mock_notification.created_at = datetime(2024, 2, 20, 14, 45)

    result = _serialize(mock_notification)

    assert result['id'] == 2
    assert result['category'] == 'info'
    assert result['severity'] == 'low'
    assert result['title'] == 'Info'
    assert result['body'] == 'Info body'
    assert result['link'] is None
    assert result['is_read'] is True
    assert result['created_at'] == '20/02/2024 14:45'


@pytest.mark.unit
def test_serialize_notification_no_created_at():
    """Test _serialize function with None created_at"""
    mock_notification = Mock()
    mock_notification.id = 3
    mock_notification.category = 'warning'
    mock_notification.severity = 'medium'
    mock_notification.title = 'Warning'
    mock_notification.body = 'Warning body'
    mock_notification.link = '/warning'
    mock_notification.is_read = False
    mock_notification.created_at = None

    result = _serialize(mock_notification)

    assert result['id'] == 3
    assert result['category'] == 'warning'
    assert result['severity'] == 'medium'
    assert result['title'] == 'Warning'
    assert result['body'] == 'Warning body'
    assert result['link'] == '/warning'
    assert result['is_read'] is False
    assert result['created_at'] == ''


@pytest.mark.unit
def test_serialize_notification_no_link():
    """Test _serialize function with None link"""
    mock_notification = Mock()
    mock_notification.id = 4
    mock_notification.category = 'success'
    mock_notification.severity = 'low'
    mock_notification.title = 'Success'
    mock_notification.body = 'Success body'
    mock_notification.link = None
    mock_notification.is_read = True
    mock_notification.created_at = datetime(2024, 3, 10, 9, 0)

    result = _serialize(mock_notification)

    assert result['id'] == 4
    assert result['category'] == 'success'
    assert result['severity'] == 'low'
    assert result['title'] == 'Success'
    assert result['body'] == 'Success body'
    assert result['link'] is None
    assert result['is_read'] is True
    assert result['created_at'] == '10/03/2024 09:00'


@pytest.mark.unit
def test_serialize_notification_date_format():
    """Test that date format is DD/MM/YYYY HH:MM"""
    mock_notification = Mock()
    mock_notification.id = 5
    mock_notification.category = 'test'
    mock_notification.severity = 'low'
    mock_notification.title = 'Date Test'
    mock_notification.body = 'Date body'
    mock_notification.link = '/date'
    mock_notification.is_read = False
    mock_notification.created_at = datetime(2024, 12, 25, 23, 59)

    result = _serialize(mock_notification)

    assert result['created_at'] == '25/12/2024 23:59'


@pytest.mark.unit
def test_serialize_notification_all_fields_present():
    """Test that all expected fields are present in serialized output"""
    mock_notification = Mock()
    mock_notification.id = 6
    mock_notification.category = 'test'
    mock_notification.severity = 'low'
    mock_notification.title = 'Test'
    mock_notification.body = 'Body'
    mock_notification.link = '/link'
    mock_notification.is_read = False
    mock_notification.created_at = datetime(2024, 1, 1, 0, 0)

    result = _serialize(mock_notification)

    expected_keys = ['id', 'category', 'severity', 'title', 'body', 'link', 'is_read', 'created_at']
    for key in expected_keys:
        assert key in result
