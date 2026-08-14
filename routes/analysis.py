"""Analysis routes - Financial analysis endpoints."""

import logging

from flask import jsonify, render_template, request, session

from bootstrap.container import get_container
from utils.auth_helpers import login_required

logger = logging.getLogger(__name__)


def _get_analysis_service():
    from bootstrap.container import get_container
    return get_container().applications.analysis()


def register_analysis_routes(bp):
    """Register analysis routes with blueprint."""
    
    analysis_service = _get_analysis_service()

    @bp.route('/analysis')
    @login_required
    def analysis_dashboard():
        """Analysis dashboard with financial metrics."""
        try:
            user_id = session.get('user_id')
            return render_template('analysis.html', user_id=user_id)
        except Exception as e:
            logger.error("Analysis dashboard error: %s", e)
            return render_template('error.html', code=500, message="Analiz sayfası yüklenirken hata oluştu"), 500

    @bp.route('/analysis/api/portfolio_real_return')
    @login_required
    def portfolio_real_return():
        """Get portfolio-level real return analysis."""
        try:
            user_id = session.get('user_id')
            country = request.args.get('country', 'TR')
            
            # Get tenant_id from user
            from models import User
            user = User.query.get(user_id)
            tenant_id = user.tenant_id if user else None
            
            result = analysis_service.get_portfolio_real_return_analysis(tenant_id, country)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error("Portfolio real return error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/analysis/api/inflation_adjusted_return')
    @login_required
    def inflation_adjusted_return():
        """Get inflation-adjusted return for an asset."""
        try:
            asset_value = request.args.get('asset_value', type=float)
            cost_basis = request.args.get('cost_basis', type=float)
            purchase_year = request.args.get('purchase_year', type=int)
            current_year = request.args.get('current_year', type=int)
            country = request.args.get('country', 'TR')
            
            result = analysis_service.get_inflation_adjusted_return(
                asset_value, cost_basis, purchase_year, current_year, country
            )
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error("Inflation adjusted return error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/analysis/api/inflation_benchmarks')
    @login_required
    def inflation_benchmarks():
        """Compare investment return with inflation benchmarks."""
        try:
            nominal_return = request.args.get('nominal_return', type=float)
            country = request.args.get('country', 'TR')
            
            result = analysis_service.compare_with_inflation_benchmarks(nominal_return, country)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error("Inflation benchmarks error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/analysis/api/portfolio_risk')
    @login_required
    def portfolio_risk():
        """Get portfolio-level risk metrics."""
        try:
            user_id = session.get('user_id')
            
            # Get tenant_id from user
            from models import User
            user = User.query.get(user_id)
            tenant_id = user.tenant_id if user else None
            
            result = analysis_service.get_portfolio_risk_metrics(tenant_id)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error("Portfolio risk error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/analysis/api/asset_risk/<int:asset_id>')
    @login_required
    def asset_risk(asset_id):
        """Get comprehensive risk metrics for an asset."""
        try:
            period_days = request.args.get('period_days', 252, type=int)
            
            from models import Asset
            asset = Asset.query.get(asset_id)
            
            if not asset:
                return jsonify({'success': False, 'error': 'Asset not found'}), 404
            
            result = analysis_service.get_asset_risk_metrics(asset, period_days)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error("Asset risk error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/analysis/api/compare_risk')
    @login_required
    def compare_risk():
        """Compare risk metrics between two assets."""
        try:
            asset1_id = request.args.get('asset1_id', type=int)
            asset2_id = request.args.get('asset2_id', type=int)
            
            from models import Asset
            asset1 = Asset.query.get(asset1_id)
            asset2 = Asset.query.get(asset2_id)
            
            if not asset1 or not asset2:
                return jsonify({'success': False, 'error': 'One or both assets not found'}), 404
            
            result = analysis_service.compare_risk_metrics(asset1, asset2)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error("Compare risk error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500
