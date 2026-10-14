import os
import unicodedata

import pytest
from playwright.sync_api import Error as PlaywrightError

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")
USERNAME = os.getenv("ECUZDAN_E2E_USERNAME")
PASSWORD = os.getenv("ECUZDAN_E2E_PASSWORD")

pytestmark = pytest.mark.e2e


def _fold_text(value):
    normalized = unicodedata.normalize("NFKD", value.casefold())
    folded = "".join(char for char in normalized if not unicodedata.combining(char))
    return folded.replace("ı", "i")


def _login(page):
    if not USERNAME or not PASSWORD:
        pytest.skip("ECUZDAN_E2E_USERNAME and ECUZDAN_E2E_PASSWORD are required")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.locator("#username").fill(USERNAME)
    page.locator("input[name=password]").fill(PASSWORD)
    page.locator("#login-submit-btn").click()
    page.locator(".user-dropdown-btn").wait_for(state="visible", timeout=15000)


def _open_locale_panel(page):
    page.goto(f"{BASE_URL}/settings#locale", wait_until="domcontentloaded")
    page.locator("button[data-tab='locale']").click()
    page.locator("[data-panel='locale']").wait_for(state="visible")


@pytest.fixture(autouse=True)
def restore_default_language(page):
    yield
    if not USERNAME or not PASSWORD:
        return
    try:
        _open_locale_panel(page)
        turkish = page.locator("button[onclick=\"changeLang('tr')\"]")
        if turkish.count() and turkish.is_enabled():
            with page.expect_response("**/set_language/tr", timeout=15000):
                turkish.click()
            page.locator("button[role='tab']").first.wait_for(state="visible", timeout=15000)
    except PlaywrightError:
        # Teardown must not mask a completed assertion when the staging server is shutting down.
        pass


def test_language_switch_persists_after_reload(page):
    _login(page)
    _open_locale_panel(page)

    english = page.locator("button[onclick=\"changeLang('en')\"]")
    with page.expect_response("**/set_language/en") as response_info:
        english.click()
    response = response_info.value
    assert response.status == 200

    page.wait_for_load_state("domcontentloaded")
    assert page.locator("html").get_attribute("lang") == "en"
    assert "SYSTEM SETTINGS" in page.locator("h2").inner_text().upper()

    page.reload(wait_until="domcontentloaded")
    assert page.locator("html").get_attribute("lang") == "en"

    _open_locale_panel(page)
    assert "border-amber-500" in (page.locator("button[onclick=\"changeLang('en')\"]").get_attribute("class") or "")


def test_language_switch_can_return_to_turkish(page):
    _login(page)
    _open_locale_panel(page)
    turkish = page.locator("button[onclick=\"changeLang('tr')\"]")
    with page.expect_response("**/set_language/tr") as response_info:
        turkish.click()
    assert response_info.value.status == 200
    page.wait_for_load_state("domcontentloaded")
    assert page.locator("html").get_attribute("lang") == "tr"


@pytest.mark.parametrize("language", ["tr", "en", "it", "de"])
def test_each_supported_language_updates_html_locale(page, language):
    _login(page)
    _open_locale_panel(page)
    button = page.locator(f"button[onclick=\"changeLang('{language}')\"]")
    with page.expect_response(f"**/set_language/{language}") as response_info:
        button.click()
    assert response_info.value.status == 200
    page.wait_for_load_state("domcontentloaded")
    assert page.locator("html").get_attribute("lang") == language


@pytest.mark.parametrize(
    ("language", "tab_labels", "panel_labels"),
    [
        (
            "tr",
            ["Profil & Güvenlik", "Finansal Tercihler", "Dil & Görünüm", "Veri & Yedekleme", "Aile & Ortak Bütçe"],
            ["Hesap Bilgileri", "Ana Para Birimi", "Görünüm", "Yedekleme & Geri Yükleme", "Bütçe Paylaşımı"],
        ),
        (
            "en",
            ["Profile & Security", "Financial Preferences", "Language & Appearance", "Data & Backups", "Family & Shared Budget"],
            ["Account Information", "Base Currency", "Appearance", "Backup & Restore", "Budget Sharing"],
        ),
        (
            "it",
            ["Profilo e sicurezza", "Preferenze finanziarie", "Lingua e aspetto", "Dati e backup", "Famiglia e budget condiviso"],
            ["Informazioni account", "Valuta principale", "Aspetto", "Backup e ripristino", "Condivisione del budget"],
        ),
        (
            "de",
            ["Profil & Sicherheit", "Finanzielle Präferenzen", "Sprache & Darstellung", "Daten & Sicherungen", "Familie & gemeinsames Budget"],
            ["Kontoinformationen", "Basiswährung", "Darstellung", "Sichern & Wiederherstellen", "Budget teilen"],
        ),
    ],
)
def test_settings_sections_are_translated(page, language, tab_labels, panel_labels):
    _login(page)
    _open_locale_panel(page)
    button = page.locator(f"button[onclick=\"changeLang('{language}')\"]")
    with page.expect_response(f"**/set_language/{language}"):
        button.click()
    page.wait_for_load_state("domcontentloaded")
    page.locator("button[role='tab']").first.wait_for(state="visible", timeout=15000)

    tabs = page.locator("button[role='tab']")
    assert tabs.count() == 5
    for index, label in enumerate(tab_labels):
        assert _fold_text(label) in _fold_text(tabs.nth(index).inner_text())

    panel_selectors = [
        "[data-panel='profile']",
        "[data-panel='finance']",
        "[data-panel='locale']",
        "[data-panel='data']",
        "[data-panel='household']",
    ]
    for selector, label in zip(panel_selectors, panel_labels):
        panel = page.locator(selector)
        tab_name = selector.split("'")[1]
        page.locator(f"button[data-tab='{tab_name}']").click()
        assert _fold_text(label) in _fold_text(panel.inner_text())
