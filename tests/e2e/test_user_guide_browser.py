"""Browser acceptance tests for the localized user guide."""

from __future__ import annotations

import os

import pytest
from playwright.sync_api import expect

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")

pytestmark = pytest.mark.e2e

LANGUAGE_CASES = {
    "tr": {"title": "Önerilen Finansal İş Akışı", "search": "mutabakat", "section": "controls"},
    "en": {"title": "Recommended Financial Workflow", "search": "reconciliation", "section": "controls"},
    "de": {"title": "Empfohlener Finanzablauf", "search": "Abstimmung", "section": "controls"},
    "it": {"title": "Flusso finanziario consigliato", "search": "riconciliazione", "section": "controls"},
}


def _set_language(page, language: str) -> None:
    page.goto(f"{BASE_URL}/settings#locale", wait_until="domcontentloaded")
    page.locator("button[data-tab='locale']").click()
    page.locator("[data-panel='locale']").wait_for(state="visible")
    button = page.locator(f"button[onclick=\"changeLang('{language}')\"]")
    with page.expect_response(f"**/set_language/{language}") as response_info:
        button.click()
    assert response_info.value.status == 200
    page.wait_for_load_state("domcontentloaded")


def test_user_guide_is_localized_searchable_and_free_of_raw_keys(phase4_authenticated_page):
    """The guide follows the selected locale and its search filters translated sections."""
    page = phase4_authenticated_page

    for language, case in LANGUAGE_CASES.items():
        _set_language(page, language)
        page.goto(f"{BASE_URL}/user_guide", wait_until="domcontentloaded")

        expect(page.locator("html")).to_have_attribute("lang", language)
        expect(page.locator("#guideContent")).to_be_visible()
        expect(page.get_by_text(case["title"], exact=True)).to_be_visible()
        expect(page.locator("#guideSearch")).to_be_visible()

        body_text = page.locator("body").inner_text()
        assert "ug2_" not in body_text

        search = page.locator("#guideSearch")
        search.fill(case["search"])
        expect(page.locator(f"#{case['section']}")).to_be_visible()
        expect(page.locator("#guideNoResults")).to_be_hidden()

        search.fill("__no_guide_match__")
        expect(page.locator("#guideNoResults")).to_be_visible()

    _set_language(page, "tr")


def test_language_defaults_to_turkish_and_survives_fresh_login(phase4_authenticated_page):
    """Anonymous entry defaults to Turkish and an explicit choice survives relogin."""
    page = phase4_authenticated_page
    username = os.getenv('ECUZDAN_E2E_USERNAME')
    password = os.getenv('ECUZDAN_E2E_PASSWORD')
    assert username and password, 'E2E credentials must be supplied through process environment'

    _set_language(page, 'tr')
    page.goto(f'{BASE_URL}/logout', wait_until='domcontentloaded')
    expect(page.locator('html')).to_have_attribute('lang', 'tr')

    page.locator('#username').fill(username)
    page.locator('#password').fill(password)
    page.locator('#login-submit-btn').click()
    page.wait_for_url(f'{BASE_URL}/**', wait_until='domcontentloaded')
    page.goto(f'{BASE_URL}/settings', wait_until='domcontentloaded')
    expect(page.locator('html')).to_have_attribute('lang', 'tr')
