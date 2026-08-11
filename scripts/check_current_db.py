"""Check current database state before import"""
import json
import sys

sys.path.insert(0, 'C:/Users/e.cetin/Desktop/e_cuzdan_v15')

from app import app
from models import Asset, AssetSector, AssetType, Category, RecurringPlan, Transaction, User

with app.app_context():
    print("=== CURRENT DATABASE STATE ===")
    print(f"Users: {User.query.count()}")
    print(f"Categories: {Category.query.count()}")
    print(f"AssetTypes: {AssetType.query.count()}")
    print(f"AssetSectors: {AssetSector.query.count()}")
    print(f"Transactions: {Transaction.query.count()}")
    print(f"RecurringPlans: {RecurringPlan.query.count()}")
    print(f"Assets: {Asset.query.count()}")

    print("\n=== CURRENT USERS ===")
    for u in User.query.all():
        print(f"  id={u.id}, username={u.username}, tenant_id={u.tenant_id}")

    print("\n=== CURRENT CATEGORIES ===")
    for c in Category.query.all():
        print(f"  id={c.id}, name={c.name}, type={c.type}, tenant={c.tenant_id}")

    print("\n=== CURRENT ASSET TYPES ===")
    for at in AssetType.query.all():
        print(f"  id={at.id}, name={at.name}")

    print("\n=== CURRENT ASSET SECTORS ===")
    for s in AssetSector.query.all():
        print(f"  id={s.id}, name={s.name}")

    print("\n=== CURRENT RECURRING PLANS ===")
    for rp in RecurringPlan.query.all():
        print(f"  id={rp.id}, name={rp.name}, category={rp.category}, type={rp.flow_type}, amount={rp.amount}, installments={rp.installments}, tenant={rp.tenant_id}")

    print("\n=== CURRENT TRANSACTIONS (first 10) ===")
    for t in Transaction.query.limit(10).all():
        print(f"  id={t.id}, date={t.date}, cat={t.category}, desc={t.description}, type={t.type}, status={t.status}, amount={t.amount}")

    # Check what's in the backup that's NOT in current DB
    print("\n=== COMPARISON ===")
    with open('C:/Users/e.cetin/Desktop/e_cuzdan_v15/database/decrypted_backup.json', 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    # Users
    current_user_ids = {u.id for u in User.query.all()}
    backup_user_ids = {u['id'] for u in backup_data.get('users', [])}
    print(f"Users: current={current_user_ids}, backup={backup_user_ids}")

    # Categories
    current_cats = {(c.id, c.name) for c in Category.query.all()}
    backup_cats = {(c['id'], c['name']) for c in backup_data.get('categories', [])}
    print(f"Categories: current count={len(current_cats)}, backup count={len(backup_cats)}")
    new_cats = backup_cats - current_cats
    print(f"  New categories to add: {new_cats}")

    # Transactions
    current_tx_ids = {t.id for t in Transaction.query.all()}
    backup_tx_ids = {t['id'] for t in backup_data.get('transactions', [])}
    print(f"Transactions: current count={len(current_tx_ids)}, backup count={len(backup_tx_ids)}")
    new_txs = backup_tx_ids - current_tx_ids
    print(f"  New transactions to add: {len(new_txs)}")
    existing_txs = backup_tx_ids & current_tx_ids
    print(f"  Existing transactions to update: {len(existing_txs)}")

    # Recurring plans
    current_rp_ids = {rp.id for rp in RecurringPlan.query.all()}
    backup_rp_ids = {rp['id'] for rp in backup_data.get('recurring_plans', [])}
    print(f"RecurringPlans: current count={len(current_rp_ids)}, backup count={len(backup_rp_ids)}")
    new_rps = backup_rp_ids - current_rp_ids
    print(f"  New recurring plans to add: {len(new_rps)}")
    existing_rps = backup_rp_ids & current_rp_ids
    print(f"  Existing recurring plans to update: {len(existing_rps)}")

    # Asset types
    current_at_ids = {at.id for at in AssetType.query.all()}
    backup_at_ids = {at['id'] for at in backup_data.get('asset_types', [])}
    print(f"AssetTypes: current count={len(current_at_ids)}, backup count={len(backup_at_ids)}")

    # Asset sectors
    current_as_ids = {s.id for s in AssetSector.query.all()}
    backup_as_ids = {s['id'] for s in backup_data.get('asset_sectors', [])}
    print(f"AssetSectors: current count={len(current_as_ids)}, backup count={len(backup_as_ids)}")
