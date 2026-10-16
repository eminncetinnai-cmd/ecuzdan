#!/usr/bin/env python3
"""
scripts/fuzz_tenant_isolation.py
================================
Adversarial Multi-Tenant Penetration Fuzzer & IDOR Gate.

Performs black-box & grey-box adversarial penetration testing against all
authenticated and unauthenticated endpoints to verify:
1. IDOR Read Protection (Zero cross-tenant data leakage in JSON and HTML).
2. IDOR Mutation Protection (Zero cross-tenant updates/deletions of transactions, assets, plans, categories).
3. Cross-Tenant Spoofing Protection (Form/JSON tenant_id overrides are safely ignored or rejected).
4. Unauthenticated Access Protection (Protected endpoints strictly require authentication).

Exits 0 on 100% pass, exits 1 on any security regression or leakage.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from werkzeug.security import generate_password_hash

from app import create_app
from models import (
    Asset,
    AssetSector,
    AssetType,
    Category,
    RecurringPlan,
    Tenant,
    Transaction,
    User,
    db,
)


@dataclass
class FuzzResult:
    vector_id: str
    category: str
    method: str
    endpoint: str
    http_status: int
    data_leaked: bool
    mutation_prevented: bool
    passed: bool
    details: str = ""


class TenantIsolationFuzzer:
    """Orchestrates adversarial multi-tenant attack scenarios."""

    def __init__(self, app=None, db_path: Optional[Path] = None):
        self.db_path = db_path
        if app is None:
            self.app = create_app()
            self.app.config["TESTING"] = True
            self.app.config["WTF_CSRF_ENABLED"] = False
            if self.db_path:
                self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path.as_posix()}"
        else:
            self.app = app

        self.victim_tenant_id = f"fuzz_victim_{uuid.uuid4().hex[:6]}"
        self.attacker_tenant_id = f"fuzz_attacker_{uuid.uuid4().hex[:6]}"

        self.victim_username = f"victim_{uuid.uuid4().hex[:4]}"
        self.attacker_username = f"attacker_{uuid.uuid4().hex[:4]}"
        self.password = "FuzzPass123!Secure"

        self.secret_tx_desc = f"VICTIM_SECRET_TX_{uuid.uuid4().hex[:8]}"
        self.secret_asset_name = f"VICTIM_SECRET_ASSET_{uuid.uuid4().hex[:8]}"
        self.secret_plan_name = f"VICTIM_SECRET_PLAN_{uuid.uuid4().hex[:8]}"
        self.secret_cat_name = f"VICTIM_SECRET_CAT_{uuid.uuid4().hex[:8]}"

        self.victim_tx_id: Optional[int] = None
        self.victim_asset_id: Optional[int] = None
        self.victim_plan_id: Optional[int] = None
        self.victim_cat_id: Optional[int] = None

    def setup_adversarial_tenants(self):
        """Seed victim and attacker tenants with isolated entities."""
        with self.app.app_context():
            # 1. Victims and Attackers
            vt = Tenant(id=self.victim_tenant_id, name="Victim Corp")
            at = Tenant(id=self.attacker_tenant_id, name="Attacker Corp")
            db.session.add_all([vt, at])
            db.session.flush()

            vu = User(
                username=self.victim_username,
                password=generate_password_hash(self.password),
                role="kullanici",
                tenant_id=self.victim_tenant_id,
            )
            au = User(
                username=self.attacker_username,
                password=generate_password_hash(self.password),
                role="kullanici",
                tenant_id=self.attacker_tenant_id,
            )
            db.session.add_all([vu, au])
            db.session.flush()

            # Required sectors/types
            sec = AssetSector.query.first()
            if not sec:
                sec = AssetSector(name="Teknoloji")
                db.session.add(sec)
                db.session.flush()

            atype = AssetType.query.first()
            if not atype:
                atype = AssetType(name="Hisse Senedi")
                db.session.add(atype)
                db.session.flush()

            # 2. Victim's Private Resources
            cat = Category(name=self.secret_cat_name, type="Gider", tenant_id=self.victim_tenant_id)
            db.session.add(cat)
            db.session.flush()
            self.victim_cat_id = cat.id

            tx = Transaction(
                date="2026-10-01",
                category=cat.name,
                description=self.secret_tx_desc,
                type="Gider",
                amount=99999.00,
                status="Bekliyor",
                tenant_id=self.victim_tenant_id,
            )
            db.session.add(tx)
            db.session.flush()
            self.victim_tx_id = tx.id

            asset = Asset(
                type=atype.name,
                name=self.secret_asset_name,
                symbol="VICTIM_SYM",
                value=88888.00,
                purchase_cost=88888.00,
                purchase_date="2026-10-01",
                currency="TRY",
                quantity=10,
                unit_price=8888.80,
                risk_level="Orta",
                liquidity="Likit",
                sector_id=sec.id,
                tenant_id=self.victim_tenant_id,
            )
            db.session.add(asset)
            db.session.flush()
            self.victim_asset_id = asset.id

            plan = RecurringPlan(
                name=self.secret_plan_name,
                flow_type="Gider",
                category=cat.name,
                amount=77777.00,
                installments=12,
                payment_day=1,
                frequency="Aylık",
                start_date="2026-10-01",
                status="Aktif",
                tenant_id=self.victim_tenant_id,
            )
            db.session.add(plan)
            db.session.commit()
            self.victim_plan_id = plan.id

    def run_fuzzing_battery(self) -> List[FuzzResult]:
        """Execute all adversarial vectors."""
        results: List[FuzzResult] = []

        # Attacker client
        attacker_client = self.app.test_client()
        login_res = attacker_client.post(
            "/login",
            data={"username": self.attacker_username, "password": self.password},
            follow_redirects=True,
        )
        assert login_res.status_code == 200

        # Unauthenticated client
        anon_client = self.app.test_client()

        # ---------------------------------------------------------
        # CATEGORY 1: IDOR READ TESTS
        # ---------------------------------------------------------
        # VEC-01: Read transactions API
        res = attacker_client.get("/transactions?format=json")
        body = res.get_data(as_text=True)
        leaked = self.secret_tx_desc in body
        results.append(
            FuzzResult(
                vector_id="VEC-01",
                category="IDOR Read",
                method="GET",
                endpoint="/transactions?format=json",
                http_status=res.status_code,
                data_leaked=leaked,
                mutation_prevented=True,
                passed=(not leaked and res.status_code == 200),
                details="Attacker requested transaction JSON listing",
            )
        )

        # VEC-02: Read assets API
        res = attacker_client.get("/api/portfolio/assets")
        body = res.get_data(as_text=True)
        leaked = self.secret_asset_name in body
        results.append(
            FuzzResult(
                vector_id="VEC-02",
                category="IDOR Read",
                method="GET",
                endpoint="/api/portfolio/assets",
                http_status=res.status_code,
                data_leaked=leaked,
                mutation_prevented=True,
                passed=(not leaked and res.status_code in (200, 404)),
                details="Attacker requested portfolio assets JSON",
            )
        )

        # VEC-03: Direct Object Reference to Victim's Plan API
        res = attacker_client.get(f"/api/plans/{self.victim_plan_id}")
        body = res.get_data(as_text=True)
        leaked = self.secret_plan_name in body
        results.append(
            FuzzResult(
                vector_id="VEC-03",
                category="IDOR Read",
                method="GET",
                endpoint=f"/api/plans/{self.victim_plan_id}",
                http_status=res.status_code,
                data_leaked=leaked,
                mutation_prevented=True,
                passed=(not leaked and res.status_code in (403, 404)),
                details="Attacker directly queried victim's recurring plan ID",
            )
        )

        # VEC-04: HTML view transactions leak
        res = attacker_client.get("/transactions")
        body = res.get_data(as_text=True)
        leaked = self.secret_tx_desc in body
        results.append(
            FuzzResult(
                vector_id="VEC-04",
                category="IDOR Read",
                method="GET",
                endpoint="/transactions",
                http_status=res.status_code,
                data_leaked=leaked,
                mutation_prevented=True,
                passed=(not leaked and res.status_code == 200),
                details="Attacker rendered transactions HTML page",
            )
        )

        # VEC-05: HTML view assets leak
        res = attacker_client.get("/assets")
        body = res.get_data(as_text=True)
        leaked = self.secret_asset_name in body
        results.append(
            FuzzResult(
                vector_id="VEC-05",
                category="IDOR Read",
                method="GET",
                endpoint="/assets",
                http_status=res.status_code,
                data_leaked=leaked,
                mutation_prevented=True,
                passed=(not leaked and res.status_code == 200),
                details="Attacker rendered assets HTML page",
            )
        )

        # VEC-06: HTML view plans leak
        res = attacker_client.get("/plans")
        body = res.get_data(as_text=True)
        leaked = self.secret_plan_name in body
        results.append(
            FuzzResult(
                vector_id="VEC-06",
                category="IDOR Read",
                method="GET",
                endpoint="/plans",
                http_status=res.status_code,
                data_leaked=leaked,
                mutation_prevented=True,
                passed=(not leaked and res.status_code == 200),
                details="Attacker rendered recurring plans HTML page",
            )
        )

        # ---------------------------------------------------------
        # CATEGORY 2: IDOR MUTATION & DELETION TESTS
        # ---------------------------------------------------------
        # VEC-07: Attacker attempts to modify Victim's Transaction
        res = attacker_client.post(
            f"/edit_t/{self.victim_tx_id}",
            data={
                "date": "2026-10-02",
                "category": "Diğer",
                "description": "COMPROMISED_TX_BY_ATTACKER",
                "type": "Gider",
                "amount": "1.00",
                "status": "Bekliyor",
            },
            follow_redirects=True,
        )
        with self.app.app_context():
            tx_check = db.session.get(Transaction, self.victim_tx_id)
            mutation_prevented = (
                tx_check is not None
                and tx_check.description == self.secret_tx_desc
                and float(tx_check.amount) == 99999.00
            )
        results.append(
            FuzzResult(
                vector_id="VEC-07",
                category="IDOR Mutation",
                method="POST",
                endpoint=f"/edit_t/{self.victim_tx_id}",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker attempted to overwrite victim transaction data",
            )
        )

        # VEC-08: Attacker attempts to delete Victim's Transaction
        res = attacker_client.post(
            f"/delete_t/{self.victim_tx_id}",
            follow_redirects=True,
        )
        with self.app.app_context():
            tx_check = db.session.get(Transaction, self.victim_tx_id)
            mutation_prevented = (tx_check is not None and not getattr(tx_check, "is_deleted", False))
        results.append(
            FuzzResult(
                vector_id="VEC-08",
                category="IDOR Mutation",
                method="POST",
                endpoint=f"/delete_t/{self.victim_tx_id}",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker attempted to delete victim transaction",
            )
        )

        # VEC-09: Attacker attempts to quick-pay Victim's Transaction
        res = attacker_client.post(
            f"/transactions/{self.victim_tx_id}/quick-pay",
            follow_redirects=True,
        )
        with self.app.app_context():
            tx_check = db.session.get(Transaction, self.victim_tx_id)
            mutation_prevented = (tx_check is not None and tx_check.status == "Bekliyor")
        results.append(
            FuzzResult(
                vector_id="VEC-09",
                category="IDOR Mutation",
                method="POST",
                endpoint=f"/transactions/{self.victim_tx_id}/quick-pay",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker attempted to trigger quick-pay on victim transaction",
            )
        )

        # VEC-10: Attacker attempts to delete Victim's Asset
        res = attacker_client.post(
            f"/delete_asset/{self.victim_asset_id}",
            follow_redirects=True,
        )
        with self.app.app_context():
            asset_check = db.session.get(Asset, self.victim_asset_id)
            mutation_prevented = (asset_check is not None and not getattr(asset_check, "is_closed", False))
        results.append(
            FuzzResult(
                vector_id="VEC-10",
                category="IDOR Mutation",
                method="POST",
                endpoint=f"/delete_asset/{self.victim_asset_id}",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker attempted to delete victim asset position",
            )
        )

        # VEC-11: Attacker attempts to delete Victim's Recurring Plan
        res = attacker_client.post(
            f"/{self.victim_plan_id}/delete",
            follow_redirects=True,
        )
        with self.app.app_context():
            plan_check = db.session.get(RecurringPlan, self.victim_plan_id)
            mutation_prevented = (plan_check is not None)
        results.append(
            FuzzResult(
                vector_id="VEC-11",
                category="IDOR Mutation",
                method="POST",
                endpoint=f"/{self.victim_plan_id}/delete",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker attempted to delete victim recurring plan",
            )
        )

        # VEC-12: Attacker attempts to change Victim's Plan Status
        res = attacker_client.post(
            f"/{self.victim_plan_id}/status",
            data={"status": "İptal"},
            follow_redirects=True,
        )
        with self.app.app_context():
            plan_check = db.session.get(RecurringPlan, self.victim_plan_id)
            mutation_prevented = (plan_check is not None and plan_check.status == "Aktif")
        results.append(
            FuzzResult(
                vector_id="VEC-12",
                category="IDOR Mutation",
                method="POST",
                endpoint=f"/{self.victim_plan_id}/status",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker attempted to toggle status on victim plan",
            )
        )

        # ---------------------------------------------------------
        # CATEGORY 3: CROSS-TENANT INJECTION & PARAMETER SPOOFING
        # ---------------------------------------------------------
        # VEC-13: Attacker injects tenant_id=tenant_victim in POST /new_transaction
        injected_tx_desc = f"INJECTED_TX_{uuid.uuid4().hex[:6]}"
        res = attacker_client.post(
            "/new_transaction",
            data={
                "date": "2026-10-05",
                "category": "Diğer",
                "description": injected_tx_desc,
                "type": "Gider",
                "amount": "500.00",
                "status": "Bekliyor",
                "tenant_id": self.victim_tenant_id,  # Adversarial Spoofing
            },
            follow_redirects=True,
        )
        with self.app.app_context():
            # The transaction MUST NOT be assigned to victim tenant
            victim_injected = Transaction.query.filter_by(
                tenant_id=self.victim_tenant_id, description=injected_tx_desc
            ).first()
            mutation_prevented = (victim_injected is None)
        results.append(
            FuzzResult(
                vector_id="VEC-13",
                category="Tenant Spoofing",
                method="POST",
                endpoint="/new_transaction",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker submitted transaction with spoofed victim tenant_id parameter",
            )
        )

        # VEC-14: Attacker injects tenant_id=tenant_victim in POST /new_asset
        injected_asset_name = f"INJECTED_ASSET_{uuid.uuid4().hex[:6]}"
        with self.app.app_context():
            sec = AssetSector.query.first()
            sec_id = str(sec.id) if sec else "1"

        res = attacker_client.post(
            "/new_asset",
            data={
                "type": "Hisse Senedi",
                "name": injected_asset_name,
                "value": "1500.00",
                "purchase_cost": "1500.00",
                "quantity": "1",
                "unit_price": "1500.00",
                "currency": "TRY",
                "sector_id": sec_id,
                "tenant_id": self.victim_tenant_id,  # Adversarial Spoofing
            },
            follow_redirects=True,
        )
        with self.app.app_context():
            victim_injected_asset = Asset.query.filter_by(
                tenant_id=self.victim_tenant_id, name=injected_asset_name
            ).first()
            mutation_prevented = (victim_injected_asset is None)
        results.append(
            FuzzResult(
                vector_id="VEC-14",
                category="Tenant Spoofing",
                method="POST",
                endpoint="/new_asset",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=mutation_prevented,
                passed=mutation_prevented,
                details="Attacker submitted asset with spoofed victim tenant_id parameter",
            )
        )

        # ---------------------------------------------------------
        # CATEGORY 4: UNAUTHENTICATED ACCESS SCRAPING
        # ---------------------------------------------------------
        # VEC-15: Anonymous access to transactions
        res = anon_client.get("/transactions")
        passed = (res.status_code in (302, 401, 403))
        results.append(
            FuzzResult(
                vector_id="VEC-15",
                category="Auth Enforce",
                method="GET",
                endpoint="/transactions",
                http_status=res.status_code,
                data_leaked=(self.secret_tx_desc in res.get_data(as_text=True)),
                mutation_prevented=True,
                passed=passed,
                details="Anonymous client attempted to view transactions",
            )
        )

        # VEC-16: Anonymous access to assets
        res = anon_client.get("/assets")
        passed = (res.status_code in (302, 401, 403))
        results.append(
            FuzzResult(
                vector_id="VEC-16",
                category="Auth Enforce",
                method="GET",
                endpoint="/assets",
                http_status=res.status_code,
                data_leaked=(self.secret_asset_name in res.get_data(as_text=True)),
                mutation_prevented=True,
                passed=passed,
                details="Anonymous client attempted to view assets",
            )
        )

        # VEC-17: Anonymous access to plans
        res = anon_client.get("/plans")
        passed = (res.status_code in (302, 401, 403))
        results.append(
            FuzzResult(
                vector_id="VEC-17",
                category="Auth Enforce",
                method="GET",
                endpoint="/plans",
                http_status=res.status_code,
                data_leaked=False,
                mutation_prevented=True,
                passed=passed,
                details="Anonymous client attempted to view recurring plans",
            )
        )

        return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Tenant Penetration Fuzzer & IDOR Gate")
    parser.parse_args()

    print("=" * 88)
    print("E-CUZDAN MULTI-TENANT PENETRATION FUZZER & IDOR GATE")
    print("=" * 88)

    fuzzer = TenantIsolationFuzzer()
    fuzzer.setup_adversarial_tenants()
    results = fuzzer.run_fuzzing_battery()

    print(f"{'VEC ID':<7} | {'CATEGORY':<16} | {'METHOD':<6} | {'ENDPOINT':<32} | {'HTTP':<4} | {'LEAK':<5} | {'VERDICT'}")
    print("-" * 88)

    failed_count = 0
    for r in results:
        leak_str = "YES" if r.data_leaked else "NO"
        verdict = "[PASS]" if r.passed else "[FAIL]"
        if not r.passed:
            failed_count += 1
        print(f"{r.vector_id:<7} | {r.category:<16} | {r.method:<6} | {r.endpoint:<32} | {r.http_status:<4} | {leak_str:<5} | {verdict}")

    print("-" * 88)
    if failed_count == 0:
        print(f"ALL {len(results)} ADVERSARIAL PENETRATION ATTACKS WERE SUCCESSFULLY DEFENDED!")
        print("ZERO IDOR DATA LEAKS DETECTED. TENANT ISOLATION FULLY ENFORCED.")
        print("=" * 88)
        return 0
    else:
        print(f"CRITICAL SECURITY ALERT: {failed_count} PENETRATION VECTORS FAILED!")
        print("=" * 88)
        return 1


if __name__ == "__main__":
    sys.exit(main())
