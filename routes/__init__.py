"""
Routes Package - Modüler Route Yapısı
Blueprint pattern ile route'ların mantıksal gruplara ayrılması
"""

import logging
import math
import os
import secrets
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, current_app, flash, g, jsonify, make_response, render_template, request, session, url_for
from markupsafe import Markup, escape
from sqlalchemy.orm.exc import DetachedInstanceError
from werkzeug.exceptions import HTTPException

from bootstrap import get_container
from engines.financial_engine import get_live_data
from infrastructure.i18n import i18n
from shared.currency_precision import get_currency_symbol
from utils.db_session import remove_session, rollback_session
from utils.format_utils import format_date, format_money, today_display

logger = logging.getLogger(__name__)

_WEEKDAYS = ("Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar")

def _get_session_service():
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
analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')
central_bank_reserves_bp = Blueprint('central_bank_reserves', __name__, url_prefix='/')
global_ratios_bp = Blueprint('global_ratios', __name__, url_prefix='/')
gold_tracking_bp = Blueprint('gold_tracking', __name__, url_prefix='/')
from .storage_health import storage_health_bp


def register_blueprints(app):
    """
    Tüm blueprint'leri Flask uygulamasına kaydeder

    Args:
        app: Flask uygulaması
    """
    from .admin import register_admin_routes
    from .analysis import register_analysis_routes
    from .assets import register_asset_routes
    from .auth import register_auth_routes
    from .categories import register_category_routes
    from .central_bank_reserves import register_central_bank_reserves_routes
    from .dashboard import register_dashboard_routes
    from .export import register_export_routes
    from .financial_education import register_financial_education_routes
    from .global_ratios import register_global_ratios_routes
    from .gold_tracking import register_gold_tracking_routes
    from .logbook import register_logbook_routes
    from .monitoring import register_monitoring_routes
    from .notifications import register_notification_routes
    from .plans import register_plan_routes
    from .profile import register_profile_routes
    from .settings import register_settings_routes
    from .storage_health import register_storage_health_routes
    from .strategy import register_strategy_routes
    from .tenant import register_tenant_routes
    from .transactions import register_transaction_routes

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
    register_analysis_routes(analysis_bp)
    register_central_bank_reserves_routes(central_bank_reserves_bp)
    register_global_ratios_routes(global_ratios_bp)
    register_gold_tracking_routes(gold_tracking_bp)
    register_storage_health_routes(storage_health_bp)

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
    app.register_blueprint(analysis_bp)
    app.register_blueprint(central_bank_reserves_bp)
    app.register_blueprint(global_ratios_bp)
    app.register_blueprint(gold_tracking_bp)
    app.register_blueprint(storage_health_bp)

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

    @app.template_filter('format_ticker_price')
    def format_ticker_price_filter(v):
        """Piyasa ve canlı ticker fiyatlarını 2 ondalık basamak ve Türkçe binlik ayracı ile formatlar."""
        if v is None or v == '' or v == '--':
            return '--'
        try:
            if isinstance(v, (int, float, Decimal)):
                val_float = float(v)
            else:
                s = str(v).strip()
                if not s or s.lower() in {'nan', 'nat', 'none', '--'}:
                    return '--'
                has_dot = '.' in s
                has_comma = ',' in s
                if has_dot and has_comma:
                    if s.rfind(',') > s.rfind('.'):
                        # Turkish: 1.234,56
                        s = s.replace('.', '').replace(',', '.')
                    else:
                        # US: 1,234.56
                        s = s.replace(',', '')
                elif has_comma:
                    s = s.replace(',', '.')
                val_float = float(s)

            if not math.isfinite(val_float):
                return '--'

            parts = f"{val_float:,.2f}".split('.')
            int_part = parts[0].replace(',', '.')
            dec_part = parts[1]
            return f"{int_part},{dec_part}"
        except Exception:
            return str(v)

    @app.template_filter('currency_symbol')
    def currency_symbol_filter(v):
        """Para birimi kodundan simge üretir (örn. USD -> $, TRY -> ₺)"""
        if not v:
            return ''
        return get_currency_symbol(str(v)) or str(v)

# --- Context Processor ---

_STATIC_MTIME_CACHE: dict[str, tuple[float, int | None]] = {}
_STATIC_MTIME_TTL = 10.0  # saniye


def _get_versioned_static_url(filename: str) -> str:
    import time
    boot_id = (current_app.config.get("APP_BOOT_ID") or "v15")[:8]
    try:
        now = time.monotonic()
        cached = _STATIC_MTIME_CACHE.get(filename)
        if cached is not None and (now - cached[0]) < _STATIC_MTIME_TTL:
            mtime = cached[1]
        else:
            static_folder = current_app.static_folder or os.path.join(current_app.root_path, "static")
            filepath = os.path.join(static_folder, filename)
            mtime = int(os.path.getmtime(filepath)) if os.path.isfile(filepath) else None
            _STATIC_MTIME_CACHE[filename] = (now, mtime)
        if mtime is not None:
            return url_for("static", filename=filename, v=f"{boot_id}_{mtime}")
    except Exception:
        pass
    return url_for("static", filename=filename, v=boot_id)


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
            # Cache check: Eğer user zaten g'de varsa ve aktif session'a bağlıysa tekrar DB'ye gitme
            from utils.auth_helpers import _is_bound_user
            cached_user = getattr(g, 'current_user', None)
            if _is_bound_user(cached_user):
                current_user = cached_user
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
        base_currency_code = 'TRY'
        base_currency_symbol = '₺'
        if current_user is not None:
            try:
                base_currency_code = getattr(current_user, 'base_currency', None) or 'TRY'
                base_currency_symbol = get_currency_symbol(base_currency_code) or '₺'
            except Exception:
                pass

        from database.schema_version import SCHEMA_VERSION
        return dict(
            live=get_live_data(),
            date_str=format_date(dt.strftime("%Y-%m-%d")),
            today_display=today_display(),
            current_day=_WEEKDAYS[dt.weekday()],
            current_time=dt.strftime("%H:%M"),
            version=f"{SCHEMA_VERSION} [Armor Edition]",
            brand="E-Cüzdan",
            csrf_token=lambda: csrf,
            lang=g.get("lang", i18n.default_lang),
            current_user=current_user,
            user_theme=theme,
            privacy_mode=privacy_mode,
            static_asset_url=_get_versioned_static_url,
            base_currency_code=base_currency_code,
            base_currency_symbol=base_currency_symbol,
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
            "/api/keepalive",
            "/manifest.json",
            "/sw.js",
            "/apple-touch-icon.png",
            "/apple-touch-icon-precomposed.png",
            "/offline",
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
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
            session_token = session.get("csrf_token")

            if not token:
                logger.warning(f"CSRF verification failed: token is missing from request to {request.path}")
                return render_template("error.html", code=400, message="Güvenlik uyarısı: CSRF token bulunamadı. Lütfen sayfayı yenileyip tekrar deneyin."), 400

            if not session_token:
                logger.warning(f"CSRF verification failed: session token missing for request to {request.path}")
                return render_template("error.html", code=400, message="Güvenlik uyarısı: Session süresi doldu. Lütfen tekrar giriş yapın."), 400

            if token != session_token:
                logger.warning(
                    "CSRF verification failed: token mismatch for request to %s",
                    request.path,
                )
                return render_template("error.html", code=400, message="Güvenlik uyarısı: CSRF doğrulaması başarısız. Lütfen formu yeniden gönderip tekrar deneyin."), 400


def _should_return_json() -> bool:
    from utils.ajax_helpers import is_ajax_request
    if request.path.startswith('/api/') or '/api/' in request.path:
        return True
    if is_ajax_request():
        return True
    if request.is_json:
        return True
    accept = request.headers.get('Accept', '')
    if 'application/json' in accept and 'text/html' not in accept:
        return True
    return False


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
        code = error.code or 500
        if code in (404, 405):
            logger.info(
                "HTTP exception caught: %s %s %s",
                error.code,
                request.method,
                request.path,
            )
        else:
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

        if _should_return_json():
            resp = make_response(jsonify({
                'success': False,
                'error': message,
                'code': code,
                'error_code': f'http_{code}',
            }), code)
            if code == 429 and 'Retry-After' not in resp.headers:
                resp.headers['Retry-After'] = '60'
            return resp

        resp = make_response(render_template("error.html", code=code, message=message), code)
        if code == 429 and 'Retry-After' not in resp.headers:
            resp.headers['Retry-After'] = '60'
        return resp

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

        if _should_return_json():
            return jsonify({
                'success': False,
                'error': "Sistem içi bir hata oluştu. İşlem geri alındı; lütfen tekrar deneyin.",
                'code': 500,
                'error_code': 'internal_server_error',
            }), 500

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
        # Login, logout, register, OAuth, healthcheck ve genel live stream endpoint'leri hariç
        if not request.endpoint or request.endpoint in ['auth.login', 'auth.logout', 'auth.register', 'auth.register_with_invite', 'auth.oauth_login', 'auth.oauth_callback', 'auth.oauth_signup', 'dashboard.live_quotes', 'dashboard.live_stream', 'static', 'healthz', 'favicon', 'manifest', 'service_worker', 'apple_touch_icon', 'offline_page', 'keepalive', 'plans.calendar_feed']:
            return

        from flask import redirect, url_for

        from config import Config

        # Session kontrolü - kullanıcı giriş yapmamışsa login'e yönlendir (API için 401 JSON)
        if 'user_id' not in session:
            if _should_return_json():
                return jsonify({
                    'success': False,
                    'error_code': 'authentication_required',
                    'message': 'Oturum gerekli.',
                }), 401
            return redirect(url_for('auth.login'))

        # Session timeout kontrolü
        is_remembered = bool(session.get('remember_me', False))
        if is_remembered:
            session.permanent = True

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
            timeout_seconds = (getattr(Config, 'REMEMBER_COOKIE_DAYS', 60) * 86400) if is_remembered else (Config.SESSION_TIMEOUT_HOURS * 3600)
            if session_age.total_seconds() > timeout_seconds:
                session.clear()
                if _should_return_json():
                    return jsonify({
                        'success': False,
                        'error_code': 'session_expired',
                        'message': 'Oturumunuz zaman aşımına uğradı.',
                    }), 401
                flash('Oturumunuz zaman aşımına uğradı. Lütfen tekrar giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))
            elif is_remembered and session_age.total_seconds() > 86400:
                # Aktif kullanılan "Beni Hatırla" oturumu: periyodik kayan pencere ile tazele
                session['session_created_at'] = datetime.now().isoformat()

        # Program yeniden açıldığında eski geçici tarayıcı session'larını geçersiz say.
        # "Beni Hatırla" seçilmiş oturumlar için boot ID kontrolü atlanır.
        if not app.config.get('TESTING') and not is_remembered and session.get('app_boot_id') != app.config.get('APP_BOOT_ID'):
            session.clear()
            if _should_return_json():
                return jsonify({
                    'success': False,
                    'error_code': 'session_invalid',
                    'message': 'Güvenliğiniz için lütfen tekrar giriş yapın.',
                }), 401
            flash('Güvenliğiniz için lütfen tekrar giriş yapın.', 'warning')
            return redirect(url_for('auth.login'))

        # Session ID kontrolü
        user, session_error = _get_session_service().validate_user_session(session['user_id'], session.get('session_id'))
        if user:
            # Şifre değiştirilmişse eski tarihli oturumları sonlandır
            if user.password_changed_at and 'session_created_at' in session:
                try:
                    session_created_at_val = datetime.fromisoformat(session['session_created_at'])
                    if session_created_at_val < user.password_changed_at:
                        session.clear()
                        flash('Şifreniz değiştirildiği için lütfen tekrar giriş yapın.', 'info')
                        return redirect(url_for('auth.login'))
                except Exception:
                    pass

            if user.last_session_id and session.get('session_id') != user.last_session_id:
                session.clear()
                if _should_return_json():
                    return jsonify({
                        'success': False,
                        'error_code': 'authentication_required',
                        'message': 'Bu hesap başka bir yerden giriş yapıldı. Oturum gerekli.',
                    }), 401
                flash('Bu hesap başka bir yerden giriş yapıldı. Oturumunuz kapatıldı.', 'warning')
                return redirect(url_for('auth.login'))

            # Tenant ve current_user context set et
            g.current_user = user
            g.tenant_id = user.tenant_id
        else:
            session.clear()
            if _should_return_json():
                return jsonify({
                    'success': False,
                    'error_code': 'authentication_required',
                    'message': 'Kullanıcı kaydı bulunamadı. Oturum gerekli.',
                }), 401
            flash('Kullanıcı kaydı bulunamadı. Lütfen tekrar giriş yapın.', 'warning')
            return redirect(url_for('auth.login'))

# --- Blueprint Registration ---

def register_security_headers(app):
    """HTTP güvenlik başlıklarını, statik önbelleklemeyi ve yanıt sıkıştırmayı kaydeder."""
    import gzip

    @app.after_request
    def set_security_and_performance_headers(response):
        # Güvenlik Başlıkları
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com https://cdn.datatables.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdn.datatables.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )

        # Statik Varlık Önbellekleme (Cache-busted varlıklar için 1 yıl immutable cache, diğerleri için 7 gün)
        if request.path.startswith('/static/'):
            if not app.config.get('TESTING'):
                if 'v' in request.args:
                    response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                else:
                    response.headers.setdefault('Cache-Control', 'public, max-age=604800')

        # GZIP Yanıt Sıkıştırma (HTML, JSON, JS, CSS, SVG yanıtlarında %85-%95 bant genişliği tasarrufu)
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if (
            'gzip' in accept_encoding
            and 200 <= response.status_code < 300
            and not response.direct_passthrough
            and not getattr(response, 'is_streamed', False)
            and 'Content-Encoding' not in response.headers
            and any(t in (response.content_type or '') for t in ('text/', 'application/json', 'application/javascript', 'image/svg+xml', 'application/xml'))
        ):
            try:
                data = response.get_data()
                if len(data) > 500:
                    compressed = gzip.compress(data, compresslevel=2)
                    response.set_data(compressed)
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Content-Length'] = len(compressed)
                    response.headers['Vary'] = 'Accept-Encoding'
            except Exception as compress_err:
                logger.debug("GZIP compression skipped: %s", compress_err)

        return response


def register_routes(app):
    """
    Tüm blueprint'leri ve ortak bileşenleri kaydeder

    Args:
        app: Flask uygulaması
    """
    from utils.request_context import register_request_context

    register_request_context(app)

    # Ortak bileşenleri kaydet
    register_security_headers(app)
    register_template_filters(app)
    register_context_processor(app)
    register_csrf_protection(app)
    register_error_handlers(app)
    register_session_check(app)

    # Blueprint'leri kaydet
    register_blueprints(app)
