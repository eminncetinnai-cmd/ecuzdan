"""
Routes Package - Modüler Route Yapısı
Blueprint pattern ile route'ların mantıksal gruplara ayrılması
"""

import logging
import secrets
from datetime import datetime

from flask import Blueprint, flash, g, render_template, request, session
from markupsafe import Markup, escape
from sqlalchemy.orm.exc import DetachedInstanceError
from werkzeug.exceptions import HTTPException

from bootstrap import get_container
from engines.financial_engine import get_live_data
from infrastructure.i18n import i18n
from utils.db_session import remove_session, rollback_session
from utils.format_utils import format_date, format_money, today_display

logger = logging.getLogger(__name__)

def _get_session_service():
    from bootstrap import get_container
    return get_container().applications.session()


# Blueprint'leri tanımla

auth_bp = Blueprint('auth', __name__, url_prefix='/')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')
transactions_bp = Blueprint('transactions', __name__, url_prefix='/')
assets_bp = Blueprint('assets', __name__, url_prefix='/')
plans_bp = Blueprint('plans', __name__, url_prefix='/')
categories_bp = Blueprint('categories', __name__, url_prefix='/')
export_bp = Blueprint('export', __name__, url_prefix='/')
settings_bp = Blueprint('settings', __name__, url_prefix='/')
strategy_bp = Blueprint('strategy', __name__, url_prefix='/')
financial_education_bp = Blueprint('financial_education', __name__, url_prefix='/')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
tenant_bp = Blueprint('tenant', __name__, url_prefix='/tenant')
logbook_bp = Blueprint('logbook', __name__, url_prefix='/logbook')
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

def register_blueprints(app):
    """
    Tüm blueprint'leri Flask uygulamasına kaydeder

    Args:
        app: Flask uygulaması
    """
    from .admin import register_admin_routes
    from .assets import register_asset_routes
    from .auth import register_auth_routes
    from .categories import register_category_routes
    from .dashboard import register_dashboard_routes
    from .export import register_export_routes
    from .financial_education import register_financial_education_routes
    from .logbook import register_logbook_routes
    from .plans import register_plan_routes
    from .profile import register_profile_routes
    from .notifications import register_notification_routes
    from .settings import register_settings_routes
    from .strategy import register_strategy_routes
    from .tenant import register_tenant_routes
    from .transactions import register_transaction_routes
    from .monitoring import register_monitoring_routes

    register_auth_routes(auth_bp)
    register_settings_routes(settings_bp)
    register_notification_routes(notifications_bp)
    register_dashboard_routes(dashboard_bp)
    register_transaction_routes(transactions_bp)
    register_asset_routes(assets_bp)
    register_plan_routes(plans_bp)
    register_category_routes(categories_bp)
    register_export_routes(export_bp)
    register_strategy_routes(strategy_bp)
    register_financial_education_routes(financial_education_bp)
    register_admin_routes(admin_bp)
    register_tenant_routes(tenant_bp)
    register_logbook_routes(logbook_bp)
    register_profile_routes(profile_bp)
    register_monitoring_routes(monitoring_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(plans_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(financial_education_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(logbook_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(notifications_bp)

# --- Template Filters ---

def register_template_filters(app):
    """
    Template filter'larını kaydeder

    Args:
        app: Flask uygulaması
    """
    @app.template_filter('format_money')
    def format_money_filter(v):
        # Tutarlar gizlilik modunun hedefleyebilmesi için işaretlenir.
        # DİKKAT: yalnızca Jinja filtresi işaretler; format_money() fonksiyonu
        # motorlarda f-string içinde kullanıldığı için düz metin döndürmeye
        # devam etmeli, aksi halde HTML rapor metinlerine sızar.
        return Markup(f'<span class="amount">{escape(format_money(v))}</span>')

    @app.template_filter('format_date')
    def format_date_filter(v):
        return format_date(v)

    @app.template_filter('asset_color')
    def asset_color_filter(index):
        """Varlık renk paleti — grafik ve badge'ler için"""
        palette = [
            '#fbbf24',  # Amber  — Altın
            '#9ca3af',  # Gray   — Gümüş
            '#ef4444',  # Red    — Petrol
            '#3b82f6',  # Blue   — BIST100
            '#f97316',  # Orange — Bitcoin
            '#10b981',  # Emerald— Nasdaq
        ]
        return palette[(int(index) - 1) % len(palette)]

# --- Context Processor ---

def register_context_processor(app):
    """
    Context processor'ı kaydeder
    Tüm template'lere global değişkenler enjekte eder

    Args:
        app: Flask uygulaması
    """
    @app.context_processor
    def inject_global_data():
        from flask import has_request_context
        dt = datetime.now()
        csrf = ''
        if has_request_context():
            try:
                if 'csrf_token' not in session:
                    session['csrf_token'] = secrets.token_hex(16)
                csrf = session.get('csrf_token', '')
            except Exception as e:
                logger.exception(f"CSRF token oluşturma hatası: {e}")
        current_user = None # Initialize current_user
        if has_request_context():
            # Cache check: Eğer user zaten g'de varsa tekrar DB'ye gitme
            if hasattr(g, 'current_user') and g.current_user is not None:
                current_user = g.current_user
            else:
                current_user = _get_session_service().get_current_user(session.get('user_id')) if 'user_id' in session else None
                g.current_user = current_user # i18n için g.current_user'ı set et

        # Tema tercihi her sayfada gerekli (layout.html <html> sınıfını belirler).
        # Tercih satırı yoksa açık tema.
        theme = 'light'
        privacy_mode = False
        if current_user is not None:
            try:
                preference = current_user.preference
                if preference is not None:
                    theme = preference.theme or theme
                    privacy_mode = bool(preference.privacy_mode)
            except DetachedInstanceError:
                # Logout gibi akışlarda User nesnesi session'dan kopmuş olabilir;
                # lazy ilişki yüklenemez. Tema kritik değil, açık temaya düşülür.
                pass

        return dict(
            live=get_live_data(),
            date_str=format_date(dt.strftime("%Y-%m-%d")),
            today_display=today_display(),
            current_day=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][dt.weekday()],
            current_time=dt.strftime("%H:%M"),
            version="v15.0 [Armor Edition]",
            brand="E-Cüzdan",
            csrf_token=lambda: csrf,
            lang=g.get("lang", i18n.default_lang),
            current_user=current_user,
            user_theme=theme,
            privacy_mode=privacy_mode,
        )

# --- CSRF Protection ---

def register_csrf_protection(app):
    """
    CSRF korumasını kaydeder
    POST, PUT, DELETE request'lerinde CSRF token doğrulaması yapar

    Args:
        app: Flask uygulaması
    """
    @app.before_request
    def csrf_protect():
        if app.config.get('TESTING'):
            return
        
        # CSRF'den muaf endpoint'ler
        csrf_exempt_paths = [
            "/login",
            "/oauth_login",
            "/oauth_callback",
            "/register",
            "/register_with_invite",
            "/healthz",
            "/notifications",
            "/notifications/read_all",
            "/api/monitoring",
            "/monitoring/api",
            "/payment_calendar"
        ]
        
        # CSRF'den muaf endpoint'leri kontrol et
        if request.path in csrf_exempt_paths:
            return
        
        # CSRF'den muaf endpoint pattern kontrolü (dinamik rotalar için)
        if request.path.startswith('/notifications/') and request.method == 'POST':
            return
        if request.path.startswith('/api/monitoring/'):
            return
        if request.path.startswith('/monitoring/api/'):
            return
        if request.path.startswith('/payment_calendar/'):
            return
            
        # Sadece state-changing request'leri kontrol et
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Token'ı form veya header'dan al
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            session_token = session.get("csrf_token")
            
            if not token:
                logger.warning(f"CSRF verification failed: token is missing from request to {request.path}")
                return render_template("error.html", code=400, message="Güvenlik uyarısı: CSRF token bulunamadı. Lütfen sayfayı yenileyip tekrar deneyin."), 400
            
            if not session_token:
                logger.warning(f"CSRF verification failed: session token missing for request to {request.path}")
                return render_template("error.html", code=400, message="Güvenlik uyarısı: Session süresi doldu. Lütfen tekrar giriş yapın."), 400
                
            if token != session_token:
                logger.warning(f"CSRF verification failed: token mismatch for request to {request.path}. Request token: {token}, Session token: {session_token}")
                return render_template("error.html", code=400, message="Güvenlik uyarısı: CSRF doğrulaması başarısız. Lütfen formu yeniden gönderip tekrar deneyin."), 400


# --- Error Handlers ---

def register_error_handlers(app):
    """
    Error handler'ları kaydeder
    HTTP hatalarını ve beklenmeyen istisnaları kaydeder, temiz rollback ve cleanup yapar.

    Args:
        app: Flask uygulaması
    """
    def _build_request_context(error):
        return {
            'method': request.method,
            'path': request.path,
            'endpoint': request.endpoint,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'tenant_id': getattr(g, 'tenant_id', None),
            'user_id': session.get('user_id'),
            'args': request.args.to_dict(flat=False),
            'form_keys': list(request.form.keys()),
            'error_type': type(error).__name__,
            'error_message': str(error)
        }

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        request_context = _build_request_context(error)
        logger.warning(
            "HTTP exception caught: %s %s %s",
            error.code,
            request.method,
            request.path,
        )
        logger.debug("HTTP exception request context: %s", request_context)

        code = error.code or 500
        if code == 404:
            message = "Aradığınız sayfa bulunamadı. Lütfen adresi kontrol edin veya ana sayfaya dönün."
        elif code == 403:
            message = "Bu sayfaya erişim yetkiniz yok. Lütfen giriş bilgilerinizi ve izinlerinizi kontrol edin."
        elif code == 400:
            message = "İsteğiniz doğru şekilde gönderilmedi. Lütfen formu kontrol ederek tekrar deneyin."
        else:
            message = error.description or "Bir hata oluştu. Lütfen sayfayı yenileyin veya tekrar deneyin."

        return render_template("error.html", code=code, message=message), code

    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        request_context = _build_request_context(error)
        logger.exception(
            "Unhandled exception during request: %s %s",
            request.method,
            request.path,
        )
        logger.debug("Unhandled exception request context: %s", request_context)

        try:
            rollback_session()
        except Exception as rollback_error:
            logger.error("Rollback failed while handling exception: %s", rollback_error)

        return render_template(
            "error.html",
            code=500,
            message="Sistem içi bir hata oluştu. İşlem geri alındı; lütfen tekrar deneyin.",
        ), 500

    @app.teardown_request
    def teardown_request(exception):
        if exception is not None:
            try:
                rollback_session()
            except Exception as rollback_error:
                logger.error("Rollback failed during teardown: %s", rollback_error)
        try:
            remove_session()
        except Exception as remove_error:
            logger.error("DB session remove failed during teardown: %s", remove_error)

# --- Session Check ---

def register_session_check(app):
    """
    Session kontrolünü kaydeder
    Her request'te session geçerliliğini kontrol eder

    Args:
        app: Flask uygulaması
    """
    @app.before_request
    def check_session():
        # Login, logout, register, OAuth, healthcheck ve Transaction Explorer sayfaları hariç
        if not request.endpoint or request.endpoint in ['auth.login', 'auth.logout', 'auth.register', 'auth.register_with_invite', 'auth.oauth_login', 'auth.oauth_callback', 'transactions.transactions_explorer', 'static', 'healthz']:
            return

        from flask import redirect, url_for

        from config import Config

        # Session kontrolü - kullanıcı giriş yapmamışsa login'e yönlendir
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        # Session timeout kontrolü
        session_timeout_hours = Config.SESSION_TIMEOUT_HOURS
        if 'session_created_at' in session:
            from datetime import datetime
            try:
                session_created_at = datetime.fromisoformat(session['session_created_at'])
            except (TypeError, ValueError) as session_error:
                logger.warning("Geçersiz session_created_at değeri temizlendi: %s", session_error)
                session.clear()
                flash('Oturum bilgisi bozulmuş. Güvenliğiniz için lütfen tekrar giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))
            session_age = datetime.now() - session_created_at
            if session_age.total_seconds() > (session_timeout_hours * 3600):
                session.clear()
                flash(f'Oturumunuz {session_timeout_hours} saat sonra otomatik olarak kapatıldı. Lütfen tekrar giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))

        # Program yeniden açıldığında eski tarayıcı session'larını geçersiz say.
        # Böylece http://127.0.0.1:5000/ doğrudan açılsa bile yeniden şifre istenir.
        if not app.config.get('TESTING') and session.get('app_boot_id') != app.config.get('APP_BOOT_ID'):
            session.clear()
            flash('Güvenliğiniz için lütfen tekrar giriş yapın.', 'warning')
            return redirect(url_for('auth.login'))

        # Session ID kontrolü
        user, session_error = _get_session_service().validate_user_session(session['user_id'], session.get('session_id'))
        if user:
            if user.last_session_id and session.get('session_id') != user.last_session_id:
                session.clear()
                flash('Bu hesap başka bir yerden giriş yapıldı. Oturumunuz kapatıldı.', 'warning')
                return redirect(url_for('auth.login'))

            # Tenant context set et
            g.tenant_id = user.tenant_id
        else:
            session.clear()
            flash('Kullanıcı kaydı bulunamadı. Lütfen tekrar giriş yapın.', 'warning')
            return redirect(url_for('auth.login'))

# --- Blueprint Registration ---

def register_security_headers(app):
    """HTTP güvenlik başlıklarını tüm yanıtlara ekler."""
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com https://cdn.datatables.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdn.datatables.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response


def register_routes(app):
    """
    Tüm blueprint'leri ve ortak bileşenleri kaydeder

    Args:
        app: Flask uygulaması
    """
    # Ortak bileşenleri kaydet
    register_security_headers(app)
    register_template_filters(app)
    register_context_processor(app)
    register_csrf_protection(app)
    register_error_handlers(app)
    register_session_check(app)

    # Blueprint'leri kaydet
    register_blueprints(app)
