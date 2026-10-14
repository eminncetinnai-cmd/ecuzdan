"""
Integration Tests - Routes
Route'lar için integration testler
"""

import pytest

from domain.portfolio.models import AssetUpdate
from models import db


def test_login_page(client):
    """Login sayfası testi"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Giri' in response.data or b'Login' in response.data

def test_login_success(client, test_user):
    """Başarılı login testi"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_login_failure(client):
    """Başarısız login testi"""
    response = client.post('/login', data={
        'username': 'invalid',
        'password': 'invalid'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_dashboard_authenticated(authenticated_client):
    """Dashboard sayfası testi (giriş yapmış kullanıcı)"""
    response = authenticated_client.get('/')
    assert response.status_code == 200


def test_dashboard_get_is_read_only_for_rolling_plan(
    authenticated_client, monkeypatch
):
    """Dashboard GET must not materialize plan transactions or occurrences."""
    from models import PlanOccurrence, RecurringPlan, Transaction
    from repositories.financial_repository import FinancialRepository

    plan = RecurringPlan(
        name='Dashboard no-write rolling plan',
        category='Maaş',
        flow_type='Gelir',
        amount=1000,
        installments=12,
        payment_day=25,
        start_date='2026-08-25',
        plan_type='Taksit',
        frequency='Aylık',
        status='Aktif',
        tenant_id='default',
    )
    db.session.add(plan)
    db.session.commit()
    plan_id = plan.id

    transaction_count_before = Transaction.query.filter_by(tenant_id='default').count()
    occurrence_count_before = PlanOccurrence.query.filter_by(tenant_id='default').count()

    def fail_if_materialized(*args, **kwargs):
        raise AssertionError('Dashboard GET must not materialize rolling transactions')

    monkeypatch.setattr(
        FinancialRepository,
        'generate_rolling_transactions',
        fail_if_materialized,
    )

    response = authenticated_client.get('/')

    assert response.status_code == 200
    assert Transaction.query.filter_by(tenant_id='default').count() == transaction_count_before
    assert PlanOccurrence.query.filter_by(tenant_id='default').count() == occurrence_count_before
    assert PlanOccurrence.query.filter_by(plan_id=plan_id).count() == 0


def test_settings_page_loads(authenticated_client):
    """Ayarlar sayfası yüklenmeli ve kritik UI bileşenleri doğru olmalı."""
    response = authenticated_client.get('/settings')
    assert response.status_code == 200
    assert b'https://cdn.jsdelivr.net/npm/chart.js' not in response.data
    assert b'chart.min.js' in response.data


def test_dashboard_unauthenticated(client):
    """Dashboard sayfası testi (giriş yapmamış kullanıcı)"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_reset_data_clears_tenant_financial_records(authenticated_admin_client, app, admin_user):
    """Reset data route should remove tenant-scoped financial records without failing."""
    from models import Asset, Transaction

    transaction = Transaction(
        date='2026-01-01',
        category='Test',
        description='Reset test transaction',
        type='Gider',
        amount=100,
        status='Ödendi',
        tenant_id=admin_user.tenant_id,
    )
    asset = Asset(
        type='Hisse Senedi',
        name='Reset Test Asset',
        value=1000,
        purchase_date='2026-01-01',
        purchase_cost=1000,
        quantity=10,
        unit_price=100,
        currency='TRY',
        symbol='RTA',
        risk_level='Orta',
        liquidity='Likit',
        sector_id=1,
        tenant_id=admin_user.tenant_id,
    )
    db.session.add_all([transaction, asset])
    db.session.commit()
    asset_id = asset.id

    asset_update = AssetUpdate(
        asset_id=asset_id,
        old_value=900,
        new_value=1000,
        update_type='manual',
    )
    db.session.add(asset_update)
    db.session.commit()

    response = authenticated_admin_client.post('/reset_data', data={'reset_pass': 'adminpass'})
    assert response.status_code == 302
    assert '/settings' in response.headers['Location']

    assert Transaction.query.filter_by(description='Reset test transaction').count() == 0
    assert Asset.query.filter_by(name='Reset Test Asset').count() == 0
    assert AssetUpdate.query.filter_by(asset_id=asset_id).count() == 0


def test_stale_browser_session_redirects_to_login(client, test_user, app):
    """Program yeniden açılışından kalmış eski session ana sayfaya alınmamalı."""
    app.config['TESTING'] = False
    try:
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
            sess['username'] = test_user.username
            sess['app_boot_id'] = 'old-boot-id'

        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    finally:
        app.config['TESTING'] = True

def test_logout(authenticated_client):
    """Logout testi"""
    response = authenticated_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

def test_transactions_page(authenticated_client):
    """Transactions sayfası testi"""
    response = authenticated_client.get('/transactions')
    assert response.status_code == 200

def test_transactions_new_modal_date_field_belongs_to_form(authenticated_client):
    """Transactions modal date input must be included in newTransactionForm FormData."""
    response = authenticated_client.get('/transactions')
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert 'id="newTxDate"' in html
    assert 'form="newTxDate"' not in html


def test_quick_transfer_accepts_display_date(authenticated_client, app):
    """Quick transfer stores dd/mm/yyyy input as yyyy-mm-dd."""
    from models import Asset, AssetTransaction, Transaction

    asset = Asset(
        type='Hisse Senedi',
        name='Quick Transfer Asset',
        value=1000,
        description='Test asset',
        purchase_date='2026-01-01',
        purchase_cost=1000,
        quantity=10,
        unit_price=100,
        currency='TRY',
        symbol='QTA',
        risk_level='Orta',
        liquidity='Likit',
        sector_id=1,
        tenant_id='default',
    )
    db.session.add(asset)
    db.session.commit()

    asset_id_str = str(asset.id)
    response = authenticated_client.post('/quick_transfer', data={
        'date': '29/06/2026',
        'amount': '250',
        'asset_id': asset_id_str,
        'note': 'display date test',
    }, headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'})

    assert response.status_code == 200
    assert response.get_json()['success'] is True

    tx = Transaction.query.filter_by(source_id=asset_id_str, source_type='asset', amount=250).first()
    assert tx is not None
    assert tx.date == '2026-06-29'

    asset_tx = AssetTransaction.query.filter_by(asset_id=asset_id_str, total_cost=250).first()
    assert asset_tx is not None
    assert asset_tx.transaction_date == '2026-06-29'


def test_new_transaction_accepts_display_date(authenticated_client):
    """New transaction stores dd/mm/yyyy input as yyyy-mm-dd."""
    from models import Transaction

    response = authenticated_client.post('/new_transaction', data={
        'date': '29/06/2026',
        'category': 'Maaş',
        'amount': '123.45',
        'description': 'display date transaction',
        'status': 'Ödendi',
    }, headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'})

    assert response.status_code == 200
    assert response.get_json()['success'] is True

    tx = Transaction.query.filter_by(description='display date transaction').first()
    assert tx is not None
    assert tx.date == '2026-06-29'


def test_new_transaction_defaults_blank_date_to_today(authenticated_client):
    """Blank new transaction date falls back to today instead of failing."""
    from engines.financial_engine import today_storage
    from models import Transaction

    response = authenticated_client.post('/new_transaction', data={
        'date': '',
        'category': 'Maaş',
        'amount': '67.89',
        'description': 'blank date transaction',
        'status': 'Ödendi',
    }, headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'})

    assert response.status_code == 200
    assert response.get_json()['success'] is True

    tx = Transaction.query.filter_by(description='blank date transaction').first()
    assert tx is not None
    assert tx.date == today_storage()


def test_assets_page(authenticated_client):
    """Assets sayfası testi"""
    response = authenticated_client.get('/assets_view')
    assert response.status_code == 200

def test_assets_management_page(authenticated_client):
    """Varlık yönetimi sayfası testi"""
    response = authenticated_client.get('/assets_management')
    assert response.status_code == 200

def test_asset_crud_flow(authenticated_client, app):
    """Varlık ekleme, güncelleme ve silme akışı"""
    from models import Asset, AssetSector, AssetTransaction, Transaction
    sector = AssetSector.query.first()
    sector_id = sector.id if sector else 1
    response = authenticated_client.post('/new_asset', data={
        'type': 'Hisse Senedi',
        'name': 'Test Hisse',
        'quantity': '10',
        'unit_price': '100',
        'purchase_cost': '1000',
        'purchase_date': '2025-01-01',
        'currency': 'TRY',
        'symbol': 'TEST',
        'risk_level': 'Orta',
        'liquidity': 'Likit',
        'sector_id': str(sector_id),
        'sync_cash': 'on',
    }, follow_redirects=True)
    assert response.status_code == 200

    asset = Asset.query.filter_by(name='Test Hisse').first()
    assert asset is not None
    asset_id = asset.id
    assert Transaction.query.filter_by(source_id=asset_id, source_type='asset').count() == 1

    response = authenticated_client.post(f'/edit_asset/{asset_id}', data={
        'type': 'Hisse Senedi',
        'name': 'Test Hisse',
        'quantity': '10',
        'unit_price': '120',
        'purchase_date': '2025-01-01',
        'currency': 'TRY',
        'symbol': 'TEST',
        'risk_level': 'Orta',
        'liquidity': 'Likit',
        'sector_id': str(sector_id),
    }, follow_redirects=True)
    assert response.status_code == 200
    assert db.session.get(Asset, asset_id).value == 1200

    response = authenticated_client.post(f'/delete_asset/{asset_id}', follow_redirects=True)
    assert response.status_code == 200
    assert db.session.get(Asset, asset_id) is None
    assert AssetTransaction.query.filter_by(asset_id=asset_id).count() == 0
    assert Transaction.query.filter_by(source_id=asset_id, source_type='asset').count() == 0

def test_plans_page(authenticated_client):
    """Plans sayfası testi"""
    response = authenticated_client.get('/plans')
    assert response.status_code == 200

def test_categories_page(authenticated_client):
    """Categories sayfası testi"""
    response = authenticated_client.get('/categories')
    assert response.status_code == 200

def test_analysis_page(authenticated_client):
    """Analysis sayfası testi"""
    response = authenticated_client.get('/analysis')
    assert response.status_code == 200

def test_financial_freedom_page(authenticated_client):
    """Finansal özgürlük sayfası testi"""
    response = authenticated_client.get('/financial_freedom')
    assert response.status_code == 200
    assert b'FI Hedefi' in response.data or b'Finansal' in response.data
    assert b'Kriter Karnesi' in response.data or b'K\xc3\xbcresel' in response.data

def test_monthly_dashboard_page(authenticated_client):
    """Aylık dashboard sayfası testi"""
    response = authenticated_client.get('/monthly_dashboard')
    assert response.status_code == 200
    assert b'Ger\xc3\xa7ekle\xc5\x9fen Net Nakit' in response.data
    assert b'Bekleyen Net Etki' in response.data
    assert 'Varlık Değerleme Farkı' in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ('language', 'first_month', 'last_month'),
    [
        ('tr', 'Ocak', 'Aralık'),
        ('en', 'January', 'December'),
        ('de', 'Januar', 'Dezember'),
        ('it', 'Gennaio', 'Dicembre'),
    ],
)
def test_monthly_dashboard_month_labels_follow_selected_locale(
    authenticated_client, language, first_month, last_month
):
    with authenticated_client.session_transaction() as flask_session:
        flask_session['lang'] = language
        flask_session['lang_source'] = 'explicit'

    response = authenticated_client.get('/monthly_dashboard')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert first_month in html
    assert last_month in html
    assert f'<html lang="{language}"' in html
    if language != 'tr':
        assert 'Ocak' not in html
        assert 'Aralık' not in html


def test_security_headers(client):
    """Security headers testi"""
    response = client.get('/login')
    assert 'X-Frame-Options' in response.headers
    assert 'X-Content-Type-Options' in response.headers
    assert 'Content-Security-Policy' in response.headers
