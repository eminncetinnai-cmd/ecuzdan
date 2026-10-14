"""Browser checks for the unified Plans information architecture."""

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


def _rows(page, panel='#tab-all'):
    return [
        text.strip()
        for text in page.locator(f'{panel} tbody tr[data-plan-row]').all_inner_texts()
    ]


def test_unified_plan_views_show_all_and_investment_panels(page):
    _login(page)
    response = page.goto(f'{BASE_URL}/plans', wait_until='networkidle')
    assert response is not None and response.ok

    assert page.locator('#tab-all').is_visible()
    assert page.locator('#tab-investment').count() == 1
    assert page.locator('#plan-search').is_visible()
    assert page.locator('#plan-flow').is_visible()
    assert page.locator('#plan-lifecycle').is_visible()
    assert page.locator('#plan-status').is_visible()
    assert page.locator('button.plan-btn-primary').count() >= 1
    assert page.locator('#tab-all .plan-desktop-table').is_visible()
    assert page.locator('#tab-all thead tr th').count() == 6
    assert page.locator('#planDetailDrawer').count() == 1
    all_rows = _rows(page)
    assert all_rows or page.locator('#tab-all tbody').count() == 1
    if all_rows:
        assert page.locator('#tab-all .plan-table-action').count() == len(all_rows) * 4
        first_detail = page.locator('#tab-all .plan-table-action.detail:visible').first
        first_detail.click()
        page.locator('#planDetailDrawer').wait_for(state='visible')
        assert page.locator('#planDetailContent').inner_text().strip()
        assert page.locator('#planDetailTitle').inner_text().strip()
        page.locator('#planDetailClose').click()
        page.locator('#planDetailDrawer').wait_for(state='hidden')
    else:
        assert page.locator('#tab-all tbody td[colspan="6"] .plan-btn-primary').count() == 1
        assert page.locator('#planDetailDrawer').is_hidden()

    page.locator('button[onclick*="tab-investment"]').click()
    assert page.locator('#tab-investment').is_visible()

    page.set_viewport_size({'width': 390, 'height': 844})
    page.reload(wait_until='networkidle')
    assert page.locator('[data-plan-card]').count() == len(all_rows)
    assert page.locator('.plan-btn').count() >= 1
    assert page.locator('.plan-desktop-table').evaluate_all(
        "elements => elements.every(element => getComputedStyle(element).display === 'none')"
    )


def test_dca_mode_exposes_target_asset_selector(page):
    _login(page)
    page.goto(f'{BASE_URL}/plans', wait_until='networkidle')
    page.locator('button[onclick="openPlanModal()"]').click()
    page.locator('#flow_type_selector').select_option('Yatırım')
    page.locator('#plan_type').select_option('DCA')
    assert page.locator('#target_asset_wrapper').is_visible()
    assert page.locator('#target_asset_id').get_attribute('required') == ''


def test_unified_plan_flow_and_search_filters_are_server_backed(page):
    _login(page)
    page.goto(f'{BASE_URL}/plans?flow=Gelir', wait_until='networkidle')

    assert page.locator('#plan-flow').input_value() == 'Gelir'
    rows = _rows(page)
    assert all('gelir' in row.casefold() for row in rows)

    page.goto(f'{BASE_URL}/plans?q=Maa%C5%9F', wait_until='networkidle')
    assert page.locator('#plan-search').input_value() == 'Maaş'
    rows = _rows(page)
    assert all('maaş' in row.casefold() for row in rows)
