"""
Centralized configuration management for E-Cüzdan application.
All configuration settings are managed in one place for easier maintenance.
"""

import os

from dotenv import load_dotenv
from shared.decimal_precision import to_decimal

# Project root directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file in project root
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """Application configuration class"""

    # Environment
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')

    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "e_cuzdan_v15.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    def __init__(self):
        """Initialize and validate configuration"""
        # Re-read dynamically from environment to support container/runtime injection
        self.FLASK_ENV = os.getenv('FLASK_ENV', self.FLASK_ENV)
        self.SECRET_KEY = os.getenv('SECRET_KEY', self.SECRET_KEY)

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

    # OAuth Settings
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Session Configuration
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '2'))
    SESSION_COOKIE_HTTPONLY = True
    # For development: use 'Lax' for OAuth compatibility without HTTPS
    # For production with HTTPS: use 'None' with SESSION_COOKIE_SECURE=True
    SESSION_COOKIE_SAMESITE = 'Lax' if os.getenv('HTTPS_ENABLED', 'false').lower() == 'false' else 'None'
    SESSION_COOKIE_SECURE = os.getenv('HTTPS_ENABLED', 'false').lower() == 'true'  # Auto-detect from environment
    SESSION_REFRESH_EACH_REQUEST = True

    # HTTPS Configuration
    HTTPS_ENABLED = os.getenv('HTTPS_ENABLED', 'false').lower() == 'true'
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'

    # Application Boot ID (for session invalidation on restart)
    APP_BOOT_ID = os.getenv('APP_BOOT_ID', None)

    # Financial Configuration
    DEFAULT_CURRENCY = 'TRY'
    INFLATION_RATE = to_decimal(os.getenv('INFLATION_RATE', '0.40'))

    # Service Configuration
    BACKGROUND_SERVICE_ENABLED = os.getenv('BACKGROUND_SERVICE_ENABLED', 'true').lower() == 'true'
    MARKET_DATA_UPDATE_INTERVAL = int(os.getenv('MARKET_DATA_UPDATE_INTERVAL', '3600'))  # 1 hour

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'e_cuzdan.log')

    # Observability (opt-in)
    OTEL_ENABLED = os.getenv('OTEL_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    LOG_ALERTS_ENABLED = os.getenv('LOG_ALERTS_ENABLED', 'false').lower() in ('1', 'true', 'yes')

    # User Configuration
    # Platform sahibinin kullanıcı adı. Ortam değişkeniyle değiştirilebilir;
    # varsayılan mevcut kurulumlarla geriye dönük uyumluluk içindir.
    SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'emin')

    @classmethod
    def from_env(cls):
        """Create configuration from environment variables"""
        return cls()
