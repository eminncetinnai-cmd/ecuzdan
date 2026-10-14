from __future__ import annotations

import os

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_reconciliation_workspace_is_standalone_and_explains_variance(phase4_authenticated_page):
    """Mutabakat ayrı bir çalışma kağıdı ve salt bakiye kartı olmamalıdır."""
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
    page = phase4_authenticated_page
    page.goto(f"{base_url}/reconciliation", wait_until="networkidle")

    panel = page.locator("#reconciliationPanel")
    expect(panel).to_be_visible()
    expect(page.locator("#reconciliationAccountSelect")).to_be_visible()
    expect(page.locator("#reconciliationAsOf")).to_be_visible()
    expect(page.locator("#reconciliationStatementBalance")).to_be_visible()
    expect(page.locator("#saveReconciliationStatement")).to_be_visible()
    expect(page.locator('[data-reconciliation="book_balance"]')).to_be_visible()
    expect(page.locator('[data-reconciliation="pending_count"]')).to_be_visible()
    expect(page.locator("#reconciliationPendingBody")).to_be_visible()
    expect(page.locator("#reconciliationIssueList")).to_be_visible()

    page.locator("#reconciliationStatementBalance").fill("0")
    page.locator("#runReconciliation").click()
    expect(page.locator("#reconciliationStatus")).not_to_have_text("Hesaplanıyor…", timeout=10000)
    expect(page.locator("#reconciliationPendingMeta")).not_to_have_text("")

    page.goto(f"{base_url}/transactions", wait_until="networkidle")
    expect(page.locator("#reconciliationPanel")).to_have_count(0)


def test_reconciliation_is_last_item_in_general_overview_navigation(phase4_authenticated_page):
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
    page = phase4_authenticated_page
    page.goto(f"{base_url}/settings#locale", wait_until="domcontentloaded")
    if page.locator('html').get_attribute('lang') != 'tr':
        with page.expect_response('**/set_language/tr') as response_info:
            page.locator("button[onclick=\"changeLang('tr')\"]").click()
        assert response_info.value.status == 200
        page.wait_for_load_state('domcontentloaded')
    page.goto(f"{base_url}/reconciliation", wait_until="networkidle")

    overview_links = page.locator("#overview-section .nav-link")
    expect(overview_links.last).to_have_attribute("href", "/reconciliation")
    expect(overview_links.last).to_contain_text("Mutabakat")


def test_reconciliation_is_mobile_usable(phase4_authenticated_page):
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
    page = phase4_authenticated_page
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base_url}/reconciliation", wait_until="networkidle")

    expect(page.locator("#reconciliationPage h1")).to_be_visible()
    expect(page.locator("#reconciliationAccountSelect")).to_be_visible()
    expect(page.locator("#reconciliationPendingSection")).to_be_visible()
