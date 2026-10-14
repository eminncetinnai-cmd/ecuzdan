"""

Unit Tests - Notification Helpers
Flash message and notification utility functions
"""

import pytest
from flask import Flask, flash, get_flashed_messages

from utils.notification_helpers import (
    NOTIFICATION_CATEGORIES,
    flash_error,
    flash_info,
    flash_notification,
    flash_success,
    flash_warning,
    get_notifications,
    with_notifications,
)


@pytest.mark.unit
def test_notification_helpers_module_imports():
    """Test notification_helpers module can be imported"""
    from utils.notification_helpers import flash_success
    assert flash_success is not None


@pytest.mark.unit
def test_notification_helpers_constants():
    """Test notification categories are defined"""
    assert 'success' in NOTIFICATION_CATEGORIES
    assert 'error' in NOTIFICATION_CATEGORIES
    assert 'warning' in NOTIFICATION_CATEGORIES
    assert 'info' in NOTIFICATION_CATEGORIES


@pytest.mark.unit
def test_notification_categories_structure():
    """Test notification categories have required keys"""
    for category, config in NOTIFICATION_CATEGORIES.items():
        assert 'icon' in config
        assert 'class' in config
        assert 'title' in config


@pytest.mark.unit
def test_flash_success():
    """Test flash_success flashes success message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_success('Test success message')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('success', 'Test success message')


@pytest.mark.unit
def test_flash_error():
    """Test flash_error flashes error message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_error('Test error message')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('error', 'Test error message')


@pytest.mark.unit
def test_flash_warning():
    """Test flash_warning flashes warning message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_warning('Test warning message')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('warning', 'Test warning message')


@pytest.mark.unit
def test_flash_info():
    """Test flash_info flashes info message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_info('Test info message')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('info', 'Test info message')


@pytest.mark.unit
def test_flash_notification_valid_category():
    """Test flash_notification with valid category"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_notification('Test message', 'success')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('success', 'Test message')


@pytest.mark.unit
def test_flash_notification_invalid_category():
    """Test flash_notification with invalid category defaults to info"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_notification('Test message', 'invalid_category')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('info', 'Test message')


@pytest.mark.unit
def test_flash_notification_default_category():
    """Test flash_notification with default category"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash_notification('Test message')
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('info', 'Test message')


@pytest.mark.unit
def test_get_notifications_empty():
    """Test get_notifications with no messages"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        notifications = get_notifications()
        assert notifications == []


@pytest.mark.unit
def test_get_notifications_success():
    """Test get_notifications with success message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash('Test success', 'success')
        notifications = get_notifications()
        assert len(notifications) == 1
        assert notifications[0]['message'] == 'Test success'
        assert notifications[0]['category'] == 'success'
        assert notifications[0]['icon'] == '✓'
        assert notifications[0]['class'] == 'success'
        assert notifications[0]['title'] == 'Başarı'


@pytest.mark.unit
def test_get_notifications_error():
    """Test get_notifications with error message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash('Test error', 'error')
        notifications = get_notifications()
        assert len(notifications) == 1
        assert notifications[0]['message'] == 'Test error'
        assert notifications[0]['category'] == 'error'
        assert notifications[0]['icon'] == '✕'
        assert notifications[0]['class'] == 'error'
        assert notifications[0]['title'] == 'Hata'


@pytest.mark.unit
def test_get_notifications_warning():
    """Test get_notifications with warning message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash('Test warning', 'warning')
        notifications = get_notifications()
        assert len(notifications) == 1
        assert notifications[0]['message'] == 'Test warning'
        assert notifications[0]['category'] == 'warning'
        assert notifications[0]['icon'] == '⚠'
        assert notifications[0]['class'] == 'warning'
        assert notifications[0]['title'] == 'Uyarı'


@pytest.mark.unit
def test_get_notifications_info():
    """Test get_notifications with info message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash('Test info', 'info')
        notifications = get_notifications()
        assert len(notifications) == 1
        assert notifications[0]['message'] == 'Test info'
        assert notifications[0]['category'] == 'info'
        assert notifications[0]['icon'] == 'ℹ'
        assert notifications[0]['class'] == 'info'
        assert notifications[0]['title'] == 'Bilgi'


@pytest.mark.unit
def test_get_notifications_multiple():
    """Test get_notifications with multiple messages"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash('Test success', 'success')
        flash('Test error', 'error')
        flash('Test info', 'info')
        notifications = get_notifications()
        assert len(notifications) == 3
        assert notifications[0]['category'] == 'success'
        assert notifications[1]['category'] == 'error'
        assert notifications[2]['category'] == 'info'


@pytest.mark.unit
def test_get_notifications_invalid_category():
    """Test get_notifications with invalid category defaults to info"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        flash('Test message', 'invalid_category')
        notifications = get_notifications()
        assert len(notifications) == 1
        assert notifications[0]['category'] == 'info'
        assert notifications[0]['icon'] == 'ℹ'
        assert notifications[0]['class'] == 'info'
        assert notifications[0]['title'] == 'Bilgi'


@pytest.mark.unit
def test_with_notifications_decorator():
    """Test with_notifications decorator adds notifications to kwargs"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @with_notifications
    def template_func(**kwargs):
        return kwargs

    with app.test_request_context():
        flash('Test message', 'success')
        result = template_func()
        assert 'notifications' in result
        assert len(result['notifications']) == 1
        assert result['notifications'][0]['message'] == 'Test message'


@pytest.mark.unit
def test_with_notifications_preserves_args():
    """Test with_notifications preserves original args and kwargs"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @with_notifications
    def template_func(arg1, arg2=None, **kwargs):
        return {'arg1': arg1, 'arg2': arg2, **kwargs}

    with app.test_request_context():
        flash('Test message', 'success')
        result = template_func('value1', arg2='value2')
        assert result['arg1'] == 'value1'
        assert result['arg2'] == 'value2'
        assert 'notifications' in result


@pytest.mark.unit
def test_with_notifications_empty_notifications():
    """Test with_notifications with no flash messages"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @with_notifications
    def template_func(**kwargs):
        return kwargs

    with app.test_request_context():
        result = template_func()
        assert 'notifications' in result
        assert result['notifications'] == []


@pytest.mark.unit
def test_with_notifications_preserves_function_metadata():
    """Test with_notifications preserves function metadata"""
    @with_notifications
    def template_func():
        """Template function docstring"""
        return {}

    assert template_func.__name__ == 'template_func'
    assert template_func.__doc__ == 'Template function docstring'


@pytest.mark.unit
def test_notification_helpers_module_structure():
    """Test notification_helpers module structure"""
    import utils.notification_helpers as notification_module

    # Check for expected functions
    assert hasattr(notification_module, 'flash_success')
    assert hasattr(notification_module, 'flash_error')
    assert hasattr(notification_module, 'flash_warning')
    assert hasattr(notification_module, 'flash_info')
    assert hasattr(notification_module, 'flash_notification')
    assert hasattr(notification_module, 'get_notifications')
    assert hasattr(notification_module, 'with_notifications')
    assert hasattr(notification_module, 'NOTIFICATION_CATEGORIES')
