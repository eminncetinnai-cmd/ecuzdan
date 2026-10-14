from __future__ import annotations

import os

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_standard_category_allows_budget_only_editing(phase4_authenticated_page):
    """Standart kategori UI'sı çekirdek alanları koruyup bütçeyi açık bırakmalıdır."""
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
    page = phase4_authenticated_page
    page.goto(f"{base_url}/categories", wait_until="networkidle")

    standard_row = page.locator('tr.cat-row[data-standard="true"]').first
    expect(standard_row).to_be_visible()
    standard_row.locator("button").first.click()

    expect(page.locator("#cat_name")).to_have_attribute("readonly", "")
    expect(page.locator("#cat_code")).to_have_attribute("readonly", "")
    expect(page.locator('input[name="type"][type="radio"]').first).to_be_disabled()
    expect(page.locator("#cat_budget_limit")).to_be_enabled()
    expect(page.locator("#cat_submit_btn")).to_have_text("AYLIK BÜTÇEYİ KAYDET")
    expect(page.locator("#cat_edit_hint")).to_contain_text("yalnızca aylık bütçe")
