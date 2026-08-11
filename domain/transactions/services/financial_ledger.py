"""
Birleşik Finans Defteri Servisi
================================
Nakit akışı, planlı gelir/gider ve varlık yönetimini aynı mimaride birleştirir.

Katmanlar:
  Pozisyon  → RecurringPlan (gelecek nakit) | Asset (portföy pozisyonu)
  Olay      → Transaction (nakit hareketi)  | AssetUpdate (değerleme)
  Köprü     → source_type='plan' | source_type='asset'
"""

from shared.decimal_precision import to_decimal

from datetime import datetime

from database import add_transaction, log_asset_update
from models import Asset, AssetUpdate, Category, RecurringPlan, Transaction, db

# Varlık pozisyonuna bağlı nakit işlemi kaynak tipleri
ASSET_LINKED_SOURCE_TYPES = ('asset', 'asset_sale', 'asset_dividend', 'asset_interest')
# Silme sonrası kasada korunacak (yalnızca bağ koparılır) kaynak tipleri
PRESERVE_CASH_SOURCE_TYPES = ('asset_sale', 'asset_dividend', 'asset_interest')


class LedgerError(ValueError):
    """Defter işlemi doğrulama hatası."""


def _validate_asset_amounts(quantity, unit_price, purchase_cost=None):
    if quantity <= 0:
        raise LedgerError("Miktar sıfırdan büyük olmalıdır.")
    if unit_price < 0:
        raise LedgerError("Birim fiyat negatif olamaz.")
    value = quantity * unit_price
    if value < 0:
        raise LedgerError("Varlık değeri negatif olamaz.")
    if purchase_cost is not None and purchase_cost < 0:
        raise LedgerError("Alış maliyeti negatif olamaz.")
    return value


def parse_asset_payload(form):
    """Form verisinden varlık alanlarını çıkarır (route'lar için ortak parser)."""
    quantity = to_decimal(form.get('quantity', 1) or 1)
    unit_price = to_decimal(form.get('unit_price', 0) or 0)
    purchase_cost = to_decimal(form.get('purchase_cost', 0) or 0)
    value = _validate_asset_amounts(quantity, unit_price, purchase_cost)

    sector_raw = form.get('sector_id', '').strip()
    sector_id = int(sector_raw) if sector_raw else None

    monthly_rent = None
    if form.get('monthly_rent'):
        monthly_rent = to_decimal(form.get('monthly_rent', 0) or 0)

    return {
        'type': form.get('type', '').strip(),
        'name': form.get('name', '').strip(),
        'value': value,
        'description': (form.get('description', '') or '').strip() or None,
        'purchase_date': (form.get('purchase_date', '') or '').strip(),
        'purchase_cost': purchase_cost or value,
        'quantity': quantity,
        'unit_price': unit_price,
        'currency': (form.get('currency', 'TRY') or 'TRY').strip(),
        'symbol': (form.get('symbol', '') or '').strip(),
        'risk_level': (form.get('risk_level', 'Orta') or 'Orta').strip(),
        'liquidity': (form.get('liquidity', 'Likit') or 'Likit').strip(),
        'sector_id': sector_id,
        'monthly_rent': monthly_rent,
        'notes': (form.get('notes', '') or '').strip() or None,
        'sync_cash': 'sync_cash' in form and form.get('sync_cash') in ('on', 'true', '1', True),
    }


def _investment_category(asset_type=None):
    if asset_type:
        asset_type = asset_type.strip()
        asset_category = Category.query.filter_by(name=asset_type, type='Yatırım').first()
        if asset_category:
            return asset_category

    fallback = Category.query.filter_by(name='Yatırıma Aktarılan', type='Yatırım').first()
    if fallback:
        return fallback

    # Yatırım kategorisi yoksa uygulama içinde otomatik oluştur
    fallback = Category(name='Yatırıma Aktarılan', type='Yatırım')
    db.session.add(fallback)
    db.session.flush()
    return fallback


def _create_purchase_transaction(asset, purchase_date, amount, user_note=None, tenant_id=None):
    """Varlık alımını nakit defterine yansıtır (Yatırım tipi işlem)."""
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    cat = _investment_category(asset.type)
    if amount <= 0:
        return None

    purchase_label = f"{asset.type} Alımı" if asset.type else "Varlık Alımı"
    note = user_note or f"{purchase_label.lower()}: {asset.name}"
    tx = Transaction(
        date=purchase_date or datetime.now().strftime('%Y-%m-%d'),
        category=cat.name,
        description=f"{purchase_label} — {asset.name}",
        note=note,
        type='Yatırım',
        amount=amount,
        status='Ödendi',
        source_id=asset.id,
        source_type='asset',
        tenant_id=tenant_id,
    )
    db.session.add(tx)
    return tx

def _create_buy_asset_transaction(asset, quantity, unit_price, cost, p_date, tenant_id=None):
    """Varlık defterine 'buy' kaydı atar."""
    from flask import g

    from models import AssetTransaction
    tenant_id = tenant_id or g.get('tenant_id')

    atx = AssetTransaction(
        asset_id=asset.id,
        transaction_type='buy',
        quantity=quantity,
        unit_price=unit_price,
        total_cost=cost,
        transaction_date=p_date,
        notes='Yeni varlık alımı',
        tenant_id=tenant_id
    )
    db.session.add(atx)
    return atx

def _create_sale_transaction(asset, sale_date, amount, realized_gain=None, user_note=None, tenant_id=None):
    """Varlık satışını nakit defterine yansıtır.
    
    Dünya standartları (QuickBooks, Xero, TDMS 16) ile uyumlu:
    - Satış tutarı her zaman Gelir olarak girilir (gerçek nakit girişi)
    - Ayrıca realized_gain bilgisi nota eklenir
    - Negatif gerçekleşen kar (zarar) durumu nota yansıtılır
    """
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    if amount <= 0:
        return None

    # Satış tutarı her zaman nakit girişi (Gelir) olarak kaydedilir
    # Gerçek kar/zarar ayrımı realized_gain ile notta belirtilir
    cat = Category.query.filter_by(name='Yatırım Geliri', type='Gelir').first()
    if not cat:
        cat = Category(name='Yatırım Geliri', type='Gelir')
        db.session.add(cat)
        db.session.flush()

    gain_info = ''
    if realized_gain is not None:
        rg_dec = to_decimal(realized_gain)
        if rg_dec >= 0:
            gain_info = f" | Kar: {rg_dec:,.2f} ₺"
        else:
            gain_info = f" | Zarar: {rg_dec:,.2f} ₺"

    base_note = user_note or f"Varlık satışı: {asset.name}"
    note = f"{base_note}{gain_info}"

    tx = Transaction(
        date=sale_date or datetime.now().strftime('%Y-%m-%d'),
        category=cat.name,
        description=f"Varlık Satışı — {asset.name}",
        note=note,
        type='Gelir',
        amount=amount,
        status='Ödendi',
        source_id=asset.id,
        source_type='asset_sale',
        tenant_id=tenant_id,
    )
    db.session.add(tx)
    return tx


def create_asset_position(user_id=None, tenant_id=None, **fields):
    """
    Yeni portföy pozisyonu oluşturur.
    Nakit akışına yansıtma seçeneğiyle bağlı Yatırım işlemi üretir.
    İlk değerleme kaydını AssetUpdate olarak tutar.
    
    sync_cash=True (varsayılan): Varlık alımı kasadan nakit çıkışı olarak kaydedilir.
    sync_cash=False: Sadece varlık defteri güncellenir, nakit işlemi oluşturulmaz.
    (QuickBooks/Xero'daki 'banka hesabından alım' mantığına eşdeğer)
    """
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    # BUG FIX: sync_cash'i doğru şekilde oku (önceden her zaman True varsayılıyordu)
    sync_cash = fields.pop('sync_cash', True)
    is_admin_generated = fields.pop('is_admin_generated', False)
    if not fields.get('name'):
        raise LedgerError("Varlık adı zorunludur.")
    if not fields.get('type'):
        raise LedgerError("Varlık türü zorunludur.")

    today = datetime.now().strftime('%Y-%m-%d')
    asset = Asset(
        type=fields['type'],
        name=fields['name'],
        value=fields['value'],
        description=fields.get('description'),
        purchase_date=fields.get('purchase_date') or today,
        purchase_cost=fields.get('purchase_cost') or fields['value'],
        quantity=fields['quantity'],
        unit_price=fields['unit_price'],
        currency=fields.get('currency') or 'TRY',
        symbol=fields.get('symbol') or fields['name'][:20],
        risk_level=fields.get('risk_level') or 'Orta',
        liquidity=fields.get('liquidity') or 'Likit',
        sector_id=fields.get('sector_id'),
        monthly_rent=fields.get('monthly_rent'),
        notes=fields.get('notes'),
        last_updated=today,
        is_admin_generated=is_admin_generated,
        tenant_id=tenant_id,
    )
    db.session.add(asset)
    db.session.flush()

    _create_buy_asset_transaction(
        asset,
        fields['quantity'],
        fields['unit_price'],
        asset.purchase_cost,
        asset.purchase_date,
        tenant_id
    )

    log_asset_update(
        asset_id=asset.id,
        old_value=0,
        new_value=asset.value,
        old_unit_price=0,
        new_unit_price=asset.unit_price,
        update_type='initial',
        notes='Pozisyon açılışı',
        user_id=user_id,
        auto_commit=False,
    )

    # BUG FIX: sync_cash=False ise nakit işlemi oluşturma
    # (Önceden bu kontrol yoktu ve her zaman nakit işlemi oluşturuluyordu)
    if sync_cash:
        _create_purchase_transaction(
            asset,
            asset.purchase_date,
            asset.purchase_cost,
            fields.get('notes'),
            tenant_id,
        )

    db.session.commit()
    return asset


def sell_asset_position(asset_id, quantity, sale_unit_price, sale_date=None, note=None, user_id=None, tenant_id=None):
    """
    Varlık kısmi veya tam satışı.
    1. AssetTransaction (sell) kaydı oluşturur
    2. Asset.quantity ve Asset.value günceller
    3. Transaction (Gelir) ile satış tutarını kasaya ekler
    4. Miktar 0'a düşerse Asset.is_closed = True
    """
    from flask import g

    from models import AssetTransaction
    tenant_id = tenant_id or g.get('tenant_id')

    asset = db.session.get(Asset, asset_id)
    if not asset or asset.tenant_id != tenant_id:
        raise LedgerError("Varlık bulunamadı veya yetkisiz erişim.")

    if asset.is_closed:
        raise LedgerError("Bu varlık zaten kapatılmış (tamamen satılmış).")

    if quantity <= 0 or quantity > asset.quantity:
        raise LedgerError(f"Geçersiz satış miktarı. (Mevcut miktar: {asset.quantity})")

    if sale_unit_price < 0:
        raise LedgerError("Satış fiyatı 0'dan küçük olamaz.")

    sale_date = sale_date or datetime.now().strftime('%Y-%m-%d')
    quantity_dec = to_decimal(quantity)
    sale_unit_price_dec = to_decimal(sale_unit_price)
    total_sale_amount = quantity_dec * sale_unit_price_dec

    # 1. AssetTransaction (sell) kaydı
    atx = AssetTransaction(
        asset_id=asset.id,
        transaction_type='sell',
        quantity=quantity_dec,
        unit_price=sale_unit_price_dec,
        total_cost=total_sale_amount,  # Satış için bu satış bedelidir
        transaction_date=sale_date,
        notes=note or 'Kısmi / Tam Satış',
        tenant_id=tenant_id
    )
    db.session.add(atx)

    # Gerçekleşen kar/zarar hesabı = Satış Bedeli - (Satılan Miktar * WAC)
    wac = to_decimal(asset.weighted_average_cost)
    realized_gain = total_sale_amount - (quantity_dec * wac)

    # 2. Asset Güncellemesi
    asset.quantity = to_decimal(asset.quantity) - quantity_dec
    asset.value = asset.quantity * to_decimal(asset.unit_price) # Geriye kalan değer
    asset.last_updated = datetime.now().strftime('%Y-%m-%d')

    if asset.quantity <= to_decimal('0.0001'):  # Decimal hassasiyet payı (Decimal vs float TypeError önlendi)
        asset.quantity = to_decimal(0)
        asset.value = to_decimal(0)
        asset.is_closed = True
        asset.closed_at = sale_date

    # 3. Kasaya Nakit Girişi (satış tutarı gelir, kar/zarar bilgisi nota yazılır)
    sale_tx = _create_sale_transaction(
        asset=asset,
        sale_date=sale_date,
        amount=total_sale_amount,
        realized_gain=realized_gain,
        user_note=note,
        tenant_id=tenant_id
    )

    db.session.commit()
    return asset, realized_gain, sale_tx


def update_asset_valuation(asset_id, user_id=None, tenant_id=None, preserve_purchase_cost=True, **fields):
    """
    Varlık pozisyonunu günceller ve değerleme olayını kaydeder.
    purchase_cost korunur (maliyet bazı değişmez).
    """
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return None

    old_value = asset.value
    old_unit_price = asset.unit_price

    asset.type = fields.get('type', asset.type)
    asset.name = fields.get('name', asset.name)
    asset.value = fields['value']
    asset.description = fields.get('description', asset.description)
    asset.purchase_date = fields.get('purchase_date') or asset.purchase_date
    if not preserve_purchase_cost and 'purchase_cost' in fields:
        asset.purchase_cost = fields['purchase_cost']
    asset.quantity = fields['quantity']
    asset.unit_price = fields['unit_price']
    asset.currency = fields.get('currency', asset.currency)
    asset.symbol = fields.get('symbol', asset.symbol)
    asset.risk_level = fields.get('risk_level', asset.risk_level)
    asset.liquidity = fields.get('liquidity', asset.liquidity)
    if fields.get('sector_id'):
        asset.sector_id = fields['sector_id']
    asset.monthly_rent = fields.get('monthly_rent', asset.monthly_rent)
    asset.notes = fields.get('notes', asset.notes)
    asset.last_updated = datetime.now().strftime('%Y-%m-%d')

    if old_value != asset.value or old_unit_price != asset.unit_price:
        log_asset_update(
            asset_id=asset.id,
            old_value=old_value,
            new_value=asset.value,
            old_unit_price=old_unit_price,
            new_unit_price=asset.unit_price,
            update_type='manual',
            user_id=user_id,
            auto_commit=False,
        )

    db.session.commit()
    return asset


def _detach_asset_ledger_references(asset_id, tenant_id=None):
    """
    Varlık silinmeden önce bağlı referansları güvenli şekilde koparır.
    LogbookEntry ve Payment FK kısıtları commit hatasını önler.
    """
    from models import LogbookEntry, Payment

    LogbookEntry.query.filter_by(asset_id=asset_id).update(
        {LogbookEntry.asset_id: None},
        synchronize_session=False,
    )

    tx_query = Transaction.query.filter(
        Transaction.source_id == asset_id,
        Transaction.source_type.in_(ASSET_LINKED_SOURCE_TYPES),
    )
    if tenant_id:
        tx_query = tx_query.filter_by(tenant_id=tenant_id)
    linked_transactions = tx_query.all()

    tx_ids = [tx.id for tx in linked_transactions]
    if tx_ids:
        LogbookEntry.query.filter(LogbookEntry.transaction_id.in_(tx_ids)).update(
            {LogbookEntry.transaction_id: None},
            synchronize_session=False,
        )
        Payment.query.filter(Payment.transaction_id.in_(tx_ids)).update(
            {Payment.transaction_id: None},
            synchronize_session=False,
        )

    return linked_transactions


def delete_asset_position(asset_id, tenant_id=None):
    """Pozisyonu, değerleme geçmişini ve bağlı nakit işlemlerini siler."""
    from flask import g

    from models import AssetTransaction
    tenant_id = tenant_id or g.get('tenant_id')

    query = Asset.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    asset = query.filter(Asset.id == asset_id).first()
    if not asset:
        return False

    linked_transactions = _detach_asset_ledger_references(asset_id, tenant_id)

    for tx in linked_transactions:
        if tx.source_type == 'asset':
            db.session.delete(tx)
        elif tx.source_type in PRESERVE_CASH_SOURCE_TYPES:
            tx.source_id = None
            tx.source_type = None

    for atx in AssetTransaction.query.filter_by(asset_id=asset.id).all():
        db.session.delete(atx)
    for update in AssetUpdate.query.filter_by(asset_id=asset.id).all():
        db.session.delete(update)

    db.session.delete(asset)
    db.session.commit()
    return True


def create_one_time_transaction(date, category_name, description, amount, status, note=None, tenant_id=None):
    """Tek seferlik nakit işlemi (Transaction tablosu, kaynak bağlantısı yok)."""
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    cat = Category.query.filter_by(name=category_name, tenant_id=tenant_id).first()
    if not cat:
        # Try system-level category as fallback
        cat = Category.query.filter_by(name=category_name, tenant_id=None).first()
    if not cat:
        raise LedgerError("Geçersiz kategori.")
    if amount <= 0:
        raise LedgerError("Tutar sıfırdan büyük olmalıdır.")

    tx = add_transaction(
        date, cat.name, description or cat.name, cat.type,
        amount, status, note, source_id=None, source_type='manual', tenant_id=tenant_id,
    )
    return tx


def create_recurring_plan(name, category, amount, installments, payment_day, note=None, start_date=None, tenant_id=None):
    """Planlı gelir/gider şablonu oluşturur ve işlemleri üretir."""
    from flask import g

    from database import add_recurring_plan
    tenant_id = tenant_id or g.get('tenant_id')

    if amount <= 0 or installments <= 0 or payment_day < 1 or payment_day > 31:
        raise LedgerError("Tutar, taksit sayısı ve ödeme günü geçerli olmalıdır.")
    return add_recurring_plan(name, category, amount, installments, payment_day, note, start_date, tenant_id)


def update_recurring_plan_entry(plan_id, name, category, amount, installments, payment_day, note=None, start_date=None, tenant_id=None):
    """Planı günceller ve bağlı işlemleri yeniden üretir."""
    from flask import g

    from database import update_recurring_plan
    tenant_id = tenant_id or g.get('tenant_id')

    # database.crud.update_recurring_plan tenant_id parametresi almaz;
    # tenant filtrelemesi plan_id üzerinden zaten yapılıyor.
    return update_recurring_plan(plan_id, name, category, amount, installments, payment_day, note, start_date)


def delete_recurring_plan(plan_id, tenant_id=None):
    """Planı siler: bekleyen işlemleri siler, ödenmişleri bağımsızlaştırır."""
    from flask import g

    from database import delete_plan
    tenant_id = tenant_id or g.get('tenant_id')

    query = RecurringPlan.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    plan = query.filter(RecurringPlan.id == plan_id).first()
    if not plan:
        return {'success': False, 'message': 'Plan bulunamadı.'}

    result = delete_plan(plan_id, tenant_id=tenant_id)
    if not result:
        return {'success': False, 'message': 'Plan silinirken hata oluştu.'}

    return {
        'success': True,
        'message': f'Plan silindi. {result["paid_count"]} ödenmiş işlem korundu, {result["pending_count"]} bekleyen işlem silindi.',
        'paid_count': result['paid_count'],
        'pending_count': result['pending_count']
    }


def _check_and_cleanup_plan_after_transaction_deletion(plan_id):
    """
    Transaction silme sonrası plan durumunu kontrol eder ve gerekirse temizlik yapar.
    Eğer planın tüm işlemleri silindiyse planı da siler.
    Ödenmiş işlemleri bağımsızlaştırır, bekleyenleri siler.
    """
    from database import delete_plan

    plan = db.session.get(RecurringPlan, plan_id)
    if not plan:
        return None

    # Planın kalan işlemlerini kontrol et
    remaining_txs = Transaction.query.filter_by(source_id=plan_id, source_type='plan').all()

    if not remaining_txs:
        # Tüm işlemler silindi, planı da sil
        delete_plan(plan_id, tenant_id=plan.tenant_id)
        return {
            'action': 'plan_deleted',
            'message': f'"{plan.name}" planının tüm işlemleri silindiği için plan da silindi.',
            'plan_name': plan.name
        }
    else:
        # Hala işlemler var, durumları kontrol et
        paid_count = sum(1 for tx in remaining_txs if tx.status == 'Ödendi')
        pending_count = sum(1 for tx in remaining_txs if tx.status == 'Bekliyor')

        if pending_count == 0:
            # Tüm kalan işlemler ödenmiş, planı sil ve işlemleri bağımsızlaştır
            delete_plan(plan_id, tenant_id=plan.tenant_id)
            return {
                'action': 'plan_deleted_with_paid',
                'message': f'"{plan.name}" planının tüm işlemleri ödenmiş olduğu için plan silindi ve {paid_count} işlem korundu.',
                'plan_name': plan.name,
                'paid_count': paid_count
            }
        else:
            # Hala bekleyen işlemler var, planı koru
            return {
                'action': 'plan_kept',
                'message': f'"{plan.name}" planı korundu. {paid_count} ödenmiş, {pending_count} bekleyen işlem mevcut.',
                'plan_name': plan.name,
                'paid_count': paid_count,
                'pending_count': pending_count
            }


def delete_one_time_transaction(transaction_id, tenant_id=None):
    """
    İşlemi siler ve planlı işlemse plan durumunu kontrol eder.
    Ödenmiş işlemleri bağımsızlaştırır, bekleyenleri siler.
    Planın tüm işlemleri silindiyse planı da siler.
    """
    from flask import g

    from models import Payment
    tenant_id = tenant_id or g.get('tenant_id')

    query = Transaction.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    tx = query.filter(Transaction.id == transaction_id).first()
    if not tx:
        return {'success': False, 'message': 'İşlem bulunamadı.'}

    # Asset işlemleri için koruma
    if tx.source_type == 'asset':
        raise LedgerError("Varlık alımına bağlı nakit işlemi doğrudan silinemez. Varlık kaydını silin veya varlık ekranından düzenleyin.")

    # Planlı işlem bilgilerini kaydet
    plan_id = tx.source_id if tx.source_type == 'plan' else None

    # Planlı işlemler için Payment kaydını kontrol et ve sil
    if tx.source_type == 'plan':
        payment = Payment.query.filter_by(transaction_id=tx.id).first()
        if payment:
            db.session.delete(payment)

    # İşlemi sil
    db.session.delete(tx)
    db.session.commit()

    # Planlı işlemse plan durumunu kontrol et
    if plan_id:
        plan_result = _check_and_cleanup_plan_after_transaction_deletion(plan_id)
        if plan_result:
            return {
                'success': True,
                'message': f'İşlem silindi. {plan_result["message"]}',
                'plan_action': plan_result['action'],
                'plan_name': plan_result.get('plan_name')
            }

    return {'success': True, 'message': 'İşlem silindi.'}


def update_one_time_transaction(transaction_id, date, category_name, description, amount, status, note=None, tenant_id=None):
    """Tek seferlik nakit işlemini günceller (bireysel işlem olarak günceller)."""
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    query = Transaction.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    tx = query.filter(Transaction.id == transaction_id).first()
    if not tx:
        raise LedgerError("İşlem bulunamadı.")
    if tx.source_type == 'asset':
        raise LedgerError("Varlık alımına bağlı nakit işlemi doğrudan güncellenemez. İlgili varlığı varlık ekranından düzenleyin.")

    cat = Category.query.filter_by(name=category_name).first()
    if not cat:
        raise LedgerError("Geçersiz kategori.")
    if amount <= 0:
        raise LedgerError("Tutar sıfırdan büyük olmalıdır.")

    tx.date = date
    tx.category = cat.name
    tx.description = (description or '').strip() or cat.name
    tx.note = (note or '').strip() or None
    tx.amount = amount
    tx.status = status
    tx.type = cat.type

    db.session.commit()
    return tx


def get_asset_ledger_summary(asset_id, tenant_id=None):
    """Varlık için defter özeti: değerleme sayısı ve nakit bağlantısı."""
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    query = Asset.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    asset = query.filter(Asset.id == asset_id).first()
    if not asset:
        return None
    updates = AssetUpdate.query.filter_by(asset_id=asset_id).count()
    cash_link = Transaction.query.filter_by(source_id=asset_id, source_type='asset').first()
    return {
        'asset': asset,
        'valuation_count': updates,
        'has_cash_link': cash_link is not None,
        'cash_amount': cash_link.amount if cash_link else 0,
    }


def get_asset_ledger_summaries(asset_ids, tenant_id=None):
    """Çoklu varlık için defter özetleri (N+1 problemi çözümü)."""
    from flask import g
    tenant_id = tenant_id or g.get('tenant_id')

    if not asset_ids:
        return {}

    # Tüm varlıkları tek sorguda getir
    query = Asset.query.filter(Asset.id.in_(asset_ids))
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    assets = {a.id: a for a in query.all()}

    # Tüm değerleme sayılarını tek sorguda getir
    update_counts = {}
    if assets:
        from sqlalchemy import func
        counts = db.session.query(
            AssetUpdate.asset_id,
            func.count(AssetUpdate.id)
        ).filter(
            AssetUpdate.asset_id.in_(asset_ids)
        ).group_by(AssetUpdate.asset_id).all()
        update_counts = {asset_id: count for asset_id, count in counts}

    # Tüm nakit bağlantılarını tek sorguda getir
    cash_links = {}
    if assets:
        links = Transaction.query.filter(
            Transaction.source_id.in_(asset_ids),
            Transaction.source_type == 'asset'
        ).all()
        cash_links = {link.source_id: link for link in links}

    # Sonuçları birleştir
    summaries = {}
    for asset_id in asset_ids:
        asset = assets.get(asset_id)
        if not asset:
            summaries[asset_id] = None
            continue

        summaries[asset_id] = {
            'asset': asset,
            'valuation_count': update_counts.get(asset_id, 0),
            'has_cash_link': asset_id in cash_links,
            'cash_amount': cash_links[asset_id].amount if asset_id in cash_links else 0,
        }

    return summaries


def transfer_cash_to_asset(asset_id, amount, transfer_date, note=None, tenant_id=None, skip_cash_tx=False):
    """
    Kasadan varlığa nakit transferini çift taraflı kayıt mantığıyla yapar.
    skip_cash_tx: Eğer DCA Planı gibi başka bir modül halihazırda Cash Out kaydını (Transaction) yaptıysa, 
                  ikinci bir Transaction (çifte nakit çıkışı) oluşmasını önler.
    """
    from flask import g

    from models import Transaction
    tenant_id = tenant_id or g.get('tenant_id')

    asset = db.session.get(Asset, asset_id)
    if not asset or asset.tenant_id != tenant_id:
        raise LedgerError("Varlık bulunamadı veya yetkisiz erişim.")

    if asset.is_closed:
        raise LedgerError("Kapatılmış varlıklara transfer yapılamaz.")

    # Tutar route/DTO katmanından float gelebilir; defter aritmetiği Decimal
    # olduğu için sınırda normalize edilir (aksi halde amount / unit_price
    # 'float / Decimal' TypeError verir).
    amount = to_decimal(amount)

    if amount <= 0:
        raise LedgerError("Transfer tutarı sıfırdan büyük olmalıdır.")

    cat = _investment_category(asset.type)
    purchase_label = f"{asset.type} Alımı" if asset.type else "Varlık Alımı"
    description = f"{purchase_label} — {asset.name}"

    # 1. Nakit çıkış kaydı (Transaction)
    if not skip_cash_tx:
        tx = Transaction(
            date=transfer_date or datetime.now().strftime('%Y-%m-%d'),
            category=cat.name,
            description=description,
            note=note,
            type='Yatırım',
            amount=amount,
            status='Ödendi',
            source_id=asset.id,
            source_type='asset',
            tenant_id=tenant_id,
        )
        db.session.add(tx)

    # 2. Varlık defter kaydı (AssetTransaction)
    unit_price = asset.unit_price if asset.unit_price > 0 else amount
    purchased_qty = amount / unit_price if unit_price > 0 else to_decimal(1)

    _create_buy_asset_transaction(
        asset=asset,
        quantity=purchased_qty,
        unit_price=unit_price,
        cost=amount,
        p_date=transfer_date,
        tenant_id=tenant_id
    )

    # 3. Varlık değer güncellemesi (Önce eski değeri sakla)
    old_value = asset.value

    asset.quantity += purchased_qty
    asset.value = asset.quantity * asset.unit_price

    # 4. Değerleme güncelleme kaydı
    log_asset_update(
        asset_id=asset.id,
        old_value=old_value,
        new_value=asset.value,
        old_unit_price=asset.unit_price,
        new_unit_price=asset.unit_price,
        update_type='transfer',
        notes=note or 'Nakit transferi',
        auto_commit=False
    )

    db.session.commit()
    return asset, tx

