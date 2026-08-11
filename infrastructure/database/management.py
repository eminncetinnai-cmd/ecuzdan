import json
import logging
from datetime import datetime

from models import (
    Asset,
    AssetSector,
    AssetTransaction,
    AssetType,
    AssetUpdate,
    BackupMetadata,
    Category,
    CategoryAssetTypeMapping,
    EntityTag,
    InvestorProfile,
    InvestorProfileAnswer,
    LogbookEntry,
    Payment,
    ProfileQuestion,
    RecurringPlan,
    StrategySettings,
    Tag,
    Tenant,
    TenantInvite,
    Transaction,
    User,
    db,
)

logger = logging.getLogger(__name__)

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
        "assets": [],
        "recurring_plans": [],
        "payments": [],
        "transactions": [],
        "asset_updates": [],
        "asset_transactions": [],
        "tags": [],
        "entity_tags": [],
        "category_asset_type_mappings": [],
        "investor_profiles": [],
        "investor_profile_answers": [],
        "profile_questions": [],
        "logbook_entries": [],
        "tenant_invites": [],
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
        ("assets", Asset),
        ("recurring_plans", RecurringPlan),
        ("payments", Payment),
        ("transactions", Transaction),
        ("asset_updates", AssetUpdate),
        ("asset_transactions", AssetTransaction),
        ("tags", Tag),
        ("entity_tags", EntityTag),
        ("category_asset_type_mappings", CategoryAssetTypeMapping),
        ("investor_profiles", InvestorProfile),
        ("investor_profile_answers", InvestorProfileAnswer),
        ("profile_questions", ProfileQuestion),
        ("logbook_entries", LogbookEntry),
        ("tenant_invites", TenantInvite),
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

def import_database_from_json(json_content, password: str = None):
    """JSON içeriğini veritabanına aktarır (mevcut verileri temizlemez, çakışmaları id bazlı yönetir).

    Args:
        json_content: JSON içeriği
        password: Şifre çözme şifresi (şifreli yedek için gerekli)

    Returns:
        (success, message)
    """
    from infrastructure.backup.encryption import BackupEncryptionService
    from infrastructure.backup.validation import BackupValidationService

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
            return False, f"Schema uyumsuz: {compatibility_message}"

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
            ("assets", Asset),
            ("recurring_plans", RecurringPlan),
            ("payments", Payment),
            ("transactions", Transaction),
            ("asset_updates", AssetUpdate),
            ("asset_transactions", AssetTransaction),
            ("entity_tags", EntityTag),
            ("investor_profiles", InvestorProfile),
            ("investor_profile_answers", InvestorProfileAnswer),
            ("logbook_entries", LogbookEntry),
            ("tenant_invites", TenantInvite),
            ("backup_metadata", BackupMetadata),
        ]

        # Datetime alanları listesi
        datetime_columns = {
            'User': ['password_changed_at'],
            'StrategySettings': ['created_at', 'updated_at'],
            'AssetUpdate': ['updated_at'],
            'Tenant': ['created_at'],
            'BackupMetadata': ['backup_timestamp', 'created_at'],
            'InvestorProfile': ['created_at'],
            'LogbookEntry': ['created_at'],
            'TenantInvite': ['created_at', 'expires_at'],
            'Payment': ['due_date', 'paid_date'],
            'Transaction': ['transaction_date'],
            'Asset': ['purchase_date'],
            'RecurringPlan': ['start_date', 'end_date'],
        }

        total_imported = 0
        total_updated = 0
        total_skipped = 0

        for key, model_class in models_map:
            if key not in data:
                # Backward compatibility: allow singular keys from older backups.
                singular_key = key[:-1] if key.endswith('s') else key
                if singular_key in data:
                    data[key] = data[singular_key]
                else:
                    logger.warning(f"Key '{key}' not found in JSON data")
                    continue

            model_name = model_class.__name__
            date_cols = datetime_columns.get(model_name, [])

            for item in data[key]:
                try:
                    with db.session.no_autoflush:
                        existing = db.session.get(model_class, item['id'])

                    if existing:
                        # Güncelle
                        for k, v in item.items():
                            if k != 'id' and v is not None:
                                if k in date_cols and isinstance(v, str):
                                    v = datetime.fromisoformat(v)
                                setattr(existing, k, v)
                        total_updated += 1
                    else:
                        # Yeni ekle
                        processed_item = item.copy()
                        for date_col in date_cols:
                            if date_col in processed_item and processed_item[date_col]:
                                processed_item[date_col] = datetime.fromisoformat(processed_item[date_col])

                        new_obj = model_class(**processed_item)
                        db.session.add(new_obj)
                        total_imported += 1
                except Exception as e:
                    logger.error(f"Error importing {key} item {item.get('id')}: {e}")
                    db.session.rollback()
                    total_skipped += 1
                    continue

        db.session.commit()
        logger.info(
            f"Database imported successfully: {total_imported} new, "
            f"{total_updated} updated, {total_skipped} skipped"
        )
        return True, (
            f"Veriler başarıyla içe aktarıldı. "
            f"{total_imported} yeni, {total_updated} güncellendi"
            + (f", {total_skipped} atlandı (çakışma)" if total_skipped else "") + "."
        )
    except json.JSONDecodeError as e:
        db.session.rollback()
        logger.error(f"JSON decode error: {e}")
        return False, f"JSON format hatası: {str(e)}"
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Decryption error: {e}")
        return False, f"Şifre çözme hatası: {str(e)}"
    except Exception as e:
        db.session.rollback()
        logger.error(f"Import error: {e}")
        return False, f"İçe aktarma hatası: {str(e)}"
