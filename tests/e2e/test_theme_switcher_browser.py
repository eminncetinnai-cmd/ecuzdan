"""Browser regression coverage for the premium theme switcher."""

import os

import pytest
from playwright.sync_api import expect

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


def _open_theme_control(page):
    page.locator(".user-dropdown-btn").click()
    toggle = page.locator("[data-theme-toggle]")
    expect(toggle).to_be_visible()
    return toggle


def test_theme_switcher_has_visible_premium_state(page):
    _login(page)
    page.set_viewport_size({"width": 1440, "height": 1000})
    toggle = _open_theme_control(page)
    assert toggle.get_attribute("aria-label") in {"Koyu temaya geç", "Açık temaya geç"}
    assert toggle.locator(".theme-toggle-icon-wrap").is_visible()
    assert toggle.locator(".theme-toggle-state").is_visible()
    background = toggle.evaluate("element => getComputedStyle(element).backgroundImage")
    assert "gradient" in background
    border = toggle.evaluate("element => getComputedStyle(element).borderTopColor")
    assert border not in {"rgba(0, 0, 0, 0)", "transparent"}


def test_theme_switcher_toggles_dark_mode_and_restores_preference(page):
    _login(page)
    toggle = _open_theme_control(page)
    initial_theme = page.locator("html").get_attribute("data-user-theme") or "light"
    target_theme = "dark" if initial_theme == "light" else "light"
    try:
        toggle.click()
        page.wait_for_function("theme => document.documentElement.dataset.userTheme === theme", arg=target_theme)
        assert page.locator("html").get_attribute("data-user-theme") == target_theme
        assert page.locator("html").evaluate("element => element.classList.contains('dark')") is (target_theme == "dark")
        assert page.evaluate("window.localStorage.getItem('theme')") == target_theme
        assert toggle.get_attribute("aria-pressed") == str(target_theme == "dark").lower()
        assert toggle.get_attribute("aria-label") in {"Koyu temaya geç", "Açık temaya geç"}
    finally:
        page.evaluate("theme => window.ECuzdanUI.setTheme(theme)", initial_theme)


def test_theme_switcher_fits_mobile_header(page):
    _login(page)
    page.set_viewport_size({"width": 390, "height": 844})
    toggle = _open_theme_control(page)
    assert toggle.locator(".theme-toggle-icon-wrap").is_visible()
    assert toggle.evaluate("element => element.getBoundingClientRect().width") >= 32
    assert toggle.evaluate("element => getComputedStyle(element.querySelector('.theme-toggle-state')).display") == "none"


def test_dashboard_chart_surface_tracks_theme(page):
    _login(page)
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    page.locator("#weekChart").wait_for(state="visible", timeout=15000)
    toggle = _open_theme_control(page)
    initial_theme = page.locator("html").get_attribute("data-user-theme") or "light"
    target_theme = "dark" if initial_theme == "light" else "light"
    try:
        toggle.click()
        page.wait_for_function("theme => document.documentElement.dataset.userTheme === theme", arg=target_theme)
        page.wait_for_timeout(450)
        chart_surface = page.locator(".chart-container").first.evaluate("element => getComputedStyle(element).backgroundColor")
        body_background = page.locator("body").evaluate("element => getComputedStyle(element).backgroundImage")
        assert chart_surface not in {"rgba(0, 0, 0, 0)", "transparent"}
        assert "gradient" in body_background
        if target_theme == "dark":
            assert "20, 34, 56" in chart_surface or "16, 28, 48" in chart_surface
    finally:
        page.evaluate("theme => window.ECuzdanUI.setTheme(theme)", initial_theme)


def _restore_theme(page, theme):
    page.evaluate("theme => window.ECuzdanUI.setTheme(theme)", theme)
    page.wait_for_function("theme => document.documentElement.dataset.userTheme === theme", arg=theme)


def test_theme_transition_animation_budget(page):
    _login(page)
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    page.locator("#weekChart").wait_for(state="visible", timeout=15000)
    toggle = _open_theme_control(page)
    initial_theme = page.locator("html").get_attribute("data-user-theme") or "light"
    target_theme = "dark" if initial_theme == "light" else "light"
    try:
        toggle.click()
        css_duration = page.locator("html").evaluate("element => parseFloat(getComputedStyle(element).transitionDuration) * 1000")
        page.wait_for_function("theme => document.documentElement.dataset.userTheme === theme", arg=target_theme)
        page.evaluate(
            """() => {
                const state = { started: performance.now(), frames: 0, maxFrameGap: 0, last: performance.now(), ended: false };
                window.__themeTransitionPerf = state;
                const deadline = state.started + 450;
                const sample = now => {
                    state.frames += 1;
                    state.maxFrameGap = Math.max(state.maxFrameGap, now - state.last);
                    state.last = now;
                    if (now < deadline) {
                        requestAnimationFrame(sample);
                    } else {
                        state.ended = true;
                        state.endedAt = now;
                    }
                };
                requestAnimationFrame(sample);
            }"""
        )
        page.wait_for_function(
            "() => window.__themeTransitionPerf && window.__themeTransitionPerf.ended === true",
            timeout=1500,
        )
        perf = page.evaluate("window.__themeTransitionPerf")
        assert perf and perf["ended"] is True
        duration = perf["endedAt"] - perf["started"]
        assert 0 < duration <= 650
        assert 0 < css_duration <= 400
        assert perf["frames"] >= 4
        assert perf["maxFrameGap"] < 160
    finally:
        _restore_theme(page, initial_theme)


def test_theme_transition_respects_reduced_motion(page):
    _login(page)
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    page.locator("#weekChart").wait_for(state="visible", timeout=15000)
    toggle = _open_theme_control(page)
    initial_theme = page.locator("html").get_attribute("data-user-theme") or "light"
    target_theme = "dark" if initial_theme == "light" else "light"
    page.emulate_media(reduced_motion="reduce")
    try:
        toggle.click()
        page.wait_for_function("theme => document.documentElement.dataset.userTheme === theme", arg=target_theme)
        motion = page.evaluate(
            """() => ({
                htmlTransition: getComputedStyle(document.documentElement).transitionDuration,
                bodyTransition: getComputedStyle(document.body).transitionDuration,
                toggleTransition: getComputedStyle(document.querySelector('[data-theme-toggle]')).transitionDuration
            })"""
        )
        assert motion["htmlTransition"] in {"0s", "0ms"}
        assert motion["bodyTransition"] in {"0s", "0ms"}
        assert motion["toggleTransition"] in {"0s", "0ms"}
    finally:
        page.emulate_media(reduced_motion=None)
        _restore_theme(page, initial_theme)


def test_theme_browser_css_capabilities(page):
    _login(page)
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    page.locator(".user-dropdown-btn").wait_for(state="visible", timeout=15000)
    capabilities = page.evaluate(
        """() => ({
            customProperties: CSS.supports('color', 'var(--theme-toggle-text)'),
            transitions: CSS.supports('transition', 'background-color 280ms ease'),
            colorMix: CSS.supports('color', 'color-mix(in srgb, white 50%, black)'),
            backdropFilter: CSS.supports('backdrop-filter', 'blur(1px)') || CSS.supports('-webkit-backdrop-filter', 'blur(1px)'),
            prefersReducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
            themeState: document.documentElement.getAttribute('data-user-theme')
        })"""
    )
    assert capabilities["customProperties"] is True
    assert capabilities["transitions"] is True
    assert capabilities["themeState"] in {"light", "dark"}
