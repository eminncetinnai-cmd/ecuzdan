"""Integration tests for UserIban database import and export round-trip."""

from __future__ import annotations

import json
import pytest

from infrastructure.backup.validation import BackupValidationService
from infrastructure.database.management import (
    export_database_to_json,
    import_database_from_json,
)
from infrastructure.export.export_service import ExportService
from models import User, UserIban, db


@pytest.mark.integration
def test_user_iban_export_and_backup_validation(app):
    with app.app_context():
        tenant_id = "default"
        iban_record = UserIban(
            tenant_id=tenant_id,
            title="Şirket Garanti Hesabı",
            iban="TR330006200511123456789012",
            bank_name="Garanti BBVA",
            account_holder="Test Kullanıcı",
            category="kendi_hesabim",
            note="Maaş ve primler buraya",
            is_favorite=True,
            easy_address_type="Telefon",
            easy_address="0532 999 88 77",
        )
        db.session.add(iban_record)
        db.session.commit()
        iban_id = iban_record.id

        # 1. Full Database Export
        exported_json = export_database_to_json(encrypt=False)
        payload = json.loads(exported_json)

        assert "user_ibans" in payload
        assert any(item["id"] == iban_id for item in payload["user_ibans"])
        item = next(it for it in payload["user_ibans"] if it["id"] == iban_id)
        assert item["bank_name"] == "Garanti BBVA"
        assert item["iban"] == "TR330006200511123456789012"
        assert item.get("is_favorite") is True
        assert item.get("easy_address") == "0532 999 88 77"

        # 2. Backup Validation
        valid, message = BackupValidationService().validate_backup_compatibility(payload)
        assert valid is True, f"Backup validation failed: {message}"

        # 3. Full Database Import / Restore
        success, import_msg = import_database_from_json(exported_json)
        assert success is True, f"Import failed: {import_msg}"

        restored = db.session.get(UserIban, iban_id)
        assert restored is not None
        assert restored.title == "Şirket Garanti Hesabı"
        assert restored.bank_name == "Garanti BBVA"
        assert restored.formatted_iban == "TR33 0006 2005 1112 3456 7890 12"
        assert restored.is_favorite is True
        assert restored.easy_address == "0532 999 88 77"

        # 4. Tenant-scoped Export
        user = User.query.filter_by(tenant_id=tenant_id).first()
        if user:
            tenant_export_str = ExportService().export_tenant_json(user.id, encrypt=False)
            tenant_payload = json.loads(tenant_export_str)
            assert "user_ibans" in tenant_payload
            assert any(it["id"] == str(iban_id) for it in tenant_payload["user_ibans"])
