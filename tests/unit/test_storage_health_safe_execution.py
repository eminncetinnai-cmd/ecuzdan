from dataclasses import replace

import pytest

from domain.storage_health.execution import ConfirmationReceipt
from domain.storage_health.models import CleanupCandidate, RecommendationSet
from domain.storage_health.policy import PolicyClass
from domain.storage_health.safe_execution import (
    ExternalArchiveShaProof,
    IdempotencyKey,
    IdempotencyReservationStatus,
    InMemoryIdempotencyRegistry,
    ProcessLockStatus,
    ProcessPreflight,
    SafeExecutionAction,
    SafeExecutionBlockReason,
    build_safe_execution_plan,
    evaluate_safe_execution,
)
from domain.storage_health.services.classifier import StorageClassifier
from domain.storage_health.services.protected import ProtectedResourceDetector
from domain.storage_health.services.scanner import StorageObservation, StorageScan
from domain.storage_health.services.snapshot import (
    SnapshotRecheck,
    build_snapshot_fingerprint,
    recheck_recommendation_snapshot,
)


def _recommendation(*observations: StorageObservation, errors=(), truncated=False):
    scan = StorageScan(
        project_root="fixture",
        scanned_at_epoch=100.0,
        observations=tuple(observations),
        category_bytes={item.category: item.bytes for item in observations},
        policy_bytes={item.policy_class: item.bytes for item in observations},
        top_consumers=tuple(observations),
        errors=tuple(errors),
        truncated=truncated,
        files_scanned=len(observations),
        directories_scanned=0,
        symlinks_skipped=0,
    )
    snapshot = build_snapshot_fingerprint(scan)
    candidates = tuple(CleanupCandidate.from_observation(item, snapshot_token=snapshot.token) for item in observations)
    return RecommendationSet(scan=scan, snapshot_token=snapshot.token, candidates=candidates)


def _safe_observation(path="__pycache__/module.pyc", size=12, modified=100.0):
    return StorageObservation(path, "cache", "SAFE_AUTO", "regenerable_cache", size, modified)


@pytest.mark.unit
def test_allowlisted_cache_plan_is_deterministic_but_remains_non_mutating():
    recommendation = _recommendation(_safe_observation())
    first = build_safe_execution_plan(recommendation)
    second = build_safe_execution_plan(recommendation)
    assert first.plan_hash == second.plan_hash
    assert first.idempotency_key == second.idempotency_key
    assert len(first.targets) == 1
    assert first.targets[0].action is SafeExecutionAction.REGENERATE_CACHE
    assert first.execute_eligible is False
    assert first.mutation_performed is False
    assert first.audit_preview.mutation_performed is False
    assert first.audit_preview.post_condition.mutation_performed is False
    assert first.to_dict()["candidate_count"] == 1


@pytest.mark.unit
def test_explicit_disposable_temp_is_allowlisted_with_distinct_action():
    observation = StorageObservation("tmp/fixture.bin", "cache", "SAFE_AUTO", "disposable_temporary_artifact", 8, 100.0)
    plan = build_safe_execution_plan(_recommendation(observation))
    assert len(plan.targets) == 1
    assert plan.targets[0].action is SafeExecutionAction.REMOVE_DISPOSABLE_TEMP


@pytest.mark.unit
def test_duplicate_candidate_ids_are_rejected_before_plan_creation():
    with pytest.raises(ValueError, match="duplicate_candidate"):
        build_safe_execution_plan(_recommendation(_safe_observation(), _safe_observation()))


@pytest.mark.unit
def test_absolute_and_traversal_paths_are_not_execution_targets():
    observations = (
        StorageObservation("C:/outside/module.pyc", "cache", "SAFE_AUTO", "regenerable_cache", 12, 100.0),
        StorageObservation("../outside/module.pyc", "cache", "SAFE_AUTO", "regenerable_cache", 12, 100.0),
    )
    plan = build_safe_execution_plan(_recommendation(*observations))
    assert plan.targets == ()
    assert SafeExecutionBlockReason.NOT_ALLOWLISTED.value in plan.blocking_reasons


@pytest.mark.unit
def test_non_allowlisted_policy_and_unknown_are_excluded_from_targets():
    observations = (
        StorageObservation("reports/output.txt", "reports", "SAFE_WITH_CONFIRMATION", "retained_report_or_evidence_review", 20, 100.0),
        StorageObservation("misc/data.bin", "unknown", "REVIEW_REQUIRED", "unclassified_resource", 20, 100.0),
    )
    plan = build_safe_execution_plan(_recommendation(*observations))
    assert plan.targets == ()
    assert SafeExecutionBlockReason.NOT_ALLOWLISTED.value in plan.blocking_reasons
    assert SafeExecutionBlockReason.POLICY_NOT_SAFE_AUTO.value in plan.blocking_reasons
    assert SafeExecutionBlockReason.UNKNOWN_GOVERNANCE.value in plan.blocking_reasons


@pytest.mark.unit
def test_root_config_tree_is_protected_and_never_a_safe_target(tmp_path):
    detector = ProtectedResourceDetector(tmp_path)
    policy, reason = detector.explain(tmp_path / "config" / "demo_data.yaml")
    assert policy is PolicyClass.PROTECTED
    assert reason == "canonical_application_tree"
    observation = StorageObservation("config/demo_data.yaml", "cache", "PROTECTED", "canonical_application_tree", 100, 100.0)
    plan = build_safe_execution_plan(_recommendation(observation))
    assert plan.targets == ()
    assert SafeExecutionBlockReason.PROTECTED_RESOURCE.value in plan.blocking_reasons


@pytest.mark.unit
def test_runtime_source_and_oauth_named_artifacts_are_protected_and_not_safe_targets(tmp_path):
    detector = ProtectedResourceDetector(tmp_path)
    expected_reasons = {
        "utils/ref_cache.py": "canonical_application_tree",
        "instance/live_data_cache.json": "canonical_application_tree",
        ".coveragerc_oauth": "sensitive_or_credential_name",
        ".env.example": "root_control_or_configuration",
        ".gitignore": "root_control_or_configuration",
        "pyproject.toml": "root_control_or_configuration",
        "pytest.ini": "root_control_or_configuration",
        "docker-compose.logging.yml": "root_control_or_configuration",
    }
    for relative_path, expected_reason in expected_reasons.items():
        policy, reason = detector.explain(tmp_path / relative_path)
        assert policy is PolicyClass.PROTECTED
        assert reason == expected_reason
        observation = StorageObservation(relative_path, "cache", "PROTECTED", expected_reason, 10, 100.0)
        plan = build_safe_execution_plan(_recommendation(observation))
        assert plan.targets == ()
        assert SafeExecutionBlockReason.PROTECTED_RESOURCE.value in plan.blocking_reasons
        assert SafeExecutionBlockReason.NOT_ALLOWLISTED.value in plan.blocking_reasons


@pytest.mark.unit
def test_security_and_audit_logs_are_review_required_and_never_safe_auto(tmp_path):
    classifier = StorageClassifier(tmp_path)
    for relative_path in ("logs/e_cuzdan_security.log", "logs/audit.log", "audit/security.log"):
        category, policy, reason = classifier.classify(tmp_path / relative_path)
        assert category == "logs"
        assert policy is PolicyClass.REVIEW_REQUIRED
        assert reason == "security_audit_log_retention_review"


@pytest.mark.unit
def test_protected_candidate_is_blocked_even_if_manually_present():
    observation = StorageObservation("e_cuzdan_v15.db", "database", "PROTECTED", "active_sqlite_anchor", 100, 100.0)
    plan = build_safe_execution_plan(_recommendation(observation))
    assert plan.targets == ()
    assert SafeExecutionBlockReason.PROTECTED_RESOURCE.value in plan.blocking_reasons
    assert SafeExecutionBlockReason.NOT_ALLOWLISTED.value in plan.blocking_reasons


@pytest.mark.unit
def test_wrong_extension_directory_and_zero_byte_targets_are_rejected():
    wrong_extension = StorageObservation("cache/state.txt", "cache", "SAFE_AUTO", "regenerable_cache", 12, 100.0)
    directory = StorageObservation("__pycache__", "cache", "SAFE_AUTO", "regenerable_cache", 12, 100.0, True)
    zero_byte = StorageObservation("__pycache__/empty.pyc", "cache", "SAFE_AUTO", "regenerable_cache", 0, 100.0)
    plan = build_safe_execution_plan(_recommendation(wrong_extension, directory, zero_byte))
    assert plan.targets == ()
    assert SafeExecutionBlockReason.NOT_ALLOWLISTED.value in plan.blocking_reasons


@pytest.mark.unit
def test_incomplete_scan_and_missing_gates_cannot_produce_approval():
    recommendation = _recommendation(_safe_observation(), errors=("walk_error:OSError",), truncated=True)
    plan = build_safe_execution_plan(recommendation)
    decision = evaluate_safe_execution(plan)
    assert decision.approved is False
    assert decision.execute_eligible is False
    assert decision.preview_only is True
    assert decision.mutation_performed is False
    assert SafeExecutionBlockReason.FRESH_SNAPSHOT_RECHECK_REQUIRED.value in decision.blocking_reasons
    assert SafeExecutionBlockReason.IDEMPOTENCY_RESERVATION_REQUIRED.value in decision.blocking_reasons


@pytest.mark.unit
def test_fresh_recheck_rejects_changed_and_missing_file_metadata(tmp_path):
    target = tmp_path / "__pycache__" / "module.pyc"
    target.parent.mkdir()
    target.write_bytes(b"fixture")
    observation = StorageObservation(
        "__pycache__/module.pyc",
        "cache",
        "SAFE_AUTO",
        "regenerable_cache",
        target.stat().st_size,
        target.stat().st_mtime,
    )
    scan = StorageScan(
        project_root=str(tmp_path),
        scanned_at_epoch=100.0,
        observations=(observation,),
        category_bytes={"cache": observation.bytes},
        policy_bytes={"SAFE_AUTO": observation.bytes},
        top_consumers=(observation,),
        errors=(),
        truncated=False,
        files_scanned=1,
        directories_scanned=1,
        symlinks_skipped=0,
    )
    target.write_bytes(b"changed-fixture")
    changed = recheck_recommendation_snapshot(str(tmp_path), scan, (observation,))
    assert changed.valid is False
    assert "size_changed" in changed.blocking_reasons
    target.unlink()
    missing = recheck_recommendation_snapshot(str(tmp_path), scan, (observation,))
    assert missing.valid is False
    assert "missing_or_reparse_or_unsupported_resource" in missing.blocking_reasons


@pytest.mark.unit
def test_confirmation_mismatch_changed_recheck_and_lock_conflict_are_blockers():
    recommendation = _recommendation(_safe_observation())
    plan = build_safe_execution_plan(recommendation)
    wrong_confirmation = ConfirmationReceipt(True, "b" * 64, plan.snapshot_id, 100.0, "confirmation-1")
    changed_recheck = SnapshotRecheck(False, 1, ("size_changed", "missing_or_reparse_or_unsupported_resource"))
    decision = evaluate_safe_execution(
        plan,
        confirmation=wrong_confirmation,
        snapshot_recheck=changed_recheck,
        process_preflight=ProcessPreflight(5000, 38720, True, False, True, ProcessLockStatus.CONFLICT),
    )
    assert decision.approved is False
    assert decision.confirmation_valid is False
    assert decision.snapshot_recheck_valid is False
    assert decision.lock_valid is False
    assert SafeExecutionBlockReason.CONFIRMATION_PLAN_MISMATCH.value in decision.blocking_reasons
    assert SafeExecutionBlockReason.FRESH_SNAPSHOT_RECHECK_FAILED.value in decision.blocking_reasons
    assert SafeExecutionBlockReason.PROCESS_LOCK_CONFLICT.value in decision.blocking_reasons
    assert SafeExecutionBlockReason.ACTIVE_PROCESS_DETECTED.value in decision.blocking_reasons


@pytest.mark.unit
def test_archive_proof_is_external_and_plan_bound():
    recommendation = _recommendation(_safe_observation())
    plan = replace(build_safe_execution_plan(recommendation), archive_proof_required=True)
    decision = evaluate_safe_execution(plan, snapshot_recheck=SnapshotRecheck(True, 1, ()))
    assert decision.archive_proof_valid is False
    assert SafeExecutionBlockReason.ARCHIVE_PROOF_REQUIRED.value in decision.blocking_reasons

    mismatched_proof = ExternalArchiveShaProof(
        plan_hash="c" * 64,
        covered_candidate_ids=plan.candidate_ids,
        external_archive_ref="external://approved/archive-1",
        archive_sha256="d" * 64,
        archived_bytes=12,
        verified_at_epoch=100.0,
    )
    decision = evaluate_safe_execution(plan, archive_proof=mismatched_proof, snapshot_recheck=SnapshotRecheck(True, 1, ()))
    assert decision.archive_proof_valid is False
    assert SafeExecutionBlockReason.ARCHIVE_PROOF_PLAN_MISMATCH.value in decision.blocking_reasons


@pytest.mark.unit
def test_idempotency_key_validation_and_memory_only_reservation_semantics():
    with pytest.raises(ValueError, match="invalid idempotency key"):
        IdempotencyKey("short")
    recommendation = _recommendation(_safe_observation())
    plan = build_safe_execution_plan(recommendation)
    registry = InMemoryIdempotencyRegistry()
    accepted = registry.reserve(plan.idempotency_key, plan.plan_hash)
    duplicate = registry.reserve(plan.idempotency_key, plan.plan_hash)
    mismatch = registry.reserve(plan.idempotency_key, "e" * 64)
    assert accepted.status is IdempotencyReservationStatus.ACCEPTED
    assert duplicate.status is IdempotencyReservationStatus.DUPLICATE
    assert mismatch.status is IdempotencyReservationStatus.PLAN_MISMATCH


@pytest.mark.unit
def test_process_preflight_requires_stopped_owner_verified_process_and_held_lock():
    conflict = ProcessPreflight(5000, 38720, False, False, True, ProcessLockStatus.CONFLICT)
    assert conflict.safe_for_preparation is False
    plan = build_safe_execution_plan(_recommendation(_safe_observation()))
    decision = evaluate_safe_execution(plan, process_preflight=conflict, snapshot_recheck=SnapshotRecheck(True, 1, ()))
    assert decision.lock_valid is False
    assert SafeExecutionBlockReason.PROCESS_LOCK_CONFLICT.value in decision.blocking_reasons
    assert SafeExecutionBlockReason.ACTIVE_PROCESS_DETECTED.value in decision.blocking_reasons
    assert SafeExecutionBlockReason.PROCESS_OWNER_UNVERIFIED.value in decision.blocking_reasons


@pytest.mark.unit
def test_full_gate_inputs_still_cannot_authorize_or_mutate_in_preparation_phase():
    recommendation = _recommendation(_safe_observation())
    plan = build_safe_execution_plan(recommendation)
    confirmation = ConfirmationReceipt(True, plan.plan_hash, plan.snapshot_id, 100.0, "confirmation-2")
    registry = InMemoryIdempotencyRegistry()
    reservation = registry.reserve(plan.idempotency_key, plan.plan_hash)
    decision = evaluate_safe_execution(
        plan,
        confirmation=confirmation,
        snapshot_recheck=SnapshotRecheck(True, 1, ()),
        process_preflight=ProcessPreflight(5000, None, True, True, True, ProcessLockStatus.HELD),
        idempotency_reservation=reservation,
        post_condition_ready=True,
    )
    assert decision.confirmation_valid is True
    assert decision.snapshot_recheck_valid is True
    assert decision.lock_valid is True
    assert decision.idempotency_valid is True
    assert decision.post_condition_ready is True
    assert decision.approved is False
    assert decision.execute_eligible is False
    assert decision.mutation_performed is False
