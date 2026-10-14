from decimal import Decimal

import pytest

from models import Tenant, Transaction, db


@pytest.mark.regression
def test_transactions_api_is_scoped_to_authenticated_user_tenant(
    app, authenticated_client
):
    foreign_tenant = Tenant(id="security-foreign", name="Security Foreign Tenant")
    db.session.add(foreign_tenant)
    db.session.flush()
    db.session.add(
        Transaction(
            date="2026-08-18",
            category="Maaş",
            description="FOREIGN_TENANT_SHOULD_NOT_LEAK",
            type="Gelir",
            amount=Decimal("999999.99"),
            status="Ödendi",
            tenant_id=foreign_tenant.id,
        )
    )
    db.session.commit()

    response = authenticated_client.get("/api/transactions")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert all(
        item.get("description") != "FOREIGN_TENANT_SHOULD_NOT_LEAK"
        for item in payload["transactions"]
    )
    assert all(item.get("amount") != "999999.99" for item in payload["transactions"])
