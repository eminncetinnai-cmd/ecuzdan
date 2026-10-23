"""Logbook routes."""

import logging
import traceback

from flask import current_app, g, jsonify, redirect, render_template, request, session, url_for

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


def _get_reminder_service():
    from bootstrap import get_container as current_get_container
    return current_get_container().applications.reminder()


def _handle_reminder_upload(file):
    """Safely process and optimize uploaded reminder document/image."""
    if not file or not getattr(file, 'filename', None) or not file.filename.strip():
        return None
    import os
    import secrets
    import time
    from werkzeug.utils import secure_filename
    from utils.profile_image import optimize_image_file

    allowed_exts = {'.jpg', '.jpeg', '.png', '.webp', '.pdf'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise ValueError("Yalnızca JPG, PNG, WEBP veya PDF formatında belge yükleyebilirsiniz.")

    # File size check (max 5MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        raise ValueError("Belge boyutu 5 MB'tan büyük olamaz.")

    filename = secure_filename(f"rem_{int(time.time())}_{secrets.token_hex(4)}{ext}")
    upload_path = os.path.join('static', 'uploads', 'reminders')
    abs_upload_dir = os.path.join(current_app.root_path, upload_path)
    os.makedirs(abs_upload_dir, exist_ok=True)
    target_filepath = os.path.join(abs_upload_dir, filename)

    if ext in ('.jpg', '.jpeg', '.png', '.webp'):
        if not optimize_image_file(file, target_filepath, max_dim=1200, quality=85):
            file.seek(0)
            file.save(target_filepath)
    else:
        file.save(target_filepath)

    return f"/{upload_path}/{filename}".replace('\\', '/')


def _delete_reminder_file(doc_url):
    """Safely delete uploaded reminder file from disk."""
    if not doc_url or not isinstance(doc_url, str):
        return
    import os
    if doc_url.startswith('/static/uploads/reminders/'):
        rel_path = doc_url.lstrip('/')
        abs_path = os.path.join(current_app.root_path, rel_path)
        if os.path.exists(abs_path) and os.path.isfile(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                logger.debug(f"Could not remove old reminder file {abs_path}: {e}")



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

            reminder_category = request.args.get('reminder_category')
            reminder_search = request.args.get('reminder_search')
            reminder_status = request.args.get('reminder_status', 'all')
            is_completed = None
            if reminder_status == 'active':
                is_completed = False
            elif reminder_status == 'completed':
                is_completed = True

            reminders = _get_reminder_service().list_reminders(
                g.get('tenant_id'),
                category=reminder_category,
                search=reminder_search,
                is_completed=is_completed,
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
                reminders=reminders,
                reminder_category=reminder_category,
                reminder_search=reminder_search,
                reminder_status=reminder_status,
            )
        except Exception as e:
            logger.exception(f"Logbook index error: {e}")
            flash_error(i18n.gettext('logbook_load_error'))
            return render_template('logbook.html', entries=[], ibans=[], reminders=[], view_type='timeline', active_tab='notes')

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

    # ── Reminder Management Routes ──────────────────────────────────────
    @bp.route('/reminders/create', methods=['POST'])
    def create_reminder():
        is_ajax = is_ajax_request()
        try:
            title = request.form.get('title', '').strip()
            if not title:
                raise ValueError("Hatırlatıcı başlığı zorunludur.")
            category = request.form.get('category', 'Genel')
            frequency = request.form.get('frequency', 'Aylık')

            due_day_raw = request.form.get('due_day')
            due_day = int(due_day_raw) if due_day_raw and due_day_raw.isdigit() else None

            due_month_raw = request.form.get('due_month')
            due_month = int(due_month_raw) if due_month_raw and due_month_raw.isdigit() else None

            due_date = request.form.get('due_date') or None
            amount = request.form.get('amount') or None
            note = request.form.get('note') or None

            file = request.files.get('document')
            doc_url = _handle_reminder_upload(file)

            created = _get_reminder_service().create_reminder(
                tenant_id=g.get('tenant_id'),
                user_id=session.get('user_id'),
                title=title,
                category=category,
                frequency=frequency,
                due_day=due_day,
                due_month=due_month,
                due_date=due_date,
                amount=amount,
                note=note,
                document_url=doc_url,
            )
            if is_ajax:
                return jsonify({'success': True, 'message': 'Hatırlatıcı başarıyla kaydedildi.', 'reminder': created.to_dict()})
            handle_ajax_or_flash(True, 'Hatırlatıcı başarıyla kaydedildi.', None)
            return redirect(url_for('logbook.index', tab='reminders'))
        except ValueError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': str(e)}), 400
            handle_ajax_or_flash(False, None, str(e))
            return redirect(url_for('logbook.index', tab='reminders'))
        except Exception as e:
            logger.exception(f"Create reminder error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'Hatırlatıcı kaydedilirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'Hatırlatıcı kaydedilirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='reminders'))

    @bp.route('/reminders/<int:id>')
    def detail_reminder(id):
        is_ajax = is_ajax_request()
        try:
            record = _get_reminder_service().get_reminder(id, g.get('tenant_id'))
            if not record:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Hatırlatıcı kaydı bulunamadı.'}), 404
                flash_error('Hatırlatıcı kaydı bulunamadı.')
                return redirect(url_for('logbook.index', tab='reminders'))
            if is_ajax:
                return jsonify({'success': True, 'reminder': record.to_dict()})
            return redirect(url_for('logbook.index', tab='reminders', open_edit_reminder=id))
        except Exception as e:
            logger.exception(f"Detail reminder error: {e}")
            if is_ajax:
                return jsonify({'success': False, 'message': 'Hatırlatıcı bilgisi yüklenemedi.'}), 500
            flash_error('Hatırlatıcı bilgisi yüklenemedi.')
            return redirect(url_for('logbook.index', tab='reminders'))

    @bp.route('/reminders/<int:id>/update', methods=['POST'])
    def update_reminder(id):
        is_ajax = is_ajax_request()
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            frequency = request.form.get('frequency')

            due_day_raw = request.form.get('due_day')
            due_day = int(due_day_raw) if due_day_raw and due_day_raw.isdigit() else None

            due_month_raw = request.form.get('due_month')
            due_month = int(due_month_raw) if due_month_raw and due_month_raw.isdigit() else None

            due_date = request.form.get('due_date') or None
            amount = request.form.get('amount') or None
            note = request.form.get('note') or None

            existing = _get_reminder_service().get_reminder(id, g.get('tenant_id'))
            file = request.files.get('document')
            new_doc_url = _handle_reminder_upload(file)
            remove_document = request.form.get('remove_document') in ('1', 'true', 'on')

            if remove_document and existing and existing.document_url:
                _delete_reminder_file(existing.document_url)
            elif new_doc_url and existing and existing.document_url:
                _delete_reminder_file(existing.document_url)

            updated = _get_reminder_service().update_reminder(
                reminder_id=id,
                tenant_id=g.get('tenant_id'),
                title=title,
                category=category,
                frequency=frequency,
                due_day=due_day,
                due_month=due_month,
                due_date=due_date,
                amount=amount,
                note=note,
                document_url=new_doc_url if new_doc_url else None,
                remove_document=remove_document,
            )
            if not updated:
                raise ValueError("Hatırlatıcı kaydı bulunamadı.")
            if is_ajax:
                return jsonify({'success': True, 'message': 'Hatırlatıcı başarıyla güncellendi.', 'reminder': updated.to_dict()})
            handle_ajax_or_flash(True, 'Hatırlatıcı başarıyla güncellendi.', None)
            return redirect(url_for('logbook.index', tab='reminders'))
        except ValueError as e:
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': str(e)}), 400
            handle_ajax_or_flash(False, None, str(e))
            return redirect(url_for('logbook.index', tab='reminders'))
        except Exception as e:
            logger.exception(f"Update reminder error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'Hatırlatıcı güncellenirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'Hatırlatıcı güncellenirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='reminders'))

    @bp.route('/reminders/<int:id>/toggle-complete', methods=['POST'])
    def toggle_complete_reminder(id):
        is_ajax = is_ajax_request()
        try:
            updated = _get_reminder_service().toggle_complete(id, g.get('tenant_id'))
            if not updated:
                raise ValueError("Hatırlatıcı kaydı bulunamadı.")
            status_text = 'tamamlandı olarak işaretlendi.' if updated.is_completed else 'tekrar aktif hale getirildi.'
            msg = f"Hatırlatıcı {status_text}"
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': msg,
                    'reminder': updated.to_dict(),
                    'is_completed': updated.is_completed,
                })
            handle_ajax_or_flash(True, msg, None)
            return redirect(url_for('logbook.index', tab='reminders'))
        except Exception as e:
            logger.exception(f"Toggle complete reminder error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'Durum güncellenirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'Durum güncellenirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='reminders'))

    @bp.route('/reminders/<int:id>/delete', methods=['POST'])
    def delete_reminder(id):
        is_ajax = is_ajax_request()
        try:
            existing = _get_reminder_service().get_reminder(id, g.get('tenant_id'))
            if existing and existing.document_url:
                _delete_reminder_file(existing.document_url)

            success = _get_reminder_service().delete_reminder(id, g.get('tenant_id'))
            if not success:
                raise ValueError("Hatırlatıcı kaydı bulunamadı veya silinemedi.")
            if is_ajax:
                return jsonify({'success': True, 'message': 'Hatırlatıcı başarıyla silindi.'})
            handle_ajax_or_flash(True, 'Hatırlatıcı başarıyla silindi.', None)
            return redirect(url_for('logbook.index', tab='reminders'))
        except Exception as e:
            logger.exception(f"Delete reminder error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': 'Hatırlatıcı silinirken bir hata oluştu.'}), 500
            handle_ajax_or_flash(False, None, 'Hatırlatıcı silinirken bir hata oluştu.')
            return redirect(url_for('logbook.index', tab='reminders'))



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
