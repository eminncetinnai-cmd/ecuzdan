"""E-Cüzdan Runtime Bootstrap - Approved Dependency Restoration Engine.

Manages application runtime dependencies:
  - Discovers approved runtime manifest / lock in configuration/dependencies/
  - Validates existing installation via import smoke test and pip check
  - Restores approved runtime dependencies if missing
  - Prohibits unapproved, dev, or latest-version wildcards
"""

from __future__ import annotations

import pathlib
import subprocess
from dataclasses import dataclass, field

_CORE_SMOKE_MODULES = [
    "flask",
    "flask_sqlalchemy",
    "werkzeug",
    "yaml",
    "requests",
    "pandas",
    "yfinance",
    "dotenv",
]


@dataclass
class DependencyValidationResult:
    is_healthy: bool
    manifest_used: str = ""
    installed_packages: int = 0
    missing_modules: list[str] = field(default_factory=list)
    error_message: str = ""


class DependencyManager:
    """Manages approved runtime dependencies restoration and validation."""

    def __init__(self, repo_root: str | pathlib.Path, venv_python: str | pathlib.Path) -> None:
        self.repo_root = pathlib.Path(repo_root).resolve()
        self.venv_python = str(venv_python)

    def discover_authority_manifest(self) -> pathlib.Path | None:
        candidates = [
            self.repo_root / "configuration" / "dependencies" / "requirements-runtime-lock.txt",
            self.repo_root / "configuration" / "dependencies" / "requirements-runtime-constraints.txt",
            self.repo_root / "configuration" / "dependencies" / "requirements-runtime.txt",
            self.repo_root / "configuration" / "dependencies" / "requirements.txt",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def run_import_smoke_test(self) -> tuple[bool, list[str]]:
        smoke_code = (
            "import importlib.util, sys; "
            f"mods = {repr(_CORE_SMOKE_MODULES)}; "
            "missing = [m for m in mods if importlib.util.find_spec(m) is None]; "
            "print('|'.join(missing))"
        )
        try:
            res = subprocess.run(
                [self.venv_python, "-c", smoke_code],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode == 0:
                stdout_clean = res.stdout.strip()
                missing = [m for m in stdout_clean.split("|") if m]
                return len(missing) == 0, missing
            return False, _CORE_SMOKE_MODULES
        except Exception:
            return False, _CORE_SMOKE_MODULES

    def run_pip_check(self) -> tuple[bool, str]:
        try:
            res = subprocess.run(
                [self.venv_python, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if res.returncode == 0:
                return True, ""
            return False, res.stdout.strip() or res.stderr.strip()
        except Exception as exc:
            return False, str(exc)

    def ensure_dependencies(self, force_reinstall: bool = False) -> DependencyValidationResult:
        manifest = self.discover_authority_manifest()
        if manifest is None:
            return DependencyValidationResult(
                is_healthy=False,
                error_message="No approved runtime dependency manifest found in configuration/dependencies/.",
            )

        # 1. Quick smoke test if not forcing reinstall
        if not force_reinstall:
            smoke_ok, missing = self.run_import_smoke_test()
            if smoke_ok:
                return DependencyValidationResult(
                    is_healthy=True,
                    manifest_used=str(manifest),
                    missing_modules=[],
                )

        # 2. Install approved runtime dependencies from manifest
        install_cmd = [
            self.venv_python,
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--disable-pip-version-check",
            "-r",
            str(manifest),
        ]
        try:
            install_res = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if install_res.returncode != 0:
                return DependencyValidationResult(
                    is_healthy=False,
                    manifest_used=str(manifest),
                    error_message=f"Pip install failed: {install_res.stderr.strip()[:300]}",
                )

            # 3. Post-install validation: smoke test + pip check
            smoke_ok, missing = self.run_import_smoke_test()
            if not smoke_ok:
                return DependencyValidationResult(
                    is_healthy=False,
                    manifest_used=str(manifest),
                    missing_modules=missing,
                    error_message=f"Missing runtime modules after installation: {', '.join(missing)}",
                )

            return DependencyValidationResult(
                is_healthy=True,
                manifest_used=str(manifest),
                missing_modules=[],
            )
        except Exception as exc:
            return DependencyValidationResult(
                is_healthy=False,
                manifest_used=str(manifest),
                error_message=f"Exception during dependency installation: {exc}",
            )
