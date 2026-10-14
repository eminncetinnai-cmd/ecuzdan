"""Notification center routes (Faz 21)."""

import logging

from flask import jsonify, render_template, session

from bootstrap.container import get_container
from infrastructure.i18n import i18n
from utils.db_session import rollback_session
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _get_notification_app():
    from bootstrap.container import get_container
    return get_container().applications.notifications()


def _get_settings_app():
    from bootstrap.container import get_container
    return get_container().applications.settings()


def _serialize(notification):
    return {
        'id': notification.id,
        'category': notification.category,
        'severity': notification.severity,
        'title': notification.title,
        'body': notification.body,
        'link': notification.link,
        'is_read': notification.is_read,
        'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M') if notification.created_at else '',
    }


def register_notification_routes(bp):
    @bp.route('/')
    @login_required
    def notifications_page():
        """Bildirimler sayfası."""
        return render_template('notifications.html')

    @bp.route('/api')
    @login_required
    def list_notifications():
        """
        Zil açıldığında çağrılır: önce kurallar değerlendirilir, sonra liste döner.

        Değerlendirme burada yapılır çünkü her istekte çalıştırmak gereksiz
        sorgu maliyeti yaratırdı; kullanıcı zile bastığında güncel veri ister.
        """
        try:
            user_id = session['user_id']
            user = get_container().applications.session().get_current_user(user_id)
            settings_app = _get_settings_app()
            notification_app = _get_notification_app()
            preferences = settings_app.get_preferences(user_id)
            notification_app.refresh(user, preferences)
            items = notification_app.list_for_user(user_id)

            logger.info(f"Notifications loaded for user {user_id}: {len(items)} items")

            return jsonify({
                'success': True,
                'unread': notification_app.unread_count(user_id),
                'items': [_serialize(n) for n in items],
            })
        except Exception as e:
            logger.exception(f"Notification list error: {e}")
            rollback_session()
            return jsonify({'success': False, 'message': i18n.gettext('notifications_load_failed')}), 500

    @bp.route('/unread_count')
    @login_required
    def unread_count():
        """Sayfa açılışında rozet için — kural değerlendirmesi YAPMAZ (ucuz)."""
        try:
            notification_app = _get_notification_app()
            return jsonify({'success': True, 'unread': notification_app.unread_count(session['user_id'])})
        except Exception as e:
            logger.exception(f"Notification count error: {e}")
            return jsonify({'success': False, 'unread': 0}), 500

    @bp.route('/<int:notification_id>/read', methods=['POST'])
    @login_required
    def mark_read(notification_id):
        try:
            notification_app = _get_notification_app()
            notification_app.mark_read(session['user_id'], notification_id)
            return jsonify({'success': True, 'unread': notification_app.unread_count(session['user_id'])})
        except PermissionError as e:
            return jsonify({'success': False, 'message': str(e)}), 403
        except Exception as e:
            logger.exception(f"Notification mark read error: {e}")
            rollback_session()
            return jsonify({'success': False, 'message': i18n.gettext('notifications_update_failed')}), 500

    @bp.route('/read_all', methods=['POST'])
    @login_required
    def mark_all_read():
        try:
            notification_app = _get_notification_app()
            count = notification_app.mark_all_read(session['user_id'])
            return jsonify({'success': True, 'marked': count, 'unread': 0})
        except Exception as e:
            logger.exception(f"Notification mark all read error: {e}")
            rollback_session()
            return jsonify({'success': False, 'message': i18n.gettext('notifications_update_failed')}), 500
    @bp.route('/delete_read', methods=['POST'])
    @login_required
    def delete_read():
        try:
            notification_app = _get_notification_app()
            count = notification_app.delete_read(session['user_id'])
            return jsonify({'success': True, 'deleted': count, 'unread': notification_app.unread_count(session['user_id'])})
        except Exception as e:
            logger.exception(f'Notification delete read error: {e}')
            rollback_session()
            return jsonify({'success': False, 'message': i18n.gettext('notifications_delete_all_failed')}), 500
    @bp.route('/<int:notification_id>/delete', methods=['POST'])
    @login_required
    def delete_notification(notification_id):
        try:
            notification_app = _get_notification_app()
            notification_app.delete(session['user_id'], notification_id)
            return jsonify({'success': True, 'deleted': notification_id})
        except PermissionError as e:
            rollback_session()
            return jsonify({'success': False, 'message': str(e)}), 403
        except Exception as e:
            logger.exception(f'Notification delete error: {e}')
            rollback_session()
            return jsonify({'success': False, 'message': i18n.gettext('notifications_delete_failed')}), 500
