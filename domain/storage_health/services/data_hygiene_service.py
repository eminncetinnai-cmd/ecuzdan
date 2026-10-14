"""Data Hygiene and Lifecycle Pruning Engine.

Pure business logic domain service for operational database hygiene.
Systematically purges transient rows (read notifications, processed outbox records)
according to strict retention policies and safety guardrails.

Compliance Rules:
- Audit logs (audit_log) and financial ledger tables are NEVER touched (append-only compliance).
- Unread notifications are NEVER purged (unless explicitly expired).
- Unprocessed or pending outbox messages are NEVER purged.
- Deletions are executed in bounded batches to prevent long SQLite table locks.
- Zero dependencies on Flask or SQLAlchemy ORM models.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DataHygienePolicy:
    """Configurable data retention and hygiene rules."""

    read_notifications_retention_days: int = 60
    processed_outbox_retention_days: int = 14
    batch_size: int = 500
    dry_run: bool = False

    def __post_init__(self) -> None:
        if self.read_notifications_retention_days < 1:
            raise ValueError("read_notifications_retention_days must be >= 1")
        if self.processed_outbox_retention_days < 1:
            raise ValueError("processed_outbox_retention_days must be >= 1")
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")


@dataclass(frozen=True, slots=True)
class HygieneInspectionResult:
    """Read-only audit of prunable rows across transient tables."""

    read_notifications_count: int
    expired_notifications_count: int
    processed_outbox_count: int
    total_prunable_rows: int
    table_breakdown: dict[str, int]
    inspected_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "read_notifications_count": self.read_notifications_count,
            "expired_notifications_count": self.expired_notifications_count,
            "processed_outbox_count": self.processed_outbox_count,
            "total_prunable_rows": self.total_prunable_rows,
            "table_breakdown": dict(self.table_breakdown),
            "inspected_at": self.inspected_at,
        }


@dataclass
class HygieneExecutionResult:
    """Result of executing data hygiene pruning."""

    success: bool
    notifications_pruned: int = 0
    outbox_messages_pruned: int = 0
    total_rows_pruned: int = 0
    duration_ms: float = 0.0
    dry_run: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "notifications_pruned": self.notifications_pruned,
            "outbox_messages_pruned": self.outbox_messages_pruned,
            "total_rows_pruned": self.total_rows_pruned,
            "duration_ms": round(self.duration_ms, 2),
            "dry_run": self.dry_run,
            "message": self.message,
        }


class DataHygieneService:
    """Service to inspect and prune transient operational data safely."""

    # Explicit compliance blacklist: tables that must NEVER be purged or modified
    PROTECTED_TABLES: frozenset[str] = frozenset({
        "audit_log",
        "storage_cleanup_audit",
        "user",
        "tenant",
        "account",
        "journal_entry",
        "ledger_line",
        "transaction",
        "payment",
        "recurring_plan",
        "asset",
        "asset_transaction",
        "bank_account",
        "bank_statement_snapshot",
    })

    def __init__(self, db_path: str | Path, connection: sqlite3.Connection | None = None) -> None:
        self.db_path = Path(db_path).resolve()
        self._provided_conn = connection

    def _get_connection(self) -> sqlite3.Connection:
        if self._provided_conn is not None:
            return self._provided_conn
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        cursor = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return cursor.fetchone() is not None

    def inspect_hygiene(
        self,
        policy: DataHygienePolicy | None = None,
    ) -> HygieneInspectionResult:
        """Inspect count of prunable rows without mutating anything (read-only)."""
        active_policy = policy or DataHygienePolicy()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        notif_cutoff = (
            now - timedelta(days=active_policy.read_notifications_retention_days)
        ).strftime("%Y-%m-%d %H:%M:%S")
        outbox_cutoff = (
            now - timedelta(days=active_policy.processed_outbox_retention_days)
        ).strftime("%Y-%m-%d %H:%M:%S")

        read_notifs = 0
        expired_notifs = 0
        processed_outbox = 0

        conn = self._get_connection()
        should_close = self._provided_conn is None
        try:
            if self._table_exists(conn, "notification"):
                # Read notifications older than retention days
                cur = conn.execute(
                    "SELECT COUNT(*) FROM notification WHERE is_read = 1 AND created_at < ?",
                    (notif_cutoff,),
                )
                row = cur.fetchone()
                read_notifs = int(row[0]) if row else 0

                # Expired notifications (regardless of read state, past expires_at)
                cur = conn.execute(
                    "SELECT COUNT(*) FROM notification WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (now_str,),
                )
                row = cur.fetchone()
                expired_notifs = int(row[0]) if row else 0

            if self._table_exists(conn, "outbox_messages"):
                cur = conn.execute(
                    "SELECT COUNT(*) FROM outbox_messages WHERE processed_on IS NOT NULL AND processed_on < ?",
                    (outbox_cutoff,),
                )
                row = cur.fetchone()
                processed_outbox = int(row[0]) if row else 0

        finally:
            if should_close:
                conn.close()

        total = read_notifs + expired_notifs + processed_outbox
        table_breakdown = {
            "notification_read_aged": read_notifs,
            "notification_expired": expired_notifs,
            "outbox_processed_aged": processed_outbox,
        }

        return HygieneInspectionResult(
            read_notifications_count=read_notifs,
            expired_notifications_count=expired_notifs,
            processed_outbox_count=processed_outbox,
            total_prunable_rows=total,
            table_breakdown=table_breakdown,
            inspected_at=now_str,
        )

    def execute_hygiene(
        self,
        policy: DataHygienePolicy | None = None,
    ) -> HygieneExecutionResult:
        """Atomically prune transient operational data in safe batches."""
        active_policy = policy or DataHygienePolicy()
        t0 = time.monotonic()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        notif_cutoff = (
            now - timedelta(days=active_policy.read_notifications_retention_days)
        ).strftime("%Y-%m-%d %H:%M:%S")
        outbox_cutoff = (
            now - timedelta(days=active_policy.processed_outbox_retention_days)
        ).strftime("%Y-%m-%d %H:%M:%S")

        if active_policy.dry_run:
            inspection = self.inspect_hygiene(active_policy)
            duration_ms = (time.monotonic() - t0) * 1000
            return HygieneExecutionResult(
                success=True,
                notifications_pruned=0,
                outbox_messages_pruned=0,
                total_rows_pruned=0,
                duration_ms=duration_ms,
                dry_run=True,
                message=f"Dry run complete: {inspection.total_prunable_rows} rows eligible for pruning.",
            )

        conn = self._get_connection()
        should_close = self._provided_conn is None
        notifs_pruned = 0
        outbox_pruned = 0

        try:
            # Step 1: Prune aged read notifications in batches
            if self._table_exists(conn, "notification"):
                # Safety check against compliance rules
                if "notification" in self.PROTECTED_TABLES:
                    raise RuntimeError("Compliance error: notification table is marked protected")

                while True:
                    cur = conn.execute(
                        """
                        DELETE FROM notification
                        WHERE id IN (
                            SELECT id FROM notification
                            WHERE is_read = 1 AND created_at < ?
                            LIMIT ?
                        )
                        """,
                        (notif_cutoff, active_policy.batch_size),
                    )
                    deleted = cur.rowcount
                    if deleted <= 0:
                        break
                    notifs_pruned += deleted
                    conn.commit()

                # Also prune expired notifications
                while True:
                    cur = conn.execute(
                        """
                        DELETE FROM notification
                        WHERE id IN (
                            SELECT id FROM notification
                            WHERE expires_at IS NOT NULL AND expires_at < ?
                            LIMIT ?
                        )
                        """,
                        (now_str, active_policy.batch_size),
                    )
                    deleted = cur.rowcount
                    if deleted <= 0:
                        break
                    notifs_pruned += deleted
                    conn.commit()

            # Step 2: Prune aged processed outbox messages in batches
            if self._table_exists(conn, "outbox_messages"):
                if "outbox_messages" in self.PROTECTED_TABLES:
                    raise RuntimeError("Compliance error: outbox_messages table is marked protected")

                while True:
                    cur = conn.execute(
                        """
                        DELETE FROM outbox_messages
                        WHERE id IN (
                            SELECT id FROM outbox_messages
                            WHERE processed_on IS NOT NULL AND processed_on < ?
                            LIMIT ?
                        )
                        """,
                        (outbox_cutoff, active_policy.batch_size),
                    )
                    deleted = cur.rowcount
                    if deleted <= 0:
                        break
                    outbox_pruned += deleted
                    conn.commit()

            conn.commit()
            duration_ms = (time.monotonic() - t0) * 1000
            total_pruned = notifs_pruned + outbox_pruned
            logger.info(
                "Data hygiene pruning completed: %d notifications, %d outbox messages (%d total) in %.2f ms",
                notifs_pruned,
                outbox_pruned,
                total_pruned,
                duration_ms,
            )
            return HygieneExecutionResult(
                success=True,
                notifications_pruned=notifs_pruned,
                outbox_messages_pruned=outbox_pruned,
                total_rows_pruned=total_pruned,
                duration_ms=duration_ms,
                dry_run=False,
                message=f"Successfully pruned {total_pruned} transient rows.",
            )

        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            duration_ms = (time.monotonic() - t0) * 1000
            logger.exception("Data hygiene execution failed: %s", exc)
            return HygieneExecutionResult(
                success=False,
                notifications_pruned=notifs_pruned,
                outbox_messages_pruned=outbox_pruned,
                total_rows_pruned=notifs_pruned + outbox_pruned,
                duration_ms=duration_ms,
                dry_run=False,
                message=f"Pruning failed: {exc}",
            )
        finally:
            if should_close:
                conn.close()
