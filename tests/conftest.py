"""
Test Configuration - Profesyonel Test Mimarisi
Test ortamı, fixtures ve test yardımcıları
"""

import sys
from pathlib import Path
import pytest
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'

from app import app as app_factory
from app import db
from models import AssetSector, AssetType, Category, Tenant, Transaction, User


@pytest.fixture
def app():
    """Flask uygulaması için fixture"""
    app = app_factory
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['DISABLE_BACKGROUND_SERVICE'] = True
    # Test environment should not be rate-limited by brute-force protection.
    if hasattr(app, 'extensions') and 'limiter' in app.extensions:
        try:
            app.extensions['limiter'].enabled = False
        except Exception:
            pass

    # Background service'i durdur
    from infrastructure.background.background_service import get_background_service_instance
    background_service = get_background_service_instance()
    if background_service is not None:
        background_service.stop()

    with app.app_context():
        # Manually create the in-memory engine and override the default engine bind
        import sqlalchemy as sa
        from sqlalchemy.pool import QueuePool

        worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'main')
        db_path = Path(app.instance_path) / f'e_cuzdan_test_{worker_id}.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.unlink(missing_ok=True)
        engine = sa.create_engine(
            f'sqlite:///{db_path.as_posix()}',
            connect_args={'check_same_thread': False},
            poolclass=QueuePool,
        )
        original_engines = dict(getattr(db, 'engines', {}))

        if hasattr(db, 'engines'):
            for existing_engine in original_engines.values():
                existing_engine.dispose()
            db.engines[None] = engine

        try:
            db.drop_all()
            db.create_all()
            _seed_test_data()
            yield app
        finally:
            db.session.remove()
            engine.dispose()
            db_path.unlink(missing_ok=True)
            if hasattr(db, 'engines'):
                db.engines.clear()
                db.engines.update(original_engines)


def _seed_test_data():
    """Test veritabanı için minimum referans veriler (idempotent)."""
    from werkzeug.security import generate_password_hash

    # Varsayılan tenant oluştur
    if not Tenant.query.filter_by(id='default').first():
        db.session.add(Tenant(id='default', name='Default Tenant'))
        db.session.flush()

    default_tenant = Tenant.query.filter_by(id='default').first()

    if not User.query.filter_by(username='testuser').first():
        db.session.add(User(
            username='testuser',
            password=generate_password_hash('testpass'),
            role='kullanici',
            tenant_id=default_tenant.id,
        ))
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(
            username='admin',
            password=generate_password_hash('adminpass'),
            role='yonetici',
            tenant_id=default_tenant.id,
        ))
    if not User.query.filter_by(username='emin').first():
        db.session.add(User(
            username='emin',
            password=generate_password_hash('1'),
            role='sistem_yoneticisi',
            tenant_id=default_tenant.id,
        ))
    for name, ctype in [
        ('Maaş', 'Gelir'), ('Avans', 'Gelir'), ('Ek Gelir', 'Gelir'), ('Kira', 'Gelir'),
        ('Vergi', 'Gider'), ('Kredi', 'Gider'), ('Kredi Kartı', 'Gider'),
        ('Aylık Sabit Gider', 'Gider'), ('Yatırıma Aktarılan', 'Yatırım'),
    ]:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, type=ctype))
    if not AssetType.query.filter_by(name='Hisse Senedi').first():
        db.session.add(AssetType(name='Hisse Senedi'))
    if not AssetSector.query.filter_by(name='Teknoloji').first():
        db.session.add(AssetSector(name='Teknoloji'))
    db.session.commit()


@pytest.fixture
def client(app):
    """Test client'i için fixture"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Test kullanıcısı için fixture"""
    return User.query.filter_by(username='testuser').first()


@pytest.fixture
def admin_user(app):
    """Admin kullanıcısı için fixture"""
    return User.query.filter_by(username='admin').first()


@pytest.fixture
def test_category(app):
    """Test kategorisi için fixture"""
    return Category.query.filter_by(name='Maaş').first()


@pytest.fixture
def test_transaction(app, test_category):
    """Test işlemi için fixture"""
    default_tenant = Tenant.query.filter_by(id='default').first()
    transaction = Transaction(
        date='2025-01-01',
        category=test_category.name,
        description='Test işlemi',
        type=test_category.type,
        amount=1000,
        status='Ödendi',
        tenant_id=default_tenant.id,
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction


@pytest.fixture
def authenticated_client(client, test_user):
    """Giriş yapmış test client'i için fixture"""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
        sess['username'] = test_user.username
    return client


@pytest.fixture
def authenticated_admin_client(client, admin_user):
    """Giriş yapmış yönetici test client'i için fixture"""
    with client.session_transaction() as sess:
        sess['user_id'] = admin_user.id
        sess['username'] = admin_user.username
    return client


@pytest.fixture
def container(app):
    """Composition Root container fixture for tests.

    Resets container before and after each test to ensure isolation. Tests may
    call container.repositories.set_override(...) before obtaining
    container.applications to inject fakes/mocks.
    """
    from bootstrap import get_container, reset_container

    # Reset before test to ensure clean singletons
    reset_container()
    c = get_container()
    try:
        yield c
    finally:
        # Reset after test to avoid leaking singletons/overrides between tests
        reset_container()


# Profesyonel Test Fixtures

@pytest.fixture
def sample_user_data():
    """Örnek kullanıcı verisi fixture'ı"""
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'role': 'kullanici',
        'email': 'test@example.com'
    }


@pytest.fixture
def sample_transaction_data():
    """Örnek işlem verisi fixture'ı"""
    return {
        'date': '2025-01-01',
        'category': 'Maaş',
        'description': 'Test işlemi',
        'type': 'Gelir',
        'amount': 10000,
        'status': 'Ödendi'
    }


@pytest.fixture
def sample_asset_data():
    """Örnek varlık verisi fixture'ı"""
    return {
        'type': 'Hisse Senedi',
        'name': 'YKBNK',
        'value': 50000,
        'description': 'Yapı Kredi Bankası',
        'purchase_date': '2023-01-15',
        'purchase_cost': 45000,
        'quantity': 1000,
        'unit_price': 45,
        'currency': 'TRY',
        'symbol': 'YKBNK.E',
        'risk_level': 'Orta',
        'liquidity': 'Yarı-Likit'
    }


@pytest.fixture
def mock_logger():
    """Mock logger fixture'ı"""
    from unittest.mock import Mock
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


# Test Yardımcı Fonksiyonları

def create_test_user(username='testuser', role='kullanici', tenant_id='default'):
    """Test kullanıcısı oluşturma yardımcısı"""
    from werkzeug.security import generate_password_hash
    from models import User

    user = User(
        username=username,
        password=generate_password_hash('testpass'),
        role=role,
        tenant_id=tenant_id
    )
    return user


def create_test_category(name='Test Kategori', type='Gelir'):
    """Test kategorisi oluşturma yardımcısı"""
    from models import Category

    category = Category(name=name, type=type)
    return category


def create_test_transaction(**kwargs):
    """Test işlemi oluşturma yardımcısı"""
    from models import Transaction

    defaults = {
        'date': '2025-01-01',
        'category': 'Test',
        'description': 'Test işlemi',
        'type': 'Gelir',
        'amount': 1000,
        'status': 'Ödendi'
    }
    defaults.update(kwargs)

    return Transaction(**defaults)


# Test Hooks

def pytest_configure(config):
    """Pytest yapılandırması"""
    config.addinivalue_line(
        "markers", "unit: Unit tests - isolated component tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests - component interaction tests"
    )
    config.addinivalue_line(
        "markers", "regression: Regression tests - bug fix validation"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests - full system tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "fast: Fast running tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication related tests"
    )
    config.addinivalue_line(
        "markers", "db: Database related tests"
    )
    config.addinivalue_line(
        "markers", "api: API related tests"
    )
    config.addinivalue_line(
        "markers", "ui: UI related tests"
    )
    config.addinivalue_line(
        "markers", "financial: Financial calculation tests"
    )
    config.addinivalue_line(
        "markers", "security: Security related tests"
    )


def pytest_collection_modifyitems(config, items):
    """Test collection özelleştirmesi"""
    # Slow testleri otomatik işaretle
    for item in items:
        if "slow" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.fast)
