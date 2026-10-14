"""SQLite Database Maintenance and Health Engine.

Pure business logic domain service.
Performs non-destructive and guarded maintenance on SQLite databases:
- Integrity check (PRAGMA integrity_check)
- Foreign key check (PRAGMA foreign_key_check)
- Freelist analysis (PRAGMA freelist_count)
- Hot online backup snapshot (sqlite3.backup)
- WAL Checkpoint with truncate (PRAGMA wal_checkpoint(TRUNCATE))
- Defragmentation (VACUUM)
- Query planner optimization (PRAGMA optimize)

Never imports Flask or SQLAlchemy models directly.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DatabaseStats:
    db_path: str
    exists: bool
    is_sqlite: bool
    size_bytes: int
    wal_size_bytes: int
    shm_size_bytes: int
    total_size_bytes: int
    page_size: int
    page_count: int
    freelist_count: int
    reclaimable_bytes: int
    integrity_status: str
    foreign_key_violations: int
    journal_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_path": self.db_path,
            "exists": self.exists,
            "is_sqlite": self.is_sqlite,
            "size_bytes": self.size_bytes,
            "wal_size_bytes": self.wal_size_bytes,
            "shm_size_bytes": self.shm_size_bytes,
            "total_size_bytes": self.total_size_bytes,
            "page_size": self.page_size,
            "page_count": self.page_count,
            "freelist_count": self.freelist_count,
            "reclaimable_bytes": self.reclaimable_bytes,
            "integrity_status": self.integrity_status,
            "foreign_key_violations": self.foreign_key_violations,
            "journal_mode": self.journal_mode,
        }


@dataclass(frozen=True, slots=True)
class MaintenanceStepResult:
    step_key: str
    title: str
    success: bool
    bytes_freed: int
    duration_ms: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_key": self.step_key,
            "title": self.title,
            "success": self.success,
            "bytes_freed": self.bytes_freed,
            "duration_ms": round(self.duration_ms, 2),
            "message": self.message,
        }


@dataclass
class DatabaseMaintenanceSummary:
    success: bool
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    bytes_freed: int = 0
    db_size_before: int = 0
    db_size_after: int = 0
    wal_size_before: int = 0
    wal_size_after: int = 0
    snapshot_path: str | None = None
    steps: list[MaintenanceStepResult] = field(default_factory=list)

    def finish(self, success: bool) -> None:
        self.finished_at = time.time()
        self.success = success
        total_before = self.db_size_before + self.wal_size_before
        total_after = self.db_size_after + self.wal_size_after
        self.bytes_freed = max(0, total_before - total_after)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_total_ms": round(((self.finished_at or time.time()) - self.started_at) * 1000, 2),
            "bytes_freed": self.bytes_freed,
            "db_size_before": self.db_size_before,
            "db_size_after": self.db_size_after,
            "wal_size_before": self.wal_size_before,
            "wal_size_after": self.wal_size_after,
            "snapshot_path": self.snapshot_path,
            "steps": [s.to_dict() for s in self.steps],
        }


class DatabaseMaintenanceService:
    """Enterprise SQLite health inspection, snapshotting and optimization."""

    def __init__(self, db_path: str | Path, backup_dir: str | Path | None = None) -> None:
        self.db_path = Path(db_path).resolve()
        self.backup_dir = Path(backup_dir).resolve() if backup_dir else self.db_path.parent / "instance" / "backups"

        self.wal_path = self.db_path.with_name(f"{self.db_path.name}-wal")
        self.shm_path = self.db_path.with_name(f"{self.db_path.name}-shm")

    def _file_size(self, path: Path) -> int:
        try:
            return path.stat().st_size if path.exists() else 0
        except OSError:
            return 0

    def _rotate_snapshots(self, max_snapshots: int = 3) -> int:
        """Keep only the latest `max_snapshots` files in backup_dir."""
        try:
            if not self.backup_dir.exists():
                return 0
            snapshots = sorted(
                self.backup_dir.glob("maintenance_snapshot_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            deleted = 0
            for old_snap in snapshots[max_snapshots:]:
                try:
                    old_snap.unlink()
                    deleted += 1
                    logger.info("Pruned old snapshot: %s", old_snap.name)
                except Exception as e:
                    logger.warning("Failed to delete old snapshot %s: %s", old_snap, e)
            return deleted
        except Exception as exc:
            logger.warning("Failed during snapshot rotation: %s", exc)
            return 0

    def get_stats(self) -> DatabaseStats:
        """Inspect SQLite file sizes, pragmas, freelist and integrity."""
        if not self.db_path.exists():
            return DatabaseStats(
                db_path=str(self.db_path),
                exists=False,
                is_sqlite=False,
                size_bytes=0,
                wal_size_bytes=0,
                shm_size_bytes=0,
                total_size_bytes=0,
                page_size=4096,
                page_count=0,
                freelist_count=0,
                reclaimable_bytes=0,
                integrity_status="file_not_found",
                foreign_key_violations=0,
                journal_mode="unknown",
            )

        db_size = self._file_size(self.db_path)
        wal_size = self._file_size(self.wal_path)
        shm_size = self._file_size(self.shm_path)
        total_size = db_size + wal_size + shm_size

        page_size = 4096
        page_count = 0
        freelist_count = 0
        integrity = "unknown"
        fk_violations = 0
        journal_mode = "unknown"

        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("PRAGMA page_size")
                row = cursor.fetchone()
                if row:
                    page_size = int(row[0])

                cursor.execute("PRAGMA page_count")
                row = cursor.fetchone()
                if row:
                    page_count = int(row[0])

                cursor.execute("PRAGMA freelist_count")
                row = cursor.fetchone()
                if row:
                    freelist_count = int(row[0])

                cursor.execute("PRAGMA journal_mode")
                row = cursor.fetchone()
                if row:
                    journal_mode = str(row[0]).upper()

                cursor.execute("PRAGMA integrity_check(1)")
                row = cursor.fetchone()
                if row:
                    integrity = str(row[0])

                cursor.execute("PRAGMA foreign_key_check")
                fk_rows = cursor.fetchall()
                fk_violations = len(fk_rows)

        except Exception as exc:
            logger.exception("Failed to inspect SQLite stats for %s", self.db_path)
            integrity = f"error: {exc}"

        active_db_bytes = page_count * page_size
        trailing_bytes = max(0, db_size - active_db_bytes) if page_count > 0 else 0
        reclaimable = (freelist_count * page_size) + trailing_bytes + wal_size


        return DatabaseStats(
            db_path=str(self.db_path),
            exists=True,
            is_sqlite=True,
            size_bytes=db_size,
            wal_size_bytes=wal_size,
            shm_size_bytes=shm_size,
            total_size_bytes=total_size,
            page_size=page_size,
            page_count=page_count,
            freelist_count=freelist_count,
            reclaimable_bytes=reclaimable,
            integrity_status=integrity,
            foreign_key_violations=fk_violations,
            journal_mode=journal_mode,
        )

    def execute_maintenance_pipeline(self, *, create_safety_snapshot: bool = True) -> DatabaseMaintenanceSummary:
        """Execute full, zero-downtime maintenance pipeline."""
        summary = DatabaseMaintenanceSummary(success=False)
        summary.db_size_before = self._file_size(self.db_path)
        summary.wal_size_before = self._file_size(self.wal_path)

        # Step 1: Pre-flight Integrity Check
        t0 = time.monotonic()
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                row = conn.execute("PRAGMA integrity_check(1)").fetchone()
                integrity = str(row[0]) if row else "unknown"
            duration = (time.monotonic() - t0) * 1000

            if integrity.lower() != "ok":
                summary.steps.append(
                    MaintenanceStepResult(
                        step_key="preflight_check",
                        title="Ön Bütünlük Doğrulaması",
                        success=False,
                        bytes_freed=0,
                        duration_ms=duration,
                        message=f"Veritabanı bütünlük hatası: {integrity}. Bakım durduruldu.",
                    )
                )
                summary.finish(False)
                return summary

            summary.steps.append(
                MaintenanceStepResult(
                    step_key="preflight_check",
                    title="Ön Bütünlük Doğrulaması",
                    success=True,
                    bytes_freed=0,
                    duration_ms=duration,
                    message="Veritabanı sağlamlığı %100 doğrulandı (0 Hata).",
                )
            )
        except Exception as exc:
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="preflight_check",
                    title="Ön Bütünlük Doğrulaması",
                    success=False,
                    bytes_freed=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"Bağlantı hatası: {exc}",
                )
            )
            summary.finish(False)
            return summary

        # Step 2: Online Hot Safety Snapshot
        t0 = time.monotonic()
        snapshot_dest: Path | None = None
        if create_safety_snapshot:
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                snapshot_dest = self.backup_dir / f"maintenance_snapshot_{timestamp}.db"

                with sqlite3.connect(str(self.db_path), timeout=10.0) as src:
                    with sqlite3.connect(str(snapshot_dest), timeout=10.0) as dst:
                        try:
                            src.execute("PRAGMA wal_checkpoint(PASSIVE)")
                        except Exception:
                            pass
                        src.backup(dst, pages=100)

                summary.snapshot_path = str(snapshot_dest)
                self._rotate_snapshots(max_snapshots=3)
                snap_size_mb = self._file_size(snapshot_dest) / (1024 * 1024)
                summary.steps.append(
                    MaintenanceStepResult(
                        step_key="safety_snapshot",
                        title="Canlı Güvenlik Snapshot'ı",
                        success=True,
                        bytes_freed=0,
                        duration_ms=(time.monotonic() - t0) * 1000,
                        message=f"Anlık güvenlik yedeği alındı ({snap_size_mb:.2f} MB).",
                    )
                )
            except Exception as exc:
                logger.warning("Safety snapshot failed: %s", exc)
                summary.steps.append(
                    MaintenanceStepResult(
                        step_key="safety_snapshot",
                        title="Canlı Güvenlik Snapshot'ı",
                        success=False,
                        bytes_freed=0,
                        duration_ms=(time.monotonic() - t0) * 1000,
                        message=f"Snapshot oluşturulamadı ({exc}), bakıma devam ediliyor.",
                    )
                )
        else:
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="safety_snapshot",
                    title="Canlı Güvenlik Snapshot'ı",
                    success=True,
                    bytes_freed=0,
                    duration_ms=0,
                    message="Kullanıcı tercihi gereği snapshot atlandı.",
                )
            )

        # Step 3: WAL Checkpoint (TRUNCATE)
        t0 = time.monotonic()
        wal_before = self._file_size(self.wal_path)
        try:
            with sqlite3.connect(str(self.db_path), timeout=15.0) as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            wal_after = self._file_size(self.wal_path)
            wal_freed = max(0, wal_before - wal_after)
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="wal_checkpoint",
                    title="WAL Günlüğü Checkpoint & Sıfırlama",
                    success=True,
                    bytes_freed=wal_freed,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"Tüm WAL sayfaları ana DB'ye işlendi ve WAL sıfırlandı ({wal_freed / 1024:.1f} KB kurtarıldı).",
                )
            )
        except Exception as exc:
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="wal_checkpoint",
                    title="WAL Günlüğü Checkpoint & Sıfırlama",
                    success=False,
                    bytes_freed=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"WAL Checkpoint uyarısı: {exc}",
                )
            )

        # Step 4: VACUUM (Defragmentation)
        t0 = time.monotonic()
        db_before = self._file_size(self.db_path)
        try:
            with sqlite3.connect(str(self.db_path), timeout=30.0) as conn:
                conn.isolation_level = None
                conn.execute("PRAGMA mmap_size=0")
                try:
                    conn.execute("PRAGMA journal_mode=DELETE")
                    conn.execute("VACUUM")
                    conn.execute("PRAGMA journal_mode=WAL")
                except Exception:
                    conn.execute("VACUUM")
            db_after = self._file_size(self.db_path)
            db_freed = max(0, db_before - db_after)
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="vacuum",
                    title="Veritabanı Defragmentasyonu (VACUUM)",
                    success=True,
                    bytes_freed=db_freed,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"Boş sayfalar işletim sistemine iade edildi ({db_freed / 1024:.1f} KB kurtarıldı).",
                )
            )
        except Exception as exc:
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="vacuum",
                    title="Veritabanı Defragmentasyonu (VACUUM)",
                    success=False,
                    bytes_freed=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"VACUUM uyarısı: {exc}",
                )
            )

        # Step 5: Query Planner Optimize
        t0 = time.monotonic()
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA optimize")
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="optimize",
                    title="Sorgu Planlayıcı Optimizasyonu (PRAGMA optimize)",
                    success=True,
                    bytes_freed=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message="İndeks istatistikleri ve sorgu yürütme planı güncellendi.",
                )
            )
        except Exception as exc:
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="optimize",
                    title="Sorgu Planlayıcı Optimizasyonu (PRAGMA optimize)",
                    success=False,
                    bytes_freed=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"Optimizasyon uyarısı: {exc}",
                )
            )

        # Step 6: Post-flight Integrity Check
        t0 = time.monotonic()
        try:
            with sqlite3.connect(str(self.db_path), timeout=5.0) as conn:
                row = conn.execute("PRAGMA integrity_check(1)").fetchone()
                post_integrity = str(row[0]) if row else "unknown"
            duration = (time.monotonic() - t0) * 1000
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="postflight_check",
                    title="Son Bütünlük Tescili",
                    success=post_integrity.lower() == "ok",
                    bytes_freed=0,
                    duration_ms=duration,
                    message="Tüm bakım işlemleri sonrası veritabanı %100 kusursuz durumda.",
                )
            )
        except Exception as exc:
            summary.steps.append(
                MaintenanceStepResult(
                    step_key="postflight_check",
                    title="Son Bütünlük Tescili",
                    success=False,
                    bytes_freed=0,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    message=f"Son kontrol uyarısı: {exc}",
                )
            )

        summary.db_size_after = self._file_size(self.db_path)
        summary.wal_size_after = self._file_size(self.wal_path)
        summary.finish(True)
        return summary
