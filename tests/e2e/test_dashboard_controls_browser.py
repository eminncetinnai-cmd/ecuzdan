from __future__ import annotations

import os
import re

import pytest
from playwright.sync_api import expect

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5000")

pytestmark = pytest.mark.e2e


DASHBOARD_LOCALES = {
    "tr": {
        "today_cash": "Bugünkü Nakit",
        "trend": "7 Günlük Nakit Akış Trendi",
        "transactions": "İşlemlerim",
        "positive": "Pozitif",
        "negative": "Negatif",
        "intl": "tr-TR",
    },
    "en": {
        "today_cash": "Today's Cash",
        "trend": "7-Day Cash Flow Trend",
        "transactions": "My transactions",
        "positive": "Positive",
        "negative": "Negative",
        "intl": "en-US",
    },
    "de": {
        "today_cash": "Heutiges Bargeld",
        "trend": "7-Tage-Cashflow-Trend",
        "transactions": "Meine Transaktionen",
        "positive": "Positiv",
        "negative": "Negativ",
        "intl": "de-DE",
    },
    "it": {
        "today_cash": "Contanti di Oggi",
        "trend": "Andamento Flusso di Cassa 7 Giorni",
        "transactions": "Le mie transazioni",
        "positive": "Positivo",
        "negative": "Negativo",
        "intl": "it-IT",
    },
}


def _set_language(page, language: str) -> None:
    """Set an explicit locale through the supported settings UI."""
    page.goto(f"{BASE_URL}/settings#locale", wait_until="domcontentloaded")
    locale_tab = page.locator("button[data-tab='locale']")
    if locale_tab.count():
        locale_tab.click()
    if page.locator("html").get_attribute("lang") == language:
        return

    with page.expect_response(f"**/set_language/{language}") as response_info:
        page.locator(f"button[onclick=\"changeLang('{language}')\"]").click()
    assert response_info.value.status == 200
    page.wait_for_load_state("domcontentloaded")


def _restore_turkish(page) -> None:
    """Restore the user's pre-existing test language when the page is usable."""
    try:
        if page.locator("html").get_attribute("lang") != "tr":
            _set_language(page, "tr")
    except Exception:
        # Teardown must not hide the original browser assertion or a stopped app.
        pass


def _assert_in_viewport(page, selector: str) -> None:
    box = page.locator(selector).bounding_box()
    viewport = page.viewport_size
    assert box and viewport
    assert box["width"] > 0 and box["height"] > 0
    assert box["x"] >= 0
    assert box["y"] >= 0
    assert box["x"] + box["width"] <= viewport["width"] + 1
    assert box["y"] + box["height"] <= viewport["height"] + 1


def _open_dashboard(page) -> None:
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    page.locator("#weekChart").wait_for(state="visible", timeout=15000)
    page.locator("#monthChart").wait_for(state="visible", timeout=15000)


@pytest.mark.parametrize(
    "viewport",
    [(1440, 900), (390, 844)],
    ids=["desktop", "mobile"],
)
def test_dashboard_surface_controls_are_stable_without_writes(
    phase4_authenticated_page, viewport
):
    """Dashboard surface and reversible controls must stay within the viewport."""
    page = phase4_authenticated_page
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    console_errors: list[str] = []
    page_errors: list[str] = []
    non_get_requests: list[str] = []
    http_errors: list[tuple[int, str]] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on(
        "response",
        lambda response: http_errors.append((response.status, response.url))
        if response.status >= 400
        else None,
    )
    _set_language(page, "tr")
    page.on(
        "request",
        lambda request: non_get_requests.append(
            f"{request.method} {request.url}"
        )
        if request.method not in {"GET", "HEAD"}
        else None,
    )
    _open_dashboard(page)

    primary_labels = [
        "Bugünkü Nakit",
        "7 Günlük Tahmin",
        "Ay Sonu Tahmin",
        "Yıl Sonu Kasa",
    ]
    secondary_labels = [
        "Yıl içi gerçekleşen nakit",
        "Ödenmiş yatırım transferi",
        "Yatırım / Gelir Oranı",
        "Bekleyen yıl etkisi",
    ]
    for label in primary_labels + secondary_labels:
        expect(page.get_by_text(re.compile(re.escape(label), re.IGNORECASE)).first).to_be_visible()

    expect(page.locator("#weekChart")).to_be_visible()
    expect(page.locator("#monthChart")).to_be_visible()
    asset_chart = page.locator("#assetDistChart")
    assert asset_chart.count() in {0, 1}
    if asset_chart.count() == 1:
        expect(asset_chart).to_be_visible()

    all_transactions_link = page.locator("a[href='/transactions']").filter(
        has_text=re.compile(r"Tüm İşlemleri Gör", re.IGNORECASE)
    )
    expect(all_transactions_link).to_have_count(1)
    expect(all_transactions_link).to_be_visible()

    quick_button = page.locator(".quick-actions-btn")
    expect(quick_button).to_be_visible()
    quick_button.click()
    quick_panel = page.locator("#quickActionsPanel")
    expect(quick_panel).to_be_visible()
    quick_links = quick_panel.locator("a")
    expect(quick_links).to_have_count(3)
    expect(quick_links.nth(0)).to_have_attribute(
        "onclick", re.compile(r"openGlobalQuickTxModal")
    )
    expect(quick_links.nth(1)).to_have_attribute("href", "/plans")
    expect(quick_links.nth(2)).to_have_attribute("href", "/assets")
    quick_button.click()
    expect(quick_panel).to_be_hidden()

    calculator_button = page.locator(".calculator-btn")
    expect(calculator_button).to_be_visible()
    calculator_button.click()
    calculator = page.locator("#calculatorModal")
    expect(calculator).to_be_visible()
    expect(calculator.locator("#calculatorDisplay")).to_have_text("0")
    calculator.locator("button[onclick='closeCalculator()']").click()
    expect(calculator).to_be_hidden()

    for selector in [
        ".quick-actions-btn",
        ".calculator-btn",
        "#privacyToggle",
        ".user-dropdown-btn",
    ]:
        _assert_in_viewport(page, selector)

    no_horizontal_overflow = page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
    )
    assert no_horizontal_overflow
    expected_rate_limited = [
        (status, url)
        for status, url in http_errors
        if status == 429 and url.rstrip("/").endswith("/notifications/unread_count")
    ]
    unexpected_http_errors = [item for item in http_errors if item not in expected_rate_limited]
    assert not unexpected_http_errors, unexpected_http_errors
    unexpected_console_errors = [
        message
        for message in console_errors
        if "429 (TOO MANY REQUESTS)" not in message
    ]
    assert not unexpected_console_errors, unexpected_console_errors
    assert not page_errors, page_errors
    assert not non_get_requests, non_get_requests


def test_dashboard_privacy_toggle_is_reversible(phase4_authenticated_page):
    """Privacy mode may be toggled for QA only when its initial state is restored."""
    page = phase4_authenticated_page
    page.set_viewport_size({"width": 1440, "height": 900})
    console_errors: list[str] = []
    page_errors: list[str] = []
    http_errors: list[tuple[int, str]] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on(
        "response",
        lambda response: http_errors.append((response.status, response.url))
        if response.status >= 400
        else None,
    )
    _set_language(page, "tr")
    _open_dashboard(page)

    initial_privacy = page.locator("html").evaluate(
        "element => element.classList.contains('privacy')"
    )
    toggle = page.locator("#privacyToggle")
    expect(toggle).to_be_visible()

    def toggle_privacy():
        current_privacy = page.locator("html").evaluate(
            "element => element.classList.contains('privacy')"
        )
        expected_privacy = not current_privacy
        with page.expect_response(
            lambda response: response.request.method == "POST"
            and "privacy" in response.url
        ) as response_info:
            toggle.click()
        assert response_info.value.status == 200
        page.wait_for_function(
            "expected => document.documentElement.classList.contains('privacy') === expected",
            arg=expected_privacy,
        )

    try:
        toggle_privacy()
        assert page.locator("html").evaluate(
            "element => element.classList.contains('privacy')"
        ) is (not initial_privacy)
        toggle_privacy()
        assert page.locator("html").evaluate(
            "element => element.classList.contains('privacy')"
        ) is initial_privacy
    finally:
        current_privacy = page.locator("html").evaluate(
            "element => element.classList.contains('privacy')"
        )
        if current_privacy != initial_privacy:
            toggle_privacy()
        _restore_turkish(page)

    expected_rate_limited = [
        (status, url)
        for status, url in http_errors
        if status == 429 and url.rstrip("/").endswith("/notifications/unread_count")
    ]
    unexpected_http_errors = [item for item in http_errors if item not in expected_rate_limited]
    assert not unexpected_http_errors, unexpected_http_errors
    unexpected_console_errors = [
        message
        for message in console_errors
        if "429 (TOO MANY REQUESTS)" not in message
    ]
    assert not unexpected_console_errors, unexpected_console_errors
    assert not page_errors, page_errors


@pytest.mark.parametrize("language", ["tr", "en", "de", "it"])
def test_dashboard_core_labels_and_chart_locale(
    phase4_authenticated_page, language
):
    """Core dashboard labels and JS money locale follow the selected language."""
    page = phase4_authenticated_page
    page.set_viewport_size({"width": 1440, "height": 900})
    expected = DASHBOARD_LOCALES[language]
    try:
        _set_language(page, language)
        _open_dashboard(page)

        expect(page.locator("html")).to_have_attribute("lang", language)
        for label in (
            expected["today_cash"],
            expected["trend"],
            expected["transactions"],
            expected["positive"],
            expected["negative"],
        ):
            expect(
                page.get_by_text(re.compile(re.escape(label), re.IGNORECASE)).first
            ).to_be_visible()

        body_text = page.locator("body").inner_text()
        assert "dashboard_today_cash" not in body_text
        assert "dashboard_trend_title" not in body_text
        assert "dashboard_tx_title" not in body_text
        assert page.evaluate(
            "() => typeof dashboardIntlLocale !== 'undefined' ? dashboardIntlLocale : null"
        ) == expected["intl"]
    finally:
        _restore_turkish(page)
