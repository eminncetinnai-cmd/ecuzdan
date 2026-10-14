import os

import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
USERNAME = os.getenv("ECUZDAN_E2E_USERNAME")
PASSWORD = os.getenv("ECUZDAN_E2E_PASSWORD")

pytestmark = pytest.mark.e2e


def _login(page):
    if not USERNAME or not PASSWORD:
        pytest.skip("ECUZDAN_E2E_USERNAME and ECUZDAN_E2E_PASSWORD are required")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.locator("#username").fill(USERNAME)
    page.locator("input[name=password]").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    page.locator(".user-dropdown-btn").wait_for(state="visible", timeout=15000)


def test_privileged_user_sees_capability_gated_settings(page):
    if os.getenv("ECUZDAN_E2E_EXPECT_PRIVILEGED") != "1":
        pytest.skip("Dedicated privileged staging entitlement is required; test will not upgrade or mutate a live user")
    _login(page)
    response = page.goto(f"{BASE_URL}/settings", wait_until="domcontentloaded")
    assert response is not None and response.ok

    page.locator('[role="tab"][data-tab="data"]').click()
    page.locator('[data-panel="data"]').wait_for(state="visible")

    assert page.get_by_text("3 Yıllık Veri Gir", exact=True).is_visible()
    assert page.get_by_text("Tam Yedek İndir", exact=True).is_visible()
    assert page.get_by_text("Yedek Yükle", exact=True).is_visible()
    assert page.locator('a[href="/monitoring"]').is_visible()


def test_privileged_user_can_open_monitoring_from_navigation(page):
    _login(page)
    page.goto(f"{BASE_URL}/settings", wait_until="domcontentloaded")
    page.locator('a[href="/monitoring"]').click()
    page.locator("#health-status").wait_for(state="visible", timeout=15000)
    assert "/monitoring" in page.url
