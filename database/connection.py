"""
Database Connection - Veritabanı bağlantı yönetimi
SQLite PRAGMA ayarları ve veritabanı başlatma
"""

import logging

from sqlalchemy import event, text

from models import db

logger = logging.getLogger(__name__)


def _should_attempt_recovery(app):
    """Local development ve test ortamında bootstrap kurtarma akışı çalıştır."""
    env_name = app.config.get('ENV') or app.config.get('FLASK_ENV') or ''
    return app.config.get('DB_RECOVERY_ON_STARTUP', env_name != 'production')


def _apply_sqlite_connection_pragmas(dbapi_connection, connection_record):
    """Apply connection-local SQLite safety and performance settings to every pooled handle."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-65536")  # 64MB sayfa önbelleği
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
    finally:
        cursor.close()


def _apply_sqlite_pragmas():
    """
    SQLite performans ayarlarını uygular.
    Sadece SQLite için çalışır; PostgreSQL gibi diğer DB'lerde sessizce atlar.
    Bu ayarlar verinin DOĞRULUĞUNU ETKILEMEZ, sadece I/O stratejisini optimize eder.
    """
    if 'sqlite' not in db.engine.url.drivername:
        logger.info("SQLite dışı DB tespit edildi, PRAGMA atlandı.")
        return

    if not event.contains(db.engine, "connect", _apply_sqlite_connection_pragmas):
        event.listen(db.engine, "connect", _apply_sqlite_connection_pragmas)

    # WAL modu veritabanı dosyasının header'ında kalıcı olarak saklanır.
    with db.engine.connect() as conn:
        try:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            logger.debug("SQLite WAL modu uygulandı.")
        except Exception as e:
            logger.warning("WAL modu uygulanamadı: %s", e)

    logger.debug("SQLite performans ayarları ve bağlantı dinleyicisi aktif.")



def init_database(app):
    """Veritabanını başlatır ve gerekli tabloları oluşturur.

    Başlangıçta herhangi bir hata oluşursa, yerel geliştirme/test ortamında
    güvenli bir kurtarma akışı çalışır; böylece ana route'lar 500 yerine
    degrade edilmiş bir durumda yaşamaya devam eder.
    """
    # Ensure the outbox model is registered before db.create_all() runs.
    from infrastructure.database.models.outbox_model import OutboxMessageModel  # noqa: F401

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
            logger.debug("Database bootstrap completed successfully.")
        except Exception as exc:
            logger.exception("Database bootstrap failed: %s", exc)
            db.session.rollback()
            app.config['DB_BOOTSTRAP_ERROR'] = str(exc)

            if 'locked' in str(exc).lower():
                logger.warning("Database is temporarily locked by another process; skipping drop/recreate recovery.")
                return

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


def checkpoint_sqlite_wal(truncate: bool = True) -> bool:
    """Flush dirty WAL pages back to database and optionally truncate WAL file.

    Frees disk space, keeps the WAL file bounded, and prevents slow index scans.

    Args:
        truncate: If True, executes PRAGMA wal_checkpoint(TRUNCATE).
                  If False, executes PRAGMA wal_checkpoint(PASSIVE).

    Returns:
        bool: True if checkpoint succeeded, False otherwise.
    """
    ctx = None
    try:
        from flask import has_app_context
        if not has_app_context():
            from app import app
            ctx = app.app_context()
    except Exception:
        ctx = None

    def _do_checkpoint():
        if 'sqlite' not in db.engine.url.drivername:
            return False

        mode = "TRUNCATE" if truncate else "PASSIVE"
        try:
            with db.engine.connect() as conn:
                conn.execute(text("PRAGMA optimize"))
                conn.execute(text(f"PRAGMA wal_checkpoint({mode})"))
                logger.info("SQLite PRAGMA optimize & WAL checkpoint (%s) successfully executed.", mode)
                return True
        except Exception as exc:
            logger.warning("SQLite WAL checkpoint failed: %s", exc)
            return False

    if ctx is not None:
        with ctx:
            return _do_checkpoint()
    return _do_checkpoint()

