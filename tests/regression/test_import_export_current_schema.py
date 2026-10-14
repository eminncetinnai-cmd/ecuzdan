from __future__ import annotations

import json

import pytest
from sqlalchemy import inspect


@pytest.mark.regression
def test_full_export_covers_current_tables_and_passes_validation(app):
    from infrastructure.backup.validation import BackupValidationService
    from infrastructure.database.management import export_database_to_json
    from models import db

    with app.app_context():
        payload = json.loads(export_database_to_json(encrypt=False))
        actual_tables = set(inspect(db.engine).get_table_names()) - {"_schema_version"}
        exported_tables = set(payload) - {"schema_version", "metadata"}
        validator = BackupValidationService()
        normalized_exported = {
            validator._normalize_table_name(table_name)
            for table_name in exported_tables
        }

        missing_tables = sorted(actual_tables - normalized_exported)
        assert not missing_tables, f"Export kapsamı dışında kalan tablolar: {missing_tables}"

        valid, message = BackupValidationService().validate_backup_compatibility(payload)
        assert valid, message


@pytest.mark.regression
def test_backup_validation_rejects_missing_foreign_key(app):
    from infrastructure.backup.validation import BackupValidationService
    from infrastructure.database.management import export_database_to_json
    from models import Category, Transaction, db

    with app.app_context():
        category = Category.query.filter_by(name="Maaş").first()
        db.session.add(
            Transaction(
                date="2026-05-01",
                category=category.name,
                description="FK validation fixture",
                type="Gelir",
                status="Ödendi",
                amount="100.0000",
                tenant_id="default",
            )
        )
        db.session.commit()
        payload = json.loads(export_database_to_json(encrypt=False))
        assert payload["transactions"]
        payload["transactions"][0]["tenant_id"] = "missing-tenant"

        valid, message = BackupValidationService().validate_backup_compatibility(payload)
        assert valid is False
        assert "foreign key" in message.lower()


@pytest.mark.regression
def test_standard_category_seed_preserves_existing_budget_and_identity(app):
    from database.seeding import _initialize_default_data
    from models import Category, db

    with app.app_context():
        category = Category.query.filter_by(tenant_id=None).first()
        assert category is not None
        category_id = category.id
        category.budget_limit = "1234.5600"
        db.session.commit()
        before_count = Category.query.filter_by(tenant_id=None).count()

        _initialize_default_data()
        db.session.expire_all()

        preserved = db.session.get(Category, category_id)
        assert preserved is not None
        assert str(preserved.budget_limit) == "1234.5600"
        assert Category.query.filter_by(tenant_id=None).count() >= before_count
