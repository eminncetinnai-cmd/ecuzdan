"""Phase 4 Playwright mock servislerinin deterministic davranış testleri."""

from __future__ import annotations

import json

import pytest

from tests.e2e.fixtures.phase4_fixtures import Phase4Fixture
from tests.e2e.mocks.phase4_mock_services import Phase4MockServices


class FakeRequest:
    def __init__(self, url, method="GET", headers=None, body=None):
        self.url = url
        self.method = method
        self.headers = headers or {"x-e2e-tenant": "e2e_phase4_tenant_a"}
        self.post_data = json.dumps(body) if body is not None else None


class FakeRoute:
    def __init__(self, request):
        self.request = request
        self.response = None

    def fulfill(self, **kwargs):
        self.response = kwargs


@pytest.fixture
def mock_services():
    return Phase4MockServices(Phase4Fixture.load())


def response_payload(route):
    assert route.response is not None
    return json.loads(route.response["body"])


@pytest.mark.unit
def test_occurrence_payment_updates_only_mock_state(mock_services):
    route = FakeRoute(
        FakeRequest(
            "http://phase4.test/api/occurrences/9601/pay",
            method="POST",
            body={"amount": "10000.0000", "payment_date": "2026-08-20"},
        )
    )

    mock_services._occurrence_pay(route)
    payload = response_payload(route)

    assert route.response["status"] == 200
    assert payload["success"] is True
    assert payload["data"]["occurrence"]["status"] == "paid"
    assert payload["data"]["occurrence"]["transaction_id"] is not None
    assert len([row for row in mock_services.state["payments"] if row["tenant_id"] == "e2e_phase4_tenant_a"]) == 2
    assert len([row for row in mock_services.state["transactions"] if row["tenant_id"] == "e2e_phase4_tenant_a"]) == 5


@pytest.mark.unit
def test_adjustment_is_idempotent_in_mock_state(mock_services):
    body = {
        "amount_delta": "500.0000",
        "reason_code": "amount_error",
        "reason_text": "E2E tutar düzeltmesi",
        "idempotency_key": "phase4-mock-adjustment-key-0001",
    }
    headers = {"x-e2e-tenant": "e2e_phase4_tenant_a"}
    first_route = FakeRoute(
        FakeRequest(
            "http://phase4.test/api/transactions/9703/adjustments",
            method="POST",
            headers=headers,
            body=body,
        )
    )
    second_route = FakeRoute(
        FakeRequest(
            "http://phase4.test/api/transactions/9703/adjustments",
            method="POST",
            headers=headers,
            body=body,
        )
    )

    mock_services._create_adjustment(first_route)
    mock_services._create_adjustment(second_route)

    first_payload = response_payload(first_route)
    second_payload = response_payload(second_route)
    assert first_route.response["status"] == 201
    assert first_payload["data"]["adjustment"]["status"] == "applied"
    assert second_route.response["status"] == 200
    assert second_payload["idempotency_replayed"] is True
    assert len([row for row in mock_services.state["ledger_adjustments"] if row["tenant_id"] == "e2e_phase4_tenant_a"]) == 2
    assert len([row for row in mock_services.state["transactions"] if row["tenant_id"] == "e2e_phase4_tenant_a"]) == 5


@pytest.mark.unit
def test_cross_tenant_lineage_is_not_exposed(mock_services):
    route = FakeRoute(
        FakeRequest(
            "http://phase4.test/api/transactions/9704/lineage",
            headers={"x-e2e-tenant": "e2e_phase4_tenant_a"},
        )
    )

    mock_services._transaction_lineage(route)
    payload = response_payload(route)

    assert route.response["status"] == 404
    assert payload["success"] is False
    assert payload["error_code"] == "resource_not_found"
