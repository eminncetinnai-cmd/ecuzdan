"""Logbook routes."""

import logging
import traceback

from flask import g, jsonify, redirect, render_template, request, session, url_for

from bootstrap.container import get_container  # noqa: F401
from infrastructure.i18n import i18n
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.db_session import rollback_session
from utils.notification_helpers import flash_error
from validators.request_validators import logbook_entry_from_request

logger = logging.getLogger(__name__)


def _get_logbook_service():
    from bootstrap import get_container as current_get_container
    return current_get_container().applications.logbook()


def _get_iban_service():
    from bootstrap import get_container as current_get_container
    return current_get_container().applications.iban()


def register_logbook_routes(bp):
    logbook_service = _get_logbook_service()

    @bp.route('/')
    def index():
        try:
            filters = _filters_from_request()
            active_tab = request.args.get('tab', 'notes')
            iban_category = request.args.get('iban_category')
            iban_search = request.args.get('iban_search')
            ibans = _get_iban_service().list_ibans(
                g.get('tenant_id'),
                category=iban_category,
                search=iban_search,
            )
            return render_template(
                'logbook.html',
                entries=logbook_service.list_entries(g.get('tenant_id'), filters),
                view_type=request.args.get('view', 'timeline'),
                category_filter=filters.get('category'),
                date_filter=filters.get('date_from'),
                ibans=ibans,
                active_tab=active_tab,
                iban_category=iban_category,
                iban_search=iban_search,
            )
        except Exception as e:
            logger.exception(f"Logbook index error: {e}")
            flash_error(i18n.gettext('logbook_load_error'))
            return render_template('logbook.html', entries=[], ibans=[], view_type='timeline', active_tab='notes')

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
            response = handle_ajax_or_flash(True, i18n.gettext('logbook_save'), i18n.gettext('logbook_save_failed'))
            if response:
                return response
        except ValueError as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f"{i18n.gettext('logbook_save_failed')}: {str(e)}")
            if response:
                return response
        except Exception as e:
            logger.error("LOGBOOK CREATE GERÇEK HATA - Tip: %s, Mesaj: %s", type(e).__name__, str(e))
            logger.error("Tam traceback:\n%s", traceback.format_exc())
            rollback_session()
            response = handle_ajax_or_flash(False, None, i18n.gettext('logbook_save_error'))
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': i18n.gettext('logbook_save_error')})
        return redirect(url_for('logbook.index'))

    @bp.route('/<int:id>')
    def detail(id):
        is_ajax = is_ajax_request()
        try:
            entry_data = logbook_service.detail_payload(id, g.get('tenant_id'))
            if not entry_data:
                if is_ajax:
                    return jsonify({'success': False, 'message': i18n.gettext('logbook_not_found')}), 404
                flash_error(i18n.gettext('logbook_not_found'))
                return redirect(url_for('logbook.index'))

            if is_ajax:
                return jsonify({'success': True, 'entry': entry_data})
            return redirect(url_for('logbook.index', open_edit=id))
        except Exception as e:
            logger.exception(f"Logbook detail error: {e}")
            if is_ajax:
                return jsonify({'success': False, 'message': i18n.gettext('logbook_load_error')}), 500
            flash_error(i18n.gettext('logbook_load_error'))
            return redirect(url_for('logbook.index'))

    @bp.route('/<int:id>/update', methods=['POST'])
    def update(id):
        is_ajax = is_ajax_request()
        try:
            logbook_service.update_entry(id, logbook_entry_from_request(request.form), g.get('tenant_id'))
            response = handle_ajax_or_flash(True, i18n.gettext('logbook_save'), i18n.gettext('logbook_save_failed'))
            if response:
                return response
        except ValueError as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f"{i18n.gettext('logbook_save_failed')}: {str(e)}")
            if response:
                return response
        except Exception as e:
            logger.exception(f"Update logbook entry error: {e}")
            rollback_session()
            response = handle_ajax_or_flash(False, None, i18n.gettext('logbook_save_error'))
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': i18n.gettext('logbook_save_error')})
        return redirect(url_for('logbook.index'))

    @bp.route('/<int:id>/delete', methods=['POST'])
    def delete(id):
        is_ajax = is_ajax_request()
        try:
            logbook_service.delete_entry(id, g.get('tenant_id'))
            response = handle_ajax_or_flash(True, i18n.gettext('logbook_delete'), i18n.gettext('logbook_delete_failed'))
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
            response = handle_ajax_or_flash(False, None, i18n.gettext('logbook_delete_error'))
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': i18n.gettext('logbook_save_error')})
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

    # ── IBAN Management Routes ───────────────────────────────────────────

    @bp.route('/ibans/create', methods=['POST'])
    def create_iban():
        is_ajax = is_ajax_request()
        try:
            title = request.form.get('title', '').strip()
            iban = request.form.get('iban', '').strip()
            bank_name = request.form.get('bank_name', '').strip()
            account_holder = request.form.get('account_holder', '').strip()
            category = request.form.get('category', 'kendi_hesabim').strip()
            note = request.form.get('note', '').strip()

            if not title:
                raise ValueError("Hesap başlığı zorunludur.")
            if not iban:
                raise ValueError("IBAN numarası zorunludur.")

            is_favorite = request.form.get('is_favorite') in ('1', 'true', 'True', True)
            easy_address_type = request.form.get('easy_address_type')
            easy_address = request.form.get('easy_address')

            created = _get_iban_service().create_iban(
                tenant_id=g.get('tenant_id'),
                user_id=session.get('user_id'),
                title=title,
                iban=iban,
                bank_name=bank_name or None,
                account_holder=account_holder or None,
                category=category,
                note=note or None,
                is_favorite=is_favorite,
                easy_address_type=easy_address_type or None,
                easy_address=easy_address or None,
            )
            if is_ajax:
                return jsonify({'success': True, 'message': 'IBAN başarıyla kaydedildi.', 'iban': created.to_dict()})
            handle_ajax_or_flash(True, 'IBAN başarıyla kaydedildi.', None)
            return redirect(url_for('logbook.index', tab='ibans'))
        except ValueError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': str(e)}), 400
            handle_ajax_or_flash(False, None, str(e))
            return redirect(url_for('logbook.index', tab='ibans'))
        except Exception as e:
            logger.exception(f"Create IBAN error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'IBAN kaydedilirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'IBAN kaydedilirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='ibans'))

    @bp.route('/ibans/<int:id>')
    def detail_iban(id):
        is_ajax = is_ajax_request()
        try:
            record = _get_iban_service().get_iban(id, g.get('tenant_id'))
            if not record:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'IBAN kaydı bulunamadı.'}), 404
                flash_error('IBAN kaydı bulunamadı.')
                return redirect(url_for('logbook.index', tab='ibans'))
            if is_ajax:
                return jsonify({'success': True, 'iban': record.to_dict()})
            return redirect(url_for('logbook.index', tab='ibans', open_edit_iban=id))
        except Exception as e:
            logger.exception(f"Detail IBAN error: {e}")
            if is_ajax:
                return jsonify({'success': False, 'message': 'IBAN bilgisi yüklenemedi.'}), 500
            flash_error('IBAN bilgisi yüklenemedi.')
            return redirect(url_for('logbook.index', tab='ibans'))

    @bp.route('/ibans/<int:id>/update', methods=['POST'])
    def update_iban(id):
        is_ajax = is_ajax_request()
        try:
            title = request.form.get('title')
            iban = request.form.get('iban')
            bank_name = request.form.get('bank_name')
            account_holder = request.form.get('account_holder')
            category = request.form.get('category')
            note = request.form.get('note')

            is_favorite = None
            if 'is_favorite' in request.form:
                is_favorite = request.form.get('is_favorite') in ('1', 'true', 'True', True)
            easy_address_type = request.form.get('easy_address_type')
            easy_address = request.form.get('easy_address')

            updated = _get_iban_service().update_iban(
                iban_id=id,
                tenant_id=g.get('tenant_id'),
                title=title,
                iban=iban,
                bank_name=bank_name,
                account_holder=account_holder,
                category=category,
                note=note,
                is_favorite=is_favorite,
                easy_address_type=easy_address_type,
                easy_address=easy_address,
            )
            if not updated:
                raise ValueError("IBAN kaydı bulunamadı.")
            if is_ajax:
                return jsonify({'success': True, 'message': 'IBAN başarıyla güncellendi.', 'iban': updated.to_dict()})
            handle_ajax_or_flash(True, 'IBAN başarıyla güncellendi.', None)
            return redirect(url_for('logbook.index', tab='ibans'))
        except ValueError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': str(e)}), 400
            handle_ajax_or_flash(False, None, str(e))
            return redirect(url_for('logbook.index', tab='ibans'))
        except Exception as e:
            logger.exception(f"Update IBAN error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'IBAN güncellenirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'IBAN güncellenirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='ibans'))

    @bp.route('/ibans/<int:id>/toggle-favorite', methods=['POST'])
    def toggle_favorite_iban(id):
        is_ajax = is_ajax_request()
        try:
            updated = _get_iban_service().toggle_favorite(id, g.get('tenant_id'))
            if not updated:
                raise ValueError("IBAN kaydı bulunamadı.")
            msg = 'Hesap favorilere eklendi.' if updated.is_favorite else 'Hesap favorilerden çıkarıldı.'
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': msg,
                    'is_favorite': updated.is_favorite,
                    'iban': updated.to_dict(),
                })
            handle_ajax_or_flash(True, msg, None)
            return redirect(url_for('logbook.index', tab='ibans'))
        except Exception as e:
            logger.exception(f"Toggle favorite error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': str(e)}), 400
            handle_ajax_or_flash(False, None, str(e))
            return redirect(url_for('logbook.index', tab='ibans'))

    @bp.route('/ibans/<int:id>/delete', methods=['POST'])
    def delete_iban(id):
        is_ajax = is_ajax_request()
        try:
            success = _get_iban_service().delete_iban(id, g.get('tenant_id'))
            if not success:
                raise ValueError("Silinecek IBAN bulunamadı.")
            if is_ajax:
                return jsonify({'success': True, 'message': 'IBAN başarıyla silindi.'})
            handle_ajax_or_flash(True, 'IBAN başarıyla silindi.', None)
            return redirect(url_for('logbook.index', tab='ibans'))
        except ValueError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': str(e)}), 400
            handle_ajax_or_flash(False, None, str(e))
            return redirect(url_for('logbook.index', tab='ibans'))
        except Exception as e:
            logger.exception(f"Delete IBAN error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'IBAN silinirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'IBAN silinirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='ibans'))

    @bp.route('/api/ibans')
    def api_ibans():
        try:
            records = _get_iban_service().list_ibans(
                g.get('tenant_id'),
                category=request.args.get('category'),
                search=request.args.get('search'),
            )
            return jsonify({'success': True, 'ibans': [r.to_dict() for r in records]})
        except Exception as e:
            logger.exception(f"API ibans error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @bp.route('/api/ibans/detect-bank')
    def api_detect_bank():
        from domain.analysis.services.iban_service import IbanService
        raw_iban = request.args.get('iban', '')
        clean = IbanService.clean_iban(raw_iban)
        bank_name = IbanService.detect_bank_name(clean)
        formatted = IbanService.format_iban(clean)
        is_valid, error = IbanService.validate_iban(clean) if clean else (False, '')
        return jsonify({
            'success': True,
            'clean_iban': clean,
            'formatted_iban': formatted,
            'bank_name': bank_name or '',
            'is_valid': is_valid,
            'validation_error': error,
        })


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
