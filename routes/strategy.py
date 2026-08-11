"""Strategy routes."""

import logging

from flask import jsonify, render_template, request, session

from bootstrap.container import get_container
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _get_strategy_service():
    from bootstrap.container import get_container
    return get_container().applications.strategy()


def register_strategy_routes(bp):
    strategy_service = _get_strategy_service()

    @bp.route('/strategy')
    @login_required
    def strategy():
        try:
            return render_template('strategy.html', **strategy_service.page_context(session.get('user_id')))
        except Exception as e:
            logger.exception(f"Strategy page error: {e}")
            import traceback
            traceback.print_exc()
            return render_template('error.html', code=500, message="Strateji sayfası yüklenirken hata oluştu"), 500

    @bp.route('/strategy/settings', methods=['GET', 'POST'])
    @login_required
    def strategy_settings():
        try:
            user_id = session.get('user_id')
            if request.method == 'POST':
                strategy_service.update_settings_from_form(user_id, request.form)
                return jsonify({'status': 'success', 'message': 'Ayarlar kaydedildi'})
            return jsonify(strategy_service.settings_payload(strategy_service.get_or_create_settings(user_id)))
        except Exception as e:
            logger.exception(f"Strategy settings error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @bp.route('/strategy/api/mc-scenarios')
    @login_required
    def mc_scenarios():
        return jsonify({
            'conservative': {
                'label': 'Muhafazakar',
                'description': 'Düşük risk, istikrarlı büyüme',
                'return': 0.08,
                'volatility': 0.12,
                'color': 'emerald',
            },
            'balanced': {
                'label': 'Dengeli',
                'description': 'Orta risk, dengeli büyüme',
                'return': 0.15,
                'volatility': 0.20,
                'color': 'amber',
            },
            'aggressive': {
                'label': 'Agresif',
                'description': 'Yüksek risk, yüksek büyüme',
                'return': 0.22,
                'volatility': 0.30,
                'color': 'rose',
            },
        })
