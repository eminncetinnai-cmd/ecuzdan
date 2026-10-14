"""Browser contract checks for the plan recurrence form."""

import os

import pytest

BASE_URL = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
USERNAME = os.getenv('ECUZDAN_E2E_USERNAME')
PASSWORD = os.getenv('ECUZDAN_E2E_PASSWORD')

pytestmark = pytest.mark.e2e


def _login(page):
    if not USERNAME or not PASSWORD:
        pytest.skip('ECUZDAN_E2E_USERNAME and ECUZDAN_E2E_PASSWORD are required')
    page.goto(f'{BASE_URL}/login', wait_until='domcontentloaded')
    page.locator('#username').fill(USERNAME)
    page.locator('input[name=password]').fill(PASSWORD)
    page.locator('#login-submit-btn').click()
    page.locator('.user-dropdown-btn').wait_for(state='visible', timeout=15000)


def test_plan_form_exposes_date_and_frequency_contract(page):
    """The UI must expose every field used by the recurrence backend."""
    _login(page)
    response = page.goto(f'{BASE_URL}/plans', wait_until='domcontentloaded')
    assert response is not None and response.ok

    page.locator('button[onclick="openPlanModal()"]').click()
    assert page.locator('#plan_start_date').is_visible()
    assert page.locator('#plan_end_date').is_visible()
    assert page.locator('#plan_frequency').is_visible()
    assert page.locator('#plan_frequency option').count() == 4
    assert page.locator('#plan_start_date').evaluate(
        "element => element.parentElement.innerText.includes('İlk kayıt bu tarihten önce oluşturulmaz')"
    )


def test_plan_page_has_no_browser_errors(page):
    """The plans page and recurrence form should load without page errors."""
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    _login(page)
    response = page.goto(f'{BASE_URL}/plans', wait_until='domcontentloaded')
    assert response is not None and response.ok
    page.wait_for_timeout(500)
    assert errors == [], errors
