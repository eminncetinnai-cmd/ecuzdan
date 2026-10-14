#!/usr/bin/env python3
"""
Schema Report Generator
Detaylı schema raporu oluşturur ve yedek uyumluluğunu analiz eder.
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema_version import SCHEMA_VERSION
from infrastructure.backup.validation import BackupValidationService


def generate_detailed_schema_report():
    """
    Detaylı schema raporu oluştur.
    """
    try:
        from app import create_app

        app = create_app()

        with app.app_context():
            validation_service = BackupValidationService()
            schema_info = validation_service.get_current_schema_info()

            report = {
                "generated_at": datetime.now().isoformat(),
                "schema_version": SCHEMA_VERSION,
                "schema_info": schema_info,
                "compatibility_status": "unknown",
                "recommendations": []
            }

            # Tablo analizi
            table_analysis = {}
            for table_name, table_info in schema_info['tables'].items():
                table_analysis[table_name] = {
                    "column_count": table_info['column_count'],
                    "columns": table_info['columns'],
                    "has_id_column": 'id' in table_info['columns'],
                    "potential_issues": []
                }

                # Temel sorun tespiti
                if not table_analysis[table_name]['has_id_column']:
                    table_analysis[table_name]['potential_issues'].append(
                        "Missing 'id' column - backup compatibility risk"
                    )

            report['table_analysis'] = table_analysis

            # Genel uyumluluk durumu
            critical_issues = []
            for table_name, analysis in table_analysis.items():
                if analysis['potential_issues']:
                    critical_issues.extend(analysis['potential_issues'])

            if critical_issues:
                report['compatibility_status'] = "warning"
                report['recommendations'].extend(critical_issues)
            else:
                report['compatibility_status'] = "compatible"
                report['recommendations'].append("Schema appears backup-compatible")

            return report

    except Exception as e:
        return {
            "error": str(e),
            "compatibility_status": "error",
            "generated_at": datetime.now().isoformat()
        }


def main():
    print("📊 Generating Detailed Schema Report...")

    report = generate_detailed_schema_report()

    if report.get('error'):
        print(f"❌ Error: {report['error']}")
        sys.exit(1)

    print(f"📋 Schema Version: {report['schema_version']}")
    print(f"📅 Generated: {report['generated_at']}")
    print(f"🔍 Status: {report['compatibility_status'].upper()}")

    if report['compatibility_status'] == 'compatible':
        print("✅ Schema is backup-compatible")
    else:
        print("⚠️  Potential compatibility issues detected")

    print("\n📝 Recommendations:")
    for rec in report.get('recommendations', []):
        print(f"  - {rec}")

    # JSON olarak da kaydet
    report_file = f"schema_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed report saved to: {report_file}")

    sys.exit(0 if report['compatibility_status'] == 'compatible' else 1)


if __name__ == "__main__":
    main()
