import pytest
from sqlalchemy import create_engine, inspect

from domain.storage_health.migration_plan import (
    MigrationReadiness,
    SchemaDiffStatus,
    build_metadata_migration_plan,
)
from domain.storage_health.persistence_models import STORAGE_METADATA_TABLES


@pytest.mark.unit
def test_metadata_migration_plan_is_deterministic_and_review_only():
    first = build_metadata_migration_plan()
    second = build_metadata_migration_plan()

    assert first.to_dict() == second.to_dict()
    assert first.readiness is MigrationReadiness.DRY_RUN_ONLY
    assert first.active_db_inspected is False
    assert first.migration_executed is False
    assert first.financial_rows_read is False
    assert first.foreign_key_count == 0
    assert first.schema_diff_status is SchemaDiffStatus.PROSPECTIVE_MANIFEST_ONLY
    assert "active_db_schema_not_inspected" in first.schema_diff
    assert "migration_not_authorized" in first.blocking_reasons
    assert first.rollback.backup_required is True
    assert first.rollback.backup_verified is False
    assert first.rollback.restore_tested is False


@pytest.mark.unit
def test_metadata_tables_are_isolated_in_memory():
    engine = create_engine("sqlite:///:memory:")
    for table in STORAGE_METADATA_TABLES:
        table.create(engine)

    names = set(inspect(engine).get_table_names())
    assert names == {"storage_scan_history", "storage_cleanup_audit"}
    assert all(len(table.foreign_keys) == 0 for table in STORAGE_METADATA_TABLES)
    assert all(table.name in names for table in STORAGE_METADATA_TABLES)
