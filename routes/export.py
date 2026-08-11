"""Export routes."""

import logging
from datetime import datetime
from io import BytesIO

from flask import flash, make_response, redirect, render_template, request, session, url_for
from xhtml2pdf import pisa

from infrastructure.export.export_service import ExportService

logger = logging.getLogger(__name__)
export_service = ExportService()


def register_export_routes(bp):
    @bp.route('/export_pdf/<period>')
    def export_pdf(period):
        try:
            user_id = session.get('user_id')
            title, transactions, today = export_service.pdf_report_context(period, user_id=user_id)
            html = render_template('report_pdf.html', transactions=transactions, title=title, period=period)
            pdf = BytesIO()
            pisa.CreatePDF(html, pdf)

            response = make_response(pdf.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=rapor_{period}_{today}.pdf'
            logger.info(f"PDF report exported for period: {period}")
            return response
        except PermissionError as e:
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"PDF export error: {e}")
            return render_template('error.html', code=500, message="PDF oluşturulurken hata oluştu"), 500

    @bp.route('/export_tenant_json')
    def export_tenant_json():
        """Tenant-scope yedek — her admin kendi tenant'ını yedekler."""
        try:
            user_id = session.get('user_id')
            encrypt = request.args.get('encrypt', 'false').lower() == 'true'
            password = request.args.get('password', None)

            if encrypt and not password:
                flash('Şifreleme için şifre gerekli.', 'warning')
                return redirect(url_for('settings.settings'))

            json_data = export_service.export_tenant_json(user_id=user_id, encrypt=encrypt, password=password)
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"tenant_backup_{today}{'_encrypted' if encrypt else ''}.json"

            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            logger.info(f"Tenant data exported by user_id={user_id}")
            return response
        except PermissionError as e:
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"Tenant JSON export error: {e}")
            flash('Veri dışa aktarılırken hata oluştu.', 'error')
            return redirect(url_for('settings.settings'))

    @bp.route('/export_db_json')
    def export_db_json():
        """Platform-scope tam yedek — yalnızca sistem_yoneticisi."""
        try:
            user_id = session.get('user_id')
            encrypt = request.args.get('encrypt', 'false').lower() == 'true'
            password = request.args.get('password', None)

            if encrypt and not password:
                flash('Şifreleme için şifre gerekli.', 'warning')
                return redirect(url_for('settings.settings'))

            # user_id artık require_platform_owner içinde doğrulanıyor
            json_data = export_service.export_database_json(user_id=user_id, encrypt=encrypt, password=password)
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"e_cuzdan_backup_{today}{'_encrypted' if encrypt else ''}.json"

            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            logger.info(f"Full DB exported by user_id={user_id} (encrypted={encrypt})")
            return response
        except PermissionError as e:
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"JSON export error: {e}")
            flash('Veritabanı dışa aktarılırken bir hata oluştu.', 'error')
            return redirect(url_for('settings.settings'))

    @bp.route('/import_db_json', methods=['POST'])
    def import_db_json():
        """Platform-scope tam geri yükleme — yalnızca sistem_yoneticisi."""
        try:
            user_id = session.get('user_id')
            file = request.files.get('db_file')
            if not file or file.filename == '':
                flash('Lütfen geçerli bir JSON dosyası seçin.', 'warning')
                return redirect(url_for('settings.settings'))

            password = request.form.get('backup_password', None)

            # user_id require_platform_owner içinde doğrulanıyor
            success, message = export_service.import_database_json(
                user_id=user_id,
                content=file.read().decode('utf-8'),
                password=password,
            )
            flash(message, 'success' if success else 'error')
            if success:
                logger.info(f"Full DB imported by user_id={user_id}")
            return redirect(url_for('settings.settings'))
        except PermissionError as e:
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"JSON import error: {e}")
            flash(f'İçe aktarma sırasında beklenmedik hata: {str(e)}', 'error')
            return redirect(url_for('settings.settings'))
