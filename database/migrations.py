"""
Database Migrations - Veritabanı migration yönetimi
Schema versiyonlama ve tablo yapısı güncellemeleri
"""

import logging

from sqlalchemy import inspect, text

from database.phase3_concurrency import ensure_phase3_columns
from database.schema_version import SCHEMA_VERSION
from models import (
    Asset,
    BankAccount,
    BankStatementSnapshot,
    InvestorProfileAnswer,
    ProfileQuestion,
    RecurringPlan,
    Transaction,
    User,
    UserIban,
    db,
)

logger = logging.getLogger(__name__)


def _ensure_schema():
    """Eksik sütunları ekler (SQLite uyumlu)"""

    # Ensure legacy databases expose the table consumed by OutboxProcessor.
    # db.create_all() is idempotent and remains compatible with migration test doubles.
    db.create_all()
    ensure_phase3_columns(db.engine)

    # Schema versiyon tablosu yoksa oluştur (tek satırlık meta tablo)
    with db.engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS _schema_version "
            "(version VARCHAR(20) PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        ))
        row = conn.execute(
            text("SELECT version FROM _schema_version WHERE version = :v"),
            {"v": SCHEMA_VERSION}
        ).fetchone()

        if row:
            logger.debug("Schema versiyon kaydı bulundu (%s); eksik sütunlar kontrol ediliyor.", SCHEMA_VERSION)
            # Daha önce bu versiyon uygulanmış olabilir; eksik kolonları yine de
            # kontrol etmeliyiz çünkü migration kısmi kalmış veya eski DB'lerde
            # satır bazında sütun eksikliği olabilir.
            # Not: return kaldırıldı, böylece eksik sütun kontrolleri devam eder.

    # --- MEVCUT SCHEMA KONTROL KODU BURADAN DEVAM EDER ---
    inspector = inspect(db.engine)

    # Tenant tablosu oluştur (yeni)
    if 'tenant' not in inspector.get_table_names():
        logger.info("Tenant tablosu oluşturuluyor...")
        db.create_all()

    # Transaction tablosu için note, installment_number ve diğer yeni sütunlar
    if 'transaction' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('transaction')}
        if 'note' not in cols:
            table = Transaction.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN note VARCHAR(200)'))
        if 'installment_number' not in cols:
            table = Transaction.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN installment_number INTEGER'))
            logger.info("Transaction tablosuna installment_number sütunu eklendi")
        if 'is_admin_generated' not in cols:
            table = Transaction.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN is_admin_generated BOOLEAN DEFAULT 0'))
            logger.info("Transaction tablosuna is_admin_generated sütunu eklendi")
        if 'tenant_id' not in cols:
            table = Transaction.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN tenant_id VARCHAR(50)'))
            logger.info("Transaction tablosuna tenant_id sütunu eklendi")

    # User tablosu için password_changed_at, last_session_id ve role sütunları
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        if 'password_changed_at' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN password_changed_at DATETIME'))
        if 'last_session_id' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN last_session_id VARCHAR(64)'))
        if 'role' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN role VARCHAR(20) DEFAULT "kullanici"'))
        if 'profile_image' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN profile_image VARCHAR(200)'))
        if 'language' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN language VARCHAR(5) DEFAULT "tr"'))
        if 'tenant_id' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN tenant_id VARCHAR(50)'))
            logger.info("User tablosuna tenant_id sütunu eklendi")


    # Asset tablosu için profesyonel alanlar
    if 'asset' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('asset')}
        asset_columns = {
            'purchase_date': 'VARCHAR(10)',
            'purchase_cost': 'FLOAT DEFAULT 0.0',
            'quantity': 'FLOAT DEFAULT 1.0',
            'unit_price': 'FLOAT DEFAULT 0.0',
            'currency': 'VARCHAR(3) DEFAULT "TRY"',
            'symbol': 'VARCHAR(20)',
            'risk_level': 'VARCHAR(20) DEFAULT "Orta"',
            'liquidity': 'VARCHAR(20) DEFAULT "Likit"',
            'notes': 'VARCHAR(500)',
            'last_updated': 'VARCHAR(10)',
            'sector_id': 'INTEGER',
            'is_admin_generated': 'BOOLEAN DEFAULT 0',
            'tenant_id': 'VARCHAR(50)',
            'cost_method': 'VARCHAR(20) DEFAULT "WEIGHTED_AVERAGE"',
        }
        table = Asset.__tablename__
        with db.engine.begin() as conn:
            for col_name, col_def in asset_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"Asset tablosuna sütun eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"Asset sütunu ekleme hatası {col_name}: {e}")

    # Category tablosu için tenant_id (Faz 2.6 — tenant-özel kategoriler)
    if 'category' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('category')}
        if 'tenant_id' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE "category" ADD COLUMN tenant_id VARCHAR(50)'))
            logger.info("Category tablosuna tenant_id sütunu eklendi")

    # RecurringPlan tablosu için tenant_id
    if 'recurring_plan' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('recurring_plan')}
        if 'tenant_id' not in cols:
            table = RecurringPlan.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN tenant_id VARCHAR(50)'))
            logger.info("RecurringPlan tablosuna tenant_id sütunu eklendi")
        if 'start_date' not in cols:
            table = RecurringPlan.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN start_date VARCHAR(10)'))
            logger.info("RecurringPlan tablosuna start_date sütunu eklendi")

    # Transaction tablosu için transfer_from ve transfer_to (Faz 2 - Cash Flow Separation)
    if 'transaction' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('transaction')}
        if 'transfer_from' not in cols:
            table = Transaction.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN transfer_from VARCHAR(50)'))
            logger.info("Transaction tablosuna transfer_from sütunu eklendi")
        if 'transfer_to' not in cols:
            table = Transaction.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN transfer_to VARCHAR(50)'))
            logger.info("Transaction tablosuna transfer_to sütunu eklendi")

    # Category tablosu için subcategory (Faz 4 - Enhanced Categorization)
    if 'category' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('category')}
        if 'subcategory' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE "category" ADD COLUMN subcategory VARCHAR(50)'))
            logger.info("Category tablosuna subcategory sütunu eklendi")

    # Tenant tablosu için base_currency (Faz 5 - Multi-Currency)
    if 'tenant' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('tenant')}
        if 'base_currency' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE "tenant" ADD COLUMN base_currency VARCHAR(3) DEFAULT "TRY"'))
            logger.info("Tenant tablosuna base_currency sütunu eklendi")

    # User tablosu için base_currency (Faz 5 - Multi-Currency)
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        if 'base_currency' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN base_currency VARCHAR(3)'))
            logger.info("User tablosuna base_currency sütunu eklendi")

    # User tablosu için email alanı (Faz 22 - OAuth Sign-up/Sign-in)
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        if 'email' not in cols:
            table = User.__tablename__
            with db.engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN email VARCHAR(100) UNIQUE'))
                # Create index for email
                conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_user_email ON "{table}" (email)'))
            logger.info("User tablosuna email sütunu eklendi")

    # User tablosu için kişisel bilgi alanları (Faz 23 - User Profile Enhancement)
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        personal_info_columns = {
            'gender': 'VARCHAR(10)',
            'birthdate': 'DATE',
            'country': 'VARCHAR(50)',
            'city': 'VARCHAR(50)',
            'phone': 'VARCHAR(20)',
        }
        table = User.__tablename__
        with db.engine.begin() as conn:
            for col_name, col_def in personal_info_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"User tablosuna kişisel bilgi sütunu eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"User kişisel bilgi sütunu ekleme hatası {col_name}: {e}")

    # User tablosu için özel kod alanları (Faz 24 - Special Code System)
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        special_code_columns = {
            'special_code': 'VARCHAR(50)',
            'special_code_used_at': 'DATETIME',
        }
        table = User.__tablename__
        with db.engine.begin() as conn:
            for col_name, col_def in special_code_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"User tablosuna özel kod sütunu eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"User özel kod sütunu ekleme hatası {col_name}: {e}")

    # User tablosu için OAuth alanları (Faz 11 - Authentication Provider Framework)
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        oauth_columns = {
            'auth_provider': 'VARCHAR(20) DEFAULT "LOCAL"',
            'oauth_id': 'VARCHAR(100)',
            'avatar_url': 'VARCHAR(500)',
            'email_verified': 'BOOLEAN DEFAULT 0',
            'last_login_at': 'DATETIME',
            'created_via': 'VARCHAR(50) DEFAULT "web"',
        }
        table = User.__tablename__
        with db.engine.begin() as conn:
            for col_name, col_def in oauth_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"User tablosuna OAuth sütunu eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"User OAuth sütunu ekleme hatası {col_name}: {e}")

    # Category tablosu için hiyerarşi alanları (Faz 16 - Hierarchical Categorization)
    if 'category' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('category')}
        category_columns = {
            'parent_id': 'INTEGER',
            'level': 'INTEGER DEFAULT 0',
            'path': 'VARCHAR(200)',
            'icon': 'VARCHAR(50)',
            'color': 'VARCHAR(7)',
            'budget_limit': 'FLOAT',
            'is_active': 'BOOLEAN DEFAULT 1',
        }
        with db.engine.begin() as conn:
            for col_name, col_def in category_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "category" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"Category tablosuna sütun eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"Category sütunu ekleme hatası {col_name}: {e}")

    # AssetType tablosu için hiyerarşi alanları (Faz 16 - Hierarchical Asset Types)
    if 'asset_type' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('asset_type')}
        asset_type_columns = {
            'parent_id': 'INTEGER',
            'level': 'INTEGER DEFAULT 0',
            'risk_profile': 'VARCHAR(20)',
            'tax_treatment': 'VARCHAR(20)',
            'min_holding_period': 'INTEGER',
            'default_currency': 'VARCHAR(3) DEFAULT "TRY"',
            'liquidity_profile': 'VARCHAR(20)',
            'volatility_range': 'VARCHAR(20)',
        }
        with db.engine.begin() as conn:
            for col_name, col_def in asset_type_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "asset_type" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"AssetType tablosuna sütun eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"AssetType sütunu ekleme hatası {col_name}: {e}")

    # CategoryAssetTypeMapping tablosu oluştur (Faz 16 - Category-AssetType Mapping)
    if 'category_asset_type_mapping' not in inspector.get_table_names():
        logger.info("CategoryAssetTypeMapping tablosu oluşturuluyor...")
        db.create_all()
        logger.info("CategoryAssetTypeMapping tablosu oluşturuldu")

    # AssetSector tablosu için hiyerarşi alanları (Faz 16 - Hierarchical Sectors)
    if 'asset_sector' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('asset_sector')}
        asset_sector_columns = {
            'parent_id': 'INTEGER',
            'level': 'INTEGER DEFAULT 0',
            'code': 'VARCHAR(10)',
            'region': 'VARCHAR(50)',
            'regulatory_class': 'VARCHAR(20)',
            'cyclical_type': 'VARCHAR(20)',
            'beta_range': 'VARCHAR(20)',
        }
        with db.engine.begin() as conn:
            for col_name, col_def in asset_sector_columns.items():
                if col_name not in cols:
                    try:
                        conn.execute(text(f'ALTER TABLE "asset_sector" ADD COLUMN {col_name} {col_def}'))
                        logger.info(f"AssetSector tablosuna sütun eklendi: {col_name}")
                    except Exception as e:
                        logger.warning(f"AssetSector sütunu ekleme hatası {col_name}: {e}")

    # Tag ve EntityTag tabloları oluştur (Faz 16 - Tag System)
    if 'tag' not in inspector.get_table_names():
        logger.info("Tag tablosu oluşturuluyor...")
        db.create_all()
        logger.info("Tag tablosu oluşturuldu")

    if 'entity_tag' not in inspector.get_table_names():
        logger.info("EntityTag tablosu oluşturuluyor...")
        db.create_all()
        logger.info("EntityTag tablosu oluşturuldu")

    # BackupMetadata tablosu oluştur (Faz 17 - Backup Security & Versioning)
    if 'backup_metadata' not in inspector.get_table_names():
        logger.info("BackupMetadata tablosu oluşturuluyor...")
        db.create_all()
        logger.info("BackupMetadata tablosu oluşturuldu")

    # UserPreference tablosu oluştur (Faz 18 - Kullanıcı Finansal Tercihleri)
    if 'user_preference' not in inspector.get_table_names():
        logger.info("UserPreference tablosu oluşturuluyor...")
        db.create_all()
        logger.info("UserPreference tablosu oluşturuldu")
        inspector = inspect(db.engine)

    # UserPreference.theme (Faz 19 - Koyu Tema)
    if 'user_preference' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user_preference')}
        if 'theme' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text(
                    'ALTER TABLE "user_preference" ADD COLUMN theme VARCHAR(10) DEFAULT \'light\''
                ))
            logger.info("UserPreference tablosuna theme sütunu eklendi")
        # Faz 20 - Gizlilik Modu
        if 'privacy_mode' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text(
                    'ALTER TABLE "user_preference" ADD COLUMN privacy_mode BOOLEAN DEFAULT 0'
                ))
            logger.info("UserPreference tablosuna privacy_mode sütunu eklendi")
        # Faz 21 - Bildirim tercihleri
        notification_prefs = {
            'notify_budget': 'BOOLEAN DEFAULT 1',
            'notify_payments': 'BOOLEAN DEFAULT 1',
            'payment_reminder_days': 'INTEGER DEFAULT 3',
        }
        with db.engine.begin() as conn:
            for col_name, col_def in notification_prefs.items():
                if col_name not in cols:
                    conn.execute(text(f'ALTER TABLE "user_preference" ADD COLUMN {col_name} {col_def}'))
                    logger.info(f"UserPreference tablosuna sütun eklendi: {col_name}")

    # Notification tablosu oluştur (Faz 21 - Bildirim Merkezi)
    if 'notification' not in inspector.get_table_names():
        logger.info("Notification tablosu oluşturuluyor...")
        db.create_all()
        logger.info("Notification tablosu oluşturuldu")

    # PlanOccurrence tablosu (Faz 3 - Plan Occurrence Lifecycle)
    # ``create_all`` yalnızca eksik tabloyu oluşturur; tekrar çalıştırılması
    # mevcut finansal kayıtları değiştirmez ve migration'ı idempotent tutar.
    inspector = inspect(db.engine)
    if 'plan_occurrence' not in inspector.get_table_names():
        logger.info("PlanOccurrence tablosu oluşturuluyor...")
        db.create_all()
        logger.info("PlanOccurrence tablosu oluşturuldu")
        inspector = inspect(db.engine)

    # Immutable ledger audit tabloları (Faz 4 - v24.0)
    for table_name, label in (
        ('ledger_adjustment', 'LedgerAdjustment'),
        ('ledger_audit_event', 'LedgerAuditEvent'),
    ):
        if table_name not in inspector.get_table_names():
            logger.info("%s tablosu oluşturuluyor...", label)
            db.create_all()
            logger.info("%s tablosu oluşturuldu", label)
            inspector = inspect(db.engine)

    # Banka mutabakat aggregate’ları (reconciliation workflow).
    # create_all yalnız eksik tabloları oluşturur; mevcut finansal kayıtları
    # değiştirmez ve eski yedeklerle uyumlu kalır.
    inspector = inspect(db.engine)
    for table_name, label in (
        (BankAccount.__tablename__, 'BankAccount'),
        (BankStatementSnapshot.__tablename__, 'BankStatementSnapshot'),
        (UserIban.__tablename__, 'UserIban'),
    ):
        if table_name not in inspector.get_table_names():
            logger.info('%s tablosu oluşturuluyor...', label)
            db.create_all()
            logger.info('%s tablosu oluşturuldu', label)
            inspector = inspect(db.engine)

    if Transaction.__tablename__ in inspector.get_table_names():
        transaction_columns = {
            column['name'] for column in inspector.get_columns(Transaction.__tablename__)
        }
        if 'bank_account_id' not in transaction_columns:
            with db.engine.begin() as conn:
                conn.execute(text(
                    'ALTER TABLE "transaction" ADD COLUMN bank_account_id INTEGER'
                ))
            logger.info('Transaction tablosuna bank_account_id sütunu eklendi')

    # UserIban tablosu ek sütunları (Favori ve FAST Kolay Adres)
    if UserIban.__tablename__ in inspector.get_table_names():
        iban_columns = {
            col['name'] for col in inspector.get_columns(UserIban.__tablename__)
        }
        with db.engine.begin() as conn:
            if 'is_favorite' not in iban_columns:
                conn.execute(text('ALTER TABLE "user_iban" ADD COLUMN is_favorite BOOLEAN DEFAULT 0 NOT NULL'))
                logger.info('UserIban tablosuna is_favorite sütunu eklendi')
            if 'easy_address_type' not in iban_columns:
                conn.execute(text('ALTER TABLE "user_iban" ADD COLUMN easy_address_type VARCHAR(30)'))
                logger.info('UserIban tablosuna easy_address_type sütunu eklendi')
            if 'easy_address' not in iban_columns:
                conn.execute(text('ALTER TABLE "user_iban" ADD COLUMN easy_address VARCHAR(100)'))
                logger.info('UserIban tablosuna easy_address sütunu eklendi')

    # Profil ranking soru/cevap alanları (Ranking soru tipi)
    inspector = inspect(db.engine)
    profile_answer_columns = {column['name'] for column in inspector.get_columns(InvestorProfileAnswer.__tablename__)} if InvestorProfileAnswer.__tablename__ in inspector.get_table_names() else set()
    if InvestorProfileAnswer.__tablename__ in inspector.get_table_names() and 'answer_order' not in profile_answer_columns:
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE "investor_profile_answer" ADD COLUMN answer_order TEXT'))
        logger.info('InvestorProfileAnswer tablosuna answer_order sütunu eklendi')

    profile_question_columns = {column['name'] for column in inspector.get_columns(ProfileQuestion.__tablename__)} if ProfileQuestion.__tablename__ in inspector.get_table_names() else set()
    if ProfileQuestion.__tablename__ in inspector.get_table_names() and 'correct_order' not in profile_question_columns:
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE "profile_question" ADD COLUMN correct_order TEXT'))
        logger.info('ProfileQuestion tablosuna correct_order sütunu eklendi')

    # Index oluşturma (SQLite için CREATE INDEX IF NOT EXISTS)
    from .indexes import _create_indexes_if_not_exist
    _create_indexes_if_not_exist()

    # Fonksiyonun en SONUNA ekle:
    with db.engine.begin() as conn:
        conn.execute(
            text("INSERT OR IGNORE INTO _schema_version (version) VALUES (:v)"),
            {"v": SCHEMA_VERSION}
        )
    logger.debug("Schema versiyonu kaydedildi: %s", SCHEMA_VERSION)
