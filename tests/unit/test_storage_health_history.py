from dataclasses import replace

import pytest

from domain.storage_health.history import (
    AuditAction,
    AuditStatus,
    CleanupAuditRecord,
    ScanHistoryRecord,
)
from domain.storage_health.models import CleanupCandidate
from domain.storage_health.persistence_models import (
    STORAGE_METADATA_TABLES,
    StorageCleanupAuditMetadata,
    StorageScanHistoryMetadata,
    render_sqlite_ddl,
)
from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.scanner import StorageObservation, StorageScan
from domain.storage_health.trend import compute_storage_trend


def make_scan(*, scanned_at=100.0, total=100, errors=(), truncated=False):
    return StorageScan(
        project_root="C:/redacted/project",
        scanned_at_epoch=scanned_at,
        observations=(),
        category_bytes={"cache": total // 2, "runtime": total - total // 2},
        policy_bytes={PolicyClass.PROTECTED.value: total // 2, PolicyClass.SAFE_AUTO.value: total - total // 2},
        top_consumers=(),
        errors=tuple(errors),
        truncated=truncated,
        files_scanned=1,
        directories_scanned=1,
        symlinks_skipped=0,
    )


def make_history(*, snapshot_id, scanned_at=100.0, total=100, errors=(), truncated=False):
    return ScanHistoryRecord.from_scan(
        make_scan(scanned_at=scanned_at, total=total, errors=errors, truncated=truncated),
        snapshot_id=snapshot_id,
    )


@pytest.mark.unit
def test_history_record_is_pathless_and_financially_isolated():
    record = make_history(snapshot_id="a" * 64)
    payload = record.to_dict()

    assert payload["scope"] == "project"
    assert payload["snapshot_id"] == "a" * 64
    assert "project_root" not in str(payload)
    assert "transaction" not in str(payload).lower()
    assert "tenant" not in str(payload).lower()


@pytest.mark.unit
def test_history_requires_canonical_sha256_snapshot_id():
    with pytest.raises(ValueError):
        make_history(snapshot_id="short")


@pytest.mark.unit
def test_trend_requires_two_complete_same_scope_snapshots():
    one = make_history(snapshot_id="a" * 64)
    assert compute_storage_trend((one,)).to_dict()["reason"] == "insufficient_snapshots"

    previous = make_history(snapshot_id="a" * 64, scanned_at=100.0, total=100)
    current = make_history(snapshot_id="b" * 64, scanned_at=200.0, total=120)
    trend = compute_storage_trend((current, previous))

    assert trend.available is True
    assert trend.reason == "two_complete_snapshots"
    assert trend.total.delta_bytes == 20
    assert trend.total.percent_change == 20.0
    assert trend.category_deltas["runtime"].delta_bytes == 10


@pytest.mark.unit
def test_trend_withholds_output_for_same_incomplete_or_mismatched_scope():
    previous = make_history(snapshot_id="a" * 64, scanned_at=100.0)
    same = make_history(snapshot_id="a" * 64, scanned_at=200.0)
    assert compute_storage_trend((previous, same)).reason == "same_snapshot"

    incomplete = make_history(snapshot_id="b" * 64, scanned_at=200.0, truncated=True)
    assert compute_storage_trend((previous, incomplete)).reason == "incomplete_snapshot"

    errored = make_history(snapshot_id="c" * 64, scanned_at=200.0, errors=("walk_error:PermissionError",))
    assert compute_storage_trend((previous, errored)).reason == "snapshot_errors_present"

    mismatched = replace(make_history(snapshot_id="d" * 64, scanned_at=200.0), scope="other")
    assert compute_storage_trend((previous, mismatched)).reason == "scope_mismatch"


@pytest.mark.unit
def test_prospective_metadata_ddl_has_no_financial_foreign_keys():
    assert {table.name for table in STORAGE_METADATA_TABLES} == {
        "storage_scan_history",
        "storage_cleanup_audit",
    }
    assert StorageScanHistoryMetadata.__table__.foreign_keys == set()
    assert StorageCleanupAuditMetadata.__table__.foreign_keys == set()

    ddl = "\n".join(render_sqlite_ddl()).upper()
    assert "CREATE TABLE STORAGE_SCAN_HISTORY" in ddl
    assert "CREATE TABLE STORAGE_CLEANUP_AUDIT" in ddl
    assert "FOREIGN KEY" not in ddl
    assert "TRANSACTION" not in ddl
    assert "SECRET" not in ddl


@pytest.mark.unit
def test_cleanup_audit_record_is_recommendation_only():
    observation = StorageObservation(
        relative_path="__pycache__/module.pyc",
        category="cache",
        policy_class=PolicyClass.SAFE_AUTO.value,
        reason="regenerable_cache",
        bytes=4,
        modified_epoch=1.0,
    )
    candidate = CleanupCandidate.from_observation(observation, snapshot_token="a" * 64)
    record = CleanupAuditRecord.from_candidate(candidate, created_at_epoch=300.0)

    assert record.action == AuditAction.RECOMMENDATION_EMITTED
    assert record.status == AuditStatus.RECOMMENDED
    assert record.mutation_performed is False
    assert record.to_dict()["reclaimable_bytes"] == 4
