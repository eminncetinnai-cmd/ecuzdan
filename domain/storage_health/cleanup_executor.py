"""Safe, allowlisted cleanup executor for Storage Health candidates.

Only SAFE_AUTO policy candidates in explicitly allowlisted directories
(``__pycache__``, ``tmp``) are eligible. Every path is validated before
any filesystem call is made.  No security logs, database files, source
files, or any protected resource are ever touched.
"""

from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

_log = logging.getLogger(__name__)

# ── Allowlisted parent-directory names (first component of relative path) ────
_ALLOWLISTED_PARENTS = {"__pycache__", ".pytest_cache"}
_ALLOWLISTED_TEMP_PARENTS = {"tmp", "temp", "temporary"}
_ALL_SAFE_PARENTS = _ALLOWLISTED_PARENTS | _ALLOWLISTED_TEMP_PARENTS

# ── Hard-blocked path fragments — never touch these ──────────────────────────
_BLOCKED_PARTS = {
    ".env", ".venv", "venv", "database", "domain", "application",
    "infrastructure", "routes", "templates", "static", "translations",
    "tests", "runtime", "configuration", ".git", "migrations",
    "credentials", "secrets", "client-secret", "client_secret",
    # DB files
}
_BLOCKED_SUFFIXES = {
    ".db", ".db-shm", ".db-wal", ".sqlite", ".sqlite3",
    # Source
    ".py", ".html", ".js", ".css", ".json", ".yaml", ".yml",
    ".txt", ".md", ".cfg", ".ini", ".toml",
    # Log — never touch logs from the executor
    ".log",
}
_SAFE_SUFFIXES = {".pyc", ".pyo"}  # Only bytecode is deletable via name


# ── Result types ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CandidateCleanupResult:
    candidate_id: str
    relative_path: str
    success: bool
    bytes_freed: int
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "relative_path": self.relative_path,
            "success": self.success,
            "bytes_freed": self.bytes_freed,
            "error": self.error,
        }


@dataclass
class CleanupSummary:
    executed: list[CandidateCleanupResult] = field(default_factory=list)
    skipped: list[CandidateCleanupResult] = field(default_factory=list)
    errors: list[CandidateCleanupResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    @property
    def bytes_freed(self) -> int:
        return sum(r.bytes_freed for r in self.executed)

    def finish(self) -> None:
        self.finished_at = time.time()

    def to_dict(self) -> dict:
        return {
            "executed": len(self.executed),
            "skipped": len(self.skipped),
            "errors": len(self.errors),
            "bytes_freed": self.bytes_freed,
            "details": {
                "executed": [r.to_dict() for r in self.executed],
                "skipped": [r.to_dict() for r in self.skipped],
                "errors": [r.to_dict() for r in self.errors],
            },
        }


# ── Validation helpers ────────────────────────────────────────────────────────

def _validate_relative_path(
    project_root: Path,
    relative_path: str,
) -> tuple[bool, str, Path | None]:
    """Return (ok, rejection_reason, resolved_abs_path)."""
    # Normalize separators
    normalized = relative_path.replace("\\", "/").strip("/")
    if not normalized:
        return False, "empty_path", None

    parts_lower = [p.lower() for p in PureWindowsPath(normalized).parts]

    # Block absolute paths and traversal
    if Path(normalized).is_absolute() or ".." in parts_lower:
        return False, "path_traversal", None

    # Block any hard-blocked directory component
    for part in parts_lower:
        if part in _BLOCKED_PARTS:
            return False, f"blocked_part:{part}", None

    # Block by suffix unless it's a safe-to-delete bytecode file
    resolved = project_root / normalized
    suffix = resolved.suffix.lower()
    if suffix in _BLOCKED_SUFFIXES and suffix not in _SAFE_SUFFIXES:
        return False, f"blocked_suffix:{suffix}", None

    # Only allow resources whose first path component is allowlisted
    if parts_lower and parts_lower[0] not in _ALL_SAFE_PARENTS:
        return False, f"not_allowlisted_parent:{parts_lower[0]}", None

    # Final safety: resolved path must be inside project_root
    try:
        resolved.resolve().relative_to(project_root.resolve())
    except ValueError:
        return False, "outside_project_root", None

    return True, "", resolved


# ── Executor ─────────────────────────────────────────────────────────────────

class CleanupExecutor:
    """Execute allowlisted SAFE_AUTO cleanup candidates.

    Validates every candidate path before touching the filesystem.
    Protected resources, source files, database files, and logs are
    always rejected regardless of what the caller supplies.
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def execute(
        self,
        candidates: list[dict],
        *,
        selected_ids: set[str] | None = None,
    ) -> CleanupSummary:
        """Run cleanup for the given candidate dicts.

        Args:
            candidates: Serialised CleanupCandidate dicts from the service.
            selected_ids: If provided, only process candidates whose
                ``candidate_id`` is in this set.

        Returns:
            CleanupSummary with per-candidate results.
        """
        summary = CleanupSummary()

        for c in candidates:
            cid = str(c.get("candidate_id", ""))
            rel = str(c.get("relative_path", ""))
            policy = str(c.get("policy_class", ""))
            execute_eligible = bool(c.get("execute_eligible", False))

            # ── Filter to selected IDs ────────────────────────────────────
            if selected_ids is not None and cid not in selected_ids:
                summary.skipped.append(CandidateCleanupResult(
                    candidate_id=cid, relative_path=rel,
                    success=False, bytes_freed=0, error="not_selected",
                ))
                continue

            # ── Must be SAFE_AUTO and execute_eligible ────────────────────
            if policy != "SAFE_AUTO" or not execute_eligible:
                summary.skipped.append(CandidateCleanupResult(
                    candidate_id=cid, relative_path=rel,
                    success=False, bytes_freed=0, error="not_eligible",
                ))
                continue

            # ── Path validation ───────────────────────────────────────────
            ok, rejection_reason, abs_path = _validate_relative_path(
                self.project_root, rel
            )
            if not ok:
                _log.warning(
                    "CleanupExecutor rejected %r: %s", rel, rejection_reason
                )
                summary.skipped.append(CandidateCleanupResult(
                    candidate_id=cid, relative_path=rel,
                    success=False, bytes_freed=0, error=rejection_reason,
                ))
                continue

            # ── Execute ───────────────────────────────────────────────────
            try:
                freed = self._remove(abs_path)
                _log.info(
                    "CleanupExecutor removed %r — %d bytes freed", rel, freed
                )
                summary.executed.append(CandidateCleanupResult(
                    candidate_id=cid, relative_path=rel,
                    success=True, bytes_freed=freed,
                ))
            except Exception as exc:
                _log.error(
                    "CleanupExecutor failed to remove %r: %s", rel, exc
                )
                summary.errors.append(CandidateCleanupResult(
                    candidate_id=cid, relative_path=rel,
                    success=False, bytes_freed=0, error=str(exc),
                ))

        summary.finish()
        return summary

    # ── Private ──────────────────────────────────────────────────────────

    def _remove(self, path: Path) -> int:
        """Remove a path (file or directory tree). Returns bytes freed."""
        if not path.exists():
            return 0
        if path.is_dir() and not path.is_symlink():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            shutil.rmtree(path, ignore_errors=False)
            return size
        size = path.stat().st_size
        path.unlink(missing_ok=False)
        return size
