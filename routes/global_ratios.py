"""Global Macro & Financial Market Ratios Dashboard routes."""

import csv
import io
import logging

from flask import Blueprint, Response, jsonify, render_template, request, session

from application.ratios.queries.get_ratios_dashboard import GetRatiosDashboardQuery
from utils.auth_helpers import login_required

logger = logging.getLogger(__name__)


def register_global_ratios_routes(bp: Blueprint) -> None:
    """Register macro ratios routes with blueprint."""

    @bp.route('/global-ratios')
    @login_required
    def global_ratios_dashboard():
        """Render 20 World-Renowned Macro & Financial Market Ratios Dashboard."""
        try:
            query = GetRatiosDashboardQuery()
            data = query.execute(range_key='all')

            if 'correlation_matrix' not in data:
                try:
                    from domain.ratios.data.historical_ratios_data import HISTORICAL_RATIOS_DEFINITIONS
                    from domain.ratios.services.macro_correlation_service import MacroCorrelationService
                    corr_service = MacroCorrelationService()
                    corr_matrix_obj = corr_service.build_matrix(HISTORICAL_RATIOS_DEFINITIONS)
                    data['correlation_matrix'] = {
                        "labels": [{"code": l[0], "name": l[1]} for l in corr_matrix_obj.labels],
                        "period_count": corr_matrix_obj.period_count,
                        "period_range": corr_matrix_obj.period_range,
                        "grid": [
                            [
                                {
                                    "row_code": cell.row_code,
                                    "row_name": cell.row_name,
                                    "col_code": cell.col_code,
                                    "col_name": cell.col_name,
                                    "coefficient": cell.coefficient,
                                    "strength_label": cell.strength_label,
                                    "color_class": cell.color_class,
                                    "description": cell.description,
                                }
                                for cell in row
                            ]
                            for row in corr_matrix_obj.matrix
                        ],
                    }
                except Exception as c_err:
                    logger.warning("Fallback correlation matrix failed: %s", c_err)
                    data['correlation_matrix'] = {
                        "labels": [],
                        "period_count": 32,
                        "period_range": "2023 - 2026",
                        "grid": [],
                    }

            if 'executive_briefing' not in data:
                kpis = data.get('kpis', {})
                data['executive_briefing'] = {
                    "period": kpis.get("latest_period_display", "Ağustos 2026"),
                    "healthy_count": kpis.get("healthy_count", 0),
                    "neutral_count": kpis.get("neutral_count", 0),
                    "elevated_count": kpis.get("elevated_count", 0),
                    "headline": "Küresel Varlık Piyasaları Makro İklim & Risk Değerlendirmesi",
                    "market_stance": "Dengeli / Seçici İyimserlik (Seçici Büyüme & Gergin Değerleme)",
                    "key_risks": ["Buffett Indicator", "Altın/Gümüş Rasyosu"],
                    "key_anchors": ["Türkiye 5Y CDS", "VIX Volatilite"],
                    "vix_status": "Sakin",
                    "cds_status": "İyileşiyor",
                }

            return render_template(
                'global_ratios.html',
                data=data,
                user_id=session.get('user_id'),
            )
        except Exception as exc:
            logger.error("Global ratios dashboard error: %s", exc)
            return render_template(
                'error.html',
                code=500,
                message="Küresel Rasyolar sayfası yüklenirken hata oluştu",
            ), 500

    @bp.route('/global-ratios/api/data')
    @login_required
    def get_ratios_api_data():
        """Return JSON payload of ratios with timeframe and category filters."""
        try:
            range_key = request.args.get('range', 'all').strip().lower()
            category = request.args.get('category', None)
            query = GetRatiosDashboardQuery()
            result = query.execute(range_key=range_key, category_filter=category)
            return jsonify({'success': True, 'data': result})
        except Exception as exc:
            logger.error("Global ratios API error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/global-ratios/api/export')
    @login_required
    def export_ratios_csv():
        """Export all 20 macro ratios monthly time series to CSV."""
        try:
            query = GetRatiosDashboardQuery()
            data = query.execute(range_key='all')

            output = io.StringIO()
            writer = csv.writer(output, delimiter=';')
            writer.writerow([
                'Rasyo Kodu',
                'Rasyo Adı',
                'Kategori',
                'Son Değer',
                'Birim',
                'Normal Min',
                'Normal Max',
                'Sinyal Durumu',
                'Aylık Değişim (%)',
                'Yıllık Değişim (%)',
                'Son Dönem'
            ])

            for r in data.get('ratios', []):
                writer.writerow([
                    r['code'],
                    r['name'],
                    r['category_name'],
                    r['latest_value'],
                    r['unit'],
                    r['normal_min'],
                    r['normal_max'],
                    r['signal_label'],
                    r['mom_change_pct'],
                    r['yoy_change_pct'],
                    r['latest_display_date']
                ])

            filename = "e_cuzdan_kuresel_makro_rasyolar.csv"
            return Response(
                "\ufeff" + output.getvalue(),
                mimetype="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as exc:
            logger.error("Global ratios CSV export error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/global-ratios/api/sync', methods=['POST'])
    @login_required
    def sync_live_ratios():
        """Fetch live market data for macro ratios and return updated payload."""
        try:
            query = GetRatiosDashboardQuery()
            sync_info = query.sync_live_market_data()
            result = query.execute(range_key='all')
            return jsonify({
                'success': True,
                'message': f"{sync_info.get('synced_count', 0)} adet piyasa rasyosu canlı fiyatlarla güncellendi.",
                'data': result,
                'sync_info': sync_info
            })
        except Exception as exc:
            logger.error("Global ratios live sync error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/global-ratios/api/correlation')
    @login_required
    def get_correlation_matrix_api():
        """Return cross-asset correlation matrix JSON payload."""
        try:
            query = GetRatiosDashboardQuery()
            data = query.execute(range_key='all')
            return jsonify({'success': True, 'data': data.get('correlation_matrix', {})})
        except Exception as exc:
            logger.error("Global ratios correlation API error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/global-ratios/api/briefing')
    @login_required
    def get_executive_briefing_api():
        """Return executive macro briefing JSON payload."""
        try:
            query = GetRatiosDashboardQuery()
            data = query.execute(range_key='all')
            return jsonify({'success': True, 'data': data.get('executive_briefing', {})})
        except Exception as exc:
            logger.error("Global ratios briefing API error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/global-ratios/api/alerts/config', methods=['POST'])
    @login_required
    def save_alerts_config():
        """Save user macro alert preferences."""
        try:
            body = request.get_json() or {}
            enabled = bool(body.get('enabled', True))
            sensitivity = body.get('sensitivity', 'BALANCED')
            channels = body.get('channels', ['IN_APP'])

            session['macro_alerts_config'] = {
                'enabled': enabled,
                'sensitivity': sensitivity,
                'channels': channels,
            }
            return jsonify({
                'success': True,
                'message': 'Makro alarm tercihleri kaydedildi.',
                'config': session['macro_alerts_config']
            })
        except Exception as exc:
            logger.error("Save macro alerts config error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

