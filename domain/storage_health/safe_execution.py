"""Non-mutating preparation model for a future PHGS Safe Execution phase.

This module builds a deterministic, explicitly allowlisted execution plan and
evaluates safety gates. It deliberately does not open, hash, copy, archive,
delete, move, rename, lock, inspect processes, or otherwise mutate any
filesystem or process state.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Iterable

from domain.storage_health.execution import ConfirmationReceipt, ExecutionPreview, build_execution_preview
from domain.storage_health.lifecycle import CleanupEligibility
from domain.storage_health.models import CleanupCandidate, RecommendationSet
from domain.storage_health.services.snapshot import SnapshotRecheck

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
_SENSITIVE_PARTS = {".env", "credentials", "secrets", "client-secret", "client_secret"}
_ALLOWLISTED_DIRS = {"__pycache__", ".pytest_cache"}
_TEMP_DIRS = {"tmp", "temp", "temporary"}
_NON_EXECUTABLE_PARTS = {
    ".git",
    ".venv",
    "application",
    "configuration",
    "database",
    "domain",
    "infrastructure",
    "routes",
    "runtime",
    "static",
    "templates",
    "tests",
    "translations",
}


class SafeExecutionAction(StrEnum):
    REGENERATE_CACHE = "regenerate_cache"
    REMOVE_DISPOSABLE_TEMP = "remove_disposable_temp"


class ArchiveProofStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    REQUIRED_NOT_VERIFIED = "required_not_verified"
    VERIFIED = "verified"


class ProcessLockStatus(StrEnum):
    NOT_ACQUIRED = "not_acquired"
    HELD = "held"
    CONFLICT = "conflict"


class IdempotencyReservationStatus(StrEnum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    PLAN_MISMATCH = "plan_mismatch"


class SafeExecutionBlockReason(StrEnum):
    NON_MUTATING_PREPARATION_ONLY = "non_mutating_preparation_only"
    NOT_ALLOWLISTED = "not_allowlisted"
    PROTECTED_RESOURCE = "protected_resource"
    UNKNOWN_GOVERNANCE = "unknown_governance"
    POLICY_NOT_SAFE_AUTO = "policy_not_safe_auto"
    EXPLICIT_USER_CONFIRMATION_REQUIRED = "explicit_user_confirmation_required"
    CONFIRMATION_PLAN_MISMATCH = "confirmation_plan_mismatch"
    CONFIRMATION_SNAPSHOT_MISMATCH = "confirmation_snapshot_mismatch"
    FRESH_SNAPSHOT_RECHECK_REQUIRED = "fresh_snapshot_recheck_required"
    FRESH_SNAPSHOT_RECHECK_FAILED = "fresh_snapshot_recheck_failed"
    ARCHIVE_PROOF_REQUIRED = "archive_proof_required"
    ARCHIVE_PROOF_PLAN_MISMATCH = "archive_proof_plan_mismatch"
    ARCHIVE_PROOF_CANDIDATE_MISMATCH = "archive_proof_candidate_mismatch"
    PROCESS_LOCK_REQUIRED = "process_lock_required"
    PROCESS_LOCK_CONFLICT = "process_lock_conflict"
    ACTIVE_PROCESS_DETECTED = "active_process_detected"
    PROCESS_OWNER_UNVERIFIED = "process_owner_unverified"
    IDEMPOTENCY_RESERVATION_REQUIRED = "idempotency_reservation_required"
    IDEMPOTENCY_ALREADY_RESERVED = "idempotency_already_reserved"
    IDEMPOTENCY_PLAN_MISMATCH = "idempotency_plan_mismatch"
    INVALID_IDEMPOTENCY_KEY = "invalid_idempotency_key"
    POST_CONDITION_REQUIRED = "post_condition_required"
    EMPTY_ALLOWLIST_SELECTION = "empty_allowlist_selection"
    DUPLICATE_CANDIDATE = "duplicate_candidate"


def _redact_relative_path(relative_path: str) -> str:
    path = Path(relative_path)
    windows_path = PureWindowsPath(relative_path)
    parts = {part.lower() for part in path.parts} | {part.lower() for part in windows_path.parts}
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or ".." in path.parts
        or ".." in windows_path.parts
    ):
        return "<protected-resource>"
    if any(part in _SENSITIVE_PARTS or "secret" in part or "credential" in part for part in parts):
        return "<protected-resource>"
    return path.as_posix()


def _relative_parts(relative_path: str) -> tuple[str, ...]:
    normalized = relative_path.replace("\\", "/")
    return tuple(part.lower() for part in PureWindowsPath(normalized).parts if part not in {"", "."})


def _canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """Bounded opaque key; its reservation is memory-only in this phase."""

    value: str

    def __post_init__(self) -> None:
        if not _IDEMPOTENCY_KEY.fullmatch(self.value):
            raise ValueError("invalid idempotency key")

    def to_dict(self) -> dict:
        return {"value": self.value}


@dataclass(frozen=True, slots=True)
class IdempotencyReservation:
    key: IdempotencyKey
    plan_hash: str
    status: IdempotencyReservationStatus

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash):
            raise ValueError("plan_hash must be a SHA-256 hex value")

    @property
    def valid(self) -> bool:
        return self.status is IdempotencyReservationStatus.ACCEPTED

    def to_dict(self) -> dict:
        return {
            "key": self.key.value,
            "plan_hash": self.plan_hash,
            "status": self.status.value,
            "valid": self.valid,
        }


class InMemoryIdempotencyRegistry:
    """Process-local reservation registry; it performs no DB or filesystem write."""

    def __init__(self) -> None:
        self._reservations: dict[str, str] = {}
        self._lock = threading.RLock()

    def reserve(self, key: IdempotencyKey | str, plan_hash: str) -> IdempotencyReservation:
        normalized_key = key if isinstance(key, IdempotencyKey) else IdempotencyKey(key)
        if not _SHA256_HEX.fullmatch(plan_hash):
            raise ValueError("plan_hash must be a SHA-256 hex value")
        with self._lock:
            previous_plan = self._reservations.get(normalized_key.value)
            if previous_plan is None:
                self._reservations[normalized_key.value] = plan_hash
                status = IdempotencyReservationStatus.ACCEPTED
            elif previous_plan == plan_hash:
                status = IdempotencyReservationStatus.DUPLICATE
            else:
                status = IdempotencyReservationStatus.PLAN_MISMATCH
        return IdempotencyReservation(normalized_key, plan_hash, status)


@dataclass(frozen=True, slots=True)
class ExternalArchiveShaProof:
    """External proof supplied by an approved archive process, never created here."""

    plan_hash: str
    covered_candidate_ids: tuple[str, ...]
    external_archive_ref: str
    archive_sha256: str
    archived_bytes: int
    verified_at_epoch: float

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash):
            raise ValueError("proof plan_hash must be a SHA-256 hex value")
        if not self.covered_candidate_ids or len(set(self.covered_candidate_ids)) != len(self.covered_candidate_ids):
            raise ValueError("proof must cover one or more unique candidates")
        if not self.external_archive_ref.startswith(("external://", "archive://")):
            raise ValueError("proof reference must identify an external archive")
        if not _SHA256_HEX.fullmatch(self.archive_sha256):
            raise ValueError("archive_sha256 must be a SHA-256 hex value")
        if self.archived_bytes <= 0:
            raise ValueError("archived_bytes must be positive")
        if self.verified_at_epoch < 0:
            raise ValueError("verified_at_epoch cannot be negative")

    def to_dict(self) -> dict:
        return {
            "plan_hash": self.plan_hash,
            "covered_candidate_ids": list(self.covered_candidate_ids),
            "external_archive_ref": self.external_archive_ref,
            "archive_sha256": self.archive_sha256,
            "archived_bytes": self.archived_bytes,
            "verified_at_epoch": self.verified_at_epoch,
        }


@dataclass(frozen=True, slots=True)
class ProcessPreflight:
    """Read-only process/maintenance facts supplied by an external preflight."""

    port: int
    listener_pid: int | None
    process_owner_verified: bool
    application_stopped: bool
    maintenance_window_open: bool
    lock_status: ProcessLockStatus

    def __post_init__(self) -> None:
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.listener_pid is not None and self.listener_pid <= 0:
            raise ValueError("listener_pid must be positive when present")

    @property
    def safe_for_preparation(self) -> bool:
        return (
            self.lock_status is ProcessLockStatus.HELD
            and (self.listener_pid is None or self.application_stopped)
            and (self.listener_pid is None or self.process_owner_verified)
        )

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "listener_present": self.listener_pid is not None,
            "process_owner_verified": self.process_owner_verified,
            "application_stopped": self.application_stopped,
            "maintenance_window_open": self.maintenance_window_open,
            "lock_status": self.lock_status.value,
            "safe_for_preparation": self.safe_for_preparation,
        }


@dataclass(frozen=True, slots=True)
class PostConditionPreview:
    expected_candidate_count: int
    expected_reclaimable_bytes: int
    expected_status: str = "post_rescan_required"
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.expected_candidate_count < 0 or self.expected_reclaimable_bytes < 0:
            raise ValueError("post-condition expectations cannot be negative")
        if self.mutation_performed:
            raise ValueError("post-condition preview cannot report a mutation")

    def to_dict(self) -> dict:
        return {
            "expected_candidate_count": self.expected_candidate_count,
            "expected_reclaimable_bytes": self.expected_reclaimable_bytes,
            "expected_status": self.expected_status,
            "mutation_performed": self.mutation_performed,
        }


@dataclass(frozen=True, slots=True)
class SafeExecutionTarget:
    candidate_id: str
    relative_path: str
    action: SafeExecutionAction
    category: str
    reclaimable_bytes: int
    metadata_fingerprint: dict[str, int | float | str | None]
    expected_post_condition: str
    archive_proof: ArchiveProofStatus
    governance_eligibility: str

    def __post_init__(self) -> None:
        if not self.candidate_id or len(self.candidate_id) > 64:
            raise ValueError("candidate_id must be bounded")
        if self.reclaimable_bytes <= 0:
            raise ValueError("safe execution target must have positive bytes")
        if _redact_relative_path(self.relative_path) == "<protected-resource>":
            raise ValueError("protected or unsafe path cannot be an execution target")
        if self.metadata_fingerprint.get("type") != "file":
            raise ValueError("safe execution target must be a leaf file")
        if self.governance_eligibility != CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION.value:
            raise ValueError("target requires explicit confirmation eligibility")

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "relative_path": _redact_relative_path(self.relative_path),
            "action": self.action.value,
            "category": self.category,
            "reclaimable_bytes": self.reclaimable_bytes,
            "metadata_fingerprint": dict(self.metadata_fingerprint),
            "expected_post_condition": self.expected_post_condition,
            "archive_proof": self.archive_proof.value,
            "governance_eligibility": self.governance_eligibility,
        }


@dataclass(frozen=True, slots=True)
class SafeExecutionAuditPreview:
    audit_id: str
    plan_hash: str
    candidate_count: int
    action: str
    status: str
    post_condition: PostConditionPreview
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash):
            raise ValueError("plan_hash must be a SHA-256 hex value")
        if not self.audit_id or len(self.audit_id) > 64:
            raise ValueError("audit_id must be bounded")
        if self.candidate_count < 0:
            raise ValueError("candidate_count cannot be negative")
        if self.mutation_performed:
            raise ValueError("audit preview cannot report a mutation")
        if self.post_condition.mutation_performed:
            raise ValueError("audit post-condition cannot report a mutation")

    def to_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "plan_hash": self.plan_hash,
            "candidate_count": self.candidate_count,
            "action": self.action,
            "status": self.status,
            "post_condition": self.post_condition.to_dict(),
            "mutation_performed": self.mutation_performed,
        }


@dataclass(frozen=True, slots=True)
class SafeExecutionPlan:
    plan_hash: str
    base_preview_hash: str
    snapshot_id: str
    candidate_ids: tuple[str, ...]
    targets: tuple[SafeExecutionTarget, ...]
    reclaimable_bytes: int
    idempotency_key: str
    lock_key: str
    lock_status: ProcessLockStatus
    archive_proof_required: bool
    blocking_reasons: tuple[str, ...]
    audit_preview: SafeExecutionAuditPreview
    preview_only: bool = True
    mutation_performed: bool = False
    execute_eligible: bool = False

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash) or not _SHA256_HEX.fullmatch(self.base_preview_hash) or not _SHA256_HEX.fullmatch(self.snapshot_id):
            raise ValueError("plan and snapshot identifiers must be SHA-256 hex values")
        IdempotencyKey(self.idempotency_key)
        if self.reclaimable_bytes < 0:
            raise ValueError("reclaimable_bytes cannot be negative")
        if self.candidate_ids != tuple(target.candidate_id for target in self.targets):
            raise ValueError("candidate_ids must match target order")
        if not self.preview_only or self.mutation_performed or self.execute_eligible:
            raise ValueError("safe execution preparation must remain non-mutating")
        if self.audit_preview.plan_hash != self.plan_hash:
            raise ValueError("audit preview must bind to plan hash")

    def to_dict(self) -> dict:
        return {
            "plan_hash": self.plan_hash,
            "base_preview_hash": self.base_preview_hash,
            "snapshot_id": self.snapshot_id,
            "candidate_ids": list(self.candidate_ids),
            "candidate_count": len(self.candidate_ids),
            "targets": [item.to_dict() for item in self.targets],
            "reclaimable_bytes": self.reclaimable_bytes,
            "idempotency_key": self.idempotency_key,
            "lock_key": self.lock_key,
            "lock_status": self.lock_status.value,
            "archive_proof_required": self.archive_proof_required,
            "blocking_reasons": list(self.blocking_reasons),
            "audit_preview": self.audit_preview.to_dict(),
            "preview_only": self.preview_only,
            "mutation_performed": self.mutation_performed,
            "execute_eligible": self.execute_eligible,
        }


@dataclass(frozen=True, slots=True)
class SafeExecutionDecision:
    plan_hash: str
    snapshot_id: str
    approved: bool
    execute_eligible: bool
    confirmation_valid: bool
    snapshot_recheck_valid: bool
    lock_valid: bool
    archive_proof_valid: bool
    idempotency_valid: bool
    post_condition_ready: bool
    blocking_reasons: tuple[str, ...]
    preview_only: bool = True
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash) or not _SHA256_HEX.fullmatch(self.snapshot_id):
            raise ValueError("plan and snapshot identifiers must be SHA-256 hex values")
        if self.execute_eligible or not self.preview_only or self.mutation_performed:
            raise ValueError("decision cannot authorize or perform mutation in preparation phase")

    def to_dict(self) -> dict:
        return {
            "plan_hash": self.plan_hash,
            "snapshot_id": self.snapshot_id,
            "approved": self.approved,
            "execute_eligible": self.execute_eligible,
            "confirmation_valid": self.confirmation_valid,
            "snapshot_recheck_valid": self.snapshot_recheck_valid,
            "lock_valid": self.lock_valid,
            "archive_proof_valid": self.archive_proof_valid,
            "idempotency_valid": self.idempotency_valid,
            "post_condition_ready": self.post_condition_ready,
            "blocking_reasons": list(self.blocking_reasons),
            "preview_only": self.preview_only,
            "mutation_performed": self.mutation_performed,
        }


def _unique_candidates(candidates: Iterable[CleanupCandidate]) -> tuple[CleanupCandidate, ...]:
    ordered: list[CleanupCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.candidate_id in seen:
            raise ValueError(SafeExecutionBlockReason.DUPLICATE_CANDIDATE.value)
        seen.add(candidate.candidate_id)
        ordered.append(candidate)
    return tuple(ordered)


def _target_action(candidate: CleanupCandidate) -> SafeExecutionAction:
    if candidate.reason == "disposable_temporary_artifact":
        return SafeExecutionAction.REMOVE_DISPOSABLE_TEMP
    return SafeExecutionAction.REGENERATE_CACHE


def _is_allowlisted(candidate: CleanupCandidate) -> bool:
    parts = _relative_parts(candidate.relative_path)
    fingerprint = candidate.metadata_fingerprint
    is_leaf_file = fingerprint.get("type") == "file" and candidate.reclaimable_bytes > 0
    has_pyc_extension = candidate.relative_path.lower().replace("\\", "/").endswith(".pyc")
    is_known_cache_location = any(part in _ALLOWLISTED_DIRS for part in parts)
    is_explicit_temp = candidate.reason == "disposable_temporary_artifact" and any(part in _TEMP_DIRS for part in parts)
    is_non_executable_location = any(part in _NON_EXECUTABLE_PARTS for part in parts)
    return (
        is_leaf_file
        and not is_non_executable_location
        and candidate.category == "cache"
        and candidate.policy_class == "SAFE_AUTO"
        and not candidate.is_protected
        and candidate.governance.cleanup_eligibility is CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION
        and _redact_relative_path(candidate.relative_path) != "<protected-resource>"
        and (has_pyc_extension or is_known_cache_location or is_explicit_temp)
    )


def build_safe_execution_plan(
    recommendation: RecommendationSet,
    *,
    candidate_ids: Iterable[str] | None = None,
) -> SafeExecutionPlan:
    """Build an allowlisted plan only; no proof, lock, or mutation is performed."""
    base_preview: ExecutionPreview = build_execution_preview(recommendation, candidate_ids=candidate_ids)
    selected_ids = None if candidate_ids is None else set(candidate_ids)
    selected = tuple(item for item in recommendation.candidates if selected_ids is None or item.candidate_id in selected_ids)
    selected = _unique_candidates(selected)

    blockers: list[str] = [SafeExecutionBlockReason.NON_MUTATING_PREPARATION_ONLY.value]
    if not selected:
        blockers.append(SafeExecutionBlockReason.EMPTY_ALLOWLIST_SELECTION.value)

    targets: list[SafeExecutionTarget] = []
    for candidate in selected:
        if candidate.is_protected:
            blockers.append(SafeExecutionBlockReason.PROTECTED_RESOURCE.value)
        if candidate.policy_class != "SAFE_AUTO":
            blockers.append(SafeExecutionBlockReason.POLICY_NOT_SAFE_AUTO.value)
        if candidate.category == "unknown" or candidate.governance.owner.value == "unknown":
            blockers.append(SafeExecutionBlockReason.UNKNOWN_GOVERNANCE.value)
        if not _is_allowlisted(candidate):
            blockers.append(SafeExecutionBlockReason.NOT_ALLOWLISTED.value)
            continue
        archive_status = ArchiveProofStatus.REQUIRED_NOT_VERIFIED if candidate.rollback.required_before_execute else ArchiveProofStatus.NOT_REQUIRED
        if archive_status is ArchiveProofStatus.REQUIRED_NOT_VERIFIED:
            blockers.append(SafeExecutionBlockReason.ARCHIVE_PROOF_REQUIRED.value)
        targets.append(
            SafeExecutionTarget(
                candidate_id=candidate.candidate_id,
                relative_path=candidate.relative_path,
                action=_target_action(candidate),
                category=candidate.category,
                reclaimable_bytes=candidate.reclaimable_bytes,
                metadata_fingerprint=dict(candidate.metadata_fingerprint),
                expected_post_condition=candidate.expected_post_condition,
                archive_proof=archive_status,
                governance_eligibility=candidate.governance.cleanup_eligibility.value,
            )
        )

    if not targets:
        blockers.append(SafeExecutionBlockReason.EMPTY_ALLOWLIST_SELECTION.value)
    blockers.extend(
        (
            SafeExecutionBlockReason.EXPLICIT_USER_CONFIRMATION_REQUIRED.value,
            SafeExecutionBlockReason.FRESH_SNAPSHOT_RECHECK_REQUIRED.value,
            SafeExecutionBlockReason.PROCESS_LOCK_REQUIRED.value,
            SafeExecutionBlockReason.IDEMPOTENCY_RESERVATION_REQUIRED.value,
            SafeExecutionBlockReason.POST_CONDITION_REQUIRED.value,
        )
    )
    unique_blockers = tuple(dict.fromkeys(blockers))
    target_tuple = tuple(targets)
    plan_hash = _canonical_hash(
        {
            "schema": "phgs-safe-execution-plan-v2",
            "base_preview_hash": base_preview.plan_hash,
            "snapshot_id": base_preview.snapshot_id,
            "targets": [
                {
                    "candidate_id": target.candidate_id,
                    "action": target.action.value,
                    "category": target.category,
                    "reclaimable_bytes": target.reclaimable_bytes,
                    "metadata_fingerprint": target.metadata_fingerprint,
                    "expected_post_condition": target.expected_post_condition,
                    "archive_proof": target.archive_proof.value,
                }
                for target in target_tuple
            ],
        }
    )
    audit_id = _canonical_hash({"schema": "phgs-safe-audit-preview-v2", "plan_hash": plan_hash})[:32]
    post_condition = PostConditionPreview(
        expected_candidate_count=len(target_tuple),
        expected_reclaimable_bytes=sum(target.reclaimable_bytes for target in target_tuple),
    )
    audit = SafeExecutionAuditPreview(
        audit_id=audit_id,
        plan_hash=plan_hash,
        candidate_count=len(target_tuple),
        action="preview",
        status="planned_non_mutating",
        post_condition=post_condition,
    )
    return SafeExecutionPlan(
        plan_hash=plan_hash,
        base_preview_hash=base_preview.plan_hash,
        snapshot_id=base_preview.snapshot_id,
        candidate_ids=tuple(target.candidate_id for target in target_tuple),
        targets=target_tuple,
        reclaimable_bytes=sum(target.reclaimable_bytes for target in target_tuple),
        idempotency_key=_canonical_hash({"schema": "phgs-idempotency-v2", "plan_hash": plan_hash}),
        lock_key=f"storage-health:{base_preview.snapshot_id}",
        lock_status=ProcessLockStatus.NOT_ACQUIRED,
        archive_proof_required=any(target.archive_proof is not ArchiveProofStatus.NOT_REQUIRED for target in target_tuple),
        blocking_reasons=unique_blockers,
        audit_preview=audit,
    )


def evaluate_safe_execution(
    plan: SafeExecutionPlan,
    *,
    confirmation: ConfirmationReceipt | None = None,
    snapshot_recheck: SnapshotRecheck | None = None,
    lock_status: ProcessLockStatus = ProcessLockStatus.NOT_ACQUIRED,
    process_preflight: ProcessPreflight | None = None,
    archive_proof: ExternalArchiveShaProof | None = None,
    idempotency_reservation: IdempotencyReservation | None = None,
    post_condition_ready: bool = False,
) -> SafeExecutionDecision:
    """Evaluate gates without acquiring locks, creating proof, or mutating files."""
    blockers = list(plan.blocking_reasons)
    confirmation_valid = False
    if confirmation is None or not confirmation.approved:
        blockers.append(SafeExecutionBlockReason.EXPLICIT_USER_CONFIRMATION_REQUIRED.value)
    else:
        confirmation_valid = True
        if confirmation.plan_hash != plan.plan_hash:
            confirmation_valid = False
            blockers.append(SafeExecutionBlockReason.CONFIRMATION_PLAN_MISMATCH.value)
        if confirmation.snapshot_id != plan.snapshot_id:
            confirmation_valid = False
            blockers.append(SafeExecutionBlockReason.CONFIRMATION_SNAPSHOT_MISMATCH.value)

    snapshot_valid = snapshot_recheck is not None and snapshot_recheck.valid
    if snapshot_recheck is None:
        blockers.append(SafeExecutionBlockReason.FRESH_SNAPSHOT_RECHECK_REQUIRED.value)
    elif not snapshot_recheck.valid:
        blockers.append(SafeExecutionBlockReason.FRESH_SNAPSHOT_RECHECK_FAILED.value)
        blockers.extend(snapshot_recheck.blocking_reasons)

    effective_lock = process_preflight.lock_status if process_preflight is not None else lock_status
    lock_valid = effective_lock is ProcessLockStatus.HELD
    if effective_lock is ProcessLockStatus.CONFLICT:
        blockers.append(SafeExecutionBlockReason.PROCESS_LOCK_CONFLICT.value)
    elif not lock_valid:
        blockers.append(SafeExecutionBlockReason.PROCESS_LOCK_REQUIRED.value)
    if process_preflight is not None:
        if not process_preflight.maintenance_window_open:
            blockers.append("maintenance_window_required")
        if process_preflight.listener_pid is not None and not process_preflight.application_stopped:
            lock_valid = False
            blockers.append(SafeExecutionBlockReason.ACTIVE_PROCESS_DETECTED.value)
        if process_preflight.listener_pid is not None and not process_preflight.process_owner_verified:
            lock_valid = False
            blockers.append(SafeExecutionBlockReason.PROCESS_OWNER_UNVERIFIED.value)

    archive_valid = not plan.archive_proof_required
    if plan.archive_proof_required and archive_proof is None:
        blockers.append(SafeExecutionBlockReason.ARCHIVE_PROOF_REQUIRED.value)
    elif archive_proof is not None:
        archive_valid = True
        if archive_proof.plan_hash != plan.plan_hash:
            archive_valid = False
            blockers.append(SafeExecutionBlockReason.ARCHIVE_PROOF_PLAN_MISMATCH.value)
        if set(archive_proof.covered_candidate_ids) != set(plan.candidate_ids):
            archive_valid = False
            blockers.append(SafeExecutionBlockReason.ARCHIVE_PROOF_CANDIDATE_MISMATCH.value)

    idempotency_valid = idempotency_reservation is not None and idempotency_reservation.valid
    if idempotency_reservation is None:
        blockers.append(SafeExecutionBlockReason.IDEMPOTENCY_RESERVATION_REQUIRED.value)
    else:
        if idempotency_reservation.key.value != plan.idempotency_key:
            idempotency_valid = False
            blockers.append(SafeExecutionBlockReason.IDEMPOTENCY_PLAN_MISMATCH.value)
        if idempotency_reservation.plan_hash != plan.plan_hash:
            idempotency_valid = False
            blockers.append(SafeExecutionBlockReason.IDEMPOTENCY_PLAN_MISMATCH.value)
        if idempotency_reservation.status is IdempotencyReservationStatus.DUPLICATE:
            idempotency_valid = False
            blockers.append(SafeExecutionBlockReason.IDEMPOTENCY_ALREADY_RESERVED.value)
        elif idempotency_reservation.status is IdempotencyReservationStatus.PLAN_MISMATCH:
            idempotency_valid = False
            blockers.append(SafeExecutionBlockReason.IDEMPOTENCY_PLAN_MISMATCH.value)

    if not post_condition_ready:
        blockers.append(SafeExecutionBlockReason.POST_CONDITION_REQUIRED.value)

    unique_blockers = tuple(dict.fromkeys(blockers))
    return SafeExecutionDecision(
        plan_hash=plan.plan_hash,
        snapshot_id=plan.snapshot_id,
        approved=not unique_blockers,
        execute_eligible=False,
        confirmation_valid=confirmation_valid,
        snapshot_recheck_valid=snapshot_valid,
        lock_valid=lock_valid,
        archive_proof_valid=archive_valid,
        idempotency_valid=idempotency_valid,
        post_condition_ready=post_condition_ready,
        blocking_reasons=unique_blockers,
    )
