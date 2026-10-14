"""
Comprehensive E-to-E Flow Tests for Income, Expense, Investment & Category Management
Verifies full CRUD interactions, Category v2 integration, and financial ledger integrity.
"""

from models import Asset, AssetSector, Transaction, db


def test_income_expense_transaction_crud_flow(app, authenticated_client):
    """Gelir ve Gider ekleme, güncelleme ve silme akışı testi"""
    # 1. Gelir İşlemi Ekleme (POST /new_transaction)
    res_income = authenticated_client.post('/new_transaction', data={
        'date': '05/08/2026',
        'category': 'Maaş',
        'type': 'Gelir',
        'amount': '35000.00',
        'description': 'Ağustos Maaş Ödemesi',
        'status': 'Ödendi',
        'note': 'Banka transferi'
    }, follow_redirects=True)
    assert res_income.status_code == 200

    tx_income = Transaction.query.filter_by(description='Ağustos Maaş Ödemesi').first()
    assert tx_income is not None
    assert float(tx_income.amount) == 35000.00
    assert tx_income.type == 'Gelir'
    assert tx_income.date == '2026-08-05'

    # 2. Gider İşlemi Ekleme (POST /new_transaction)
    res_expense = authenticated_client.post('/new_transaction', data={
        'date': '05/08/2026',
        'category': 'Aylık Sabit Gider',
        'type': 'Gider',
        'amount': '4500.00',
        'description': 'Ev Kirası ve Fatura',
        # Bekleyen kayıt düzenlenebilir; Ödendi kayıtlar immutable’dır.
        'status': 'Bekliyor',
        'note': 'Kira'
    }, follow_redirects=True)
    assert res_expense.status_code == 200

    tx_expense = Transaction.query.filter_by(description='Ev Kirası ve Fatura').first()
    assert tx_expense is not None
    expense_id = tx_expense.id
    assert float(tx_expense.amount) == 4500.00
    assert tx_expense.type == 'Gider'

    # 3. İşlem Güncelleme (POST /edit_t/<id>)
    res_update = authenticated_client.post(f'/edit_t/{expense_id}', data={
        'date': '2026-08-05',
        'category': 'Aylık Sabit Gider',
        'amount': '4800.00',
        'description': 'Ev Kirası Güncellendi',
        'status': 'Bekliyor'
    }, follow_redirects=True)
    assert res_update.status_code == 200

    updated_tx = db.session.get(Transaction, expense_id)
    assert float(updated_tx.amount) == 4800.00
    assert updated_tx.description == 'Ev Kirası Güncellendi'

    # 4. İşlem Silme - GET reddedilmeli (405 Method Not Allowed), sadece POST kabul edilmeli
    assert authenticated_client.get(f'/delete_t/{expense_id}').status_code == 405
    res_delete = authenticated_client.post(f'/delete_t/{expense_id}', follow_redirects=True)
    assert res_delete.status_code == 200
    assert db.session.get(Transaction, expense_id) is None or db.session.get(Transaction, expense_id).is_deleted


def test_investment_asset_and_cash_sync_flow(app, authenticated_client):
    """Yatırım ve Nakit Senkronizasyonu Alım/Satım Akışı Testi (Kar ve Zarar Senaryoları)"""
    sector = AssetSector.query.first()
    sector_id = sector.id if sector else 1

    # 1. Yeni Varlık Alımı (POST /new_asset, sync_cash=on)
    res_asset = authenticated_client.post('/new_asset', data={
        'type': 'Hisse Senedi',
        'name': 'GARAN Hisse',
        'quantity': '50',
        'unit_price': '80.00',
        'purchase_cost': '4000.00',
        'symbol': 'GARAN',
        'currency': 'TRY',
        'risk_level': 'Orta',
        'liquidity': 'Likit',
        'sector_id': str(sector_id),
        'purchase_date': '2026-08-01',
        'sync_cash': 'on'
    }, follow_redirects=True)
    assert res_asset.status_code == 200

    asset = Asset.query.filter_by(name='GARAN Hisse').first()
    assert asset is not None
    assert float(asset.value) == 4000.00

    # Yatırım Alımında Otomatik Nakit Çıkışı (Transaction) Oluşmalı
    tx_asset = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    assert tx_asset is not None
    assert float(tx_asset.amount) == 4000.00
    assert tx_asset.type == 'Yatırım'

    asset_id = asset.id

    # 2. Varlık Satışı - Kar Eden Satış (POST /sell_asset/<id>)
    # 50 adetten 20 adet 95 TL'den satılıyor (Birim maliyet: 80 TL -> Kar: 15 TL/adet)
    res_sell_profit = authenticated_client.post(f'/sell_asset/{asset_id}', data={
        'quantity': '20',
        'sale_unit_price': '95.00',
        'sale_date': '2026-08-05',
        'note': 'Kısmi kar satışı'
    }, follow_redirects=True)
    assert res_sell_profit.status_code == 200

    # Kısmi satış sonrası kalan miktar 30 olmalı
    refreshed_asset = db.session.get(Asset, asset_id)
    assert float(refreshed_asset.quantity) == 30.0

    # Satış Nakit Girişi İşlemi (Transaction) Oluşmalı
    sale_tx = Transaction.query.filter_by(source_id=asset_id, source_type='asset_sale').first()
    assert sale_tx is not None
    assert float(sale_tx.amount) == 1900.00  # 20 * 95.00
    assert 'Kar:' in sale_tx.note

    # 3. Varlık Satışı - Zarar Eden Satış (POST /sell_asset/<id>)
    # Kalan 30 adetten 10 adet 60 TL'den satılıyor (Birim maliyet: 80 TL -> Zarar: -20 TL/adet)
    res_sell_loss = authenticated_client.post(f'/sell_asset/{asset_id}', data={
        'quantity': '10',
        'sale_unit_price': '60.00',
        'sale_date': '2026-08-05',
        'note': 'Zarar kes satışı'
    }, follow_redirects=True)
    assert res_sell_loss.status_code == 200

    loss_txs = Transaction.query.filter_by(source_id=asset_id, source_type='asset_sale').all()
    assert len(loss_txs) == 2
    latest_sale_tx = loss_txs[-1]
    assert float(latest_sale_tx.amount) == 600.00  # 10 * 60.00
    assert 'Zarar:' in latest_sale_tx.note


def test_asset_creation_without_cash_sync(app, authenticated_client):
    """sync_cash=False olduğunda nakit işlemi oluşturulmama testi (BUG FIX DOĞRULAMASI)"""
    sector = AssetSector.query.first()
    sector_id = sector.id if sector else 1

    res = authenticated_client.post('/new_asset', data={
        'type': 'Gayrimenkul',
        'name': 'Yatırımlık Arsa',
        'quantity': '1',
        'unit_price': '500000.00',
        'purchase_cost': '500000.00',
        'symbol': 'ARSA01',
        'currency': 'TRY',
        'risk_level': 'Düşük',
        'liquidity': 'Düşük',
        'sector_id': str(sector_id),
        'purchase_date': '2026-08-01',
        # sync_cash gönderilmiyor (yani False)
    }, follow_redirects=True)
    assert res.status_code == 200

    asset = Asset.query.filter_by(name='Yatırımlık Arsa').first()
    assert asset is not None
    assert float(asset.value) == 500000.00

    # sync_cash=False olduğu için Nakit İşlemi (Transaction) OLUSMAMALI
    tx_asset = Transaction.query.filter_by(source_id=asset.id, source_type='asset').first()
    assert tx_asset is None  # ✅ FIX VERIFIED



