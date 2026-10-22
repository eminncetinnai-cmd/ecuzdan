"""
Backup Validation Service - Schema ve integrity validation
Phase 17: Backup validation and schema compatibility checking
"""

import json
import logging
from datetime import timezone
from typing import Dict, List, Tuple

from sqlalchemy import inspect

from database.schema_version import SCHEMA_VERSION
from models import db

logger = logging.getLogger(__name__)


class BackupValidationService:
    """Yedek doğrulama servisi"""

    # Mevcut schema versiyonu
    CURRENT_SCHEMA_VERSION = SCHEMA_VERSION

    # Beklenen tablo yapısı
    EXPECTED_TABLES = {
        'account', 'asset', 'asset_sector', 'asset_transaction', 'asset_type',
        'bank_account', 'bank_statement_snapshot',
        'asset_update', 'audit_log', 'backup_metadata', 'category',
        'category_asset_type_mapping', 'entity_tag', 'investor_profile',
        'investor_profile_answer', 'journal_entry', 'ledger_adjustment',
        'ledger_audit_event', 'ledger_line', 'logbook_entry',
        'monitoring_alert_config', 'notification', 'outbox_messages',
        'payment', 'plan_occurrence', 'profile_question', 'quiz_attempt',
        'quiz_question', 'recurring_plan', 'strategy_settings', 'tag',
        'tenant', 'tenant_invite', 'transaction', 'user',
        'user_achievement', 'user_iban', 'user_preference', 'user_progress',
    }
    # These were introduced after earlier backups. Their absence is valid;
    # when present, their rows and columns are validated normally.
    OPTIONAL_TABLES = {'bank_account', 'bank_statement_snapshot', 'user_iban'}

    def __init__(self):

        self.inspector = inspect(db.engine)

    def _normalize_table_name(self, table_name: str) -> str:
        """Normalize backup table names to singular canonical names."""
        if table_name in self.EXPECTED_TABLES:
            return table_name
        if table_name.endswith('batches'):
            candidate = table_name[:-2]
            if candidate in self.EXPECTED_TABLES:
                return candidate
        if table_name.endswith('ies'):
            candidate = table_name[:-3] + 'y'
            if candidate in self.EXPECTED_TABLES:
                return candidate
        if table_name.endswith('s'):
            candidate = table_name[:-1]
            if candidate in self.EXPECTED_TABLES:
                return candidate
        return table_name

    def _get_table_data(self, backup_data: Dict, table_name: str):
        """Return table data for singular or plural table keys."""
        if table_name in backup_data:
            return backup_data[table_name]
        plural_key = (
            f"{table_name[:-1]}ies" if table_name.endswith('y')
            else (f"{table_name}es" if table_name.endswith('batch') else f"{table_name}s")
        )
        if plural_key in backup_data:
            return backup_data[plural_key]
        norm = self._normalize_table_name(table_name)
        for key, val in backup_data.items():
            if key not in {'schema_version', 'metadata'} and self._normalize_table_name(key) == norm and isinstance(val, list):
                return val
        return []

    def validate_schema(self, backup_data: Dict) -> Tuple[bool, List[str]]:
        """
        Schema uyumluluğunu kontrol et

        Args:
            backup_data: Yedek verisi

        Returns:
            (geçerli mi, hata mesajları listesi)
        """
        errors = []

        # Schema version kontrolü
        schema_version = backup_data.get('schema_version')
        if schema_version is not None and schema_version != self.CURRENT_SCHEMA_VERSION:
            errors.append(f"Schema versiyon uyumsuz: Beklenen {self.CURRENT_SCHEMA_VERSION}, bulunan {schema_version}")

        # Tablo kontrolü
        raw_tables = {name for name in backup_data.keys() if name not in {'schema_version', 'metadata'}}
        normalized_tables = {self._normalize_table_name(name) for name in raw_tables}
        extra_tables = {name for name in raw_tables if self._normalize_table_name(name) not in self.EXPECTED_TABLES}

        if schema_version is not None:
            missing_tables = self.EXPECTED_TABLES - normalized_tables - self.OPTIONAL_TABLES

            if missing_tables:
                errors.append(f"Eksik tablolar: {', '.join(sorted(missing_tables))}")

        if extra_tables:
            errors.append(f"Fazla tablolar: {', '.join(sorted(extra_tables))}")

        # Her tablo için yapı kontrolü
        for table_name in self.EXPECTED_TABLES:
            table_data = self._get_table_data(backup_data, table_name)
            if table_data:
                table_errors = self._validate_table_structure(table_name, table_data)
                errors.extend(table_errors)

        return len(errors) == 0, errors

    def _validate_table_structure(self, table_name: str, table_data: List[Dict]) -> List[str]:
        """
        Tablo yapısını doğrula

        Args:
            table_name: Tablo adı
            table_data: Tablo verisi

        Returns:
            Hata mesajları listesi
        """
        errors = []

        if not table_data:
            return errors  # Boş tablo hata değil

        # Mevcut tablo sütunlarını al
        if table_name not in self.inspector.get_table_names():
            errors.append(f"Tablo veritabanında mevcut değil: {table_name}")
            return errors

        current_columns = {col['name'] for col in self.inspector.get_columns(table_name)}

        # İlk kayıttan sütunları al
        backup_columns = set(table_data[0].keys()) if table_data else set()

        # Zorunlu sütunlar
        required_columns = {'id'}

        missing_columns = required_columns - backup_columns
        if missing_columns:
            errors.append(f"{table_name} tablosunda eksik zorunlu sütunlar: {', '.join(missing_columns)}")

        # Uyumsuz sütunlar (mevcut DB'de olmayan)
        incompatible_columns = backup_columns - current_columns
        if incompatible_columns:
            errors.append(f"{table_name} tablosunda uyumsuz sütunlar: {', '.join(incompatible_columns)}")

        return errors

    def validate_integrity(self, backup_data: Dict, checksum: str) -> bool:
        """
        Veri bütünlüğünü kontrol et (checksum doğrulama)

        Args:
            backup_data: Yedek verisi
            checksum: Beklenen checksum

        Returns:
            True eşleşirse, False eşleşmezse
        """
        from infrastructure.backup.encryption import BackupEncryptionService

        encryption_service = BackupEncryptionService()
        json_str = json.dumps(backup_data, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')

        actual_checksum = encryption_service.generate_checksum(json_bytes)

        return actual_checksum == checksum

    def validate_foreign_keys(self, backup_data: Dict) -> List[str]:
        """
        Foreign key ilişkilerini doğrula

        Args:
            backup_data: Yedek verisi

        Returns:
            Hata mesajları listesi
        """
        errors = []

        # ORM foreign key metadata'sını kullanarak tüm tablo ilişkilerini doğrula.
        # Böylece yeni eklenen ledger, plan, notification ve outbox tabloları
        # manuel bir kontrol listesi güncellenmeden kapsamda kalır.
        for table_name in self.EXPECTED_TABLES:
            table = db.metadata.tables.get(table_name)
            if table is None:
                continue
            rows = self._get_table_data(backup_data, table_name)
            if not rows:
                continue

            for row in rows:
                row_id = row.get("id")
                for foreign_key in table.foreign_keys:
                    local_column = foreign_key.parent.name
                    local_value = row.get(local_column)
                    if local_value is None:
                        continue

                    target_table = foreign_key.column.table.name
                    target_column = foreign_key.column.name
                    # schema_version içermeyen minimal/partial importlarda
                    # payload’da bulunmayan target tablo mevcut DB’den çözülebilir.
                    # Tablo açıkça payload’a dahil edilmişse FK kontrolü sürer.
                    target_present = any(
                        self._normalize_table_name(name) == target_table
                        for name in backup_data
                        if name not in {'schema_version', 'metadata'}
                    )
                    if not target_present:
                        continue
                    target_rows = self._get_table_data(backup_data, target_table)
                    target_values = {target.get(target_column) for target in target_rows}
                    if local_value not in target_values:
                        errors.append(
                            f"{table_name} {row_id} için geçersiz "
                            f"{local_column}={local_value}; hedef "
                            f"{target_table}.{target_column} bulunamadı"
                        )

        # Transaction.category gerçek bir SQL foreign key değildir; ancak
        # finansal kayıtların kategori sözlüğüyle tutarlı olması gerekir.
        categories = self._get_table_data(backup_data, 'category')
        category_names = {category.get('name') for category in categories}
        for transaction in self._get_table_data(backup_data, 'transaction'):
            category = transaction.get('category')
            if category and category_names and category not in category_names:
                errors.append(
                    f"Transaction {transaction.get('id')} için geçersiz "
                    f"category: {category}"
                )

        return errors

    def validate_backup_compatibility(self, backup_data: Dict) -> Tuple[bool, str]:
        """
        Yedeğin mevcut sistemle uyumluluğunu kontrol et

        Args:
            backup_data: Yedek verisi

        Returns:
            (uyumlu mu, mesaj)
        """
        # Schema kontrolü
        schema_valid, schema_errors = self.validate_schema(backup_data)
        if not schema_valid:
            return False, f"Schema uyumsuz: {', '.join(schema_errors)}"

        # Foreign key kontrolü
        fk_errors = self.validate_foreign_keys(backup_data)
        if fk_errors:
            return False, f"Foreign key hataları: {', '.join(fk_errors[:5])}"  # İlk 5 hatayı göster

        return True, "Yedek uyumlu"

    def get_current_schema_info(self) -> Dict:
        """
        Mevcut schema bilgisini döndür

        Returns:
            Schema bilgisi
        """
        tables = self.inspector.get_table_names()

        schema_info = {
            'schema_version': self.CURRENT_SCHEMA_VERSION,
            'tables': {},
            'total_tables': len(tables)
        }

        for table in tables:
            columns = self.inspector.get_columns(table)
            schema_info['tables'][table] = {
                'column_count': len(columns),
                'columns': [col['name'] for col in columns]
            }

        return schema_info

    def generate_backup_metadata(self, backup_data: Dict, user_id: int,
                                tenant_id: str = None, encrypted: bool = False,
                                compression: str = None, backup_type: str = 'full') -> Dict:
        """
        Yedek meta verisi oluştur

        Args:
            backup_data: Yedek verisi
            user_id: Kullanıcı ID
            tenant_id: Tenant ID
            encrypted: Şifreli mi
            compression: Sıkıştırma algoritması
            backup_type: Yedek tipi

        Returns:
            Meta veri dict
        """
        from datetime import datetime

        from infrastructure.backup.encryption import BackupEncryptionService

        encryption_service = BackupEncryptionService()
        json_str = json.dumps(backup_data, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')

        record_counts = {}
        for table_name, table_data in backup_data.items():
            if isinstance(table_data, list):
                record_counts[table_name] = len(table_data)

        metadata = {
            'schema_version': self.CURRENT_SCHEMA_VERSION,
            'backup_timestamp': datetime.now(timezone.utc).isoformat(),
            'checksum': encryption_service.generate_checksum(json_bytes),
            'encrypted': encrypted,
            'compression': compression,
            'tenant_id': tenant_id,
            'user_id': user_id,
            'size_bytes': len(json_bytes),
            'record_counts': record_counts,
            'backup_type': backup_type,
            'status': 'completed'
        }

        return metadata
