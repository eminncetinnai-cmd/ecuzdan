"""Authentication routes."""

import logging
import os
import secrets
from datetime import datetime

from flask import current_app, flash, g, jsonify, redirect, render_template, request, session, url_for

from bootstrap.container import get_container
from infrastructure.i18n import i18n
from utils.audit import (ACTION_LOGIN, ACTION_LOGIN_FAILED, ACTION_LOGOUT,
                         ACTION_REGISTER, audit_log)
from utils.financial_insights import get_daily_insight

logger = logging.getLogger(__name__)


def _get_auth_service():
    from bootstrap.container import get_container
    return get_container().applications.auth()


def register_auth_routes(bp):
    auth_service = _get_auth_service()

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        try:
            daily_insight = get_daily_insight()
            if request.method == 'POST':
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                if not username or not password:
                    flash('Kullanıcı adı ve şifre gereklidir.', 'error')
                    return render_template('login.html', daily_insight=daily_insight)

                user = auth_service.authenticate(username, password)
                if user:
                    session.clear()
                    session.permanent = False
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['lang'] = user.language
                    session['csrf_token'] = secrets.token_hex(16)
                    session['app_boot_id'] = current_app.config.get('APP_BOOT_ID')
                    session['session_created_at'] = datetime.now().isoformat()
                    session['session_id'] = secrets.token_hex(32)
                    auth_service.record_session(user, session['session_id'])
                    audit_log(ACTION_LOGIN,
                              user_id=user.id, username=user.username,
                              tenant_id=user.tenant_id)
                    if user.password_changed_at is None:
                        flash('Güvenliğiniz için lütfen varsayılan şifrenizi değiştirin.', 'warning')
                    logger.info(f"User {username} logged in successfully")
                    return redirect(url_for('dashboard.index'))

                audit_log(ACTION_LOGIN_FAILED, username=username,
                          details={'reason': 'bad_credentials'})
                flash('Hatalı kullanıcı adı veya şifre!', 'error')
                logger.warning(f"Failed login attempt for username: {username}")

            return render_template('login.html', daily_insight=daily_insight)
        except Exception as e:
            logger.exception(f"Login error: {e}")
            flash('Giriş sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return render_template('login.html', daily_insight=get_daily_insight())

    @bp.route('/logout')
    def logout():
        try:
            username = session.get('username', 'unknown')
            user_id  = session.get('user_id')
            tenant_id = None
            if user_id:
                auth_service.clear_session(user_id)
                try:
                    from models import User
                    from shared.db import db as _db
                    u = _db.session.get(User, user_id)
                    if u:
                        tenant_id = u.tenant_id
                except Exception:
                    pass
            audit_log(ACTION_LOGOUT, user_id=user_id, username=username, tenant_id=tenant_id)
            session.clear()
            flash('Çıkış yapıldı.', 'success')
            logger.info(f"User {username} logged out")
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.exception(f"Logout error: {e}")
            session.clear()
            flash('Çıkış yapıldı.', 'success')
            return redirect(url_for('auth.login'))

    @bp.route('/set_language/<lang>', methods=['GET'])
    def set_language(lang):
        if lang in i18n.translations:
            session['lang'] = lang
            g.lang = lang
            if 'user_id' in session:
                auth_service.set_language(session['user_id'], lang)
            return jsonify({'status': 'success', 'message': i18n.gettext('language_changed_success')})
        return jsonify({'status': 'error', 'message': i18n.gettext('language_not_supported')}), 400

    @bp.route('/register', methods=['GET', 'POST'])
    def register():
        try:
            if request.method == 'POST':
                email = request.form.get('email', '').strip()
                auth_service.register_user(
                    request.form.get('full_name', '').strip(),
                    email,
                    request.form.get('password', ''),
                    request.form.get('confirm_password', ''),
                )
                logger.info(f"New user registered: {email}")
                flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
                return redirect(url_for('auth.login'))
            return render_template('register.html')
        except ValueError as e:
            auth_service.rollback()
            flash(str(e), 'error')
            return render_template('register.html')
        except Exception as e:
            logger.exception(f"Registration error: {e}")
            auth_service.rollback()
            flash('Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return render_template('register.html')

    @bp.route('/login/<provider>', methods=['GET'])
    def oauth_login(provider):
        """Initiate OAuth login flow
        
        Args:
            provider: OAuth provider name (e.g., 'google')
        """
        try:
            if provider != 'google':
                flash('Desteklenmeyen kimlik doğrulama sağlayıcısı.', 'error')
                return redirect(url_for('auth.login'))
            
            # Get Google OAuth provider from container
            from infrastructure.auth.google_provider import GoogleOAuthProvider
            
            google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
            google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            
            if not google_client_id or not google_client_secret:
                logger.error("Google OAuth credentials not configured")
                flash('Google OAuth yapılandırması eksik. Lütfen sistem yöneticisi ile iletişime geçin.', 'error')
                return redirect(url_for('auth.login'))
            
            google_provider = GoogleOAuthProvider(google_client_id, google_client_secret)
            
            # Generate CSRF state
            state = secrets.token_urlsafe(32)
            session['oauth_state'] = state
            session['oauth_provider'] = provider
            
            # Generate redirect URI
            redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
            
            # Get authorization URL
            auth_url = google_provider.get_authorization_url(redirect_uri, state)
            
            logger.info(f"Redirecting to Google OAuth: provider={provider}")
            return redirect(auth_url)
            
        except Exception as e:
            logger.exception(f"OAuth login error: {e}")
            flash('OAuth girişi başlatılırken bir hata oluştu.', 'error')
            return redirect(url_for('auth.login'))

    @bp.route('/callback/<provider>', methods=['GET'])
    def oauth_callback(provider):
        """Handle OAuth callback from provider
        
        Args:
            provider: OAuth provider name (e.g., 'google')
        """
        try:
            if provider != 'google':
                flash('Desteklenmeyen kimlik doğrulama sağlayıcısı.', 'error')
                return redirect(url_for('auth.login'))
            
            # Validate state parameter (CSRF protection)
            state = request.args.get('state')
            if not state or state != session.get('oauth_state'):
                logger.warning("OAuth state validation failed")
                flash('OAuth doğrulaması başarısız. Lütfen tekrar deneyin.', 'error')
                return redirect(url_for('auth.login'))
            
            # Get authorization code
            code = request.args.get('code')
            if not code:
                error = request.args.get('error', 'Bilinmeyen hata')
                logger.warning(f"OAuth callback error: {error}")
                flash(f'Google ile giriş başarısız: {error}', 'error')
                return redirect(url_for('auth.login'))
            
            # Get Google OAuth provider
            from infrastructure.auth.google_provider import GoogleOAuthProvider
            from application.users.oauth_application_service import OAuthApplicationService
            
            google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
            google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
            
            if not google_client_id or not google_client_secret:
                logger.error("Google OAuth credentials not configured")
                flash('Google OAuth yapılandırması eksik.', 'error')
                return redirect(url_for('auth.login'))
            
            google_provider = GoogleOAuthProvider(google_client_id, google_client_secret)
            oauth_app_service = OAuthApplicationService(google_provider)
            
            # Generate redirect URI
            redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
            
            # Verify code and login/create user
            user = oauth_app_service.verify_and_login(code, redirect_uri)
            
            # Create session
            session.clear()
            session.permanent = False
            session['user_id'] = user.id
            session['username'] = user.username
            session['lang'] = user.language
            session['csrf_token'] = secrets.token_hex(16)
            session['app_boot_id'] = current_app.config.get('APP_BOOT_ID')
            session['session_created_at'] = datetime.now().isoformat()
            session['session_id'] = secrets.token_hex(32)
            session['auth_provider'] = user.auth_provider
            
            auth_service.record_session(user, session['session_id'])
            
            # Clear OAuth state
            session.pop('oauth_state', None)
            session.pop('oauth_provider', None)
            
            logger.info(f"OAuth login successful: user_id={user.id}, provider={provider}")
            flash(f'{provider.capitalize()} ile giriş başarılı!', 'success')
            return redirect(url_for('dashboard.index'))
            
        except ValueError as e:
            logger.exception(f"OAuth verification error: {e}")
            flash(str(e), 'error')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.exception(f"OAuth callback error: {e}")
            flash('OAuth işlemi sırasında bir hata oluştu.', 'error')
            return redirect(url_for('auth.login'))

    @bp.route('/register/<token>', methods=['GET', 'POST'])
    def register_with_invite(token):
        try:
            invite = auth_service.get_valid_invite(token)
            if not invite:
                flash('Geçersiz veya süresi dolmuş davet bağlantısı.', 'error')
                return redirect(url_for('auth.login'))

            if request.method == 'POST':
                auth_service.register_invited_user(
                    invite,
                    request.form.get('full_name', '').strip(),
                    request.form.get('password', ''),
                    request.form.get('confirm_password', ''),
                )
                logger.info(f"User registered with invite: {invite.email}, tenant: {invite.tenant_id}")
                flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
                return redirect(url_for('auth.login'))

            return render_template('register_invite.html', token=token, email=invite.email)
        except ValueError as e:
            auth_service.rollback()
            invite = auth_service.get_valid_invite(token)
            if invite:
                flash(str(e), 'error')
                return render_template('register_invite.html', token=token, email=invite.email)
            flash(str(e), 'error')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.exception(f"Invite registration error: {e}")
            auth_service.rollback()
            flash('Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return redirect(url_for('auth.login'))
