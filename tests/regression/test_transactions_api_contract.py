from decimal import Decimal

import pytest
from flask import g, session

from app import db
from models import BankAccount, Tenant, Transaction


@pytest.mark.regression
def test_transactions_api_has_additive_paginated_contract(authenticated_client):
    response = authenticated_client.get("/api/transactions?page=1")

    assert response.status_code == 200
    payload = response.get_json()
    assert {
        "success",
        "transactions",
        "summary",
        "pagination",
        "filters",
        "accounts",
        "has_more",
    } <= set(payload)
    assert payload["success"] is True
    assert isinstance(payload["transactions"], list)
    assert {
        "total_count",
        "total_amount",
        "total_income",
        "total_expense",
        "total_net",
        "total_pending",
    } <= set(payload["summary"])
    assert payload["pagination"]["page"] == 1
    assert payload["pagination"]["per_page"] == 50
    assert isinstance(payload["pagination"]["has_next"], bool)
    assert isinstance(payload["has_more"], bool)
    assert response.headers["X-Request-ID"]
    assert response.headers["Server-Timing"].startswith("app;dur=")


@pytest.mark.regression
def test_transactions_api_rejects_invalid_filter_json(authenticated_client):
    response = authenticated_client.get(
        "/api/transactions?filters=not-valid-json",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error_code"] == "invalid_filters"


@pytest.mark.regression
def test_transactions_api_requires_authentication_and_tenant(client, app, test_user):
    unauthenticated = client.get("/api/transactions")
    assert unauthenticated.status_code == 401
    assert unauthenticated.get_json()["error_code"] == "authentication_required"

    with client.session_transaction() as client_session:
        client_session["user_id"] = 999999
    invalid_user = client.get("/api/transactions")
    assert invalid_user.status_code == 401
    assert invalid_user.get_json()["error_code"] == "authentication_required"

    with app.test_request_context("/api/transactions"):
        session["user_id"] = test_user.id
        g.tenant_id = None
        result = app.view_functions["transactions.api_transactions"]()
        response, status = result
        assert status == 403
        assert response.get_json()["error_code"] == "tenant_context_required"


@pytest.mark.regression
def test_transactions_api_excludes_deleted_and_foreign_rows_and_filters_accounts(
    authenticated_client, test_user
):
    foreign_tenant = Tenant(id="foreign-api-tenant", name="Foreign API Tenant")
    db.session.add(foreign_tenant)
    own_account = BankAccount(
        tenant_id=test_user.tenant_id,
        name="Primary API Account",
        currency="TRY",
    )
    foreign_account = BankAccount(
        tenant_id=foreign_tenant.id,
        name="Foreign API Account",
        currency="USD",
    )
    db.session.add_all([own_account, foreign_account])
    db.session.flush()

    own = Transaction(
        tenant_id=test_user.tenant_id,
        date="2026-08-20",
        category="Maaş",
        description="Own visible",
        type="Gelir",
        status="Ödendi",
        amount=Decimal("100.00"),
        bank_account_id=own_account.id,
        is_deleted=False,
    )
    deleted = Transaction(
        tenant_id=test_user.tenant_id,
        date="2026-08-21",
        category="Vergi",
        description="Own deleted",
        type="Gider",
        status="Ödendi",
        amount=Decimal("25.00"),
        bank_account_id=own_account.id,
        is_deleted=True,
    )
    foreign = Transaction(
        tenant_id=foreign_tenant.id,
        date="2026-08-22",
        category="Maaş",
        description="Foreign visible",
        type="Gelir",
        status="Ödendi",
        amount=Decimal("900.00"),
        bank_account_id=foreign_account.id,
        is_deleted=False,
    )
    db.session.add_all([own, deleted, foreign])
    db.session.commit()

    response = authenticated_client.get(
        f"/api/transactions?filters={{\"bankAccountId\":{foreign_account.id}}}"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["transactions"] == []
    assert payload["summary"]["total_count"] == 0

    response = authenticated_client.get(
        f"/api/transactions?filters={{\"bankAccountId\":{own_account.id}}}"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert [item["description"] for item in payload["transactions"]] == ["Own visible"]
    assert payload["transactions"][0]["bank_account_name"] == "Primary API Account"
    assert payload["transactions"][0]["bank_account_currency"] == "TRY"
    assert payload["summary"]["total_count"] == 1


@pytest.mark.regression
def test_transactions_api_summary_is_full_filtered_scope_and_order_is_deterministic(
    authenticated_client, test_user
):
    account = BankAccount(
        tenant_id=test_user.tenant_id,
        name="Aggregate API Account",
        currency="TRY",
    )
    db.session.add(account)
    db.session.flush()
    rows = [
        Transaction(
            tenant_id=test_user.tenant_id,
            date="2026-08-23",
            category="Maaş",
            description="Income one",
            type="Gelir",
            status="Ödendi",
            amount=Decimal("100.00"),
            bank_account_id=account.id,
            is_deleted=False,
        ),
        Transaction(
            tenant_id=test_user.tenant_id,
            date="2026-08-23",
            category="Maaş",
            description="Income two",
            type="Gelir",
            status="Bekliyor",
            amount=Decimal("200.00"),
            bank_account_id=account.id,
            is_deleted=False,
        ),
        Transaction(
            tenant_id=test_user.tenant_id,
            date="2026-08-22",
            category="Vergi",
            description="Expense one",
            type="Gider",
            status="Ödendi",
            amount=Decimal("50.00"),
            bank_account_id=account.id,
            is_deleted=False,
        ),
    ]
    db.session.add_all(rows)
    db.session.commit()

    response = authenticated_client.get(
        "/api/transactions?page=1&per_page=2&filters="
        '%7B%22bankAccountId%22%3A' + str(account.id) + '%7D'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert [item["description"] for item in payload["transactions"]] == [
        "Income two",
        "Income one",
    ]
    assert payload["pagination"] == {
        "page": 1,
        "per_page": 2,
        "total": 3,
        "has_next": True,
    }
    assert payload["summary"] == {
        "total_count": 3,
        "total_amount": "350.0000",
        "total_income": "300.0000",
        "total_expense": "50.0000",
        "total_net": "250.0000",
        "total_pending": 1,
        "currency": "TRY",
    }


@pytest.mark.regression
@pytest.mark.parametrize(
    "filters",
    [
        '{"dateFrom":"2026-99-01"}',
        '{"dateFrom":"2026-08-24","dateTo":"2026-08-01"}',
        '{"minAmount":"not-a-number"}',
        '{"minAmount":"20","maxAmount":"10"}',
        '{"types":["Unknown"]}',
        '{"statuses":["Unknown"]}',
        '{"bankAccountId":"not-an-id"}',
    ],
)
def test_transactions_api_rejects_invalid_filter_values(authenticated_client, filters):
    response = authenticated_client.get(
        "/api/transactions?filters=" + filters.replace("{", "%7B").replace("}", "%7D")
    )
    assert response.status_code == 400
    assert response.get_json()["success"] is False


@pytest.mark.regression
def test_transactions_api_get_is_read_only(authenticated_client, test_user):
    before = Transaction.query.filter_by(tenant_id=test_user.tenant_id).count()
    response = authenticated_client.get("/api/transactions")
    after = Transaction.query.filter_by(tenant_id=test_user.tenant_id).count()

    assert response.status_code == 200
    assert before == after


@pytest.mark.regression
def test_transaction_detail_is_tenant_scoped_and_exposes_read_only_context(
    authenticated_client, test_user, test_transaction
):
    account = BankAccount(
        tenant_id=test_user.tenant_id,
        name="Detail API Account",
        currency="TRY",
    )
    db.session.add(account)
    db.session.flush()
    test_transaction.bank_account_id = account.id
    db.session.commit()

    response = authenticated_client.get(f"/api/transactions/{test_transaction.id}")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["bank_account_name"] == "Detail API Account"
    assert payload["bank_account_currency"] == "TRY"
    assert payload["ledger_layer"] == "nakit_olay"
    assert payload["is_immutable"] is True
    assert payload["reconciliation_available"] is True

    db.session.query(Transaction).filter_by(
        id=test_transaction.id,
        tenant_id=test_user.tenant_id,
    ).update({Transaction.is_deleted: True}, synchronize_session=False)
    db.session.commit()
    db.session.expire_all()
    persisted = db.session.get(Transaction, test_transaction.id)
    assert persisted is not None and persisted.is_deleted is True
    assert Transaction.query.filter_by(
        id=test_transaction.id,
        tenant_id=test_user.tenant_id,
        is_deleted=False,
    ).first() is None
    deleted_response = authenticated_client.get(f"/api/transactions/{test_transaction.id}")
    assert deleted_response.status_code == 404
    assert deleted_response.get_json()["error_code"] == "resource_not_found"
