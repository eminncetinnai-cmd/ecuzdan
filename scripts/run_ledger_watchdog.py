#!/usr/bin/env python3
"""
scripts/run_ledger_watchdog.py
==============================
CLI Runner for Continuous Ledger & Balance Drift Watchdog.

Audits double-entry invariants, cryptographic hash chains, and balance drift.
Returns exit code 0 if healthy, exit code 1 if violations are detected.
"""

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["DISABLE_BACKGROUND_SERVICE"] = "true"
os.environ["BACKGROUND_SERVICE_ENABLED"] = "false"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from domain.ledger.services.ledger_watchdog_service import RuntimeLedgerWatchdog


def main():
    parser = argparse.ArgumentParser(description="Run Runtime Ledger & Balance Drift Watchdog")
    parser.add_argument("--tenant-id", type=str, default=None, help="Audit a specific tenant (default: all)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        watchdog = RuntimeLedgerWatchdog()
        if args.tenant_id:
            result = watchdog.audit_tenant(args.tenant_id)
        else:
            result = watchdog.audit_all_tenants()

        if args.json:
            print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
        else:
            print("=" * 70)
            print("RUN-TIME GENERAL LEDGER & BALANCE DRIFT WATCHDOG REPORT")
            print("=" * 70)
            print(f"Status:                 {'[HEALTHY]' if result.healthy else '[INTEGRITY VIOLATION]'}")
            print(f"Checked Tenants:        {', '.join(result.checked_tenants)}")
            print(f"Total Journal Entries:  {result.total_journal_entries}")
            print(f"Total Ledger Lines:     {result.total_ledger_lines}")
            print(f"Total Paid Transactions:{result.total_paid_transactions}")
            print(f"Error Count:            {result.error_count}")
            print("-" * 70)

            if result.violations:
                print("VIOLATIONS DETECTED:")
                for i, v in enumerate(result.violations, 1):
                    print(f"  {i}. [{v.severity}] [{v.code}] Tenant: {v.tenant_id}")
                    print(f"     Entity: {v.entity_type} #{v.entity_id}")
                    print(f"     Message: {v.message}")
                    if v.details:
                        print(f"     Details: {v.details}")
            else:
                print("No violations detected. All double-entry and cryptographic invariants hold.")
            print("=" * 70)

        sys.exit(0 if result.healthy else 1)


if __name__ == "__main__":
    main()
