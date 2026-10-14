"""
Database Seeding - Veri seeding
Varsayılan veri oluşturma ve migration
"""

import logging

from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from models import AssetSector, AssetType, Category, RecurringPlan, Tenant, Transaction, User, db

logger = logging.getLogger(__name__)


def _initialize_default_data():
    """
    Sistem verilerini başlatır.
    1. Platform sahibi kullanıcısını (User.SUPER_ADMIN_USERNAME, şifre: 1)
       mutlak süper admin olarak garanti eder.
    2. Diğer kullanıcıların varlığına izin verir.
    """
    owner_username = User.SUPER_ADMIN_USERNAME
    # Varsayılan tenant oluştur
    try:
        default_tenant = Tenant.query.filter_by(id='default').first()
    except Exception as q_err:
        logger.warning(f"Tenant query error: {q_err}")
        default_tenant = None

    if not default_tenant:
        logger.info("Varsayılan tenant oluşturuluyor...")
        default_tenant = Tenant(id='default', name='Default Tenant')
        db.session.add(default_tenant)
        try:
            db.session.flush()
        except Exception as flush_err:
            db.session.rollback()
            logger.info("Default tenant already exists or flush failed. Fetching again...")
            default_tenant = Tenant.query.filter_by(id='default').first()
            if not default_tenant:
                raise flush_err

    try:
        emin = User.query.filter_by(username=owner_username).first()
    except Exception as q_err:
        logger.warning(f"User query error: {q_err}")
        emin = None

    if not emin:
        logger.info(f"Süper admin ({owner_username}) oluşturuluyor...")
        emin = User(
            username=owner_username,
            password=generate_password_hash('1'),
            password_changed_at=None,
            role='sistem_yoneticisi',
            tenant_id=default_tenant.id
        )
        db.session.add(emin)
        try:
            db.session.flush()
        except Exception as flush_err:
            db.session.rollback()
            logger.info(f"User {owner_username} already exists or flush failed. Fetching again...")
            emin = User.query.filter_by(username=owner_username).first()
            if not emin:
                raise flush_err
    else:
        # Yetkileri ve şifreleme formatını doğrula
        emin.role = 'sistem_yoneticisi'
        if not (emin.password.startswith('pbkdf2:') or emin.password.startswith('scrypt:')):
            emin.password = generate_password_hash(emin.password)
        # Tenant ID ata (eğer yoksa)
        if not emin.tenant_id:
            emin.tenant_id = default_tenant.id

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        logger.warning(f"Initial default tenant/admin commit failed: {commit_err}")

    v_tipleri = ['Gayrimenkul', 'Hisse Senedi', 'Fon', 'BES', 'Altın', 'Kripto', 'Nakit']
    for t in v_tipleri:
        try:
            if not AssetType.query.filter_by(name=t).first():
                db.session.add(AssetType(name=t))
                db.session.flush()
        except Exception:
            db.session.rollback()

    v_sektorleri = ['Emtia & Hammadde', 'Savunma & Güvenlik', 'Finansal Sistem', 'Tüketim (Perakende & E-Ticaret)',
                    'Sağlık', 'Teknoloji', 'Enerji', 'Üretim & Lojistik', 'Gayrimenkul & Fiziksel Varlıklar',
                    'İletişim', 'Bankacılık']
    for s in v_sektorleri:
        try:
            if not AssetSector.query.filter_by(name=s).first():
                db.session.add(AssetSector(name=s))
                db.session.flush()
        except Exception:
            db.session.rollback()

    # -----------------------------------------------------------------------
    # Standart Kategori Listesi — GL Kodları ile
    # Gelir → GLR-6xxx, Gider → GDR-7xxx, Yatırım → YTR-1xxx, Transfer → TRF-2xxx
    # Not: Kategori listesi scripts/seed_standard_categories.py'den import edilir
    # Tek kaynak yönetimi için burada doğrudan tanımlanmamıştır
    # -----------------------------------------------------------------------
    from scripts.seed_standard_categories import STANDARD_CATEGORIES

    # Standart kategoriler kalıcı referans veridir. Mevcut satırları silmek veya
    # çekirdek alanlarını yeniden yazmak kullanıcı bütçelerini, işlem geçmişi
    # bağlantılarını ve kategori kimliklerini bozabilir. Yalnızca eksik kodları
    # varsayılan bütçeyle ekle; mevcut satırların tüm alanlarını koru.
    all_system_cats = Category.query.filter_by(tenant_id=None).all()
    by_code = {cat.code: cat for cat in all_system_cats if cat.code}
    by_name = {cat.name: cat for cat in all_system_cats if cat.name}

    for code, name, type_, sort_order, budget_limit in STANDARD_CATEGORIES:
        if code in by_code or name in by_name:
            continue
        try:
            new_cat = Category(
                name=name,
                type=type_,
                code=code,
                tenant_id=None,
                budget_limit=budget_limit,
            )
            db.session.add(new_cat)
            db.session.flush()
            by_code[code] = new_cat
            by_name[name] = new_cat
        except Exception:
            db.session.rollback()

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        logger.warning(f"Default reference data commit failed: {commit_err}")

    try:
        from database.seeds.quiz_questions_seed import seed_quiz_questions
        seed_quiz_questions()
    except Exception as quiz_seed_error:
        db.session.rollback()
        logger.warning(f"Quiz question seed failed: {quiz_seed_error}")



def _migrate_legacy_plans():
    """Eski plan tablolarından RecurringPlan'a taşır (bir kez)"""
    if RecurringPlan.query.first() is not None:
        return
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    def _add_from_row(name, category, flow_type, amount, installments, payment_day, note, old_source, old_id):
        plan = RecurringPlan(
            name=name, category=category, flow_type=flow_type,
            amount=amount, installments=installments, payment_day=payment_day, note=note
        )
        db.session.add(plan)
        db.session.flush()
        # _create_transactions_from_plan(plan)  # Bu fonksiyonun database.py'de tanımlı olduğunu varsayıyoruz
        Transaction.query.filter_by(source_id=old_id, source_type=old_source).update(
            {'source_id': plan.id, 'source_type': 'plan'}
        )

    if 'income_plan' in tables:
        for row in db.session.execute(text('SELECT id, name, amount, payment_day, installments, type_cat FROM income_plan')):
            _add_from_row(row.name, row.type_cat, 'Gelir', row.amount, row.installments, row.payment_day, None, 'income', row.id)

    if 'fixed_payment' in tables:
        for row in db.session.execute(text('SELECT id, name, amount, installments, payment_day FROM fixed_payment')):
            _add_from_row(row.name, 'Aylık Sabit Gider', 'Gider', row.amount, row.installments, row.payment_day, None, 'fixed', row.id)

    if 'loan' in tables:
        for row in db.session.execute(text('SELECT id, name, bank, monthly, installments, payment_day FROM loan')):
            _add_from_row(row.name, 'Kredi', 'Gider', row.monthly, row.installments, row.payment_day, row.bank, 'loan', row.id)

    if 'credit_card' in tables:
        for row in db.session.execute(text('SELECT id, name, debt, due_date FROM credit_card')):
            day = min(int(row.due_date.split('-')[2]), 28)
            _add_from_row(row.name, 'Kredi Kartı', 'Gider', row.debt, 1, day, None, 'card', row.id)

    db.session.commit()

def _initialize_tenant_data():
    """
    Mevcut verileri varsayılan tenant'a atar (migration)
    Bu fonksiyon bir kez çalışır, mevcut verileri 'default' tenant'a bağlar
    """
    default_tenant = Tenant.query.filter_by(id='default').first()
    if not default_tenant:
        logger.warning("Varsayılan tenant bulunamadı, tenant verisi atanamadı")
        return

    # User tablosu için tenant_id ata
    users_without_tenant = User.query.filter_by(tenant_id=None).all()
    if users_without_tenant:
        logger.info(f"{len(users_without_tenant)} kullanıcıya varsayılan tenant atanıyor...")
        for user in users_without_tenant:
            user.tenant_id = default_tenant.id
        db.session.commit()

    # Transaction tablosu için tenant_id ata
    transactions_without_tenant = Transaction.query.filter_by(tenant_id=None).all()
    if transactions_without_tenant:
        logger.info(f"{len(transactions_without_tenant)} işleme varsayılan tenant atanıyor...")
        for tx in transactions_without_tenant:
            tx.tenant_id = default_tenant.id
        db.session.commit()
    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        logger.warning(f"Default reference data commit failed: {commit_err}")

    try:
        from database.seeds.quiz_questions_seed import seed_quiz_questions
        seed_quiz_questions()
    except Exception as quiz_seed_error:
        db.session.rollback()
        logger.warning(f"Quiz question seed failed: {quiz_seed_error}")



def _migrate_legacy_plans():
    """Eski plan tablolarından RecurringPlan'a taşır (bir kez)"""
    if RecurringPlan.query.first() is not None:
        return
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    def _add_from_row(name, category, flow_type, amount, installments, payment_day, note, old_source, old_id):
        plan = RecurringPlan(
            name=name, category=category, flow_type=flow_type,
            amount=amount, installments=installments, payment_day=payment_day, note=note
        )
        db.session.add(plan)
        db.session.flush()
        # _create_transactions_from_plan(plan)  # Bu fonksiyonun database.py'de tanımlı olduğunu varsayıyoruz
        Transaction.query.filter_by(source_id=old_id, source_type=old_source).update(
            {'source_id': plan.id, 'source_type': 'plan'}
        )

    if 'income_plan' in tables:
        for row in db.session.execute(text('SELECT id, name, amount, payment_day, installments, type_cat FROM income_plan')):
            _add_from_row(row.name, row.type_cat, 'Gelir', row.amount, row.installments, row.payment_day, None, 'income', row.id)

    if 'fixed_payment' in tables:
        for row in db.session.execute(text('SELECT id, name, amount, installments, payment_day FROM fixed_payment')):
            _add_from_row(row.name, 'Aylık Sabit Gider', 'Gider', row.amount, row.installments, row.payment_day, None, 'fixed', row.id)

    if 'loan' in tables:
        for row in db.session.execute(text('SELECT id, name, bank, monthly, installments, payment_day FROM loan')):
            _add_from_row(row.name, 'Kredi', 'Gider', row.monthly, row.installments, row.payment_day, row.bank, 'loan', row.id)

    if 'credit_card' in tables:
        for row in db.session.execute(text('SELECT id, name, debt, due_date FROM credit_card')):
            day = min(int(row.due_date.split('-')[2]), 28)
            _add_from_row(row.name, 'Kredi Kartı', 'Gider', row.debt, 1, day, None, 'card', row.id)

    db.session.commit()

def _initialize_tenant_data():
    """
    Mevcut verileri varsayılan tenant'a atar (migration)
    Bu fonksiyon bir kez çalışır, mevcut verileri 'default' tenant'a bağlar
    """
    default_tenant = Tenant.query.filter_by(id='default').first()
    if not default_tenant:
        logger.warning("Varsayılan tenant bulunamadı, tenant verisi atanamadı")
        return

    # User tablosu için tenant_id ata
    users_without_tenant = User.query.filter_by(tenant_id=None).all()
    if users_without_tenant:
        logger.debug(f"{len(users_without_tenant)} kullanıcıya varsayılan tenant atanıyor...")
        for user in users_without_tenant:
            user.tenant_id = default_tenant.id
        db.session.commit()

    # Transaction tablosu için tenant_id ata
    transactions_without_tenant = Transaction.query.filter_by(tenant_id=None).all()
    if transactions_without_tenant:
        logger.debug(f"{len(transactions_without_tenant)} işleme varsayılan tenant atanıyor...")
        for tx in transactions_without_tenant:
            tx.tenant_id = default_tenant.id
        db.session.commit()

    # Asset tablosu için tenant_id ata
    from models import Asset
    assets_without_tenant = Asset.query.filter_by(tenant_id=None).all()
    if assets_without_tenant:
        logger.debug(f"{len(assets_without_tenant)} varlığa varsayılan tenant atanıyor...")
        for asset in assets_without_tenant:
            asset.tenant_id = default_tenant.id
        db.session.commit()

    # RecurringPlan tablosu için tenant_id ata
    plans_without_tenant = RecurringPlan.query.filter_by(tenant_id=None).all()
    if plans_without_tenant:
        logger.debug(f"{len(plans_without_tenant)} plana varsayılan tenant atanıyor...")
        for plan in plans_without_tenant:
            plan.tenant_id = default_tenant.id
        db.session.commit()

    logger.debug("Tenant verisi atama tamamlandı")
