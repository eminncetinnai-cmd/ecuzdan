"""Non-mutating PHGS architecture and development governance guards.

The guard reports drift and policy gaps. It never deletes, moves, archives,
opens file contents, reads database rows, or changes project configuration.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable

from domain.storage_health.lifecycle import ArtifactGovernance, ArtifactOwner, LifecycleState, RetentionClass
from domain.storage_health.policy import PROTECTED_NAMES


class GuardSeverity(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass(frozen=True, slots=True)
class GuardIssue:
    code: str
    severity: GuardSeverity
    message: str
    relative_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "relative_path": self.relative_path,
        }


@dataclass(frozen=True, slots=True)
class ArchitectureGuardReport:
    checks: tuple[GuardIssue, ...]

    @property
    def blocking(self) -> tuple[GuardIssue, ...]:
        return tuple(item for item in self.checks if item.severity is GuardSeverity.BLOCK)

    @property
    def warnings(self) -> tuple[GuardIssue, ...]:
        return tuple(item for item in self.checks if item.severity is GuardSeverity.WARN)

    @property
    def passed(self) -> bool:
        return not self.blocking

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "blocking_count": len(self.blocking),
            "warning_count": len(self.warnings),
            "checks": [item.to_dict() for item in self.checks],
            "mutation_performed": False,
        }


_SENSITIVE_SEGMENT_RE = re.compile(r"secret|credential|token|oauth|cookie", re.IGNORECASE)
_DEPENDENCY_SHADOW_RE = re.compile(r"^(requirements|constraints|pipfile|poetry)\b.*", re.IGNORECASE)
_DEFAULT_ALLOWED_ROOT_FILES = frozenset(
    {
        ".coveragerc_oauth",
        ".env",
        ".env.example",
        ".gitignore",
        "__init__.py",
        "app.py",
        "config.py",
        "docker-compose.logging.yml",
        "docker-compose.observability.yml",
        "e_cuzdan_v15.db",
        "e_cuzdan_v15.db-shm",
        "e_cuzdan_v15.db-wal",
        "market_data_service.py",
        "models.py",
        "pyproject.toml",
        "pytest.ini",
        "start_e_cuzdan.bat",
        "strategy.py",
        "worker.py",
        "wsgi.py",
    }
)


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _path_issue(path: Path, root: Path) -> GuardIssue | None:
    candidate = Path(path)
    relative = _relative(root, candidate)
    parts = Path(relative).parts
    if candidate.is_absolute():
        return GuardIssue("absolute_path", GuardSeverity.BLOCK, "Absolute path cannot enter governance payload.", None)
    if ".." in parts:
        return GuardIssue("path_traversal", GuardSeverity.BLOCK, "Traversal path is not a valid artifact location.", None)
    if any(_SENSITIVE_SEGMENT_RE.search(part) for part in parts):
        return GuardIssue("sensitive_path", GuardSeverity.BLOCK, "Sensitive path segment is protected and redacted.", "<protected-resource>")
    lower_parts = {part.lower() for part in parts}
    protected_parts = {item.lower() for item in PROTECTED_NAMES}
    if lower_parts.intersection(protected_parts):
        return GuardIssue("protected_path", GuardSeverity.BLOCK, "Protected application or recovery anchor cannot enter cleanup governance.", relative)
    return None


def check_root_drift(
    project_root: str | Path,
    *,
    allowed_root_files: Iterable[str] = _DEFAULT_ALLOWED_ROOT_FILES,
) -> tuple[GuardIssue, ...]:
    """Report unexpected root files without changing the repository."""
    root = Path(project_root).resolve()
    allowed = {Path(item).name.lower() for item in allowed_root_files}
    issues: list[GuardIssue] = []
    try:
        entries = sorted(os.scandir(root), key=lambda item: item.name.lower())
    except OSError as exc:
        return (GuardIssue("root_scan_error", GuardSeverity.BLOCK, f"Root metadata scan failed: {type(exc).__name__}"),)
    for entry in entries:
        if not entry.is_file(follow_symlinks=False):
            continue
        if entry.name.lower() in allowed:
            continue
        issues.append(
            GuardIssue(
                "root_drift",
                GuardSeverity.BLOCK,
                "Root file is outside the approved baseline allowlist.",
                entry.name,
            )
        )
    if not issues:
        return (GuardIssue("root_drift_clear", GuardSeverity.PASS, "Root file allowlist has no drift."),)
    return tuple(issues)


def check_dependency_shadowing(project_root: str | Path) -> tuple[GuardIssue, ...]:
    """Detect dependency manifests outside configuration/dependencies."""
    root = Path(project_root).resolve()
    issues: list[GuardIssue] = []
    try:
        entries = sorted(os.scandir(root), key=lambda item: item.name.lower())
    except OSError as exc:
        return (GuardIssue("dependency_scan_error", GuardSeverity.BLOCK, f"Dependency metadata scan failed: {type(exc).__name__}"),)
    for entry in entries:
        if entry.is_file(follow_symlinks=False) and _DEPENDENCY_SHADOW_RE.match(entry.name):
            issues.append(
                GuardIssue(
                    "dependency_shadowing",
                    GuardSeverity.BLOCK,
                    "Dependency manifest must live under configuration/dependencies.",
                    entry.name,
                )
            )
    if not issues:
        return (GuardIssue("dependency_shadowing_clear", GuardSeverity.PASS, "No root dependency shadowing detected."),)
    return tuple(issues)


def check_governance(governance: ArtifactGovernance) -> tuple[GuardIssue, ...]:
    """Validate ownership/lifecycle/retention metadata without granting execution."""
    issues: list[GuardIssue] = []
    if governance.owner is ArtifactOwner.UNKNOWN or not governance.owner_assigned:
        issues.append(GuardIssue("owner_missing", GuardSeverity.BLOCK, "Artifact owner is missing or unknown."))
    if governance.lifecycle_state is LifecycleState.CREATED:
        issues.append(GuardIssue("lifecycle_unclassified", GuardSeverity.BLOCK, "Artifact must be classified before governance use."))
    if governance.retention_class is RetentionClass.UNKNOWN:
        issues.append(GuardIssue("retention_unknown", GuardSeverity.BLOCK, "Retention class is unknown."))
    elif governance.retention_days is None and governance.retention_class is not RetentionClass.PROTECTED:
        issues.append(GuardIssue("retention_policy_pending", GuardSeverity.WARN, "Numeric retention requires owner-approved policy; no default is invented."))
    if governance.retention_class is RetentionClass.PROTECTED and governance.cleanup_eligibility.value != "never":
        issues.append(GuardIssue("protected_cleanup_leak", GuardSeverity.BLOCK, "Protected artifact is incorrectly cleanup eligible."))
    if not issues:
        return (GuardIssue("governance_valid", GuardSeverity.PASS, "Ownership, lifecycle and retention metadata are internally consistent."),)
    return tuple(issues)


def check_path(project_root: str | Path, path: str | Path) -> GuardIssue:
    """Validate a path boundary without reading the target contents."""
    root = Path(project_root).resolve()
    candidate = Path(path)
    return _path_issue(candidate, root) or GuardIssue("path_valid", GuardSeverity.PASS, "Path is within a non-sensitive governance boundary.", _relative(root, candidate))


def check_transient_lifecycle(
    project_root: str | Path,
    *,
    now_epoch: float,
    max_age_seconds: float = 86_400.0,
) -> tuple[GuardIssue, ...]:
    """Warn about old temp artifacts; never removes them."""
    root = Path(project_root).resolve()
    temp_root = root / "tmp"
    if not temp_root.exists():
        return (GuardIssue("temp_scope_absent", GuardSeverity.PASS, "Canonical tmp scope is absent."),)
    issues: list[GuardIssue] = []
    try:
        entries = sorted(temp_root.iterdir(), key=lambda item: item.name.lower())
    except OSError as exc:
        return (GuardIssue("temp_scan_error", GuardSeverity.BLOCK, f"Temp metadata scan failed: {type(exc).__name__}"),)
    for item in entries:
        if not item.is_file():
            continue
        try:
            age = max(0.0, now_epoch - item.stat().st_mtime)
        except OSError:
            issues.append(GuardIssue("temp_stat_error", GuardSeverity.WARN, "Temp artifact metadata could not be read.", "tmp/<redacted>"))
            continue
        if age > max_age_seconds:
            issues.append(GuardIssue("stale_transient", GuardSeverity.WARN, "Transient artifact exceeded the configured review age; no automatic deletion is performed.", f"tmp/{item.name}"))
    if not issues:
        return (GuardIssue("transient_lifecycle_clear", GuardSeverity.PASS, "No stale transient artifact exceeded the review age."),)
    return tuple(issues)


def run_architecture_guard(
    project_root: str | Path,
    *,
    governance: ArtifactGovernance | None = None,
    paths: Iterable[str | Path] = (),
    allowed_root_files: Iterable[str] = _DEFAULT_ALLOWED_ROOT_FILES,
    now_epoch: float | None = None,
    max_temp_age_seconds: float = 86_400.0,
) -> ArchitectureGuardReport:
    """Run all non-mutating guards and return an explainable report."""
    root = Path(project_root).resolve()
    issues: list[GuardIssue] = list(check_root_drift(root, allowed_root_files=allowed_root_files))
    issues.extend(check_dependency_shadowing(root))
    if governance is not None:
        issues.extend(check_governance(governance))
    for path in paths:
        issues.append(check_path(root, path))
    if now_epoch is not None:
        issues.extend(check_transient_lifecycle(root, now_epoch=now_epoch, max_age_seconds=max_temp_age_seconds))
    return ArchitectureGuardReport(tuple(issues))
