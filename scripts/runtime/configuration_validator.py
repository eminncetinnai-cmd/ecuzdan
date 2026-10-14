"""E-Cüzdan Runtime Bootstrap - Configuration Pre-flight Engine.

Validates:
  - Critical repository assets (app.py, config.py, models.py)
  - Environment configuration availability
  - Database accessibility and directory writability
  - Logs directory writability
Prohibits logging or exposing any secret values or credentials.
"""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field


@dataclass
class ConfigValidationResult:
    is_ready: bool
    db_path: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ConfigurationValidator:
    """Validates runtime configuration readiness without exposing secrets."""

    def __init__(self, repo_root: str | pathlib.Path) -> None:
        self.repo_root = pathlib.Path(repo_root).resolve()

    def validate(self) -> ConfigValidationResult:
        warnings: list[str] = []
        errors: list[str] = []

        # 1. Essential Source Files
        for required_file in ["app.py", "config.py", "models.py"]:
            if not (self.repo_root / required_file).is_file():
                errors.append(f"Required application entry file '{required_file}' is missing.")

        # 2. Environment file check
        env_file = self.repo_root / ".env"
        env_example = self.repo_root / ".env.example"
        if not env_file.is_file() and not env_example.is_file():
            warnings.append(".env file not found; application will use defaults.")

        # 3. Database writability check
        db_candidates = list(self.repo_root.glob("e_cuzdan_v*.db"))
        db_path_str = str(db_candidates[0]) if db_candidates else str(self.repo_root / "e_cuzdan_v15.db")
        if db_candidates:
            # Check read/write on existing DB
            if not os.access(db_candidates[0], os.R_OK | os.W_OK):
                errors.append(f"Database file '{db_candidates[0].name}' is not read/writable.")
        else:
            # Check directory write permission to create DB
            if not os.access(self.repo_root, os.W_OK):
                errors.append("Repository root is not writable to initialize database.")

        # 4. Logs directory writability
        logs_dir = self.repo_root / "logs"
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                errors.append(f"Cannot create logs directory: {exc}")
        elif not os.access(logs_dir, os.W_OK):
            errors.append("Logs directory is not writable.")

        # 5. Instance directory writability
        instance_dir = self.repo_root / "instance"
        if not instance_dir.exists():
            try:
                instance_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                warnings.append(f"Cannot create instance directory: {exc}")

        # 6. Template Syntax & Integrity Pre-flight
        template_dir = self.repo_root / "templates"
        if template_dir.exists():
            try:
                import jinja2
                env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_dir)))
                for t_file in template_dir.glob("**/*.html"):
                    rel = str(t_file.relative_to(template_dir)).replace("\\", "/")
                    try:
                        with open(t_file, "r", encoding="utf-8", errors="ignore") as f:
                            env.parse(f.read())
                    except Exception as t_err:
                        errors.append(f"Template syntax error in '{rel}': {t_err}")
            except Exception as j_err:
                warnings.append(f"Template pre-check skipped: {j_err}")

        is_ready = len(errors) == 0
        return ConfigValidationResult(
            is_ready=is_ready,
            db_path=db_path_str,
            warnings=warnings,
            errors=errors,
        )
