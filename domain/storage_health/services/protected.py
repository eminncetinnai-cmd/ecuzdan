"""Protected resource detection for metadata-only storage scans."""

from __future__ import annotations

import os
from pathlib import Path

from domain.storage_health.policy import PolicyClass


class ProtectedResourceDetector:
    """Classify resources that must never enter automatic cleanup."""

    def __init__(self, project_root: str | os.PathLike[str]):
        self.root = Path(project_root).resolve()
        self._protected_relative_names = {
            ".git",
            ".venv",
            ".env",
            "app.py",
            "config.py",
            "wsgi.py",
            "configuration",
            "config",
            "domain",
            "routes",
            "infrastructure",
            "application",
            "repositories",
            "utils",
            "scripts",
            "bootstrap",
            "shared",
            "observability",
            "data",
            "instance",
            "source",
            "templates",
            "static",
            "translations",
            "tests",
            "e_cuzdan_v15.db",
            "e_cuzdan_v15.db-wal",
            "e_cuzdan_v15.db-shm",
            ".env.example",
            ".gitignore",
            "pyproject.toml",
            "pytest.ini",
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.logging.yml",
            "docker-compose.observability.yml",
            "Makefile",
            "makefile",
        }

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _contains_sensitive_name(relative_path: str) -> bool:
        parts = {part.lower() for part in Path(relative_path).parts}
        name = Path(relative_path).name.lower()
        return bool(
            parts.intersection({".env", "credentials", "secrets", "client-secret", "client_secret"})
            or any(token in name for token in ("secret", "credential", "oauth", "oauth_client"))
        )

    def explain(self, path: str | os.PathLike[str]) -> tuple[PolicyClass | None, str | None]:
        candidate = Path(path)
        relative = self._relative(candidate)
        relative_parts = Path(relative).parts
        basename = Path(relative).name

        if self._contains_sensitive_name(relative):
            return PolicyClass.PROTECTED, "sensitive_or_credential_name"
        if any(part in {".git", ".venv"} for part in relative_parts):
            return PolicyClass.PROTECTED, "active_repository_or_environment"
        if basename in {"e_cuzdan_v15.db", "e_cuzdan_v15.db-wal", "e_cuzdan_v15.db-shm"}:
            return PolicyClass.PROTECTED, "active_sqlite_anchor"
        if basename in {"app.py", "config.py", "wsgi.py"}:
            return PolicyClass.PROTECTED, "runtime_entrypoint_or_config"
        if basename in {
            ".env",
            ".env.example",
            ".gitignore",
            "pyproject.toml",
            "pytest.ini",
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.logging.yml",
            "docker-compose.observability.yml",
            "Makefile",
            "makefile",
        }:
            return PolicyClass.PROTECTED, "root_control_or_configuration"
        if relative_parts and relative_parts[0] in {
            "configuration",
            "config",
            "domain",
            "routes",
            "infrastructure",
            "application",
            "repositories",
            "utils",
            "scripts",
            "bootstrap",
            "shared",
            "observability",
            "data",
            "instance",
            "source",
            "templates",
            "static",
            "translations",
            "tests",
        }:
            return PolicyClass.PROTECTED, "canonical_application_tree"
        return None, None

    def is_protected(self, path: str | os.PathLike[str]) -> bool:
        policy, _ = self.explain(path)
        return policy == PolicyClass.PROTECTED
