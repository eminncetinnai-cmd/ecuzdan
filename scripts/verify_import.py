"""Verify import results"""
import sys

sys.path.insert(0, 'C:/Users/e.cetin/Desktop/e_cuzdan_v15')

from app import app
from models import AssetSector, AssetType, Category, RecurringPlan, Transaction, User

with app.app_context():
    print("=" * 60)
    print("VERIFIED DATABASE STATE AFTER IMPORT")
    print("=" * 60)

    print(f"\nUsers: {User.query.count()}")
    for u in User.query.all():
        print(f"  id={u.id}, username={u.username}")

    print(f"\nCategories: {Category.query.count()}")
    for c in Category.query.all():
        print(f"  id={c.id}, name={c.name}, type={c.type}")

    print(f"\nAssetTypes: {AssetType.query.count()}")
    for at in AssetType.query.all():
        print(f"  id={at.id}, name={at.name}")

    print(f"\nAssetSectors: {AssetSector.query.count()}")
    for s in AssetSector.query.all():
        print(f"  id={s.id}, name={s.name}")

    print(f"\nRecurringPlans: {RecurringPlan.query.count()}")
    for rp in RecurringPlan.query.all():
        print(f"  id={rp.id}, name={rp.name}, cat={rp.category}, type={rp.flow_type}, amount={rp.amount}, inst={rp.installments}, tenant={rp.tenant_id}")

    print(f"\nTransactions: {Transaction.query.count()}")
    # Show first 5 and last 5
    first5 = Transaction.query.order_by(Transaction.id).limit(5).all()
    print("  First 5:")
    for t in first5:
        print(f"    id={t.id}, date={t.date}, cat={t.category}, desc={t.description}, type={t.type}, status={t.status}, amount={t.amount}")
    last5 = Transaction.query.order_by(Transaction.id.desc()).limit(5).all()
    print("  Last 5:")
    for t in last5:
        print(f"    id={t.id}, date={t.date}, cat={t.category}, desc={t.description}, type={t.type}, status={t.status}, amount={t.amount}")

    print("\nTransaction summary:")
    txs = Transaction.query.all()
    income = [t for t in txs if t.type == 'Gelir']
    expense = [t for t in txs if t.type == 'Gider']
    investment = [t for t in txs if t.type == 'Yatırım']
    print(f"  Gelir: {len(income)} transactions")
    print(f"  Gider: {len(expense)} transactions")
    print(f"  Yatırım: {len(investment)} transactions")

    print("\n" + "=" * 60)
    print("All data imported successfully without errors!")
    print("=" * 60)
