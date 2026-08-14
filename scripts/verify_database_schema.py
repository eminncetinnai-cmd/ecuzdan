#!/usr/bin/env python3
"""Verify that the E-Cüzdan runtime database exposes its required tables."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Importing the application uses the same configuration and bootstrap path as runtime.
from app import app  # noqa: E402
from models import db  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

REQUIRED_TABLES = frozenset(
    {
        '_schema_version',
        'tenant',
        'user',
        'category',
        'asset',
        'asset_type',
        'asset_sector',
        'transaction',
        'asset_transaction',
        'recurring_plan',
        'notification',
        'user_preference',
    }
)


def main() -> int:
    with app.app_context():
        actual_tables = set(inspect(db.engine).get_table_names())

    missing = sorted(REQUIRED_TABLES - actual_tables)
    if missing:
        print('Database schema verification failed.')
        print('Missing tables: ' + ', '.join(missing))
        return 1

    print(f'Database schema verification passed ({len(actual_tables)} tables discovered).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
