"""Minimal PHGS artifact ownership, lifecycle and retention model.

This module classifies metadata observations without reading content or deciding
that any resource may be deleted automatically. Retention days remain unset
until an owner-approved policy provides a numeric value.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from domain.storage_health.policy import PolicyClass


class ArtifactOwner(StrEnum):
    DEVELOPMENT = "development"
    QA = "qa"
    OPERATIONS = "operations"
    RECOVERY_POLICY = "recovery_policy"
    GENERATOR = "generator"
    CREATING_PROCESS = "creating_process"
    PLATFORM = "platform"
    SECURITY = "security"
    UNKNOWN = "unknown"


class LifecycleState(StrEnum):
    CREATED = "created"
    CLASSIFIED = "classified"
    OWNER_ASSIGNED = "owner_assigned"
    ACTIVE = "active"
    RETAINED = "retained"
    REVIEW = "review"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETION_CANDIDATE = "deletion_candidate"
    USER_APPROVED = "user_approved"
    EXECUTED = "executed"
    VERIFIED = "verified"
    KEPT = "kept"


class RetentionClass(StrEnum):
    PROTECTED = "protected"
    REGENERABLE = "regenerable"
    REVIEW_BEFORE_DELETE = "review_before_delete"
    OWNER_POLICY_REQUIRED = "owner_policy_required"
    UNKNOWN = "unknown"


class CleanupEligibility(StrEnum):
    NEVER = "never"
    CANDIDATE_AFTER_EXPLICIT_CONFIRMATION = "candidate_after_explicit_confirmation"
    REVIEW_BEFORE_DELETE = "review_before_delete"


@dataclass(frozen=True, slots=True)
class ArtifactGovernance:
    """Ownership and lifecycle metadata for one classified artifact group."""

    owner: ArtifactOwner
    lifecycle_state: LifecycleState
    retention_class: RetentionClass
    retention_days: int | None
    protection_level: str
    cleanup_eligibility: CleanupEligibility
    storage_location: str
    purpose: str
    owner_assigned: bool

    def __post_init__(self) -> None:
        if self.retention_days is not None and self.retention_days < 0:
            raise ValueError("retention_days cannot be negative")
        if self.owner is ArtifactOwner.UNKNOWN and self.owner_assigned:
            raise ValueError("unknown owner cannot be marked assigned")
        if self.retention_class is RetentionClass.PROTECTED:
            if self.cleanup_eligibility is not CleanupEligibility.NEVER:
                raise ValueError("protected artifacts cannot be cleanup eligible")
            if self.protection_level != "protected":
                raise ValueError("protected retention requires protected protection_level")
        if self.cleanup_eligibility is CleanupEligibility.NEVER and self.lifecycle_state in {
            LifecycleState.USER_APPROVED,
            LifecycleState.EXECUTED,
        }:
            raise ValueError("never-cleanup artifact cannot enter execution states")

    def to_dict(self) -> dict:
        return {
            "owner": self.owner.value,
            "lifecycle_state": self.lifecycle_state.value,
            "retention_class": self.retention_class.value,
            "retention_days": self.retention_days,
            "protection_level": self.protection_level,
            "cleanup_eligibility": self.cleanup_eligibility.value,
            "storage_location": self.storage_location,
            "purpose": self.purpose,
            "owner_assigned": self.owner_assigned,
        }


_ALLOWED_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.CREATED: frozenset({LifecycleState.CLASSIFIED}),
    LifecycleState.CLASSIFIED: frozenset({LifecycleState.OWNER_ASSIGNED, LifecycleState.REVIEW}),
    LifecycleState.OWNER_ASSIGNED: frozenset({LifecycleState.ACTIVE, LifecycleState.RETAINED, LifecycleState.REVIEW}),
    LifecycleState.ACTIVE: frozenset({LifecycleState.RETAINED, LifecycleState.REVIEW}),
    LifecycleState.RETAINED: frozenset({LifecycleState.REVIEW, LifecycleState.KEPT}),
    LifecycleState.REVIEW: frozenset({LifecycleState.ARCHIVED, LifecycleState.EXPIRED, LifecycleState.DELETION_CANDIDATE, LifecycleState.KEPT}),
    LifecycleState.ARCHIVED: frozenset({LifecycleState.EXPIRED, LifecycleState.KEPT}),
    LifecycleState.EXPIRED: frozenset({LifecycleState.DELETION_CANDIDATE, LifecycleState.KEPT}),
    LifecycleState.DELETION_CANDIDATE: frozenset({LifecycleState.USER_APPROVED, LifecycleState.KEPT}),
    LifecycleState.USER_APPROVED: frozenset({LifecycleState.EXECUTED}),
    LifecycleState.EXECUTED: frozenset({LifecycleState.VERIFIED}),
    LifecycleState.VERIFIED: frozenset(),
    LifecycleState.KEPT: frozenset(),
}


def can_transition(current: LifecycleState, target: LifecycleState) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())


def transition_lifecycle(current: LifecycleState, target: LifecycleState) -> LifecycleState:
    if not can_transition(current, target):
        raise ValueError(f"invalid_lifecycle_transition:{current.value}->{target.value}")
    return target


_OWNER_BY_CATEGORY = {
    "database": ArtifactOwner.RECOVERY_POLICY,
    "runtime": ArtifactOwner.OPERATIONS,
    "backups": ArtifactOwner.RECOVERY_POLICY,
    "logs": ArtifactOwner.OPERATIONS,
    "reports": ArtifactOwner.GENERATOR,
    "cache": ArtifactOwner.CREATING_PROCESS,
    "test_artifacts": ArtifactOwner.QA,
    "source": ArtifactOwner.DEVELOPMENT,
    "configuration": ArtifactOwner.PLATFORM,
    "archives": ArtifactOwner.RECOVERY_POLICY,
    "build_artifacts": ArtifactOwner.DEVELOPMENT,
}

_PURPOSE_BY_CATEGORY = {
    "database": "active financial storage anchor",
    "runtime": "active application runtime",
    "backups": "recovery and disaster-recovery evidence",
    "logs": "operational diagnostics and observability",
    "reports": "generated analysis or delivery output",
    "cache": "regenerable process cache",
    "test_artifacts": "quality-assurance generated output",
    "source": "application source or repository content",
    "configuration": "runtime and deployment configuration",
    "archives": "retained evidence or archived output",
    "build_artifacts": "regenerable build output",
    "unknown": "unclassified resource requiring owner review",
}


def governance_for(
    category: str,
    policy_class: str | PolicyClass,
    *,
    reason: str = "",
) -> ArtifactGovernance:
    """Map an observation to governance metadata; never grants deletion authority."""
    policy = PolicyClass(policy_class)
    owner = _OWNER_BY_CATEGORY.get(category, ArtifactOwner.UNKNOWN)
    purpose = _PURPOSE_BY_CATEGORY.get(category, _PURPOSE_BY_CATEGORY["unknown"])

    if policy is PolicyClass.PROTECTED:
        return ArtifactGovernance(
            owner=owner if owner is not ArtifactOwner.UNKNOWN else ArtifactOwner.PLATFORM,
            lifecycle_state=LifecycleState.RETAINED,
            retention_class=RetentionClass.PROTECTED,
            retention_days=None,
            protection_level="protected",
            cleanup_eligibility=CleanupEligibility.NEVER,
            storage_location="canonical_project_scope",
            purpose=purpose,
            owner_assigned=True,
        )

    if category == "unknown":
        return ArtifactGovernance(
            owner=ArtifactOwner.UNKNOWN,
            lifecycle_state=LifecycleState.REVIEW,
            retention_class=RetentionClass.UNKNOWN,
            retention_days=None,
            protection_level="review_required",
            cleanup_eligibility=CleanupEligibility.NEVER,
            storage_location="unclassified_project_scope",
            purpose=_PURPOSE_BY_CATEGORY["unknown"],
            owner_assigned=False,
        )

    if policy is PolicyClass.SAFE_AUTO:
        retention_class = RetentionClass.REGENERABLE
        eligibility = CleanupEligibility.CANDIDATE_AFTER_EXPLICIT_CONFIRMATION
        lifecycle = LifecycleState.REVIEW
        protection = "policy_safe_with_confirmation"
    else:
        retention_class = RetentionClass.REVIEW_BEFORE_DELETE
        eligibility = CleanupEligibility.REVIEW_BEFORE_DELETE
        lifecycle = LifecycleState.REVIEW
        protection = "review_required"

    return ArtifactGovernance(
        owner=owner,
        lifecycle_state=lifecycle,
        retention_class=retention_class,
        retention_days=None,
        protection_level=protection,
        cleanup_eligibility=eligibility,
        storage_location="canonical_project_scope",
        purpose=purpose,
        owner_assigned=owner is not ArtifactOwner.UNKNOWN,
    )
