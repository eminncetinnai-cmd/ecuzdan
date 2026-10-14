"""RCCALS Change Preflight Engine.

Validates planned file/directory creations and modifications BEFORE mutation.

Evaluates:
  - TARGET_LAYER
  - DIRECTORY_POLICY
  - NAMING_POLICY
  - DUPLICATE_RISK
  - LIFECYCLE_CLASS
  - ROOT_POLLUTION
  - TEMPORARY_ARTIFACT_POLICY

Outputs:
  - ALLOW
  - WARN
  - BLOCK
  - REVIEW_REQUIRED
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

# Ensure repository root is in sys.path
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from scripts.governance.duplicate_prevention import (
    DuplicateCheckResult,
    DuplicatePreventionScanner,
    DuplicateRiskStatus,
)


class PreflightDecision(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCK = "BLOCK"


@dataclass
class ArtifactIntent:
    path: str
    purpose: str = ""
    artifact_type: str = "source"  # source, test, config, template, temporary, script
    target_layer: str = ""
    lifecycle_class: str = "ACTIVE"
    component_names: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


@dataclass
class PreflightNotice:
    category: str
    message: str
    severity: str = "BLOCK"  # BLOCK, WARN, REVIEW_REQUIRED


@dataclass
class PreflightResult:
    decision: PreflightDecision
    intents: list[ArtifactIntent]
    notices: list[PreflightNotice] = field(default_factory=list)
    duplicate_results: list[DuplicateCheckResult] = field(default_factory=list)

    @property
    def is_allowed(self) -> bool:
        return self.decision in (PreflightDecision.ALLOW, PreflightDecision.WARN)


# ── Deterministic Policy Rules ────────────────────────────────────────────────
_ROOT_ALLOWED_EXACT = {
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
    "docker-compose.logging.yml",
    "docker-compose.observability.yml",
    "start_e_cuzdan.bat",
    "README.md",
    "AGENTS.md",
}

_ROOT_ALLOWED_PATTERNS = [
    re.compile(r"^client_secret_.*\.json$"),
    re.compile(r"^e_cuzdan_v\d+\.db(-shm|-wal)?$"),
]

_ROOT_BLOCKED_PREFIXES = (
    "analysis_",
    "debug_",
    "probe_",
    "experiment_",
    "tmp_",
    "temp_",
    "copy_",
    "test_",
    "fix_",
)

_AUTHORIZED_TOP_DIRS = {
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
    "observability",
    ".work",
    ".agents",
}

_FORBIDDEN_NAME_PATTERNS = [
    (re.compile(r"(?:^|[_.\\-])(?:tmp|temp|test2|final|final2|backup|old|copy|fix|latest)(?:[_.\\-]|$)", re.IGNORECASE), "Forbidden keyword in filename"),
    (re.compile(r".*_v\d+\.(py|js|css|html)$", re.IGNORECASE), "Forbidden version suffix '_v[N]' in source file"),
]

_KNOWN_JUSTIFIED_NAMES = {
    "verify_backup_restore.py",
    "backup_manager.py",
    "backup_service.py",
    "docker-compose.logging.yml",
    "docker-compose.observability.yml",
    "e_cuzdan_v15.db",
}


class ChangePreflightEngine:
    """Preflight validator for repository changes and artifact creation."""

    def __init__(self, repo_root: str | pathlib.Path | None = None) -> None:
        if repo_root is None:
            self.repo_root = pathlib.Path(__file__).resolve().parents[2]
        else:
            self.repo_root = pathlib.Path(repo_root).resolve()

        self.duplicate_scanner = DuplicatePreventionScanner(self.repo_root)

    def evaluate(self, intents: Sequence[ArtifactIntent] | Sequence[str]) -> PreflightResult:
        normalized_intents: list[ArtifactIntent] = []
        for item in intents:
            if isinstance(item, str):
                normalized_intents.append(ArtifactIntent(path=item))
            else:
                normalized_intents.append(item)

        notices: list[PreflightNotice] = []
        duplicate_results: list[DuplicateCheckResult] = []

        for intent in normalized_intents:
            norm_path = os.path.normpath(intent.path).replace("\\", "/")
            parts = norm_path.split("/")
            filename = parts[-1]
            stem = pathlib.Path(filename).stem
            is_root = len(parts) == 1

            # 1. Root Directory Pollution Check
            if is_root:
                # Check blocked prefixes
                if any(filename.lower().startswith(prefix) for prefix in _ROOT_BLOCKED_PREFIXES):
                    notices.append(PreflightNotice(
                        category="ROOT_POLLUTION",
                        message=f"Root file '{filename}' has forbidden prefix. Temporary work must reside in .work/",
                        severity="BLOCK"
                    ))
                elif filename not in _ROOT_ALLOWED_EXACT and not any(p.match(filename) for p in _ROOT_ALLOWED_PATTERNS):
                    notices.append(PreflightNotice(
                        category="ROOT_POLLUTION",
                        message=f"Creating unauthorized file '{filename}' in root directory is blocked.",
                        severity="BLOCK"
                    ))

            # 2. Directory Governance Check
            top_dir = parts[0] if not is_root else "root"
            if not is_root and top_dir not in _AUTHORIZED_TOP_DIRS:
                notices.append(PreflightNotice(
                    category="UNAUTHORIZED_DIRECTORY",
                    message=f"Top-level directory '{top_dir}' is not authorized by architectural registry.",
                    severity="BLOCK"
                ))

            # 3. Temporary Artifact Placement Check
            if intent.artifact_type == "temporary" or any(k in stem.lower() for k in ["probe", "experiment", "debug", "investigation"]):
                if not norm_path.startswith(".work/") and not norm_path.startswith("tmp/"):
                    notices.append(PreflightNotice(
                        category="TEMP_ARTIFACT_OUTSIDE_WORKSPACE",
                        message=f"Temporary artifact '{norm_path}' must reside inside .work/ subdirectories.",
                        severity="BLOCK"
                    ))

            # 4. Naming Policy Check
            # Allow migration scripts with 'fix' if in database/migrations or known justified names
            is_migration = "migrations" in parts or "database" in parts
            if filename not in _KNOWN_JUSTIFIED_NAMES:
                for pat, reason in _FORBIDDEN_NAME_PATTERNS:
                    if pat.search(filename) and not is_migration:
                        notices.append(PreflightNotice(
                            category="INVALID_NAMING",
                            message=f"File '{filename}' violates naming policy: {reason}",
                            severity="BLOCK"
                        ))
                        break

            # 5. Domain Layer Purity Preflight
            if parts[0] == "domain" and intent.target_layer.lower() in {"route", "flask", "web", "controller"}:
                notices.append(PreflightNotice(
                    category="DOMAIN_PURITY_VIOLATION",
                    message=f"Cannot place web/controller artifact '{norm_path}' in domain layer.",
                    severity="BLOCK"
                ))

            # 6. Duplicate Component Check
            if intent.artifact_type == "source" and not is_root and top_dir not in {"tests", "scripts", "docs"}:
                dup_res = self.duplicate_scanner.check_intent(
                    norm_path,
                    component_names=intent.component_names,
                    keywords=intent.keywords
                )
                duplicate_results.append(dup_res)
                if dup_res.status == DuplicateRiskStatus.EXISTING_COMPONENT_REUSE:
                    notices.append(PreflightNotice(
                        category="DUPLICATE_COMPONENT_EXISTS",
                        message=dup_res.message,
                        severity="BLOCK"
                    ))
                elif dup_res.status == DuplicateRiskStatus.POSSIBLE_DUPLICATE:
                    notices.append(PreflightNotice(
                        category="POSSIBLE_DUPLICATE",
                        message=dup_res.message,
                        severity="WARN"
                    ))
                elif dup_res.status == DuplicateRiskStatus.REVIEW_REQUIRED:
                    notices.append(PreflightNotice(
                        category="DUPLICATE_REVIEW_REQUIRED",
                        message=dup_res.message,
                        severity="REVIEW_REQUIRED"
                    ))

        # Determine Final Decision
        if any(n.severity == "BLOCK" for n in notices):
            decision = PreflightDecision.BLOCK
        elif any(n.severity == "REVIEW_REQUIRED" for n in notices):
            decision = PreflightDecision.REVIEW_REQUIRED
        elif any(n.severity == "WARN" for n in notices):
            decision = PreflightDecision.WARN
        else:
            decision = PreflightDecision.ALLOW

        return PreflightResult(
            decision=decision,
            intents=normalized_intents,
            notices=notices,
            duplicate_results=duplicate_results
        )
