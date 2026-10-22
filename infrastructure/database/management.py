import json
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import Date, DateTime, Numeric

from infrastructure.database.models.outbox_model import OutboxMessageModel
from models import (
    Account,
    Asset,
    AssetSector,
    AssetTransaction,
    AssetType,
    AssetUpdate,
    AuditLog,
    BackupMetadata,
    BankAccount,
    BankStatementSnapshot,
    Category,
    CategoryAssetTypeMapping,
    EntityTag,
    InvestorProfile,
    InvestorProfileAnswer,
    JournalEntry,
    LedgerAdjustment,
    LedgerAuditEvent,
    LedgerLine,
    LogbookEntry,
    MonitoringAlertConfig,
    Notification,
    Payment,
    PlanOccurrence,
    ProfileQuestion,
    QuizAttempt,
    QuizQuestion,
    RecurringPlan,
    StrategySettings,
    Tag,
    Tenant,
    TenantInvite,
    Transaction,
    User,
    UserAchievement,
    UserIban,
    UserPreference,
    UserProgress,
    db,
)

logger = logging.getLogger(__name__)


class ImportRecordError(Exception):
    """Raised when a backup record cannot be imported atomically."""


class BackupRestoreValidationError(ValueError):
    """Raised when a backup cannot be safely mapped to the current schema."""


def _coerce_backup_value(value, column):
    """Convert JSON scalar values to the SQLAlchemy column's Python type."""
    if value is None:
        return None

    column_type = column.type
    if isinstance(column_type, DateTime):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
        raise BackupRestoreValidationError(
            f"{column.name} için DateTime değeri geçersiz: {value!r}"
        )

    if isinstance(column_type, Date):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value[:10])
            except ValueError as exc:
                raise BackupRestoreValidationError(
                    f"{column.name} için Date değeri geçersiz: {value!r}"
                ) from exc
        raise BackupRestoreValidationError(
            f"{column.name} için Date değeri geçersiz: {value!r}"
        )

    if isinstance(column_type, Numeric):
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, AttributeError) as exc:
            raise BackupRestoreValidationError(
                f"{column.name} için Numeric değeri geçersiz: {value!r}"
            ) from exc

    return value


def _prepare_backup_record(model_class, item):
    """Validate record keys and coerce values before model construction."""
    if not isinstance(item, dict):
        raise BackupRestoreValidationError(
            f"{model_class.__tablename__} kaydı nesne olmalı."
        )

    columns = {column.name: column for column in model_class.__table__.columns}
    unknown_columns = sorted(set(item) - set(columns))
    if unknown_columns:
        raise BackupRestoreValidationError(
            f"{model_class.__tablename__} kaydında bilinmeyen alan(lar): "
            f"{', '.join(unknown_columns)}"
        )

    return {
        key: _coerce_backup_value(value, columns[key])
        for key, value in item.items()
    }


def export_database_to_json(encrypt: bool = False, password: str = None):
    """Tüm veritabanı tablolarını JSON formatında dışa aktarır.

    Args:
        encrypt: Şifreleme yapılacak mı
        password: Şifreleme şifresi (encrypt=True ise gerekli)

    Returns:
        JSON string veya şifrelenmiş veri
    """
    from infrastructure.backup.encryption import BackupEncryptionService
    from infrastructure.backup.validation import BackupValidationService

    encryption_service = BackupEncryptionService()
    validation_service = BackupValidationService()

    data = {
        "schema_version": validation_service.CURRENT_SCHEMA_VERSION,
        "tenants": [],
        "users": [],
        "categories": [],
        "asset_types": [],
        "asset_sectors": [],
        "strategy_settings": [],
        "accounts": [],
        "bank_accounts": [],
        "assets": [],
        "recurring_plans": [],
        "plan_occurrences": [],
        "payments": [],
        "transactions": [],
        "bank_statement_snapshots": [],
        "asset_updates": [],
        "asset_transactions": [],
        "journal_entries": [],
        "ledger_lines": [],
        "ledger_adjustments": [],
        "ledger_audit_events": [],
        "tags": [],
        "entity_tags": [],
        "category_asset_type_mappings": [],
        "investor_profiles": [],
        "investor_profile_answers": [],
        "profile_questions": [],
        "user_progress": [],
        "quiz_attempts": [],
        "user_achievements": [],
        "quiz_questions": [],
        "user_preferences": [],
        "notifications": [],
        "logbook_entries": [],
        "tenant_invites": [],
        "audit_logs": [],
        "monitoring_alert_configs": [],
        "outbox_messages": [],
        "backup_metadata": [],
    }

    # Helper function to serialize SQLAlchemy objects
    def serialize_model(model_obj):
        from decimal import Decimal
        d = {}
        for column in model_obj.__table__.columns:
            val = getattr(model_obj, column.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            elif isinstance(val, Decimal):
                # Decimal → str olarak saklanır; JSON serializasyon hatası önlendi.
                # Onceki hata: 'Object of type Decimal is not JSON serializable'
                val = str(val)
            d[column.name] = val
        return d

    # Tüm tabloları serialize et
    all_models = [
        ("tenants", Tenant),
        ("users", User),
        ("categories", Category),
        ("asset_types", AssetType),
        ("asset_sectors", AssetSector),
        ("strategy_settings", StrategySettings),
        ("accounts", Account),
        ("bank_accounts", BankAccount),
        ("assets", Asset),
        ("recurring_plans", RecurringPlan),
        ("plan_occurrences", PlanOccurrence),
        ("payments", Payment),
        ("transactions", Transaction),
        ("bank_statement_snapshots", BankStatementSnapshot),
        ("asset_updates", AssetUpdate),
        ("asset_transactions", AssetTransaction),
        ("journal_entries", JournalEntry),
        ("ledger_lines", LedgerLine),
        ("ledger_adjustments", LedgerAdjustment),
        ("ledger_audit_events", LedgerAuditEvent),
        ("tags", Tag),
        ("entity_tags", EntityTag),
        ("category_asset_type_mappings", CategoryAssetTypeMapping),
        ("investor_profiles", InvestorProfile),
        ("investor_profile_answers", InvestorProfileAnswer),
        ("profile_questions", ProfileQuestion),
        ("user_progress", UserProgress),
        ("quiz_attempts", QuizAttempt),
        ("user_achievements", UserAchievement),
        ("quiz_questions", QuizQuestion),
        ("user_preferences", UserPreference),
        ("notifications", Notification),
        ("logbook_entries", LogbookEntry),
        ("user_ibans", UserIban),
        ("tenant_invites", TenantInvite),
        ("audit_logs", AuditLog),
        ("monitoring_alert_configs", MonitoringAlertConfig),
        ("outbox_messages", OutboxMessageModel),
        ("backup_metadata", BackupMetadata),
    ]

    try:
        for key, model_class in all_models:
            data[key] = [serialize_model(obj) for obj in model_class.query.all()]

        logger.info(
            f"Database exported successfully: "
            f"{len(data['users'])} users, {len(data['transactions'])} transactions"
        )

        if encrypt:
            if not password:
                raise ValueError("Şifreleme için şifre gerekli")
            encrypted_data, checksum = encryption_service.encrypt_json(data, password)
            # Şifreli veriyi base64 olarak döndür (JSON içinde taşınabilir)
            import base64
            result = {
                'encrypted': True,
                'checksum': checksum,
                'data': base64.b64encode(encrypted_data).decode('utf-8'),
                'schema_version': validation_service.CURRENT_SCHEMA_VERSION
            }
            return json.dumps(result, indent=4, ensure_ascii=False, default=str)
        else:
            return json.dumps(data, indent=4, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Database export error: {e}")
        raise

def import_database_from_json(
    json_content,
    password: str = None,
    replace_existing: bool = False,
):
    """JSON içeriğini transaction içinde içe aktarır.

    ``replace_existing=False`` varsayılanı geriye uyumlu merge davranışıdır.
    ``replace_existing=True`` ise tüm uygulama tablolarını FK bağımlılıklarına
    göre temizler ve yedeği aynı transaction içinde yeniden kurar.

    Args:
        json_content: JSON içeriği
        password: Şifre çözme şifresi (şifreli yedek için gerekli)

    Returns:
        (success, message)
    """
    from infrastructure.backup.encryption import BackupEncryptionService
    from infrastructure.backup.validation import BackupValidationService
    from infrastructure.database.migration import migration_service

    encryption_service = BackupEncryptionService()
    validation_service = BackupValidationService()

    try:
        # JSON parse et
        parsed_data = json.loads(json_content)

        # Şifreli mi kontrol et
        if parsed_data.get('encrypted', False):
            if not password:
                return False, "Şifreli yedek için şifre gerekli"

            import base64
            encrypted_data = base64.b64decode(parsed_data['data'])
            expected_checksum = parsed_data.get('checksum')

            data = encryption_service.decrypt_json(encrypted_data, password, expected_checksum)
        else:
            data = parsed_data

        # Schema uyumluluğunu kontrol et
        is_compatible, compatibility_message = validation_service.validate_backup_compatibility(data)
        if not is_compatible:
            # Migration stratejisi kontrol et
            logger.info(f"Schema incompatible, attempting migration: {compatibility_message}")
            migration_success, migrated_data, migration_message = migration_service.migrate_backup(data)

            if migration_success:
                data = migrated_data
                logger.info(f"Migration successful: {migration_message}")

                # Migration sonrası tekrar validate et
                is_compatible, compatibility_message = validation_service.validate_backup_compatibility(data)
                if not is_compatible:
                    return False, f"Migration sonrası schema hala uyumsuz: {compatibility_message}"
            else:
                return False, f"Schema uyumsuz ve migration başarısız: {migration_message}"

        # Import sıralaması (Foreign Key bağımlılıkları nedeniyle)
        models_map = [
            ("tenants", Tenant),
            ("tags", Tag),
            ("profile_questions", ProfileQuestion),
            ("users", User),
            ("categories", Category),
            ("asset_types", AssetType),
            ("asset_sectors", AssetSector),
            ("category_asset_type_mappings", CategoryAssetTypeMapping),
            ("strategy_settings", StrategySettings),
            ("accounts", Account),
            ("bank_accounts", BankAccount),
            ("assets", Asset),
            ("recurring_plans", RecurringPlan),
            ("transactions", Transaction),
            ("bank_statement_snapshots", BankStatementSnapshot),
            ("plan_occurrences", PlanOccurrence),
            ("payments", Payment),
            ("asset_updates", AssetUpdate),
            ("asset_transactions", AssetTransaction),
            ("journal_entries", JournalEntry),
            ("ledger_lines", LedgerLine),
            ("ledger_adjustments", LedgerAdjustment),
            ("ledger_audit_events", LedgerAuditEvent),
            ("entity_tags", EntityTag),
            ("investor_profiles", InvestorProfile),
            ("investor_profile_answers", InvestorProfileAnswer),
            ("user_progress", UserProgress),
            ("quiz_attempts", QuizAttempt),
            ("user_achievements", UserAchievement),
            ("quiz_questions", QuizQuestion),
            ("user_preferences", UserPreference),
            ("notifications", Notification),
            ("logbook_entries", LogbookEntry),
            ("user_ibans", UserIban),
            ("tenant_invites", TenantInvite),
            ("audit_logs", AuditLog),
            ("monitoring_alert_configs", MonitoringAlertConfig),
            ("outbox_messages", OutboxMessageModel),
            ("backup_metadata", BackupMetadata),
        ]

        if replace_existing:
            # Reverse dependency order: child rows are deleted before parents.
            for _, model_class in reversed(models_map):
                db.session.query(model_class).delete(synchronize_session=False)
            db.session.flush()
            db.session.expunge_all()

        total_imported = 0
        total_updated = 0
        table_stats: dict[str, dict[str, int]] = {}

        def _find_existing_import_record(model_class, item):
            """Find an existing row by stable ID, then Category natural key."""
            item_id = item.get("id")
            if item_id is not None:
                existing = db.session.get(model_class, item_id)
                if existing is not None:
                    return existing
            if model_class.__name__ != "Category":
                return None
            name = item.get("name")
            category_type = item.get("type")
            if not name or not category_type:
                return None
            query = model_class.query.filter_by(name=name, type=category_type)
            tenant_id = item.get("tenant_id")
            if tenant_id is None:
                query = query.filter(model_class.tenant_id.is_(None))
            else:
                query = query.filter_by(tenant_id=tenant_id)
            code = item.get("code")
            if code is not None:
                query = query.filter_by(code=code)
            return query.first()

        for key, model_class in models_map:
            if key not in data:
                # Backward compatibility: allow singular keys from older backups.
                singular_key = key[:-1] if key.endswith('s') else key
                if singular_key in data:
                    data[key] = data[singular_key]
                else:
                    logger.debug("Optional backup section '%s' is absent; keeping current rows", key)
                    continue

            tbl_new = 0
            tbl_upd = 0
            for item in data[key]:
                try:
                    processed_item = _prepare_backup_record(model_class, item)
                    with db.session.no_autoflush:
                        existing = _find_existing_import_record(model_class, processed_item)

                    if existing:
                        # Merge mode preserves the established non-null update semantics.
                        for key_name, value in processed_item.items():
                            if key_name != 'id' and value is not None:
                                setattr(existing, key_name, value)
                        tbl_upd += 1
                        total_updated += 1
                    else:
                        db.session.add(model_class(**processed_item))
                        tbl_new += 1
                        total_imported += 1

                except Exception as e:
                    logger.exception(f"Error importing {key} item {item.get('id')}: {e}")
                    raise ImportRecordError(
                        f"{key} kaydı (id={item.get('id')}) içe aktarılamadı: {e}"
                    ) from e

            if tbl_new or tbl_upd:
                table_stats[key] = {"new": tbl_new, "updated": tbl_upd}

            # Parent tables are materialized before the next dependency tier;
            # the outer transaction still commits only after every table passes.
            db.session.flush()

        db.session.flush()

        db.session.commit()

        # Build human-readable per-table summary (only non-zero tables)
        detail_parts = [
            f"{k}: +{v['new']} / ~{v['updated']}"
            for k, v in table_stats.items()
            if v["new"] or v["updated"]
        ]
        detail = " | ".join(detail_parts) if detail_parts else "değişiklik yok"
        logger.info(
            "Database imported successfully: %d new, %d updated. [%s]",
            total_imported, total_updated, detail,
        )
        msg = (
            f"İçe aktarma tamamlandı: {total_imported} yeni, {total_updated} güncellendi. "
            f"({detail})"
        )
        return True, msg

    except json.JSONDecodeError as e:

        db.session.rollback()
        logger.error(f"JSON decode error: {e}")
        return False, f"JSON format hatası: {str(e)}"
    except ImportRecordError as e:
        db.session.rollback()
        logger.error(f"Import record error: {e}")
        return False, f"İçe aktarma atomik olarak geri alındı: {str(e)}"

    except BackupRestoreValidationError as e:
        db.session.rollback()
        logger.error(f"Backup record validation error: {e}")
        return False, f"Yedek kayıt doğrulama hatası: {str(e)}"
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Decryption error: {e}")
        return False, f"Şifre çözme hatası: {str(e)}"
    except Exception as e:

        db.session.rollback()
        logger.error(f"Import error: {e}")
        return False, f"İçe aktarma atomik olarak geri alındı: {str(e)}"
