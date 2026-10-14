import pytest

from domain.storage_health.lifecycle import (
    ArtifactOwner,
    CleanupEligibility,
    LifecycleState,
    RetentionClass,
    can_transition,
    governance_for,
    transition_lifecycle,
)
from domain.storage_health.models import CleanupCandidate
from domain.storage_health.services.scanner import StorageObservation


@pytest.mark.unit
def test_safe_auto_gets_owner_and_explicit_confirmation_eligibility():
    governance = governance_for("cache", "SAFE_AUTO")
    assert governance.owner is ArtifactOwner.CREATING_PROCESS
    assert governance.retention_class is RetentionClass.REGENERABLE
    assert governance.cleanup_eligibility is CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION
    assert governance.owner_assigned is True
    assert governance.retention_days is None


@pytest.mark.unit
def test_protected_governance_can_never_be_cleanup_eligible():
    governance = governance_for("database", "PROTECTED")
    assert governance.owner is ArtifactOwner.RECOVERY_POLICY
    assert governance.retention_class is RetentionClass.PROTECTED
    assert governance.cleanup_eligibility is CleanupEligibility.NEVER
    assert governance.protection_level == "protected"


@pytest.mark.unit
def test_unknown_governance_has_no_owner_and_cannot_be_deleted():
    governance = governance_for("unknown", "REVIEW_REQUIRED")
    assert governance.owner is ArtifactOwner.UNKNOWN
    assert governance.owner_assigned is False
    assert governance.retention_class is RetentionClass.UNKNOWN
    assert governance.cleanup_eligibility is CleanupEligibility.NEVER


@pytest.mark.unit
def test_lifecycle_transitions_require_ordered_review_and_approval():
    assert can_transition(LifecycleState.CREATED, LifecycleState.CLASSIFIED)
    assert can_transition(LifecycleState.DELETION_CANDIDATE, LifecycleState.USER_APPROVED)
    assert not can_transition(LifecycleState.CREATED, LifecycleState.EXECUTED)
    assert transition_lifecycle(LifecycleState.CREATED, LifecycleState.CLASSIFIED) is LifecycleState.CLASSIFIED
    with pytest.raises(ValueError, match="invalid_lifecycle_transition"):
        transition_lifecycle(LifecycleState.CREATED, LifecycleState.EXECUTED)


@pytest.mark.unit
def test_candidate_payload_contains_governance_without_changing_existing_identity():
    observation = StorageObservation(
        relative_path="cache/module.pyc",
        category="cache",
        policy_class="SAFE_AUTO",
        reason="regenerable_cache",
        bytes=12,
        modified_epoch=100.0,
        is_directory=False,
    )
    candidate = CleanupCandidate.from_observation(observation, snapshot_token="a" * 64)
    payload = candidate.to_dict()
    assert payload["governance"]["owner"] == ArtifactOwner.CREATING_PROCESS.value
    assert payload["governance"]["retention_class"] == RetentionClass.REGENERABLE.value
    assert payload["governance"]["cleanup_eligibility"] == CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION.value
    assert payload["execute_eligible"] is False
    assert payload["relative_path"] == "cache/module.pyc"
