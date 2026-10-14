#!/usr/bin/env python3
"""E-Cüzdan SQLite -> PostgreSQL Data Migration Engine.

Migrates all tables, schemas, constraints, sequences, and cryptographic ledger
records from a local SQLite database to an enterprise PostgreSQL instance.

Usage:
    # 1. Test inspection and plan (Dry Run):
    python scripts/migrate_sqlite_to_postgres.py --dry-run

    # 2. Execute migration with explicit PostgreSQL URL:
    python scripts/migrate_sqlite_to_postgres.py --target-url postgresql+psycopg://user:pass@localhost:5432/ecuzdan

    # 3. Verify parity between SQLite and PostgreSQL:
    python scripts/migrate_sqlite_to_postgres.py --target-url postgresql+psycopg://user:pass@localhost:5432/ecuzdan --verify-only
"""
from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

# Windows console encoding uyumluluğu
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("migration")


def get_sqlite_tables(sqlite_path: Path) -> list[str]:
    """Retrieve user tables from SQLite in deterministic order."""
    conn = sqlite3.connect(str(sqlite_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_sqlite_table_counts(sqlite_path: Path, tables: list[str]) -> dict[str, int]:
    """Return dictionary of table row counts in SQLite."""
    conn = sqlite3.connect(str(sqlite_path))
    counts = {}
    try:
        cur = conn.cursor()
        for tbl in tables:
            cur.execute(f"SELECT COUNT(*) FROM [{tbl}]")
            counts[tbl] = cur.fetchone()[0]
    finally:
        conn.close()
    return counts


def read_sqlite_table_data(sqlite_path: Path, table_name: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Read all rows and column names from a SQLite table."""
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM [{table_name}]")
        rows = cur.fetchall()
        if not rows:
            # Table is empty, fetch column names via PRAGMA
            cur.execute(f"PRAGMA table_info([{table_name}])")
            cols = [r[1] for r in cur.fetchall()]
            return cols, []
        cols = list(rows[0].keys())
        data = [dict(r) for r in rows]
        return cols, data
    finally:
        conn.close()


def execute_migration(
    sqlite_path: Path,
    target_url: str,
    dry_run: bool = False,
    verify_only: bool = False,
    batch_size: int = 500,
) -> int:
    """Migrate SQLite data to target PostgreSQL database."""
    if not sqlite_path.exists():
        logger.error("SQLite veritabanı bulunamadı: %s", sqlite_path)
        return 1

    tables = get_sqlite_tables(sqlite_path)
    counts = get_sqlite_table_counts(sqlite_path, tables)
    populated = {t: c for t, c in counts.items() if c > 0}

    print("=" * 70)
    print("  E-CÜZDAN SQLITE ➔ POSTGRESQL MİGRASYON MOTORU")
    print("=" * 70)
    print(f"Kaynak SQLite : {sqlite_path.resolve()} ({len(tables)} tablo)")
    print(f"Dolu Tablolar : {len(populated)} adet ({sum(populated.values())} toplam kayıt)")
    print(f"Hedef URL     : {target_url if not dry_run else '[DRY-RUN - Bağlantı yapılmayacak]'}")
    print("-" * 70)

    if dry_run:
        print("\n[PLAN] Tablo Kayıt Dağılımı:")
        for tbl, cnt in sorted(populated.items(), key=lambda x: -x[1]):
            print(f"  • {tbl:<30} : {cnt:>6} kayıt")
        print("\n[BİLGİ] Dry-run modu tamamlandı. Hiçbir veri yazılmadı.")
        return 0

    try:
        from sqlalchemy import create_engine, inspect, text
    except ImportError:
        logger.error("SQLAlchemy bulunamadı. Lütfen virtualenv içinde çalıştırın.")
        return 1

    # Connect to PostgreSQL
    logger.info("Hedef PostgreSQL veritabanına bağlanılıyor...")
    engine = create_engine(target_url, future=True)

    with engine.connect() as test_conn:
        db_type = test_conn.dialect.name
        if db_type != "postgresql":
            logger.warning("Hedef dialect '%s' (PostgreSQL bekleniyordu).", db_type)

    if verify_only:
        print("\n[DOĞRULAMA] SQLite vs PostgreSQL Karşılaştırması:")
        all_match = True
        inspector = inspect(engine)
        pg_tables = set(inspector.get_table_names())

        with engine.connect() as conn:
            for tbl, sqlite_count in populated.items():
                if tbl not in pg_tables:
                    print(f"  ❌ {tbl:<30} : SQLite={sqlite_count} | PostgreSQL=TABLO YOK")
                    all_match = False
                    continue
                pg_count = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
                match = sqlite_count == pg_count
                status = "✅" if match else "❌"
                if not match:
                    all_match = False
                print(f"  {status} {tbl:<30} : SQLite={sqlite_count:>5} | PostgreSQL={pg_count:>5}")

        engine.dispose()
        print("-" * 70)
        if all_match:
            print("✨ TÜM KAYIT SAYILARI VE TABLOLAR BİREBİR EŞLEŞTİ! MİGRASYON BAŞARILI.")
            return 0
        else:
            print("⚠️ BAZI TABLOLARDA SAYI UYUMSUZLUĞU TESPİT EDİLDİ.")
            return 1

    # Normal migration execution
    # 1. Initialize schema in target DB using models
    logger.info("Hedef şema modelleri hazırlanıyor (create_all)...")
    from app import app
    from models import db
    try:
        from domain.storage_health.persistence_models import StorageCleanupAudit, StorageScanHistory  # noqa: F401
    except ImportError:
        pass

    # Geçici app context ile hedef engine üzerinde tabloları oluştur
    with app.app_context():
        # Hedef veritabanında tabloları oluştur
        metadata = db.metadata
        metadata.create_all(bind=engine)
        with engine.begin() as init_conn:
            init_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS "_schema_version" (
                    version VARCHAR(64) PRIMARY KEY,
                    applied_at VARCHAR(64)
                );
            """))
        logger.info("Hedef şema ve tablolar başarıyla oluşturuldu.")

    start_time = time.time()
    total_migrated = 0

    # 2. Transfer data table by table
    # Bağımlılık sıralaması: önce ana tablolar (tenant, user, category vb.)
    fk_priority = {
        "tenant": 1,
        "user": 2,
        "_schema_version": 3,
        "asset_type": 4,
        "asset_sector": 5,
        "category": 6,
        "quiz_question": 7,
        "strategy_settings": 8,
    }
    sorted_tables = sorted(tables, key=lambda t: fk_priority.get(t, 99))

    is_pg = False
    with engine.begin() as conn:
        is_pg = conn.dialect.name == "postgresql"

        for tbl in sorted_tables:
            row_count = counts.get(tbl, 0)
            if row_count == 0:
                continue

            cols, rows = read_sqlite_table_data(sqlite_path, tbl)
            if not rows:
                continue

            target_table = metadata.tables.get(tbl)
            bool_col_set = set()
            if target_table is not None:
                bool_col_set = {c.name for c in target_table.columns if 'Bool' in type(c.type).__name__}

            for row in rows:
                for b_col in bool_col_set:
                    if b_col in row and row[b_col] is not None:
                        row[b_col] = bool(row[b_col])

            logger.info("Aktarılıyor: %s (%d kayıt)...", tbl, len(rows))

            # Batch inserts
            col_names = ", ".join([f'"{c}"' for c in cols])
            placeholders = ", ".join([f":{c}" for c in cols])
            if is_pg:
                insert_stmt = text(f'INSERT INTO "{tbl}" ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING')
            else:
                insert_stmt = text(f'INSERT INTO "{tbl}" ({col_names}) VALUES ({placeholders})')

            for i in range(0, len(rows), batch_size):
                chunk = rows[i : i + batch_size]
                conn.execute(insert_stmt, chunk)

            total_migrated += len(rows)

    # Veriler güvenle commit edildi. Şimdi PostgreSQL sequence değerlerini güncelle
    if is_pg:
        logger.info("PostgreSQL Primary Key Sequence değerleri senkronize ediliyor...")
        with engine.connect() as conn:
            for tbl in sorted_tables:
                if counts.get(tbl, 0) == 0:
                    continue
                target_table = metadata.tables.get(tbl)
                # Sadece Integer tipinde id kolonu olan tablolar için sequence güncelle
                if target_table is not None and "id" in target_table.columns and "Integer" in type(target_table.columns["id"].type).__name__:
                    try:
                        seq_name = conn.execute(
                            text(f"SELECT pg_get_serial_sequence('\"{tbl}\"', 'id')")
                        ).scalar()
                        if seq_name:
                            conn.execute(
                                text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM \"{tbl}\"), 1), true)")
                            )
                            conn.commit()
                            logger.info("Sequence güncellendi: %s -> %s", tbl, seq_name)
                    except Exception as seq_err:
                        logger.warning("Sequence atlandı (%s): %s", tbl, seq_err)

    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"🎉 MİGRASYON TAMAMLANDI! {total_migrated} kayıt {elapsed:.2f} saniyede aktarıldı.")
    print("=" * 70)

    engine.dispose()

    # Verification run
    return execute_migration(sqlite_path, target_url, verify_only=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="E-Cüzdan SQLite ➔ PostgreSQL Canlı Veri Aktarım Betiği"
    )
    parser.add_argument(
        "--sqlite-path",
        default="e_cuzdan_v15.db",
        help="Kaynak SQLite veritabanı dosya yolu (Varsayılan: e_cuzdan_v15.db)",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("DATABASE_URL"),
        help="Hedef PostgreSQL bağlantı dizesi (Varsayılan: DATABASE_URL env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Veritabanına yazmadan sadece kaynak analizi ve planı gösterir",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Kaynak SQLite ile hedef PostgreSQL kayıt sayılarını karşılaştırır",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Toplu ekleme blok boyutu (Varsayılan: 500)",
    )

    args = parser.parse_args()
    sqlite_file = Path(args.sqlite_path)

    if not args.dry_run and not args.target_url:
        print("HATA: --target-url belirtilmedi veya DATABASE_URL ortam değişkeni tanımlı değil.")
        print("Örnek: python scripts/migrate_sqlite_to_postgres.py --target-url postgresql+psycopg://user:pass@localhost:5432/ecuzdan")
        return 1

    return execute_migration(
        sqlite_path=sqlite_file,
        target_url=args.target_url or "",
        dry_run=args.dry_run,
        verify_only=args.verify_only,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    sys.exit(main())
