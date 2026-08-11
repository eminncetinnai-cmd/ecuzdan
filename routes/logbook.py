"""Logbook routes."""

import logging
import traceback

from flask import g, jsonify, redirect, render_template, request, session, url_for

from bootstrap.container import get_container
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.db_session import rollback_session
from utils.notification_helpers import flash_error
from validators.request_validators import logbook_entry_from_request

logger = logging.getLogger(__name__)


def _get_logbook_service():
    from bootstrap import get_container
    return get_container().applications.logbook()


def register_logbook_routes(bp):
    logbook_service = _get_logbook_service()

    @bp.route('/')
    def index():
        try:
            filters = _filters_from_request()
            return render_template(
                'logbook.html',
                entries=logbook_service.list_entries(g.get('tenant_id'), filters),
                view_type=request.args.get('view', 'timeline'),
                category_filter=filters.get('category'),
                date_filter=filters.get('date_from'),
            )
        except Exception as e:
            logger.exception(f"Logbook index error: {e}")
            flash_error('Logbook yüklenirken hata oluştu.')
            return render_template('logbook.html', entries=[], view_type='timeline')

    @bp.route('/timeline')
    def timeline():
        return redirect(url_for('logbook.index', view='timeline'))

    @bp.route('/calendar')
    def calendar():
        return redirect(url_for('logbook.index', view='calendar'))

    @bp.route('/create', methods=['POST'])
    def create():
        is_ajax = is_ajax_request()
        try:
            logbook_service.create_entry(
                logbook_entry_from_request(request.form),
                tenant_id=g.get('tenant_id'),
                user_id=session.get('user_id'),
            )
            response = handle_ajax_or_flash(True, 'Kayıt başarıyla oluşturuldu!', 'Kayıt oluşturulamadı.')
            if response:
                return response
        except ValueError as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f'Validasyon hatası: {str(e)}')
            if response:
                return response
        except Exception as e:
            logger.error("LOGBOOK CREATE GERÇEK HATA - Tip: %s, Mesaj: %s", type(e).__name__, str(e))
            logger.error("Tam traceback:\n%s", traceback.format_exc())
            rollback_session()
            response = handle_ajax_or_flash(False, None, 'Kayıt oluşturulurken beklenmeyen bir hata oluştu.')
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('logbook.index'))

    @bp.route('/<int:id>')
    def detail(id):
        is_ajax = is_ajax_request()
        try:
            entry_data = logbook_service.detail_payload(id, g.get('tenant_id'))
            if not entry_data:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Kayıt bulunamadı veya yetkiniz yok.'}), 404
                flash_error('Kayıt bulunamadı veya yetkiniz yok.')
                return redirect(url_for('logbook.index'))

            if is_ajax:
                return jsonify({'success': True, 'entry': entry_data})
            return redirect(url_for('logbook.index', open_edit=id))
        except Exception as e:
            logger.exception(f"Logbook detail error: {e}")
            if is_ajax:
                return jsonify({'success': False, 'message': 'Kayıt yüklenirken hata oluştu.'}), 500
            flash_error('Kayıt detayı yüklenirken hata oluştu.')
            return redirect(url_for('logbook.index'))

    @bp.route('/<int:id>/update', methods=['POST'])
    def update(id):
        is_ajax = is_ajax_request()
        try:
            logbook_service.update_entry(id, logbook_entry_from_request(request.form), g.get('tenant_id'))
            response = handle_ajax_or_flash(True, 'Kayıt başarıyla güncellendi!', 'Kayıt güncellenemedi.')
            if response:
                return response
        except ValueError as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f'Validasyon hatası: {str(e)}')
            if response:
                return response
        except Exception as e:
            logger.exception(f"Update logbook entry error: {e}")
            rollback_session()
            response = handle_ajax_or_flash(False, None, 'Kayıt güncellenirken beklenmeyen bir hata oluştu.')
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('logbook.index'))

    @bp.route('/<int:id>/delete', methods=['POST'])
    def delete(id):
        is_ajax = is_ajax_request()
        try:
            logbook_service.delete_entry(id, g.get('tenant_id'))
            response = handle_ajax_or_flash(True, 'Kayıt silindi.', 'Kayıt silinemedi.')
            if response:
                return response
        except ValueError as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, str(e))
            if response:
                return response
        except Exception as e:
            logger.exception(f"Delete logbook entry error: {e}")
            rollback_session()
            response = handle_ajax_or_flash(False, None, 'Kayıt silinirken beklenmeyen bir hata oluştu.')
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('logbook.index'))

    @bp.route('/api/entries')
    def api_entries():
        try:
            return jsonify(logbook_service.entries_api_payload(
                g.get('tenant_id'),
                _filters_from_request(),
                page=request.args.get('page', 1, type=int),
                per_page=request.args.get('per_page', 20, type=int),
            ))
        except Exception as e:
            logger.exception(f"API entries error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @bp.route('/api/calendar-events')
    def api_calendar_events():
        try:
            filters = {
                'date_from': request.args.get('start'),
                'date_to': request.args.get('end'),
            }
            return jsonify(logbook_service.calendar_events(g.get('tenant_id'), filters, _get_category_color))
        except Exception as e:
            logger.exception(f"API calendar events error: {e}")
            return jsonify([]), 500

    @bp.route('/api/assets')
    def api_assets():
        try:
            return jsonify(logbook_service.assets_api_payload(g.get('tenant_id')))
        except Exception as e:
            logger.exception(f"API assets error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @bp.route('/api/transactions')
    def api_transactions():
        try:
            return jsonify(logbook_service.transactions_api_payload(g.get('tenant_id')))
        except Exception as e:
            logger.exception(f"API transactions error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500


def _filters_from_request():
    return {
        'category': request.args.get('category'),
        'date_from': request.args.get('date'),
    }


def _get_category_color(category):
    colors = {
        'Finansal': '#3b82f6',
        'Yatırım': '#10b981',
        'Ödeme': '#f59e0b',
        'Kilometre Taşı': '#8b5cf6',
        'Fikir': '#6b7280',
    }
    return colors.get(category, '#3b82f6')
