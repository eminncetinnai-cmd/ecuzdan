"""
Centralized configuration management for E-Cüzdan application.
All configuration settings are managed in one place for easier maintenance.
"""

import os

from dotenv import load_dotenv

from shared.decimal_precision import to_decimal

# Project root directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _bounded_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(int(os.getenv(name, str(default))), maximum))
    except (TypeError, ValueError):
        return default


# Load environment variables from .env file in project root
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """Application configuration class"""

    # Environment
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')

    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "e_cuzdan_v15.db")}')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    def __init__(self):
        """Initialize and validate configuration"""
        # Re-read dynamically from environment to support container/runtime injection
        self.FLASK_ENV = os.getenv('FLASK_ENV', self.FLASK_ENV)
        self.SECRET_KEY = os.getenv('SECRET_KEY', self.SECRET_KEY)
        db_url = os.getenv('DATABASE_URL', self.DATABASE_URL)
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        self.DATABASE_URL = db_url
        self.GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', self.GOOGLE_CLIENT_ID)
        self.GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', self.GOOGLE_CLIENT_SECRET)
        is_render = os.getenv('RENDER', 'false').lower() == 'true'
        default_https = 'true' if (self.FLASK_ENV == 'production' or is_render) else 'false'
        self.HTTPS_ENABLED = os.getenv('HTTPS_ENABLED', default_https).lower() == 'true'
        self.FORCE_HTTPS = os.getenv('FORCE_HTTPS', default_https).lower() == 'true'
        self.BACKGROUND_SERVICE_ENABLED = os.getenv(
            'BACKGROUND_SERVICE_ENABLED', str(self.BACKGROUND_SERVICE_ENABLED).lower()
        ).lower() == 'true'
        default_bg_owner = 'web' if (self.FLASK_ENV != 'production' or is_render or os.getenv('ALLOW_SINGLE_INSTANCE_RATELIMIT', '').lower() == 'true') else 'worker'
        self.BACKGROUND_WORKER_OWNER = os.getenv(
            'BACKGROUND_WORKER_OWNER', default_bg_owner
        ).strip().lower()
        self.FX_PROVIDER_CHAIN_ENABLED = os.getenv(
            'FX_PROVIDER_CHAIN_ENABLED', str(self.FX_PROVIDER_CHAIN_ENABLED)
        ).lower() == 'true'
        self.FX_PROVIDER_TIMEOUT_SECONDS = _bounded_int_env(
            'FX_PROVIDER_TIMEOUT_SECONDS', self.FX_PROVIDER_TIMEOUT_SECONDS, 2, 30
        )
        self.FX_PROVIDER_RETRIES = _bounded_int_env(
            'FX_PROVIDER_RETRIES', self.FX_PROVIDER_RETRIES, 0, 3
        )
        self.RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', self.RATELIMIT_STORAGE_URI)
        self.RATELIMIT_KEY_PREFIX = os.getenv('RATELIMIT_KEY_PREFIX', self.RATELIMIT_KEY_PREFIX)
        self.RATELIMIT_REDIS_SOCKET_TIMEOUT_SECONDS = _bounded_int_env(
            'RATELIMIT_REDIS_SOCKET_TIMEOUT_SECONDS',
            self.RATELIMIT_REDIS_SOCKET_TIMEOUT_SECONDS,
            1,
            10,
        )
        self.RATELIMIT_REDIS_CONNECT_TIMEOUT_SECONDS = _bounded_int_env(
            'RATELIMIT_REDIS_CONNECT_TIMEOUT_SECONDS',
            self.RATELIMIT_REDIS_CONNECT_TIMEOUT_SECONDS,
            1,
            10,
        )
        self.RATELIMIT_IN_MEMORY_FALLBACK_ENABLED = os.getenv(
            'RATELIMIT_IN_MEMORY_FALLBACK_ENABLED',
            str(self.RATELIMIT_IN_MEMORY_FALLBACK_ENABLED),
        ).lower() == 'true'
        default_proxy_hops = '1' if is_render else str(self.TRUST_PROXY_HOPS)
        self.TRUST_PROXY_HOPS = int(os.getenv('TRUST_PROXY_HOPS', default_proxy_hops))

        if is_render or os.getenv('ALLOW_SINGLE_INSTANCE_RATELIMIT', '').lower() == 'true':
            self.RATELIMIT_IN_MEMORY_FALLBACK_ENABLED = True
            if self.RATELIMIT_STORAGE_URI.startswith('redis://127.0.0.1'):
                self.RATELIMIT_STORAGE_URI = 'memory://'

        # Hard security validation in production
        if self.FLASK_ENV not in ('development', 'testing'):
            if not self.SECRET_KEY or self.SECRET_KEY == 'dev-secret-key-change-in-production':
                raise ValueError(
                    "CRITICAL SECURITY ERROR: SECRET_KEY must be explicitly set to a secure, "
                    "non-default value in a production environment."
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: SECRET_KEY must be at least 32 characters long."
                )
            if not self.HTTPS_ENABLED or not self.FORCE_HTTPS:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: HTTPS_ENABLED and FORCE_HTTPS must both be true in production."
                )
            if not os.getenv('DATABASE_URL'):
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: DATABASE_URL must be explicitly set in production."
                )
            allow_sqlite_prod = os.getenv('ALLOW_SQLITE_IN_PRODUCTION', 'false').lower() == 'true'
            if 'sqlite' in self.DATABASE_URL.lower() and not allow_sqlite_prod:
                raise ValueError(
                    "CRITICAL PRODUCTION DATA SAFETY ERROR: SQLite on an ephemeral container filesystem "
                    "risks silent data loss on restart or redeploy. A persistent managed database (PostgreSQL) "
                    "must be configured via DATABASE_URL in production. "
                    "To explicitly bypass this check for testing, set ALLOW_SQLITE_IN_PRODUCTION=true."
                )
            allow_single_instance = (
                os.getenv('ALLOW_SINGLE_INSTANCE_RATELIMIT', 'false').lower() == 'true'
                or is_render
            )
            if self.RATELIMIT_STORAGE_URI.startswith('memory://') and not allow_single_instance:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: RATELIMIT_STORAGE_URI must use a shared persistent backend in production (or set ALLOW_SINGLE_INSTANCE_RATELIMIT=true for single-container deployment)."
                )

    # OAuth Settings
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Session Configuration
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
    REMEMBER_COOKIE_DAYS = int(os.getenv('REMEMBER_COOKIE_DAYS', '60'))
    SESSION_COOKIE_HTTPONLY = True
    _default_https_class = 'true' if (FLASK_ENV == 'production' or os.getenv('RENDER') == 'true') else 'false'
    # Use Lax by default for rock-solid cross-browser and mobile support
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.getenv('HTTPS_ENABLED', _default_https_class).lower() == 'true'  # Auto-detect from environment
    SESSION_REFRESH_EACH_REQUEST = True

    # HTTPS Configuration
    HTTPS_ENABLED = os.getenv('HTTPS_ENABLED', _default_https_class).lower() == 'true'
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', _default_https_class).lower() == 'true'

    # Application Boot ID (for session invalidation on restart)
    APP_BOOT_ID = os.getenv('APP_BOOT_ID', None)

    # Financial Configuration
    DEFAULT_CURRENCY = 'TRY'
    INFLATION_RATE = to_decimal(os.getenv('INFLATION_RATE', '0.40'))

    # Service Configuration
    _is_render_cls = os.getenv('RENDER', 'false').lower() == 'true' or os.getenv('ALLOW_SINGLE_INSTANCE_RATELIMIT', '').lower() == 'true'
    BACKGROUND_SERVICE_ENABLED = os.getenv(
        'BACKGROUND_SERVICE_ENABLED', 'true' if (_is_render_cls or FLASK_ENV != 'production') else 'true'
    ).lower() == 'true'
    BACKGROUND_WORKER_OWNER = os.getenv(
        'BACKGROUND_WORKER_OWNER', 'web' if (_is_render_cls or FLASK_ENV != 'production') else 'worker'
    ).strip().lower()
    # Public FX/metals provider resilience (indicative/local-staging data only).
    FX_PROVIDER_CHAIN_ENABLED = os.getenv('FX_PROVIDER_CHAIN_ENABLED', 'true').lower() == 'true'
    FX_PROVIDER_TIMEOUT_SECONDS = _bounded_int_env('FX_PROVIDER_TIMEOUT_SECONDS', 8, 2, 30)
    FX_PROVIDER_RETRIES = _bounded_int_env('FX_PROVIDER_RETRIES', 1, 0, 3)

    # Production reverse proxy and rate limiting
    # Redis is the canonical shared backend; local/test may opt into bounded
    # in-memory fallback when the local Redis service is not running.
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'redis://127.0.0.1:6379/0')
    RATELIMIT_KEY_PREFIX = os.getenv('RATELIMIT_KEY_PREFIX', 'ecuzdan:v15')
    RATELIMIT_REDIS_SOCKET_TIMEOUT_SECONDS = _bounded_int_env(
        'RATELIMIT_REDIS_SOCKET_TIMEOUT_SECONDS', 1, 1, 10
    )
    RATELIMIT_REDIS_CONNECT_TIMEOUT_SECONDS = _bounded_int_env(
        'RATELIMIT_REDIS_CONNECT_TIMEOUT_SECONDS', 1, 1, 10
    )
    RATELIMIT_IN_MEMORY_FALLBACK_ENABLED = FLASK_ENV in ('development', 'testing')
    TRUST_PROXY_HOPS = int(os.getenv('TRUST_PROXY_HOPS', '0'))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.abspath(os.getenv('ECUZDAN_LOG_DIR', os.path.join(BASE_DIR, 'logs')))
    LOG_FILE = os.path.join(LOG_DIR, 'e_cuzdan.log')

    # Observability (opt-in)
    OTEL_ENABLED = os.getenv('OTEL_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    LOG_ALERTS_ENABLED = os.getenv('LOG_ALERTS_ENABLED', 'false').lower() in ('1', 'true', 'yes')

    # User Configuration
    # Platform sahibinin kullanıcı adı ve yetkili e-postaları. Ortam değişkeniyle genişletilebilir.
    SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'emin')
    SUPER_ADMIN_USERNAMES = frozenset(
        u.strip().lower() for u in os.getenv(
            'SUPER_ADMIN_USERNAMES',
            'emin,eminncetinn@gmail.com,eminncetinn.ai@gmail.com'
        ).split(',') if u.strip()
    )

    @classmethod
    def from_env(cls):
        """Create configuration from environment variables"""
        return cls()
