import os
import re

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_transactions_uses_page_title_and_contextual_create_title(phase4_authenticated_page):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    page.goto(f'{base_url}/settings#locale', wait_until='domcontentloaded')
    if page.locator('html').get_attribute('lang') != 'tr':
        with page.expect_response('**/set_language/tr') as response_info:
            page.locator("button[onclick=\"changeLang('tr')\"]").click()
        assert response_info.value.status == 200
        page.wait_for_load_state('domcontentloaded')
    page.goto(f'{base_url}/transactions', wait_until='networkidle')

    expect(page).to_have_title(re.compile(r'İşlemler\s*\|'))
    page_heading = page.locator('#main-content h1')
    expect(page_heading).to_contain_text('İşlemler')
    expect(page_heading.locator('xpath=..')).to_contain_text(
        'Finansal hareketlerinizi tek yerde yönetin'
    )
    plans_link = page.get_by_role('link', name=re.compile(r'Planlı'))
    expect(plans_link).to_be_visible()
    expect(plans_link).to_contain_text(re.compile(r'Planlı'))
    expect(page.locator('.tx-action-toolbar .tx-btn')).to_have_count(5)
    expect(page.get_by_test_id('transactions-create-primary')).to_have_class(re.compile(r'\btx-btn-success\b'))
    expect(page.locator('#transTable thead th')).to_have_count(8)
    if page.locator('#transTable tbody .tx-table-action').count():
        expect(page.locator('#transTable tbody .tx-table-action').first).to_be_visible()

    page.get_by_test_id('transactions-create-primary').click()
    expect(page.locator('#newTransactionModal')).to_be_visible()
    expect(page.locator('#newTransactionModal h3')).to_contain_text('Yeni işlem ekle')
    expect(page.locator('#newTransactionModal')).to_contain_text('Tek bir tarih için finansal kayıt oluşturun.')
    expect(page.locator('#newTxBankAccount')).to_be_visible()


@pytest.mark.parametrize(
    ('language', 'expected_title'),
    [
        ('tr', 'İşlemler'),
        ('en', 'Transactions'),
        ('de', 'Transaktionen'),
        ('it', 'Transazioni'),
    ],
)
def test_transactions_title_renders_in_selected_locale(
    phase4_authenticated_page, language, expected_title
):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    page.goto(f'{base_url}/settings#locale', wait_until='domcontentloaded')
    page.locator("button[data-tab='locale']").click()
    if page.locator('html').get_attribute('lang') != language:
        with page.expect_response(f'**/set_language/{language}') as response_info:
            page.locator(f"button[onclick=\"changeLang('{language}')\"]").click()
        assert response_info.value.status == 200
        page.wait_for_load_state('domcontentloaded')
    page.goto(f'{base_url}/transactions', wait_until='networkidle')

    expect(page.locator('html')).to_have_attribute('lang', language)
    expect(page.locator('#main-content h1')).to_have_text(expected_title)
    expect(page).to_have_title(re.compile(rf'{re.escape(expected_title)}\\s*\\|'))


@pytest.mark.e2e
def test_transactions_explorer_workspace_and_filter_state(phase4_authenticated_page):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    page.goto(f'{base_url}/settings#locale', wait_until='domcontentloaded')
    if page.locator('html').get_attribute('lang') != 'tr':
        with page.expect_response('**/set_language/tr') as response_info:
            page.locator("button[onclick=\"changeLang('tr')\"]").click()
        assert response_info.value.status == 200
        page.wait_for_load_state('domcontentloaded')
    page.goto(f'{base_url}/transactions/explorer', wait_until='networkidle')

    expect(page).to_have_title(re.compile(r'İşlem Gezgini\s*\|'))
    expect(page.locator('#main-content h1')).to_have_text('İşlem Gezgini')
    expect(page.locator('#filterBankAccount')).to_be_visible()
    expect(page.locator('#filterTypeTransfer')).to_be_visible()
    expect(page.locator('#summaryNet')).to_be_visible()
    expect(page.locator('#summaryPending')).to_be_visible()
    expect(page.locator('#explorerError')).to_be_hidden()

    with page.expect_response(
        lambda response: '/api/transactions' in response.url and response.request.method == 'GET'
    ) as search_response:
        page.locator('#globalSearch').fill('Maaş')
        page.wait_for_timeout(450)
    assert search_response.value.status == 200
    expect(page).to_have_url(re.compile(r'[?&]q='))

    with page.expect_response(
        lambda response: '/api/transactions' in response.url and response.request.method == 'GET'
    ) as reset_response:
        page.locator('#globalSearch').fill('')
        page.wait_for_timeout(450)
    assert reset_response.value.status == 200
    cards = page.locator('#transactionList .transaction-card')
    if cards.count():
        with page.expect_response(
            lambda response: '/api/transactions/' in response.url and response.request.method == 'GET'
        ):
            cards.first.click()
        expect(page.locator('#sideDrawer')).to_have_class(re.compile(r'open'))
        expect(page.locator('#drawerContent')).to_contain_text('Banka hesabı')
        page.locator('.side-drawer .drawer-header button').click()
        expect(page.locator('#sideDrawer')).not_to_have_class(re.compile(r'open'))


@pytest.mark.e2e
@pytest.mark.parametrize(
    ('language', 'expected_title'),
    [
        ('tr', 'İşlem Gezgini'),
        ('en', 'Transaction Explorer'),
        ('de', 'Transaktions-Explorer'),
        ('it', 'Esplora transazioni'),
    ],
)
def test_transactions_explorer_renders_in_selected_locale(
    phase4_authenticated_page, language, expected_title
):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    page.goto(f'{base_url}/settings#locale', wait_until='domcontentloaded')
    if page.locator('html').get_attribute('lang') != language:
        with page.expect_response(f'**/set_language/{language}') as response_info:
            page.locator(f"button[onclick=\"changeLang('{language}')\"]").click()
        assert response_info.value.status == 200
        page.wait_for_load_state('domcontentloaded')
    page.goto(f'{base_url}/transactions/explorer', wait_until='networkidle')

    expect(page.locator('html')).to_have_attribute('lang', language)
    expect(page.locator('#main-content h1')).to_have_text(expected_title)
    expect(page).to_have_title(re.compile(rf'{re.escape(expected_title)}\\s*\\|'))
    expect(page.locator('#filterBankAccount')).to_be_visible()
    expect(page.locator('#summaryNet')).to_be_visible()


@pytest.mark.e2e
def test_transactions_action_toolbar_wraps_on_mobile(phase4_authenticated_page):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f'{base_url}/transactions', wait_until='networkidle')

    toolbar = page.locator('.tx-action-toolbar')
    expect(toolbar).to_be_visible()
    buttons = toolbar.locator('.tx-btn')
    expect(buttons).to_have_count(5)
    for index in range(buttons.count()):
        box = buttons.nth(index).bounding_box()
        assert box and box['width'] > 0 and box['height'] > 0
        assert box['x'] >= 0
        assert box['x'] + box['width'] <= 390


@pytest.mark.e2e
def test_transactions_table_has_consistent_columns_without_datatables_warning(
    phase4_authenticated_page,
):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    datatables_warnings = []
    page.on(
        'console',
        lambda message: datatables_warnings.append(message.text)
        if 'DataTables warning' in message.text
        else None,
    )
    page.goto(f'{base_url}/transactions', wait_until='networkidle')

    expect(page.locator('#transTable thead tr th')).to_have_count(8)
    rows = page.locator('#transTable tbody tr')
    for index in range(rows.count()):
        row = rows.nth(index)
        if row.locator('td.dataTables_empty').count():
            expect(row.locator('td')).to_have_count(1)
        else:
            expect(row.locator('td')).to_have_count(8)
    assert not datatables_warnings, datatables_warnings


@pytest.mark.e2e
@pytest.mark.parametrize(
    'viewport',
    [(1440, 900), (390, 844)],
    ids=['desktop', 'mobile'],
)
def test_transactions_empty_state_is_accessible_and_stable(
    phase4_authenticated_page, viewport
):
    base_url = os.getenv('E2E_BASE_URL', 'http://127.0.0.1:5000')
    page = phase4_authenticated_page
    page.set_viewport_size({'width': viewport[0], 'height': viewport[1]})
    console_errors = []
    page_errors = []
    page.on(
        'console',
        lambda message: console_errors.append(message.text)
        if message.type == 'error'
        else None,
    )
    page.on('pageerror', lambda error: page_errors.append(str(error)))
    page.goto(f'{base_url}/transactions', wait_until='networkidle')

    expect(page.locator('#transTable thead tr th')).to_have_count(8)
    live_rows = page.locator('#transTable tbody tr.tx-row')
    if live_rows.count():
        pytest.skip('Empty-state contract requires an isolated empty tenant/test DB; live staging contains real transaction records')

    empty_rows = page.locator('#transTable tbody tr')
    expect(empty_rows).to_have_count(1)
    expect(empty_rows.first.locator('td.dataTables_empty')).to_have_count(1)
    expect(empty_rows.first.locator('td')).to_have_count(1)

    empty_state = page.locator('#transactionTableEmptyState')
    expect(empty_state).to_be_visible()
    expect(empty_state.locator('h4')).not_to_be_empty()
    cta = empty_state.locator('button')
    expect(cta).to_have_count(1)
    cta_box = cta.bounding_box()
    assert cta_box and cta_box['width'] > 0 and cta_box['height'] > 0
    assert cta_box['x'] >= 0
    assert cta_box['x'] + cta_box['width'] <= page.viewport_size['width']
    expect(page.locator('#transTable .tx-table-action')).to_have_count(0)

    cta.click()
    expect(page.locator('#newTransactionModal')).to_be_visible()
    page.locator('#newTransactionModal .tx-modal-close').click()
    expect(page.locator('#newTransactionModal')).not_to_be_visible()
    assert not console_errors, console_errors
    assert not page_errors, page_errors
