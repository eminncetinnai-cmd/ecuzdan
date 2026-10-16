"""
Admin Routes - Sistem Admin Paneli
Tenant yÃ¶netimi ve sistem yÃ¶neticisi iÅŸlemleri
"""

import logging

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from utils.auth_helpers import login_required, require_role, superadmin_required

logger = logging.getLogger(__name__)


def get_container():
    from bootstrap.container import get_container as _gc
    return _gc()


def _get_admin_service():
    return get_container().applications.admin()


def register_admin_routes(bp):
    """
    Admin route'larını blueprint'e kaydeder

    Args:
        bp: Flask Blueprint
    """

    admin_service = _get_admin_service()

    # ─── KULLANICI YÖNETİMİ ──────────────────────────────────────────

    @bp.route('/users', methods=['GET'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def list_users():
        """
        sistem_yoneticisi: tüm kullanıcıları listeler (tenant bilgisiyle birlikte)
        tenant_yoneticisi: sadece kendi tenant'ındaki kullanıcıları listeler
        """
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            users = admin_service.get_users_for_admin(current_user)
            tenants = admin_service.get_all_tenants()
            user_stats = admin_service.get_user_stats(current_user)
            return render_template(
                'admin_users.html',
                users=users,
                tenants=tenants,
                current_user=current_user,
                user_stats=user_stats
            )
        except Exception as e:
            logger.error("Users list error: %s", e)
            flash('Kullanıcı listesi yüklenirken hata oluştu.', 'error')
            return render_template('admin_users.html', users=[], tenants=[], current_user=None, user_stats=None)

    @bp.route('/api/user-stats', methods=['GET'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def api_user_stats():
        """Kullanıcı sayıları ve dağılım istatistikleri API endpoint'i."""
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            stats = admin_service.get_user_stats(current_user)
            return jsonify({'success': True, 'data': stats})
        except Exception as e:
            logger.error("API user stats error: %s", e)
            return jsonify({'success': False, 'error': str(e)}), 500


    @bp.route('/users/create', methods=['GET', 'POST'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def create_user():
        """
        Yeni kullanÄ±cÄ± oluÅŸturma
        """
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            tenants = admin_service.get_all_tenants()

            if request.method == 'POST':
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '').strip()
                role = request.form.get('role', '').strip()
                tenant_id = request.form.get('tenant_id', '').strip()

                try:
                    admin_service.create_user(
                        current_user=current_user,
                        username=username,
                        password=password,
                        role=role,
                        tenant_id=tenant_id
                    )
                    flash('KullanÄ±cÄ± baÅŸarÄ±yla oluÅŸturuldu.', 'success')
                    return redirect(url_for('admin.list_users'))
                except ValueError as e:
                    flash(str(e), 'error')
                    return render_template('admin_users.html', users=[], tenants=tenants, current_user=current_user)

            # GET request - form gÃ¶ster
            return render_template('admin_users.html', users=[], tenants=tenants, current_user=current_user)

        except Exception as e:
            logger.error("Create user error: %s", e)
            flash('KullanÄ±cÄ± oluÅŸturulurken hata oluÅŸtu.', 'error')
            return render_template('admin_users.html', users=[], tenants=[], current_user=None)

    @bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def edit_user(user_id):
        """
        KullanÄ±cÄ± dÃ¼zenleme
        """
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            target_user = admin_service.get_user_or_raise(user_id)
            tenants = admin_service.get_all_tenants()

            # Authorization check before proceeding to edit form
            if current_user.role == 'tenant_yoneticisi' and target_user.tenant_id != current_user.tenant_id:
                flash('Bu kullanÄ±cÄ±yÄ± dÃ¼zenleme yetkiniz yok.', 'error')
                return redirect(url_for('admin.list_users'))

            if request.method == 'POST':
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '').strip()
                role = request.form.get('role', '').strip()
                tenant_id = request.form.get('tenant_id', '').strip()

                try:
                    admin_service.update_user(
                        current_user=current_user,
                        user_id=user_id,
                        username=username,
                        password=password,
                        role=role,
                        tenant_id=tenant_id
                    )
                    flash('KullanÄ±cÄ± baÅŸarÄ±yla gÃ¼ncellendi.', 'success')
                    return redirect(url_for('admin.list_users'))
                except ValueError as e:
                    flash(str(e), 'error')
                    return render_template('admin_users.html', users=[target_user], tenants=tenants, current_user=current_user, edit_user=target_user)
                except PermissionError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('admin.list_users'))

            # GET request - form gÃ¶ster
            return render_template('admin_users.html', users=[], tenants=tenants, current_user=current_user, edit_user=target_user)

        except Exception as e:
            logger.error("Edit user error: %s", e)
            flash('KullanÄ±cÄ± gÃ¼ncellenirken hata oluÅŸtu.', 'error')
            return redirect(url_for('admin.list_users'))

    @bp.route('/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def delete_user(user_id):
        """
        KullanÄ±cÄ± silme
        """
        try:
            current_user = admin_service.get_current_user(session['user_id'])

            try:
                admin_service.delete_user(current_user, user_id)
                flash('KullanÄ±cÄ± baÅŸarÄ±yla silindi.', 'success')
            except (ValueError, PermissionError) as e:
                flash(str(e), 'error')
            except KeyError:
                flash('KullanÄ±cÄ± bulunamadÄ±.', 'error')

            return redirect(url_for('admin.list_users'))

        except Exception as e:
            logger.error("Delete user error: %s", e)
            flash('KullanÄ±cÄ± silinirken hata oluÅŸtu.', 'error')
            return redirect(url_for('admin.list_users'))

    # â”€â”€â”€ TENANT YÃ–NETÄ°MÄ° â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @bp.route('/tenants')
    @superadmin_required
    def tenants():
        """
        Tenant listesi
        """
        try:
            tenants_list = admin_service.get_all_tenants()
            return render_template('admin_tenants.html', tenants=tenants_list)
        except Exception as e:
            logger.error("Tenants list error: %s", e)
            flash('Tenant listesi yÃ¼klenirken hata oluÅŸtu.', 'error')
            return render_template('admin_tenants.html', tenants=[])

    @bp.route('/tenants/create', methods=['GET', 'POST'])
    @superadmin_required
    def create_tenant():
        """
        Yeni tenant oluÅŸturur
        """
        try:
            if request.method == 'POST':
                name = request.form.get('name', '').strip()
                tenant_id = request.form.get('tenant_id', '').strip()

                try:
                    admin_service.create_tenant(tenant_id, name, created_by=session.get('username'))
                    flash('Tenant baÅŸarÄ±yla oluÅŸturuldu.', 'success')
                    return redirect(url_for('admin.tenants'))
                except ValueError as e:
                    flash(str(e), 'error')
                    return render_template('admin_tenants.html', tenants=admin_service.get_all_tenants())

            # GET request - form gÃ¶ster
            return render_template('admin_tenants.html', tenants=admin_service.get_all_tenants())

        except Exception as e:
            logger.error("Create tenant error: %s", e)
            flash('Tenant oluÅŸturulurken hata oluÅŸtu.', 'error')
            return render_template('admin_tenants.html', tenants=[])

    @bp.route('/tenants/<tenant_id>/edit', methods=['POST'])
    @superadmin_required
    def edit_tenant(tenant_id):
        """
        Tenant bilgilerini gÃ¼nceller
        """
        try:
            name = request.form.get('name', '').strip()
            try:
                admin_service.edit_tenant(tenant_id, name, updated_by=session.get('username'))
                flash('Tenant baÅŸarÄ±yla gÃ¼ncellendi.', 'success')
            except ValueError as e:
                flash(str(e), 'error')
            except KeyError:
                flash('Tenant bulunamadÄ±.', 'error')

            return redirect(url_for('admin.tenants'))

        except Exception as e:
            logger.error("Edit tenant error: %s", e)
            flash('Tenant gÃ¼ncellenirken hata oluÅŸtu.', 'error')
            return redirect(url_for('admin.tenants'))

    @bp.route('/tenants/<tenant_id>/activate', methods=['POST'])
    @superadmin_required
    def activate_tenant(tenant_id):
        """
        Tenant'Ä± aktifleÅŸtirir
        """
        try:
            try:
                admin_service.update_tenant_status(tenant_id, 'active', updated_by=session.get('username'))
                flash('Tenant baÅŸarÄ±yla aktifleÅŸtirildi.', 'success')
            except KeyError:
                flash('Tenant bulunamadÄ±.', 'error')

            return redirect(url_for('admin.tenants'))

        except Exception as e:
            logger.error("Activate tenant error: %s", e)
            flash('Tenant aktifleÅŸtirilirken hata oluÅŸtu.', 'error')
            return redirect(url_for('admin.tenants'))

    @bp.route('/tenants/<tenant_id>/suspend', methods=['POST'])
    @superadmin_required
    def suspend_tenant(tenant_id):
        """
        Tenant'Ä± askÄ±ya alÄ±r
        """
        try:
            try:
                admin_service.update_tenant_status(tenant_id, 'suspended', updated_by=session.get('username'))
                flash('Tenant baÅŸarÄ±yla askÄ±ya alÄ±ndÄ±.', 'success')
            except KeyError:
                flash('Tenant bulunamadÄ±.', 'error')

            return redirect(url_for('admin.tenants'))

        except Exception as e:
            logger.error("Suspend tenant error: %s", e)
            flash('Tenant askÄ±ya alÄ±nÄ±rken hata oluÅŸtu.', 'error')
            return redirect(url_for('admin.tenants'))

    @bp.route('/tenants/<tenant_id>/delete', methods=['POST'])
    @superadmin_required
    def delete_tenant(tenant_id):
        """
        Tenant'Ä± siler (soft delete)
        """
        try:
            try:
                admin_service.update_tenant_status(tenant_id, 'deleted', updated_by=session.get('username'))
                flash('Tenant baÅŸarÄ±yla silindi.', 'success')
            except ValueError as e:
                flash(str(e), 'error')
            except KeyError:
                flash('Tenant bulunamadÄ±.', 'error')

            return redirect(url_for('admin.tenants'))

        except Exception as e:
            logger.error("Delete tenant error: %s", e)
            flash('Tenant silinirken hata oluÅŸtu.', 'error')
            return redirect(url_for('admin.tenants'))

    # â”€â”€â”€ SÄ°STEM DURUMU â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @bp.route('/', methods=['GET'])
    @bp.route('/dashboard', methods=['GET'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def admin_dashboard():
        """
        Sistem admin dashboard istatistikleri
        """
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            stats = admin_service.get_admin_dashboard_stats(current_user)
            return render_template('admin_dashboard.html', stats=stats, current_user=current_user)

        except Exception as e:
            logger.error("Admin dashboard error: %s", e)
            flash('Dashboard yÃ¼klenirken hata oluÅŸtu.', 'error')
            return redirect(url_for('dashboard.index'))

    @bp.route('/design_system', methods=['GET'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def design_system():
        """
        Tasarım sistemi ve UI bileşen kataloğu
        """
        return render_template('admin_design_system.html')

    # ─── CANLI DENETİM & DEFTER BÜTÜNLÜĞÜ ─────────────────────────

    @bp.route('/audit', methods=['GET'])
    @bp.route('/integrity', methods=['GET'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def audit_dashboard():
        """Canlı Denetim, Kriptografik Defter Bütünlüğü ve Sistem Güvenliği Paneli."""
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            is_superadmin = (getattr(current_user, 'role', '') == 'sistem_yoneticisi')
            tenant_id = None if is_superadmin else getattr(current_user, 'tenant_id', None)

            from sqlalchemy import text

            from domain.ledger.services.ledger_watchdog_service import RuntimeLedgerWatchdog
            from models import AuditLog, db

            watchdog = RuntimeLedgerWatchdog()
            if is_superadmin or not tenant_id:
                audit_result = watchdog.audit_all_tenants()
            else:
                audit_result = watchdog.audit_tenant(tenant_id)

            pragma_integrity = "ok"
            pragma_journal = "wal"
            try:
                res = db.session.execute(text("PRAGMA integrity_check")).scalar()
                pragma_integrity = str(res) if res else "unknown"
                j_mode = db.session.execute(text("PRAGMA journal_mode")).scalar()
                pragma_journal = str(j_mode) if j_mode else "unknown"
            except Exception as pe:
                logger.warning("PRAGMA check warning: %s", pe)

            query = AuditLog.query
            if not is_superadmin and tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            recent_logs = query.order_by(AuditLog.id.desc()).limit(20).all()

            context = {
                'current_user': current_user,
                'is_superadmin': is_superadmin,
                'audit_result': audit_result,
                'pragma_integrity': pragma_integrity,
                'pragma_journal': pragma_journal,
                'recent_logs': recent_logs,
            }
            return render_template('admin_audit.html', **context)
        except Exception as e:
            logger.error("Audit dashboard error: %s", e)
            flash(f'Denetim paneli yüklenirken hata oluştu: {str(e)}', 'error')
            return redirect(url_for('admin.admin_dashboard'))

    @bp.route('/audit/run-watchdog', methods=['POST'])
    @login_required
    @require_role('sistem_yoneticisi', 'tenant_yoneticisi')
    def run_watchdog_scan():
        """Tetiklenen anlık derin defter ve kriptografik zincir denetimi."""
        try:
            current_user = admin_service.get_current_user(session['user_id'])
            is_superadmin = (getattr(current_user, 'role', '') == 'sistem_yoneticisi')
            tenant_id = None if is_superadmin else getattr(current_user, 'tenant_id', None)

            from domain.ledger.services.ledger_watchdog_service import RuntimeLedgerWatchdog
            watchdog = RuntimeLedgerWatchdog()
            report = watchdog.audit_all_tenants() if (is_superadmin or not tenant_id) else watchdog.audit_tenant(tenant_id)

            from utils.audit import audit_log
            audit_log(
                "LEDGER_AUDIT_ON_DEMAND",
                user_id=session.get('user_id'),
                username=getattr(current_user, 'username', 'admin'),
                tenant_id=getattr(current_user, 'tenant_id', None),
                details={
                    'healthy': report.healthy,
                    'error_count': report.error_count,
                    'total_journal_entries': report.total_journal_entries,
                    'total_ledger_lines': report.total_ledger_lines,
                    'total_paid_transactions': report.total_paid_transactions,
                }
            )
            from models import db
            db.session.commit()

            if report.healthy:
                flash(f"Bütünlük Taraması Başarılı: {report.total_journal_entries} yevmiye kaydı, {report.total_ledger_lines} defter satırı ve kriptografik zincir doğrulandı. 0 hata.", 'success')
            else:
                flash(f"Bütünlük Uyarısı: {report.error_count} adet uyumsuzluk tespit edildi!", 'error')
        except Exception as e:
            logger.error("Run watchdog scan error: %s", e)
            flash(f"Tarama sırasında hata oluştu: {str(e)}", 'error')

        return redirect(url_for('admin.audit_dashboard'))


