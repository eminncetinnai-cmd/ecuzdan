"""Playwright Phase 4 testleri için opt-in fixture'lar."""

from __future__ import annotations

import os

import pytest

from tests.e2e.fixtures.phase4_fixtures import Phase4Fixture
from tests.e2e.mocks.phase4_mock_services import Phase4MockServices


@pytest.fixture
def phase4_data() -> Phase4Fixture:
    """Her test için bağımsız fixture verisi yükle."""
    return Phase4Fixture.load()


@pytest.fixture
def phase4_tenant_id() -> str:
    return os.getenv("E2E_PHASE4_TENANT", "e2e_phase4_tenant_a")


@pytest.fixture
def phase4_mock_services(page, phase4_data, phase4_tenant_id) -> Phase4MockServices:
    """Faz 4 endpoint'lerini yalnızca ilgili test page'inde mock'la."""
    services = Phase4MockServices(phase4_data, phase4_tenant_id)
    services.install(page)
    return services


@pytest.fixture
def phase4_authenticated_page(page):
    """Gerçek local/staging login gerektiren testler için opt-in fixture."""
    username = os.getenv("ECUZDAN_E2E_USERNAME")
    password = os.getenv("ECUZDAN_E2E_PASSWORD")
    if not username or not password:
        pytest.skip("ECUZDAN_E2E_USERNAME ve ECUZDAN_E2E_PASSWORD gerekli")

    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")
    page.locator("#username").fill(username)
    page.locator("input[name=password]").fill(password)
    page.locator("#login-submit-btn").click()
    page.locator(".user-dropdown-btn").wait_for(state="visible", timeout=15000)
    return page


@pytest.fixture
def phase4_request_headers(phase4_tenant_id):
    """Mock ve API contract testlerinde ortak tenant/request header'ları."""
    return {
        "Accept": "application/json",
        "X-E2E-Tenant": phase4_tenant_id,
        "X-Request-ID": "e2e-phase4-request",
    }
