#!/usr/bin/env python3
"""E-Cüzdan EAFGS Architecture & Repository Health Gate (Read-Only MVP).

Inspects the repository structure against governance policies:
  - Root directory cleanliness
  - Forbidden naming patterns (_final, _v2, fix, debug, etc.)
  - Architectural layer import boundaries (e.g. Domain -> Flask)
  - Test file placement
  - Temporary artifact leakage outside .work/

Operates strictly read-only: does not delete, move, or modify any files.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── Root Allowlist ────────────────────────────────────────────────────────────
_ROOT_ALLOWED_FILES = {
    "app.py",
    "config.py",
    "models.py",
    "market_data_service.py",
    "strategy.py",
    "worker.py",
    "wsgi.py",
    "pyproject.toml",
    "pytest.ini",
    "mypy.ini",
    ".gitignore",
    ".env",
    ".env.example",
    ".coveragerc_oauth",
    ".coverage",
    "docker-compose.logging.yml",
    "docker-compose.observability.yml",
    "docker-compose.prod.yml",
    "Dockerfile",
    ".dockerignore",
    "start_e_cuzdan.bat",
    "start_silent.vbs",
    "README.md",
    "AGENTS.md",
    "package.json",
    "package-lock.json",
    "tailwind.config.js",
    "requirements.txt",
}
_ROOT_ALLOWED_PATTERNS = [
    re.compile(r"^client_secret_.*\.json$"),
    re.compile(r"^e_cuzdan_v\d+\.db(-shm|-wal)?$"),
    re.compile(r"^E-Cuzdan.*\.lnk$"),
]

# ── Forbidden Name Patterns ───────────────────────────────────────────────────
_FORBIDDEN_NAME_PATTERNS = [
    (re.compile(r".*_final\d*\.[a-zA-Z0-9]+$", re.IGNORECASE), "Forbidden '_final' pattern in filename"),
    (re.compile(r".*_v\d+\.(py|js|css|html)$", re.IGNORECASE), "Forbidden '_v[N]' suffix in source file"),
    (re.compile(r".*_(old|backup|copy|temp|tmp)\.[a-zA-Z0-9]+$", re.IGNORECASE), "Forbidden artifact keyword in filename"),
    (re.compile(r"^(fix|debug)\d*\.py$", re.IGNORECASE), "Temporary probe script must reside in .work/"),
]

# ── Ignored Directories ───────────────────────────────────────────────────────
_IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".benchmarks",
    "htmlcov",
    ".work",
    ".agents",
    "tmp",
    "node_modules",
}


_AUTHORIZED_TOP_DIRS = {
    ".agents",
    "domain",
    "application",
    "repositories",
    "infrastructure",
    "routes",
    "database",
    "templates",
    "static",
    "config",
    "configuration",
    "tests",
    "docs",
    "scripts",
    "governance",
    "translations",
    "utils",
    "validators",
    "dtos",
    "engines",
    "shared",
    "bootstrap",
    "instance",
    "logs",
    "data",
    "backups",
    "observability",
    ".work",
    ".idea",
    ".vscode",
    ".github",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".benchmarks",
    "htmlcov",
    "tmp",
    "node_modules",
}


@dataclass
class GateViolation:
    category: str
    file_path: str
    message: str
    severity: str = "WARNING"  # WARNING or BLOCK


@dataclass
class ArchitectureGateReport:
    scanned_files: int = 0
    scanned_dirs: int = 0
    violations: list[GateViolation] = field(default_factory=list)

    @property
    def has_blocking(self) -> bool:
        return any(v.severity == "BLOCK" for v in self.violations)

    @property
    def total_violations(self) -> int:
        return len(self.violations)


class ArchitectureGate:
    """Read-only repository architecture and governance inspector."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()

    def run_check(self) -> ArchitectureGateReport:
        report = ArchitectureGateReport()
        self._check_top_level_directories(report)
        self._check_root_directory(report)
        self._check_recursive_tree(report)
        self._check_domain_layer_purity(report)
        self._check_design_system_ratchet(report)
        return report

    scan = run_check

    # ── 0. Top-Level Directory Inspection ─────────────────────────────────────

    def _check_top_level_directories(self, report: ArchitectureGateReport) -> None:
        for entry in self.repo_root.iterdir():
            if entry.is_dir() and entry.name not in _AUTHORIZED_TOP_DIRS:
                report.violations.append(GateViolation(
                    category="UNAUTHORIZED_DIRECTORY",
                    file_path=entry.name,
                    message=f"Unauthorized top-level directory '{entry.name}' not in architectural registry",
                    severity="BLOCK",
                ))

    # ── 1. Root Directory Inspection ──────────────────────────────────────────

    def _check_root_directory(self, report: ArchitectureGateReport) -> None:
        for entry in self.repo_root.iterdir():
            if entry.is_dir():
                continue
            name = entry.name
            if name in _ROOT_ALLOWED_FILES:
                continue
            if any(p.match(name) for p in _ROOT_ALLOWED_PATTERNS):
                continue

            # Check if root has __init__.py which is a duplicate of routes/__init__.py
            if name == "__init__.py":
                report.violations.append(GateViolation(
                    category="ROOT_POLLUTION",
                    file_path=name,
                    message="Root __init__.py found (duplicate of routes/__init__.py)",
                    severity="WARNING",
                ))
                continue

            report.violations.append(GateViolation(
                category="ROOT_POLLUTION",
                file_path=name,
                message=f"Unregistered file in repository root: {name}",
                severity="WARNING",
            ))

    # ── 2. Recursive File and Naming Inspection ───────────────────────────────

    def _check_recursive_tree(self, report: ArchitectureGateReport) -> None:
        for root, dirs, files in os.walk(self.repo_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS]
            report.scanned_dirs += len(dirs)

            for file_name in files:
                report.scanned_files += 1
                full_path = Path(root) / file_name
                rel_path = full_path.relative_to(self.repo_root).as_posix()

                # Check forbidden naming patterns
                for pattern, msg in _FORBIDDEN_NAME_PATTERNS:
                    if pattern.match(file_name):
                        # Allow .work/ exceptions
                        if rel_path.startswith(".work/"):
                            continue
                        report.violations.append(GateViolation(
                            category="FORBIDDEN_NAMING",
                            file_path=rel_path,
                            message=msg,
                            severity="WARNING",
                        ))

                # Check tests outside tests/
                if file_name.startswith("test_") and file_name.endswith(".py"):
                    if not rel_path.startswith("tests/"):
                        report.violations.append(GateViolation(
                            category="MISPLACED_TEST",
                            file_path=rel_path,
                            message="Test file located outside tests/ hierarchy",
                            severity="WARNING",
                        ))

    # ── 3. Domain Layer Purity Inspection (AST) ───────────────────────────────

    def _check_domain_layer_purity(self, report: ArchitectureGateReport) -> None:
        domain_path = self.repo_root / "domain"
        if not domain_path.exists():
            return

        for py_file in domain_path.rglob("*.py"):
            rel_path = py_file.relative_to(self.repo_root).as_posix()
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
            except Exception as exc:
                report.violations.append(GateViolation(
                    category="AST_PARSE_ERROR",
                    file_path=rel_path,
                    message=f"Failed to parse AST: {exc}",
                    severity="WARNING",
                ))
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(("flask", "routes", "templates", "static")):
                            report.violations.append(GateViolation(
                                category="DOMAIN_PURITY_VIOLATION",
                                file_path=rel_path,
                                message=f"Domain layer imports external framework/route: '{alias.name}'",
                                severity="BLOCK",
                            ))
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod.startswith(("flask", "routes", "templates", "static")):
                        report.violations.append(GateViolation(
                            category="DOMAIN_PURITY_VIOLATION",
                            file_path=rel_path,
                            message=f"Domain layer imports external framework/route: '{mod}'",
                            severity="BLOCK",
                        ))

    # ── 4. Design System Ratchet Inspection ───────────────────────────────────

    def _check_design_system_ratchet(self, report: ArchitectureGateReport) -> None:
        """Runs the design system consistency check with ratchet mechanism."""
        try:
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))
            from scripts.check_design_system import DesignSystemChecker
            checker = DesignSystemChecker(self.repo_root)
            results = checker.check_directory(checker.templates_dir)
            passed, violations = checker.check_ratchet(results)
            if not passed:
                for v in violations:
                    report.violations.append(GateViolation(
                        category="DESIGN_SYSTEM_RATCHET_VIOLATION",
                        file_path="templates/",
                        message=f"{v} (See docs/AI_AGENT_DESIGN_SYSTEM.md)",
                        severity="BLOCK",
                    ))
        except Exception as e:
            report.violations.append(GateViolation(
                category="DESIGN_SYSTEM_CHECKER_ERROR",
                file_path="scripts/check_design_system.py",
                message=f"Failed to execute design system checker: {e}",
                severity="WARNING",
            ))


def main() -> int:
    mode = os.getenv("EAFGS_MODE", "WARNING").upper()
    repo_root = Path(__file__).resolve().parent.parent.parent
    gate = ArchitectureGate(repo_root)
    report = gate.run_check()

    print("=" * 70)
    print("E-CÜZDAN EAFGS ARCHITECTURE & REPOSITORY HEALTH GATE (MVP)")
    print(f"Enforcement Mode    : {mode}")
    print("=" * 70)
    print(f"Scanned Directories : {report.scanned_dirs}")
    print(f"Scanned Files       : {report.scanned_files}")
    print(f"Total Violations    : {report.total_violations}")
    print("-" * 70)

    if not report.violations:
        print("RESULT: PASS — All architecture governance checks passed cleanly.")
        print("=" * 70)
        return 0

    print("VIOLATIONS / GOVERNANCE NOTICES:")
    for i, v in enumerate(report.violations, 1):
        sev_tag = "[BLOCK]" if v.severity == "BLOCK" else "[WARN] "
        print(f"  {i:02d}. {sev_tag} [{v.category}] {v.file_path}: {v.message}")

    print("-" * 70)
    if report.has_blocking and mode == "BLOCK":
        print("RESULT: BLOCK — Critical architectural boundary violations detected in BLOCK mode.")
        print("=" * 70)
        return 1

    print("RESULT: WARNING — Phase 1 Discovery: Identified architectural boundaries & violations reported.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
