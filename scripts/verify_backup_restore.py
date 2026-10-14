"""Verify a SQLite backup/restore round trip without mutating the live DB."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import tempfile
from pathlib import Path


def _read_only_uri(path: Path) -> str:
    return f"file:{path.resolve().as_posix()}?mode=ro"


def _pragma_one(connection: sqlite3.Connection, statement: str):
    return connection.execute(statement).fetchone()[0]


def verify(source: Path, requested_output: Path | None = None) -> tuple[dict, int]:
    if not source.is_file():
        raise FileNotFoundError(source)

    temporary_output = requested_output is None
    if requested_output is None:
        fd, temporary_path = tempfile.mkstemp(prefix="e_cuzdan_restore_smoke_", suffix=".db")
        os.close(fd)
        output = Path(temporary_path)
    else:
        output = requested_output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not temporary_output:
        output.unlink()

    source_connection = sqlite3.connect(_read_only_uri(source), uri=True, timeout=10)
    destination_connection = sqlite3.connect(str(output), timeout=10)
    try:
        source_connection.execute("PRAGMA busy_timeout=10000")
        destination_connection.execute("PRAGMA busy_timeout=10000")
        source_connection.backup(destination_connection, pages=100, sleep=0.05)
        destination_connection.commit()

        integrity = _pragma_one(destination_connection, "PRAGMA integrity_check")
        foreign_key_rows = destination_connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
        tables = [
            row[0]
            for row in destination_connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        schema_version = None
        if "_schema_version" in tables:
            columns = {
                row[1]
                for row in destination_connection.execute(
                    "PRAGMA table_info(_schema_version)"
                ).fetchall()
            }
            if "version" in columns:
                row = destination_connection.execute(
                    "SELECT version FROM _schema_version ORDER BY rowid DESC LIMIT 1"
                ).fetchone()
                schema_version = row[0] if row else None
        result = {
            "source": str(source.resolve()),
            "backup": str(output.resolve()),
            "source_bytes": source.stat().st_size,
            "backup_bytes": output.stat().st_size,
            "integrity_check": integrity,
            "foreign_key_violation_count": len(foreign_key_rows),
            "table_count": len(tables),
            "schema_version": schema_version,
            "temporary_backup_removed": temporary_output,
        }
        code = 0 if integrity == "ok" and not foreign_key_rows and tables else 2
        return result, code
    finally:
        destination_connection.close()
        source_connection.close()
        if temporary_output:
            output.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("e_cuzdan_v15.db"),
        help="SQLite database file to verify",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional restored copy to keep; otherwise a temporary copy is removed",
    )
    args = parser.parse_args()
    result, code = verify(args.source, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
