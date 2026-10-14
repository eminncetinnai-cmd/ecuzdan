"""Export routes."""

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import flash, make_response, redirect, render_template, request, session, url_for

from infrastructure.export.export_service import ExportService
from infrastructure.i18n import i18n
from utils.auth_helpers import capability_required
from utils.capabilities import Capability

logger = logging.getLogger(__name__)
export_service = ExportService()


# xhtml2pdf (+ pyhanko) costs ~1.4s at import time; load it on first PDF export.
# Module-level __getattr__ does NOT cover bare global lookups inside functions,
# so route code must call _pisa(). globals() is read first to honour mock.patch.
def _pisa():
    mod = globals().get('pisa')
    if mod is None:
        from xhtml2pdf import pisa as mod
        globals()['pisa'] = mod
    return mod


def __getattr__(name):
    if name == 'pisa':
        return _pisa()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def register_export_routes(bp):
    @bp.route('/export_pdf/<period>')
    def export_pdf(period):
        try:
            user_id = session.get('user_id')
            title, transactions, today = export_service.pdf_report_context(period, user_id=user_id)
            html = render_template('report_pdf.html', transactions=transactions, title=title, period=period)
            pdf = BytesIO()
            _pisa().CreatePDF(html, pdf)

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
                flash(i18n.gettext("ui_auto_95e702e3f41f"), 'warning')
                return redirect(url_for('settings.settings'))

            logger.info(f"Starting tenant export by user_id={user_id} (encrypted={encrypt})")

            json_data = export_service.export_tenant_json(user_id=user_id, encrypt=encrypt, password=password)

            data_size_kb = len(json_data) / 1024
            size_message = f"{data_size_kb:.1f} KB" if data_size_kb < 1024 else f"{data_size_kb/1024:.1f} MB"

            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"tenant_backup_{today}{'_encrypted' if encrypt else ''}.json"

            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            logger.info(f"Tenant data exported successfully by user_id={user_id} (encrypted={encrypt}, size={size_message})")
            return response
        except PermissionError as e:
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"Tenant JSON export error: {e}")
            flash(i18n.gettext("ui_auto_babee8ae30f0"), 'error')
            return redirect(url_for('settings.settings'))

    @bp.route('/export_db_json', methods=['GET', 'POST'])
    @capability_required(Capability.PLATFORM_BACKUP)
    def export_db_json():
        """Platform-scope tam yedek — yalnızca sistem_yoneticisi.

        GET  → şifresiz JSON indirme (doğrudan link için).
        POST → şifreli veya şifresiz; şifre body'de taşınır,
               URL'de asla görünmez (browser history / access log güvenliği).
        """
        try:
            user_id = session.get('user_id')

            if request.method == 'POST':
                encrypt = request.form.get('encrypt', '0') in ('1', 'true', 'yes')
                password = request.form.get('password') or None
            else:
                # GET: sadece şifresiz yedek
                encrypt = False
                password = None

            if encrypt and not password:
                if request.method == 'POST':
                    return make_response(i18n.gettext("ui_auto_95e702e3f41f"), 400)
                flash(i18n.gettext("ui_auto_95e702e3f41f"), 'warning')
                return redirect(url_for('settings.settings'))

            logger.info(
                "Starting full DB export by user_id=%s (encrypted=%s, method=%s)",
                user_id, encrypt, request.method,
            )

            json_data = export_service.export_database_json(
                user_id=user_id, encrypt=encrypt, password=password
            )

            data_size_kb = len(json_data) / 1024
            size_message = (
                f"{data_size_kb:.1f} KB" if data_size_kb < 1024
                else f"{data_size_kb / 1024:.1f} MB"
            )

            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"e_cuzdan_backup_{today}{'_encrypted' if encrypt else ''}.json"

            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            logger.info(
                "Full DB exported successfully by user_id=%s (encrypted=%s, size=%s)",
                user_id, encrypt, size_message,
            )
            return response
        except PermissionError as e:
            if request.method == 'POST':
                return make_response(str(e), 403)
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"JSON export error: {e}")
            if request.method == 'POST':
                return make_response(i18n.gettext("ui_auto_e81707f2d8fa"), 500)
            flash(i18n.gettext("ui_auto_e81707f2d8fa"), 'error')
            return redirect(url_for('settings.settings'))

    @bp.route('/import_db_json', methods=['POST'])
    @capability_required(Capability.PLATFORM_BACKUP)
    def import_db_json():
        """Platform-scope tam geri yükleme — yalnızca sistem_yoneticisi."""
        try:
            user_id = session.get('user_id')
            file = request.files.get('db_file')
            if not file or file.filename == '':
                flash(i18n.gettext("ui_auto_d604351006bf"), 'warning')
                return redirect(url_for('settings.settings'))

            # ── File size guard (50 MB) ───────────────────────────────────
            raw_bytes = file.read()
            size_mb = len(raw_bytes) / (1024 * 1024)
            if size_mb > 50:
                flash(
                    f"Yedek dosyası çok büyük ({size_mb:.1f} MB). Maksimum 50 MB desteklenmektedir.",
                    'error',
                )
                return redirect(url_for('settings.settings'))

            # ── UTF-8 / BOM-safe decode ───────────────────────────────────
            try:
                content = raw_bytes.decode('utf-8-sig')   # BOM varsa soyar
            except UnicodeDecodeError:
                content = raw_bytes.decode('utf-8', errors='replace')

            password = request.form.get('backup_password') or None
            replace_existing = request.form.get('restore_mode') == 'replace'

            # ── Pre-import otomatik snapshot ──────────────────────────────
            try:
                db_path = Path('e_cuzdan_v15.db')
                if db_path.exists():
                    snapshot_dir = Path('.work/snapshots')
                    snapshot_dir.mkdir(parents=True, exist_ok=True)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    snapshot_path = snapshot_dir / f"pre_import_{ts}.db"
                    import sqlite3
                    with sqlite3.connect(str(db_path), timeout=15.0) as src_conn, sqlite3.connect(str(snapshot_path), timeout=15.0) as dst_conn:
                        try:
                            src_conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                        except Exception:
                            pass
                        src_conn.backup(dst_conn, pages=100)
                    logger.info(
                        "Pre-import DB snapshot taken: %s (%.1f MB)",
                        snapshot_path,
                        snapshot_path.stat().st_size / (1024 * 1024),
                    )
            except Exception as snap_err:
                logger.warning("Pre-import snapshot failed (non-fatal): %s", snap_err)

            logger.info(
                "Starting full DB import by user_id=%s (replace_existing=%s, file_size=%.2f MB)",
                user_id, replace_existing, size_mb,
            )

            success, message = export_service.import_database_json(
                user_id=user_id,
                content=content,
                password=password,
                replace_existing=replace_existing,
            )

            flash(message, 'success' if success else 'error')
            if success:
                logger.info(
                    "Full DB imported by user_id=%s (replace_existing=%s)",
                    user_id, replace_existing,
                )

            return redirect(url_for('settings.settings') + '#data')
        except PermissionError as e:
            flash(str(e), 'error')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.exception(f"JSON import error: {e}")
            flash(i18n.gettext("ui_auto_ace0ba554207", **{"str(e)": str(e)}), 'error')
            return redirect(url_for('settings.settings') + '#data')
