"""Unit tests for DataHygieneService and data retention policies."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from domain.storage_health.services.data_hygiene_service import (
    DataHygienePolicy,
    DataHygieneService,
)


@pytest.fixture
def memory_db() -> sqlite3.Connection:
    """Create in-memory SQLite database mimicking application transient tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Mimic notification schema
    conn.execute(
        """
        CREATE TABLE notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tenant_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            dedupe_key TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            expires_at TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # Mimic outbox_messages schema
    conn.execute(
        """
        CREATE TABLE outbox_messages (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            occurred_on TEXT NOT NULL,
            processed_on TEXT,
            error TEXT
        )
        """
    )

    # Mimic audit_log schema (protected)
    conn.execute(
        """
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    yield conn
    conn.close()


def test_data_hygiene_policy_validation():
    """Policy must reject negative or zero values."""
    with pytest.raises(ValueError, match="read_notifications_retention_days"):
        DataHygienePolicy(read_notifications_retention_days=0)

    with pytest.raises(ValueError, match="processed_outbox_retention_days"):
        DataHygienePolicy(processed_outbox_retention_days=-5)

    with pytest.raises(ValueError, match="batch_size"):
        DataHygienePolicy(batch_size=0)

    policy = DataHygienePolicy(read_notifications_retention_days=30, processed_outbox_retention_days=7)
    assert policy.read_notifications_retention_days == 30
    assert policy.processed_outbox_retention_days == 7


def test_data_hygiene_inspection_empty(memory_db):
    """Empty database should report 0 prunable rows."""
    service = DataHygieneService(":memory:", connection=memory_db)
    result = service.inspect_hygiene()

    assert result.total_prunable_rows == 0
    assert result.read_notifications_count == 0
    assert result.expired_notifications_count == 0
    assert result.processed_outbox_count == 0


def test_data_hygiene_notification_pruning(memory_db):
    """Aged read notifications and expired notifications are pruned; unread & fresh are preserved."""
    service = DataHygieneService(":memory:", connection=memory_db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    date_90_days_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    date_10_days_ago = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    date_future = (now + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
    date_yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Aged read notification -> SHOULD BE PRUNED
    memory_db.execute(
        "INSERT INTO notification (id, user_id, tenant_id, category, title, dedupe_key, is_read, expires_at, created_at) "
        "VALUES (1, 1, 't1', 'sys', 'Old Read', 'k1', 1, NULL, ?)",
        (date_90_days_ago,),
    )
    # 2. Aged UNREAD notification -> MUST NOT BE PRUNED (retention rule)
    memory_db.execute(
        "INSERT INTO notification (id, user_id, tenant_id, category, title, dedupe_key, is_read, expires_at, created_at) "
        "VALUES (2, 1, 't1', 'sys', 'Old Unread', 'k2', 0, NULL, ?)",
        (date_90_days_ago,),
    )
    # 3. Fresh read notification -> MUST NOT BE PRUNED (< 60 days)
    memory_db.execute(
        "INSERT INTO notification (id, user_id, tenant_id, category, title, dedupe_key, is_read, expires_at, created_at) "
        "VALUES (3, 1, 't1', 'sys', 'Fresh Read', 'k3', 1, NULL, ?)",
        (date_10_days_ago,),
    )
    # 4. Expired notification -> SHOULD BE PRUNED regardless of read state
    memory_db.execute(
        "INSERT INTO notification (id, user_id, tenant_id, category, title, dedupe_key, is_read, expires_at, created_at) "
        "VALUES (4, 1, 't1', 'sys', 'Expired Alert', 'k4', 0, ?, ?)",
        (date_yesterday, date_10_days_ago),
    )
    # 5. Future-expiring notification -> MUST NOT BE PRUNED
    memory_db.execute(
        "INSERT INTO notification (id, user_id, tenant_id, category, title, dedupe_key, is_read, expires_at, created_at) "
        "VALUES (5, 1, 't1', 'sys', 'Active Alert', 'k5', 0, ?, ?)",
        (date_future, date_10_days_ago),
    )
    memory_db.commit()

    # Step A: Inspect
    inspection = service.inspect_hygiene(DataHygienePolicy(read_notifications_retention_days=60))
    assert inspection.read_notifications_count == 1
    assert inspection.expired_notifications_count == 1
    assert inspection.total_prunable_rows == 2

    # Step B: Execute Dry Run
    dry_result = service.execute_hygiene(DataHygienePolicy(read_notifications_retention_days=60, dry_run=True))
    assert dry_result.dry_run is True
    assert dry_result.total_rows_pruned == 0
    # Verify rows still exist
    cur = memory_db.execute("SELECT COUNT(*) FROM notification")
    assert cur.fetchone()[0] == 5

    # Step C: Real Execution
    exec_result = service.execute_hygiene(DataHygienePolicy(read_notifications_retention_days=60))
    assert exec_result.success is True
    assert exec_result.notifications_pruned == 2
    assert exec_result.total_rows_pruned == 2

    # Verify surviving records
    surviving_ids = [r[0] for r in memory_db.execute("SELECT id FROM notification ORDER BY id").fetchall()]
    assert surviving_ids == [2, 3, 5]  # Old unread, fresh read, active future alert


def test_data_hygiene_outbox_pruning(memory_db):
    """Processed outbox messages older than threshold are pruned; pending/recent are preserved."""
    service = DataHygieneService(":memory:", connection=memory_db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    date_20_days_ago = (now - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
    date_2_days_ago = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Aged processed message -> SHOULD BE PRUNED
    memory_db.execute(
        "INSERT INTO outbox_messages (id, event_type, payload, occurred_on, processed_on) "
        "VALUES ('msg-old-proc', 'TxCreated', '{}', ?, ?)",
        (date_20_days_ago, date_20_days_ago),
    )
    # 2. Fresh processed message -> MUST NOT BE PRUNED (< 14 days)
    memory_db.execute(
        "INSERT INTO outbox_messages (id, event_type, payload, occurred_on, processed_on) "
        "VALUES ('msg-fresh-proc', 'TxCreated', '{}', ?, ?)",
        (date_2_days_ago, date_2_days_ago),
    )
    # 3. Pending/unprocessed message (even if old) -> MUST NEVER BE PRUNED
    memory_db.execute(
        "INSERT INTO outbox_messages (id, event_type, payload, occurred_on, processed_on) "
        "VALUES ('msg-old-pending', 'TxCreated', '{}', ?, NULL)",
        (date_20_days_ago,),
    )
    memory_db.commit()

    inspection = service.inspect_hygiene(DataHygienePolicy(processed_outbox_retention_days=14))
    assert inspection.processed_outbox_count == 1
    assert inspection.total_prunable_rows == 1

    exec_result = service.execute_hygiene(DataHygienePolicy(processed_outbox_retention_days=14))
    assert exec_result.success is True
    assert exec_result.outbox_messages_pruned == 1

    surviving_ids = [r[0] for r in memory_db.execute("SELECT id FROM outbox_messages ORDER BY id").fetchall()]
    assert surviving_ids == ["msg-fresh-proc", "msg-old-pending"]


def test_protected_tables_compliance(memory_db):
    """AuditLog and compliance tables must never be deleted or purged."""
    memory_db.execute("INSERT INTO audit_log (action, timestamp) VALUES ('USER_LOGIN', '2026-01-01 00:00:00')")
    memory_db.commit()

    service = DataHygieneService(":memory:", connection=memory_db)
    assert "audit_log" in service.PROTECTED_TABLES
    assert "transaction" in service.PROTECTED_TABLES

    # Execute hygiene
    res = service.execute_hygiene()
    assert res.success is True

    # Verify audit_log is completely untouched
    cur = memory_db.execute("SELECT COUNT(*) FROM audit_log")
    assert cur.fetchone()[0] == 1
