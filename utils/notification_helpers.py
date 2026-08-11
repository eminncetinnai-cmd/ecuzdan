"""
Notification Helpers - Standart Bildirim Sistemi
Flash mesajları ve toast bildirimleri için yardımcı fonksiyonlar
"""

from functools import wraps

from flask import flash, get_flashed_messages

# Bildirim kategorileri
NOTIFICATION_CATEGORIES = {
    'success': {'icon': '✓', 'class': 'success', 'title': 'Başarı'},
    'error': {'icon': '✕', 'class': 'error', 'title': 'Hata'},
    'warning': {'icon': '⚠', 'class': 'warning', 'title': 'Uyarı'},
    'info': {'icon': 'ℹ', 'class': 'info', 'title': 'Bilgi'},
}


def flash_success(message):
    """Başarı mesajı flash'lar"""
    flash(message, 'success')


def flash_error(message):
    """Hata mesajı flash'lar"""
    flash(message, 'error')


def flash_warning(message):
    """Uyarı mesajı flash'lar"""
    flash(message, 'warning')


def flash_info(message):
    """Bilgi mesajı flash'lar"""
    flash(message, 'info')


def flash_notification(message, category='info'):
    """
    Genel bildirim flash'lar

    Args:
        message: Mesaj içeriği
        category: Bildirim kategorisi (success, error, warning, info)
    """
    if category not in NOTIFICATION_CATEGORIES:
        category = 'info'
    flash(message, category)


def get_notifications():
    """
    Tüm flash mesajlarını standart formatta döner

    Returns:
        list: Bildirim nesneleri listesi
    """
    messages = get_flashed_messages(with_categories=True)
    notifications = []

    for category, message in messages:
        if category in NOTIFICATION_CATEGORIES:
            notifications.append({
                'message': message,
                'category': category,
                'icon': NOTIFICATION_CATEGORIES[category]['icon'],
                'class': NOTIFICATION_CATEGORIES[category]['class'],
                'title': NOTIFICATION_CATEGORIES[category]['title']
            })
        else:
            notifications.append({
                'message': message,
                'category': 'info',
                'icon': NOTIFICATION_CATEGORIES['info']['icon'],
                'class': NOTIFICATION_CATEGORIES['info']['class'],
                'title': NOTIFICATION_CATEGORIES['info']['title']
            })

    return notifications


def with_notifications(template_func):
    """
    Template fonksiyonuna bildirimleri ekleyen decorator

    Args:
        template_func: Template render fonksiyonu

    Returns:
        Decorated function
    """
    @wraps(template_func)
    def wrapper(*args, **kwargs):
        kwargs['notifications'] = get_notifications()
        return template_func(*args, **kwargs)
    return wrapper
