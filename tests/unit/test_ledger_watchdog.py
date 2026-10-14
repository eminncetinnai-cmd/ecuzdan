"""
tests/unit/test_ledger_watchdog.py
==================================
Unit tests for RuntimeLedgerWatchdog and LedgerWatchdogWorker.
Verifies continuous invariant checking, broken chain detection, and balance drift alerting.
"""

from decimal import Decimal

import pytest

from domain.ledger.models.ledger_models import Account as LedgerAccount
from domain.ledger.models.ledger_models import JournalEntry, LedgerLine
from domain.ledger.services.ledger_watchdog_service import RuntimeLedgerWatchdog
from infrastructure.background.ledger_watchdog_worker import LedgerWatchdogWorker
from models import AuditLog, Tenant, Transaction
from shared.db import db


@pytest.fixture
def test_tenant(app):
    with app.app_context():
        tenant_id = "test_watchdog_tenant"
        existing = db.session.get(Tenant, tenant_id)
        if not existing:
            t = Tenant(id=tenant_id, name="Watchdog Test Tenant")
            db.session.add(t)
            db.session.commit()
        yield tenant_id
        # Cleanup
        JournalEntry.query.filter_by(tenant_id=tenant_id).delete()
        LedgerAccount.query.filter_by(tenant_id=tenant_id).delete()
        Transaction.query.filter_by(tenant_id=tenant_id).delete()
        AuditLog.query.filter_by(tenant_id=tenant_id).delete()
        db.session.commit()


def test_watchdog_healthy_tenant(app, test_tenant):
    """Clean tenant with balanced double-entry records must report healthy."""
    with app.app_context():
        watchdog = RuntimeLedgerWatchdog(session=db.session)
        result = watchdog.audit_tenant(test_tenant)

        assert result.healthy is True
        assert result.error_count == 0
        assert len(result.violations) == 0


def test_watchdog_detects_unbalanced_journal_entry(app, test_tenant):
    """An unbalanced journal entry (Debit != Credit) must be flagged with CRITICAL severity."""
    with app.app_context():
        je = JournalEntry(
            tenant_id=test_tenant,
            date="2026-10-08",
            description="Unbalanced JE Test",
            hash="test_unbalanced_hash",
            previous_hash="GENESIS",
            status="Posted"
        )
        db.session.add(je)
        db.session.flush()

        ll1 = LedgerLine(journal_entry_id=je.id, account_id=1, debit=Decimal("100.00"), credit=Decimal("0.00"), currency="TRY")
        ll2 = LedgerLine(journal_entry_id=je.id, account_id=2, debit=Decimal("0.00"), credit=Decimal("80.00"), currency="TRY")
        db.session.add_all([ll1, ll2])
        db.session.commit()

        watchdog = RuntimeLedgerWatchdog(session=db.session)
        result = watchdog.audit_tenant(test_tenant)

        assert result.healthy is False
        assert result.error_count >= 1
        codes = [v.code for v in result.violations]
        assert "LEDGER_UNBALANCED" in codes
        unbalanced_finding = next(v for v in result.violations if v.code == "LEDGER_UNBALANCED")
        assert unbalanced_finding.severity == "CRITICAL"
        assert Decimal(unbalanced_finding.details["debit"]) == Decimal("100.00")
        assert Decimal(unbalanced_finding.details["credit"]) == Decimal("80.00")


def test_watchdog_detects_broken_hash_chain(app, test_tenant):
    """An invalid previous_hash breaking the cryptographic sequence must be flagged."""
    with app.app_context():
        je = JournalEntry(
            tenant_id=test_tenant,
            date="2026-10-08",
            description="Broken Chain JE Test",
            hash="test_broken_hash",
            previous_hash="CORRUPTED_HASH_VALUE",
            status="Posted"
        )
        db.session.add(je)
        db.session.flush()

        ll1 = LedgerLine(journal_entry_id=je.id, account_id=1, debit=Decimal("50.00"), credit=Decimal("0.00"), currency="TRY")
        ll2 = LedgerLine(journal_entry_id=je.id, account_id=2, debit=Decimal("0.00"), credit=Decimal("50.00"), currency="TRY")
        db.session.add_all([ll1, ll2])
        db.session.commit()

        watchdog = RuntimeLedgerWatchdog(session=db.session)
        result = watchdog.audit_tenant(test_tenant)

        assert result.healthy is False
        codes = [v.code for v in result.violations]
        assert "CRYPTOGRAPHIC_CHAIN_BROKEN" in codes
        finding = next(v for v in result.violations if v.code == "CRYPTOGRAPHIC_CHAIN_BROKEN")
        assert finding.details["expected"] == "GENESIS"
        assert finding.details["actual"] == "CORRUPTED_HASH_VALUE"


def test_watchdog_detects_balance_drift(app, test_tenant):
    """When Transaction movements diverge from Ledger Cash accounts, drift must be detected."""
    with app.app_context():
        # Create a paid transaction of 1000 TL
        tx = Transaction(
            tenant_id=test_tenant,
            date="2026-10-08",
            category="Maaş",
            type="Gelir",
            amount=Decimal("1000.00"),
            status="Ödendi",
            description="Paid Salary with No Matching Ledger"
        )
        db.session.add(tx)

        # Create cash account with 500 TL in ledger (a 500 TL drift)
        cash_acct = LedgerAccount(tenant_id=test_tenant, name="Nakit Kasa", type="Asset", currency="TRY")
        db.session.add(cash_acct)
        db.session.flush()

        je = JournalEntry(
            tenant_id=test_tenant,
            date="2026-10-08",
            description="Under-recorded Cash",
            hash="hash_cash_500",
            previous_hash="GENESIS",
            status="Posted"
        )
        db.session.add(je)
        db.session.flush()

        ll1 = LedgerLine(journal_entry_id=je.id, account_id=cash_acct.id, debit=Decimal("500.00"), credit=Decimal("0.00"), currency="TRY")
        ll2 = LedgerLine(journal_entry_id=je.id, account_id=999, debit=Decimal("0.00"), credit=Decimal("500.00"), currency="TRY")
        db.session.add_all([ll1, ll2])
        db.session.commit()

        watchdog = RuntimeLedgerWatchdog(session=db.session)
        result = watchdog.audit_tenant(test_tenant)

        assert result.healthy is False
        assert "BALANCE_DRIFT_DETECTED" in [v.code for v in result.violations]
        drift_finding = next(v for v in result.violations if v.code == "BALANCE_DRIFT_DETECTED")
        assert Decimal(drift_finding.details["drift_delta"]) == Decimal("500.00")


def test_watchdog_worker_run_once_persists_alerts(app, test_tenant):
    """LedgerWatchdogWorker run_once must record AuditLog alerts when violations occur."""
    with app.app_context():
        # Create unbacked unbalanced entry
        je = JournalEntry(
            tenant_id=test_tenant,
            date="2026-10-08",
            description="Alert Persistence Test",
            hash="alert_hash",
            previous_hash="INVALID",
            status="Posted"
        )
        db.session.add(je)
        db.session.commit()

        worker = LedgerWatchdogWorker(flask_app=app, interval_seconds=60)
        result = worker.run_once()

        assert result.healthy is False
        # Verify an AuditLog entry was written
        alerts = AuditLog.query.filter_by(tenant_id=test_tenant, username="SYSTEM_LEDGER_WATCHDOG").all()
        assert len(alerts) >= 1
        assert "ALERT_" in alerts[0].action
