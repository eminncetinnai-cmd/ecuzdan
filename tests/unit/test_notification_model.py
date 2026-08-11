"""
Unit Tests - Notification Model
Tests for Notification model methods and properties
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from models import Notification


@pytest.mark.unit
class TestNotificationModel:
    """Test Notification model methods"""

    def test_notification_repr(self):
        """Test Notification __repr__ method"""
        notification = Notification(
            category='budget',
            dedupe_key='budget:1:2026-08'
        )
        result = repr(notification)
        assert 'budget' in result
        assert 'budget:1:2026-08' in result

    def test_is_expired_no_expiration(self):
        """Test is_expired when expires_at is None"""
        notification = Notification(
            category='budget',
            dedupe_key='test'
        )
        assert notification.is_expired() is False

    def test_is_expired_not_expired(self):
        """Test is_expired when notification is not expired"""
        notification = Notification(
            category='budget',
            dedupe_key='test',
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        assert notification.is_expired() is False

    def test_is_expired_expired(self):
        """Test is_expired when notification is expired"""
        notification = Notification(
            category='budget',
            dedupe_key='test',
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert notification.is_expired() is True

    def test_mark_sent(self):
        """Test mark_sent method"""
        notification = Notification(
            category='budget',
            dedupe_key='test',
            delivery_status='pending'
        )
        notification.mark_sent()
        
        assert notification.sent_at is not None
        assert notification.delivery_status == 'sent'

    def test_mark_delivered(self):
        """Test mark_delivered method"""
        notification = Notification(
            category='budget',
            dedupe_key='test',
            delivery_status='sent'
        )
        notification.mark_delivered()
        
        assert notification.delivered_at is not None
        assert notification.delivery_status == 'delivered'

    def test_mark_read(self):
        """Test mark_read method"""
        notification = Notification(
            category='budget',
            dedupe_key='test',
            delivery_status='delivered',
            is_read=False
        )
        notification.mark_read()
        
        assert notification.read_at is not None
        assert notification.is_read is True
        assert notification.delivery_status == 'read'

    def test_mark_failed(self):
        """Test mark_failed method"""
        notification = Notification(
            category='budget',
            dedupe_key='test',
            delivery_status='pending'
        )
        notification.mark_failed('Connection timeout')
        
        assert notification.failed_at is not None
        assert notification.failure_reason == 'Connection timeout'
        assert notification.delivery_status == 'failed'

    def test_severities_constant(self):
        """Test SEVERITIES constant"""
        assert Notification.SEVERITIES == ('info', 'warning', 'danger')

    def test_priorities_constant(self):
        """Test PRIORITIES constant"""
        assert Notification.PRIORITIES == ('low', 'normal', 'high', 'urgent')

    def test_delivery_statuses_constant(self):
        """Test DELIVERY_STATUSES constant"""
        assert Notification.DELIVERY_STATUSES == ('pending', 'sent', 'delivered', 'read', 'failed')

    def test_default_values(self):
        """Test default field values"""
        notification = Notification(
            user_id=1,
            tenant_id='test_tenant',
            category='budget',
            severity='info',
            priority='normal',
            delivery_status='pending',
            is_read=False,
            dedupe_key='test'
        )
        
        assert notification.severity == 'info'
        assert notification.priority == 'normal'
        assert notification.delivery_status == 'pending'
        assert notification.is_read is False

    def test_actions_json_field(self):
        """Test actions JSON field"""
        actions = [
            {"label": "View", "action": "link", "value": "/transactions"},
            {"label": "Dismiss", "action": "dismiss"}
        ]
        notification = Notification(
            user_id=1,
            tenant_id='test_tenant',
            category='budget',
            dedupe_key='test',
            actions=actions
        )
        
        assert notification.actions == actions

    def test_category_values(self):
        """Test category field accepts valid values"""
        valid_categories = ['budget', 'payment', 'system', 'asset']
        for category in valid_categories:
            notification = Notification(
                user_id=1,
                tenant_id='test_tenant',
                category=category,
                dedupe_key='test'
            )
            assert notification.category == category
