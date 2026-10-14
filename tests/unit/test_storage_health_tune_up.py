import sqlite3

import pytest

from application.storage_health.service import StorageHealthApplicationService


@pytest.fixture
def mock_app_environment(tmp_path):
    # Create DB
    db_file = tmp_path / "e_cuzdan_v15.db"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE sample (id INT, txt TEXT)")
        for i in range(100):
            conn.execute("INSERT INTO sample VALUES (?, ?)", (i, "data"))
        conn.commit()

    # Create dummy cache files
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "module.cpython-313.pyc").write_bytes(b"compiled bytecode")

    return tmp_path, db_file


@pytest.mark.unit
def test_overview_includes_telemetry_and_database(mock_app_environment):
    tmp_path, db_file = mock_app_environment
    service = StorageHealthApplicationService(tmp_path, db_path=db_file)

    overview = service.get_overview(refresh=True)
    assert "telemetry" in overview
    assert "database_vitality" in overview
    assert "data_hygiene" in overview
    assert "storage_breakdown" in overview

    assert overview["telemetry"]["health_status"] in {"OPTIMAL", "WARNING", "CRITICAL"}
    assert overview["database_vitality"]["integrity_status"] == "ok"
    assert overview["data_hygiene"]["total_prunable_rows"] == 0
    assert len(overview["storage_breakdown"]["categories"]) == 5


@pytest.mark.unit
def test_execute_smart_tune_up_full_pipeline(mock_app_environment):
    tmp_path, db_file = mock_app_environment
    service = StorageHealthApplicationService(tmp_path, db_path=db_file)

    result = service.execute_smart_tune_up(purge_cache=True, create_snapshot=True)
    assert result["success"] is True
    assert "total_bytes_freed" in result
    assert "database_summary" in result
    assert "rows_pruned" in result
    assert result["rows_pruned"] == 0
    assert result["snapshot_path"] is not None
