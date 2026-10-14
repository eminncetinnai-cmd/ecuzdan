"""Regression coverage for database connection and import/export contracts."""

from __future__ import annotations

import inspect
import json

import pytest


@pytest.mark.regression
def test_schema_version_has_single_current_value():
    from database.migrations import SCHEMA_VERSION as migration_version
    from database.schema_version import SCHEMA_VERSION
    from infrastructure.backup.validation import BackupValidationService

    assert migration_version == "v25.2"
    assert SCHEMA_VERSION == migration_version
    assert BackupValidationService.CURRENT_SCHEMA_VERSION == SCHEMA_VERSION


@pytest.mark.regression
def test_sqlite_connection_enables_foreign_keys_per_connection():
    from app import app, db

    with app.app_context():
        with db.engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar() in (5000, 30000)


@pytest.mark.regression
def test_export_payload_uses_current_schema_version():
    from app import app
    from database.schema_version import SCHEMA_VERSION
    from infrastructure.database.management import export_database_to_json

    with app.app_context():
        payload = json.loads(export_database_to_json(encrypt=False))

    assert payload["schema_version"] == SCHEMA_VERSION


@pytest.mark.regression
def test_connection_module_contains_pool_connection_hook():
    import database.connection as connection_module

    source = inspect.getsource(connection_module)
    assert "event.listen" in source
    assert "_apply_sqlite_connection_pragmas" in source
