"""Persistence-neutral contracts for Storage Health history and audit metadata.

These records intentionally contain no financial row values, tenant business
payloads, credentials, absolute paths, or filesystem contents. They are DTO
contracts for a later, separately approved metadata persistence phase; creating
an instance never writes to SQLite.
"""

from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from domain.storage_health.models import CleanupCandidate
from domain.storage_health.services.scanner import StorageScan


class HistoryScope(StrEnum):
    PROJECT = "project"


class AuditStatus(StrEnum):
    RECOMMENDED = "recommended"
    CONFIRMED = "confirmed"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AuditAction(StrEnum):
    RECOMMENDATION_EMITTED = "recommendation_emitted"
    CLEANUP_REQUESTED = "cleanup_requested"
    CLEANUP_EXECUTED = "cleanup_executed"
    CLEANUP_ROLLED_BACK = "cleanup_rolled_back"


def _copy_nonnegative(values: Mapping[str, int]) -> dict[str, int]:
    result = {str(key): int(value) for key, value in values.items()}
    if any(value < 0 for value in result.values()):
        raise ValueError("metadata byte totals must be non-negative")
    return dict(sorted(result.items()))


def _history_id(scope: str, snapshot_id: str) -> str:
    return hashlib.sha256(f"storage-history-v1|{scope}|{snapshot_id}".encode("utf-8")).hexdigest()[:32]


def _audit_id(candidate_id: str, snapshot_id: str) -> str:
    return hashlib.sha256(f"storage-audit-v1|{candidate_id}|{snapshot_id}".encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True, slots=True)
class ScanHistoryRecord:
    history_id: str
    scope: HistoryScope
    snapshot_id: str
    scanned_at_epoch: float
    total_bytes: int
    category_bytes: dict[str, int]
    policy_bytes: dict[str, int]
    protected_bytes: int
    candidate_bytes: int
    safe_reclaimable_bytes: int
    files_scanned: int
    directories_scanned: int
    symlinks_skipped: int
    errors_count: int
    truncated: bool
    schema_version: int = 1

    @classmethod
    def from_scan(
        cls,
        scan: StorageScan,
        *,
        snapshot_id: str,
        scope: HistoryScope = HistoryScope.PROJECT,
    ) -> "ScanHistoryRecord":
        integer_values = {
            "total_bytes": scan.total_bytes,
            "protected_bytes": scan.protected_bytes,
            "candidate_bytes": scan.candidate_bytes,
            "safe_reclaimable_bytes": scan.safe_reclaimable_bytes,
            "files_scanned": scan.files_scanned,
            "directories_scanned": scan.directories_scanned,
            "symlinks_skipped": scan.symlinks_skipped,
        }
        if any(value < 0 for value in integer_values.values()):
            raise ValueError("scan metadata counters must be non-negative")
        if (
            not snapshot_id
            or len(snapshot_id) != 64
            or any(character not in string.hexdigits for character in snapshot_id)
        ):
            raise ValueError("snapshot_id must be a canonical SHA-256 hex string")
        return cls(
            history_id=_history_id(scope.value, snapshot_id),
            scope=scope,
            snapshot_id=snapshot_id,
            scanned_at_epoch=float(scan.scanned_at_epoch),
            total_bytes=int(scan.total_bytes),
            category_bytes=_copy_nonnegative(scan.category_bytes),
            policy_bytes=_copy_nonnegative(scan.policy_bytes),
            protected_bytes=int(scan.protected_bytes),
            candidate_bytes=int(scan.candidate_bytes),
            safe_reclaimable_bytes=int(scan.safe_reclaimable_bytes),
            files_scanned=int(scan.files_scanned),
            directories_scanned=int(scan.directories_scanned),
            symlinks_skipped=int(scan.symlinks_skipped),
            errors_count=len(scan.errors),
            truncated=bool(scan.truncated),
        )

    def to_dict(self) -> dict:
        return {
            "history_id": self.history_id,
            "scope": self.scope.value,
            "snapshot_id": self.snapshot_id,
            "scanned_at_epoch": self.scanned_at_epoch,
            "total_bytes": self.total_bytes,
            "category_bytes": dict(self.category_bytes),
            "policy_bytes": dict(self.policy_bytes),
            "protected_bytes": self.protected_bytes,
            "candidate_bytes": self.candidate_bytes,
            "safe_reclaimable_bytes": self.safe_reclaimable_bytes,
            "files_scanned": self.files_scanned,
            "directories_scanned": self.directories_scanned,
            "symlinks_skipped": self.symlinks_skipped,
            "errors_count": self.errors_count,
            "truncated": self.truncated,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class CleanupAuditRecord:
    audit_id: str
    candidate_id: str
    scan_snapshot_id: str
    action: AuditAction
    status: AuditStatus
    risk_level: str
    rollback_strategy: str
    reclaimable_bytes: int
    mutation_performed: bool
    created_at_epoch: float
    schema_version: int = 1

    @classmethod
    def from_candidate(
        cls,
        candidate: CleanupCandidate,
        *,
        created_at_epoch: float,
    ) -> "CleanupAuditRecord":
        if candidate.execute_eligible or not candidate.user_confirmation_required:
            raise ValueError("recommendation audit requires a non-executable, explicit-confirmation candidate")
        if candidate.reclaimable_bytes < 0:
            raise ValueError("reclaimable bytes must be non-negative")
        return cls(
            audit_id=_audit_id(candidate.candidate_id, candidate.snapshot_token),
            candidate_id=candidate.candidate_id,
            scan_snapshot_id=candidate.snapshot_token,
            action=AuditAction.RECOMMENDATION_EMITTED,
            status=AuditStatus.RECOMMENDED,
            risk_level=candidate.risk_level.value,
            rollback_strategy=candidate.rollback.kind.value,
            reclaimable_bytes=candidate.reclaimable_bytes,
            mutation_performed=False,
            created_at_epoch=float(created_at_epoch),
        )

    def to_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "candidate_id": self.candidate_id,
            "scan_snapshot_id": self.scan_snapshot_id,
            "action": self.action.value,
            "status": self.status.value,
            "risk_level": self.risk_level,
            "rollback_strategy": self.rollback_strategy,
            "reclaimable_bytes": self.reclaimable_bytes,
            "mutation_performed": self.mutation_performed,
            "created_at_epoch": self.created_at_epoch,
            "schema_version": self.schema_version,
        }
