"""
Database Migration Service
Schema değişikliklerini yönetir ve yedek uyumluluğunu garanti eder.
"""

import logging
from typing import Dict, List, Optional, Tuple

from database.schema_version import SCHEMA_VERSION
from infrastructure.backup.validation import BackupValidationService

logger = logging.getLogger(__name__)


class MigrationStrategy:
    """
    Migration stratejileri için temel sınıf.
    Her schema değişikliği için özel strateji tanımlanmalıdır.
    """

    def __init__(self, from_version: str, to_version: str):
        self.from_version = from_version
        self.to_version = to_version

    def can_migrate_backup(self, backup_data: Dict) -> Tuple[bool, str]:
        """
        Bu stratejinin verilen yedeği migrate edip edemeyeceğini kontrol et.
        """
        backup_version = backup_data.get('schema_version')
        if backup_version != self.from_version:
            return False, f"Expected version {self.from_version}, got {backup_version}"
        return True, "Can migrate"

    def migrate_backup_data(self, backup_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Yedek verisini yeni schema'ya migrate et.
        
        Returns:
            (success, migrated_data, message)
        """
        raise NotImplementedError("Subclasses must implement migrate_backup_data")


class AddColumnMigration(MigrationStrategy):
    """
    Yeni sütun ekleme migration'ı - genellikle geriye uyumludur.
    """

    def __init__(self, from_version: str, to_version: str, table_column_map: Dict[str, List[str]]):
        super().__init__(from_version, to_version)
        self.table_column_map = table_column_map

    def migrate_backup_data(self, backup_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Yeni sütunları varsayılan değerlerle ekle.
        """
        try:
            for table_name, new_columns in self.table_column_map.items():
                if table_name in backup_data:
                    for row in backup_data[table_name]:
                        for column in new_columns:
                            if column not in row:
                                row[column] = None  # Varsayılan değer

            backup_data['schema_version'] = self.to_version
            return True, backup_data, f"Successfully migrated from {self.from_version} to {self.to_version}"

        except Exception as e:
            return False, backup_data, f"Migration failed: {str(e)}"


class RemoveColumnMigration(MigrationStrategy):
    """
    Sütun kaldırma migration'ı - veri kaybı riski içerir.
    """

    def __init__(self, from_version: str, to_version: str, table_column_map: Dict[str, List[str]]):
        super().__init__(from_version, to_version)
        self.table_column_map = table_column_map

    def migrate_backup_data(self, backup_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Belirtilen sütunları yedekten kaldır.
        """
        try:
            removed_columns = []

            for table_name, columns_to_remove in self.table_column_map.items():
                if table_name in backup_data:
                    for row in backup_data[table_name]:
                        for column in columns_to_remove:
                            if column in row:
                                removed_columns.append(f"{table_name}.{column}")
                                del row[column]

            backup_data['schema_version'] = self.to_version

            message = f"Removed {len(removed_columns)} columns: {', '.join(removed_columns[:5])}"
            if len(removed_columns) > 5:
                message += f" and {len(removed_columns) - 5} more"

            return True, backup_data, message

        except Exception as e:
            return False, backup_data, f"Migration failed: {str(e)}"


class RenameColumnMigration(MigrationStrategy):
    """
    Sütun yeniden adlandırma migration'ı.
    """

    def __init__(self, from_version: str, to_version: str, table_column_map: Dict[str, Dict[str, str]]):
        super().__init__(from_version, to_version)
        self.table_column_map = table_column_map  # {table: {old_name: new_name}}

    def migrate_backup_data(self, backup_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Sütunları yeniden adlandır.
        """
        try:
            renamed_columns = []

            for table_name, column_mapping in self.table_column_map.items():
                if table_name in backup_data:
                    for row in backup_data[table_name]:
                        for old_name, new_name in column_mapping.items():
                            if old_name in row:
                                row[new_name] = row[old_name]
                                del row[old_name]
                                renamed_columns.append(f"{table_name}.{old_name}->{new_name}")

            backup_data['schema_version'] = self.to_version
            return True, backup_data, f"Renamed {len(renamed_columns)} columns"

        except Exception as e:
            return False, backup_data, f"Migration failed: {str(e)}"


class MigrationService:
    """
    Migration işlemlerini yöneten servis.
    """

    def __init__(self):
        self.migration_strategies: List[MigrationStrategy] = []
        self.validation_service = BackupValidationService()

    def register_migration(self, strategy: MigrationStrategy):
        """
        Yeni bir migration stratejisi kaydet.
        """
        self.migration_strategies.append(strategy)
        logger.info(f"Registered migration: {strategy.from_version} -> {strategy.to_version}")

    def get_migration_for_backup(self, backup_data: Dict) -> Optional[MigrationStrategy]:
        """
        Verilen yedek için uygun migration stratejisini bul.
        """
        for strategy in self.migration_strategies:
            can_migrate, message = strategy.can_migrate_backup(backup_data)
            if can_migrate:
                return strategy

        return None

    def migrate_backup(self, backup_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Yedeği mevcut schema'ya migrate et.
        """
        backup_version = backup_data.get('schema_version')

        if backup_version == SCHEMA_VERSION:
            return True, backup_data, "Backup already at current schema version"

        migration = self.get_migration_for_backup(backup_data)

        if not migration:
            return False, backup_data, f"No migration strategy found for version {backup_version}"

        logger.info(f"Migrating backup from {migration.from_version} to {migration.to_version}")

        return migration.migrate_backup_data(backup_data)

    def check_migration_requirements(self) -> Dict:
        """
        Mevcut migration gereksinimlerini kontrol et.
        """
        return {
            "current_schema_version": SCHEMA_VERSION,
            "available_migrations": [
                {
                    "from": strategy.from_version,
                    "to": strategy.to_version,
                    "type": strategy.__class__.__name__
                }
                for strategy in self.migration_strategies
            ],
            "backup_compatibility": "compatible" if not self.migration_strategies else "migration_required"
        }


# Global migration service instance
migration_service = MigrationService()

# Örnek migration kayıtları (gerçek projede bunlar veritabanında veya config dosyasında tutulmalı)
# migration_service.register_migration(
#     AddColumnMigration("v25.0", "v25.1", {
#         "users": ["email_verified", "auth_provider"],
#         "transactions": ["source_type"]
#     })
# )
