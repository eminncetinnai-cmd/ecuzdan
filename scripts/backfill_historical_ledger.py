#!/usr/bin/env python3
"""
scripts/backfill_historical_ledger.py
======================================
Historical Paid Transactions General Ledger Backfill Migration.

Synchronizes historical paid transactions created before Sprint 18 dual-write
provisioning into the immutable double-entry ledger (journal_entry and ledger_line).
"""

import argparse
import logging
import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from domain.ledger.models.ledger_models import Account as LedgerAccount
from domain.ledger.models.ledger_models import JournalEntry
from domain.ledger.services.ledger_service import LedgerService
from models import Transaction
from shared.db import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_historical_ledger")


def backfill_historical_ledger(dry_run: bool = False) -> int:
    app = create_app()
    with app.app_context():
        # Step 1: Find all paid transactions
        paid_txs = Transaction.query.filter_by(status="Ödendi", is_deleted=False).order_by(Transaction.date.asc(), Transaction.id.asc()).all()
        logger.info("Found %d total paid transactions in database", len(paid_txs))

        unbacked = []
        for tx in paid_txs:
            je = JournalEntry.query.filter_by(tenant_id=tx.tenant_id, date=tx.date, description=tx.description).first()
            if not je:
                unbacked.append(tx)

        logger.info("Identified %d historical transactions without ledger entries", len(unbacked))
        if not unbacked:
            logger.info("All paid transactions already have ledger entries. Nothing to do.")
            return 0

        created_count = 0
        for tx in unbacked:
            tenant_id = tx.tenant_id or "default"
            dec_amount = Decimal(str(tx.amount))
            logger.info("Processing TX #%d (date: %s, tenant: %s, type: %s, amount: %s, desc: '%s')",
                        tx.id, tx.date, tenant_id, tx.type, dec_amount, tx.description)

            # Resolve accounts
            cash_acct = LedgerAccount.query.filter_by(tenant_id=tenant_id, name="Nakit Kasa", type="Asset").first()
            if not cash_acct:
                cash_acct = LedgerAccount(tenant_id=tenant_id, name="Nakit Kasa", type="Asset", currency="TRY")
                db.session.add(cash_acct)
                db.session.flush()

            acct_type = "Revenue" if tx.type == "Gelir" else ("Asset" if tx.type == "Yatırım" else "Expense")
            target_acct = LedgerAccount.query.filter_by(tenant_id=tenant_id, name=tx.category).first()
            if not target_acct:
                target_acct = LedgerAccount(tenant_id=tenant_id, name=tx.category, type=acct_type, currency="TRY")
                db.session.add(target_acct)
                db.session.flush()

            if tx.type == "Gelir":
                lines = [
                    {"account_id": cash_acct.id, "debit": dec_amount, "credit": Decimal("0.0000"), "currency": "TRY"},
                    {"account_id": target_acct.id, "debit": Decimal("0.0000"), "credit": dec_amount, "currency": "TRY"}
                ]
            else:
                lines = [
                    {"account_id": cash_acct.id, "debit": Decimal("0.0000"), "credit": dec_amount, "currency": "TRY"},
                    {"account_id": target_acct.id, "debit": dec_amount, "credit": Decimal("0.0000"), "currency": "TRY"}
                ]

            if not dry_run:
                je = LedgerService.record_transaction(
                    tenant_id=tenant_id,
                    date=tx.date,
                    description=tx.description or tx.category,
                    lines=lines
                )
                logger.info("Created JournalEntry #%d with hash %s (prev: %s)", je.id, je.hash[:16], je.previous_hash[:16])
            created_count += 1

        if dry_run:
            logger.info("[DRY-RUN] Would create %d JournalEntries and %d LedgerLines", created_count, created_count * 2)
            db.session.rollback()
        else:
            db.session.commit()
            logger.info("Successfully committed %d JournalEntries and %d LedgerLines to database", created_count, created_count * 2)

        return created_count


def main():
    parser = argparse.ArgumentParser(description="Backfill historical transactions into ledger")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without committing changes")
    args = parser.parse_args()

    count = backfill_historical_ledger(dry_run=args.dry_run)
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
