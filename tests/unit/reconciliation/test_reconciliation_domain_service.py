"""Unit tests for Reconciliation Domain Service (domain/reconciliation/service.py).

Tests parameter parsing validations, cash flow signing and aggregation,
statement resolution, multi-currency account handling, and reconciliation worksheets.
"""

from decimal import Decimal
import pytest
from domain.reconciliation.models import BankAccount, BankStatementSnapshot
from domain.reconciliation.service import (
    ReconciliationAccountNotFoundError,
    ReconciliationInputError,
    _fmt,
    _signed_cash,
    _total,
    _serialize_account,
    build_reconciliation,
    create_bank_account,
    get_bank_account,
    list_bank_accounts,
    list_statement_snapshots,
    parse_reconciliation_params,
    save_statement_snapshot,
)
from models import Transaction, db


class MockTx:
    def __init__(self, tx_type, amount):
        self.type = tx_type
        self.amount = amount


def test_fmt_and_signed_cash():
    assert _fmt(Decimal("123.45678")) == "123.4568"
    assert _fmt(None) is None

    # Signed cash rules
    assert _signed_cash(MockTx("Gelir", 100)) == Decimal("100")
    assert _signed_cash(MockTx("Gider", 50)) == Decimal("-50")
    assert _signed_cash(MockTx("Yatırım", 30)) == Decimal("-30")
    assert _signed_cash(MockTx("Transfer", 200)) == Decimal("0")

    total = _total([MockTx("Gelir", 100), MockTx("Gider", 40), MockTx("Transfer", 500)])
    assert total == Decimal("60")


def test_parse_reconciliation_params_valid():
    params = {
        "as_of": "2026-10-14",
        "statement_balance": "1500.50",
        "pending_limit": "25",
        "account_id": "3",
        "currency": "try",
    }
    parsed = parse_reconciliation_params(params)
    assert parsed["as_of"] == "2026-10-14"
    assert parsed["statement_balance"] == Decimal("1500.50")
    assert parsed["pending_limit"] == 25
    assert parsed["account_id"] == 3
    assert parsed["currency"] == "TRY"


def test_parse_reconciliation_params_validation_errors():
    # Invalid date
    with pytest.raises(ReconciliationInputError, match="YYYY-MM-DD"):
        parse_reconciliation_params({"as_of": "14-10-2026"})

    # Invalid statement balance
    with pytest.raises(ReconciliationInputError, match="geçerli bir sayı"):
        parse_reconciliation_params({"statement_balance": "abc"})

    # Non-finite statement balance
    with pytest.raises(ReconciliationInputError, match="geçerli bir sayı"):
        parse_reconciliation_params({"statement_balance": "Infinity"})

    # Invalid pending limit
    with pytest.raises(ReconciliationInputError, match="tam sayı"):
        parse_reconciliation_params({"pending_limit": "xyz"})
    with pytest.raises(ReconciliationInputError, match="1 ile 200"):
        parse_reconciliation_params({"pending_limit": "0"})
    with pytest.raises(ReconciliationInputError, match="1 ile 200"):
        parse_reconciliation_params({"pending_limit": "250"})

    # Invalid account_id
    with pytest.raises(ReconciliationInputError, match="tam sayı"):
        parse_reconciliation_params({"account_id": "abc"})
    with pytest.raises(ReconciliationInputError, match="pozitif"):
        parse_reconciliation_params({"account_id": "-5"})

    # Invalid currency
    with pytest.raises(ReconciliationInputError, match="ISO 4217"):
        parse_reconciliation_params({"currency": "US1"})
    with pytest.raises(ReconciliationInputError, match="ISO 4217"):
        parse_reconciliation_params({"currency": "TOOLONG"})


def test_serialize_account():
    class DummyAccount:
        id = 1
        name = "Vadesiz TL"
        institution = "İş Bankası"
        account_type = "checking"
        currency = "TRY"
        is_active = True
        created_at = None

    data = _serialize_account(DummyAccount())
    assert data["id"] == 1
    assert data["name"] == "Vadesiz TL"
    assert data["currency"] == "TRY"
    assert data["is_active"] is True


def test_build_reconciliation_account_not_found(app):
    with app.app_context():
        with pytest.raises(ReconciliationAccountNotFoundError):
            build_reconciliation(
                tenant_id="default",
                as_of="2026-10-14",
                bank_account_id=999999,
            )


def test_build_reconciliation_single_account(app):
    with app.app_context():
        tenant_id = "default"
        # Seed bank account
        account = BankAccount(
            name="Test TL Hesabı",
            institution="Garanti",
            account_type="checking",
            currency="TRY",
            is_active=True,
            tenant_id=tenant_id,
        )
        db.session.add(account)
        db.session.commit()

        # Seed transactions
        t1 = Transaction(
            type="Gelir",
            category="Maaş",
            status="Ödendi",
            amount=20000.0,
            date="2026-10-01",
            bank_account_id=account.id,
            tenant_id=tenant_id,
            is_deleted=False,
        )
        t2 = Transaction(
            type="Gider",
            category="Kira",
            status="Ödendi",
            amount=8000.0,
            date="2026-10-02",
            bank_account_id=account.id,
            tenant_id=tenant_id,
            is_deleted=False,
        )
        # Pending transaction
        t3 = Transaction(
            type="Gider",
            category="Fatura",
            status="Bekliyor",
            amount=500.0,
            date="2026-10-05",
            bank_account_id=account.id,
            tenant_id=tenant_id,
            is_deleted=False,
        )
        db.session.add_all([t1, t2, t3])
        db.session.commit()

        res = build_reconciliation(
            tenant_id=tenant_id,
            as_of="2026-10-14",
            bank_account_id=account.id,
            statement_balance=Decimal("12000.00"),
        )

        assert res["success"] is True
        assert res["scope"] == "account"
        assert res["currency"] == "TRY"
        # Cleared balance = 20000 - 8000 = 12000
        assert Decimal(res["cleared_balance"]) == Decimal("12000.0000")
        assert Decimal(res["statement_balance"]) == Decimal("12000.0000")
        assert res["status_code"] == "explained_by_pending"
        assert res["explainable"] is True
        assert res["reconciled"] is False
        assert Decimal(res["difference"]) == Decimal("500.0000")
        assert res["pending_count"] == 1

        # Now test exact match when statement_balance matches book_balance (11500.00)
        res_exact = build_reconciliation(
            tenant_id=tenant_id,
            as_of="2026-10-14",
            bank_account_id=account.id,
            statement_balance=Decimal("11500.00"),
        )
        assert res_exact["status_code"] == "reconciled"
        assert res_exact["reconciled"] is True
        assert Decimal(res_exact["difference"]) == Decimal("0.0000")


def test_build_reconciliation_with_saved_snapshot(app):
    with app.app_context():
        tenant_id = "default"
        account = BankAccount.query.filter_by(tenant_id=tenant_id, is_active=True).first()
        if not account:
            account = BankAccount(
                name="Snapshot Hesabı",
                institution="Akbank",
                currency="TRY",
                is_active=True,
                tenant_id=tenant_id,
            )
            db.session.add(account)
            db.session.commit()

        snapshot = BankStatementSnapshot(
            bank_account_id=account.id,
            as_of="2026-10-10",
            balance=Decimal("12000.00"),
            currency="TRY",
            tenant_id=tenant_id,
        )
        db.session.add(snapshot)
        db.session.commit()

        # Reconcile without explicit statement_balance -> uses saved snapshot
        res = build_reconciliation(
            tenant_id=tenant_id,
            as_of="2026-10-14",
            bank_account_id=account.id,
            statement_balance=None,
        )
        assert res["statement_source"] == "saved_snapshot"
        assert res["statement_as_of"] == "2026-10-10"


def test_build_reconciliation_multi_currency_and_all_accounts(app):
    with app.app_context():
        tenant_id = "multi_curr_tenant"
        acc_try = BankAccount(
            name="TL Kasa",
            institution="Garanti",
            currency="TRY",
            is_active=True,
            tenant_id=tenant_id,
        )
        acc_usd = BankAccount(
            name="USD Kasa",
            institution="İş Bankası",
            currency="USD",
            is_active=True,
            tenant_id=tenant_id,
        )
        db.session.add_all([acc_try, acc_usd])
        db.session.commit()

        # Without currency specified, when multiple currencies exist -> requires selection
        res = build_reconciliation(tenant_id=tenant_id, as_of="2026-10-14")
        assert res["status_code"] == "currency_selection_required"
        assert len(res["currency_groups"]) == 2

        # Filter by USD
        res_usd = build_reconciliation(tenant_id=tenant_id, as_of="2026-10-14", currency="USD")
        assert res_usd["currency"] == "USD"
        assert res_usd["scope"] == "all_accounts"
        assert res_usd["status_code"] == "statement_required"


def test_bank_account_crud_and_snapshots(app):
    with app.app_context():
        tenant_id = "crud_tenant"
        # 1. Create bank account
        acc = create_bank_account(
            tenant_id=tenant_id,
            name="Yeni Vadesiz",
            institution="Yapı Kredi",
            account_type="checking",
            currency="TRY",
            created_by=1,
        )
        assert acc.id is not None
        assert acc.name == "Yeni Vadesiz"

        # 2. Get bank account
        fetched = get_bank_account(acc.id, tenant_id)
        assert fetched is not None
        assert fetched.id == acc.id

        # 3. Non-existent account returns None
        assert get_bank_account(999999, tenant_id) is None

        # 4. Save statement snapshot (create)
        snap1 = save_statement_snapshot(
            tenant_id=tenant_id,
            bank_account_id=acc.id,
            as_of="2026-10-01",
            balance=Decimal("5000.00"),
            currency="TRY",
            note="Ekim basi ekstre",
            source="manual",
        )
        assert snap1.id is not None
        assert snap1.balance == Decimal("5000.00")

        # 5. Save statement snapshot (update existing on same date and currency)
        snap1_updated = save_statement_snapshot(
            tenant_id=tenant_id,
            bank_account_id=acc.id,
            as_of="2026-10-01",
            balance=Decimal("5500.00"),
            currency="TRY",
            note="Ekim basi ekstre duzeltildi",
            source="manual",
        )
        assert snap1_updated.id == snap1.id
        assert snap1_updated.balance == Decimal("5500.00")

        # 6. List statement snapshots
        snapshots = list_statement_snapshots(acc.id, tenant_id)
        assert len(snapshots) == 1
        assert snapshots[0].id == snap1.id


def test_build_reconciliation_empty_accounts(app):
    with app.app_context():
        tenant_id = "empty_tenant"
        res = build_reconciliation(tenant_id=tenant_id, as_of="2026-10-14")
        assert res["status_code"] == "no_accounts"
        assert res["transaction_count"] == 0


