from pathlib import Path

import pytest

from domain.storage_health.services.system_telemetry import (
    DiskTelemetry,
    StorageBreakdown,
    SystemTelemetryService,
)


@pytest.mark.unit
def test_disk_telemetry_query():
    service = SystemTelemetryService(Path("."))
    telemetry = service.get_disk_telemetry()

    assert isinstance(telemetry, DiskTelemetry)
    assert telemetry.total_bytes > 0
    assert telemetry.used_bytes > 0
    assert telemetry.free_bytes > 0
    assert 0.0 <= telemetry.used_percentage <= 100.0
    assert telemetry.health_status in {"OPTIMAL", "WARNING", "CRITICAL"}


@pytest.mark.unit
def test_storage_breakdown_categories(tmp_path):
    # Setup dummy structure
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "app.log").write_text("log data", encoding="utf-8")
    (tmp_path / "backups").mkdir()
    (tmp_path / "backups" / "b.json").write_text("backup data", encoding="utf-8")
    db_file = tmp_path / "app.db"
    db_file.write_text("sqlite format", encoding="utf-8")

    service = SystemTelemetryService(tmp_path, db_path=db_file)
    breakdown = service.get_storage_breakdown()

    assert isinstance(breakdown, StorageBreakdown)
    assert len(breakdown.categories) == 5
    cat_keys = {c.key for c in breakdown.categories}
    assert cat_keys == {"database", "backups", "logs", "cache", "app_core"}
