"""
Unit/Integration Tests — Financial Repository (Real SQLite DB)
repositories/financial_repository.py metodlarını gerçek veritabanı oturumuyla test eder.
Hedef: %8 → %60+ kapsam artışı
"""

import pytest

from models import Asset, Category, Transaction, db
from repositories.financial_repository import FinancialRepository


@pytest.fixture
def repo(app):
    return FinancialRepository(database=db)


@pytest.fixture
def setup_categories(app):
    """Gerekli temel kategorileri ve ledger hesaplarını ekler"""
    from domain.ledger.models.ledger_models import Account

    tenant_id = 'test-repo-tenant'
    # Gelir ve Gider kategorileri
    cat_income = Category(name='Maaş', type='Gelir', icon='fa-wallet', tenant_id=tenant_id)
    cat_expense = Category(name='Market', type='Gider', icon='fa-shopping-cart', tenant_id=tenant_id)
    cat_invest = Category(name='Hisse', type='Yatırım', icon='fa-chart-line', tenant_id=tenant_id)
    db.session.add_all([cat_income, cat_expense, cat_invest])

    # Ledger hesapları (Nakit Kasa, vb.)
    acct_cash = Account(name='Nakit Kasa', type='Asset', tenant_id=tenant_id, is_active=True)
    acct_income = Account(name='Maaş', type='Revenue', tenant_id=tenant_id, is_active=True)
    acct_expense = Account(name='Market', type='Expense', tenant_id=tenant_id, is_active=True)
    db.session.add_all([acct_cash, acct_income, acct_expense])
    db.session.commit()
    return tenant_id


# ─── Transactions: add, get, list, page ───────────────────────────────────────

@pytest.mark.unit
def test_add_transaction_income_and_get(repo, setup_categories):
    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-01',
        category='Maaş',
        description='Aylık maaş',
        type_='Gelir',
        amount=25000,
        status='Ödendi',
        note='Banka transferi',
        tenant_id=tenant
    )
    assert tx.id is not None
    assert tx.amount == 25000

    fetched = repo.get_transaction(tx.id, tenant_id=tenant)
    assert fetched is not None
    assert fetched.description == 'Aylık maaş'


@pytest.mark.unit
def test_add_transaction_expense(repo, setup_categories):
    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-02',
        category='Market',
        description='Haftalık alışveriş',
        type_='Gider',
        amount=1500,
        status='Ödendi',
        tenant_id=tenant
    )
    assert tx.id is not None
    assert tx.type == 'Gider'


@pytest.mark.unit
def test_transaction_page_and_list(repo, setup_categories):
    tenant = setup_categories
    for i in range(5):
        repo.add_transaction(
            date=f'2026-03-0{i+1}',
            category='Market',
            description=f'Harcama {i}',
            type_='Gider',
            amount=100 * (i + 1),
            status='Bekliyor',
            tenant_id=tenant
        )

    all_txs = repo.list_transactions(tenant_id=tenant)
    assert len(all_txs) == 5

    page = repo.transaction_page(page=1, per_page=3, tenant_id=tenant)
    assert len(page.items) == 3
    assert page.total == 5


# ─── Update & Quick Pay & Delete Transaction ──────────────────────────────────

@pytest.mark.unit
def test_update_pending_transaction(repo, setup_categories):
    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-10',
        category='Market',
        description='Bekleyen harcama',
        type_='Gider',
        amount=500,
        status='Bekliyor',
        tenant_id=tenant
    )
    updated = repo.update_transaction(
        transaction_id=tx.id,
        date='2026-03-11',
        category='Market',
        description='Güncellenen harcama',
        amount=650,
        status='Bekliyor',
        note='Not eklendi',
        tenant_id=tenant
    )
    assert updated.amount == 650
    assert updated.description == 'Güncellenen harcama'
    assert updated.note == 'Not eklendi'


@pytest.mark.unit
def test_update_paid_transaction_raises_ledger_error(repo, setup_categories):
    from domain.transactions.services.financial_ledger import LedgerError

    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-10',
        category='Market',
        description='Ödenmiş harcama',
        type_='Gider',
        amount=500,
        status='Ödendi',
        tenant_id=tenant
    )
    with pytest.raises(LedgerError, match="Ödenmiş işlem doğrudan güncellenemez"):
        repo.update_transaction(
            transaction_id=tx.id,
            date='2026-03-11',
            category='Market',
            description='Değişiklik denemesi',
            amount=600,
            status='Ödendi',
            tenant_id=tenant
        )


@pytest.mark.unit
def test_quick_pay_transaction(repo, setup_categories):
    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-12',
        category='Market',
        description='Fatura',
        type_='Gider',
        amount=800,
        status='Bekliyor',
        tenant_id=tenant
    )
    paid = repo.quick_pay_transaction(tx.id, tenant_id=tenant)
    assert paid.status == 'Ödendi'

    # Zaten ödenmişse tekrar çağrıldığında aynı işlem döner
    again = repo.quick_pay_transaction(tx.id, tenant_id=tenant)
    assert again.status == 'Ödendi'


@pytest.mark.unit
def test_delete_pending_transaction(repo, setup_categories):
    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-15',
        category='Market',
        description='Silinecek',
        type_='Gider',
        amount=200,
        status='Bekliyor',
        tenant_id=tenant
    )
    repo.delete_transaction(tx.id, tenant_id=tenant)
    assert repo.get_transaction(tx.id, tenant_id=tenant) is None


@pytest.mark.unit
def test_delete_paid_transaction_raises_ledger_error(repo, setup_categories):
    from domain.transactions.services.financial_ledger import LedgerError

    tenant = setup_categories
    tx = repo.add_transaction(
        date='2026-03-15',
        category='Market',
        description='Ödenmiş silinmez',
        type_='Gider',
        amount=200,
        status='Ödendi',
        tenant_id=tenant
    )
    with pytest.raises(LedgerError, match="Ödenmiş işlem silinemez"):
        repo.delete_transaction(tx.id, tenant_id=tenant)


@pytest.mark.unit
def test_pending_transactions_between(repo, setup_categories):
    tenant = setup_categories
    repo.add_transaction('2026-04-05', 'Market', 'Nisan 1', 'Gider', 100, 'Bekliyor', tenant_id=tenant)
    repo.add_transaction('2026-04-15', 'Market', 'Nisan 2', 'Gider', 200, 'Bekliyor', tenant_id=tenant)
    repo.add_transaction('2026-05-01', 'Market', 'Mayıs 1', 'Gider', 300, 'Bekliyor', tenant_id=tenant)

    results = repo.pending_transactions_between('2026-04-01', '2026-04-30', tenant_id=tenant)
    assert len(results) == 2


# ─── Recurring Plans & Occurrences ───────────────────────────────────────────

@pytest.mark.unit
def test_add_recurring_plan_installments(repo, setup_categories):
    tenant = setup_categories
    plan = repo.add_recurring_plan(
        name='Laptop Taksiti',
        category='Market',
        amount=3000,
        installments=6,
        payment_day=15,
        start_date='2026-01-01',
        tenant_id=tenant
    )
    assert plan.id is not None
    assert plan.installments == 6

    # 6 adet 'Bekliyor' transaction oluşturulmuş olmalı
    txs = Transaction.query.filter_by(source_id=plan.id, source_type='plan', tenant_id=tenant).all()
    assert len(txs) == 6


@pytest.mark.unit
def test_add_recurring_plan_invalid_category(repo, setup_categories):
    tenant = setup_categories
    with pytest.raises(ValueError, match="Geçersiz kategori"):
        repo.add_recurring_plan(
            name='Hatalı Plan',
            category='OlmayanKategori',
            amount=500,
            installments=3,
            payment_day=1,
            tenant_id=tenant
        )


@pytest.mark.unit
def test_add_recurring_plan_exceeds_max_installments(repo, setup_categories):
    tenant = setup_categories
    with pytest.raises(ValueError, match="Taksit sayısı 600'ü geçemez"):
        repo.add_recurring_plan(
            name='Çok Uzun Plan',
            category='Market',
            amount=500,
            installments=700,
            payment_day=1,
            tenant_id=tenant
        )


@pytest.mark.unit
def test_generate_rolling_transactions(repo, setup_categories):
    tenant = setup_categories
    plan = repo.add_recurring_plan(
        name='Netflix Aboneliği',
        category='Market',
        amount=150,
        installments=0,  # 0 = Süresiz abonelik
        payment_day=5,
        start_date='2026-01-01',
        plan_type='Abonelik',
        tenant_id=tenant
    )
    # generate_rolling_transactions en az 3 bekleyen işlem tutmalı
    repo.generate_rolling_transactions(tenant_id=tenant)
    txs = Transaction.query.filter_by(source_id=plan.id, source_type='plan', tenant_id=tenant).all()
    assert len(txs) >= 3


# ─── Payments & Plan Lifecycle ────────────────────────────────────────────────

@pytest.mark.unit
def test_create_payment_for_plan(repo, setup_categories):
    tenant = setup_categories
    plan = repo.add_recurring_plan(
        name='Telefon',
        category='Market',
        amount=1000,
        installments=3,
        payment_day=10,
        start_date='2026-01-01',
        tenant_id=tenant
    )
    payment = repo.create_payment(
        plan_id=plan.id,
        amount=1000,
        payment_date='2026-01-10',
        installment_number=1,
        notes='İlk taksit ödendi',
        tenant_id=tenant
    )
    assert payment.id is not None
    assert payment.installment_number == 1


@pytest.mark.unit
def test_update_recurring_plan(repo, setup_categories):
    tenant = setup_categories
    plan = repo.add_recurring_plan(
        name='Eski Plan Adı',
        category='Market',
        amount=500,
        installments=4,
        payment_day=10,
        start_date='2026-01-01',
        tenant_id=tenant
    )
    updated = repo.update_recurring_plan(
        plan_id=plan.id,
        name='Yeni Plan Adı',
        category='Market',
        amount=600,
        installments=4,
        payment_day=10,
        start_date='2026-01-01',
        tenant_id=tenant
    )
    assert updated.name == 'Yeni Plan Adı'
    assert updated.amount == 600


@pytest.mark.unit
def test_delete_plan_lifecycle(repo, setup_categories):
    tenant = setup_categories
    plan = repo.add_recurring_plan(
        name='Silinecek Plan',
        category='Market',
        amount=250,
        installments=3,
        payment_day=1,
        start_date='2026-01-01',
        tenant_id=tenant
    )
    result = repo.delete_plan(plan.id, tenant_id=tenant)
    assert result['success'] is True
    assert repo.get_recurring_plan_for_tenant(plan.id, tenant) is None


# ─── Assets ───────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_asset_queries(repo, setup_categories):
    from models import AssetSector

    tenant = setup_categories
    sector = AssetSector(name='Finans')
    db.session.add(sector)
    db.session.commit()

    a1 = Asset(
        type='Emtia', name='Altın Hesabı', value=50000,
        purchase_date='2026-01-01', purchase_cost=50000,
        quantity=20, unit_price=2500, currency='TRY',
        symbol='GLD', risk_level='Düşük', liquidity='Likit',
        sector_id=sector.id, tenant_id=tenant
    )
    a2 = Asset(
        type='Hisse', name='BIST Portföy', value=75000,
        purchase_date='2026-01-01', purchase_cost=70000,
        quantity=100, unit_price=750, currency='TRY',
        symbol='BST', risk_level='Orta', liquidity='Likit',
        sector_id=sector.id, tenant_id=tenant
    )
    db.session.add_all([a1, a2])
    db.session.commit()

    assets = repo.list_assets(tenant_id=tenant)
    assert len(assets) == 2

    by_name = repo.list_assets_by_name(tenant_id=tenant)
    assert by_name[0].name <= by_name[1].name

    page = repo.asset_page(page=1, per_page=10, tenant_id=tenant)
    assert len(page.items) == 2

    single = repo.get_asset_for_tenant(a1.id, tenant_id=tenant)
    assert single is not None
    assert single.name == 'Altın Hesabı'
