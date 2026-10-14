"""
domain/ledger/services/ledger_watchdog_service.py
=================================================
Continuous Runtime Ledger & Balance Drift Watchdog Service.

Performs deterministic, non-mutating audits of general ledger invariants:
1. Double-Entry Balance Invariant: SUM(debit) == SUM(credit) for every JournalEntry.
2. Cryptographic Block Chain Invariant: Unbroken SHA-256 chain starting from GENESIS.
3. Balance Drift Invariant: Verifies that net cash transaction movements match
   the net General Ledger Cash Asset account balances without silent divergence.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

from domain.ledger.models.ledger_models import Account as LedgerAccount
from domain.ledger.models.ledger_models import JournalEntry, LedgerLine
from models import Tenant, Transaction
from shared.db import db

logger = logging.getLogger(__name__)
_ZERO = Decimal("0.0000")


@dataclass(frozen=True)
class WatchdogFinding:
    """One immutable violation or alert produced by the watchdog."""

    code: str
    severity: str  # 'CRITICAL', 'ERROR', 'WARNING'
    message: str
    tenant_id: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[dict[str, Any]] = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WatchdogAuditResult:
    """Consolidated immutable result of an automated watchdog scan."""

    healthy: bool
    checked_tenants: List[str]
    total_journal_entries: int
    total_ledger_lines: int
    total_paid_transactions: int
    violations: List[WatchdogFinding]
    timestamp: str

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity in ("CRITICAL", "ERROR"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "error_count": self.error_count,
            "checked_tenants": self.checked_tenants,
            "total_journal_entries": self.total_journal_entries,
            "total_ledger_lines": self.total_ledger_lines,
            "total_paid_transactions": self.total_paid_transactions,
            "timestamp": self.timestamp,
            "violations": [v.as_dict() for v in self.violations],
        }


class RuntimeLedgerWatchdog:
    """Deterministic, read-only watchdog verifying accounting invariants and balance drift."""

    def __init__(self, session=None):
        self.session = session or db.session

    def audit_all_tenants(self) -> WatchdogAuditResult:
        """Scan all active tenants in the system."""
        tenants = self.session.query(Tenant.id).all()
        tenant_ids = [t[0] for t in tenants] if tenants else ["default"]
        if "default" not in tenant_ids:
            tenant_ids.append("default")

        all_violations: List[WatchdogFinding] = []
        total_je = 0
        total_ll = 0
        total_tx = 0

        for tid in tenant_ids:
            res = self.audit_tenant(tid)
            all_violations.extend(res.violations)
            total_je += res.total_journal_entries
            total_ll += res.total_ledger_lines
            total_tx += res.total_paid_transactions

        is_healthy = len([v for v in all_violations if v.severity in ("CRITICAL", "ERROR")]) == 0
        return WatchdogAuditResult(
            healthy=is_healthy,
            checked_tenants=tenant_ids,
            total_journal_entries=total_je,
            total_ledger_lines=total_ll,
            total_paid_transactions=total_tx,
            violations=all_violations,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def audit_tenant(self, tenant_id: str) -> WatchdogAuditResult:
        """Audit accounting invariants for a specific tenant."""
        if not tenant_id:
            raise ValueError("tenant_id must not be empty")

        violations: List[WatchdogFinding] = []

        # 1. Fetch entries
        journal_entries = (
            self.session.query(JournalEntry)
            .filter_by(tenant_id=tenant_id)
            .order_by(JournalEntry.id.asc())
            .all()
        )
        total_je = len(journal_entries)

        # 2. Check Double-Entry Balance and Block Chain
        expected_prev_hash = "GENESIS"
        total_ll = 0

        for je in journal_entries:
            lines = (
                self.session.query(LedgerLine)
                .filter_by(journal_entry_id=je.id)
                .order_by(LedgerLine.id.asc())
                .all()
            )
            total_ll += len(lines)

            if not lines:
                violations.append(
                    WatchdogFinding(
                        code="ORPHAN_JOURNAL_ENTRY",
                        severity="CRITICAL",
                        message=f"JournalEntry #{je.id} has no associated ledger lines.",
                        tenant_id=tenant_id,
                        entity_type="journal_entry",
                        entity_id=je.id,
                    )
                )
                continue

            sum_debit = sum((Decimal(str(line.debit)) for line in lines), Decimal("0"))
            sum_credit = sum((Decimal(str(line.credit)) for line in lines), Decimal("0"))

            if sum_debit != sum_credit:
                violations.append(
                    WatchdogFinding(
                        code="LEDGER_UNBALANCED",
                        severity="CRITICAL",
                        message=f"JournalEntry #{je.id} debit sum ({sum_debit}) != credit sum ({sum_credit}).",
                        tenant_id=tenant_id,
                        entity_type="journal_entry",
                        entity_id=je.id,
                        details={"debit": str(sum_debit), "credit": str(sum_credit)},
                    )
                )

            # Cryptographic chain
            if je.previous_hash != expected_prev_hash:
                violations.append(
                    WatchdogFinding(
                        code="CRYPTOGRAPHIC_CHAIN_BROKEN",
                        severity="CRITICAL",
                        message=(
                            f"JournalEntry #{je.id} previous_hash does not link to preceding entry: "
                            f"expected '{expected_prev_hash}', got '{je.previous_hash}'."
                        ),
                        tenant_id=tenant_id,
                        entity_type="journal_entry",
                        entity_id=je.id,
                        details={"expected": expected_prev_hash, "actual": je.previous_hash},
                    )
                )

            expected_prev_hash = je.hash

        # 3. Check Balance Drift Invariant (Transaction Cash Net vs General Ledger Cash Net)
        paid_txs = (
            self.session.query(Transaction)
            .filter_by(tenant_id=tenant_id, status="Ödendi", is_deleted=False)
            .all()
        )
        total_tx = len(paid_txs)

        tx_net_cash = Decimal("0")
        for tx in paid_txs:
            amt = Decimal(str(tx.amount))
            if tx.type == "Gelir":
                tx_net_cash += amt
            elif tx.type in ("Gider", "Yatırım"):
                tx_net_cash -= amt

        # Find Cash account in General Ledger
        cash_account = (
            self.session.query(LedgerAccount)
            .filter_by(tenant_id=tenant_id, name="Nakit Kasa")
            .first()
        )
        ledger_net_cash = Decimal("0")
        if cash_account:
            cash_lines = (
                self.session.query(LedgerLine)
                .filter_by(account_id=cash_account.id)
                .all()
            )
            for cl in cash_lines:
                ledger_net_cash += Decimal(str(cl.debit)) - Decimal(str(cl.credit))

        drift = tx_net_cash - ledger_net_cash
        if abs(drift) > Decimal("0.0001"):
            violations.append(
                WatchdogFinding(
                    code="BALANCE_DRIFT_DETECTED",
                    severity="ERROR",
                    message=(
                        f"Silent balance drift detected for tenant '{tenant_id}': "
                        f"Transaction Net Cash ({tx_net_cash}) != Ledger Net Cash ({ledger_net_cash}). "
                        f"Divergence delta: {drift}."
                    ),
                    tenant_id=tenant_id,
                    entity_type="account",
                    entity_id=cash_account.id if cash_account else None,
                    details={
                        "transaction_net_cash": str(tx_net_cash),
                        "ledger_net_cash": str(ledger_net_cash),
                        "drift_delta": str(drift),
                    },
                )
            )

        is_healthy = len([v for v in violations if v.severity in ("CRITICAL", "ERROR")]) == 0
        return WatchdogAuditResult(
            healthy=is_healthy,
            checked_tenants=[tenant_id],
            total_journal_entries=total_je,
            total_ledger_lines=total_ll,
            total_paid_transactions=total_tx,
            violations=violations,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
