"""
Unit tests for scripts/migrate_sqlite_to_postgres.py.
"""
from pathlib import Path
import tempfile
import pytest

from scripts.migrate_sqlite_to_postgres import (
    execute_migration,
    get_sqlite_tables,
    get_sqlite_table_counts,
    read_sqlite_table_data,
)

SQLITE_PATH = Path("e_cuzdan_v15.db")


@pytest.mark.unit
def test_get_sqlite_tables():
    tables = get_sqlite_tables(SQLITE_PATH)
    assert len(tables) >= 40
    assert "user" in tables
    assert "tenant" in tables
    assert "transaction" in tables
    assert "journal_entry" in tables


@pytest.mark.unit
def test_get_sqlite_table_counts():
    tables = ["user", "tenant", "category", "transaction"]
    counts = get_sqlite_table_counts(SQLITE_PATH, tables)
    assert counts["user"] >= 1
    assert counts["tenant"] >= 1
    assert counts["category"] >= 1
    assert counts["transaction"] >= 0


@pytest.mark.unit
def test_read_sqlite_table_data():
    cols, rows = read_sqlite_table_data(SQLITE_PATH, "user")
    assert "id" in cols
    assert "username" in cols
    assert len(rows) >= 1
    assert rows[0]["username"] is not None


@pytest.mark.unit
def test_dry_run_execution():
    code = execute_migration(SQLITE_PATH, target_url="", dry_run=True)
    assert code == 0


@pytest.mark.unit
def test_migration_roundtrip_temp_target(tmp_path):
    target_db = tmp_path / "target_test.db"
    target_url = f"sqlite:///{target_db.as_posix()}"

    exit_code = execute_migration(
        sqlite_path=SQLITE_PATH,
        target_url=target_url,
        dry_run=False,
        verify_only=False,
    )
    assert exit_code == 0
    assert target_db.exists()
