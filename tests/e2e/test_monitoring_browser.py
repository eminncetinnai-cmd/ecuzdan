"""End-to-end browser coverage for the monitoring control center."""
import os
from pathlib import Path

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

    response = page.goto(f"{BASE_URL}/monitoring/", wait_until="domcontentloaded")
    assert response is not None and response.ok
    assert "/monitoring" in page.url

def test_monitoring_requires_authentication(page):
    response = page.goto(f"{BASE_URL}/monitoring/", wait_until="domcontentloaded")
    assert response is not None
    assert "/login" in page.url

def test_monitoring_dashboard_renders_core_regions(page):
    _login(page)
    assert page.locator("#health-status").is_visible()
    assert page.locator("#total-logs").is_visible()
    assert page.locator("#log-container").is_visible()
    assert page.locator("#log-upload-dropzone").is_visible()
    assert page.locator("#live-stream-status").is_visible()
    assert page.locator("#log-search-input").is_visible()

def test_monitoring_filters_are_interactive(page):
    _login(page)
    page.locator("#log-search-input").fill("ERROR")
    page.locator("#log-level-select").select_option("ERROR")
    page.locator("#log-lines-input").fill("50")
    page.locator("#load-logs-btn").click()
    assert page.locator("#log-search-input").input_value() == "ERROR"
    assert page.locator("#log-level-select").input_value() == "ERROR"

def test_monitoring_sse_connection_status(page):
    _login(page)
    page.wait_for_function("""() => { const s = document.querySelector('#live-stream-status'); return s && ['connected','reconnecting','error'].includes(s.dataset.state); }""", timeout=15000)
    state = page.locator("#live-stream-status").get_attribute("data-state")
    assert state in {"connected", "reconnecting", "error"}

def test_monitoring_upload_rejects_unsupported_file(page, tmp_path: Path):
    _login(page)
    bad_file = tmp_path / "payload.exe"
    bad_file.write_bytes(b"MZ")
    page.locator("#log-upload-input").set_input_files(str(bad_file))
    assert page.locator("#log-upload-submit").is_disabled()
    assert page.locator("#log-upload-status").inner_text() != ""

def test_monitoring_responsive_layout(page):
    _login(page)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.locator("#log-container").is_visible()
    assert page.locator("#log-upload-dropzone").is_visible()
    page.set_viewport_size({"width": 1440, "height": 1000})
    assert page.locator("#log-container").is_visible()

def test_monitoring_console_has_no_page_errors(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    _login(page)
    page.wait_for_timeout(1500)
    assert errors == [], errors

def test_monitoring_visual_contract(page):
    _login(page)
    assert page.locator(".stat-card").count() >= 4
    assert page.locator(".collapsible-section").count() >= 3
    assert page.locator(".monitor-upload-card").is_visible()
    assert page.locator(".log-container").evaluate("element => getComputedStyle(element).overflowY") == "auto"
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_monitoring_api_payloads_and_rendered_values(page):
    _login(page)
    page.wait_for_function("""() => document.querySelector('#total-logs')?.textContent.trim() !== '-'""", timeout=15000)

    payloads = page.evaluate("""async () => {
        const endpoints = window.ECuzdanEndpoints.monitoring;
        const paths = [endpoints.stats, endpoints.health, endpoints.logsTimeline];
        const responses = await Promise.all(paths.map(path => fetch(path, {credentials: 'same-origin'}).then(response => response.json())));
        return {stats: responses[0], health: responses[1], timeline: responses[2]};
    }""")

    stats = payloads['stats']['data']
    health = payloads['health']['data']
    timeline = payloads['timeline']['data']
    assert payloads['stats']['success'] is True
    assert set(stats['log_files']) == {'main', 'structured', 'errors', 'errors_structured', 'security'}
    assert isinstance(stats['recent_errors'], list)
    assert health['status'] in {'healthy', 'degraded', 'critical'}
    assert {'database', 'logs', 'disk_space'} <= set(health['components'])
    assert isinstance(timeline['points'], list)
    assert page.locator('#total-logs').inner_text() != '-'
    assert page.locator('#log-files-info').inner_text() != ''


def test_monitoring_log_filter_renders_only_requested_level(page):
    _login(page)
    page.locator('#log-level-select').select_option('ERROR')
    page.locator('#load-logs-btn').click()
    page.wait_for_timeout(500)
    levels = page.locator('#log-container .log-entry').evaluate_all("elements => elements.map(element => element.dataset.level)")
    assert all(level == 'ERROR' for level in levels)


def test_monitoring_time_preset_sends_since_filter(page):
    _login(page)
    with page.expect_request(
        lambda request: '/monitoring/api/logs?' in request.url and 'since=' in request.url
    ) as request_info:
        page.locator('#log-preset-select').select_option('last_24h')
    assert 'since=' in request_info.value.url
