from dataclasses import replace

import pytest

from domain.storage_health.models import CleanupCandidate, RiskLevel, RollbackKind
from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.recommender import StorageRecommender
from domain.storage_health.services.scanner import StorageScanner
from domain.storage_health.services.snapshot import (
    build_snapshot_fingerprint,
    observation_matches_snapshot,
    recheck_recommendation_snapshot,
)


@pytest.fixture
def recommendation_fixture(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "module.pyc").write_bytes(b"cache")
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "transient.tmp").write_bytes(b"tmp")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "application.log").write_bytes(b"log")
    (tmp_path / "backups").mkdir()
    (tmp_path / "backups" / "old.zip").write_bytes(b"backup")
    (tmp_path / "configuration").mkdir()
    (tmp_path / "configuration" / "requirements.txt").write_bytes(b"protected config")
    return tmp_path


@pytest.mark.unit
def test_recommender_emits_leaf_candidates_only_and_never_protected(recommendation_fixture):
    scan = StorageScanner(recommendation_fixture, max_files=100, max_seconds=5).scan()
    result = StorageRecommender(recommendation_fixture).recommend(scan)
    paths = {item.relative_path for item in result.candidates}

    assert "__pycache__/module.pyc" in paths
    assert "tmp/transient.tmp" in paths
    assert "logs/application.log" in paths
    assert "backups/old.zip" in paths
    assert "configuration/requirements.txt" not in paths
    assert all("/" not in item.relative_path or not item.relative_path.endswith("/") for item in result.candidates)
    assert all(item.execute_eligible is False for item in result.candidates)
    assert all(item.user_confirmation_required for item in result.candidates)


@pytest.mark.unit
def test_risk_and_rollback_mapping_is_explicit(recommendation_fixture):
    scan = StorageScanner(recommendation_fixture, max_files=100, max_seconds=5).scan()
    result = StorageRecommender(recommendation_fixture).recommend(scan)
    by_path = {item.relative_path: item for item in result.candidates}

    assert by_path["__pycache__/module.pyc"].risk_level == RiskLevel.LOW
    assert by_path["__pycache__/module.pyc"].rollback.kind == RollbackKind.REGENERATE
    assert by_path["logs/application.log"].risk_level == RiskLevel.MEDIUM
    assert by_path["logs/application.log"].rollback.kind == RollbackKind.ARCHIVE_THEN_DELETE
    assert by_path["backups/old.zip"].risk_level == RiskLevel.HIGH
    assert by_path["backups/old.zip"].rollback.kind == RollbackKind.MANUAL_REVIEW
    assert "explicit_user_confirmation_required" in by_path["logs/application.log"].blocking_reasons


@pytest.mark.unit
def test_snapshot_token_is_deterministic_and_uses_metadata_only(recommendation_fixture):
    first = StorageScanner(recommendation_fixture, max_files=100, max_seconds=5).scan()
    second = StorageScanner(recommendation_fixture, max_files=100, max_seconds=5).scan()

    first_token = build_snapshot_fingerprint(first).token
    second_token = build_snapshot_fingerprint(second).token
    assert first_token == second_token
    assert len(first_token) == 64


@pytest.mark.unit
def test_snapshot_recheck_rejects_changed_type_absolute_and_traversal(recommendation_fixture):
    scan = StorageScanner(recommendation_fixture, max_files=100, max_seconds=5).scan()
    observation = next(item for item in scan.observations if item.relative_path == "tmp/transient.tmp")

    assert observation_matches_snapshot(recommendation_fixture, observation)
    assert not observation_matches_snapshot(
        recommendation_fixture,
        replace(observation, is_directory=True),
    )
    assert not observation_matches_snapshot(
        recommendation_fixture,
        replace(observation, relative_path=str(recommendation_fixture / "tmp" / "transient.tmp")),
    )
    assert not observation_matches_snapshot(
        recommendation_fixture,
        replace(observation, relative_path="../outside.tmp"),
    )


@pytest.mark.unit
def test_snapshot_recheck_rejects_protected_policy_errors_and_truncation(recommendation_fixture):
    scan = StorageScanner(recommendation_fixture, max_files=100, max_seconds=5).scan()
    observation = next(item for item in scan.observations if item.relative_path == "tmp/transient.tmp")

    protected = replace(observation, policy_class=PolicyClass.PROTECTED.value)
    protected_result = recheck_recommendation_snapshot(recommendation_fixture, scan, (protected,))
    assert protected_result.valid is False
    assert "protected_policy" in protected_result.blocking_reasons

    truncated_result = recheck_recommendation_snapshot(
        recommendation_fixture,
        replace(scan, truncated=True),
        (observation,),
    )
    assert truncated_result.valid is False
    assert "scan_truncated" in truncated_result.blocking_reasons

    error_result = recheck_recommendation_snapshot(
        recommendation_fixture,
        replace(scan, errors=("walk_error:PermissionError",)),
        (observation,),
    )
    assert error_result.valid is False
    assert "scan_errors_present" in error_result.blocking_reasons


@pytest.mark.unit
def test_candidate_dto_redacts_sensitive_relative_path():
    from domain.storage_health.services.scanner import StorageObservation

    observation = StorageObservation(
        relative_path="reports/oauth_client_secret.json",
        category="reports",
        policy_class=PolicyClass.SAFE_WITH_CONFIRMATION.value,
        reason="retained_report_or_evidence_review",
        bytes=12,
        modified_epoch=None,
    )
    dto = CleanupCandidate.from_observation(observation, snapshot_token="a" * 64).to_dict()
    assert dto["relative_path"] == "<protected-resource>"
    assert dto["execute_eligible"] is False
    assert dto["metadata_fingerprint"]["type"] == "file"
