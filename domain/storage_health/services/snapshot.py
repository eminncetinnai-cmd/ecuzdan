"""Metadata snapshot tokens and non-destructive rechecks.

The fingerprint is built from relative path, size, mtime, policy and resource
type metadata. It is not a content hash and never opens a file.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.protected import ProtectedResourceDetector
from domain.storage_health.services.scanner import StorageObservation, StorageScan


@dataclass(frozen=True, slots=True)
class SnapshotFingerprint:
    token: str
    observation_count: int
    generated_at_epoch: float

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "observation_count": self.observation_count,
            "generated_at_epoch": self.generated_at_epoch,
        }


@dataclass(frozen=True, slots=True)
class SnapshotRecheck:
    valid: bool
    checked_count: int
    blocking_reasons: tuple[str, ...]

    @property
    def execute_eligible(self) -> bool:
        """Recommend Core never authorizes execution; this is a safety gate only."""
        return False

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checked_count": self.checked_count,
            "blocking_reasons": list(self.blocking_reasons),
            "execute_eligible": self.execute_eligible,
        }


def build_snapshot_fingerprint(scan: StorageScan) -> SnapshotFingerprint:
    digest = hashlib.sha256()
    digest.update(b"storage-health-metadata-snapshot-v1\n")
    digest.update(f"truncated={scan.truncated}|errors={len(scan.errors)}\n".encode("utf-8"))
    for item in sorted(scan.observations, key=lambda value: value.relative_path):
        mtime = "" if item.modified_epoch is None else f"{item.modified_epoch:.6f}"
        digest.update(
            "|".join(
                (
                    item.relative_path,
                    item.category,
                    item.policy_class,
                    str(item.bytes),
                    mtime,
                    "directory" if item.is_directory else "file",
                )
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return SnapshotFingerprint(
        token=digest.hexdigest(),
        observation_count=len(scan.observations),
        generated_at_epoch=scan.scanned_at_epoch,
    )


def _unsafe_relative_path(relative_path: str) -> bool:
    path = Path(relative_path)
    windows_path = PureWindowsPath(relative_path)
    return (
        not relative_path
        or path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive != ""
        or any(part == ".." for part in path.parts)
        or any(part == ".." for part in windows_path.parts)
    )


def _is_reparse_or_symlink(path: Path, stat_result: os.stat_result) -> bool:
    if path.is_symlink():
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
    attributes = getattr(stat_result, "st_file_attributes", 0)
    return bool(attributes & reparse_flag)


def _current_metadata(
    root: str | Path,
    observation: StorageObservation,
) -> tuple[int, float, bool] | None:
    if _unsafe_relative_path(observation.relative_path):
        return None
    root_path = Path(root).resolve()
    candidate = root_path / Path(observation.relative_path)
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root_path)
        stat_result = candidate.stat(follow_symlinks=False)
    except (OSError, ValueError):
        return None
    if _is_reparse_or_symlink(candidate, stat_result):
        return None
    is_directory = stat.S_ISDIR(stat_result.st_mode)
    is_regular_file = stat.S_ISREG(stat_result.st_mode)
    if not is_directory and not is_regular_file:
        return None
    return int(stat_result.st_size), float(stat_result.st_mtime), is_directory


def _observation_blockers(
    root: str | Path,
    observation: StorageObservation,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if _unsafe_relative_path(observation.relative_path):
        return ("absolute_or_traversal_path",)

    detector = ProtectedResourceDetector(root)
    candidate = Path(root).resolve() / Path(observation.relative_path)
    protected_policy, protected_reason = detector.explain(candidate)
    if protected_policy == PolicyClass.PROTECTED:
        blockers.append(protected_reason or "protected_resource")
    if observation.policy_class == PolicyClass.PROTECTED.value:
        blockers.append("protected_policy")

    current = _current_metadata(root, observation)
    if current is None:
        blockers.append("missing_or_reparse_or_unsupported_resource")
        return tuple(dict.fromkeys(blockers))
    current_size, current_mtime, current_is_directory = current
    expected_type = "directory" if observation.is_directory else "file"
    actual_type = "directory" if current_is_directory else "file"
    if current_size != observation.bytes:
        blockers.append("size_changed")
    if observation.modified_epoch is not None and abs(current_mtime - observation.modified_epoch) >= 0.000001:
        blockers.append("mtime_changed")
    if actual_type != expected_type:
        blockers.append("type_changed")
    return tuple(dict.fromkeys(blockers))


def observation_matches_snapshot(
    root: str | Path,
    observation: StorageObservation,
) -> bool:
    """Compare current stat metadata to a planned observation, without reading it."""
    return not _observation_blockers(root, observation)


def recheck_recommendation_snapshot(
    root: str | Path,
    scan: StorageScan,
    observations: tuple[StorageObservation, ...] | list[StorageObservation],
) -> SnapshotRecheck:
    """Return a safety result; it never deletes, archives, or mutates resources."""
    blockers: list[str] = []
    if scan.truncated:
        blockers.append("scan_truncated")
    if scan.errors:
        blockers.append("scan_errors_present")

    checked = 0
    for observation in observations:
        checked += 1
        blockers.extend(_observation_blockers(root, observation))
    unique_blockers = tuple(dict.fromkeys(blockers))
    return SnapshotRecheck(
        valid=not unique_blockers,
        checked_count=checked,
        blocking_reasons=unique_blockers,
    )


def all_observations_match_snapshot(
    root: str | Path,
    observations: tuple[StorageObservation, ...] | list[StorageObservation],
) -> bool:
    return all(observation_matches_snapshot(root, item) for item in observations)
