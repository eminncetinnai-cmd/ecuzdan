"""Phase 3 schema compatibility helpers for SQLite legacy databases."""
from sqlalchemy import inspect, text


def ensure_phase3_columns(engine):
    specs = {
        "transaction": {"updated_at": "DATETIME", "version": "INTEGER NOT NULL DEFAULT 1", "idempotency_key": "VARCHAR(64)"},
        "recurring_plan": {"updated_at": "DATETIME", "version": "INTEGER NOT NULL DEFAULT 1"},
        "asset": {"updated_at": "DATETIME", "version": "INTEGER NOT NULL DEFAULT 1"},
    }
    table_names = set(inspect(engine).get_table_names())
    with engine.begin() as conn:
        for table_name, columns in specs.items():
            if table_name not in table_names:
                continue
            existing = {column["name"] for column in inspect(engine).get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}'))
            conn.execute(text(f'UPDATE "{table_name}" SET version = 1 WHERE version IS NULL'))
            conn.execute(text(f'UPDATE "{table_name}" SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL'))
        if "transaction" in table_names:
            conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS uq_transaction_idempotency_key ON "transaction" (idempotency_key)'))
