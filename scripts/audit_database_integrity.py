"""
Phase 4: Database Schema, Migration & Constraint Integrity Auditor
Audits SQLite PRAGMAs, foreign keys, orphan rows, constraints, nullability, and negative boundaries.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ['TESTING'] = 'True'

from sqlalchemy import text

from app import create_app
from shared.db import db

app = create_app()

def audit_database():
    results = {
        'pragma_integrity': None,
        'pragma_foreign_keys': [],
        'orphan_checks': {},
        'nullability_violations': {},
        'negative_or_invalid_values': {},
        'unique_constraint_checks': {}
    }

    with app.app_context():
        # 1. SQLite PRAGMA Integrity Check
        res = db.session.execute(text("PRAGMA integrity_check;")).fetchall()
        results['pragma_integrity'] = [r[0] for r in res]

        # 2. SQLite PRAGMA Foreign Key Check
        res_fk = db.session.execute(text("PRAGMA foreign_key_check;")).fetchall()
        results['pragma_foreign_keys'] = [
            {'table': r[0], 'rowid': r[1], 'parent': r[2], 'fkid': r[3]} for r in res_fk
        ]

        # 3. Orphan Checks across key entity relationships
        # a) Transaction without valid Tenant
        orphan_tx_tenant = db.session.execute(text(
            "SELECT count(*) FROM \"transaction\" WHERE tenant_id NOT IN (SELECT id FROM tenant)"
        )).scalar()
        results['orphan_checks']['transaction_invalid_tenant'] = orphan_tx_tenant

        # b) RecurringPlan without valid Tenant
        orphan_plan_tenant = db.session.execute(text(
            "SELECT count(*) FROM recurring_plan WHERE tenant_id NOT IN (SELECT id FROM tenant)"
        )).scalar()
        results['orphan_checks']['recurring_plan_invalid_tenant'] = orphan_plan_tenant

        # c) Asset without valid Tenant
        orphan_asset_tenant = db.session.execute(text(
            "SELECT count(*) FROM asset WHERE tenant_id NOT IN (SELECT id FROM tenant)"
        )).scalar()
        results['orphan_checks']['asset_invalid_tenant'] = orphan_asset_tenant

        # d) Payment without valid RecurringPlan
        orphan_payment_plan = db.session.execute(text(
            "SELECT count(*) FROM payment WHERE plan_id IS NOT NULL AND plan_id NOT IN (SELECT id FROM recurring_plan)"
        )).scalar()
        results['orphan_checks']['payment_invalid_plan'] = orphan_payment_plan

        # e) Payment with invalid Transaction
        orphan_payment_tx = db.session.execute(text(
            "SELECT count(*) FROM payment WHERE transaction_id IS NOT NULL AND transaction_id NOT IN (SELECT id FROM \"transaction\")"
        )).scalar()
        results['orphan_checks']['payment_invalid_transaction'] = orphan_payment_tx

        # f) PlanOccurrence with invalid RecurringPlan
        orphan_occ_plan = db.session.execute(text(
            "SELECT count(*) FROM plan_occurrence WHERE plan_id NOT IN (SELECT id FROM recurring_plan)"
        )).scalar()
        results['orphan_checks']['plan_occurrence_invalid_plan'] = orphan_occ_plan

        # g) AssetTransaction with invalid Asset
        orphan_asset_tx = db.session.execute(text(
            "SELECT count(*) FROM asset_transaction WHERE asset_id NOT IN (SELECT id FROM asset)"
        )).scalar()
        results['orphan_checks']['asset_transaction_invalid_asset'] = orphan_asset_tx

        # h) LedgerAdjustment with invalid Transaction
        orphan_adj_orig = db.session.execute(text(
            "SELECT count(*) FROM ledger_adjustment WHERE original_transaction_id NOT IN (SELECT id FROM \"transaction\")"
        )).scalar()
        results['orphan_checks']['ledger_adjustment_invalid_orig_tx'] = orphan_adj_orig

        orphan_adj_comp = db.session.execute(text(
            "SELECT count(*) FROM ledger_adjustment WHERE compensating_transaction_id IS NOT NULL AND compensating_transaction_id NOT IN (SELECT id FROM \"transaction\")"
        )).scalar()
        results['orphan_checks']['ledger_adjustment_invalid_comp_tx'] = orphan_adj_comp

        # 4. Negative / Invalid values
        # a) Transaction amount <= 0
        tx_invalid_amount = db.session.execute(text(
            "SELECT count(*) FROM \"transaction\" WHERE amount <= 0"
        )).scalar()
        results['negative_or_invalid_values']['transaction_non_positive_amount'] = tx_invalid_amount

        # b) Asset quantity < 0
        asset_neg_units = db.session.execute(text(
            "SELECT count(*) FROM asset WHERE quantity < 0"
        )).scalar()
        results['negative_or_invalid_values']['asset_negative_quantity'] = asset_neg_units

        # c) Asset purchase_cost < 0
        asset_neg_cost = db.session.execute(text(
            "SELECT count(*) FROM asset WHERE purchase_cost < 0"
        )).scalar()
        results['negative_or_invalid_values']['asset_negative_purchase_cost'] = asset_neg_cost

        # 5. Nullability in required fields
        tx_null_tenant = db.session.execute(text(
            "SELECT count(*) FROM \"transaction\" WHERE tenant_id IS NULL OR tenant_id = ''"
        )).scalar()
        results['nullability_violations']['transaction_null_tenant'] = tx_null_tenant

        tx_null_date = db.session.execute(text(
            "SELECT count(*) FROM \"transaction\" WHERE date IS NULL OR date = ''"
        )).scalar()
        results['nullability_violations']['transaction_null_date'] = tx_null_date

        tx_null_type = db.session.execute(text(
            "SELECT count(*) FROM \"transaction\" WHERE type IS NULL OR type = ''"
        )).scalar()
        results['nullability_violations']['transaction_null_type'] = tx_null_type

        # 6. Tenant Mismatches (e.g. Transaction tenant != Plan tenant)
        mismatch_tx_plan = db.session.execute(text(
            """
            SELECT count(*) 
            FROM \"transaction\" t 
            JOIN recurring_plan p ON t.source_id = p.id AND t.source_type = 'plan'
            WHERE t.tenant_id != p.tenant_id
            """
        )).scalar()
        results['orphan_checks']['tenant_mismatch_tx_plan'] = mismatch_tx_plan

    print(json.dumps(results, indent=2))
    return results

if __name__ == '__main__':
    audit_database()
