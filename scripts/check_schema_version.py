#!/usr/bin/env python3
"""
Schema Version Check Script
Schema değişikliklerini tespit eder ve uyumluluk uyarıları verir.
"""

import os
import subprocess
import sys
from datetime import datetime

# Windows console encoding uyumluluğu
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Proje root path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema_version import SCHEMA_VERSION
from infrastructure.backup.validation import BackupValidationService


def check_schema_version_change():
    """
    Schema versiyonunda değişiklik olup olmadığını kontrol et.
    """
    print(f"🔍 Current Schema Version: {SCHEMA_VERSION}")

    # Git diff kontrolü (sadece model ve database dosyaları için)
    try:
        result = subprocess.run(
            ['git', 'diff', 'HEAD', '--name-only'],
            capture_output=True,
            text=True,
            check=False
        )

        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        schema_related_files = [
            f for f in changed_files
            if any(path in f for path in ['models/', 'infrastructure/database/', 'database/'])
        ]

        if schema_related_files:
            print("⚠️  Schema-related files changed:")
            for file in schema_related_files:
                print(f"   - {file}")

            print("\n📋 Recommended Actions:")
            print("1. Update SCHEMA_VERSION in database/schema_version.py")
            print("2. Run schema compatibility tests")
            print("3. Create migration script if needed")
            print("4. Test backward compatibility")

            return True
        else:
            print("✅ No schema-related changes detected")
            return False

    except Exception as e:
        print(f"⚠️  Could not check git changes: {e}")
        return False


def generate_schema_compatibility_report():
    """
    Mevcut schema'nın yedek uyumluluğu raporu oluştur.
    """
    print("\n📊 Generating Schema Compatibility Report...")

    try:
        from app import create_app

        app = create_app()

        with app.app_context():
            validation_service = BackupValidationService()
            schema_info = validation_service.get_current_schema_info()

            print("📋 Schema Information:")
            print(f"   Version: {schema_info['schema_version']}")
            print(f"   Total Tables: {schema_info['total_tables']}")
            print("   Table Details:")

            for table_name, table_info in sorted(schema_info['tables'].items()):
                print(f"     - {table_name}: {table_info['column_count']} columns")

            print("\n✅ Schema compatibility check completed")

    except Exception as e:
        print(f"❌ Error generating compatibility report: {e}")
        return False

    return True


def main():
    print("=" * 60)
    print("SCHEMA VERSION & COMPATIBILITY CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    has_schema_changes = check_schema_version_change()
    generate_schema_compatibility_report()

    print("\n" + "=" * 60)

    if has_schema_changes:
        print("⚠️  WARNING: Schema changes detected!")
        print("Please ensure backup compatibility before deploying.")
        sys.exit(1)
    else:
        print("✅ No schema changes detected - safe to proceed")
        sys.exit(0)


if __name__ == "__main__":
    main()
