"""
Schema Compatibility Testing - Yedek uyumluluğu otomatik testleri
Bu testler, her schema değişikliğinde yedek uyumluluğunu garanti eder.
"""

import json

import pytest

from database.schema_version import SCHEMA_VERSION
from infrastructure.backup.validation import BackupValidationService
from infrastructure.database.management import export_database_to_json, import_database_from_json


@pytest.mark.integration
def test_current_schema_exports_and_imports_successfully(app):
    """
    Mevcut schema'nın export/import round-trip başarılı olmalı.
    Bu test, her schema değişikliğinde çalıştırılmalıdır.
    """
    with app.app_context():
        # Export
        exported_json = export_database_to_json(encrypt=False)
        exported_data = json.loads(exported_json)

        # Validate schema version
        assert exported_data.get('schema_version') == SCHEMA_VERSION, \
            f"Schema version mismatch: expected {SCHEMA_VERSION}, got {exported_data.get('schema_version')}"

        # Validate compatibility
        validation_service = BackupValidationService()
        is_compatible, message = validation_service.validate_backup_compatibility(exported_data)
        assert is_compatible, f"Backup compatibility check failed: {message}"

        # Import (merge mode)
        success, import_message = import_database_from_json(exported_json, replace_existing=False)
        assert success, f"Import failed: {import_message}"


@pytest.mark.integration
def test_current_schema_supports_replace_mode(app):
    """
    Replace mode da çalışmalı - bu tam temizlik + yeniden oluşturma anlamına gelir.
    """
    with app.app_context():
        exported_json = export_database_to_json(encrypt=False)

        # Replace mode test
        success, message = import_database_from_json(exported_json, replace_existing=True)
        assert success, f"Replace mode import failed: {message}"


@pytest.mark.integration
def test_schema_backward_compatibility_with_previous_version(app):
    """
    Önceki schema versiyonundan gelen yedekler import edilebilmeli.
    Bu test için önceki versiyonun bir yedeği fixture olarak gereklidir.
    """
    # Örnek: tests/fixtures/backups/v24.0_backup.json gibi bir fixture
    # Bu test, migration stratejisi için kritiktir
    pass


@pytest.mark.integration
def test_encrypted_backup_compatibility(app):
    """
    Şifreli yedeklerin de uyumluluğu test edilmeli.
    """
    with app.app_context():
        test_password = "test-password-12345678"

        # Export encrypted
        encrypted_json = export_database_to_json(encrypt=True, password=test_password)
        encrypted_data = json.loads(encrypted_json)

        assert encrypted_data.get('encrypted') is True
        assert encrypted_data.get('schema_version') == SCHEMA_VERSION

        # Import encrypted
        success, message = import_database_from_json(
            encrypted_json,
            password=test_password,
            replace_existing=False
        )
        assert success, f"Encrypted import failed: {message}"


@pytest.mark.integration
def test_schema_metadata_completeness(app):
    """
    Yedek metadata'sının eksiksiz olup olmadığını kontrol et.
    """
    with app.app_context():
        validation_service = BackupValidationService()
        schema_info = validation_service.get_current_schema_info()

        assert schema_info['schema_version'] == SCHEMA_VERSION
        assert schema_info['total_tables'] > 0
        assert len(schema_info['tables']) > 0

        # Her tablonun sütun bilgisi olmalı
        for table_name, table_info in schema_info['tables'].items():
            assert 'column_count' in table_info
            assert 'columns' in table_info
            assert len(table_info['columns']) > 0


@pytest.mark.integration
def test_foreign_key_integrity_after_import(app):
    """
    Import sonrası foreign key integrity kontrolü.
    """
    with app.app_context():
        exported_json = export_database_to_json(encrypt=False)
        exported_data = json.loads(exported_json)

        validation_service = BackupValidationService()
        fk_errors = validation_service.validate_foreign_keys(exported_data)

        assert len(fk_errors) == 0, f"Foreign key integrity errors: {fk_errors}"


@pytest.mark.integration
def test_telemetry_tables_isolated_from_business_backups(app):
    """
    Operasyonel telemetri tabloları (storage_cleanup_audit, storage_scan_history)
    kullanıcı ve domain veritabanı JSON yedeklerine karışmamalı, izole kalmalıdır.
    """
    with app.app_context():
        exported_json = export_database_to_json(encrypt=False)
        exported_data = json.loads(exported_json)

        telemetry_keys = {"storage_cleanup_audit", "storage_cleanup_audits", "storage_scan_history", "storage_scan_histories"}
        found_telemetry = telemetry_keys.intersection(exported_data.keys())
        assert not found_telemetry, f"Telemetry tables leaked into backup JSON: {found_telemetry}"
