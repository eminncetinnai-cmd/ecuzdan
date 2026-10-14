"""Run the read-only financial consistency scan for all or selected tenants."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402
from domain.ledger.services.financial_consistency import FinancialConsistencyChecker  # noqa: E402
from models import Tenant  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", action="append", dest="tenant_ids")
    args = parser.parse_args()

    with app.app_context():
        tenant_ids = args.tenant_ids or [
            tenant.id for tenant in Tenant.query.order_by(Tenant.id.asc()).all()
        ]
        checker = FinancialConsistencyChecker()
        reports = [checker.check_tenant(tenant_id).as_dict() for tenant_id in tenant_ids]

    payload = {
        "healthy": all(report["healthy"] for report in reports),
        "tenant_count": len(reports),
        "reports": reports,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["healthy"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
