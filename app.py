"""
E-Cüzdan v15 - Modüler Mimari
Ana Flask uygulaması - Konfigürasyon ve başlatma
"""
import logging
import os
import secrets
import sys
from datetime import timedelta

from flask import Flask, jsonify, send_from_directory

from config import Config
from database import init_database
from infrastructure.i18n import i18n
from models import db
from routes import register_routes
from utils.auth_helpers import set_tenant_context

# Centralized logging configuration
from utils.logging_config import get_logger, setup_logging

_log_level_name = os.getenv('LOG_LEVEL', Config.LOG_LEVEL).upper()
_log_level = getattr(logging, _log_level_name, None)
if not isinstance(_log_level, int):
    _log_level = logging.INFO
setup_logging(level=_log_level)

# OpenTelemetry Setup (opt-in: OTEL_ENABLED=true)
from utils.otel_setup import instrument_flask_app, setup_tracing

setup_tracing(service_name="e_cuzdan")

logger = get_logger(__name__)

# Flask uygulamasını başlat
app = Flask(__name__)
app.url_map.strict_slashes = False
app.config.setdefault('DB_BOOTSTRAP_READY', False)
app.config.setdefault('DB_BOOTSTRAP_ERROR', None)

# Instrument Flask with OpenTelemetry (opt-in)
instrument_flask_app(app)

config = Config.from_env()
app.config['TESTING'] = os.getenv('FLASK_ENV', '').lower() == 'testing' or os.getenv('TESTING', 'false').lower() == 'true'

# Apply configuration
# Production'da SECRET_KEY mutlaka .env ile set edilmeli.
# Geliştirmede (dev) her restart'ta aynı kalması için sabit fallback kullan.
if config.SECRET_KEY and config.SECRET_KEY != 'dev-secret-key-change-in-production':
    app.secret_key = config.SECRET_KEY
else:
    # Geliştirme ortamı: sabit bir değer kullan ki her restart'ta session'lar geçersiz olmasın.
    # Üretimde .env dosyasına SECRET_KEY eklenmeli.
    logger.warning(
        "SECRET_KEY ayarlanmamış veya varsayılan değerde. "
        "Üretimde .env içinde güçlü bir SECRET_KEY tanımlanmalıdır."
    )
    app.secret_key = 'dev-only-fixed-fallback-key-do-not-use-in-production'
import hashlib
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
if config.APP_BOOT_ID:
    app.config['APP_BOOT_ID'] = config.APP_BOOT_ID
elif os.getenv('RENDER') == 'true' or config.FLASK_ENV == 'production':
    app.config['APP_BOOT_ID'] = secrets.token_hex(16)
else:
    app.config['APP_BOOT_ID'] = secrets.token_hex(32)
app.config['GOOGLE_CLIENT_ID'] = config.GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = config.GOOGLE_CLIENT_SECRET
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.config['BACKGROUND_SERVICE_ENABLED'] = config.BACKGROUND_SERVICE_ENABLED
app.config['BACKGROUND_WORKER_OWNER'] = config.BACKGROUND_WORKER_OWNER

if config.BACKGROUND_SERVICE_ENABLED:
    try:
        from infrastructure.background.background_service import get_background_service
        get_background_service(flask_app=app)
    except Exception as bg_err:
        logger.warning("BackgroundService başlatılamadı: %s", bg_err)

# Jinja2 globals, filters ve whitespace optimizasyonu
from shared.currency_precision import get_currency_symbol

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.globals.update(min=min, max=max)
app.jinja_env.filters['currency_symbol'] = lambda v: get_currency_symbol(str(v)) or str(v) if v else ''

@app.context_processor
def inject_global_categories():
    try:
        from flask import g

        from repositories.catalog_repository import CatalogRepository
        from utils.ref_cache import get_cached

        tenant_id = g.get('tenant_id')
        cache_key = f"global_categories:{tenant_id or 'default'}"

        def _fetch_categories():
            repo = CatalogRepository()
            cats = repo.list_visible_categories(tenant_id)
            return {
                'global_income_cats': [c.name for c in cats if c.type == 'Gelir'],
                'global_expense_cats': [c.name for c in cats if c.type == 'Gider'],
                'global_investment_cats': [c.name for c in cats if c.type == 'Yatırım']
            }

        return get_cached(cache_key, _fetch_categories, ttl=120)
    except Exception:
        return {'global_income_cats': [], 'global_expense_cats': [], 'global_investment_cats': []}

@app.context_processor
def inject_csrf_token():
    """csrf_token() Jinja helper - layout.html modalinda kullanilir."""
    from flask import session
    def csrf_token():
        return session.get('csrf_token', '')
    return {'csrf_token': csrf_token}

# Session ve Cookie Güvenlik Ayarları
app.permanent_session_lifetime = timedelta(hours=config.SESSION_TIMEOUT_HOURS)
app.config.update(
    SESSION_COOKIE_HTTPONLY=config.SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE=config.SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE=config.SESSION_COOKIE_SECURE,
    SESSION_REFRESH_EACH_REQUEST=config.SESSION_REFRESH_EACH_REQUEST,
)

# ── Rate Limiting ─────────────────────────────────────────────────────────
# Flask-Limiter: Çeşitli endpoint'ler için rate limiting koruması.
# Login, register, ve diğer kritik endpoint'ler özel limitlere tabidir.
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        # Global varsayılan: yüksek ama sınırsız değil
        default_limits=["1000 per day", "200 per hour"],
        storage_uri="memory://" if (config.FLASK_ENV in ('development', 'testing') or getattr(config, 'RATELIMIT_IN_MEMORY_FALLBACK_ENABLED', False)) else (config.RATELIMIT_STORAGE_URI or "memory://"),
        strategy="fixed-window",
    )
    app.config['RATELIMIT_ENABLED'] = not app.config.get('TESTING', False)
    # extensions dict'e koy — auth.py before_request hook'u buradan erişir
    app.extensions['limiter'] = limiter
    logger.debug("Flask-Limiter aktif (memory storage). Testing=%s", app.config['TESTING'])
    _limiter_instance = limiter
except ImportError:
    logger.warning("flask-limiter yüklü değil; rate limiting devre dışı.")
    app.config['RATELIMIT_ENABLED'] = False
    _limiter_instance = None

# Veritabanını ve servisleri başlat
db.init_app(app)
i18n.init_app(app)


@app.route('/healthz')
def healthz():
    return jsonify({
        'status': 'ok' if app.config.get('DB_BOOTSTRAP_READY', False) else 'degraded',
        'database_ready': app.config.get('DB_BOOTSTRAP_READY', False),
        'database_error': app.config.get('DB_BOOTSTRAP_ERROR') if app.config.get('TESTING') else None,
        'environment': app.config.get('ENV') or app.config.get('FLASK_ENV') or 'production',
    })


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )

try:
    init_database(app)
except Exception as init_error:
    logger.exception("Database initialization did not complete successfully: %s", init_error)

# Demo data configuration validation on startup
try:
    from domain.demo.startup_validation import validate_demo_data_config
    with app.app_context():
        if not validate_demo_data_config():
            logger.warning("Demo data configuration validation failed. Demo data generation may not work correctly.")
except Exception as e:
    logger.warning(f"Demo data configuration validation error: {e}")

register_routes(app)

# Flask-Limiter mevcutsa kritik endpoint'lere spesifik limitler ekle
# register_routes'TAN SONRA çalışır — view fonksiyonu bu noktada kayıtlı
if _limiter_instance is not None:
    try:
        # Login endpoint'i için sıkı limit
        login_view = app.view_functions.get('auth.login')
        if login_view:
            decorated = _limiter_instance.limit(
                "10 per minute",
                methods=["POST"],
                error_message="Çok fazla giriş denemesi. Lütfen bir dakika bekleyin.",
            )(login_view)
            app.view_functions['auth.login'] = decorated
            logger.debug("Flask-Limiter: /login route'una 10/dk limit uygulandı.")

        # Register endpoint'i için sıkı limit
        register_view = app.view_functions.get('auth.register')
        if register_view:
            decorated = _limiter_instance.limit(
                "5 per minute",
                methods=["POST"],
                error_message="Çok fazla kayıt denemesi. Lütfen bir dakika bekleyin.",
            )(register_view)
            app.view_functions['auth.register'] = decorated
            logger.debug("Flask-Limiter: /register route'una 5/dk limit uygulandı.")

        # Password reset endpoint'i için sıkı limit
        reset_view = app.view_functions.get('auth.reset_password')
        if reset_view:
            decorated = _limiter_instance.limit(
                "3 per hour",
                methods=["POST"],
                error_message="Çok fazla şifre sıfırlama denemesi. Lütfen bir saat bekleyin.",
            )(reset_view)
            app.view_functions['auth.reset_password'] = decorated
            logger.debug("Flask-Limiter: /reset_password route'una 3/saat limit uygulandı.")

        # Settings reset_data endpoint'i için sıkı limit (3 per minute)
        settings_reset_view = app.view_functions.get('settings.reset_data')
        if settings_reset_view:
            decorated = _limiter_instance.limit(
                "3 per minute",
                methods=["POST"],
                error_message="Çok fazla veri sıfırlama denemesi. Lütfen bekleyin.",
            )(settings_reset_view)
            app.view_functions['settings.reset_data'] = decorated
            logger.debug("Flask-Limiter: /reset_data route'una 3/dk limit uygulandı.")

        if app.config.get('TESTING', False):
            _limiter_instance.enabled = False
            logger.debug("Flask-Limiter disabled in testing mode.")
    except Exception as _e:
        logger.warning("Flask-Limiter route binding başarısız: %s", _e)

# Tenant context middleware'i kaydet
@app.before_request
def tenant_context_middleware():
    """
    Her istekte tenant context'i set eder
    g.current_user ve g.tenant_id'yi ayarlar
    """
    result = set_tenant_context()
    if result:
        return result


# Temizlik: request sonunda TenantContext temizle
@app.teardown_request
def clear_tenant_context(exception=None):
    """Tüm istek sonrası TenantContext'i temizleyerek leakage önler"""
    try:
        from domain.tenant.context import TenantContext
        TenantContext.set(None)
    except Exception:
        pass

# HTTPS enforcement middleware
# Config bir kez okunur; her request'te yeniden parse edilmez.
_force_https = config.FORCE_HTTPS
_https_enabled = config.HTTPS_ENABLED

@app.before_request
def enforce_https():
    """
    HTTPS zorunlu hale getirir (production ortamında)
    FORCE_HTTPS=True veya HTTPS_ENABLED=True olduğunda HTTP isteklerini HTTPS'e yönlendirir
    """
    if _force_https or _https_enabled:
        from flask import redirect, request
        if not request.is_secure:
            return redirect(request.url.replace('http://', 'https://'), code=301)

# Arka plan veri güncelleme servisini başlatma ve yönetme
import atexit

from application.transactions.handlers import register_handlers
from bootstrap import get_container
from infrastructure.background.outbox_processor import OutboxProcessor

_background_workers_started = False
_background_service = None
_outbox_processor = None
_ledger_watchdog_worker = None
_event_bus = None


def _background_workers_enabled(owner: str = "web"):
    if app.config.get('TESTING', False):
        return False
    if app.config.get('DISABLE_BACKGROUND_SERVICE'):
        return False
    if os.environ.get('DISABLE_BACKGROUND_SERVICE', 'false').lower() == 'true':
        return False
    configured_owner = str(
        app.config.get('BACKGROUND_WORKER_OWNER')
        or os.environ.get('BACKGROUND_WORKER_OWNER', 'web')
    ).strip().lower()
    if configured_owner and configured_owner != str(owner or 'web').strip().lower():
        return False
    return True


def _start_background_workers(owner: str = "web"):
    global _background_workers_started, _event_bus, _outbox_processor, _ledger_watchdog_worker
    if _background_workers_started:
        return
    if not _background_workers_enabled(owner=owner):
        logger.info("Background services disabled by configuration.")
        _background_workers_started = True
        return

    global _background_service

    try:
        from infrastructure.background.background_service import get_background_service
        _background_service = get_background_service()
        _background_service.start()
    except Exception as e:
        logger.exception("Arka plan servisi başlatılamadı, uygulama servissiz devam edecek: %s", e)

    try:
        _event_bus = get_container().infrastructure.async_event_bus()
        register_handlers(_event_bus)
        _outbox_processor = OutboxProcessor(event_bus=_event_bus, app=app)
        _outbox_processor.start(interval_seconds=5)
    except Exception as e:
        _outbox_processor = None
        logger.exception("OutboxProcessor başlatılamadı: %s", e)

    try:
        from infrastructure.background.ledger_watchdog_worker import get_ledger_watchdog_worker
        _ledger_watchdog_worker = get_ledger_watchdog_worker(flask_app=app, interval_seconds=300)
        _ledger_watchdog_worker.start()
    except Exception as e:
        _ledger_watchdog_worker = None
        logger.exception("LedgerWatchdogWorker başlatılamadı: %s", e)

    _background_workers_started = True


@app.before_request
def _initialize_background_workers_on_first_request():
    if not _background_workers_started:
        _start_background_workers()


def _cleanup_database_resources():
    """Explicitly remove DB session and dispose engine at process exit."""
    try:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
    except Exception as exc:
        print(f"DB cleanup failed during shutdown: {exc}", file=sys.stderr)


# Register DB cleanup before background service shutdown so it runs last.
atexit.register(_cleanup_database_resources)


def _stop_background_service():
    try:
        from infrastructure.background.background_service import get_background_service_instance
        svc = get_background_service_instance()
        if svc is not None:
            svc.stop()
    except Exception as exc:
        print(f"BackgroundService stop failed during shutdown: {exc}", file=sys.stderr)

atexit.register(_stop_background_service)


def _stop_outbox_processor():
    try:
        if _outbox_processor is not None:
            _outbox_processor.stop()
    except Exception as exc:
        print(f"OutboxProcessor stop failed during shutdown: {exc}", file=sys.stderr)

atexit.register(_stop_outbox_processor)


def _stop_ledger_watchdog():
    try:
        if _ledger_watchdog_worker is not None:
            _ledger_watchdog_worker.stop()
    except Exception as exc:
        print(f"LedgerWatchdogWorker stop failed during shutdown: {exc}", file=sys.stderr)

atexit.register(_stop_ledger_watchdog)


def _shutdown_event_bus():
    try:
        if _event_bus is not None and hasattr(_event_bus, 'shutdown'):
            _event_bus.shutdown(wait=False)
    except Exception as exc:
        print(f"EventBus shutdown failed during shutdown: {exc}", file=sys.stderr)

atexit.register(_shutdown_event_bus)


def create_app():
    """Application factory compatibility wrapper returning the application instance."""
    return app


if __name__ == '__main__':
    # Lokal geliştirme için tarayıcı açma fonksiyonu
    import time
    import urllib.request
    import webbrowser
    from threading import Thread

    def open_browser():
        """
        Sunucu gerçekten hazır olduğunda tarayıcıyı açar.
        Sabit bekleme yerine health-check polling kullanır — race condition'ı önler.
        """
        url = "http://127.0.0.1:5000"
        max_attempts = 30          # toplam ~15 saniye dene
        interval = 0.5              # her 500ms'de bir kontrol et

        for attempt in range(max_attempts):
            try:
                urllib.request.urlopen(url, timeout=1)
                webbrowser.open(url)
                logger.info("Sunucu hazır, tarayıcı açıldı (deneme: %d)", attempt + 1)
                return
            except Exception:
                time.sleep(interval)

        logger.warning("Sunucu %d denemede yanıt vermedi, tarayıcı açılmadı.", max_attempts)

    # Ayrı bir thread'de health-check polling başlat (sunucu bloklanmasın)
    Thread(target=open_browser, daemon=True).start()
    # Windows stabilitesi için debug=False önerilir
    # Geliştirme aşamasında hataları görmek için debug=True yapıldı
    _start_background_workers()
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
