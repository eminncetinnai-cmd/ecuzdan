"""
Unit Tests - Transactions Routes
Transaction route functions
"""

from unittest.mock import Mock

import pytest

from routes.transactions import (
    register_transaction_routes,
)


@pytest.mark.unit
def test_register_transaction_routes():
    """Test register_transaction_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    register_transaction_routes(mock_bp)

    assert mock_bp.route.called


@pytest.mark.unit
def test_transactions_imports():
    """Test that register_transaction_routes can be imported"""
    from routes.transactions import register_transaction_routes

    assert callable(register_transaction_routes)


@pytest.mark.unit
def test_transactions_routes_structure():
    """Test transactions routes module structure"""
    import routes.transactions as transactions_module

    # Check for expected function
    assert hasattr(transactions_module, 'register_transaction_routes')

    # Check for expected imports
    assert hasattr(transactions_module, 'logging')
    assert hasattr(transactions_module, 'json')
    assert hasattr(transactions_module, 'datetime')
    assert hasattr(transactions_module, 'flash')
    assert hasattr(transactions_module, 'g')
    assert hasattr(transactions_module, 'jsonify')
    assert hasattr(transactions_module, 'redirect')
    assert hasattr(transactions_module, 'render_template')
    assert hasattr(transactions_module, 'request')
    assert hasattr(transactions_module, 'url_for')


@pytest.mark.unit
def test_transactions_logger_exists():
    """Test transactions module has logger"""
    import routes.transactions as transactions_module
    assert hasattr(transactions_module, 'logger')
    assert transactions_module.logger is not None


@pytest.mark.unit
def test_register_transaction_routes_route_registration():
    """Test register_transaction_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    register_transaction_routes(mock_bp)

    # Should register multiple routes
    assert mock_bp.route.call_count >= 6


@pytest.mark.unit
def test_transactions_module_has_required_imports():
    """Test transactions module has required imports"""
    import routes.transactions as transactions_module

    # Flask imports
    assert hasattr(transactions_module, 'flash')
    assert hasattr(transactions_module, 'g')
    assert hasattr(transactions_module, 'jsonify')
    assert hasattr(transactions_module, 'redirect')
    assert hasattr(transactions_module, 'render_template')
    assert hasattr(transactions_module, 'request')
    assert hasattr(transactions_module, 'url_for')

    # Custom imports
    assert hasattr(transactions_module, 'get_container')
    assert hasattr(transactions_module, 'today_display')
    assert hasattr(transactions_module, 'Transaction')
    assert hasattr(transactions_module, 'db')
    assert hasattr(transactions_module, 'handle_ajax_or_flash')
    assert hasattr(transactions_module, 'is_ajax_request')
    assert hasattr(transactions_module, 'rollback_session')
    assert hasattr(transactions_module, 'transaction_form_from_request')
    assert hasattr(transactions_module, 'LedgerError')
    assert hasattr(transactions_module, 'to_decimal')


@pytest.mark.unit
def test_transactions_blueprint_parameter():
    """Test register_transaction_routes accepts blueprint parameter"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    # Should not raise exception
    register_transaction_routes(mock_bp)


@pytest.mark.unit
def test_transactions_list_route_exists():
    """Test transactions list route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/transactions' in source


@pytest.mark.unit
def test_transactions_new_transaction_route_exists():
    """Test new transaction route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/new_transaction' in source


@pytest.mark.unit
def test_transactions_edit_route_exists():
    """Test edit transaction route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/edit_t' in source


@pytest.mark.unit
def test_transactions_delete_route_exists():
    """Test delete transaction route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/delete_t' in source


@pytest.mark.unit
def test_transactions_explorer_route_exists():
    """Test transactions explorer route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/transactions/explorer' in source


@pytest.mark.unit
def test_transactions_api_transactions_route_exists():
    """Test API transactions route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/api/transactions' in source


@pytest.mark.unit
def test_transactions_api_transaction_detail_route_exists():
    """Test API transaction detail route exists"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '/api/transactions/<int:id>' in source or '/api/transactions' in source


@pytest.mark.unit
def test_transactions_error_handling_structure():
    """Test transactions routes have error handling"""
    import inspect

    import routes.transactions as transactions_module

    # Check that the module has error handling patterns
    source = inspect.getsource(transactions_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_transactions_ajax_handling():
    """Test transactions routes use AJAX helpers"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'is_ajax_request' in source or 'handle_ajax_or_flash' in source


@pytest.mark.unit
def test_transactions_json_responses():
    """Test transactions routes use jsonify"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'jsonify' in source


@pytest.mark.unit
def test_transactions_flash_messaging():
    """Test transactions routes use flash messaging"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'flash' in source


@pytest.mark.unit
def test_transactions_rollback_session():
    """Test transactions routes use rollback_session"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'rollback_session' in source


@pytest.mark.unit
def test_transactions_ledger_error():
    """Test transactions routes handle LedgerError"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'LedgerError' in source


@pytest.mark.unit
def test_transactions_query_filters():
    """Test transactions API uses query filters"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'filters' in source


@pytest.mark.unit
def test_transactions_pagination():
    """Test transactions API uses pagination"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'paginate' in source


@pytest.mark.unit
def test_transactions_container_usage():
    """Test transactions module uses container"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'get_container' in source or '_container' in source


@pytest.mark.unit
def test_transactions_commands_queries():
    """Test transactions module uses commands and queries"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '_commands' in source or '_queries' in source


@pytest.mark.unit
def test_transactions_outbox():
    """Test transactions module uses outbox"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert '_outbox' in source


@pytest.mark.unit
def test_transactions_transaction_model():
    """Test transactions module uses Transaction model"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'Transaction' in source


@pytest.mark.unit
def test_transactions_decimal_precision():
    """Test transactions module uses decimal precision"""
    import inspect

    import routes.transactions as transactions_module

    source = inspect.getsource(transactions_module)
    assert 'to_decimal' in source or 'Decimal' in source


@pytest.mark.unit
def test_transactions_cache_invalidation_and_api():
    """Test transactions routes include financial cache invalidation and flat query API support"""
    import inspect

    import routes.transactions_api as api_module
    import routes.transactions_crud as crud_module

    crud_source = inspect.getsource(crud_module)
    assert 'invalidate_financial_cache' in crud_source
    assert 'format' in crud_source

    api_source = inspect.getsource(api_module)
    assert 'flat_search' in api_source
    assert 'flat_types' in api_source


# ── Live Route & Client Functional Integration Tests ─────────────────────────

from decimal import Decimal
from models import BankAccount, Category, Tenant, Transaction, db


@pytest.mark.unit
def test_transactions_page_get(authenticated_client, app):
    """GET /transactions returns 200 and renders transaction table."""
    resp = authenticated_client.get('/transactions')
    assert resp.status_code == 200
    assert b'transactions' in resp.data or b'table' in resp.data


@pytest.mark.unit
def test_transactions_page_smart_default_tab_with_pending(authenticated_client, app):
    """GET /transactions defaults to 'pending' when pending transactions exist."""
    with app.app_context():
        tx = Transaction.query.filter_by(status='Bekliyor', is_deleted=False).first()
        if not tx:
            tx = Transaction(
                date='2026-10-25',
                category='Maaş',
                description='Test Bekleyen Fatura',
                type='Gider',
                amount=500,
                status='Bekliyor',
                tenant_id='default',
            )
            db.session.add(tx)
            db.session.commit()

        resp = authenticated_client.get('/transactions')
        assert resp.status_code == 200
        assert b'data-active-tab="pending"' in resp.data

        # Explicit tab=all override should be respected
        resp_all = authenticated_client.get('/transactions?tab=all')
        assert resp_all.status_code == 200
        assert b'data-active-tab="all"' in resp_all.data

        # Explicit tab=paid override should be respected
        resp_paid = authenticated_client.get('/transactions?tab=paid')
        assert resp_paid.status_code == 200
        assert b'data-active-tab="paid"' in resp_paid.data


@pytest.mark.unit
def test_transactions_page_smart_default_tab_without_pending(authenticated_client, app):
    """GET /transactions defaults to 'all' when no pending transactions exist."""
    with app.app_context():
        pendings = Transaction.query.filter_by(status='Bekliyor').all()
        for p in pendings:
            p.status = 'Ödendi'
        db.session.commit()

        resp = authenticated_client.get('/transactions')
        assert resp.status_code == 200
        assert b'data-active-tab="all"' in resp.data


@pytest.mark.unit
def test_transactions_page_pagination(authenticated_client, app):
    """GET /transactions?page=2 handles pagination properly."""
    resp = authenticated_client.get('/transactions?page=2')
    assert resp.status_code == 200



@pytest.mark.unit
def test_new_transaction_success_redirect(authenticated_client, app):
    """POST /new_transaction redirects and creates record in database."""
    with app.app_context():
        resp = authenticated_client.post('/new_transaction', data={
            'amount': '450.00',
            'category': 'Maaş',
            'description': 'Aylık prim',
            'status': 'Ödendi',
            'date': '2026-10-12',
            'note': 'Test notu',
        }, follow_redirects=False)
        assert resp.status_code == 302
        tx = Transaction.query.filter_by(description='Aylık prim').first()
        assert tx is not None
        assert tx.amount == Decimal('450.00')
        assert tx.status == 'Ödendi'


@pytest.mark.unit
def test_new_transaction_ajax_success(authenticated_client, app):
    """POST /new_transaction with AJAX header returns JSON."""
    with app.app_context():
        resp = authenticated_client.post('/new_transaction', headers={
            'X-Requested-With': 'XMLHttpRequest',
        }, data={
            'amount': '125.50',
            'category': 'Maaş',
            'description': 'Ajax ekleme',
            'status': 'Bekliyor',
            'date': '2026-10-12',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        tx = Transaction.query.filter_by(description='Ajax ekleme').first()
        assert tx is not None
        assert tx.status == 'Bekliyor'


@pytest.mark.unit
def test_new_transaction_validation_errors(authenticated_client, app):
    """POST /new_transaction rejects zero/negative amounts and invalid categories."""
    resp = authenticated_client.post('/new_transaction', headers={
        'X-Requested-With': 'XMLHttpRequest',
    }, data={
        'amount': '-50',
        'category': 'Maaş',
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False

    resp2 = authenticated_client.post('/new_transaction', headers={
        'X-Requested-With': 'XMLHttpRequest',
    }, data={
        'amount': '100',
        'category': 'BilinmeyenKategori_XYZ',
    })
    assert resp2.status_code == 200
    assert resp2.get_json()['success'] is False


@pytest.mark.unit
def test_new_transaction_idempotency_key(authenticated_client, app):
    """POST /new_transaction with duplicate idempotency_key prevents multiple rows."""
    with app.app_context():
        idem_key = "test-idem-key-999"
        payload = {
            'amount': '75.00',
            'category': 'Maaş',
            'description': 'Idempotent işlem',
            'status': 'Ödendi',
            'idempotency_key': idem_key,
        }
        resp1 = authenticated_client.post('/new_transaction', headers={'X-Requested-With': 'XMLHttpRequest'}, data=payload)
        assert resp1.get_json()['success'] is True

        resp2 = authenticated_client.post('/new_transaction', headers={'X-Requested-With': 'XMLHttpRequest'}, data=payload)
        assert resp2.status_code == 200
        count = Transaction.query.filter_by(idempotency_key=idem_key).count()
        assert count == 1


@pytest.mark.unit
def test_edit_transaction_pending(authenticated_client, app):
    """POST /edit_t/<id> updates pending transaction."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-12',
            category='Maaş',
            description='Eski açıklama',
            type='Gelir',
            amount=Decimal('100.00'),
            status='Bekliyor',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

        resp = authenticated_client.post(f'/edit_t/{tx_id}', headers={'X-Requested-With': 'XMLHttpRequest'}, data={
            'amount': '150.00',
            'category': 'Maaş',
            'description': 'Güncel açıklama',
            'status': 'Bekliyor',
            'date': '2026-10-12',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

        updated = db.session.get(Transaction, tx_id)
        assert updated.amount == Decimal('150.00')
        assert updated.description == 'Güncel açıklama'


@pytest.mark.unit
def test_edit_transaction_paid_blocked(authenticated_client, app):
    """POST /edit_t/<id> for paid transaction is rejected by ledger immutability rule."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-12',
            category='Maaş',
            description='Ödenmiş işlem',
            type='Gelir',
            amount=Decimal('500.00'),
            status='Ödendi',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

        resp = authenticated_client.post(f'/edit_t/{tx_id}', headers={'X-Requested-With': 'XMLHttpRequest'}, data={
            'amount': '600.00',
            'category': 'Maaş',
            'description': 'Değiştirilmek istenen',
            'status': 'Ödendi',
            'date': '2026-10-12',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False


@pytest.mark.unit
def test_delete_transaction_pending(authenticated_client, app):
    """POST /delete_t/<id> successfully deletes a pending transaction."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-12',
            category='Maaş',
            description='Silinecek bekleyen işlem',
            type='Gelir',
            amount=Decimal('200.00'),
            status='Bekliyor',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

        resp = authenticated_client.post(f'/delete_t/{tx_id}', headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        deleted = db.session.get(Transaction, tx_id)
        assert deleted is None or deleted.is_deleted is True


@pytest.mark.unit
def test_delete_transaction_paid_blocked(authenticated_client, app):
    """POST /delete_t/<id> blocks deletion of paid transactions."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-12',
            category='Maaş',
            description='Silinemez ödenmiş işlem',
            type='Gelir',
            amount=Decimal('300.00'),
            status='Ödendi',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

        resp = authenticated_client.post(f'/delete_t/{tx_id}', headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False
        assert db.session.get(Transaction, tx_id) is not None


@pytest.mark.unit
def test_quick_pay_route(authenticated_client, app):
    """POST /transactions/<id>/quick-pay marks pending transaction as paid."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-12',
            category='Maaş',
            description='Hızlı ödenecek işlem',
            type='Gelir',
            amount=Decimal('350.00'),
            status='Bekliyor',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

        resp = authenticated_client.post(f'/transactions/{tx_id}/quick-pay', headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['status'] == 'Ödendi'

        # Check not found
        resp404 = authenticated_client.post('/transactions/999999/quick-pay', headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp404.status_code == 404


@pytest.mark.unit
def test_transactions_explorer_page(authenticated_client, app):
    """GET /transactions/explorer returns 200."""
    resp = authenticated_client.get('/transactions/explorer')
    assert resp.status_code == 200


@pytest.mark.unit
def test_api_transactions_list_and_filters(authenticated_client, app):
    """GET /api/transactions supports pagination and date range validation."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-10',
            category='Maaş',
            description='API Test işlem',
            type='Gelir',
            amount=Decimal('100.00'),
            status='Ödendi',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()

    resp = authenticated_client.get('/api/transactions?page=1&limit=10')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'transactions' in data
    assert len(data['transactions']) >= 1

    # Test invalid date range
    bad_resp = authenticated_client.get('/api/transactions?dateFrom=2026-12-31&dateTo=2026-01-01')
    assert bad_resp.status_code == 400


@pytest.mark.unit
def test_api_transaction_detail(authenticated_client, app):
    """GET /api/transactions/<id> returns transaction details or 404."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-10',
            category='Maaş',
            description='Detay işlem',
            type='Gelir',
            amount=Decimal('100.00'),
            status='Ödendi',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

    resp = authenticated_client.get(f'/api/transactions/{tx_id}')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    resp404 = authenticated_client.get('/api/transactions/999999')
    assert resp404.status_code == 404


@pytest.mark.unit
def test_api_transaction_lineage(authenticated_client, app):
    """GET /api/transactions/<id>/lineage returns audit and lineage tree."""
    with app.app_context():
        tx = Transaction(
            date='2026-10-10',
            category='Maaş',
            description='Lineage test işlem',
            type='Gelir',
            amount=Decimal('100.00'),
            status='Ödendi',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

    resp = authenticated_client.get(f'/api/transactions/{tx_id}/lineage')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'original' in data['data']


@pytest.mark.unit
def test_new_transaction_with_bank_account(authenticated_client, app):
    """POST /new_transaction assigns active bank account and validates invalid accounts."""
    with app.app_context():
        acc = BankAccount(
            name="Garanti Vadeli",
            currency="TRY",
            account_type="Mevduat",
            tenant_id="default",
            is_active=True,
        )
        db.session.add(acc)
        db.session.commit()
        acc_id = acc.id

    resp = authenticated_client.post('/new_transaction', headers={'X-Requested-With': 'XMLHttpRequest'}, data={
        'amount': '250.00',
        'category': 'Maaş',
        'description': 'Banka hesaplı işlem',
        'status': 'Ödendi',
        'bank_account_id': str(acc_id),
    })
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    # Invalid bank account ID
    resp_invalid = authenticated_client.post('/new_transaction', headers={'X-Requested-With': 'XMLHttpRequest'}, data={
        'amount': '250.00',
        'category': 'Maaş',
        'bank_account_id': '999999',
    })
    assert resp_invalid.status_code == 200
    assert resp_invalid.get_json()['success'] is False


@pytest.mark.unit
def test_api_adjustment_and_reversal(client, app):
    """Test adjustments and reversals with capability guarding and idempotency."""
    with app.app_context():
        from models import User
        emin = User.query.filter_by(username='emin').first()
        test_user = User.query.filter_by(username='testuser').first()
        test_user_id = test_user.id
        test_user_name = test_user.username
        emin_id = emin.id
        emin_name = emin.username
        tx = Transaction(
            date='2026-10-10',
            category='Maaş',
            description='Ödenmiş maaş işlemi',
            type='Gelir',
            amount=Decimal('1000.00'),
            status='Ödendi',
            tenant_id='default',
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

    # Normal user without capability -> blocked
    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['username'] = test_user_name
    resp_forbidden = client.post(f'/api/transactions/{tx_id}/adjustments', json={
        'amount_delta': '-100.00',
        'reason_code': 'OVERCHARGE',
        'reason_text': 'Fazla ödeme düzeltmesi',
    }, headers={'Idempotency-Key': 'adj-idem-001'})
    assert resp_forbidden.status_code in (401, 403)

    # Superadmin user with capability -> authorized
    with client.session_transaction() as sess:
        sess['user_id'] = emin_id
        sess['username'] = emin_name

    # Missing fields -> 400
    resp_bad = client.post(f'/api/transactions/{tx_id}/adjustments', json={
        'amount_delta': '-100.00',
    })
    assert resp_bad.status_code == 400

    # Valid adjustment -> 201
    resp_adj = client.post(f'/api/transactions/{tx_id}/adjustments', json={
        'amount_delta': '-100.00',
        'reason_code': 'OVERCHARGE',
        'reason_text': 'Fazla ödeme düzeltmesi',
    }, headers={'Idempotency-Key': 'adj-idem-001'})
    assert resp_adj.status_code == 201
    adj_data = resp_adj.get_json()
    assert adj_data['success'] is True

    # Replay same idempotency key -> 200
    resp_adj_replay = client.post(f'/api/transactions/{tx_id}/adjustments', json={
        'amount_delta': '-100.00',
        'reason_code': 'OVERCHARGE',
        'reason_text': 'Fazla ödeme düzeltmesi',
    }, headers={'Idempotency-Key': 'adj-idem-001'})
    assert resp_adj_replay.status_code == 200
    assert resp_adj_replay.get_json()['idempotency_replayed'] is True

    # Valid reversal -> 201
    resp_rev = client.post(f'/api/transactions/{tx_id}/reversal', json={
        'reason_code': 'CANCELLED',
        'reason_text': 'İptal edilen işlem',
    }, headers={'Idempotency-Key': 'rev-idem-001'})
    assert resp_rev.status_code == 201
    rev_data = resp_rev.get_json()
    assert rev_data['success'] is True

    # Reversal replay -> 200
    resp_rev_replay = client.post(f'/api/transactions/{tx_id}/reversal', json={
        'reason_code': 'CANCELLED',
        'reason_text': 'İptal edilen işlem',
    }, headers={'Idempotency-Key': 'rev-idem-001'})
    assert resp_rev_replay.status_code == 200
    assert resp_rev_replay.get_json()['idempotency_replayed'] is True


