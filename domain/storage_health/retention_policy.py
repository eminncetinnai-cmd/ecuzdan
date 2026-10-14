"""Read-only retention policy contracts for security and audit artifacts.

The module does not delete, archive, mutate files, or persist policy decisions.
Numeric retention remains unset until an owner-approved policy assigns it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from domain.storage_health.lifecycle import (
    ArtifactOwner,
    CleanupEligibility,
    RetentionClass,
)


class RetentionDecision(StrEnum):
    """Read-only result of evaluating retention prerequisites."""

    HOLD = "hold"
    OWNER_POLICY_REQUIRED = "owner_policy_required"
    RETAIN = "retain"
    REVIEW_REQUIRED = "review_required"
    DISPOSAL_ELIGIBLE = "disposal_eligible"


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Owner- and purpose-bound retention policy without mutation authority."""

    policy_id: str
    owner: ArtifactOwner
    purpose: str
    retention_class: RetentionClass
    retention_days: int | None = None
    hold_active: bool = False
    hold_reason: str | None = None
    owner_approved: bool = False
    source: str = "owner_policy_pending"

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id cannot be empty")
        if not self.purpose.strip():
            raise ValueError("purpose cannot be empty")
        if self.retention_days is not None and self.retention_days < 0:
            raise ValueError("retention_days cannot be negative")
        if self.hold_active and not self.hold_reason:
            raise ValueError("active hold requires hold_reason")
        if self.owner is ArtifactOwner.UNKNOWN and self.owner_approved:
            raise ValueError("unknown owner cannot approve a retention policy")
        if self.retention_class is RetentionClass.PROTECTED and self.retention_days is not None:
            raise ValueError("protected policy cannot carry a disposal period")

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "owner": self.owner.value,
            "purpose": self.purpose,
            "retention_class": self.retention_class.value,
            "retention_days": self.retention_days,
            "hold_active": self.hold_active,
            "hold_reason": self.hold_reason,
            "owner_approved": self.owner_approved,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class RetentionEvaluation:
    """Read-only retention decision and cleanup eligibility explanation."""

    decision: RetentionDecision
    cleanup_eligibility: CleanupEligibility
    reason: str
    retention_days: int | None
    mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.mutation_performed:
            raise ValueError("retention evaluation must remain read-only")

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision.value,
            "cleanup_eligibility": self.cleanup_eligibility.value,
            "reason": self.reason,
            "retention_days": self.retention_days,
            "mutation_performed": self.mutation_performed,
        }


def evaluate_retention(
    policy: RetentionPolicy,
    *,
    retention_elapsed: bool = False,
) -> RetentionEvaluation:
    """Evaluate retention prerequisites without reading or mutating an artifact."""
    if policy.hold_active:
        return RetentionEvaluation(
            decision=RetentionDecision.HOLD,
            cleanup_eligibility=CleanupEligibility.NEVER,
            reason=policy.hold_reason or "retention_hold_active",
            retention_days=policy.retention_days,
        )

    if policy.owner is ArtifactOwner.UNKNOWN:
        return RetentionEvaluation(
            decision=RetentionDecision.OWNER_POLICY_REQUIRED,
            cleanup_eligibility=CleanupEligibility.NEVER,
            reason="unknown_owner",
            retention_days=policy.retention_days,
        )

    if policy.retention_days is None:
        return RetentionEvaluation(
            decision=RetentionDecision.OWNER_POLICY_REQUIRED,
            cleanup_eligibility=CleanupEligibility.NEVER,
            reason="numeric_retention_period_not_assigned",
            retention_days=None,
        )

    if not policy.owner_approved:
        return RetentionEvaluation(
            decision=RetentionDecision.REVIEW_REQUIRED,
            cleanup_eligibility=CleanupEligibility.REVIEW_BEFORE_DELETE,
            reason="owner_approval_required",
            retention_days=policy.retention_days,
        )

    if not retention_elapsed:
        return RetentionEvaluation(
            decision=RetentionDecision.RETAIN,
            cleanup_eligibility=CleanupEligibility.REVIEW_BEFORE_DELETE,
            reason="retention_period_not_elapsed",
            retention_days=policy.retention_days,
        )

    return RetentionEvaluation(
        decision=RetentionDecision.DISPOSAL_ELIGIBLE,
        cleanup_eligibility=CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION,
        reason="retention_period_elapsed_and_owner_approved",
        retention_days=policy.retention_days,
    )


def security_audit_log_policy() -> RetentionPolicy:
    """Return the fail-closed policy for the current security/audit log."""
    return RetentionPolicy(
        policy_id="security_audit_log_policy_pending",
        owner=ArtifactOwner.SECURITY,
        purpose="security and audit event traceability",
        retention_class=RetentionClass.OWNER_POLICY_REQUIRED,
        retention_days=None,
        hold_active=True,
        hold_reason="security_audit_retention_policy_pending",
        owner_approved=False,
        source="phgs_security_log_governance",
    )
