from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from database.schema_version import SCHEMA_VERSION
from models import db


@pytest.mark.regression
def test_phase4_tables_constraints_and_schema_version(app):
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    assert {"plan_occurrence", "ledger_adjustment", "ledger_audit_event"}.issubset(tables)

    adjustment_columns = {column["name"] for column in inspector.get_columns("ledger_adjustment")}
    assert {
        "tenant_id",
        "original_transaction_id",
        "compensating_transaction_id",
        "kind",
        "status",
        "amount_delta",
        "original_amount_snapshot",
        "reason_code",
        "reason_text",
        "idempotency_key",
        "correlation_id",
        "metadata",
    }.issubset(adjustment_columns)

    unique_names = {item.get("name") for item in inspector.get_unique_constraints("ledger_adjustment")}
    assert "uq_ledger_adjustment_tenant_idempotency" in unique_names

    adjustment_fks = {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("ledger_adjustment")
    }
    audit_fks = {
        foreign_key["referred_table"]
        for foreign_key in inspector.get_foreign_keys("ledger_audit_event")
    }
    assert {"tenant", "transaction", "user"}.issubset(adjustment_fks)
    assert {"tenant", "transaction", "user", "ledger_adjustment"}.issubset(audit_fks)

    if "_schema_version" in tables:
        schema_row = db.session.execute(
            text("SELECT version FROM _schema_version WHERE version = :version"),
            {"version": SCHEMA_VERSION},
        ).scalar_one_or_none()
        assert schema_row == SCHEMA_VERSION
    else:
        # Unit fixture db.drop_all()/create_all() does not execute migrations;
        # the real local migration smoke test validates the persisted row.
        assert SCHEMA_VERSION == "v25.2"
    assert db.session.execute(text("PRAGMA integrity_check")).scalar() == "ok"
    assert db.session.execute(text("PRAGMA foreign_key_check")).fetchall() == []
