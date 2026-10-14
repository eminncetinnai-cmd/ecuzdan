"""
Master Comprehensive Software Validation & Database Integrity Suite
Covers:
  - Phase 5: CRUD End-to-End Matrix & DB Verification
  - Phase 6: Independent Calculation & Floating Point / Decimal Precision Validation
  - Phase 7: Transaction / Rollback / Double Submission / Concurrency Testing
  - Phase 8: Authentication, Authorization & Tenant Isolation (IDOR) Testing
  - Phase 10: Negative, Boundary & Security Injection Testing

Isolated in 'audit_tenant_test' to protect production data.
"""
import json
import os
import sys
import threading
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ['TESTING'] = 'True'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

import models
from app import create_app
from models import (
    Asset,
    AssetTransaction,
    BankAccount,
    Category,
    LedgerAdjustment,
    LedgerAuditEvent,
    LogbookEntry,
    Payment,
    PlanOccurrence,
    RecurringPlan,
    Tenant,
    Transaction,
    User,
)
from shared.db import db
from shared.decimal_precision import to_decimal

app = create_app()

AUDIT_TENANT = "audit_tenant_2026"
AUDIT_TENANT_B = "audit_tenant_other"
AUDIT_USER = "audit_user_primary"
AUDIT_USER_B = "audit_user_secondary"
AUDIT_ADMIN = "audit_admin_root"

report = {
    'phase5_crud': {},
    'phase6_calculations': {},
    'phase7_transactions_concurrency': {},
    'phase8_auth_tenant_isolation': {},
    'phase10_negative_boundaries': {},
    'discovered_bugs': []
}

def record_bug(bug_id, severity, module, page_or_endpoint, action, expected, actual, root_cause):
    report['discovered_bugs'].append({
        'bug_id': bug_id,
        'severity': severity,
        'module': module,
        'page_or_endpoint': page_or_endpoint,
        'action': action,
        'expected': expected,
        'actual': actual,
        'root_cause': root_cause
    })

def setup_test_environment():
    with app.app_context():
        # Clean previous audit tenant if leftover
        for t_id in [AUDIT_TENANT, AUDIT_TENANT_B]:
            for model in [LedgerAdjustment, LedgerAuditEvent, LogbookEntry, Payment, PlanOccurrence, Transaction, RecurringPlan, AssetTransaction, Asset, Category, BankAccount]:
                if hasattr(model, 'tenant_id'):
                    model.query.filter_by(tenant_id=t_id).delete(synchronize_session=False)
            User.query.filter_by(tenant_id=t_id).delete(synchronize_session=False)
            Tenant.query.filter_by(id=t_id).delete(synchronize_session=False)
        db.session.commit()

        # Create Tenant A & B
        t_a = Tenant(id=AUDIT_TENANT, name="Audit Tenant A", status="active")
        t_b = Tenant(id=AUDIT_TENANT_B, name="Audit Tenant B", status="active")
        db.session.add_all([t_a, t_b])
        db.session.commit()

        from werkzeug.security import generate_password_hash
        pwd = generate_password_hash("AuditPass123!")
        pwd_adm = generate_password_hash("AdminPass123!")
        u_a = User(username=AUDIT_USER, role="kullanici", tenant_id=AUDIT_TENANT, password=pwd)
        u_b = User(username=AUDIT_USER_B, role="kullanici", tenant_id=AUDIT_TENANT_B, password=pwd)
        u_adm = User(username=AUDIT_ADMIN, role="sistem_yoneticisi", tenant_id=AUDIT_TENANT, password=pwd_adm)
        db.session.add_all([u_a, u_b, u_adm])
        db.session.commit()

def cleanup_test_environment():
    with app.app_context():
        for t_id in [AUDIT_TENANT, AUDIT_TENANT_B]:
            for model in [LedgerAdjustment, LedgerAuditEvent, LogbookEntry, Payment, PlanOccurrence, Transaction, RecurringPlan, AssetTransaction, Asset, Category, BankAccount]:
                if hasattr(model, 'tenant_id'):
                    model.query.filter_by(tenant_id=t_id).delete(synchronize_session=False)
            User.query.filter_by(tenant_id=t_id).delete(synchronize_session=False)
            Tenant.query.filter_by(id=t_id).delete(synchronize_session=False)
        db.session.commit()

# =========================================================================
# PHASE 5: CRUD End-to-End Matrix & DB Verification
# =========================================================================
def run_phase5_crud():
    print("Executing Phase 5: CRUD Matrix...")
    client = app.test_client()

    with app.app_context():
        u = User.query.filter_by(username=AUDIT_USER).first()
        u_id = u.id
        u.last_session_id = "sess_audit_a"
        db.session.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = u_id
        sess['session_id'] = "sess_audit_a"
        sess['tenant_id'] = AUDIT_TENANT
        sess['csrf_token'] = "csrf_audit_token"
        sess['app_boot_id'] = app.config.get('APP_BOOT_ID')

    # 1. Category CRUD
    with app.app_context():
        cat = Category(name="Maaş", type="Gelir", tenant_id=AUDIT_TENANT)
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

        # Verify DB Read
        read_cat = Category.query.filter_by(id=cat_id, tenant_id=AUDIT_TENANT).first()
        assert read_cat is not None
        assert read_cat.name == "Maaş"

    report['phase5_crud']['Category'] = {'create': 'PASS', 'read': 'PASS'}

    # 2. Transaction CRUD
    tx_payload = {
        'date': '2026-10-06',
        'category': 'Maaş',
        'description': 'Ekim Maaşı',
        'amount': '50000.00',
        'type': 'Gelir',
        'status': 'Ödendi',
        'csrf_token': 'csrf_audit_token'
    }
    tx_payload = {
        'date': '2026-10-06',
        'category': 'Maaş',
        'description': 'Ekim Maaşı',
        'amount': '50000.00',
        'type': 'Gelir',
        'status': 'Ödendi',
        'csrf_token': 'csrf_audit_token'
    }
    resp = client.post('/new_transaction', data=tx_payload, follow_redirects=True)
    report['phase5_crud']['Transaction_Create_HTTP'] = resp.status_code

    with app.app_context():
        created_tx = Transaction.query.filter_by(description='Ekim Maaşı', tenant_id=AUDIT_TENANT).first()
        if created_tx:
            tx_id = created_tx.id
            db_amount = float(created_tx.amount)
            report['phase5_crud']['Transaction'] = {
                'create': 'PASS',
                'db_id': tx_id,
                'db_amount': db_amount,
                'db_type': created_tx.type,
                'db_status': created_tx.status,
                'db_tenant': created_tx.tenant_id
            }
            # Test Update
            update_payload = {
                'id': tx_id,
                'date': '2026-10-06',
                'category': 'Maaş',
                'description': 'Ekim Maaşı Güncellendi',
                'amount': '55000.00',
                'type': 'Gelir',
                'status': 'Ödendi',
                'csrf_token': 'csrf_audit_token'
            }
            client.post(f'/edit_t/{tx_id}', data=update_payload, follow_redirects=True)
            db.session.expire_all()
            updated_tx = Transaction.query.filter_by(id=tx_id, tenant_id=AUDIT_TENANT).first()
            if updated_tx and updated_tx.description == 'Ekim Maaşı Güncellendi' and float(updated_tx.amount) == 55000.0:
                report['phase5_crud']['Transaction']['update'] = 'PASS'
            else:
                report['phase5_crud']['Transaction']['update'] = 'FAIL'
                record_bug('BUG-CRUD-TX-UPD', 'HIGH', 'Transactions', f'/edit_t/{tx_id}', 'Update transaction',
                           'Amount updated to 55000.0 and desc updated', f'Desc: {getattr(updated_tx, "description", None)}, Amount: {getattr(updated_tx, "amount", None)}',
                           'Transaction update did not commit expected attributes')

            # Test Delete
            client.post(f'/delete_t/{tx_id}', data={'csrf_token': 'csrf_audit_token'}, follow_redirects=True)
            db.session.expire_all()
            deleted_tx = Transaction.query.filter_by(id=tx_id, tenant_id=AUDIT_TENANT).first()
            # Check if soft deleted or hard deleted
            if deleted_tx is None or getattr(deleted_tx, 'is_deleted', False):
                report['phase5_crud']['Transaction']['delete'] = 'PASS (soft or hard deleted verified)'
            else:
                report['phase5_crud']['Transaction']['delete'] = 'FAIL'
                record_bug('BUG-CRUD-TX-DEL', 'HIGH', 'Transactions', f'/delete_t/{tx_id}', 'Delete transaction',
                           'Transaction row deleted or marked is_deleted=True', 'Row still active in DB', 'Delete endpoint did not purge or flag row')
        else:
            report['phase5_crud']['Transaction'] = {'create': 'FAIL'}
            record_bug('BUG-CRUD-TX-CRT', 'HIGH', 'Transactions', '/new_transaction', 'Create transaction',
                       'Transaction inserted in DB', 'No row found', 'Transaction creation failed silently')

    # 3. RecurringPlan CRUD
    plan_payload = {
        'name': 'Ofis Kirası',
        'category': 'Maaş',
        'amount': '20000.00',
        'installments': '12',
        'payment_day': '15',
        'flow_type': 'Gider',
        'start_date': '2026-10-01',
        'csrf_token': 'csrf_audit_token'
    }
    client.post('/plans', data=plan_payload, follow_redirects=True)
    with app.app_context():
        created_plan = RecurringPlan.query.filter_by(name='Ofis Kirası', tenant_id=AUDIT_TENANT).first()
        if created_plan:
            plan_id = created_plan.id
            report['phase5_crud']['RecurringPlan'] = {
                'create': 'PASS',
                'id': plan_id,
                'amount': float(created_plan.amount),
                'installments': created_plan.installments
            }
            # Check if transactions / occurrences were generated
            occurrences_count = PlanOccurrence.query.filter_by(plan_id=plan_id, tenant_id=AUDIT_TENANT).count()
            report['phase5_crud']['RecurringPlan']['occurrences_count'] = occurrences_count

            # Delete Plan
            client.post(f'/{plan_id}/delete', data={'csrf_token': 'csrf_audit_token'}, follow_redirects=True)
            db.session.expire_all()
            del_p = RecurringPlan.query.filter_by(id=plan_id, tenant_id=AUDIT_TENANT).first()
            if del_p is None:
                report['phase5_crud']['RecurringPlan']['delete'] = 'PASS'
            else:
                report['phase5_crud']['RecurringPlan']['delete'] = 'FAIL'
                record_bug('BUG-CRUD-PLAN-DEL', 'HIGH', 'Plans', f'/{plan_id}/delete', 'Delete recurring plan',
                           'Plan row deleted from DB', 'Plan still exists in DB', 'Plan delete failed')
        else:
            report['phase5_crud']['RecurringPlan'] = {'create': 'FAIL'}
            record_bug('BUG-CRUD-PLAN-CRT', 'HIGH', 'Plans', '/plans', 'Create recurring plan',
                       'RecurringPlan inserted in DB', 'No row found', 'Plan add endpoint failed')

    # 4. Asset CRUD
    with app.app_context():
        sec = models.AssetSector.query.first()
        sec_id = sec.id if sec else 1

    asset_payload = {
        'name': 'Test Gram Altın',
        'type': 'Emtia',
        'symbol': 'ALTIN',
        'quantity': '10.0',
        'unit_price': '3000.0',
        'purchase_cost': '30000.0',
        'purchase_date': '2026-10-01',
        'currency': 'TRY',
        'risk_level': 'Düşük',
        'liquidity': 'Yüksek',
        'sector_id': sec_id,
        'csrf_token': 'csrf_audit_token'
    }
    client.post('/new_asset', data=asset_payload, follow_redirects=True)
    with app.app_context():
        created_asset = Asset.query.filter_by(symbol='ALTIN', tenant_id=AUDIT_TENANT).first()
        if created_asset:
            asset_id = created_asset.id
            report['phase5_crud']['Asset'] = {
                'create': 'PASS',
                'id': asset_id,
                'quantity': float(created_asset.quantity),
                'purchase_cost': float(created_asset.purchase_cost)
            }
            # Delete asset
            client.post(f'/delete_asset/{asset_id}', data={'csrf_token': 'csrf_audit_token'}, follow_redirects=True)
            db.session.expire_all()
            del_a = Asset.query.filter_by(id=asset_id, tenant_id=AUDIT_TENANT).first()
            if del_a is None:
                report['phase5_crud']['Asset']['delete'] = 'PASS'
            else:
                report['phase5_crud']['Asset']['delete'] = 'FAIL'
                record_bug('BUG-CRUD-ASSET-DEL', 'HIGH', 'Assets', f'/delete_asset/{asset_id}', 'Delete asset',
                           'Asset row deleted from DB', 'Asset still in DB', 'Asset delete endpoint failed')
        else:
            report['phase5_crud']['Asset'] = {'create': 'FAIL'}
            record_bug('BUG-CRUD-ASSET-CRT', 'HIGH', 'Assets', '/new_asset', 'Create asset',
                       'Asset inserted in DB', 'No row found', 'Asset creation failed')


# =========================================================================
# PHASE 6: Independent Calculation & Floating Point / Decimal Precision Validation
# =========================================================================
def run_phase6_calculations():
    print("Executing Phase 6: Independent Calculations & Precision...")
    with app.app_context():
        # Test 1: Financial Balance Math Invariant
        # Initial: 0
        # + Income 5,000.25
        # + Income 10,000.50
        # - Expense 3,250.75
        # - Investment 4,000.00
        # Expected Net Balance = 5,000.25 + 10,000.50 - 3,250.75 - 4,000.00 = 7,750.00
        t1 = Transaction(date="2026-10-01", category="Maaş", description="Inc 1", amount=to_decimal(5000.25), type="Gelir", status="Ödendi", tenant_id=AUDIT_TENANT)
        t2 = Transaction(date="2026-10-02", category="Maaş", description="Inc 2", amount=to_decimal(10000.50), type="Gelir", status="Ödendi", tenant_id=AUDIT_TENANT)
        t3 = Transaction(date="2026-10-03", category="Kira", description="Exp 1", amount=to_decimal(3250.75), type="Gider", status="Ödendi", tenant_id=AUDIT_TENANT)
        t4 = Transaction(date="2026-10-04", category="Fon", description="Inv 1", amount=to_decimal(4000.00), type="Yatırım", status="Ödendi", tenant_id=AUDIT_TENANT)
        db.session.add_all([t1, t2, t3, t4])
        db.session.commit()

        from routes.dashboard import _get_dashboard_service
        ctx = _get_dashboard_service().index_context(AUDIT_TENANT)

        expected_balance = Decimal('7750.00')
        app_balance = to_decimal(ctx.get('year_paid_cash', 0))
        diff_balance = abs(expected_balance - app_balance)

        report['phase6_calculations']['Balance_Invariant'] = {
            'expected_balance': str(expected_balance),
            'actual_balance': str(app_balance),
            'diff': str(diff_balance),
            'result': 'PASS' if diff_balance == Decimal('0.00') else 'FAIL'
        }
        if diff_balance != Decimal('0.00'):
            record_bug('BUG-CALC-BAL', 'CRITICAL', 'DashboardService', 'index_context', 'Calculate net balance',
                       str(expected_balance), str(app_balance), f'Discrepancy of {diff_balance}')

        # Test 2: Asset Position & Realized PnL Calculation
        # Buy: 20 units @ 100.00 = 2,000.00
        # Sell: 10 units @ 150.00
        # Expected Realized PnL = (150 - 100) * 10 = +500.00
        # Remaining units = 10, Sale proceeds = 1,500.00
        from domain.transactions.services import create_asset_position, sell_asset_position
        sec = models.AssetSector.query.first()
        sec_id = sec.id if sec else 1

        a = create_asset_position(
            user_id=1, tenant_id=AUDIT_TENANT, name="Hisse ABC", type="Hisse", symbol="ABC",
            quantity=20.0, unit_price=100.0, purchase_cost=2000.0, value=2000.0, purchase_date="2026-10-01",
            sector_id=sec_id, currency="TRY", risk_level="Orta", liquidity="Yüksek", sync_cash=False
        )
        db.session.commit()

        asset_sold, realized_gain, sale_tx = sell_asset_position(
            asset_id=a.id, quantity=10.0, sale_unit_price=150.0, sale_date="2026-10-02",
            user_id=1, tenant_id=AUDIT_TENANT
        )
        db.session.commit()

        expected_realized_pnl = Decimal('500.00')
        actual_realized_pnl = to_decimal(realized_gain)
        expected_rem_units = Decimal('10.0')
        actual_rem_units = to_decimal(asset_sold.quantity)

        report['phase6_calculations']['Asset_WAC_PnL'] = {
            'expected_pnl': str(expected_realized_pnl),
            'actual_pnl': str(actual_realized_pnl),
            'expected_rem_units': str(expected_rem_units),
            'actual_rem_units': str(actual_rem_units),
            'result': 'PASS' if (actual_realized_pnl == expected_realized_pnl and actual_rem_units == expected_rem_units) else 'FAIL'
        }
        if actual_realized_pnl != expected_realized_pnl:
            record_bug('BUG-CALC-PNL', 'CRITICAL', 'AssetPositionService', 'sell_asset_position', 'Calculate realized PnL on partial sale',
                       str(expected_realized_pnl), str(actual_realized_pnl), 'PnL calculation discrepancy on asset sale')

        # Test 3: Decimal 0.1 + 0.2 precision boundary
        d1 = to_decimal(0.1)
        d2 = to_decimal(0.2)
        expected_sum = Decimal('0.3')
        report['phase6_calculations']['Decimal_Float_Boundary'] = {
            'sum_0.1_0.2': str(d1 + d2),
            'expected': str(expected_sum),
            'result': 'PASS' if (d1 + d2) == expected_sum else 'FAIL'
        }


# =========================================================================
# PHASE 7: Transaction / Rollback / Double Submission / Concurrency Testing
# =========================================================================
def run_phase7_transactions_concurrency():
    print("Executing Phase 7: Rollback & Concurrency...")

    # 1. Rollback Test: Verify atomicity when an operation fails halfway
    with app.app_context():
        count_before = Transaction.query.filter_by(tenant_id=AUDIT_TENANT).count()

        try:
            with db.session.begin_nested():
                # Step 1: Insert valid transaction
                tx_part = Transaction(date="2026-10-06", category="Maaş", description="Partial Tx",
                                      amount=to_decimal(999.00), type="Gelir", status="Ödendi", tenant_id=AUDIT_TENANT)
                db.session.add(tx_part)
                db.session.flush()
                # Step 2: Force DB constraint failure (e.g. invalid foreign key or check constraint)
                db.session.execute(models.db.text("INSERT INTO \"transaction\" (id, amount, tenant_id) VALUES (9999999, 'INVALID_AMOUNT', NULL)"))
                db.session.flush()
        except Exception:
            db.session.rollback()

        count_after = Transaction.query.filter_by(tenant_id=AUDIT_TENANT).count()
        report['phase7_transactions_concurrency']['Rollback_Integrity'] = {
            'count_before': count_before,
            'count_after': count_after,
            'result': 'PASS' if count_before == count_after else 'FAIL'
        }
        if count_before != count_after:
            record_bug('BUG-TX-ROLLBACK', 'CRITICAL', 'Database', 'Transaction rollback', 'Atomic rollback',
                       'Count before == count after', f'Partial write remained: {count_after - count_before} records', 'Session rollback failed to purge uncommitted objects')

    # 2. Concurrency Test: 5 simultaneous threads inserting transactions
    threads = []
    concurrency_errors = []

    def concurrent_insert(idx):
        try:
            with app.app_context():
                t = Transaction(date="2026-10-06", category="Maaş", description=f"Concurrent Tx {idx}",
                                amount=to_decimal(100.0 * (idx + 1)), type="Gelir", status="Ödendi", tenant_id=AUDIT_TENANT)
                db.session.add(t)
                db.session.commit()
        except Exception as e:
            concurrency_errors.append(str(e))

    for i in range(5):
        t = threading.Thread(target=concurrent_insert, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    report['phase7_transactions_concurrency']['Concurrent_Inserts'] = {
        'threads_spawned': 5,
        'errors_caught': len(concurrency_errors),
        'error_details': concurrency_errors,
        'result': 'PASS' if len(concurrency_errors) == 0 else 'FAIL'
    }
    if concurrency_errors:
        record_bug('BUG-CONC-INSERT', 'HIGH', 'Database/Concurrency', 'Concurrent writes', '5 successful writes',
                   f'{len(concurrency_errors)} errors', f'SQLite concurrency locked: {concurrency_errors[0]}')


# =========================================================================
# PHASE 8: Authentication, Authorization & Tenant Isolation (IDOR) Testing
# =========================================================================
def run_phase8_auth_tenant_isolation():
    print("Executing Phase 8: Auth & Tenant Isolation (IDOR)...")
    client = app.test_client()

    with app.app_context():
        # Setup item belonging strictly to Tenant B
        tx_b = Transaction(date="2026-10-06", category="Gizli", description="Tenant B Secret Data",
                           amount=to_decimal(88888.00), type="Gelir", status="Ödendi", tenant_id=AUDIT_TENANT_B)
        db.session.add(tx_b)
        db.session.commit()
        tx_b_id = tx_b.id

        u_a = User.query.filter_by(username=AUDIT_USER).first()
        u_a_id = u_a.id
        u_a.last_session_id = "sess_audit_a_idor"
        db.session.commit()

    # User A logs in
    with client.session_transaction() as sess:
        sess['user_id'] = u_a_id
        sess['session_id'] = "sess_audit_a_idor"
        sess['tenant_id'] = AUDIT_TENANT
        sess['csrf_token'] = "csrf_token_a"
        sess['app_boot_id'] = app.config.get('APP_BOOT_ID')

    # Test 1: IDOR - User A attempts to edit Tenant B's transaction
    resp_edit = client.post(f'/edit_t/{tx_b_id}', data={
        'id': tx_b_id,
        'date': '2026-10-06',
        'category': 'Hacked',
        'description': 'Hacked by Tenant A',
        'amount': '1.00',
        'type': 'Gelir',
        'status': 'Ödendi',
        'csrf_token': 'csrf_token_a'
    }, follow_redirects=True)

    with app.app_context():
        db.session.expire_all()
        tx_b_check = db.session.get(Transaction, tx_b_id)
        is_isolated = (tx_b_check.description == "Tenant B Secret Data" and tx_b_check.amount == Decimal('88888.0000'))

    report['phase8_auth_tenant_isolation']['IDOR_Transaction_Update'] = {
        'status_code': resp_edit.status_code,
        'isolated': is_isolated,
        'result': 'PASS' if is_isolated else 'FAIL'
    }
    if not is_isolated:
        record_bug('BUG-SEC-IDOR-UPD', 'CRITICAL', 'Transactions', f'/edit_t/{tx_b_id}',
                   'User A updating Tenant B transaction', '403/404 Forbidden and row untouched',
                   f'Row modified: {tx_b_check.description}', 'Missing tenant_id filter in transaction edit query')

    # Test 2: IDOR - User A attempts to delete Tenant B's transaction
    resp_del = client.post(f'/delete_t/{tx_b_id}', data={'csrf_token': 'csrf_token_a'}, follow_redirects=True)
    with app.app_context():
        db.session.expire_all()
        tx_b_del_check = db.session.get(Transaction, tx_b_id)
        is_del_isolated = (tx_b_del_check is not None and not getattr(tx_b_del_check, 'is_deleted', False))

    report['phase8_auth_tenant_isolation']['IDOR_Transaction_Delete'] = {
        'status_code': resp_del.status_code,
        'isolated': is_del_isolated,
        'result': 'PASS' if is_del_isolated else 'FAIL'
    }
    if not is_del_isolated:
        record_bug('BUG-SEC-IDOR-DEL', 'CRITICAL', 'Transactions', f'/delete_t/{tx_b_id}',
                   'User A deleting Tenant B transaction', '403/404 Forbidden and row remains',
                   'Row deleted by cross-tenant request', 'Missing tenant_id check in transaction delete')

    # Test 3: Privilege Escalation - Standard User accessing Admin Panel
    resp_admin = client.get('/admin/', follow_redirects=False)
    report['phase8_auth_tenant_isolation']['Privilege_Escalation_Admin'] = {
        'status_code': resp_admin.status_code,
        'result': 'PASS' if resp_admin.status_code in (302, 403) else 'FAIL'
    }
    if resp_admin.status_code == 200:
        record_bug('BUG-SEC-PRIV-ESC', 'CRITICAL', 'Admin', '/admin/', 'Standard user visiting admin panel',
                   '302 Redirect or 403 Forbidden', 'HTTP 200 OK', 'Missing @role_required decorator on admin dashboard')

    # Test 4: CSRF Protection - State-changing POST without CSRF token
    resp_no_csrf = client.post('/new_transaction', data={
        'date': '2026-10-06', 'category': 'Maaş', 'description': 'No CSRF',
        'amount': '100.0', 'type': 'Gelir', 'status': 'Ödendi'
    })
    report['phase8_auth_tenant_isolation']['CSRF_Enforcement'] = {
        'status_code': resp_no_csrf.status_code,
        'result': 'PASS' if resp_no_csrf.status_code == 400 else 'FAIL'
    }
    if resp_no_csrf.status_code != 400:
        record_bug('BUG-SEC-CSRF-MISS', 'HIGH', 'Security', '/new_transaction', 'POST without CSRF token',
                   'HTTP 400 Bad Request', f'HTTP {resp_no_csrf.status_code}', 'CSRF protection failed to reject request')


# =========================================================================
# PHASE 10: Negative, Boundary & Failure Testing
# =========================================================================
def run_phase10_negative_boundaries():
    print("Executing Phase 10: Negative & Boundary Tests...")
    client = app.test_client()

    with app.app_context():
        u = User.query.filter_by(username=AUDIT_USER).first()
        u_id = u.id
        u.last_session_id = "sess_audit_a_neg"
        db.session.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = u_id
        sess['session_id'] = "sess_audit_a_neg"
        sess['tenant_id'] = AUDIT_TENANT
        sess['csrf_token'] = "csrf_token_neg"
        sess['app_boot_id'] = app.config.get('APP_BOOT_ID')

    # 1. Negative Amount: e.g. -500.00
    resp_neg = client.post('/new_transaction', data={
        'date': '2026-10-06', 'category': 'Maaş', 'description': 'Negatif Tutar',
        'amount': '-500.00', 'type': 'Gelir', 'status': 'Ödendi', 'csrf_token': 'csrf_token_neg'
    }, follow_redirects=True)
    with app.app_context():
        neg_tx = Transaction.query.filter_by(description='Negatif Tutar', tenant_id=AUDIT_TENANT).first()
    report['phase10_negative_boundaries']['Negative_Amount'] = {
        'status_code': resp_neg.status_code,
        'row_created': neg_tx is not None,
        'result': 'PASS' if neg_tx is None else 'FAIL'
    }
    if neg_tx is not None:
        record_bug('BUG-BND-NEG-AMT', 'HIGH', 'Transactions', '/new_transaction', 'Insert negative amount (-500.00)',
                   'Validation error, 0 rows in DB', 'Row created with negative amount', 'Form validator permits negative amount in transaction')

    # 2. Zero Amount: 0.00
    resp_zero = client.post('/new_transaction', data={
        'date': '2026-10-06', 'category': 'Maaş', 'description': 'Sıfır Tutar',
        'amount': '0.00', 'type': 'Gelir', 'status': 'Ödendi', 'csrf_token': 'csrf_token_neg'
    }, follow_redirects=True)
    with app.app_context():
        zero_tx = Transaction.query.filter_by(description='Sıfır Tutar', tenant_id=AUDIT_TENANT).first()
    report['phase10_negative_boundaries']['Zero_Amount'] = {
        'status_code': resp_zero.status_code,
        'row_created': zero_tx is not None,
        'result': 'PASS' if zero_tx is None else 'FAIL'
    }
    if zero_tx is not None:
        record_bug('BUG-BND-ZERO-AMT', 'MEDIUM', 'Transactions', '/new_transaction', 'Insert zero amount (0.00)',
                   'Validation error, 0 rows in DB', 'Row created with 0.00 amount', 'Zero amount allowed without rejection')

    # 3. Invalid Date: 2026-02-31 (non-existent day)
    resp_date = client.post('/new_transaction', data={
        'date': '2026-02-31', 'category': 'Maaş', 'description': 'Geçersiz Tarih',
        'amount': '100.00', 'type': 'Gelir', 'status': 'Ödendi', 'csrf_token': 'csrf_token_neg'
    }, follow_redirects=True)
    with app.app_context():
        date_tx = Transaction.query.filter_by(description='Geçersiz Tarih', tenant_id=AUDIT_TENANT).first()
    report['phase10_negative_boundaries']['Invalid_Date'] = {
        'status_code': resp_date.status_code,
        'row_created': date_tx is not None,
        'result': 'PASS' if date_tx is None else 'FAIL'
    }
    if date_tx is not None:
        record_bug('BUG-BND-INV-DATE', 'MEDIUM', 'Transactions', '/new_transaction', 'Insert invalid calendar date (2026-02-31)',
                   'Validation error, 0 rows in DB', 'Row created with invalid date string', 'Date validator does not check calendar existence')

    # 4. XSS Injection in description
    xss_payload = '<script>alert("XSS")</script>'
    client.post('/new_transaction', data={
        'date': '2026-10-06', 'category': 'Maaş', 'description': xss_payload,
        'amount': '150.00', 'type': 'Gelir', 'status': 'Ödendi', 'csrf_token': 'csrf_token_neg'
    }, follow_redirects=True)
    resp_html = client.get('/transactions', follow_redirects=True).get_data(as_text=True)
    has_unescaped_xss = ('<script>alert("XSS")</script>' in resp_html)
    report['phase10_negative_boundaries']['XSS_Sanitization'] = {
        'unescaped_found': has_unescaped_xss,
        'result': 'PASS' if not has_unescaped_xss else 'FAIL'
    }
    if has_unescaped_xss:
        record_bug('BUG-SEC-XSS', 'CRITICAL', 'Transactions', '/transactions', 'Render XSS in transaction table',
                   'HTML-escaped string', 'Raw unescaped script tag executed in DOM', 'Jinja template rendered description without auto-escaping or |safe')


if __name__ == '__main__':
    try:
        setup_test_environment()
        run_phase5_crud()
        run_phase6_calculations()
        run_phase7_transactions_concurrency()
        run_phase8_auth_tenant_isolation()
        run_phase10_negative_boundaries()
    finally:
        cleanup_test_environment()

    Path("logs").mkdir(exist_ok=True)
    with open("logs/audit_comprehensive_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print("COMPREHENSIVE AUDIT SUITE COMPLETED")
    print(f"Total Discovered Bugs: {len(report['discovered_bugs'])}")
    for bug in report['discovered_bugs']:
        print(f"[{bug['severity']}] {bug['bug_id']}: {bug['module']} -> {bug['action']}")
    print("="*60)
