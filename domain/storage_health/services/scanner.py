"""Bounded, metadata-only project storage scanner.

The scanner never opens file contents, never hashes files, never touches SQLite,
and never mutates the filesystem. It reads only directory entries and stat
metadata. Symlink/reparse targets are reported as skipped resources rather than
followed.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.classifier import StorageClassifier


@dataclass(frozen=True, slots=True)
class StorageObservation:
    relative_path: str
    category: str
    policy_class: str
    reason: str
    bytes: int
    modified_epoch: float | None
    is_directory: bool = False


@dataclass(frozen=True, slots=True)
class StorageScan:
    project_root: str
    scanned_at_epoch: float
    observations: tuple[StorageObservation, ...]
    category_bytes: dict[str, int]
    policy_bytes: dict[str, int]
    top_consumers: tuple[StorageObservation, ...]
    errors: tuple[str, ...]
    truncated: bool
    files_scanned: int
    directories_scanned: int
    symlinks_skipped: int

    @property
    def total_bytes(self) -> int:
        return sum(self.category_bytes.values())

    @property
    def protected_bytes(self) -> int:
        return self.policy_bytes.get(PolicyClass.PROTECTED.value, 0)

    @property
    def candidate_bytes(self) -> int:
        return sum(
            value
            for key, value in self.policy_bytes.items()
            if key != PolicyClass.PROTECTED.value
        )

    @property
    def safe_reclaimable_bytes(self) -> int:
        return self.policy_bytes.get(PolicyClass.SAFE_AUTO.value, 0)

    def to_dict(self) -> dict:
        return {
            "project_root": self.project_root,
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
            "top_consumers": [
                {
                    "relative_path": item.relative_path,
                    "category": item.category,
                    "policy_class": item.policy_class,
                    "reason": item.reason,
                    "bytes": item.bytes,
                    "modified_epoch": item.modified_epoch,
                }
                for item in self.top_consumers
            ],
        }


class StorageScanner:
    """Scan project metadata without reading file contents."""

    def __init__(
        self,
        project_root: str | os.PathLike[str],
        *,
        max_files: int = 250_000,
        max_seconds: float = 90.0,
        top_consumer_limit: int = 50,
    ):
        self.root = Path(project_root).resolve()
        self.max_files = max(1, int(max_files))
        self.max_seconds = max(1.0, float(max_seconds))
        self.top_consumer_limit = max(1, int(top_consumer_limit))
        self.classifier = StorageClassifier(self.root)

    @staticmethod
    def _safe_mtime(path: Path) -> float | None:
        try:
            return path.stat(follow_symlinks=False).st_mtime
        except OSError:
            return None

    @staticmethod
    def _safe_size(path: Path) -> int:
        try:
            return int(path.stat(follow_symlinks=False).st_size)
        except OSError:
            return 0

    def _observation(self, path: Path, *, is_directory: bool = False) -> StorageObservation:
        relative = path.relative_to(self.root).as_posix() or "."
        category, policy, reason = self.classifier.classify(path, is_directory=is_directory)
        return StorageObservation(
            relative_path=relative,
            category=category,
            policy_class=policy.value,
            reason=reason,
            bytes=self._safe_size(path),
            modified_epoch=self._safe_mtime(path),
            is_directory=is_directory,
        )

    def scan(self) -> StorageScan:
        started = time.monotonic()
        scanned_at = time.time()
        observations: list[StorageObservation] = []
        errors: list[str] = []
        category_bytes: dict[str, int] = defaultdict(int)
        policy_bytes: dict[str, int] = defaultdict(int)
        files_scanned = 0
        directories_scanned = 0
        symlinks_skipped = 0
        truncated = False

        if not self.root.is_dir():
            return StorageScan(
                project_root=self.root.as_posix(),
                scanned_at_epoch=scanned_at,
                observations=(),
                category_bytes={},
                policy_bytes={},
                top_consumers=(),
                errors=("project_root_not_directory",),
                truncated=False,
                files_scanned=0,
                directories_scanned=0,
                symlinks_skipped=0,
            )

        def on_walk_error(error: OSError) -> None:
            errors.append(f"walk_error:{type(error).__name__}")

        for current_root, dirnames, filenames in os.walk(
            self.root,
            topdown=True,
            followlinks=False,
            onerror=on_walk_error,
        ):
            if time.monotonic() - started >= self.max_seconds:
                truncated = True
                break

            current_path = Path(current_root)
            safe_dirnames: list[str] = []
            for dirname in dirnames:
                candidate = current_path / dirname
                try:
                    if candidate.is_symlink():
                        symlinks_skipped += 1
                        continue
                except OSError:
                    errors.append("symlink_check_error")
                    continue
                safe_dirnames.append(dirname)
                if len(observations) < self.max_files:
                    try:
                        item = self._observation(candidate, is_directory=True)
                        observations.append(item)
                        category_bytes[item.category] += item.bytes
                        policy_bytes[item.policy_class] += item.bytes
                        directories_scanned += 1
                    except (OSError, ValueError) as error:
                        errors.append(f"directory_metadata_error:{type(error).__name__}")
            dirnames[:] = safe_dirnames

            for filename in filenames:
                if files_scanned >= self.max_files:
                    truncated = True
                    break
                if time.monotonic() - started >= self.max_seconds:
                    truncated = True
                    break
                candidate = current_path / filename
                try:
                    if candidate.is_symlink():
                        symlinks_skipped += 1
                        continue
                    item = self._observation(candidate)
                    observations.append(item)
                    category_bytes[item.category] += item.bytes
                    policy_bytes[item.policy_class] += item.bytes
                    files_scanned += 1
                except (OSError, ValueError) as error:
                    errors.append(f"file_metadata_error:{type(error).__name__}")

            if truncated:
                break

        top_consumers = tuple(
            sorted(
                (item for item in observations if not item.is_directory),
                key=lambda item: item.bytes,
                reverse=True,
            )[: self.top_consumer_limit]
        )
        return StorageScan(
            project_root=self.root.as_posix(),
            scanned_at_epoch=scanned_at,
            observations=tuple(observations),
            category_bytes={key: int(value) for key, value in category_bytes.items()},
            policy_bytes={key: int(value) for key, value in policy_bytes.items()},
            top_consumers=top_consumers,
            errors=tuple(errors[:100]),
            truncated=truncated,
            files_scanned=files_scanned,
            directories_scanned=directories_scanned,
            symlinks_skipped=symlinks_skipped,
        )
