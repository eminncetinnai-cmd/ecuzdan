"""Tenant administration routes."""

import logging

from flask import redirect, render_template, request, session, url_for

from bootstrap.container import get_container
from utils.auth_helpers import tenant_admin_required
from utils.notification_helpers import flash_error, flash_info, flash_success, flash_warning

logger = logging.getLogger(__name__)


def _get_tenant_service():
    from bootstrap.container import get_container
    return get_container().applications.tenant()


def register_tenant_routes(bp):
    tenant_service = _get_tenant_service()

    @bp.route('/users')
    @tenant_admin_required
    def users():
        try:
            return render_template('tenant_users.html', **tenant_service.users_context(session['user_id']))
        except Exception as e:
            logger.exception(f"Tenant users list error: {e}")
            flash_error('Kullanıcı listesi yüklenirken hata oluştu.')
            return render_template('tenant_users.html', users=[], current_user=None)

    @bp.route('/users/<user_id>/toggle_status', methods=['POST'])
    @tenant_admin_required
    def toggle_user_status(user_id):
        try:
            tenant_service.validate_target_user(session['user_id'], user_id)
            flash_info('Kullanıcı durumu değiştirildi (demo).')
        except (PermissionError, ValueError) as e:
            flash_error(str(e))
        except Exception as e:
            logger.exception(f"Toggle user status error: {e}")
            flash_error('Kullanıcı durumu değiştirilirken hata oluştu.')
        return redirect(url_for('tenant.users'))

    @bp.route('/users/<user_id>/change_role', methods=['POST'])
    @tenant_admin_required
    def change_user_role(user_id):
        try:
            tenant_service.change_user_role(
                session['user_id'],
                user_id,
                request.form.get('role', 'kullanici'),
            )
            logger.info(f"User role changed: {user_id} by {session.get('username')}")
            flash_success('Kullanıcı rolü başarıyla değiştirildi.')
        except (PermissionError, ValueError) as e:
            tenant_service.rollback()
            flash_error(str(e))
        except Exception as e:
            logger.exception(f"Change user role error: {e}")
            tenant_service.rollback()
            flash_error('Kullanıcı rolü değiştirilirken hata oluştu.')
        return redirect(url_for('tenant.users'))

    @bp.route('/invite', methods=['GET', 'POST'])
    @tenant_admin_required
    def invite():
        try:
            if request.method == 'POST':
                invite_obj = tenant_service.create_invite(
                    session['user_id'],
                    request.form.get('email', '').strip(),
                    request.form.get('role', 'kullanici'),
                )
                invite_link = url_for('auth.register_with_invite', token=invite_obj.token, _external=True)
                logger.info(f"Invite created: {invite_obj.email} by {session.get('username')}")
                flash_success(f'Davet oluşturuldu! Davet linki: {invite_link}')
                return render_template('invite_user.html', invite_link=invite_link)
            return render_template('invite_user.html')
        except LookupError as e:
            flash_warning(str(e))
            return render_template('invite_user.html')
        except ValueError as e:
            flash_error(str(e))
            return render_template('invite_user.html')
        except Exception as e:
            logger.exception(f"Invite error: {e}")
            tenant_service.rollback()
            flash_error('Davet oluşturulurken hata oluştu.')
            return render_template('invite_user.html')

    @bp.route('/users/<int:user_id>/remove', methods=['POST'])
    @tenant_admin_required
    def remove_user(user_id):
        """Tenant admin kendi kiracısındaki bir kullanıcıyı siler (CSRF korumalı)."""
        try:
            _, target = tenant_service.remove_user(session['user_id'], user_id)
            logger.info(f"User removed: {target.username} (id={user_id}) by {session.get('username')}")
            flash_success(f'Kullanıcı "{target.username}" başarıyla silindi.')
        except (PermissionError, ValueError) as e:
            tenant_service.rollback()
            flash_error(str(e))
        except Exception as e:
            logger.exception(f"Remove user error: {e}")
            tenant_service.rollback()
            flash_error('Kullanıcı silinirken hata oluştu.')
        return redirect(url_for('tenant.users'))

    @bp.route('/invites')
    @tenant_admin_required
    def invites():
        try:
            return render_template('invite_list.html', invites=tenant_service.list_invites(session['user_id']))
        except Exception as e:
            logger.exception(f"Invites list error: {e}")
            flash_error('Davet listesi yüklenirken hata oluştu.')
            return render_template('invite_list.html', invites=[])
