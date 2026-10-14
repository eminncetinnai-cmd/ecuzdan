"""Phase 3 transaction retry and optimistic concurrency regression tests."""
from models import Transaction
from shared.db import db

JSON_HEADERS = {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}

def test_transaction_create_is_idempotent(authenticated_client, app):
    key = "phase3-idempotency-replay-001"
    payload = {'date': '29/06/2026', 'category': 'Maaş', 'amount': '321.45', 'description': 'phase3 idempotent transaction', 'status': 'Ödendi'}
    headers = {**JSON_HEADERS, 'Idempotency-Key': key}
    first = authenticated_client.post('/new_transaction', data=payload, headers=headers)
    second = authenticated_client.post('/new_transaction', data=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json()['success'] is True
    assert second.get_json()['success'] is True
    with app.app_context():
        rows = Transaction.query.filter_by(idempotency_key=key).all()
        assert len(rows) == 1
        assert rows[0].version == 1

def test_transaction_update_rejects_stale_if_match(authenticated_client, app):
    payload = {'date': '29/06/2026', 'category': 'Maaş', 'amount': '654.32', 'description': 'phase3 concurrency transaction', 'status': 'Bekliyor'}

    created = authenticated_client.post('/new_transaction', data=payload, headers=JSON_HEADERS)
    assert created.status_code == 200
    with app.app_context():
        tx = Transaction.query.filter_by(description='phase3 concurrency transaction').first()
        tx_id, original_version = tx.id, tx.version
    update = {**payload, 'description': 'phase3 concurrency updated'}
    first = authenticated_client.post(f'/edit_t/{tx_id}', data=update, headers={**JSON_HEADERS, 'If-Match': f'"{original_version}"'})
    assert first.status_code == 200
    assert first.get_json()['success'] is True
    stale = authenticated_client.post(f'/edit_t/{tx_id}', data=update, headers={**JSON_HEADERS, 'If-Match': f'"{original_version}"'})
    assert stale.status_code in (200, 302, 409)
    assert stale.get_json()['success'] is False
    with app.app_context():
        tx = db.session.get(Transaction, tx_id)
        assert tx.version == original_version + 1
        assert tx.description == 'phase3 concurrency updated'


def test_asset_update_rejects_stale_if_match(authenticated_client, app):
    from models import Asset, AssetSector
    with app.app_context():
        sector_id = AssetSector.query.first().id
        asset = Asset(type="Hisse Senedi", name="phase3 asset", value=100, purchase_date="2026-01-01", purchase_cost=100, quantity=1, unit_price=100, currency="TRY", symbol="P3A", risk_level="Orta", liquidity="Likit", sector_id=sector_id, tenant_id="default")
        db.session.add(asset)
        db.session.commit()
        asset_id, original_version = asset.id, asset.version
    payload = {"asset_id": str(asset_id), "type": "Hisse Senedi", "name": "phase3 asset", "quantity": "2", "unit_price": "125", "purchase_cost": "100", "currency": "TRY", "symbol": "P3A", "risk_level": "Orta", "liquidity": "Likit"}
    first = authenticated_client.post("/update_asset", data=payload, headers={**JSON_HEADERS, "If-Match": str(original_version)})
    assert first.status_code in (200, 302)
    stale = authenticated_client.post("/update_asset", data=payload, headers={**JSON_HEADERS, "If-Match": str(original_version)})
    assert stale.status_code in (200, 302, 409)
    if stale.is_json:
        assert stale.get_json()["success"] is False
    with app.app_context():
        asset = db.session.get(Asset, asset_id)
        assert asset.version == original_version + 1
        assert float(asset.value) == 250.0


def test_plan_update_is_atomic_and_versioned(app):
    import pytest

    from domain.transactions.services import OptimisticConcurrencyError
    from models import RecurringPlan, Transaction
    from repositories.financial_repository import FinancialRepository
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan("phase3 plan", "Maaş", 100, 2, 1, tenant_id="default", plan_type="Taksit", frequency="Aylık", status="Aktif")
        plan_id, original_version = plan.id, plan.version
        generated = Transaction.query.filter_by(source_id=plan_id, source_type="plan", tenant_id="default").all()
        assert len(generated) == 2
        repo.update_recurring_plan(plan_id, "phase3 plan updated", "Maaş", 125, 2, 1, tenant_id="default", version=original_version)
        refreshed = db.session.get(RecurringPlan, plan_id)
        assert refreshed.version == original_version + 1
        pending = Transaction.query.filter_by(source_id=plan_id, source_type="plan", tenant_id="default", status="Bekliyor").all()
        assert len(pending) == 2
        with pytest.raises(OptimisticConcurrencyError):
            repo.update_recurring_plan(plan_id, "stale", "Maaş", 130, 2, 1, tenant_id="default", version=original_version)

def test_plan_delete_soft_deletes_pending_generated_transactions(app):
    from domain.transactions.services import delete_recurring_plan
    from models import Transaction
    from repositories.financial_repository import FinancialRepository
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan("phase3 delete plan", "Maaş", 90, 2, 1, tenant_id="default", plan_type="Taksit", frequency="Aylık", status="Aktif")
        plan_id = plan.id
        generated_ids = [tx.id for tx in Transaction.query.filter_by(source_id=plan_id, source_type="plan", tenant_id="default").all()]
        assert generated_ids
        result = delete_recurring_plan(plan_id, tenant_id="default")
        assert result["success"] is True
        remaining = Transaction.query.filter(Transaction.id.in_(generated_ids)).all()
        assert remaining
        assert all(tx.is_deleted for tx in remaining)
