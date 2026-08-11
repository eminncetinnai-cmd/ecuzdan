"""
Database Connection - Veritabanı bağlantı yönetimi
SQLite PRAGMA ayarları ve veritabanı başlatma
"""

import logging

from sqlalchemy import text

from models import db

logger = logging.getLogger(__name__)


def _should_attempt_recovery(app):
    """Local development ve test ortamında bootstrap kurtarma akışı çalıştır."""
    env_name = app.config.get('ENV') or app.config.get('FLASK_ENV') or ''
    return app.config.get('DB_RECOVERY_ON_STARTUP', env_name != 'production')


def _apply_sqlite_pragmas():
    """
    SQLite performans ayarlarını uygular.
    Sadece SQLite için çalışır; PostgreSQL gibi diğer DB'lerde sessizce atlar.
    Bu ayarlar verinin DOĞRULUĞUNU ETKILEMEZ, sadece I/O stratejisini optimize eder.
    """
    if 'sqlite' not in db.engine.url.drivername:
        logger.info("SQLite dışı DB tespit edildi, PRAGMA atlandı.")
        return

    pragmas = [
        # Foreign key desteğini aç, SQLite varsayılan olarak kapalıdır
        "PRAGMA foreign_keys=ON",

        # WAL modu: okuma işlemleri yazma işlemlerini bloklamaz
        # Eşzamanlı kullanıcılarda büyük fark yaratır
        "PRAGMA journal_mode=WAL",

        # 64MB sayfa önbelleği (varsayılan: 2MB)
        # Tekrarlayan sorguları bellekten okur, diskten değil
        "PRAGMA cache_size=-65536",

        # NORMAL: her commit'te disk sync yapmaz; güç kesintisine dayanıklı ama daha hızlı
        # FULL (varsayılan) her commit'te fsync() çağırır
        "PRAGMA synchronous=NORMAL",

        # Geçici tablolar için disk yerine RAM kullan
        "PRAGMA temp_store=MEMORY",

        # Memory-mapped I/O: 256MB — büyük sorgularda disk okuma hızını artırır
        "PRAGMA mmap_size=268435456",

        # Sayfa boyutu (varsayılan 4096 genellikle idealdir, değiştirme)
        # "PRAGMA page_size=4096"  ← Mevcut DB'de etki etmez, yorumda bırak
    ]

    with db.engine.connect() as conn:
        for pragma in pragmas:
            try:
                conn.execute(text(pragma))
                logger.debug("SQLite PRAGMA uygulandı: %s", pragma)
            except Exception as e:
                logger.warning("PRAGMA uygulanamadı (%s): %s", pragma, e)

    logger.info("SQLite performans ayarları uygulandı.")


def init_database(app):
    """Veritabanını başlatır ve gerekli tabloları oluşturur.

    Başlangıçta herhangi bir hata oluşursa, yerel geliştirme/test ortamında
    güvenli bir kurtarma akışı çalışır; böylece ana route'lar 500 yerine
    degrade edilmiş bir durumda yaşamaya devam eder.
    """
    from .migrations import _ensure_schema
    from .seeding import _initialize_default_data, _initialize_tenant_data, _migrate_legacy_plans

    with app.app_context():
        app.config.setdefault('DB_BOOTSTRAP_READY', False)
        app.config['DB_BOOTSTRAP_ERROR'] = None

        try:
            _apply_sqlite_pragmas()
            db.create_all()
            _ensure_schema()
            _initialize_default_data()
            _migrate_legacy_plans()
            _initialize_tenant_data()
            app.config['DB_BOOTSTRAP_READY'] = True
            logger.info("Database bootstrap completed successfully.")
        except Exception as exc:
            logger.exception("Database bootstrap failed: %s", exc)
            db.session.rollback()
            app.config['DB_BOOTSTRAP_ERROR'] = str(exc)

            if not _should_attempt_recovery(app):
                logger.warning("Database bootstrap recovery skipped for current environment.")
                return

            try:
                logger.warning("Attempting database bootstrap recovery by recreating tables.")
                db.session.remove()
                if db.engine.url.drivername.startswith('sqlite'):
                    db.drop_all()
                db.create_all()
                _ensure_schema()
                _initialize_default_data()
                _migrate_legacy_plans()
                _initialize_tenant_data()
                app.config['DB_BOOTSTRAP_READY'] = True
                app.config['DB_BOOTSTRAP_ERROR'] = None
                logger.info("Database bootstrap recovery completed successfully.")
            except Exception as recovery_error:
                logger.exception("Database bootstrap recovery failed: %s", recovery_error)
                app.config['DB_BOOTSTRAP_READY'] = False
                app.config['DB_BOOTSTRAP_ERROR'] = str(recovery_error)
        finally:
            db.session.remove()
