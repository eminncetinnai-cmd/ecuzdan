"""
Tests for centralized configuration validation and security hardening.
"""

import os
from decimal import Decimal

import pytest

from config import Config


def test_config_development_fallback_allowed():
    """Verify that fallback SECRET_KEY is allowed in development environment."""
    os.environ['FLASK_ENV'] = 'development'
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    # Should not raise any error
    config = Config()
    assert config.SECRET_KEY == 'dev-secret-key-change-in-production'
    assert config.FLASK_ENV == 'development'


def test_config_testing_fallback_allowed():
    """Verify that fallback SECRET_KEY is allowed in testing environment."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    # Should not raise any error
    config = Config()
    assert config.SECRET_KEY == 'dev-secret-key-change-in-production'
    assert config.FLASK_ENV == 'testing'


def test_config_production_fallback_raises_error():
    """Verify that default fallback SECRET_KEY raises ValueError in production."""
    os.environ['FLASK_ENV'] = 'production'
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    with pytest.raises(ValueError) as excinfo:
        Config()

    assert "CRITICAL SECURITY ERROR" in str(excinfo.value)


def test_config_production_empty_secret_raises_error():
    """Verify that missing SECRET_KEY raises ValueError in production."""
    os.environ['FLASK_ENV'] = 'production'
    # Delete SECRET_KEY env variable if exists
    if 'SECRET_KEY' in os.environ:
        del os.environ['SECRET_KEY']

    # Temporarily override default class fallback to verify None check
    original_secret_key = Config.SECRET_KEY
    Config.SECRET_KEY = None
    try:
        with pytest.raises(ValueError) as excinfo:
            Config()
        assert "CRITICAL SECURITY ERROR" in str(excinfo.value)
    finally:
        Config.SECRET_KEY = original_secret_key


def test_config_production_secure_key_allowed(monkeypatch):
    """Verify that a complete secure production configuration is accepted."""
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'a-secure-custom-key-12345678901234567890123456789012')
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://app:placeholder@db.internal:5432/e_cuzdan')
    monkeypatch.setenv('HTTPS_ENABLED', 'true')
    monkeypatch.setenv('FORCE_HTTPS', 'true')
    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'redis://:placeholder@redis.internal:6379/0')

    config = Config()
    assert config.SECRET_KEY == 'a-secure-custom-key-12345678901234567890123456789012'
    assert config.FLASK_ENV == 'production'
    assert config.HTTPS_ENABLED is True
    assert config.FORCE_HTTPS is True


def test_config_inflation_rate_uses_decimal():
    """Verify the default inflation rate is stored as a Decimal for financial precision."""
    os.environ['FLASK_ENV'] = 'development'
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    config = Config()
    assert isinstance(config.INFLATION_RATE, Decimal)
    assert config.INFLATION_RATE == Decimal('0.4000')
