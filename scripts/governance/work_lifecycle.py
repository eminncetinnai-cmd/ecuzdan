"""RCCALS .work Workspace Lifecycle & Retention Auditor.

Inspects the .work/ workspace without performing destructive blind deletes.
Categorizes artifacts into:
  - investigations
  - experiments
  - probes
  - generated
  - sessions

Provides age, size metrics, and retention status reporting.
"""

from __future__ import annotations

import os
import pathlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WorkCategory(str, Enum):
    INVESTIGATIONS = "investigations"
    EXPERIMENTS = "experiments"
    PROBES = "probes"
    GENERATED = "generated"
    SESSIONS = "sessions"
    UNCLASSIFIED = "unclassified"


@dataclass
class WorkArtifactItem:
    relative_path: str
    category: WorkCategory
    size_bytes: int
    modified_at: datetime
    age_days: float
    is_retention_exceeded: bool


@dataclass
class WorkWorkspaceReport:
    workspace_path: str
    total_files: int
    total_bytes: int
    category_counts: dict[str, int] = field(default_factory=dict)
    items: list[WorkArtifactItem] = field(default_factory=list)
    expired_items: list[WorkArtifactItem] = field(default_factory=list)


_DEFAULT_RETENTION_DAYS = {
    WorkCategory.INVESTIGATIONS: 14,
    WorkCategory.EXPERIMENTS: 7,
    WorkCategory.PROBES: 3,
    WorkCategory.GENERATED: 7,
    WorkCategory.SESSIONS: 30,
    WorkCategory.UNCLASSIFIED: 3,
}


class WorkLifecycleAuditor:
    """Read-only and controlled auditor for .work/ workspace."""

    def __init__(self, repo_root: str | pathlib.Path | None = None) -> None:
        if repo_root is None:
            self.repo_root = pathlib.Path(__file__).resolve().parents[2]
        else:
            self.repo_root = pathlib.Path(repo_root).resolve()

        self.work_dir = self.repo_root / ".work"

    def audit(self) -> WorkWorkspaceReport:
        if not self.work_dir.exists():
            return WorkWorkspaceReport(
                workspace_path=str(self.work_dir),
                total_files=0,
                total_bytes=0,
            )

        now = time.time()
        items: list[WorkArtifactItem] = []
        category_counts: dict[str, int] = {cat.value: 0 for cat in WorkCategory}
        total_bytes = 0

        for root, dirs, files in os.walk(self.work_dir):
            rel_root = os.path.relpath(root, self.work_dir)
            parts = rel_root.split(os.sep)
            first_part = parts[0].lower() if parts[0] != "." else "unclassified"

            try:
                cat = WorkCategory(first_part)
            except ValueError:
                cat = WorkCategory.UNCLASSIFIED

            for f in files:
                full_path = pathlib.Path(root) / f
                rel_path = os.path.normpath(os.path.relpath(full_path, self.repo_root)).replace("\\", "/")
                size = full_path.stat().st_size
                mtime = full_path.stat().st_mtime
                age_days = (now - mtime) / 86400.0
                mod_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)

                max_retention = _DEFAULT_RETENTION_DAYS.get(cat, 7)
                expired = age_days > max_retention

                item = WorkArtifactItem(
                    relative_path=rel_path,
                    category=cat,
                    size_bytes=size,
                    modified_at=mod_dt,
                    age_days=round(age_days, 2),
                    is_retention_exceeded=expired,
                )
                items.append(item)
                category_counts[cat.value] += 1
                total_bytes += size

        expired_items = [it for it in items if it.is_retention_exceeded]

        return WorkWorkspaceReport(
            workspace_path=str(self.work_dir),
            total_files=len(items),
            total_bytes=total_bytes,
            category_counts=category_counts,
            items=items,
            expired_items=expired_items,
        )


if __name__ == "__main__":
    auditor = WorkLifecycleAuditor()
    rep = auditor.audit()
    print(f".work Workspace Status: {rep.total_files} files, {rep.total_bytes} bytes")
    print("Category Breakdown:", rep.category_counts)
    print(f"Expired Items (Retention Exceeded): {len(rep.expired_items)}")
