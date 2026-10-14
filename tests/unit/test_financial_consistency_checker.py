from decimal import Decimal
from types import SimpleNamespace

from domain.ledger.models.ledger_models import LedgerLine
from domain.ledger.services.financial_consistency import FinancialConsistencyChecker
from domain.ledger.services.ledger_service import LedgerService


class QueryStub:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, *criteria):
        filtered = self.items
        for crit in criteria:
            if hasattr(crit, 'left') and hasattr(crit, 'right'):
                col_name = getattr(crit.left, 'name', getattr(crit.left, 'key', None))
                val = getattr(crit.right, 'value', crit.right)
                op_name = getattr(crit.operator, '__name__', '')
                if col_name and op_name:
                    if op_name in ('eq', '__eq__'):
                        filtered = [x for x in filtered if getattr(x, col_name, None) == val]
                    elif op_name in ('ne', '__ne__'):
                        filtered = [x for x in filtered if getattr(x, col_name, None) != val]
        return QueryStub(filtered)

    def filter_by(self, **kwargs):
        filtered = self.items
        for k, v in kwargs.items():
            filtered = [x for x in filtered if getattr(x, k, None) == v]
        return QueryStub(filtered)

    def group_by(self, *_args, **_kwargs):
        return self

    def having(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return list(self.items)


class SessionStub:
    def __init__(self, lines_by_entry=None, related=None, journal_entries=None, transactions=None, ledger_lines=None):
        self.lines_by_entry = lines_by_entry or {}
        self.related = related or {}
        self.journal_entries = list(journal_entries or [])
        self.transactions = list(transactions or [])
        self.ledger_lines = list(ledger_lines or [])
        if self.lines_by_entry and not self.ledger_lines:
            for entry_id, lines in self.lines_by_entry.items():
                for l in lines:
                    if not hasattr(l, 'journal_entry_id'):
                        setattr(l, 'journal_entry_id', entry_id)
                self.ledger_lines.extend(lines)

    def query(self, *entities):
        if len(entities) == 1:
            model = entities[0]
            m_name = getattr(model, '__name__', str(model))
            if 'JournalEntry' in m_name:
                return QueryStub(self.journal_entries)
            if 'LedgerLine' in m_name:
                if self.ledger_lines:
                    return QueryStub(self.ledger_lines)
                items = next(iter(self.lines_by_entry.values()), [])
                return QueryStub(items)
            if 'Transaction' in m_name:
                return QueryStub(self.transactions)
        return QueryStub([])

    def get(self, model, entity_id):
        return self.related.get((model, entity_id))


def _entry(*, entry_id=10, tenant_id="tenant-a", previous_hash="GENESIS", debit="10.00", credit="10.00"):
    lines = [
        SimpleNamespace(
            id=1,
            journal_entry_id=entry_id,
            debit=Decimal(debit),
            credit=Decimal("0"),
        ),
        SimpleNamespace(
            id=2,
            journal_entry_id=entry_id,
            debit=Decimal("0"),
            credit=Decimal(credit),
        ),
    ]
    entry = SimpleNamespace(
        id=entry_id,
        date="2026-08-18",
        description="Test journal entry",
        previous_hash=previous_hash,
        hash=LedgerService.calculate_hash(
            "2026-08-18",
            "Test journal entry",
            Decimal(debit),
            Decimal(credit),
            "GENESIS",
        ),
        status="Posted",
        tenant_id=tenant_id,
    )
    return entry, lines


def test_balanced_ledger_entry_and_hash_chain_are_healthy():
    entry, lines = _entry()
    checker = FinancialConsistencyChecker(
        session=SessionStub(lines_by_entry={entry.id: lines})
    )

    issues, line_count = checker._check_ledger("tenant-a", [entry])

    assert issues == []
    assert line_count == 2


def test_unbalanced_entry_and_hash_chain_break_are_reported():
    entry, lines = _entry(previous_hash="wrong", credit="9.00")
    checker = FinancialConsistencyChecker(
        session=SessionStub(lines_by_entry={entry.id: lines})
    )

    issues, _ = checker._check_ledger("tenant-a", [entry])
    codes = {issue.code for issue in issues}

    assert "LEDGER_NOT_BALANCED" in codes
    assert "LEDGER_HASH_CHAIN_BREAK" in codes
    assert "LEDGER_HASH_MISMATCH" in codes


def test_transaction_bridge_to_foreign_plan_is_reported():
    transaction = SimpleNamespace(
        id=22,
        type="Gider",
        amount=Decimal("25.00"),
        source_type="plan",
        source_id=99,
    )
    foreign_plan = SimpleNamespace(id=99, tenant_id="tenant-b")
    checker = FinancialConsistencyChecker(
        session=SessionStub(related={(object, 99): foreign_plan})
    )

    # The checker asks for the concrete RecurringPlan model. Return the foreign
    # object for any related lookup in this focused unit test.
    checker.session.get = lambda _model, _entity_id: foreign_plan
    issues, plan_count, asset_count = checker._check_transaction_bridges(
        "tenant-a", [transaction]
    )

    assert plan_count == 1
    assert asset_count == 0
    assert {issue.code for issue in issues} == {"TRANSACTION_PLAN_BRIDGE_BROKEN"}


def test_negative_transaction_amount_is_reported():
    transaction = SimpleNamespace(
        id=23,
        type="Gelir",
        amount=Decimal("-1.00"),
        source_type=None,
        source_id=None,
    )
    checker = FinancialConsistencyChecker(session=SessionStub())

    issues, _, _ = checker._check_transaction_bridges("tenant-a", [transaction])

    assert {issue.code for issue in issues} == {"TRANSACTION_AMOUNT_INVALID"}


def test_consistency_report_health_status_distinguishes_warning_and_error():
    from domain.ledger.services.financial_consistency import ConsistencyIssue, ConsistencyReport

    warning_issue = ConsistencyIssue(
        code="TEST_WARN",
        severity="warning",
        message="Minor warning",
        tenant_id="t1",
        entity_type="transaction",
        entity_id=1,
    )
    error_issue = ConsistencyIssue(
        code="TEST_ERR",
        severity="error",
        message="Critical error",
        tenant_id="t1",
        entity_type="ledger",
        entity_id=2,
    )

    # Clean report
    clean_report = ConsistencyReport(
        tenant_id="t1", issues=(), journal_entry_count=0, ledger_line_count=0,
        transaction_count=0, plan_bridge_count=0, asset_bridge_count=0
    )
    assert clean_report.healthy is True
    assert clean_report.error_count == 0

    # Warning-only report must remain healthy
    warning_report = ConsistencyReport(
        tenant_id="t1", issues=(warning_issue,), journal_entry_count=0, ledger_line_count=0,
        transaction_count=0, plan_bridge_count=0, asset_bridge_count=0
    )
    assert warning_report.healthy is True
    assert warning_report.error_count == 0

    # Error report must be unhealthy
    error_report = ConsistencyReport(
        tenant_id="t1", issues=(warning_issue, error_issue), journal_entry_count=0, ledger_line_count=0,
        transaction_count=0, plan_bridge_count=0, asset_bridge_count=0
    )
    assert error_report.healthy is False
    assert error_report.error_count == 1


def test_check_tenant_full_lifecycle_and_multi_tenant_isolation():
    """Verify check_tenant correctly scopes to target tenant and aggregates all issues."""
    entry_a, lines_a = _entry(entry_id=10, tenant_id="tenant-a")
    entry_b, lines_b = _entry(entry_id=20, tenant_id="tenant-b")

    tx_a = SimpleNamespace(
        id=101,
        tenant_id="tenant-a",
        type="Gider",
        amount=Decimal("50.00"),
        source_type=None,
        source_id=None,
    )
    tx_b = SimpleNamespace(
        id=201,
        tenant_id="tenant-b",
        type="Gelir",
        amount=Decimal("100.00"),
        source_type=None,
        source_id=None,
    )

    session = SessionStub(
        journal_entries=[entry_a, entry_b],
        ledger_lines=lines_a + lines_b,
        transactions=[tx_a, tx_b],
    )
    checker = FinancialConsistencyChecker(session=session)

    report_a = checker.check_tenant("tenant-a")

    assert report_a.tenant_id == "tenant-a"
    assert report_a.journal_entry_count == 1
    assert report_a.transaction_count == 1
    assert report_a.ledger_line_count == 2
    assert report_a.healthy is True
    assert len(report_a.issues) == 0


def test_check_tenant_aggregates_ledger_and_bridge_issues_without_failure():
    """Verify check_tenant aggregates ledger_issues and bridge_issues via list concatenation."""
    # Broken entry (unbalanced) -> yields LEDGER_NOT_BALANCED
    entry_bad, lines_bad = _entry(entry_id=30, tenant_id="tenant-bad", credit="5.00")
    # Broken transaction (negative amount) -> yields TRANSACTION_AMOUNT_INVALID
    tx_bad = SimpleNamespace(
        id=301,
        tenant_id="tenant-bad",
        type="Gider",
        amount=Decimal("-10.00"),
        source_type=None,
        source_id=None,
    )

    session = SessionStub(
        journal_entries=[entry_bad],
        ledger_lines=lines_bad,
        transactions=[tx_bad],
    )
    checker = FinancialConsistencyChecker(session=session)

    report = checker.check_tenant("tenant-bad")

    assert report.healthy is False
    codes = {issue.code for issue in report.issues}
    assert "LEDGER_NOT_BALANCED" in codes
    assert "TRANSACTION_AMOUNT_INVALID" in codes
    # Verify both ledger issues and bridge issues were concatenated into issues tuple
    assert len(report.issues) >= 2


def test_check_tenant_requires_tenant_id():
    checker = FinancialConsistencyChecker(session=SessionStub())
    import pytest
    with pytest.raises(ValueError, match="tenant_id is required"):
        checker.check_tenant("")


