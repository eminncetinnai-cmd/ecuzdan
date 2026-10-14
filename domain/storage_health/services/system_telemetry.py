"""System & Storage Telemetry Service.

Pure business logic domain service.
Collects OS disk statistics, storage category breakdowns, and log sizes.
Never imports Flask or database models directly.
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DiskTelemetry:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percentage: float
    health_status: str  # "OPTIMAL", "WARNING", "CRITICAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "used_percentage": round(self.used_percentage, 1),
            "health_status": self.health_status,
        }


@dataclass(frozen=True, slots=True)
class CategorySizeItem:
    key: str
    label: str
    bytes: int
    percentage: float
    color: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "bytes": self.bytes,
            "percentage": round(self.percentage, 1),
            "color": self.color,
        }


@dataclass(frozen=True, slots=True)
class StorageBreakdown:
    total_project_bytes: int
    categories: tuple[CategorySizeItem, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_project_bytes": self.total_project_bytes,
            "categories": [c.to_dict() for c in self.categories],
        }


class SystemTelemetryService:
    """Collects operating system disk usage and project storage category distribution."""

    def __init__(self, project_root: str | Path, db_path: str | Path | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.db_path = Path(db_path).resolve() if db_path else self.project_root / "e_cuzdan_v15.db"

    def get_disk_telemetry(self) -> DiskTelemetry:
        """Query operating system disk usage on the project partition."""
        try:
            usage = shutil.disk_usage(str(self.project_root))
            total = usage.total
            used = usage.used
            free = usage.free
            pct = (used / total * 100) if total > 0 else 0.0

            if pct >= 90.0:
                health = "CRITICAL"
            elif pct >= 75.0:
                health = "WARNING"
            else:
                health = "OPTIMAL"

            return DiskTelemetry(
                total_bytes=total,
                used_bytes=used,
                free_bytes=free,
                used_percentage=pct,
                health_status=health,
            )
        except Exception as exc:
            logger.warning("Failed to query disk usage: %s", exc)
            return DiskTelemetry(
                total_bytes=0,
                used_bytes=0,
                free_bytes=0,
                used_percentage=0.0,
                health_status="UNKNOWN",
            )

    def _dir_size(self, path: Path) -> int:
        total = 0
        if not path.exists():
            return 0
        try:
            for root, _, files in os.walk(str(path)):
                for f in files:
                    try:
                        p = Path(root) / f
                        if not p.is_symlink():
                            total += p.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
        return total

    def _file_size(self, path: Path) -> int:
        try:
            return path.stat().st_size if path.exists() else 0
        except OSError:
            return 0

    def get_storage_breakdown(self) -> StorageBreakdown:
        """Calculate storage breakdown across 5 key categories for Chart.js Donut."""
        # 1. Database (.db + .db-wal + .db-shm)
        db_bytes = (
            self._file_size(self.db_path)
            + self._file_size(self.db_path.with_name(f"{self.db_path.name}-wal"))
            + self._file_size(self.db_path.with_name(f"{self.db_path.name}-shm"))
        )

        # 2. Backups (instance/backups/ or backups/)
        backup_bytes = self._dir_size(self.project_root / "instance" / "backups") + self._dir_size(self.project_root / "backups")


        # 3. Logs (logs/)
        logs_dir = self.project_root / "logs"
        log_bytes = self._dir_size(logs_dir)

        # 4. Cache & Temp (__pycache__, .pytest_cache, tmp/)
        cache_bytes = 0
        for p in self.project_root.rglob("__pycache__"):
            cache_bytes += self._dir_size(p)
        cache_bytes += self._dir_size(self.project_root / ".pytest_cache")
        cache_bytes += self._dir_size(self.project_root / "tmp")

        # 5. Application Code & Static (everything else in root excluding .git and .venv)
        static_bytes = self._dir_size(self.project_root / "static")
        templates_bytes = self._dir_size(self.project_root / "templates")
        src_dirs = ["domain", "application", "infrastructure", "repositories", "routes", "shared", "utils"]
        code_bytes = sum(self._dir_size(self.project_root / d) for d in src_dirs)
        app_core_bytes = static_bytes + templates_bytes + code_bytes

        total = db_bytes + backup_bytes + log_bytes + cache_bytes + app_core_bytes
        safe_total = max(1, total)

        categories = (
            CategorySizeItem(
                key="database",
                label="Veritabanı Motoru (.db & WAL)",
                bytes=db_bytes,
                percentage=(db_bytes / safe_total) * 100,
                color="#0ea5e9",  # Sky-500
            ),
            CategorySizeItem(
                key="backups",
                label="Sistem Yedekleri (backups/)",
                bytes=backup_bytes,
                percentage=(backup_bytes / safe_total) * 100,
                color="#8b5cf6",  # Violet-500
            ),
            CategorySizeItem(
                key="logs",
                label="Uygulama & Güvenlik Logları (logs/)",
                bytes=log_bytes,
                percentage=(log_bytes / safe_total) * 100,
                color="#f59e0b",  # Amber-500
            ),
            CategorySizeItem(
                key="cache",
                label="Geçici Dosyalar & Önbellekler",
                bytes=cache_bytes,
                percentage=(cache_bytes / safe_total) * 100,
                color="#ef4444",  # Rose-500
            ),
            CategorySizeItem(
                key="app_core",
                label="Uygulama Kodu & Statik Varlıklar",
                bytes=app_core_bytes,
                percentage=(app_core_bytes / safe_total) * 100,
                color="#10b981",  # Emerald-500
            ),
        )

        return StorageBreakdown(
            total_project_bytes=total,
            categories=categories,
        )
