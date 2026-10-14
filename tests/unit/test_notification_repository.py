"""
Unit Tests - Notification Repository
Tests for NotificationRepository data access methods
"""

from unittest.mock import Mock, patch

import pytest

from models import Notification
from repositories.notification_repository import NotificationRepository


@pytest.mark.unit
class TestNotificationRepository:
    """Test NotificationRepository methods"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.session = Mock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create NotificationRepository with mock database"""
        return NotificationRepository(database=mock_db)

    def test_repository_initialization(self, mock_db):
        """Test repository initialization"""
        repo = NotificationRepository(database=mock_db)
        assert repo.session == mock_db.session

    def test_add_notification(self, repository, mock_db):
        """Test add_notification method"""
        with patch.object(repository, 'add') as mock_add:
            mock_notification = Mock()
            mock_add.return_value = mock_notification

            result = repository.add_notification(
                user_id=1,
                tenant_id='test_tenant',
                category='budget',
                title='Test',
                dedupe_key='test'
            )

            mock_add.assert_called_once()
            assert result == mock_notification

    def test_get_notification(self, repository, mock_db):
        """Test get_notification method"""
        with patch.object(repository, 'get') as mock_get:
            mock_notification = Mock()
            mock_get.return_value = mock_notification

            result = repository.get_notification(1)

            mock_get.assert_called_once_with(Notification, 1)
            assert result == mock_notification

    def test_existing_keys_empty(self, repository):
        """Test existing_keys with empty dedupe_keys"""
        result = repository.existing_keys(user_id=1, dedupe_keys=[])
        assert result == set()

    def test_existing_keys_none(self, repository):
        """Test existing_keys with None dedupe_keys"""
        result = repository.existing_keys(user_id=1, dedupe_keys=None)
        assert result == set()

    def test_existing_keys_with_keys(self, repository):
        """Test existing_keys with dedupe_keys"""
        with patch('models.Notification'):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [('key1',), ('key2',)]
            repository.session.query.return_value = mock_query

            result = repository.existing_keys(user_id=1, dedupe_keys=['key1', 'key2', 'key3'])

            assert result == {'key1', 'key2'}

    def test_existing_keys_no_matches(self, repository):
        """Test existing_keys with no matching keys"""
        with patch('models.Notification'):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = []
            repository.session.query.return_value = mock_query

            result = repository.existing_keys(user_id=1, dedupe_keys=['key1', 'key2'])

            assert result == set()

    def test_list_notifications(self, repository):
        """Test list_notifications method"""
        with patch('models.Notification'):
            mock_notifications = [Mock(), Mock()]
            mock_query = Mock()
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
            repository.session.query.return_value = mock_query

            result = repository.list_notifications(user_id=1, limit=30)

            assert result == mock_notifications

    def test_list_notifications_default_limit(self, repository):
        """Test list_notifications with default limit"""
        with patch('models.Notification'):
            mock_notifications = [Mock()]
            mock_query = Mock()
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
            repository.session.query.return_value = mock_query

            result = repository.list_notifications(user_id=1)

            assert result == mock_notifications

    def test_unread_count(self, repository):
        """Test unread_count method"""
        with patch('models.Notification'):
            mock_query = Mock()
            mock_query.filter_by.return_value.count.return_value = 5
            repository.session.query.return_value = mock_query

            result = repository.unread_count(user_id=1)

            assert result == 5

    def test_mark_all_read(self, repository):
        """Test mark_all_read method"""
        with patch('models.Notification'):
            mock_query = Mock()
            mock_query.filter_by.return_value.update.return_value = 10
            repository.session.query.return_value = mock_query

            result = repository.mark_all_read(user_id=1)

            assert result == 10

    def test_delete_read(self, repository):
        """Test delete_read method"""
        with patch('models.Notification'):
            mock_query = Mock()
            mock_query.filter_by.return_value.delete.return_value = 5
            repository.session.query.return_value = mock_query

            result = repository.delete_read(user_id=1)

            assert result == 5

    def test_delete_expired(self, repository):
        """Test delete_expired method"""
        with patch('models.Notification'):
            mock_query = Mock()
            mock_query.filter.return_value.delete.return_value = 3
            repository.session.query.return_value = mock_query

            result = repository.delete_expired(user_id=1)

            assert result == 3

    def test_list_by_priority(self, repository):
        """Test list_by_priority method"""
        with patch('models.Notification'):
            mock_notifications = [Mock(), Mock()]
            mock_query = Mock()
            mock_query.filter_by.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
            repository.session.query.return_value = mock_query

            result = repository.list_by_priority(user_id=1, priority='high', limit=10)

            assert result == mock_notifications

    def test_list_by_priority_no_priority_filter(self, repository):
        """Test list_by_priority without priority filter"""
        with patch('models.Notification'):
            mock_notifications = [Mock()]
            mock_query = Mock()
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
            repository.session.query.return_value = mock_query

            result = repository.list_by_priority(user_id=1)

            assert result == mock_notifications

    def test_list_by_delivery_status(self, repository):
        """Test list_by_delivery_status method"""
        with patch('models.Notification'):
            mock_notifications = [Mock(), Mock()]
            mock_query = Mock()
            mock_query.filter_by.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
            repository.session.query.return_value = mock_query

            result = repository.list_by_delivery_status(user_id=1, status='failed', limit=10)

            assert result == mock_notifications

    def test_list_by_delivery_status_no_status_filter(self, repository):
        """Test list_by_delivery_status without status filter"""
        with patch('models.Notification'):
            mock_notifications = [Mock()]
            mock_query = Mock()
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
            repository.session.query.return_value = mock_query

            result = repository.list_by_delivery_status(user_id=1)

            assert result == mock_notifications
