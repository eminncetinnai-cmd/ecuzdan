"""Central bank reserves and global gold holdings routes."""

import csv
import io
import logging

from flask import Blueprint, Response, jsonify, render_template, request, session

from application.central_bank.queries.get_reserves_overview import GetReservesOverviewQuery
from utils.auth_helpers import login_required

logger = logging.getLogger(__name__)


def register_central_bank_reserves_routes(bp: Blueprint) -> None:
    """Register central bank reserves routes with blueprint."""

    @bp.route('/central-bank-reserves')
    @login_required
    def central_bank_reserves_dashboard():
        """Render Central Bank Reserves and Global Gold Holdings dashboard."""
        try:
            query = GetReservesOverviewQuery()
            overview_data = query.execute(range_key='all')
            return render_template(
                'central_bank_reserves.html',
                data=overview_data,
                user_id=session.get('user_id'),
            )
        except Exception as exc:
            logger.error("Central bank reserves dashboard error: %s", exc)
            return render_template(
                'error.html',
                code=500,
                message="Merkez Bankası Rezervleri sayfası yüklenirken hata oluştu",
            ), 500

    @bp.route('/central-bank-reserves/api/data')
    @login_required
    def get_reserves_data():
        """Return JSON payload of reserves and global gold holdings with range filtering."""
        try:
            range_key = request.args.get('range', 'all').strip().lower()
            query = GetReservesOverviewQuery()
            result = query.execute(range_key=range_key)
            return jsonify({'success': True, 'data': result})
        except Exception as exc:
            logger.error("Central bank reserves API error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500

    @bp.route('/central-bank-reserves/api/export')
    @login_required
    def export_reserves_csv():
        """Export TCMB monthly reserves and global comparison to CSV."""
        try:
            export_type = request.args.get('type', 'tcmb').strip().lower()
            query = GetReservesOverviewQuery()
            payload = query.execute(range_key='all')

            output = io.StringIO()
            output.write('\ufeff')  # UTF-8 BOM for Excel compatibility

            writer = csv.writer(output, delimiter=';')

            if export_type == 'global':
                writer.writerow([
                    'Sıra', 'Ülke', 'Merkez Bankası', 'Toplam Rezerv ($ Milyar)',
                    'Altın Stoku (Ton)', 'Altın Değeri ($ Milyar)', 'Altın Oranı (%)',
                    'Döviz Rezervi ($ Milyar)', '1 Yıllık Net Değişim (Ton)', 'Notlar'
                ])
                for row in payload['global_table']:
                    writer.writerow([
                        row['rank'],
                        row['country_name'],
                        row['central_bank_name'],
                        row['total_reserves'],
                        row['gold_tonnes'],
                        row['gold_usd'],
                        row['gold_share_pct'],
                        row['fx_reserves'],
                        row['net_change_1y_tonnes'],
                        row['note'] or '',
                    ])
                filename = 'Kuresel_Merkez_Bankalari_Altin_Rezervleri.csv'
            else:
                writer.writerow([
                    'Tarih', 'Dönem', 'Toplam Brüt Rezerv ($ Milyar)', 'Brüt Döviz Rezervi ($ Milyar)',
                    'Altın Rezervi ($ Milyar)', 'Altın Stoku (Ton)', 'Net Uluslararası Rezerv ($ Milyar)',
                    'Swap Hariç Net Rezerv ($ Milyar)', 'Aylık Değişim (%)', 'Yıllık Değişim (%)', 'Altın Payı (%)'
                ])
                for row in payload['monthly_table']:
                    writer.writerow([
                        row['date'],
                        row['display_date'],
                        row['gross_total'],
                        row['gross_fx'],
                        row['gold_usd'],
                        row['gold_tonnes'],
                        row['net_reserves'],
                        row['net_ex_swap'],
                        row['mom_change'],
                        row['yoy_change'],
                        row['gold_share'],
                    ])
                filename = 'TCMB_Aylik_Rezerv_Dagilimi.csv'

            return Response(
                output.getvalue(),
                mimetype='text/csv; charset=utf-8',
                headers={'Content-Disposition': f'attachment; filename={filename}'},
            )
        except Exception as exc:
            logger.error("Central bank reserves export error: %s", exc)
            return jsonify({'success': False, 'error': str(exc)}), 500
