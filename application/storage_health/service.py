"""Application adapter for the Storage Health surface.

Provides read-only overview, guarded cleanup execution, full
zero-downtime smart tune-up maintenance, and historical audit records.
"""

from __future__ import annotations

import copy
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from domain.storage_health.cleanup_executor import CleanupExecutor, CleanupSummary
from domain.storage_health.dto import StorageScanDTO
from domain.storage_health.execution import build_execution_preview
from domain.storage_health.retention_policy import evaluate_retention, security_audit_log_policy
from domain.storage_health.safe_execution import build_safe_execution_plan
from domain.storage_health.services.data_hygiene_service import (
    DataHygieneService,
    HygieneExecutionResult,
)
from domain.storage_health.services.database_maintenance import (
    DatabaseMaintenanceService,
)
from domain.storage_health.services.recommender import StorageRecommender
from domain.storage_health.services.scanner import StorageScanner
from domain.storage_health.services.system_telemetry import SystemTelemetryService
from domain.storage_health.trend import compute_storage_trend

logger = logging.getLogger(__name__)


class StorageHealthApplicationService:
    """Build a bounded overview, disk telemetry, DB vitals, guarded maintenance, and audit history."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        cache_ttl_seconds: float = 10.0,
        max_files: int = 250_000,
        max_seconds: float = 90.0,
        db_path: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.cache_ttl_seconds = max(0.0, float(cache_ttl_seconds))
        self.max_files = max(1, int(max_files))
        self.max_seconds = max(1.0, float(max_seconds))
        self._cache: tuple[float, dict] | None = None
        self._lock = threading.RLock()
        self._executor = CleanupExecutor(self.project_root)

        self.db_path = Path(db_path).resolve() if db_path else self._resolve_db_path()
        self.db_maintenance = DatabaseMaintenanceService(
            self.db_path,
            backup_dir=self.project_root / "backups",
        )
        self.data_hygiene = DataHygieneService(self.db_path)
        self.telemetry_service = SystemTelemetryService(
            self.project_root,
            db_path=self.db_path,
        )

        self.history_file = self.project_root / "instance" / "maintenance_history.json"

    def _resolve_db_path(self) -> Path:
        """Locate primary SQLite database file in the project."""
        default = self.project_root / "e_cuzdan_v15.db"
        if default.exists():
            return default
        for f in self.project_root.glob("*.db"):
            if "snapshot" not in f.name and "backup" not in f.name:
                return f
        return default

    # ── History & Audit persistence ───────────────────────────────────────

    def _record_history(self, entry: dict[str, Any]) -> None:
        """Append record to immutable JSON history log (capped at 50 runs)."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            history = self.get_history(limit=50)
            history.insert(0, entry)
            history = history[:50]
            temp_file = self.history_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_file.replace(self.history_file)
        except Exception as exc:
            logger.warning("Failed to record maintenance history: %s", exc)

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return most recent maintenance execution records."""
        try:
            if not self.history_file.exists():
                return []
            content = self.history_file.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, list):
                return data[:limit]
            return []
        except Exception as exc:
            logger.warning("Failed to read maintenance history: %s", exc)
            return []

    # ── Read-only overview ────────────────────────────────────────────────

    def get_overview(self, *, refresh: bool = False) -> dict:
        now = time.monotonic()
        with self._lock:
            if (
                not refresh
                and self._cache is not None
                and now - self._cache[0] < self.cache_ttl_seconds
            ):
                return copy.deepcopy(self._cache[1])

            scan = StorageScanner(
                self.project_root,
                max_files=self.max_files,
                max_seconds=self.max_seconds,
            ).scan()
            recommendations = StorageRecommender(self.project_root).recommend(scan)
            execution_preview = build_execution_preview(recommendations)
            safe_execution_preview = build_safe_execution_plan(recommendations)
            security_retention_preview = evaluate_retention(
                security_audit_log_policy()
            )
            trend = compute_storage_trend(())

            telemetry = self.telemetry_service.get_disk_telemetry()
            db_vitals = self.db_maintenance.get_stats()
            breakdown = self.telemetry_service.get_storage_breakdown()
            history = self.get_history(limit=5)

            payload = {
                "mode": "OBSERVE_RECOMMEND",
                "read_only": True,
                "execute_available": True,
                "mutation_performed": False,
                "scan": StorageScanDTO.from_scan(scan).to_dict(),
                "recommendation": recommendations.to_dict(),
                "execution_preview": execution_preview.to_dict(),
                "safe_execution_preview": safe_execution_preview.to_dict(),
                "security_log_retention_preview": security_retention_preview.to_dict(),
                "trend": trend.to_dict(),
                "telemetry": telemetry.to_dict(),
                "database_vitality": db_vitals.to_dict(),
                "data_hygiene": self.data_hygiene.inspect_hygiene().to_dict(),
                "storage_breakdown": breakdown.to_dict(),
                "maintenance_history": history,
            }
            self._cache = (now, payload)
            return copy.deepcopy(payload)

    # ── Guarded cleanup ───────────────────────────────────────────────────

    def execute_cleanup(
        self,
        *,
        plan_hash: str,
        snapshot_id: str,
        candidate_ids: list[str],
    ) -> CleanupSummary:
        """Execute cleanup for the given candidate IDs."""
        if not candidate_ids:
            raise ValueError("no_candidates_selected")

        with self._lock:
            if self._cache is None:
                raise ValueError("no_cached_scan")

            cached_payload = self._cache[1]
            rec = cached_payload.get("recommendation", {})
            exec_preview = cached_payload.get("execution_preview", {})

            cached_plan_hash = exec_preview.get("plan_hash", "")
            if plan_hash and cached_plan_hash and plan_hash != cached_plan_hash:
                raise ValueError("plan_hash_mismatch")

            cached_snapshot_id = (
                exec_preview.get("snapshot_id")
                or rec.get("scan_snapshot_id")
                or rec.get("snapshot_token")
                or ""
            )
            if snapshot_id and cached_snapshot_id and snapshot_id != cached_snapshot_id:
                raise ValueError("snapshot_mismatch")

            candidates = list(rec.get("candidates", []))

        selected = set(candidate_ids)
        summary = self._executor.execute(candidates, selected_ids=selected)

        with self._lock:
            self._cache = None

        return summary

    # ── One-Click Full Smart Tune-Up ──────────────────────────────────────

    def execute_smart_tune_up(
        self,
        *,
        purge_cache: bool = True,
        purge_transient_data: bool = True,
        create_snapshot: bool = True,
        trigger_source: str = "manual_ui",
        user_name: str = "Yönetici",
    ) -> dict[str, Any]:
        """Execute full enterprise maintenance pipeline.

        1. Operational Data Hygiene (Aged read notifications & processed outbox pruning)
        2. Database Maintenance (Preflight -> Hot Snapshot -> WAL Checkpoint -> VACUUM -> Optimize)
        3. Safe Cache & Temp Purge (__pycache__, .pytest_cache, tmp/)
        4. Recalculate metrics, append history log & invalidate cache
        """
        logger.info(
            "Initiating smart tune-up pipeline (purge_cache=%s, purge_transient=%s, snapshot=%s, trigger=%s, user=%s)",
            purge_cache, purge_transient_data, create_snapshot, trigger_source, user_name
        )
        start_time = time.monotonic()

        # Step A1: Prune operational transient rows before compaction
        hygiene_summary: HygieneExecutionResult | None = None
        rows_pruned = 0
        if purge_transient_data:
            try:
                hygiene_summary = self.data_hygiene.execute_hygiene()
                rows_pruned = hygiene_summary.total_rows_pruned
                logger.info("Data hygiene pruned %d rows prior to database compaction.", rows_pruned)
            except Exception as exc:
                logger.warning("Data hygiene execution encountered warning: %s", exc)

        # Step A2: Run Database Maintenance Pipeline (VACUUM reclaims freed row space)
        db_summary = self.db_maintenance.execute_maintenance_pipeline(
            create_safety_snapshot=create_snapshot
        )

        # Step B: Purge safe caches if requested
        cache_freed = 0
        cache_items_count = 0
        if purge_cache:
            try:
                scan = StorageScanner(self.project_root, max_files=self.max_files, max_seconds=self.max_seconds).scan()
                recs = StorageRecommender(self.project_root).recommend(scan)
                safe_candidates = [
                    c for c in recs.candidates
                    if getattr(c, "policy_class", "") == "SAFE_AUTO"
                    or (isinstance(c, dict) and c.get("policy_class") == "SAFE_AUTO")
                ]
                safe_ids = {getattr(c, "candidate_id", "") or (c.get("candidate_id") if isinstance(c, dict) else "") for c in safe_candidates}
                safe_ids.discard("")
                if safe_ids:
                    candidate_dicts = [
                        c.to_dict() if hasattr(c, "to_dict") else c
                        for c in recs.candidates
                    ]
                    cleanup_summary = self._executor.execute(candidate_dicts, selected_ids=safe_ids)
                    cache_freed = cleanup_summary.bytes_freed
                    cache_items_count = len(cleanup_summary.executed)
            except Exception as exc:
                logger.warning("Cache purge during tune-up had warnings: %s", exc)

        total_bytes_freed = db_summary.bytes_freed + cache_freed
        duration_ms = (time.monotonic() - start_time) * 1000

        # Step C: Persist audit history record
        timestamp = time.time()
        history_entry = {
            "id": f"maint_{int(timestamp)}",
            "timestamp": timestamp,
            "date_str": time.strftime("%d.%m.%Y %H:%M"),
            "trigger_source": trigger_source,
            "user_name": user_name,
            "success": db_summary.success,
            "total_bytes_freed": total_bytes_freed,
            "db_bytes_freed": db_summary.bytes_freed,
            "cache_freed_bytes": cache_freed,
            "rows_pruned": rows_pruned,
            "duration_ms": round(duration_ms, 2),
            "snapshot_path": db_summary.snapshot_path,
        }
        self._record_history(history_entry)

        with self._lock:
            self._cache = None

        logger.info(
            "Smart tune-up completed: total_freed=%d bytes (DB=%d, Cache=%d, RowsPruned=%d) in %.2f ms",
            total_bytes_freed, db_summary.bytes_freed, cache_freed, rows_pruned, duration_ms
        )

        return {
            "success": db_summary.success,
            "total_bytes_freed": total_bytes_freed,
            "db_bytes_freed": db_summary.bytes_freed,
            "cache_freed_bytes": cache_freed,
            "cache_items_deleted": cache_items_count,
            "rows_pruned": rows_pruned,
            "hygiene_summary": hygiene_summary.to_dict() if hygiene_summary else None,
            "duration_ms": round(duration_ms, 2),
            "snapshot_path": db_summary.snapshot_path,
            "database_summary": db_summary.to_dict(),
            "history_entry": history_entry,
        }

