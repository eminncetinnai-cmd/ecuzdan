import pytest

from app import db
from models import Transaction


@pytest.mark.regression
def test_reconciliation_endpoint_is_read_only_and_returns_contract(authenticated_client):
    response = authenticated_client.get('/api/transactions/reconciliation?as_of=2026-12-31')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['as_of'] == '2026-12-31'
    for key in (
        'transaction_count', 'income', 'expense', 'investment', 'book_balance',
        'cleared_balance', 'pending_net', 'reconciled', 'status_code',
        'explainable', 'pending_summary', 'pending_items', 'issues',
        'recommendations',
    ):
        assert key in payload
    assert payload['status_code'] == 'statement_required'
    assert payload['pending_summary']['count'] == payload['pending_count']


@pytest.mark.regression
def test_reconciliation_rejects_invalid_statement_balance(authenticated_client):
    response = authenticated_client.get('/api/transactions/reconciliation?statement_balance=not-a-number')
    assert response.status_code == 400
    assert response.get_json()['success'] is False


def test_reconciliation_requires_authentication(client):
    response = client.get('/api/transactions/reconciliation')
    assert response.status_code in {302, 401}
    if response.status_code == 302:
        assert response.headers['Location'].endswith('/login')
    else:
        assert response.get_json()['error_code'] == 'authentication_required'


def test_reconciliation_classifies_pending_timing_difference(app, authenticated_client):
    db.session.add(Transaction(
        date='2026-12-01',
        category='Kredi',
        description='Bekleyen banka hareketi',
        type='Gider',
        amount=50,
        status='Bekliyor',
        tenant_id='default',
    ))
    db.session.commit()

    response = authenticated_client.get(
        '/api/transactions/reconciliation?as_of=2026-12-31&statement_balance=0'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status_code'] == 'explained_by_pending'
    assert payload['reconciled'] is False
    assert payload['explainable'] is True
    assert payload['pending_count'] == 1
    assert payload['pending_items'][0]['description'] == 'Bekleyen banka hareketi'
    assert payload['issues'][0]['code'] == 'PENDING_TIMING_DIFFERENCE'


def test_reconciliation_rejects_invalid_date_and_pending_limit(authenticated_client):
    invalid_date = authenticated_client.get(
        '/api/transactions/reconciliation?as_of=31-12-2026'
    )
    invalid_limit = authenticated_client.get(
        '/api/transactions/reconciliation?pending_limit=201'
    )
    assert invalid_date.status_code == 400
    assert invalid_limit.status_code == 400


def test_reconciliation_keeps_internal_transfers_cash_neutral(app, authenticated_client):
    db.session.add(Transaction(
        date='2026-12-01',
        category='Transfer',
        description='Hesaplar arası aktarım',
        type='Transfer',
        amount=500,
        status='Ödendi',
        tenant_id='default',
        transfer_from='vadesiz',
        transfer_to='yatirim',
    ))
    db.session.commit()

    response = authenticated_client.get(
        '/api/transactions/reconciliation?as_of=2026-12-31&statement_balance=0'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['book_balance'] == '0.0000'
    assert payload['cleared_balance'] == '0.0000'
    assert payload['status_code'] == 'reconciled'
