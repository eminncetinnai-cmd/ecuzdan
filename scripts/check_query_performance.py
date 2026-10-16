#!/usr/bin/env python3
"""
scripts/check_query_performance.py
==================================
Automated N+1 SQL Query Profiler & Performance SLA Gate.

Audits core application routes under authenticated sessions:
- Measures total SQL queries executed per page.
- Detects N+1 query loops (repeated statement templates).
- Measures total database duration per page request.
Exits 0 if all routes meet the SLA budget, exits 1 on violation.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from shared.db import db
from shared.query_profiler import QueryProfiler

CORE_ROUTES_TO_PROFILE = [
    ("/", "Dashboard / Summary"),
    ("/transactions", "Transactions History"),
    ("/plans", "Recurring Plans"),
    ("/payment_calendar", "Payment Calendar"),
    ("/assets", "Assets Overview"),
    ("/investment_performance", "Investment Performance"),
    ("/analysis", "Financial Analysis"),
    ("/financial_freedom", "Financial Freedom FIRE"),
    ("/categories", "Category Management"),
    ("/profile", "User Profile"),
    ("/settings", "System Settings"),
    ("/global-ratios", "Global Financial Ratios"),
    ("/central-bank-reserves", "Central Bank Reserves"),
]

MAX_QUERY_BUDGET = 25
MAX_DUPLICATE_BUDGET = 4


def profile_application_routes(max_budget: int = MAX_QUERY_BUDGET, max_dup: int = MAX_DUPLICATE_BUDGET) -> int:
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    client = app.test_client()

    with app.app_context():
        from models import User
        user = User.query.first()
        uid = user.id if user else 1
        tid = user.tenant_id if user else "default"
        engine = db.engine

    with client.session_transaction() as sess:
        sess["user_id"] = uid
        sess["tenant_id"] = tid
        sess["_user_id"] = str(uid)

    print("=" * 80)
    print("E-CUZDAN N+1 SQL QUERY PROFILER & PERFORMANCE SLA GATE")
    print("=" * 80)
    print(f"Query Count Budget per Route: <= {max_budget}")
    print(f"Max Repeated Template Budget: <= {max_dup}")
    print("-" * 80)
    print(f"{'ROUTE':<28} | {'HTTP':<4} | {'QUERIES':<7} | {'DUPS':<5} | {'DB TIME':<10} | {'SLA STATUS'}")
    print("-" * 80)

    violations = []

    for path, label in CORE_ROUTES_TO_PROFILE:
        with QueryProfiler(engine) as profiler:
            resp = client.get(path, follow_redirects=True)

        stats = profiler.stats
        status = resp.status_code
        q_count = stats.total_queries
        max_rep = stats.max_duplicate_count
        db_ms = stats.total_duration_ms

        is_passed = (q_count <= max_budget) and (max_rep <= max_dup) and (status == 200)
        verdict = "[PASS]" if is_passed else "[FAIL]"

        if not is_passed:
            violations.append((path, label, q_count, max_rep, stats.duplicate_patterns))

        print(f"{path:<28} | {status:<4} | {q_count:<7} | {max_rep:<5} | {db_ms:>6.2f}ms   | {verdict}")

    print("-" * 80)
    if violations:
        print("PERFORMANCE SLA VIOLATIONS DETECTED:")
        for path, label, q_count, max_rep, dups in violations:
            print(f"  * {path} ({label}): {q_count} queries (budget: {max_budget}), max repeated: {max_rep}")
            for stmt, cnt in dups.items():
                if cnt > max_dup:
                    print(f"    - [{cnt}x] {stmt[:100]}...")
        print("=" * 80)
        return 1
    else:
        print(f"ALL {len(CORE_ROUTES_TO_PROFILE)} CORE ROUTES COMPLY WITH N+1 AND SQL QUERY BUDGET SLAs!")
        print("=" * 80)
        return 0


def main():
    parser = argparse.ArgumentParser(description="Profile routes for SQL efficiency and N+1 patterns")
    parser.add_argument("--max-queries", type=int, default=MAX_QUERY_BUDGET, help="Max queries allowed per route")
    parser.add_argument("--max-duplicates", type=int, default=MAX_DUPLICATE_BUDGET, help="Max repeated query templates")
    args = parser.parse_args()

    exit_code = profile_application_routes(max_budget=args.max_queries, max_dup=args.max_duplicates)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
