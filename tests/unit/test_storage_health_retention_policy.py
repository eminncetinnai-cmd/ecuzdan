import pytest

from domain.storage_health.lifecycle import ArtifactOwner, CleanupEligibility, RetentionClass
from domain.storage_health.retention_policy import (
    RetentionDecision,
    RetentionPolicy,
    evaluate_retention,
    security_audit_log_policy,
)


@pytest.mark.unit
def test_security_audit_policy_is_fail_closed():
    policy = security_audit_log_policy()
    assert policy.owner is ArtifactOwner.SECURITY
    assert policy.retention_class is RetentionClass.OWNER_POLICY_REQUIRED
    assert policy.retention_days is None
    assert policy.hold_active is True
    assert policy.owner_approved is False


@pytest.mark.unit
def test_security_audit_policy_evaluates_to_hold_without_mutation():
    evaluation = evaluate_retention(security_audit_log_policy())
    assert evaluation.decision is RetentionDecision.HOLD
    assert evaluation.cleanup_eligibility is CleanupEligibility.NEVER
    assert evaluation.mutation_performed is False
    assert evaluation.retention_days is None


@pytest.mark.unit
def test_unknown_owner_is_never_cleanup_eligible():
    policy = RetentionPolicy(
        policy_id='unknown-owner',
        owner=ArtifactOwner.UNKNOWN,
        purpose='unclassified audit artifact',
        retention_class=RetentionClass.UNKNOWN,
    )
    evaluation = evaluate_retention(policy)
    assert evaluation.decision is RetentionDecision.OWNER_POLICY_REQUIRED
    assert evaluation.cleanup_eligibility is CleanupEligibility.NEVER


@pytest.mark.unit
def test_numeric_period_is_required_before_disposal_evaluation():
    policy = RetentionPolicy(
        policy_id='security-review',
        owner=ArtifactOwner.SECURITY,
        purpose='security audit review',
        retention_class=RetentionClass.OWNER_POLICY_REQUIRED,
        owner_approved=True,
    )
    evaluation = evaluate_retention(policy, retention_elapsed=True)
    assert evaluation.decision is RetentionDecision.OWNER_POLICY_REQUIRED
    assert evaluation.reason == 'numeric_retention_period_not_assigned'
    assert evaluation.cleanup_eligibility is CleanupEligibility.NEVER


@pytest.mark.unit
def test_owner_approval_is_required_after_numeric_period_is_assigned():
    policy = RetentionPolicy(
        policy_id='owner-review',
        owner=ArtifactOwner.SECURITY,
        purpose='security audit review',
        retention_class=RetentionClass.REVIEW_BEFORE_DELETE,
        retention_days=90,
    )
    evaluation = evaluate_retention(policy, retention_elapsed=True)
    assert evaluation.decision is RetentionDecision.REVIEW_REQUIRED
    assert evaluation.cleanup_eligibility is CleanupEligibility.REVIEW_BEFORE_DELETE


@pytest.mark.unit
def test_not_elapsed_policy_is_retained():
    policy = RetentionPolicy(
        policy_id='active-policy',
        owner=ArtifactOwner.SECURITY,
        purpose='security audit review',
        retention_class=RetentionClass.REVIEW_BEFORE_DELETE,
        retention_days=90,
        owner_approved=True,
    )
    evaluation = evaluate_retention(policy, retention_elapsed=False)
    assert evaluation.decision is RetentionDecision.RETAIN
    assert evaluation.cleanup_eligibility is CleanupEligibility.REVIEW_BEFORE_DELETE


@pytest.mark.unit
def test_elapsed_and_approved_policy_becomes_confirmation_candidate_only():
    policy = RetentionPolicy(
        policy_id='expired-policy',
        owner=ArtifactOwner.SECURITY,
        purpose='security audit review',
        retention_class=RetentionClass.REVIEW_BEFORE_DELETE,
        retention_days=90,
        owner_approved=True,
    )
    evaluation = evaluate_retention(policy, retention_elapsed=True)
    assert evaluation.decision is RetentionDecision.DISPOSAL_ELIGIBLE
    assert evaluation.cleanup_eligibility is CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION
    assert evaluation.mutation_performed is False


@pytest.mark.unit
def test_invalid_policy_values_are_rejected():
    with pytest.raises(ValueError):
        RetentionPolicy(
            policy_id='',
            owner=ArtifactOwner.SECURITY,
            purpose='audit',
            retention_class=RetentionClass.OWNER_POLICY_REQUIRED,
        )
    with pytest.raises(ValueError):
        RetentionPolicy(
            policy_id='negative',
            owner=ArtifactOwner.SECURITY,
            purpose='audit',
            retention_class=RetentionClass.REVIEW_BEFORE_DELETE,
            retention_days=-1,
        )
    with pytest.raises(ValueError):
        RetentionPolicy(
            policy_id='hold-without-reason',
            owner=ArtifactOwner.SECURITY,
            purpose='audit',
            retention_class=RetentionClass.OWNER_POLICY_REQUIRED,
            hold_active=True,
        )
