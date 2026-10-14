"""Non-mutating execution preview and approval gates.

This module deliberately does not delete, move, archive, hash, or open files.
It creates a deterministic plan and explains why a future Execute phase remains
blocked until every independent safety gate is satisfied.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from domain.storage_health.models import CleanupCandidate, RecommendationSet
from domain.storage_health.services.snapshot import SnapshotRecheck

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class ExecutionBlockReason(StrEnum):
    RECOMMEND_ONLY_PHASE = "recommend_only_phase"
    EXPLICIT_USER_CONFIRMATION_REQUIRED = "explicit_user_confirmation_required"
    CONFIRMATION_PLAN_MISMATCH = "confirmation_plan_mismatch"
    CONFIRMATION_SNAPSHOT_MISMATCH = "confirmation_snapshot_mismatch"
    SNAPSHOT_RECHECK_REQUIRED = "snapshot_recheck_required"
    SNAPSHOT_RECHECK_FAILED = "snapshot_recheck_failed"
    SCAN_INCOMPLETE = "scan_incomplete"
    PROTECTED_RESOURCE = "protected_resource"
    POLICY_REVIEW_REQUIRED = "policy_review_required"
    MAINTENANCE_WINDOW_REQUIRED = "maintenance_window_required"
    EMPTY_CANDIDATE_SELECTION = "empty_candidate_selection"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    INVALID_SNAPSHOT_ID = "invalid_snapshot_id"


@dataclass(frozen=True, slots=True)
class ConfirmationReceipt:
    """Opaque confirmation receipt; no user identity, secret or raw token is stored."""

    approved: bool
    plan_hash: str
    snapshot_id: str
    confirmed_at_epoch: float
    confirmation_id: str

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash):
            raise ValueError("plan_hash must be a 64-character lowercase SHA-256 hex value")
        if not _SHA256_HEX.fullmatch(self.snapshot_id):
            raise ValueError("snapshot_id must be a 64-character lowercase SHA-256 hex value")
        if self.confirmed_at_epoch < 0:
            raise ValueError("confirmed_at_epoch cannot be negative")
        if not self.confirmation_id or len(self.confirmation_id) > 128:
            raise ValueError("confirmation_id must be a bounded opaque identifier")

    def to_dict(self) -> dict:
        return {
            "approved": self.approved,
            "plan_hash": self.plan_hash,
            "snapshot_id": self.snapshot_id,
            "confirmed_at_epoch": self.confirmed_at_epoch,
            "confirmation_id": self.confirmation_id,
        }


@dataclass(frozen=True, slots=True)
class ExecutionPreview:
    """Deterministic plan only; it is not an authorization to mutate."""

    plan_hash: str
    snapshot_id: str
    candidate_ids: tuple[str, ...]
    candidate_count: int
    reclaimable_bytes: int
    risk_levels: tuple[str, ...]
    rollback_strategies: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    confirmation_required: bool
    maintenance_window_required: bool
    archive_required: bool
    preview_only: bool = True
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash):
            raise ValueError("plan_hash must be a 64-character lowercase SHA-256 hex value")
        if not _SHA256_HEX.fullmatch(self.snapshot_id):
            raise ValueError("snapshot_id must be a 64-character lowercase SHA-256 hex value")
        if self.candidate_count != len(self.candidate_ids):
            raise ValueError("candidate_count must match candidate_ids")
        if self.reclaimable_bytes < 0:
            raise ValueError("reclaimable_bytes cannot be negative")
        if not self.preview_only or self.mutation_performed:
            raise ValueError("execution preview must remain non-mutating")

    def to_dict(self) -> dict:
        return {
            "plan_hash": self.plan_hash,
            "snapshot_id": self.snapshot_id,
            "candidate_ids": list(self.candidate_ids),
            "candidate_count": self.candidate_count,
            "reclaimable_bytes": self.reclaimable_bytes,
            "risk_levels": list(self.risk_levels),
            "rollback_strategies": list(self.rollback_strategies),
            "blocking_reasons": list(self.blocking_reasons),
            "confirmation_required": self.confirmation_required,
            "maintenance_window_required": self.maintenance_window_required,
            "archive_required": self.archive_required,
            "preview_only": self.preview_only,
            "mutation_performed": self.mutation_performed,
        }


@dataclass(frozen=True, slots=True)
class ExecutionDecision:
    """Gate result. It never authorizes a mutation in the current phase."""

    plan_hash: str
    snapshot_id: str
    approved: bool
    execute_eligible: bool
    blocking_reasons: tuple[str, ...]
    confirmation_valid: bool
    snapshot_recheck_valid: bool
    maintenance_window_valid: bool
    preview_only: bool = True
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not _SHA256_HEX.fullmatch(self.plan_hash):
            raise ValueError("plan_hash must be a 64-character lowercase SHA-256 hex value")
        if not _SHA256_HEX.fullmatch(self.snapshot_id):
            raise ValueError("snapshot_id must be a 64-character lowercase SHA-256 hex value")
        if self.execute_eligible or not self.preview_only or self.mutation_performed:
            raise ValueError("current Execute gate cannot authorize or perform mutation")

    def to_dict(self) -> dict:
        return {
            "plan_hash": self.plan_hash,
            "snapshot_id": self.snapshot_id,
            "approved": self.approved,
            "execute_eligible": self.execute_eligible,
            "blocking_reasons": list(self.blocking_reasons),
            "confirmation_valid": self.confirmation_valid,
            "snapshot_recheck_valid": self.snapshot_recheck_valid,
            "maintenance_window_valid": self.maintenance_window_valid,
            "preview_only": self.preview_only,
            "mutation_performed": self.mutation_performed,
        }


def _canonical_plan_payload(snapshot_id: str, candidates: tuple[CleanupCandidate, ...]) -> bytes:
    payload = {
        "schema": "storage-health-execution-preview-v1",
        "snapshot_id": snapshot_id,
        "candidates": [
            {
                "candidate_id": item.candidate_id,
                "category": item.category,
                "policy_class": item.policy_class,
                "reclaimable_bytes": item.reclaimable_bytes,
                "risk_level": item.risk_level.value,
                "rollback_strategy": item.rollback.kind.value,
                "metadata_fingerprint": dict(item.metadata_fingerprint),
                "is_protected": item.is_protected,
            }
            for item in candidates
        ],
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _plan_hash(snapshot_id: str, candidates: tuple[CleanupCandidate, ...]) -> str:
    return hashlib.sha256(_canonical_plan_payload(snapshot_id, candidates)).hexdigest()


def _unique_candidates(candidates: Iterable[CleanupCandidate]) -> tuple[CleanupCandidate, ...]:
    ordered: list[CleanupCandidate] = []
    seen: set[str] = set()
    for item in candidates:
        if item.candidate_id in seen:
            raise ValueError(ExecutionBlockReason.DUPLICATE_CANDIDATE.value)
        seen.add(item.candidate_id)
        ordered.append(item)
    return tuple(ordered)


def build_execution_preview(
    recommendation: RecommendationSet,
    *,
    candidate_ids: Iterable[str] | None = None,
) -> ExecutionPreview:
    """Build a plan from recommendations without touching the filesystem."""
    snapshot_id = recommendation.snapshot_token
    if not _SHA256_HEX.fullmatch(snapshot_id):
        raise ValueError(ExecutionBlockReason.INVALID_SNAPSHOT_ID.value)

    selected_ids = None if candidate_ids is None else set(candidate_ids)
    candidates = tuple(
        item for item in recommendation.candidates
        if selected_ids is None or item.candidate_id in selected_ids
    )
    candidates = _unique_candidates(candidates)
    blockers: list[str] = [ExecutionBlockReason.RECOMMEND_ONLY_PHASE.value]
    if recommendation.scan.truncated or recommendation.scan.errors:
        blockers.append(ExecutionBlockReason.SCAN_INCOMPLETE.value)
    if not candidates:
        blockers.append(ExecutionBlockReason.EMPTY_CANDIDATE_SELECTION.value)

    for item in candidates:
        if item.is_protected:
            blockers.append(ExecutionBlockReason.PROTECTED_RESOURCE.value)
        if item.review_required or not item.eligible_for_safe_cleanup:
            blockers.append(ExecutionBlockReason.POLICY_REVIEW_REQUIRED.value)
        if item.maintenance_window_required:
            blockers.append(ExecutionBlockReason.MAINTENANCE_WINDOW_REQUIRED.value)

    unique_blockers = tuple(dict.fromkeys(blockers))
    plan_hash = _plan_hash(snapshot_id, candidates)
    return ExecutionPreview(
        plan_hash=plan_hash,
        snapshot_id=snapshot_id,
        candidate_ids=tuple(item.candidate_id for item in candidates),
        candidate_count=len(candidates),
        reclaimable_bytes=sum(item.reclaimable_bytes for item in candidates),
        risk_levels=tuple(sorted({item.risk_level.value for item in candidates})),
        rollback_strategies=tuple(sorted({item.rollback.kind.value for item in candidates})),
        blocking_reasons=unique_blockers,
        confirmation_required=True,
        maintenance_window_required=any(item.maintenance_window_required for item in candidates),
        archive_required=any(item.rollback.required_before_execute for item in candidates),
    )


def evaluate_execution_decision(
    preview: ExecutionPreview,
    *,
    confirmation: ConfirmationReceipt | None = None,
    snapshot_recheck: SnapshotRecheck | None = None,
    maintenance_window_open: bool = False,
) -> ExecutionDecision:
    """Evaluate gates and always return a non-authorizing decision in this phase."""
    blockers = list(preview.blocking_reasons)
    confirmation_valid = False
    if confirmation is None or not confirmation.approved:
        blockers.append(ExecutionBlockReason.EXPLICIT_USER_CONFIRMATION_REQUIRED.value)
    else:
        confirmation_valid = True
        if confirmation.plan_hash != preview.plan_hash:
            confirmation_valid = False
            blockers.append(ExecutionBlockReason.CONFIRMATION_PLAN_MISMATCH.value)
        if confirmation.snapshot_id != preview.snapshot_id:
            confirmation_valid = False
            blockers.append(ExecutionBlockReason.CONFIRMATION_SNAPSHOT_MISMATCH.value)

    snapshot_valid = snapshot_recheck is not None and snapshot_recheck.valid
    if snapshot_recheck is None:
        blockers.append(ExecutionBlockReason.SNAPSHOT_RECHECK_REQUIRED.value)
    elif not snapshot_recheck.valid:
        blockers.append(ExecutionBlockReason.SNAPSHOT_RECHECK_FAILED.value)
        blockers.extend(snapshot_recheck.blocking_reasons)

    maintenance_valid = not preview.maintenance_window_required or maintenance_window_open
    if not maintenance_valid:
        blockers.append(ExecutionBlockReason.MAINTENANCE_WINDOW_REQUIRED.value)

    unique_blockers = tuple(dict.fromkeys(blockers))
    return ExecutionDecision(
        plan_hash=preview.plan_hash,
        snapshot_id=preview.snapshot_id,
        approved=(
            not unique_blockers
            and confirmation_valid
            and snapshot_valid
            and maintenance_valid
        ),
        execute_eligible=False,
        blocking_reasons=unique_blockers,
        confirmation_valid=confirmation_valid,
        snapshot_recheck_valid=snapshot_valid,
        maintenance_window_valid=maintenance_valid,
    )
