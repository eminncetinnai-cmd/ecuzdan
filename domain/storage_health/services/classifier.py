"""Deterministic metadata classifier for Storage Health Observe mode."""

from __future__ import annotations

from pathlib import Path

from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.protected import ProtectedResourceDetector


class StorageClassifier:
    """Assign a category and a non-destructive cleanup policy to a path."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.protected = ProtectedResourceDetector(self.root)

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def classify(self, path: str | Path, *, is_directory: bool = False) -> tuple[str, PolicyClass, str]:
        candidate = Path(path)
        relative = self._relative(candidate)
        normalized = relative.lower()
        name = candidate.name.lower()

        protected_policy, protected_reason = self.protected.explain(candidate)
        if protected_policy is not None:
            path_parts = {part.lower() for part in Path(relative).parts}
            if ".venv" in path_parts:
                return "runtime", protected_policy, protected_reason or "active_environment"
            if ".git" in path_parts:
                return "source", protected_policy, protected_reason or "repository_metadata"
            if name in {"e_cuzdan_v15.db", "e_cuzdan_v15.db-wal", "e_cuzdan_v15.db-shm"}:
                return "database", protected_policy, protected_reason or "active_sqlite_anchor"
            if normalized.startswith("configuration/"):
                return "configuration", protected_policy, protected_reason or "configuration"
            return "source", protected_policy, protected_reason or "canonical_application_tree"

        if any(token in normalized for token in ("backup", "backups")):
            return "backups", PolicyClass.REVIEW_REQUIRED, "backup_retention_and_integrity_review"
        if any(token in normalized for token in ("report", "reports", "evidence")):
            return "reports", PolicyClass.SAFE_WITH_CONFIRMATION, "retained_report_or_evidence_review"
        if any(token in normalized for token in ("security.log", "security_log", "audit.log", "audit_log")) or name in {"security.log", "audit.log"}:
            return "logs", PolicyClass.REVIEW_REQUIRED, "security_audit_log_retention_review"
        if any(token in normalized for token in ("log", "logs")) or name.endswith(".log"):
            return "logs", PolicyClass.SAFE_WITH_CONFIRMATION, "non_security_log_retention_review"
        if any(token in normalized for token in ("pytest_cache", "__pycache__", "coverage", "htmlcov", "cache")):
            return "cache", PolicyClass.SAFE_AUTO, "regenerable_cache"
        if any(token in normalized for token in ("test_artifact", "test-artifact", "test_output")):
            return "test_artifacts", PolicyClass.SAFE_WITH_CONFIRMATION, "regenerable_test_artifact"
        if any(token in normalized for token in ("archive", "archives")) or name.endswith((".zip", ".tar", ".gz", ".7z")):
            return "archives", PolicyClass.REVIEW_REQUIRED, "archive_integrity_and_retention_review"
        if any(token in normalized for token in ("build", "dist", "wheel")):
            return "build_artifacts", PolicyClass.SAFE_WITH_CONFIRMATION, "regenerable_build_artifact"
        if any(token in normalized for token in ("tmp", "temp", "temporary")):
            return "cache", PolicyClass.SAFE_AUTO, "disposable_temporary_artifact"
        if any(token in normalized for token in ("domain", "routes", "application", "infrastructure", "templates", "static", "translations", "tests")):
            return "source", PolicyClass.PROTECTED, "canonical_application_tree"
        if candidate.suffix.lower() in {".py", ".pyi", ".html", ".css", ".js", ".ts", ".bat", ".ps1"}:
            return "source", PolicyClass.PROTECTED, "source_file"
        return "unknown", PolicyClass.REVIEW_REQUIRED, "unclassified_resource"
