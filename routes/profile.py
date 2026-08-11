"""Investor profile routes."""

import logging

from flask import g, jsonify, redirect, render_template, request, session, url_for

from bootstrap.container import get_container
from domain.tenant.accessor import get_tenant as get_tenant_id
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.notification_helpers import flash_error

logger = logging.getLogger(__name__)


def _get_profile_service():
    from bootstrap import get_container
    return get_container().applications.profile()


def register_profile_routes(bp):
    profile_service = _get_profile_service()

    @bp.route('/')
    def index():
        try:
            return render_template(
                'profile.html',
                **profile_service.index_context(get_tenant_id(), session.get('user_id')),
            )
        except Exception as e:
            logger.exception(f"Profile index error: {e}")
            flash_error('Profil sayfası yüklenirken hata oluştu.')
            return render_template('profile.html', active_profile=None, profile_history=[])

    @bp.route('/start')
    def start():
        try:
            return render_template('profile_wizard.html', **profile_service.wizard_context())
        except Exception as e:
            logger.exception(f"Profile start error: {e}")
            flash_error('Test başlatılırken hata oluştu.')
            return redirect(url_for('profile.index'))

    @bp.route('/submit', methods=['POST'])
    def submit():
        is_ajax = is_ajax_request()
        try:
            profile, profile_result = profile_service.submit_answers(
                g.get('tenant_id'),
                session.get('user_id'),
                (request.json or {}).get('answers', []),
            )
            logger.info(f"Profile created for user {session.get('user_id')}: {profile_result['final_risk_level']}")
            response = handle_ajax_or_flash(True, 'Profil başarıyla oluşturuldu!', 'Profil oluşturulamadı.')
            if response:
                return response
        except ValueError as e:
            profile_service.rollback()
            response = handle_ajax_or_flash(False, None, f'Validasyon hatası: {str(e)}')
            if response:
                return response
        except Exception as e:
            logger.exception(f"Profile submit error: {e}")
            profile_service.rollback()
            response = handle_ajax_or_flash(False, None, 'Profil oluşturulurken beklenmeyen bir hata oluştu.')
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('profile.index'))

    @bp.route('/result/<int:id>')
    def result(id):
        try:
            context = profile_service.result_context(id, get_tenant_id())
            if not context:
                flash_error('Profil bulunamadı veya yetkiniz yok.')
                return redirect(url_for('profile.index'))
            return render_template('profile_result.html', **context)
        except Exception as e:
            logger.exception(f"Profile result error: {e}")
            flash_error('Profil detayı yüklenirken hata oluştu.')
            return redirect(url_for('profile.index'))

    @bp.route('/api/questions')
    def api_questions():
        try:
            return jsonify(profile_service.questions_payload())
        except Exception as e:
            logger.exception(f"API questions error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @bp.route('/api/submit', methods=['POST'])
    def api_submit():
        try:
            profile, profile_result = profile_service.submit_answers(
                g.get('tenant_id'),
                session.get('user_id'),
                (request.json or {}).get('answers', []),
            )
            logger.info(f"Profile created via API for user {session.get('user_id')}: {profile_result['final_risk_level']}")
            return jsonify({'success': True, 'profile_id': profile.id, 'result': profile_result})
        except ValueError as e:
            profile_service.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.exception(f"API submit error: {e}")
            profile_service.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @bp.route('/api/profile/<int:id>')
    def api_profile(id):
        try:
            profile_data = profile_service.profile_payload(id, get_tenant_id())
            if not profile_data:
                return jsonify({'success': False, 'message': 'Profil bulunamadı'}), 404
            return jsonify({'success': True, 'profile': profile_data})
        except Exception as e:
            logger.exception(f"API profile error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @bp.route('/api/history')
    def api_history():
        try:
            return jsonify({
                'success': True,
                'profiles': profile_service.history_payload(get_tenant_id(), session.get('user_id')),
            })
        except Exception as e:
            logger.exception(f"API history error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
