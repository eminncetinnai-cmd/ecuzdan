"""UI/API-safe DTOs for Storage Health Observe results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.scanner import StorageObservation, StorageScan

_SENSITIVE_PARTS = {".env", "credentials", "secrets", "client-secret", "client_secret"}


def _safe_relative_path(relative_path: str) -> str:
    path = Path(relative_path)
    parts = list(path.parts)
    if any(part.lower() in _SENSITIVE_PARTS or "secret" in part.lower() for part in parts):
        return "<protected-resource>"
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class StorageObservationDTO:
    relative_path: str
    category: str
    policy_class: str
    reason: str
    bytes: int
    modified_epoch: float | None
    is_directory: bool

    @classmethod
    def from_observation(cls, observation: StorageObservation) -> "StorageObservationDTO":
        return cls(
            relative_path=_safe_relative_path(observation.relative_path),
            category=observation.category,
            policy_class=observation.policy_class,
            reason=observation.reason,
            bytes=observation.bytes,
            modified_epoch=observation.modified_epoch,
            is_directory=observation.is_directory,
        )

    def to_dict(self) -> dict:
        return {
            "relative_path": self.relative_path,
            "category": self.category,
            "policy_class": self.policy_class,
            "reason": self.reason,
            "bytes": self.bytes,
            "modified_epoch": self.modified_epoch,
            "is_directory": self.is_directory,
        }


@dataclass(frozen=True, slots=True)
class StorageScanDTO:
    scanned_at_epoch: float
    total_bytes: int
    category_bytes: dict[str, int]
    policy_bytes: dict[str, int]
    protected_bytes: int
    candidate_bytes: int
    safe_reclaimable_bytes: int
    files_scanned: int
    directories_scanned: int
    symlinks_skipped: int
    errors: tuple[str, ...]
    truncated: bool
    top_consumers: tuple[StorageObservationDTO, ...]

    @classmethod
    def from_scan(cls, scan: StorageScan) -> "StorageScanDTO":
        return cls(
            scanned_at_epoch=scan.scanned_at_epoch,
            total_bytes=scan.total_bytes,
            category_bytes=dict(scan.category_bytes),
            policy_bytes=dict(scan.policy_bytes),
            protected_bytes=scan.protected_bytes,
            candidate_bytes=scan.candidate_bytes,
            safe_reclaimable_bytes=scan.safe_reclaimable_bytes,
            files_scanned=scan.files_scanned,
            directories_scanned=scan.directories_scanned,
            symlinks_skipped=scan.symlinks_skipped,
            errors=tuple(scan.errors),
            truncated=scan.truncated,
            top_consumers=tuple(
                StorageObservationDTO.from_observation(item)
                for item in scan.top_consumers
            ),
        )

    def to_dict(self) -> dict:
        return {
            "scanned_at_epoch": self.scanned_at_epoch,
            "total_bytes": self.total_bytes,
            "category_bytes": dict(self.category_bytes),
            "policy_bytes": dict(self.policy_bytes),
            "protected_bytes": self.protected_bytes,
            "candidate_bytes": self.candidate_bytes,
            "safe_reclaimable_bytes": self.safe_reclaimable_bytes,
            "files_scanned": self.files_scanned,
            "directories_scanned": self.directories_scanned,
            "symlinks_skipped": self.symlinks_skipped,
            "errors": list(self.errors),
            "truncated": self.truncated,
            "top_consumers": [item.to_dict() for item in self.top_consumers],
            "policy_classes": [item.value for item in PolicyClass],
        }
