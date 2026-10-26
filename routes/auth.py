"""Authentication routes."""

import logging
import secrets
from datetime import datetime

from flask import current_app, flash, g, jsonify, redirect, render_template, request, session, url_for

from infrastructure.i18n import i18n
from utils.audit import ACTION_LOGIN, ACTION_LOGIN_FAILED, ACTION_LOGOUT, audit_log
from utils.financial_insights import get_daily_insight
from utils.log_redaction import mask_email, mask_identifier, mask_provider_id

logger = logging.getLogger(__name__)


def get_container():
    from bootstrap.container import get_container as _gc
    return _gc()


def _get_auth_service():
    return get_container().applications.auth()


def register_auth_routes(bp):
    auth_service = _get_auth_service()

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        try:
            daily_insight = get_daily_insight()

            # Oturumu zaten açık olan kullanıcıyı doğrudan dashboard veya next sayfasına yönlendir
            if request.method == 'GET' and 'user_id' in session:
                user_id = session.get('user_id')
                session_id = session.get('session_id')
                user, _ = get_container().applications.session().validate_user_session(user_id, session_id)
                if user:
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                        return redirect(next_page)
                    return redirect(url_for('dashboard.index'))

            if request.method == 'POST':
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                remember_me = request.form.get('remember_me') in ('true', '1', 'on', 'yes')
                if not username or not password:
                    flash('Kullanıcı adı ve şifre gereklidir.', 'error')
                    return render_template('login.html', daily_insight=daily_insight)

                user = auth_service.authenticate(username, password)
                if user:
                    session.clear()
                    session.permanent = bool(remember_me)
                    session['remember_me'] = bool(remember_me)
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['lang'] = user.language
                    session['lang_source'] = 'user'
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
                    next_page = request.args.get('next') or request.form.get('next')
                    if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                        return redirect(next_page)
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

    @bp.route('/set_language/<lang>', methods=['POST'])
    def set_language(lang):
        if lang in i18n.translations:
            session['lang'] = lang
            session['lang_source'] = 'explicit'
            g.lang = lang
            if 'user_id' in session:
                auth_service.set_language(session['user_id'], lang)
            return jsonify({
                'status': 'success',
                'success': True,
                'language': lang,
                'message': 'Language updated successfully.',
            })
        return jsonify({
            'status': 'error',
            'success': False,
            'message': i18n.gettext('language_not_supported'),
        }), 400

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
                logger.info(f"New user registered: {mask_email(email)}")
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
            from flask import current_app

            from infrastructure.auth.google_provider import GoogleOAuthProvider

            google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            google_client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')

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
        logger.info(f"OAuth callback invoked - Provider: {provider}, Args count: {len(request.args)}")
        try:
            if provider != 'google':
                flash('Desteklenmeyen kimlik doğrulama sağlayıcısı.', 'error')
                return redirect(url_for('auth.login'))

            # Validate state parameter (CSRF protection)
            state = request.args.get('state')
            session_state = session.get('oauth_state')
            logger.info(f"OAuth state validation - Match: {bool(state and state == session_state)}")

            if not state or state != session_state:
                logger.warning("OAuth state validation failed - state mismatch or missing")
                flash('OAuth doğrulaması başarısız. Lütfen tekrar deneyin.', 'error')
                return redirect(url_for('auth.login'))

            # Clear OAuth state immediately upon validation (one-time CSRF token)
            session.pop('oauth_state', None)
            session.pop('oauth_provider', None)

            # Get authorization code
            code = request.args.get('code')
            logger.info(f"OAuth callback received - Code: {'present' if code else 'missing'}")
            if not code:
                error = request.args.get('error', 'Bilinmeyen hata')
                logger.warning(f"OAuth callback error: {error}")
                flash(f'Google ile giriş başarısız: {error}', 'error')
                return redirect(url_for('auth.login'))

            # Get Google OAuth provider
            from flask import current_app

            from infrastructure.auth.google_provider import GoogleOAuthProvider

            google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            google_client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')

            if not google_client_id or not google_client_secret:
                logger.error("Google OAuth credentials not configured")
                flash('Google OAuth yapılandırması eksik.', 'error')
                return redirect(url_for('auth.login'))

            google_provider = GoogleOAuthProvider(google_client_id, google_client_secret)

            # Generate redirect URI
            redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)

            # Exchange code for token
            token_info = google_provider.exchange_code_for_token(code, redirect_uri)
            access_token = token_info.get('access_token')

            if not access_token:
                raise ValueError("OAuth token alınamadı.")

            # Get user info from Google
            user_info = google_provider.verify_token_and_get_user_info(access_token)

            # Check if user already exists by oauth_id (most reliable for OAuth users)
            from repositories import UserRepository
            user_repo = UserRepository()
            logger.info(
                "Checking for existing user - Email: %s, Provider ID: %s",
                mask_email(user_info.email),
                mask_provider_id(user_info.provider_id),
            )
            existing_user = user_repo.find_user_by_oauth_id(
                provider=user_info.provider.upper(),
                oauth_id=user_info.provider_id,
            )

            # If not found by oauth_id, check by email (for account linking)
            if not existing_user:
                logger.info(f"User not found by oauth_id, checking by email: {mask_email(user_info.email)}")
                existing_user = user_repo.find_user_by_email(user_info.email)

            logger.info(f"User check result - Existing user: {existing_user is not None}")
            if existing_user:
                # User exists - log them in
                logger.info(f"Existing user found via OAuth: user_id={existing_user.id}")

                # Update OAuth fields if not already set
                if not existing_user.oauth_id:
                    existing_user.oauth_id = user_info.provider_id
                if not existing_user.auth_provider or existing_user.auth_provider == 'LOCAL':
                    existing_user.auth_provider = user_info.provider.upper()

                # Download and save profile picture
                if user_info.avatar_url:
                    from utils.profile_image import download_profile_image
                    profile_image_path = download_profile_image(user_info.avatar_url)
                    if profile_image_path:
                        existing_user.profile_image = profile_image_path

                existing_user.last_login_at = datetime.now()
                from shared.db import db
                db.session.commit()

                # Create session
                session.clear()
                session.permanent = True
                session['remember_me'] = True
                session['user_id'] = existing_user.id
                session['username'] = existing_user.username
                session['lang'] = existing_user.language
                session['csrf_token'] = secrets.token_hex(16)
                session['app_boot_id'] = current_app.config.get('APP_BOOT_ID')
                session['session_created_at'] = datetime.now().isoformat()
                session['session_id'] = secrets.token_hex(32)
                session['auth_provider'] = existing_user.auth_provider

                auth_service.record_session(existing_user, session['session_id'])

                # Clear OAuth state
                session.pop('oauth_state', None)
                session.pop('oauth_provider', None)

                logger.info(f"OAuth login successful: user_id={existing_user.id}, provider={provider}")
                flash(f'{provider.capitalize()} ile giriş başarılı!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                # New user - redirect to sign-up form
                logger.info(f"New user via OAuth: email={mask_email(user_info.email)}, redirecting to oauth-signup")

                # Store OAuth info in session for sign-up form
                session['oauth_signup_info'] = {
                    'email': user_info.email,
                    'name': user_info.name,
                    'provider': user_info.provider,
                    'provider_id': user_info.provider_id,
                    'avatar_url': user_info.avatar_url,
                    'access_token': access_token,
                    'created_at': datetime.now().isoformat()
                }

                # Clear OAuth state
                session.pop('oauth_state', None)
                session.pop('oauth_provider', None)

                logger.info(f"Session data stored, redirecting to: {url_for('auth.oauth_signup')}")
                redirect_url = url_for('auth.oauth_signup')
                logger.info(f"About to redirect to: {redirect_url}")
                return redirect(redirect_url)

        except ValueError as e:
            logger.exception(f"OAuth verification error: {e}")
            flash(str(e), 'error')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.exception(f"OAuth callback error: {e}")
            flash('OAuth işlemi sırasında bir hata oluştu.', 'error')
            return redirect(url_for('auth.login'))

    @bp.route('/oauth-signup', methods=['GET', 'POST'])
    def oauth_signup():
        """Handle OAuth sign-up form

        This route is shown to new users after OAuth callback
        to complete their account with username and password.
        """
        from datetime import datetime

        from repositories import UserRepository
        logger.info(f"OAuth signup route invoked - Method: {request.method}, Session keys: {list(session.keys())}")
        try:
            # Check if OAuth signup info exists in session
            oauth_info = session.get('oauth_signup_info')
            logger.info(f"OAuth signup info in session: {oauth_info is not None}")

            if not oauth_info:
                flash('OAuth oturumu sona erdi. Lütfen tekrar deneyin.', 'error')
                logger.warning("OAuth signup info not found in session, redirecting to login")
                return redirect(url_for('auth.login'))

            # Check session expiration (15 minutes max for signup session)
            if 'created_at' in oauth_info:
                try:
                    created_at = datetime.fromisoformat(oauth_info['created_at'])
                    session_age = datetime.now() - created_at
                    if session_age.total_seconds() > 900:  # 15 minutes
                        session.pop('oauth_signup_info', None)
                        flash('OAuth oturumu zaman aşımına uğradı. Lütfen tekrar deneyin.', 'error')
                        logger.warning("OAuth signup session expired, redirecting to login")
                        return redirect(url_for('auth.login'))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid signup session timestamp: {e}")
                    session.pop('oauth_signup_info', None)
                    flash('OAuth oturumu geçersiz. Lütfen tekrar deneyin.', 'error')
                    return redirect(url_for('auth.login'))

            # If user already exists by email (e.g. preexisting user account),
            # auto-link OAuth and log in directly instead of prompting for sign-up
            email = oauth_info.get('email')
            if email:
                user_repo = UserRepository()
                existing_user = user_repo.find_user_by_email(email)
                if existing_user:
                    logger.info(f"Existing user found for email {mask_email(email)} during oauth-signup. Auto-linking and logging in directly.")
                    if not existing_user.oauth_id and oauth_info.get('provider_id'):
                        existing_user.oauth_id = oauth_info.get('provider_id')
                    if not existing_user.auth_provider or existing_user.auth_provider == 'LOCAL':
                        existing_user.auth_provider = (oauth_info.get('provider') or 'GOOGLE').upper()
                    if oauth_info.get('avatar_url') and not existing_user.profile_image:
                        from utils.profile_image import download_profile_image
                        profile_image_path = download_profile_image(oauth_info['avatar_url'])
                        if profile_image_path:
                            existing_user.profile_image = profile_image_path

                    existing_user.last_login_at = datetime.now()
                    from shared.db import db
                    db.session.commit()

                    session.clear()
                    session.permanent = True
                    session['remember_me'] = True
                    session['user_id'] = existing_user.id
                    session['username'] = existing_user.username
                    session['lang'] = existing_user.language
                    session['csrf_token'] = secrets.token_hex(16)
                    session['app_boot_id'] = current_app.config.get('APP_BOOT_ID')
                    session['session_created_at'] = datetime.now().isoformat()
                    session['session_id'] = secrets.token_hex(32)
                    session['auth_provider'] = existing_user.auth_provider

                    auth_service.record_session(existing_user, session['session_id'])
                    session.pop('oauth_signup_info', None)
                    flash('Google ile giriş başarılı!', 'success')
                    return redirect(url_for('dashboard.index'))

            if request.method == 'POST':
                logger.info("[OAuthSignup] Form submission started")
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirm_password', '')
                gender = request.form.get('gender', '').strip()
                birthdate = request.form.get('birthdate', '').strip()
                country = request.form.get('country', '').strip()
                city = request.form.get('city', '').strip()
                phone = request.form.get('phone', '').strip()
                logger.info(
                    "[OAuthSignup] Form data received - Username: %s, Email: %s",
                    mask_identifier(username, 'user'),
                    mask_email(oauth_info.get('email')),
                )

                # Validate input
                if not username or not password:
                    logger.warning("[OAuthSignup] Validation failed - Missing username or password")
                    flash('Kullanıcı adı ve şifre gereklidir.', 'error')
                    return render_template('oauth_signup.html',
                        email=oauth_info['email'],
                        name=oauth_info['name'],
                        profile_picture=oauth_info.get('avatar_url'),
                        provider=oauth_info['provider'],
                        provider_id=oauth_info['provider_id'])

                if password != confirm_password:
                    logger.warning("[OAuthSignup] Validation failed - Passwords don't match")
                    flash('Şifreler eşleşmiyor.', 'error')
                    return render_template('oauth_signup.html',
                        email=oauth_info['email'],
                        name=oauth_info['name'],
                        profile_picture=oauth_info.get('avatar_url'),
                        provider=oauth_info['provider'],
                        provider_id=oauth_info['provider_id'])

                # Validate password complexity
                if len(password) < 8:
                    logger.warning("[OAuthSignup] Validation failed - Password too short")
                    flash('Şifre en az 8 karakter olmalıdır.', 'error')
                    return render_template('oauth_signup.html',
                        email=oauth_info['email'],
                        name=oauth_info['name'],
                        profile_picture=oauth_info.get('avatar_url'),
                        provider=oauth_info['provider'],
                        provider_id=oauth_info['provider_id'])

                # Validate personal information
                if not gender or not birthdate or not country or not city or not phone:
                    logger.warning("[OAuthSignup] Validation failed - Missing personal information")
                    flash('Kişisel bilgiler gereklidir.', 'error')
                    return render_template('oauth_signup.html',
                        email=oauth_info['email'],
                        name=oauth_info['name'],
                        profile_picture=oauth_info.get('avatar_url'),
                        provider=oauth_info['provider'],
                        provider_id=oauth_info['provider_id'])

                # Check if username already exists
                from repositories import UserRepository
                if UserRepository().username_exists(username):
                    logger.warning(f"[OAuthSignup] Validation failed - Username already exists: {username}")
                    flash('Bu kullanıcı adı zaten kullanımda.', 'error')
                    return render_template('oauth_signup.html',
                        email=oauth_info['email'],
                        name=oauth_info['name'],
                        profile_picture=oauth_info.get('avatar_url'),
                        provider=oauth_info['provider'],
                        provider_id=oauth_info['provider_id'])

                # Download and save profile picture
                profile_image_path = None
                if oauth_info.get('avatar_url'):
                    from utils.profile_image import download_profile_image
                    logger.info("[OAuthSignup] Downloading profile picture")
                    profile_image_path = download_profile_image(oauth_info['avatar_url'])

                # Create tenant
                import secrets
                from datetime import datetime

                from werkzeug.security import generate_password_hash

                from models import Tenant
                from shared.db import db

                logger.info("[OAuthSignup] Creating tenant")
                tenant_id = f"tenant_{oauth_info['email'].split('@')[0]}_{secrets.token_hex(8)}"
                tenant = Tenant(
                    id=tenant_id,
                    name=f"{oauth_info['name']}'s Tenant",
                    base_currency='TRY',
                    status='active'
                )
                db.session.add(tenant)
                db.session.flush()
                logger.info(f"[OAuthSignup] Tenant created: {tenant_id}")

                # Parse birthdate
                birthdate_obj = None
                if birthdate:
                    try:
                        birthdate_obj = datetime.strptime(birthdate, '%Y-%m-%d').date()
                    except ValueError:
                        flash('Geçersiz doğum tarihi formatı.', 'error')
                        return render_template('oauth_signup.html',
                            email=oauth_info['email'],
                            name=oauth_info['name'],
                            profile_picture=oauth_info.get('avatar_url'),
                            provider=oauth_info['provider'],
                            provider_id=oauth_info['provider_id'])

                # Create user
                logger.info("[OAuthSignup] Creating user")
                user_repo = UserRepository()
                user = user_repo.add_user(
                    username=username,
                    email=oauth_info['email'],
                    password=generate_password_hash(password),
                    auth_provider=oauth_info['provider'].upper(),
                    oauth_id=oauth_info['provider_id'],
                    avatar_url=oauth_info.get('avatar_url'),
                    profile_image=profile_image_path,  # Google profile picture saved as profile image
                    email_verified=True,
                    last_login_at=datetime.now(),
                    created_via='oauth',
                    role='kullanici',
                    language='tr',
                    tenant_id=tenant.id,
                    gender=gender,
                    birthdate=birthdate_obj,
                    country=country,
                    city=city,
                    phone=phone
                )
                user_repo.commit()

                logger.info(
                    f"[OAuthSignup] User created successfully - user_id={user.id}, email={mask_email(oauth_info['email'])}"
                )

                # Create session
                logger.info("[OAuthSignup] Creating user session")
                session.clear()
                session.permanent = True
                session['remember_me'] = True
                session['user_id'] = user.id
                session['username'] = user.username
                session['lang'] = user.language
                session['csrf_token'] = secrets.token_hex(16)
                session['app_boot_id'] = current_app.config.get('APP_BOOT_ID')
                session['session_created_at'] = datetime.now().isoformat()
                session['session_id'] = secrets.token_hex(32)
                session['auth_provider'] = user.auth_provider

                auth_service.record_session(user, session['session_id'])
                logger.info(f"[OAuthSignup] Session created successfully - session_id={session['session_id']}")

                # Clear OAuth signup info
                session.pop('oauth_signup_info', None)

                flash('Hesabınız başarıyla oluşturuldu!', 'success')
                logger.info(f"[OAuthSignup] Redirecting to dashboard - user_id={user.id}")
                return redirect(url_for('dashboard.index'))

            # GET request - show sign-up form
            return render_template('oauth_signup.html',
                email=oauth_info['email'],
                name=oauth_info['name'],
                profile_picture=oauth_info.get('avatar_url'),
                provider=oauth_info['provider'],
                provider_id=oauth_info['provider_id'])

        except Exception as e:
            logger.exception(f"OAuth sign-up error: {e}")
            flash('Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error')
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
                logger.info(
                    f"User registered with invite: {mask_email(invite.email)}, tenant: {invite.tenant_id}"
                )
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
