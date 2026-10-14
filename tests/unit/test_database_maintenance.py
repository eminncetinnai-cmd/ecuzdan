import sqlite3
from pathlib import Path

import pytest

from domain.storage_health.services.database_maintenance import (
    DatabaseMaintenanceService,
    DatabaseMaintenanceSummary,
    DatabaseStats,
)


@pytest.fixture
def temp_sqlite_db(tmp_path):
    """Create a real temporary SQLite database with tables and records."""
    db_file = tmp_path / "test_app.db"
    backup_folder = tmp_path / "backups"
    backup_folder.mkdir()

    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE transactions (id INTEGER PRIMARY KEY, title TEXT, amount REAL)")
        # Insert 1,000 rows
        for i in range(1000):
            conn.execute("INSERT INTO transactions (title, amount) VALUES (?, ?)", (f"Tx {i}", i * 10.5))
        conn.commit()

        # Delete 500 rows to create freelist pages
        conn.execute("DELETE FROM transactions WHERE id <= 500")
        conn.commit()

    return db_file, backup_folder


@pytest.mark.unit
def test_database_stats_inspection(temp_sqlite_db):
    db_file, backup_folder = temp_sqlite_db
    service = DatabaseMaintenanceService(db_file, backup_dir=backup_folder)

    stats = service.get_stats()
    assert isinstance(stats, DatabaseStats)
    assert stats.exists is True
    assert stats.is_sqlite is True
    assert stats.size_bytes > 0
    assert stats.integrity_status == "ok"
    assert stats.foreign_key_violations == 0
    assert stats.journal_mode == "WAL"
    assert stats.freelist_count > 0  # We deleted 500 rows


@pytest.mark.unit
def test_database_maintenance_pipeline_execution(temp_sqlite_db):
    db_file, backup_folder = temp_sqlite_db
    service = DatabaseMaintenanceService(db_file, backup_dir=backup_folder)

    summary = service.execute_maintenance_pipeline(create_safety_snapshot=True)
    assert isinstance(summary, DatabaseMaintenanceSummary)
    assert summary.success is True
    assert summary.snapshot_path is not None
    assert Path(summary.snapshot_path).exists()
    assert len(summary.steps) >= 5

    # Check step keys
    step_keys = [s.step_key for s in summary.steps]
    assert "preflight_check" in step_keys
    assert "safety_snapshot" in step_keys
    assert "wal_checkpoint" in step_keys
    assert "vacuum" in step_keys
    assert "optimize" in step_keys
    assert "postflight_check" in step_keys

    # All steps should be successful
    assert all(s.success for s in summary.steps)

    # Post-maintenance verification
    post_stats = service.get_stats()
    assert post_stats.freelist_count == 0  # Vacuum eliminated freelist
    assert post_stats.integrity_status == "ok"


@pytest.mark.unit
def test_database_stats_missing_file(tmp_path):
    missing_file = tmp_path / "non_existent.db"
    service = DatabaseMaintenanceService(missing_file)
    stats = service.get_stats()
    assert stats.exists is False
    assert stats.integrity_status == "file_not_found"


@pytest.mark.unit
def test_database_snapshot_rotation(temp_sqlite_db):
    db_file, backup_folder = temp_sqlite_db
    service = DatabaseMaintenanceService(db_file, backup_dir=backup_folder)

    # Create 5 dummy snapshots
    for i in range(5):
        snap = backup_folder / f"maintenance_snapshot_2026090{i}_120000.db"
        snap.write_text(f"dummy content {i}")

    assert len(list(backup_folder.glob("maintenance_snapshot_*.db"))) == 5

    deleted = service._rotate_snapshots(max_snapshots=3)
    assert deleted == 2
    assert len(list(backup_folder.glob("maintenance_snapshot_*.db"))) == 3

