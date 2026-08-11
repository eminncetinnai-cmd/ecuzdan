"""
Admin demo veri üretici — 12 aylık kapsamlı finans defteri simülasyonu.
Tek seferlik işlemler, planlı gelir/gider, varlık pozisyonları ve değerlemeler.
"""

import calendar
import random
from datetime import datetime

from database import delete_plan
from domain.transactions.services.financial_ledger import create_asset_position, create_recurring_plan
from models import Asset, AssetSector, AssetUpdate, Category, RecurringPlan, Transaction, db
from shared.decimal_precision import to_decimal

ADMIN_NOTE = 'Admin otomatik veri — demo'
ADMIN_DESC_PREFIX = '[Admin Demo]'


def _today_str():
    return datetime.now().strftime('%Y-%m-%d')


def _tx_status(date_str):
    return 'Bekliyor' if date_str > _today_str() else 'Ödendi'


def _month_day(year, month, day):
    last = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-{min(day, last):02d}"


def clear_admin_demo_data():
    """Admin tarafından oluşturulan tüm demo verileri temizler."""
    admin_asset_ids = [
        a.id for a in Asset.query.filter(
            db.or_(Asset.is_admin_generated.is_(True), Asset.notes.ilike('%Admin%'))
        ).all()
    ]
    if admin_asset_ids:
        AssetUpdate.query.filter(AssetUpdate.asset_id.in_(admin_asset_ids)).delete(synchronize_session=False)
        Transaction.query.filter(
            Transaction.source_type == 'asset',
            Transaction.source_id.in_(admin_asset_ids),
        ).delete(synchronize_session=False)
        Asset.query.filter(Asset.id.in_(admin_asset_ids)).delete(synchronize_session=False)

    # tenant_id açıkça geçilir: bu fonksiyon request context dışında da çalışır.
    for plan in RecurringPlan.query.filter(RecurringPlan.note.ilike('%Admin%')).all():
        delete_plan(plan.id, tenant_id=plan.tenant_id)

    legacy_plan_names = ['Maaş Planı', 'Konut Kirası', 'Konut Kredisi', 'Kredi Kartı Limit', 'Kira Geliri Planı']
    for name in legacy_plan_names:
        plan = RecurringPlan.query.filter_by(name=name).first()
        if plan:
            delete_plan(plan.id, tenant_id=plan.tenant_id)

    deleted_tx = Transaction.query.filter(
        db.or_(
            Transaction.is_admin_generated.is_(True),
            Transaction.note.ilike('%Admin%'),
            Transaction.description.like(f'{ADMIN_DESC_PREFIX}%'),
        )
    ).delete(synchronize_session=False)

    db.session.commit()
    return {
        'transactions': deleted_tx,
        'assets': len(admin_asset_ids),
    }


def _add_one_time_tx(year, month, day, category, type_, description, amount, status=None):
    date_str = _month_day(year, month, day)
    status = status or _tx_status(date_str)
    exists = Transaction.query.filter_by(
        date=date_str, category=category, description=description, type=type_,
    ).first()
    if exists:
        return False
    db.session.add(Transaction(
        date=date_str,
        category=category,
        description=description,
        note=ADMIN_NOTE,
        type=type_,
        status=status,
        amount=to_decimal(amount),
        source_id=None,
        source_type=None,
        is_admin_generated=True,
        tenant_id='default'
    ))
    return True


def _seed_one_time_transactions(year):
    created = 0
    income_rows = [
        (5, 'Maaş / Ücret Geliri', 'Gelir', 'Aylık maaş ödemesi', 28500, None),
        (15, 'Ek Gelir / Diğer Gelirler', 'Gelir', 'Ek proje geliri', 3500, None),
        (1, 'Kira Geliri', 'Gelir', 'Kira geliri', 7500, None),
    ]
    expense_rows = [
        (3, 'Kira', 'Gider', 'Konut kirası', 8500, None),
        (10, 'Diğer Giderler', 'Gider', 'Market alışverişi', 4200, None),
        (12, 'Kredi Kartı Ödemesi', 'Gider', 'Kredi kartı ödemesi', 2800, None),
        (18, 'Diğer Giderler', 'Gider', 'Vergi / SGK kesintisi', 1500, None),
        (22, 'Kredi Ödemeleri', 'Gider', 'Banka kredisi taksiti', 5500, None),
    ]
    investment_rows = [
        (8, 'Nakit & Mevduat', 'Yatırım', 'Aylık portföy aktarımı', 4000, None),
    ]

    for month in range(1, 13):
        for day, cat, typ, desc, base, forced_status in income_rows:
            if cat == 'Ek Gelir / Diğer Gelirler' and month % 2 != 0:
                continue
            amt = base + random.randint(-400, 400)
            if _add_one_time_tx(year, month, day, cat, typ, f'{ADMIN_DESC_PREFIX} {desc}', amt, forced_status):
                created += 1
        for day, cat, typ, desc, base, forced_status in expense_rows:
            amt = base + random.randint(-250, 250)
            if _add_one_time_tx(year, month, day, cat, typ, f'{ADMIN_DESC_PREFIX} {desc}', amt, forced_status):
                created += 1
        for day, cat, typ, desc, base, forced_status in investment_rows:
            amt = base + random.randint(-300, 300)
            if _add_one_time_tx(year, month, day, cat, typ, f'{ADMIN_DESC_PREFIX} {desc}', amt, forced_status):
                created += 1

    db.session.commit()
    return created


def _seed_recurring_plans(year):
    created = 0
    templates = [
        ('Maaş Planı', 'Maaş / Ücret Geliri', 30000, 12, 1, f'{year} Admin — düzenli maaş'),
        ('Kira Geliri Planı', 'Kira Geliri', 8000, 12, 1, f'{year} Admin — kira geliri'),
        ('Konut Kirası', 'Kira', 8500, 12, 3, f'{year} Admin — konut kirası'),
        ('Konut Kredisi', 'Kredi Ödemeleri', 5500, 12, 10, f'{year} Admin — konut kredisi'),
        ('Kredi Kartı Limit', 'Kredi Kartı Ödemesi', 2500, 12, 15, f'{year} Admin — kart ödemesi'),
    ]
    for name, cat, amount, inst, pay_day, note in templates:
        if not RecurringPlan.query.filter_by(name=name).first():
            create_recurring_plan(name, cat, amount, inst, pay_day, note, tenant_id='default')
            created += 1
    return created


def _get_or_create_sector(name):
    sec = AssetSector.query.filter_by(name=name).first()
    if not sec:
        sec = AssetSector(name=name)
        db.session.add(sec)
        db.session.flush()
    return sec


def _seed_assets(year):
    created = 0
    valuations = 0
    sectors = {
        'Teknoloji': _get_or_create_sector('Teknoloji'),
        'Bankacılık': _get_or_create_sector('Bankacılık'),
        'Emtia & Hammadde': _get_or_create_sector('Emtia & Hammadde'),
        'Finansal Sistem': _get_or_create_sector('Finansal Sistem'),
        'Gayrimenkul & Fiziksel Varlıklar': _get_or_create_sector('Gayrimenkul & Fiziksel Varlıklar'),
    }

    samples = [
        ('Hisse Senedi', 'Türk Hava Yolları', 'THYAO', 'Teknoloji', f'{year}-01-10', 100, 285, 'TRY', 'Orta', 'Likit'),
        ('Hisse Senedi', 'Garanti BBVA', 'GARAN', 'Bankacılık', f'{year}-02-15', 500, 95, 'TRY', 'Orta', 'Likit'),
        ('Altın', 'Gram Altın', 'XAU', 'Emtia & Hammadde', f'{year}-03-01', 50, 2450, 'TRY', 'Düşük', 'Likit'),
        ('Kripto', 'Bitcoin', 'BTC', 'Finansal Sistem', f'{year}-04-20', 0.15, 2800000, 'TRY', 'Yüksek', 'Likit'),
        ('Fon', 'BIST 100 Fonu', 'BIST100', 'Finansal Sistem', f'{year}-05-05', 1000, 12.5, 'TRY', 'Orta', 'Yarı-Likit'),
        ('BES', 'Emeklilik Fonu', 'BES01', 'Finansal Sistem', f'{year}-06-01', 1, 85000, 'TRY', 'Düşük', 'İlik'),
        ('Gayrimenkul', 'Arsa Payı', 'ARSA1', 'Gayrimenkul & Fiziksel Varlıklar', f'{year}-07-01', 1, 450000, 'TRY', 'Orta', 'İlik'),
        ('Nakit', 'Döviz Rezervi', 'USD', 'Finansal Sistem', f'{year}-08-15', 2000, 34.5, 'TRY', 'Düşük', 'Likit'),
    ]

    for atype, aname, sym, sec_name, pdate, qty, price, cur, risk, liq in samples:
        if Asset.query.filter_by(name=aname).first():
            continue
        sector = sectors[sec_name]
        pcost = qty * price
        asset = create_asset_position(
            type=atype, name=aname, value=pcost,
            description=f'{ADMIN_DESC_PREFIX} {aname}',
            purchase_date=pdate, purchase_cost=pcost,
            quantity=qty, unit_price=price, currency=cur,
            symbol=sym, risk_level=risk, liquidity=liq,
            sector_id=sector.id, notes=ADMIN_NOTE,
            is_admin_generated=True,
            tenant_id='default'
        )
        created += 1

        growth_steps = [1.0, 1.04, 1.09, 1.12]
        for i, mult in enumerate(growth_steps[1:], start=1):
            m = ((int(pdate[5:7]) - 1 + i * 3) % 12) + 1
            vdate = _month_day(year, m, 28)
            old_val = pcost * growth_steps[i - 1]
            new_val = pcost * mult
            new_price = price * mult
            db.session.add(AssetUpdate(
                asset_id=asset.id,
                old_value=old_val,
                new_value=new_val,
                old_unit_price=price * growth_steps[i - 1],
                new_unit_price=new_price,
                update_type='manual',
                notes=f'{ADMIN_NOTE} — çeyreklik değerleme',
                updated_at=datetime.strptime(vdate, '%Y-%m-%d'),
            ))
            valuations += 1
        asset.value = pcost * growth_steps[-1]
        asset.unit_price = price * growth_steps[-1]
        asset.last_updated = _today_str()

    db.session.commit()
    return created, valuations


def _ensure_demo_categories():
    """Demo veri için gerekli kategorilerin varlığını garanti eder.
    NOT: Bu fonksiyon yeni kategori oluşturmaz, sadece standart kategorileri kullanır.
    """
    # Standart kategoriler zaten sistemde var (tenant_id=None)
    # Ekstra kategori oluşturma, sadece mevcutları kontrol et
    standard_categories = Category.query.filter_by(tenant_id=None).all()
    print(f"  {len(standard_categories)} standart kategori kullanılıyor.")


def generate_admin_demo_data(year=None):
    """
    12 aylık kapsamlı demo veri seti oluşturur.
    Döner: özet istatistik sözlüğü
    """
    year = year or datetime.now().year
    
    # Use new professional architecture
    from infrastructure.demo.demo_data_orchestrator import DemoDataOrchestrator
    
    orchestrator = DemoDataOrchestrator(tenant_id='default')
    stats = orchestrator.generate_comprehensive_demo_data(
        start_year=year,
        end_year=year,
        is_admin_generated=True
    )
    
    # Get additional statistics
    plan_tx_count = Transaction.query.filter_by(source_type='plan').count()
    pending_count = Transaction.query.filter(
        Transaction.is_admin_generated.is_(True),
        Transaction.status == 'Bekliyor',
    ).count()
    paid_count = Transaction.query.filter(
        Transaction.is_admin_generated.is_(True),
        Transaction.status == 'Ödendi',
    ).count()

    return {
        'year': year,
        'one_time_transactions': stats['transactions'],
        'recurring_plans': stats['recurring_plans'],
        'assets': stats['assets'],
        'asset_valuations': stats['asset_valuations'],
        'plan_transactions': plan_tx_count,
        'pending_transactions': pending_count,
        'paid_transactions': paid_count,
        'total_admin_transactions': Transaction.query.filter(
            db.or_(Transaction.is_admin_generated.is_(True), Transaction.note.ilike('%Admin%'))
        ).count(),
    }
