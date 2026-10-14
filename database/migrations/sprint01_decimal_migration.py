"""
SPRINT-01 Decimal Migration Script

This script migrates financial data from FLOAT to NUMERIC(19,4) for banking-grade precision.

IMPORTANT: This migration is designed for SQLite. For PostgreSQL, use Alembic migrations.

Migration Strategy:
1. Create new tables with NUMERIC columns
2. Migrate data from old tables to new tables
3. Rename old tables to backup
4. Rename new tables to original names
5. Verify data integrity

BACKUP: Always backup your database before running this migration.

Usage:
    python database/migrations/sprint01_decimal_migration.py
"""

import os
import sqlite3
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config


def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    import shutil
    shutil.copy2(db_path, backup_path)

    print(f"✓ Database backed up to: {backup_path}")
    return backup_path


def migrate_table(conn, table_name: str, float_columns: list) -> bool:
    """
    Migrate a single table from FLOAT to NUMERIC(19,4).

    Args:
        conn: Database connection
        table_name: Name of the table to migrate
        float_columns: List of column names to migrate

    Returns:
        bool: True if successful, False otherwise
    """
    cursor = conn.cursor()

    try:
        # Get table schema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        table_sql = cursor.fetchone()

        if not table_sql:
            print(f"⚠ Table {table_name} not found, skipping")
            return True

        original_sql = table_sql[0]
        print(f"\nMigrating table: {table_name}")
        print(f"  Columns to migrate: {float_columns}")

        # Create new table schema with NUMERIC columns
        new_sql = original_sql
        for col in float_columns:
            # Replace FLOAT with NUMERIC(19,4)
            new_sql = new_sql.replace(f"{col} REAL", f"{col} NUMERIC(19,4)")
            new_sql = new_sql.replace(f"{col} FLOAT", f"{col} NUMERIC(19,4)")

        new_table_name = f"{table_name}_new"
        new_sql = new_sql.replace(f"CREATE TABLE {table_name}", f"CREATE TABLE {new_table_name}")

        # Create new table
        cursor.execute(new_sql)

        # Copy data from old table to new table
        columns = []
        cursor.execute(f"PRAGMA table_info({table_name})")
        for col_info in cursor.fetchall():
            columns.append(col_info[1])

        columns_str = ", ".join(columns)
        cursor.execute(f"INSERT INTO {new_table_name} ({columns_str}) SELECT {columns_str} FROM {table_name}")

        rows_copied = cursor.rowcount
        print(f"  ✓ Copied {rows_copied} rows")

        # Drop old table
        cursor.execute(f"DROP TABLE {table_name}")

        # Rename new table to original name
        cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")

        # Recreate indexes
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
        indexes = cursor.fetchall()

        for index in indexes:
            if index[0]:
                # Drop and recreate index
                index_name = index[0].split()[-1].rstrip(')')
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                    cursor.execute(index[0])
                    print(f"  ✓ Recreated index: {index_name}")
                except Exception as e:
                    print(f"  ⚠ Could not recreate index {index_name}: {e}")

        conn.commit()
        print(f"  ✓ Table {table_name} migrated successfully")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error migrating table {table_name}: {e}")
        return False


def verify_migration(conn, table_name: str, float_columns: list) -> bool:
    """Verify that migration was successful."""
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        for col in float_columns:
            col_found = False
            for col_info in columns:
                if col_info[1] == col:
                    col_found = True
                    # Check if column type is NUMERIC
                    if 'NUMERIC' in col_info[2].upper():
                        print(f"  ✓ Column {col} is NUMERIC")
                    else:
                        print(f"  ✗ Column {col} is not NUMERIC: {col_info[2]}")
                        return False
                    break

            if not col_found:
                print(f"  ⚠ Column {col} not found in table {table_name}")

        return True

    except Exception as e:
        print(f"  ✗ Error verifying table {table_name}: {e}")
        return False


def main():
    """Main migration function."""
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')

    if not os.path.exists(db_path):
        print(f"✗ Database not found: {db_path}")
        return False

    print("=" * 60)
    print("SPRINT-01: Decimal Migration")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Backup database
    backup_path = backup_database(db_path)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")

    # Define tables and columns to migrate
    migrations = [
        # (table_name, [float_columns])
        ('category_asset_type_mapping', ['weight']),
        ('transaction', ['amount']),
        ('recurring_plan', ['amount']),
        ('payment', ['amount']),
        ('strategy_settings', [
            'mc_expected_return', 'mc_volatility', 'annual_inflation',
            'anomaly_sigma_threshold', 'bucket_emergency_pct',
            'bucket_short_term_pct', 'bucket_long_term_pct'
        ]),
        ('investor_profile', [
            'literacy_score', 'capacity_score', 'tolerance_score',
            'behavioral_score', 'experience_score', 'confidence_score'
        ]),
        ('asset_update', ['old_value', 'new_value', 'old_unit_price', 'new_unit_price']),
        ('asset_transaction', ['quantity', 'unit_price', 'total_cost']),
        ('asset', ['value', 'purchase_cost', 'quantity', 'unit_price', 'monthly_rent']),
        ('category', ['budget_limit']),
    ]

    success_count = 0
    failure_count = 0

    # Migrate each table
    for table_name, columns in migrations:
        if migrate_table(conn, table_name, columns):
            if verify_migration(conn, table_name, columns):
                success_count += 1
            else:
                failure_count += 1
        else:
            failure_count += 1

    conn.close()
    conn.execute("PRAGMA foreign_keys = ON")

    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Tables migrated successfully: {success_count}")
    print(f"Tables failed: {failure_count}")
    print(f"Backup location: {backup_path}")

    # If failed, restore from backup
    if failure_count > 0:
        print()
        print("⚠ Some migrations failed. To restore from backup:")
        print(f"  cp {backup_path} {db_path}")
        return False

    print()
    print("✓ Migration completed successfully!")
    print()
    print("Next steps:")
    print("1. Test the application thoroughly")
    print("2. Verify all financial calculations")
    print("3. If issues occur, restore from backup")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
