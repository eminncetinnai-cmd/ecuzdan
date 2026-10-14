"""Read-only financial consistency checks for a tenant.

The checker never mutates application data. It reports ledger balance/hash-chain
issues and broken transaction-to-plan/asset references so callers can alert,
block a release, or investigate without silently repairing financial records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func

from domain.ledger.models.ledger_models import JournalEntry, LedgerLine
from domain.ledger.services.ledger_service import LedgerService
from models import Asset, RecurringPlan, Transaction
from shared.db import db

_ZERO = Decimal("0.0000")
_VALID_TRANSACTION_TYPES = {"Gelir", "Gider", "Yatırım", "Transfer"}
_VALID_LEDGER_STATUSES = {"Posted", "Reversed"}
_PLAN_SOURCE_TYPES = {"plan"}
_ASSET_SOURCE_TYPES = {"asset", "asset_sale", "asset_dividend", "asset_interest"}


@dataclass(frozen=True)
class ConsistencyIssue:
    """One deterministic finding produced by the checker."""

    code: str
    severity: str
    message: str
    tenant_id: str
    entity_type: str | None = None
    entity_id: int | None = None
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsistencyReport:
    """Immutable result of a tenant consistency scan."""

    tenant_id: str
    issues: tuple[ConsistencyIssue, ...]
    journal_entry_count: int
    ledger_line_count: int
    transaction_count: int
    plan_bridge_count: int
    asset_bridge_count: int

    @property
    def healthy(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "healthy": self.healthy,
            "error_count": self.error_count,
            "journal_entry_count": self.journal_entry_count,
            "ledger_line_count": self.ledger_line_count,
            "transaction_count": self.transaction_count,
            "plan_bridge_count": self.plan_bridge_count,
            "asset_bridge_count": self.asset_bridge_count,
            "issues": [issue.as_dict() for issue in self.issues],
        }


class FinancialConsistencyChecker:
    """Run non-mutating integrity checks for one tenant."""

    def __init__(self, session=None):
        self.session = session or db.session

    def check_tenant(self, tenant_id: str) -> ConsistencyReport:
        if not tenant_id:
            raise ValueError("tenant_id is required")

        journal_entries = (
            self.session.query(JournalEntry)
            .filter(JournalEntry.tenant_id == tenant_id)
            .order_by(JournalEntry.id.asc())
            .all()
        )
        ledger_issues, ledger_line_count = self._check_ledger(
            tenant_id, journal_entries
        )

        transactions = (
            self.session.query(Transaction)
            .filter(Transaction.tenant_id == tenant_id)
            .order_by(Transaction.id.asc())
            .all()
        )
        bridge_issues, plan_bridge_count, asset_bridge_count = (
            self._check_transaction_bridges(tenant_id, transactions)
        )
        duplicate_issues = self._check_duplicate_transactions(tenant_id)

        return ConsistencyReport(
            tenant_id=tenant_id,
            issues=tuple(ledger_issues + bridge_issues + duplicate_issues),
            journal_entry_count=len(journal_entries),
            ledger_line_count=ledger_line_count,
            transaction_count=len(transactions),
            plan_bridge_count=plan_bridge_count,
            asset_bridge_count=asset_bridge_count,
        )

    def _check_ledger(
        self, tenant_id: str, journal_entries: list[JournalEntry]
    ) -> tuple[list[ConsistencyIssue], int]:
        issues: list[ConsistencyIssue] = []
        expected_previous_hash = "GENESIS"
        ledger_line_count = 0

        for entry in journal_entries:
            lines = (
                self.session.query(LedgerLine)
                .filter(LedgerLine.journal_entry_id == entry.id)
                .order_by(LedgerLine.id.asc())
                .all()
            )
            ledger_line_count += len(lines)
            total_debit = sum(
                (_to_decimal(line.debit) for line in lines), start=Decimal("0")
            )
            total_credit = sum(
                (_to_decimal(line.credit) for line in lines), start=Decimal("0")
            )

            if not lines:
                issues.append(
                    self._issue(
                        tenant_id,
                        "LEDGER_ENTRY_WITHOUT_LINES",
                        "error",
                        "Journal entry has no ledger lines.",
                        "journal_entry",
                        entry.id,
                    )
                )
            if total_debit.quantize(_ZERO) != total_credit.quantize(_ZERO):
                issues.append(
                    self._issue(
                        tenant_id,
                        "LEDGER_NOT_BALANCED",
                        "error",
                        "Total debit and credit are not equal.",
                        "journal_entry",
                        entry.id,
                        {"debit": str(total_debit), "credit": str(total_credit)},
                    )
                )
            for line in lines:
                if _to_decimal(line.debit) < 0 or _to_decimal(line.credit) < 0:
                    issues.append(
                        self._issue(
                            tenant_id,
                            "NEGATIVE_LEDGER_LINE",
                            "error",
                            "Ledger debit/credit values cannot be negative.",
                            "ledger_line",
                            line.id,
                        )
                    )
                if _to_decimal(line.debit) > 0 and _to_decimal(line.credit) > 0:
                    issues.append(
                        self._issue(
                            tenant_id,
                            "LEDGER_LINE_BOTH_SIDES",
                            "error",
                            "A ledger line cannot contain both debit and credit.",
                            "ledger_line",
                            line.id,
                        )
                    )

            if entry.previous_hash != expected_previous_hash:
                issues.append(
                    self._issue(
                        tenant_id,
                        "LEDGER_HASH_CHAIN_BREAK",
                        "error",
                        "Journal entry previous_hash does not match the prior entry.",
                        "journal_entry",
                        entry.id,
                        {
                            "expected": expected_previous_hash,
                            "actual": entry.previous_hash,
                        },
                    )
                )
            if not entry.hash:
                issues.append(
                    self._issue(
                        tenant_id,
                        "LEDGER_HASH_MISSING",
                        "error",
                        "Journal entry hash is missing.",
                        "journal_entry",
                        entry.id,
                    )
                )
            else:
                expected_hash = LedgerService.calculate_hash(
                    entry.date,
                    entry.description or "",
                    total_debit,
                    total_credit,
                    entry.previous_hash or "GENESIS",
                )
                if entry.hash != expected_hash:
                    issues.append(
                        self._issue(
                            tenant_id,
                            "LEDGER_HASH_MISMATCH",
                            "error",
                            "Journal entry hash does not match its content.",
                            "journal_entry",
                            entry.id,
                            {"expected": expected_hash, "actual": entry.hash},
                        )
                    )

            if entry.status not in _VALID_LEDGER_STATUSES:
                issues.append(
                    self._issue(
                        tenant_id,
                        "LEDGER_STATUS_INVALID",
                        "error",
                        "Journal entry has an unsupported status.",
                        "journal_entry",
                        entry.id,
                        {"status": entry.status},
                    )
                )
            expected_previous_hash = entry.hash or expected_previous_hash

        return issues, ledger_line_count

    def _check_transaction_bridges(
        self, tenant_id: str, transactions: list[Transaction]
    ) -> tuple[list[ConsistencyIssue], int, int]:
        issues: list[ConsistencyIssue] = []
        plan_bridge_count = 0
        asset_bridge_count = 0

        for transaction in transactions:
            if transaction.type not in _VALID_TRANSACTION_TYPES:
                issues.append(
                    self._issue(
                        tenant_id,
                        "TRANSACTION_TYPE_INVALID",
                        "error",
                        "Transaction type is outside the supported domain values.",
                        "transaction",
                        transaction.id,
                        {"type": transaction.type},
                    )
                )
            if _to_decimal(transaction.amount) <= 0:
                issues.append(
                    self._issue(
                        tenant_id,
                        "TRANSACTION_AMOUNT_INVALID",
                        "error",
                        "Transaction amount must be positive.",
                        "transaction",
                        transaction.id,
                        {"amount": str(transaction.amount)},
                    )
                )

            if transaction.source_type in _PLAN_SOURCE_TYPES:
                plan_bridge_count += 1
                plan = self.session.get(RecurringPlan, transaction.source_id)
                if not plan or plan.tenant_id != tenant_id:
                    issues.append(
                        self._issue(
                            tenant_id,
                            "TRANSACTION_PLAN_BRIDGE_BROKEN",
                            "error",
                            "Transaction points to a missing or foreign plan.",
                            "transaction",
                            transaction.id,
                            {"source_id": transaction.source_id},
                        )
                    )
            elif transaction.source_type in _ASSET_SOURCE_TYPES:
                asset_bridge_count += 1
                asset = self.session.get(Asset, transaction.source_id)
                if not asset or asset.tenant_id != tenant_id:
                    issues.append(
                        self._issue(
                            tenant_id,
                            "TRANSACTION_ASSET_BRIDGE_BROKEN",
                            "error",
                            "Transaction points to a missing or foreign asset.",
                            "transaction",
                            transaction.id,
                            {"source_id": transaction.source_id},
                        )
                    )

        return issues, plan_bridge_count, asset_bridge_count

    def _check_duplicate_transactions(self, tenant_id: str) -> list[ConsistencyIssue]:
        duplicate_groups = (
            self.session.query(
                Transaction.date,
                Transaction.category,
                Transaction.description,
                Transaction.amount,
                func.count(Transaction.id).label("duplicate_count"),
            )
            .filter(Transaction.tenant_id == tenant_id)
            .group_by(
                Transaction.date,
                Transaction.category,
                Transaction.description,
                Transaction.amount,
            )
            .having(func.count(Transaction.id) > 1)
            .all()
        )
        return [
            self._issue(
                tenant_id,
                "TRANSACTION_DUPLICATE_GROUP",
                "error",
                "Multiple transactions share the deduplication key.",
                "transaction",
                details={
                    "date": group.date,
                    "category": group.category,
                    "description": group.description,
                    "amount": str(group.amount),
                    "count": group.duplicate_count,
                },
            )
            for group in duplicate_groups
        ]

    @staticmethod
    def _issue(
        tenant_id: str,
        code: str,
        severity: str,
        message: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> ConsistencyIssue:
        return ConsistencyIssue(
            code=code,
            severity=severity,
            message=message,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")
