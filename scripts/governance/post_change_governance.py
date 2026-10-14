"""RCCALS Post-Change Governance Auditor.

Audits the repository working tree and recent changes after development:
  - Discovers new files & directories
  - Validates naming compliance
  - Validates directory placement
  - Verifies root directory protection
  - Verifies temporary artifact containment
  - Runs Architecture Gate scan

Outputs:
  - PASS
  - WARN
  - BLOCK
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

# Ensure repository root is in sys.path
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from dataclasses import dataclass, field
from enum import Enum

from scripts.governance.architecture_gate import ArchitectureGate, ArchitectureGateReport
from scripts.governance.change_preflight import (
    ArtifactIntent,
    ChangePreflightEngine,
    PreflightDecision,
    PreflightResult,
)


class PostChangeStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass
class PostChangeReport:
    status: PostChangeStatus
    new_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    preflight_result: PreflightResult | None = None
    gate_report: ArchitectureGateReport | None = None
    messages: list[str] = field(default_factory=list)


class PostChangeGovernanceAuditor:
    """Audits repository after changes before PR or final deployment."""

    def __init__(self, repo_root: str | pathlib.Path | None = None) -> None:
        if repo_root is None:
            self.repo_root = pathlib.Path(__file__).resolve().parents[2]
        else:
            self.repo_root = pathlib.Path(repo_root).resolve()

        self.preflight_engine = ChangePreflightEngine(self.repo_root)
        self.architecture_gate = ArchitectureGate(self.repo_root)

    def _get_git_changes(self) -> tuple[list[str], list[str]]:
        new_files: list[str] = []
        modified_files: list[str] = []
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                for raw_line in res.stdout.splitlines():
                    if not raw_line.strip():
                        continue
                    status = raw_line[:2]
                    filepath = raw_line[3:].strip()
                    norm_p = filepath.replace('"', '').strip()
                    target = self.repo_root / norm_p
                    if target.is_dir():
                        for root, _, files in os.walk(target):
                            for f in files:
                                f_rel = os.path.normpath(os.path.relpath(os.path.join(root, f), self.repo_root)).replace("\\", "/")
                                if "??" in status or "A" in status:
                                    new_files.append(f_rel)
                                else:
                                    modified_files.append(f_rel)
                    else:
                        norm_f = os.path.normpath(norm_p).replace("\\", "/")
                        if "??" in status or "A" in status:
                            new_files.append(norm_f)
                        else:
                            modified_files.append(norm_f)
        except Exception:
            pass
        return new_files, modified_files

    def run_audit(self) -> PostChangeReport:
        new_files, modified_files = self._get_git_changes()

        # 1. Run Preflight on new files
        preflight_res: PreflightResult | None = None
        if new_files:
            intents = [ArtifactIntent(path=f) for f in new_files]
            preflight_res = self.preflight_engine.evaluate(intents)

        # 2. Run Architecture Gate across repository
        gate_rep = self.architecture_gate.scan()

        # 3. Aggregate Status
        messages: list[str] = []
        status = PostChangeStatus.PASS

        if preflight_res and preflight_res.decision == PreflightDecision.BLOCK:
            status = PostChangeStatus.BLOCK
            for notice in preflight_res.notices:
                if notice.severity == "BLOCK":
                    messages.append(f"[PREFLIGHT_BLOCK] {notice.category}: {notice.message}")

        if gate_rep.has_blocking:
            status = PostChangeStatus.BLOCK
            for v in gate_rep.violations:
                if v.severity == "BLOCK":
                    messages.append(f"[GATE_BLOCK] {v.category}: {v.file_path} - {v.message}")

        if status != PostChangeStatus.BLOCK:
            if (preflight_res and preflight_res.decision in (PreflightDecision.WARN, PreflightDecision.REVIEW_REQUIRED)) or gate_rep.violations:
                status = PostChangeStatus.WARN

        return PostChangeReport(
            status=status,
            new_files=new_files,
            modified_files=modified_files,
            preflight_result=preflight_res,
            gate_report=gate_rep,
            messages=messages,
        )


if __name__ == "__main__":
    auditor = PostChangeGovernanceAuditor()
    rep = auditor.run_audit()
    print("=" * 60)
    print(f"E-CÜZDAN RCCALS POST-CHANGE GOVERNANCE AUDIT: {rep.status.value}")
    print("=" * 60)
    print(f"New Files Detected     : {len(rep.new_files)}")
    print(f"Modified Files         : {len(rep.modified_files)}")
    print(f"Total Gate Violations  : {rep.gate_report.total_violations if rep.gate_report else 0}")
    if rep.messages:
        print("\nBlocking Issues:")
        for m in rep.messages:
            print("  -", m)
    sys.exit(0 if rep.status != PostChangeStatus.BLOCK else 1)
