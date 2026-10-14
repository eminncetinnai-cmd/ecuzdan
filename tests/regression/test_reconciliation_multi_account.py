import pytest

from app import db
from models import BankAccount, BankStatementSnapshot, Tenant, Transaction

pytestmark = pytest.mark.regression


def _account(name, currency='TRY', tenant_id='default'):
    account = BankAccount(
        tenant_id=tenant_id,
        name=name,
        institution=f'{name} Bank',
        account_type='checking',
        currency=currency,
    )
    db.session.add(account)
    db.session.flush()
    return account


def _transaction(account, *, amount, type_, status='Ödendi', description='Test hareketi'):
    transaction = Transaction(
        date='2026-12-01',
        category='Maaş' if type_ == 'Gelir' else 'Kredi',
        description=description,
        type=type_,
        amount=amount,
        status=status,
        tenant_id=account.tenant_id,
        bank_account_id=account.id,
    )
    db.session.add(transaction)
    return transaction


def test_canonical_reconciliation_empty_state_is_explicit_and_read_only(app, authenticated_client):
    before = db.session.query(Transaction).count()

    response = authenticated_client.get('/api/reconciliation?as_of=2026-12-31')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status_code'] == 'no_accounts'
    assert payload['issues'][0]['code'] == 'NO_BANK_ACCOUNTS'
    assert payload['recommendations'] == ['ADD_BANK_ACCOUNT']
    assert payload['accounts'] == []
    assert db.session.query(Transaction).count() == before


def test_reconciliation_filters_each_account_and_consolidates_same_currency(app, authenticated_client):
    primary = _account('Vadesiz TRY')
    secondary = _account('Birikim TRY')
    _transaction(primary, amount=100, type_='Gelir', description='Maaş')
    _transaction(primary, amount=10, type_='Gider', status='Bekliyor', description='Bekleyen fatura')
    _transaction(secondary, amount=40, type_='Gider', description='Kira')
    db.session.commit()

    primary_response = authenticated_client.get(
        f'/api/reconciliation?account_id={primary.id}&as_of=2026-12-31&statement_balance=90'
    )
    secondary_response = authenticated_client.get(
        f'/api/reconciliation?account_id={secondary.id}&as_of=2026-12-31&statement_balance=-40'
    )
    all_response = authenticated_client.get(
        '/api/reconciliation?as_of=2026-12-31&statement_balance=50'
    )

    primary_payload = primary_response.get_json()
    secondary_payload = secondary_response.get_json()
    all_payload = all_response.get_json()
    assert primary_payload['transaction_count'] == 2
    assert primary_payload['book_balance'] == '90.0000'
    assert primary_payload['pending_count'] == 1
    assert primary_payload['reconciled'] is True
    assert secondary_payload['transaction_count'] == 1
    assert secondary_payload['book_balance'] == '-40.0000'
    assert secondary_payload['reconciled'] is True
    assert all_payload['scope'] == 'all_accounts'
    assert all_payload['transaction_count'] == 3
    assert all_payload['book_balance'] == '50.0000'
    assert all_payload['reconciled'] is True


def test_reconciliation_never_silently_merges_different_currencies(app, authenticated_client):
    _account('TRY hesabı', 'TRY')
    _account('USD hesabı', 'USD')
    db.session.commit()

    response = authenticated_client.get('/api/reconciliation?as_of=2026-12-31')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status_code'] == 'currency_selection_required'
    assert payload['book_balance'] == '0.0000'
    assert {group['currency'] for group in payload['currency_groups']} == {'TRY', 'USD'}
    assert payload['issues'][0]['code'] == 'CURRENCY_SELECTION_REQUIRED'


def test_statement_snapshot_is_explicitly_saved_and_reused(app, authenticated_client):
    account = _account('Ana hesap')
    _transaction(account, amount=125, type_='Gelir', description='Statement ile eşleşen gelir')
    db.session.commit()

    save_response = authenticated_client.post(
        '/api/reconciliation/statements',
        json={
            'account_id': account.id,
            'as_of': '2026-12-31',
            'balance': '125.00',
            'note': 'Aralık banka ekstresi',
        },
    )
    assert save_response.status_code == 200
    saved = save_response.get_json()
    assert saved['statement']['currency'] == 'TRY'
    assert saved['statement']['source'] == 'manual'
    assert saved['reconciliation']['statement_source'] == 'saved_snapshot'
    assert saved['reconciliation']['reconciled'] is True

    summary_response = authenticated_client.get(
        f'/api/reconciliation?account_id={account.id}&as_of=2026-12-31'
    )
    history_response = authenticated_client.get(
        f'/api/reconciliation/statements?account_id={account.id}'
    )
    summary = summary_response.get_json()
    history = history_response.get_json()
    assert summary['statement_balance'] == '125.0000'
    assert summary['statement_snapshot_id'] == saved['statement']['id']
    assert len(history['statements']) == 1
    assert history['statements'][0]['note'] == 'Aralık banka ekstresi'
    assert db.session.query(BankStatementSnapshot).count() == 1


def test_transaction_create_preserves_selected_bank_account(app, authenticated_client):
    account = _account('İşlem hesabı')
    account_id = account.id
    db.session.commit()

    response = authenticated_client.post(
        '/new_transaction',
        data={
            'date': '2026-12-01',
            'category': 'Maaş',
            'description': 'Hesaba bağlanan maaş',
            'amount': '200',
            'status': 'Ödendi',
            'note': '',
            'bank_account_id': str(account_id),
        },
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )

    assert response.status_code == 200
    transaction = Transaction.query.filter_by(description='Hesaba bağlanan maaş').one()
    assert transaction.bank_account_id == account_id


def test_reconciliation_hides_cross_tenant_account(app, authenticated_client):
    other = Tenant(id='other-tenant', name='Other Tenant')
    db.session.add(other)
    db.session.flush()
    foreign_account = _account('Başka tenant hesabı', tenant_id=other.id)
    db.session.commit()

    response = authenticated_client.get(
        f'/api/reconciliation?account_id={foreign_account.id}&as_of=2026-12-31'
    )

    assert response.status_code == 404
    assert response.get_json()['error_code'] == 'resource_not_found'
