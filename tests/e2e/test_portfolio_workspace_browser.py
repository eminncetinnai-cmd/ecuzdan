from __future__ import annotations

import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
USERNAME = os.getenv("ECUZDAN_E2E_USERNAME")
PASSWORD = os.getenv("ECUZDAN_E2E_PASSWORD")

pytestmark = pytest.mark.e2e


def _login(page):
    if not USERNAME or not PASSWORD:
        pytest.skip("ECUZDAN_E2E_USERNAME ve ECUZDAN_E2E_PASSWORD gerekli")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.locator("#username").fill(USERNAME)
    page.locator("input[name=password]").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    page.locator(".user-dropdown-btn").wait_for(state="visible", timeout=15000)


def test_portfolio_views_share_workspace_toolbar(page):
    _login(page)

    for path in ("/assets_view", "/investment_performance"):
        page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
        toolbar = page.locator("#market-workspace-toolbar")
        assert toolbar.is_visible()
        portfolio_link = toolbar.locator("[data-workspace-view='portfolio']")
        assert portfolio_link.is_visible()
        assert portfolio_link.get_attribute("aria-current") == "page"
        assert toolbar.locator("[data-density='comfortable']").is_visible()
        assert toolbar.locator("[data-density='compact']").is_visible()
