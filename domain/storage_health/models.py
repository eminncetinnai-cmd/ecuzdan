"""Value objects for non-destructive Storage Health recommendations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from domain.storage_health.lifecycle import ArtifactGovernance, governance_for
from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.scanner import StorageObservation, StorageScan


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RollbackKind(StrEnum):
    REGENERATE = "regenerate"
    ARCHIVE_THEN_DELETE = "archive_then_delete"
    MANUAL_REVIEW = "manual_review"
    NOT_APPLICABLE = "not_applicable"


_SENSITIVE_PARTS = {".env", "credentials", "secrets", "client-secret", "client_secret"}


def _redacted_relative_path(relative_path: str) -> str:
    path = Path(relative_path)
    parts = path.parts
    if path.is_absolute() or ".." in parts:
        return "<protected-resource>"
    if any(
        part.lower() in _SENSITIVE_PARTS or "secret" in part.lower() or "credential" in part.lower()
        for part in parts
    ):
        return "<protected-resource>"
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class RollbackPlan:
    kind: RollbackKind
    available: bool
    required_before_execute: bool
    description: str

    def to_dict(self) -> dict:
        return {
            "strategy": self.kind.value,
            "available": self.available,
            "required_before_execute": self.required_before_execute,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class CleanupCandidate:
    candidate_id: str
    relative_path: str
    category: str
    policy_class: str
    reason: str
    reclaimable_bytes: int
    modified_epoch: float | None
    risk_level: RiskLevel
    risk_reasons: tuple[str, ...]
    rollback: RollbackPlan
    user_confirmation_required: bool
    review_required: bool
    maintenance_window_required: bool
    eligible_for_safe_cleanup: bool
    execute_eligible: bool
    blocking_reasons: tuple[str, ...]
    expected_post_condition: str
    metadata_fingerprint: dict[str, int | float | str | None]
    is_protected: bool
    snapshot_token: str

    @staticmethod
    def _candidate_id(observation: StorageObservation, snapshot_token: str) -> str:
        payload = "|".join(
            (
                observation.relative_path,
                observation.category,
                observation.policy_class,
                str(observation.bytes),
                "" if observation.modified_epoch is None else f"{observation.modified_epoch:.6f}",
                "directory" if observation.is_directory else "file",
                snapshot_token,
            )
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:24]

    @property
    def governance(self) -> ArtifactGovernance:
        return governance_for(self.category, self.policy_class, reason=self.reason)

    @classmethod
    def from_observation(
        cls,
        observation: StorageObservation,
        *,
        snapshot_token: str,
    ) -> "CleanupCandidate":
        policy = PolicyClass(observation.policy_class)
        if policy == PolicyClass.SAFE_AUTO:
            risk = RiskLevel.LOW
            reasons = ("regenerable_resource", "no_application_source_dependency_detected")
            rollback = RollbackPlan(
                RollbackKind.REGENERATE,
                available=True,
                required_before_execute=False,
                description="Kaynak yeniden üretilebilir; archive zorunlu değil.",
            )
            review_required = False
            maintenance = False
            eligible = True
        elif policy == PolicyClass.SAFE_WITH_CONFIRMATION:
            risk = RiskLevel.MEDIUM
            reasons = ("retention_decision_required", "resource_may_be_needed_for_diagnostics")
            rollback = RollbackPlan(
                RollbackKind.ARCHIVE_THEN_DELETE,
                available=False,
                required_before_execute=True,
                description="Silmeden önce external archive ve SHA kanıtı gerekir.",
            )
            review_required = False
            maintenance = False
            eligible = False
        elif policy == PolicyClass.REVIEW_REQUIRED:
            risk = RiskLevel.HIGH
            reasons = ("retention_or_integrity_review_required", "not_safe_auto_scope")
            rollback = RollbackPlan(
                RollbackKind.MANUAL_REVIEW,
                available=False,
                required_before_execute=True,
                description="Retention, integrity ve archive kanıtı olmadan yürütülemez.",
            )
            review_required = True
            maintenance = False
            eligible = False
        elif policy == PolicyClass.MAINTENANCE_WINDOW_REQUIRED:
            risk = RiskLevel.CRITICAL
            reasons = ("maintenance_window_required", "runtime_or_database_change_risk")
            rollback = RollbackPlan(
                RollbackKind.MANUAL_REVIEW,
                available=False,
                required_before_execute=True,
                description="Maintenance window ve doğrulanmış rollback planı gerekir.",
            )
            review_required = True
            maintenance = True
            eligible = False
        else:
            risk = RiskLevel.CRITICAL
            reasons = ("protected_resource", "automatic_cleanup_blocked")
            rollback = RollbackPlan(
                RollbackKind.NOT_APPLICABLE,
                available=False,
                required_before_execute=False,
                description="Protected kaynak; cleanup yürütülemez.",
            )
            review_required = False
            maintenance = False
            eligible = False

        if policy == PolicyClass.SAFE_AUTO:
            expected_post_condition = "Kaynak yalnız açık kullanıcı onayı ve yeniden doğrulama sonrası kaldırılır; uygulama korunur."
        elif policy == PolicyClass.SAFE_WITH_CONFIRMATION:
            expected_post_condition = "External archive kanıtı alındıktan sonra yalnız hedef dosya kaldırılır."
        elif policy == PolicyClass.REVIEW_REQUIRED:
            expected_post_condition = "İnceleme tamamlanana kadar kaynak değişmeden kalır."
        elif policy == PolicyClass.MAINTENANCE_WINDOW_REQUIRED:
            expected_post_condition = "Maintenance window açılana kadar kaynak değişmeden kalır."
        else:
            expected_post_condition = "Protected kaynak değişmeden kalır."

        blocking_reasons = ("recommend_only_phase", "explicit_user_confirmation_required")
        if policy != PolicyClass.SAFE_AUTO:
            blocking_reasons += ("policy_requires_additional_review",)
        if maintenance:
            blocking_reasons += ("maintenance_window_required",)

        return cls(
            candidate_id=cls._candidate_id(observation, snapshot_token),
            relative_path=observation.relative_path,
            category=observation.category,
            policy_class=policy.value,
            reason=observation.reason,
            reclaimable_bytes=observation.bytes,
            modified_epoch=observation.modified_epoch,
            risk_level=risk,
            risk_reasons=reasons,
            rollback=rollback,
            user_confirmation_required=True,
            review_required=review_required,
            maintenance_window_required=maintenance,
            eligible_for_safe_cleanup=eligible,
            execute_eligible=False,
            blocking_reasons=blocking_reasons,
            expected_post_condition=expected_post_condition,
            metadata_fingerprint={
                "size": observation.bytes,
                "mtime": observation.modified_epoch,
                "type": "directory" if observation.is_directory else "file",
            },
            is_protected=policy == PolicyClass.PROTECTED,
            snapshot_token=snapshot_token,
        )

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "relative_path": _redacted_relative_path(self.relative_path),
            "category": self.category,
            "policy_class": self.policy_class,
            "reason": self.reason,
            "reclaimable_bytes": self.reclaimable_bytes,
            "modified_epoch": self.modified_epoch,
            "risk_level": self.risk_level.value,
            "risk_reasons": list(self.risk_reasons),
            "rollback": self.rollback.to_dict(),
            "user_confirmation_required": self.user_confirmation_required,
            "review_required": self.review_required,
            "maintenance_window_required": self.maintenance_window_required,
            "eligible_for_safe_cleanup": self.eligible_for_safe_cleanup,
            "execute_eligible": self.execute_eligible,
            "blocking_reasons": list(self.blocking_reasons),
            "expected_post_condition": self.expected_post_condition,
            "metadata_fingerprint": dict(self.metadata_fingerprint),
            "is_protected": self.is_protected,
            "governance": self.governance.to_dict(),
            "snapshot_token": self.snapshot_token,
            "scan_snapshot_id": self.snapshot_token,
        }


@dataclass(frozen=True, slots=True)
class RecommendationSet:
    scan: StorageScan
    snapshot_token: str
    candidates: tuple[CleanupCandidate, ...]

    @property
    def safe_auto_candidates(self) -> tuple[CleanupCandidate, ...]:
        return tuple(item for item in self.candidates if item.eligible_for_safe_cleanup)

    @property
    def safe_reclaimable_bytes(self) -> int:
        return sum(item.reclaimable_bytes for item in self.safe_auto_candidates)

    def to_dict(self) -> dict:
        return {
            "snapshot_token": self.snapshot_token,
            "scan_snapshot_id": self.snapshot_token,
            "candidate_count": len(self.candidates),
            "safe_auto_count": len(self.safe_auto_candidates),
            "safe_reclaimable_bytes": self.safe_reclaimable_bytes,
            "candidates": [item.to_dict() for item in self.candidates],
        }
