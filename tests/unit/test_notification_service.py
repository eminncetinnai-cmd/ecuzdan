"""
Unit Tests - Notification Service
Tests for NotificationService business logic
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from domain.notifications.services.notification_service import NotificationService, LIST_LIMIT


@pytest.mark.unit
class TestNotificationService:
    """Test NotificationService methods"""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository"""
        repo = Mock()
        repo.session = Mock()
        return repo

    @pytest.fixture
    def service(self, mock_repository):
        """Create NotificationService with mock repository"""
        return NotificationService(repository=mock_repository)

    def test_service_initialization(self, mock_repository):
        """Test service initialization"""
        service = NotificationService(repository=mock_repository)
        assert service.repository == mock_repository

    def test_list_limit_constant(self):
        """Test LIST_LIMIT constant"""
        assert LIST_LIMIT == 30

    def test_list_for_user(self, service, mock_repository):
        """Test list_for_user method"""
        mock_notifications = [Mock(), Mock()]
        mock_repository.list_notifications.return_value = mock_notifications
        
        result = service.list_for_user(user_id=1)
        
        mock_repository.list_notifications.assert_called_once_with(1, limit=LIST_LIMIT)
        assert result == mock_notifications

    def test_list_for_user_custom_limit(self, service, mock_repository):
        """Test list_for_user with custom limit"""
        mock_notifications = [Mock()]
        mock_repository.list_notifications.return_value = mock_notifications
        
        result = service.list_for_user(user_id=1, limit=10)
        
        mock_repository.list_notifications.assert_called_once_with(1, limit=10)
        assert result == mock_notifications

    def test_unread_count(self, service, mock_repository):
        """Test unread_count method"""
        mock_repository.unread_count.return_value = 5
        
        result = service.unread_count(user_id=1)
        
        mock_repository.unread_count.assert_called_once_with(1)
        assert result == 5

    def test_mark_read_success(self, service, mock_repository):
        """Test mark_read with valid notification"""
        mock_notification = Mock()
        mock_notification.user_id = 1
        mock_repository.get_notification.return_value = mock_notification
        
        result = service.mark_read(user_id=1, notification_id=1)
        
        mock_repository.get_notification.assert_called_once_with(1)
        assert result == mock_notification
        mock_repository.commit.assert_called_once()

    def test_mark_read_wrong_user(self, service, mock_repository):
        """Test mark_read with wrong user"""
        mock_notification = Mock()
        mock_notification.user_id = 2
        mock_repository.get_notification.return_value = mock_notification
        
        with pytest.raises(PermissionError, match='Bu bildirime erişiminiz yok'):
            service.mark_read(user_id=1, notification_id=1)
        
        mock_repository.commit.assert_not_called()

    def test_mark_read_not_found(self, service, mock_repository):
        """Test mark_read with non-existent notification"""
        mock_repository.get_notification.return_value = None
        
        with pytest.raises(PermissionError, match='Bu bildirime erişiminiz yok'):
            service.mark_read(user_id=1, notification_id=1)
        
        mock_repository.commit.assert_not_called()

    def test_mark_all_read(self, service, mock_repository):
        """Test mark_all_read method"""
        mock_repository.mark_all_read.return_value = 10
        
        result = service.mark_all_read(user_id=1)
        
        mock_repository.mark_all_read.assert_called_once_with(1)
        mock_repository.commit.assert_called_once()
        assert result == 10

    def test_delete_success(self, service, mock_repository):
        """Test delete with valid notification"""
        mock_notification = Mock()
        mock_notification.user_id = 1
        mock_repository.get_notification.return_value = mock_notification
        
        result = service.delete(user_id=1, notification_id=1)
        
        mock_repository.get_notification.assert_called_once_with(1)
        mock_repository.delete.assert_called_once_with(mock_notification)
        mock_repository.commit.assert_called_once()
        assert result == mock_notification

    def test_delete_wrong_user(self, service, mock_repository):
        """Test delete with wrong user"""
        mock_notification = Mock()
        mock_notification.user_id = 2
        mock_repository.get_notification.return_value = mock_notification
        
        with pytest.raises(PermissionError, match='Bu bildirime erişiminiz yok'):
            service.delete(user_id=1, notification_id=1)
        
        mock_repository.delete.assert_not_called()
        mock_repository.commit.assert_not_called()

    def test_delete_read(self, service, mock_repository):
        """Test delete_read method"""
        mock_repository.delete_read.return_value = 5
        
        result = service.delete_read(user_id=1)
        
        mock_repository.delete_read.assert_called_once_with(1)
        mock_repository.commit.assert_called_once()
        assert result == 5

    def test_delete_expired(self, service, mock_repository):
        """Test delete_expired method"""
        mock_repository.delete_expired.return_value = 3
        
        result = service.delete_expired(user_id=1)
        
        mock_repository.delete_expired.assert_called_once_with(1)
        mock_repository.commit.assert_called_once()
        assert result == 3

    def test_mark_sent(self, service, mock_repository):
        """Test mark_sent method"""
        mock_notification = Mock()
        mock_repository.get_notification.return_value = mock_notification
        
        result = service.mark_sent(notification_id=1)
        
        mock_repository.get_notification.assert_called_once_with(1)
        mock_repository.commit.assert_called_once()
        assert result == mock_notification

    def test_mark_sent_not_found(self, service, mock_repository):
        """Test mark_sent with non-existent notification"""
        mock_repository.get_notification.return_value = None
        
        result = service.mark_sent(notification_id=1)
        
        mock_repository.get_notification.assert_called_once_with(1)
        mock_repository.commit.assert_not_called()
        assert result is None

    def test_mark_delivered(self, service, mock_repository):
        """Test mark_delivered method"""
        mock_notification = Mock()
        mock_repository.get_notification.return_value = mock_notification
        
        result = service.mark_delivered(notification_id=1)
        
        mock_repository.get_notification.assert_called_once_with(1)
        mock_repository.commit.assert_called_once()
        assert result == mock_notification

    def test_mark_failed(self, service, mock_repository):
        """Test mark_failed method"""
        mock_notification = Mock()
        mock_repository.get_notification.return_value = mock_notification
        
        result = service.mark_failed(notification_id=1, reason='Connection timeout')
        
        mock_repository.get_notification.assert_called_once_with(1)
        mock_repository.commit.assert_called_once()
        assert result == mock_notification
