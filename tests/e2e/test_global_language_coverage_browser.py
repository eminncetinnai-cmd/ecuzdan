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


EXPECTED = {
    "tr": {
        "logbook": "Cüzdan Defteri",
        "profile": "Yatırımcı Profili",
        "notifications": "Bildirimler",
        "settings": "Ayarlar",
        "guide": "E-Cüzdan Kullanım Kılavuzu",
        "strategy": "Fon Laboratuvarı",
        "education": "Finansal Okuryazarlık Öğrenme Rehberi",
        "nav_guide": "Kullanım Kılavuzu",
        "nav_education": "Finansal Eğitim",
        "toc": "İçindekiler",
        "quiz_start": "Quizi Başlat",
    },
    "en": {
        "logbook": "Financial Logbook",
        "profile": "Investor Profile",
        "notifications": "Notifications",
        "settings": "Settings",
        "guide": "E-Wallet User Guide",
        "strategy": "Fund Laboratory",
        "education": "Financial Literacy Learning Guide",
        "nav_guide": "User Guide",
        "nav_education": "Financial Education",
        "toc": "Table of Contents",
        "quiz_start": "Start Quiz",
    },
    "de": {
        "logbook": "Finanz-Tagebuch",
        "profile": "Anlegerprofil",
        "notifications": "Benachrichtigungen",
        "settings": "Einstellungen",
        "guide": "E-Wallet Benutzerhandbuch",
        "strategy": "Fondslabor",
        "education": "Finanzielle Alphabetisierung Lernleitfaden",
        "nav_guide": "Benutzerhandbuch",
        "nav_education": "Finanzbildung",
        "toc": "Inhaltsverzeichnis",
        "quiz_start": "Quiz starten",
    },
    "it": {
        "logbook": "Diario finanziario",
        "profile": "Profilo investitore",
        "notifications": "Notifiche",
        "settings": "Impostazioni",
        "guide": "Guida Utente E-Wallet",
        "strategy": "Laboratorio Fondi",
        "education": "Guida all'Alfabetizzazione Finanziaria",
        "nav_guide": "Manuale utente",
        "nav_education": "Educazione finanziaria",
        "toc": "Indice",
        "quiz_start": "Inizia quiz",
    },
}


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


def _set_language(page, language):
    _open_locale_panel(page)
    if page.locator("html").get_attribute("lang") == language:
        return
    button = page.locator(f"button[onclick=\"changeLang('{language}')\"]")
    with page.expect_response(f"**/set_language/{language}") as response_info:
        button.click()
    assert response_info.value.status == 200
    page.wait_for_load_state("domcontentloaded")
    assert page.locator("html").get_attribute("lang") == language


@pytest.fixture(autouse=True)
def restore_default_language(page):
    yield
    if not USERNAME or not PASSWORD:
        return
    try:
        _set_language(page, "tr")
    except PlaywrightError:
        pass


@pytest.mark.parametrize("language", ["tr", "en", "de", "it"])
def test_global_navigation_and_page_contents_follow_language(page, language):
    _login(page)
    _set_language(page, language)
    expected = EXPECTED[language]

    routes = [
        ("/logbook", ".logbook-title", expected["logbook"]),
        ("/profile", ".page-header h1", expected["profile"]),
        ("/notifications", ".page-title", expected["notifications"]),
        ("/settings", ".max-w-5xl h2", expected["settings"]),
        ("/user_guide", ".section-header h1", expected["guide"]),
        ("/financial_education?view=quiz", ".max-w-7xl > div:first-child h1", expected["education"]),
    ]

    for route, selector, page_label in routes:
        page.goto(f"{BASE_URL}{route}", wait_until="domcontentloaded")
        assert page.locator("html").get_attribute("lang") == language
        assert _fold_text(page_label) in _fold_text(page.locator(selector).first.inner_text().strip())

    page.goto(f"{BASE_URL}/user_guide", wait_until="domcontentloaded")
    assert _fold_text(expected["toc"]) in _fold_text(page.locator("body").inner_text())

    page.goto(f"{BASE_URL}/financial_education?view=quiz", wait_until="domcontentloaded")
    assert page.get_by_text(expected["quiz_start"], exact=True).count() >= 1

    body = page.locator("body").text_content() or ""
    folded_body = _fold_text(body)
    for menu_label in (expected["logbook"], expected["profile"], expected["notifications"], expected["settings"], expected["nav_guide"], expected["nav_education"]):
        assert _fold_text(menu_label) in folded_body
