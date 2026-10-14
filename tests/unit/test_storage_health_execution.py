import hashlib
import time

import pytest

from domain.storage_health.execution import (
    ConfirmationReceipt,
    ExecutionBlockReason,
    build_execution_preview,
    evaluate_execution_decision,
)
from domain.storage_health.models import CleanupCandidate, RecommendationSet
from domain.storage_health.services.scanner import StorageObservation, StorageScan
from domain.storage_health.services.snapshot import SnapshotRecheck, build_snapshot_fingerprint


def _scan(observations, *, errors=(), truncated=False):
    category_bytes = {}
    policy_bytes = {}
    for item in observations:
        category_bytes[item.category] = category_bytes.get(item.category, 0) + item.bytes
        policy_bytes[item.policy_class] = policy_bytes.get(item.policy_class, 0) + item.bytes
    return StorageScan(
        project_root="fixture",
        scanned_at_epoch=100.0,
        observations=tuple(observations),
        category_bytes=category_bytes,
        policy_bytes=policy_bytes,
        top_consumers=tuple(observations),
        errors=tuple(errors),
        truncated=truncated,
        files_scanned=len(observations),
        directories_scanned=0,
        symlinks_skipped=0,
    )


def _recommendation(*, protected=False, errors=(), truncated=False):
    observation = StorageObservation(
        relative_path=".env" if protected else "cache/disposable.pyc",
        category="configuration" if protected else "cache",
        policy_class="PROTECTED" if protected else "SAFE_AUTO",
        reason="protected" if protected else "generated_cache",
        bytes=10,
        modified_epoch=100.0,
        is_directory=False,
    )
    scan = _scan((observation,), errors=errors, truncated=truncated)
    snapshot_id = build_snapshot_fingerprint(scan).token
    candidate = CleanupCandidate.from_observation(observation, snapshot_token=snapshot_id)
    return RecommendationSet(scan=scan, snapshot_token=snapshot_id, candidates=(candidate,))


@pytest.mark.unit
def test_preview_is_deterministic_and_always_blocked_in_recommend_phase():
    recommendation = _recommendation()
    first = build_execution_preview(recommendation)
    second = build_execution_preview(recommendation)

    assert first.to_dict() == second.to_dict()
    assert len(first.plan_hash) == 64
    assert first.preview_only is True
    assert first.mutation_performed is False
    assert ExecutionBlockReason.RECOMMEND_ONLY_PHASE.value in first.blocking_reasons

    recheck = SnapshotRecheck(valid=True, checked_count=1, blocking_reasons=())
    receipt = ConfirmationReceipt(
        approved=True,
        plan_hash=first.plan_hash,
        snapshot_id=first.snapshot_id,
        confirmed_at_epoch=time.time(),
        confirmation_id="test-confirmation",
    )
    decision = evaluate_execution_decision(
        first,
        confirmation=receipt,
        snapshot_recheck=recheck,
    )
    assert decision.approved is False
    assert decision.execute_eligible is False
    assert decision.mutation_performed is False
    assert ExecutionBlockReason.RECOMMEND_ONLY_PHASE.value in decision.blocking_reasons


@pytest.mark.unit
def test_protected_candidate_is_denied():
    preview = build_execution_preview(_recommendation(protected=True))
    assert ExecutionBlockReason.PROTECTED_RESOURCE.value in preview.blocking_reasons
    assert preview.preview_only is True


@pytest.mark.unit
def test_incomplete_scan_is_denied_even_with_valid_confirmation():
    recommendation = _recommendation(errors=("walk_error:OSError",), truncated=True)
    preview = build_execution_preview(recommendation)
    assert ExecutionBlockReason.SCAN_INCOMPLETE.value in preview.blocking_reasons

    decision = evaluate_execution_decision(
        preview,
        snapshot_recheck=SnapshotRecheck(
            valid=False,
            checked_count=1,
            blocking_reasons=("scan_truncated", "scan_errors_present"),
        ),
    )
    assert decision.approved is False
    assert ExecutionBlockReason.SNAPSHOT_RECHECK_FAILED.value in decision.blocking_reasons


@pytest.mark.unit
def test_missing_confirmation_and_plan_mismatch_are_explicitly_blocked():
    recommendation = _recommendation()
    preview = build_execution_preview(recommendation)
    recheck = SnapshotRecheck(valid=True, checked_count=1, blocking_reasons=())

    missing = evaluate_execution_decision(preview, snapshot_recheck=recheck)
    assert ExecutionBlockReason.EXPLICIT_USER_CONFIRMATION_REQUIRED.value in missing.blocking_reasons

    other_plan = hashlib.sha256(b"different-plan").hexdigest()
    receipt = ConfirmationReceipt(
        approved=True,
        plan_hash=other_plan,
        snapshot_id=preview.snapshot_id,
        confirmed_at_epoch=time.time(),
        confirmation_id="mismatch-confirmation",
    )
    mismatch = evaluate_execution_decision(
        preview,
        confirmation=receipt,
        snapshot_recheck=recheck,
    )
    assert ExecutionBlockReason.CONFIRMATION_PLAN_MISMATCH.value in mismatch.blocking_reasons
    assert mismatch.approved is False


@pytest.mark.unit
def test_duplicate_candidate_ids_are_rejected_before_preview_creation():
    recommendation = _recommendation()
    candidate = recommendation.candidates[0]
    duplicate = RecommendationSet(
        scan=recommendation.scan,
        snapshot_token=recommendation.snapshot_token,
        candidates=(candidate, candidate),
    )
    with pytest.raises(ValueError, match="duplicate_candidate"):
        build_execution_preview(duplicate)
