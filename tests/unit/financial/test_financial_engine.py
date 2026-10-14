"""
Unit Tests — Financial Engine (Kapsamlı)
Saf matematik fonksiyonları + DB-bağımlı fonksiyonlar (app fixture ile)
Hedef: %7 → %60+ kapsam artışı
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from engines.financial_engine import (
    FINANCIAL_ANALYSIS_CACHE,
    MONTHLY_DASHBOARD_CACHE,
    _as_decimal,
    _criterion_score,
    _determine_fire_profile,
    _determine_freedom_stage,
    _resolve_freedom_assumptions,
    _resolve_tenant_id,
    _safe_percentage,
    _status_from_score,
    _years_to_financial_independence,
    calculate_cash_trend,
    calculate_monthly_daily_balance,
    get_empty_freedom_analysis,
    get_financial_analysis,
    get_financial_freedom_analysis,
    get_monthly_dashboard_data,
)

# ─── _as_decimal ──────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_as_decimal_with_int():
    assert _as_decimal(100) == Decimal('100.0000')


@pytest.mark.unit
def test_as_decimal_with_float():
    result = _as_decimal(100.50)
    assert isinstance(result, Decimal)
    assert result == Decimal('100.5000')


@pytest.mark.unit
def test_as_decimal_with_none_returns_zero():
    assert _as_decimal(None) == Decimal('0')


@pytest.mark.unit
def test_as_decimal_custom_scale():
    result = _as_decimal(100.50, scale=2)
    assert result == Decimal('100.50')


@pytest.mark.unit
def test_as_decimal_with_decimal_input():
    d = Decimal('999.1234')
    assert _as_decimal(d) == Decimal('999.1234')


# ─── _safe_percentage ─────────────────────────────────────────────────────────

@pytest.mark.unit
def test_safe_percentage_basic():
    result = _safe_percentage(25, 100)
    assert result == Decimal('25')


@pytest.mark.unit
def test_safe_percentage_zero_denominator_returns_zero():
    assert _safe_percentage(50, 0) == 0


@pytest.mark.unit
def test_safe_percentage_negative_denominator_returns_zero():
    assert _safe_percentage(50, -1) == 0


@pytest.mark.unit
def test_safe_percentage_zero_numerator():
    assert _safe_percentage(0, 100) == Decimal('0')


@pytest.mark.unit
def test_safe_percentage_full_100():
    result = _safe_percentage(100, 100)
    assert result == Decimal('100')


@pytest.mark.unit
def test_safe_percentage_over_100():
    # 150/100 → 150%  — kabul edilebilir davranış
    result = _safe_percentage(150, 100)
    assert result == Decimal('150')


# ─── _resolve_tenant_id ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_resolve_tenant_id_explicit():
    assert _resolve_tenant_id('t-1') == 't-1'


@pytest.mark.unit
def test_resolve_tenant_id_none_outside_context():
    # Flask request context yok → None döner
    assert _resolve_tenant_id() is None


@pytest.mark.unit
def test_resolve_tenant_id_empty_string():
    # Boş string falsy — kodu doğrulayalım
    result = _resolve_tenant_id('')
    assert result is None


# ─── _criterion_score ─────────────────────────────────────────────────────────

@pytest.mark.unit
def test_criterion_score_below_all_thresholds():
    assert _criterion_score(0, [(25, 8), (50, 15), (100, 25)]) == 0


@pytest.mark.unit
def test_criterion_score_first_threshold():
    assert _criterion_score(30, [(25, 8), (50, 15), (100, 25)]) == 8


@pytest.mark.unit
def test_criterion_score_second_threshold():
    assert _criterion_score(55, [(25, 8), (50, 15), (100, 25)]) == 15


@pytest.mark.unit
def test_criterion_score_max_threshold():
    assert _criterion_score(100, [(25, 8), (50, 15), (100, 25)]) == 25


@pytest.mark.unit
def test_criterion_score_exact_boundary():
    assert _criterion_score(25, [(25, 8), (50, 15)]) == 8


# ─── _status_from_score ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_status_from_score_success():
    # 85/100 = 0.85 → success
    assert _status_from_score(85, 100) == 'success'


@pytest.mark.unit
def test_status_from_score_warning():
    # 60/100 = 0.60 → warning
    assert _status_from_score(60, 100) == 'warning'


@pytest.mark.unit
def test_status_from_score_danger():
    # 30/100 = 0.30 → danger
    assert _status_from_score(30, 100) == 'danger'


@pytest.mark.unit
def test_status_from_score_zero_max():
    assert _status_from_score(0, 0) == 'danger'


@pytest.mark.unit
def test_status_from_score_exact_85():
    assert _status_from_score(85, 100) == 'success'


# ─── _years_to_financial_independence ────────────────────────────────────────

@pytest.mark.unit
def test_years_to_fi_already_free():
    # Portföy hedeften büyük → 0.0
    assert _years_to_financial_independence(3_000_000, 5_000, 10_000) == 0.0


@pytest.mark.unit
def test_years_to_fi_no_expenses():
    # Gider sıfır → 0.0
    assert _years_to_financial_independence(100_000, 5_000, 0) == 0.0


@pytest.mark.unit
def test_years_to_fi_no_savings():
    # Tasarruf yok → None (hiç ulaşamaz)
    assert _years_to_financial_independence(0, 0, 10_000) is None


@pytest.mark.unit
def test_years_to_fi_negative_savings():
    # Negatif tasarruf → None
    assert _years_to_financial_independence(0, -500, 10_000) is None


@pytest.mark.unit
def test_years_to_fi_reasonable_scenario():
    # 1M TL portföy, 5000 TL/ay birikim, 10000 TL/ay gider
    # FI hedefi: 10000 * 12 * 25 = 3_000_000 TL
    # Başlangıç: 1_000_000 → 2_000_000 TL daha gerekli
    years = _years_to_financial_independence(1_000_000, 5_000, 10_000, annual_return=0.07)
    assert years is not None
    assert 10 < years < 40  # Makul bir aralık


@pytest.mark.unit
def test_years_to_fi_with_custom_multiplier():
    # 3% SWR → 33x çarpan, daha yüksek hedef
    years_25x = _years_to_financial_independence(0, 5_000, 5_000, fi_multiplier=25)
    years_33x = _years_to_financial_independence(0, 5_000, 5_000, fi_multiplier=33)
    assert years_33x > years_25x


# ─── _determine_freedom_stage ─────────────────────────────────────────────────

@pytest.mark.unit
def test_freedom_stage_fire():
    stage = _determine_freedom_stage(100, 50, 12, 100, True)
    assert stage['key'] == 'fire'
    assert stage['level'] == 7


@pytest.mark.unit
def test_freedom_stage_semi_independent():
    stage = _determine_freedom_stage(80, 30, 5, 80, False)
    assert stage['key'] == 'coast'
    assert stage['level'] == 6


@pytest.mark.unit
def test_freedom_stage_accumulate():
    stage = _determine_freedom_stage(30, 25, 5, 10, False)
    assert stage['key'] == 'accumulate'
    assert stage['level'] == 5


@pytest.mark.unit
def test_freedom_stage_security():
    stage = _determine_freedom_stage(10, 5, 3, 5, False)
    assert stage['key'] == 'security'
    assert stage['level'] == 4


@pytest.mark.unit
def test_freedom_stage_awareness():
    stage = _determine_freedom_stage(5, 5, 0, 5, False)
    assert stage['key'] == 'awareness'
    assert stage['level'] == 3


@pytest.mark.unit
def test_freedom_stage_start():
    stage = _determine_freedom_stage(0, 0, 0, 0, False)
    assert stage['key'] == 'start'
    assert stage['level'] == 2


# ─── _determine_fire_profile ──────────────────────────────────────────────────

@pytest.mark.unit
def test_fire_profile_traditional():
    profile = _determine_fire_profile(100, 50, 10_000, True)
    assert profile['key'] == 'traditional'


@pytest.mark.unit
def test_fire_profile_barista():
    profile = _determine_fire_profile(30, 60, 10_000, False)
    assert profile['key'] == 'barista'


@pytest.mark.unit
def test_fire_profile_coast():
    profile = _determine_fire_profile(45, 20, 10_000, False)
    assert profile['key'] == 'coast'


@pytest.mark.unit
def test_fire_profile_lean():
    profile = _determine_fire_profile(10, 5, 8_000, False)
    assert profile['key'] == 'lean'


@pytest.mark.unit
def test_fire_profile_building():
    profile = _determine_fire_profile(10, 5, 50_000, False)
    assert profile['key'] == 'building'


# ─── _resolve_freedom_assumptions ────────────────────────────────────────────

@pytest.mark.unit
def test_resolve_assumptions_no_preferences():
    result = _resolve_freedom_assumptions(None)
    assert result['safe_withdrawal_rate'] == Decimal('0.04')
    assert result['emergency_fund_target_months'] == 6
    assert result['is_customized'] is False


@pytest.mark.unit
def test_resolve_assumptions_with_custom_swr():
    class FakePrefs:
        safe_withdrawal_rate = 0.03
        emergency_fund_target_months = 12
        target_monthly_passive_income = None
        target_retirement_year = None

    result = _resolve_freedom_assumptions(FakePrefs())
    assert result['safe_withdrawal_rate'] == Decimal('0.03')
    assert result['emergency_fund_target_months'] == 12
    # fi_multiplier = 1/0.03 ≈ 33.33
    assert result['fi_multiplier'] > Decimal('33')
    assert result['is_customized'] is True


@pytest.mark.unit
def test_resolve_assumptions_emergency_target():
    class FakePrefs:
        safe_withdrawal_rate = None
        emergency_fund_target_months = 9
        target_monthly_passive_income = None
        target_retirement_year = None

    result = _resolve_freedom_assumptions(FakePrefs())
    assert result['emergency_fund_target_months'] == 9


# ─── get_empty_freedom_analysis ───────────────────────────────────────────────

@pytest.mark.unit
def test_empty_freedom_analysis_structure():
    result = get_empty_freedom_analysis()
    # Zorunlu anahtarlar mevcut
    required_keys = [
        'net_worth', 'total_assets', 'monthly_avg_income', 'monthly_avg_expenses',
        'freedom_score', 'criteria', 'milestones', 'freedom_stage', 'fire_profile',
        'fi_number', 'savings_rate', 'emergency_fund_months', 'is_financially_free',
        'assumptions',
    ]
    for key in required_keys:
        assert key in result, f"Eksik anahtar: {key}"


@pytest.mark.unit
def test_empty_freedom_analysis_zero_score():
    result = get_empty_freedom_analysis()
    assert result['freedom_score'] == 0


@pytest.mark.unit
def test_empty_freedom_analysis_empty_criteria():
    result = get_empty_freedom_analysis()
    assert result['criteria'] == []


@pytest.mark.unit
def test_empty_freedom_analysis_not_free():
    result = get_empty_freedom_analysis()
    assert result['is_financially_free'] is False


# ─── calculate_cash_trend ────────────────────────────────────────────────────

class _FakeTx:
    """Mock transaction nesnesi"""
    def __init__(self, date: str, type_: str, amount: float,
                 status: str = 'Ödendi', category: str = 'Test', description: str = ''):
        self.date = date
        self.type = type_
        self.amount = amount
        self.status = status
        self.category = category
        self.description = description
        self.source_id = None
        self.source_type = None
        self.is_deleted = False
        self.account_id = None
        self.target_account_id = None


@pytest.mark.unit
def test_calculate_cash_trend_length():
    now = datetime(2026, 1, 10)
    txs = [_FakeTx('2026-01-05', 'Gelir', 1000)]
    result = calculate_cash_trend(now, txs, 5)
    assert len(result) == 5


@pytest.mark.unit
def test_calculate_cash_trend_income_adds():
    now = datetime(2026, 1, 10)
    txs = [_FakeTx('2026-01-09', 'Gelir', 500, 'Ödendi')]
    result = calculate_cash_trend(now, txs, 3)
    # Tüm günler için 500 eklenmiş olmalı (tarih <= current_date)
    assert all(v == 500 for v in result)


@pytest.mark.unit
def test_calculate_cash_trend_expense_subtracts():
    now = datetime(2026, 1, 10)
    txs = [_FakeTx('2026-01-09', 'Gider', 300, 'Ödendi')]
    result = calculate_cash_trend(now, txs, 3)
    assert all(v == -300 for v in result)


@pytest.mark.unit
def test_calculate_cash_trend_future_tx_excluded_on_day0():
    """İlerideki tarihli işlem ilk gün için dahil edilmemeli"""
    now = datetime(2026, 1, 10)
    # 3 gün sonraki işlem
    txs = [_FakeTx('2026-01-13', 'Gelir', 999, 'Ödendi')]
    result = calculate_cash_trend(now, txs, 1)
    assert result[0] == 0


@pytest.mark.unit
def test_calculate_cash_trend_empty_transactions():
    now = datetime(2026, 1, 10)
    result = calculate_cash_trend(now, [], 7)
    assert result == [0] * 7


# ─── calculate_monthly_daily_balance ─────────────────────────────────────────

@pytest.mark.unit
def test_monthly_daily_balance_label_format():
    txs = []
    labels, data = calculate_monthly_daily_balance(2026, 3, txs)
    # Mart → 31 gün
    assert all(label.startswith('2026-03-') for label in labels)


@pytest.mark.unit
def test_monthly_daily_balance_length_future_month():
    # Gelecek ay → tüm günleri göster (1–31)
    future_year = datetime.now().year + 1
    txs = []
    labels, data = calculate_monthly_daily_balance(future_year, 1, txs)
    assert len(labels) == 31  # Ocak = 31 gün


@pytest.mark.unit
def test_monthly_daily_balance_data_matches_labels():
    txs = []
    labels, data = calculate_monthly_daily_balance(2025, 2, txs)
    assert len(labels) == len(data)


@pytest.mark.unit
def test_monthly_daily_balance_income_transaction():
    txs = [_FakeTx('2025-02-10', 'Gelir', 5000, 'Ödendi')]
    _, data = calculate_monthly_daily_balance(2025, 2, txs)
    # Şubat 2025 geçmiş ay — tüm günler dahil
    # 10. günden itibaren 5000 görünmeli
    assert data[-1] == 5000


@pytest.mark.unit
def test_monthly_daily_balance_zero_for_empty():
    txs = []
    _, data = calculate_monthly_daily_balance(2025, 6, txs)
    assert all(v == 0 for v in data)


# ─── DB bağımlı: get_financial_analysis ──────────────────────────────────────

@pytest.mark.unit
def test_get_financial_analysis_structure(app):
    """get_financial_analysis() — DB ile entegre, doğru yapı döner"""
    from engines.financial_engine import get_financial_analysis

    result = get_financial_analysis(tenant_id='test-tenant')
    required = [
        'score', 'strategy', 'flags', 'recs',
        'liquidity', 'liq_status', 'liq_msg',
        'debt_ratio', 'dr_status', 'dr_msg',
        'savings', 'sr_status', 'sr_msg',
        'sustain', 'sus_status', 'sus_msg',
        'total_servet', 'total_debt', 'net_worth', 'actual_cash',
    ]
    for key in required:
        assert key in result, f"Eksik anahtar: {key}"


@pytest.mark.unit
def test_get_financial_analysis_score_range(app):
    from engines.financial_engine import get_financial_analysis

    result = get_financial_analysis(tenant_id='test-tenant')
    assert 0 <= result['score'] <= 100


@pytest.mark.unit
def test_get_financial_analysis_status_values(app):
    from engines.financial_engine import get_financial_analysis

    result = get_financial_analysis(tenant_id='test-tenant')
    valid = {'success', 'warning', 'danger'}
    assert result['liq_status'] in valid
    assert result['dr_status'] in valid
    assert result['sr_status'] in valid
    assert result['sus_status'] in valid


@pytest.mark.unit
def test_get_financial_analysis_with_income(app):
    """Gelir eklendiğinde tasarruf oranı pozitif olmalı"""
    from models import Transaction, db

    today = datetime.now().strftime('%Y-%m-%d')
    tx = Transaction(
        date=today, category='Maaş', type='Gelir',
        amount=10000, status='Ödendi', description='Test',
        tenant_id='analysis-tenant'
    )
    db.session.add(tx)
    db.session.commit()

    FINANCIAL_ANALYSIS_CACHE['data'].pop('analysis-tenant', None)

    result = get_financial_analysis(tenant_id='analysis-tenant')
    assert result['actual_cash'] > 0


@pytest.mark.unit
def test_get_financial_analysis_cache_works(app):
    """İkinci çağrı önbellekten döner"""
    from engines.financial_engine import get_financial_analysis

    FINANCIAL_ANALYSIS_CACHE['data'].pop('cache-tenant', None)
    r1 = get_financial_analysis(tenant_id='cache-tenant')
    r2 = get_financial_analysis(tenant_id='cache-tenant')
    assert r1 is r2  # Aynı obje — önbellekten


# ─── DB bağımlı: get_financial_freedom_analysis ──────────────────────────────

@pytest.mark.unit
def test_freedom_analysis_structure(app):

    result = get_financial_freedom_analysis(tenant_id='fire-tenant')
    required = [
        'net_worth', 'monthly_avg_income', 'monthly_avg_expenses',
        'savings_rate', 'fi_number', 'fi_progress_pct',
        'freedom_score', 'criteria', 'milestones', 'freedom_stage',
        'fire_profile', 'is_financially_free', 'assumptions', 'references',
    ]
    for key in required:
        assert key in result, f"Eksik anahtar: {key}"


@pytest.mark.unit
def test_freedom_analysis_criteria_count(app):
    """6 kriter dönmeli"""

    result = get_financial_freedom_analysis(tenant_id='criteria-tenant')
    assert len(result['criteria']) == 6


@pytest.mark.unit
def test_freedom_analysis_milestones_count(app):
    """7 milestone dönmeli"""

    result = get_financial_freedom_analysis(tenant_id='milestone-tenant')
    assert len(result['milestones']) == 7


@pytest.mark.unit
def test_freedom_analysis_score_range(app):

    result = get_financial_freedom_analysis(tenant_id='score-tenant')
    assert 0 <= result['freedom_score'] <= 100


@pytest.mark.unit
def test_freedom_analysis_with_transactions(app):
    """Gerçek işlemlerle analiz — savings_rate pozitif"""
    from models import Transaction, db

    today = datetime.now()
    for i in range(6):
        d = (today - timedelta(days=30 * i)).strftime('%Y-%m-%d')
        db.session.add(Transaction(
            date=d, category='Maaş', type='Gelir',
            amount=20000, status='Ödendi', description='Maaş', tenant_id='fire-with-tx'
        ))
        db.session.add(Transaction(
            date=d, category='Kira', type='Gider',
            amount=8000, status='Ödendi', description='Kira', tenant_id='fire-with-tx'
        ))
    db.session.commit()


    result = get_financial_freedom_analysis(tenant_id='fire-with-tx')
    assert result['monthly_avg_income'] > 0
    assert result['monthly_avg_expenses'] > 0
    assert result['savings_rate'] > 0


@pytest.mark.unit
def test_freedom_analysis_with_custom_preferences(app):
    """Kullanıcı %3 SWR girerse fi_multiplier ~33× olmalı"""
    class Prefs:
        safe_withdrawal_rate = 0.03
        emergency_fund_target_months = 9
        target_monthly_passive_income = None
        target_retirement_year = None


    result = get_financial_freedom_analysis(tenant_id='custom-prefs', preferences=Prefs())
    assert result['assumptions']['safe_withdrawal_rate'] == Decimal('0.03')
    assert result['assumptions']['fi_multiplier'] > Decimal('33')


@pytest.mark.unit
def test_freedom_analysis_indefinite_plan_debts(app):
    """FIRE analizinde süresiz planlar borç hanesine yazılmamalıdır (total_debts = 0)."""
    from models import RecurringPlan, db
    from engines.financial_engine import get_financial_freedom_analysis, FREEDOM_ANALYSIS_CACHE

    tenant = 'fire-indefinite-tenant'
    plan = RecurringPlan(
        name='Süresiz Ev Kirası',
        category='Konut & Kira',
        amount=25000,
        flow_type='Gider',
        frequency='Aylık',
        plan_type='Kira',
        installments=0,
        payment_day=1,
        status='Aktif',
        tenant_id=tenant,
    )
    db.session.add(plan)
    db.session.commit()

    FREEDOM_ANALYSIS_CACHE['data'].clear()
    result = get_financial_freedom_analysis(tenant_id=tenant)
    assert result['total_debts'] == 0


# ─── DB bağımlı: get_monthly_dashboard_data ──────────────────────────────────

@pytest.mark.unit
def test_monthly_dashboard_structure(app):

    MONTHLY_DASHBOARD_CACHE['data'].clear()
    m_data, i_data, tr = get_monthly_dashboard_data(2026, tenant_id='dash-tenant')
    assert len(m_data) == 12
    assert len(i_data) == 12
    assert len(tr) == 12


@pytest.mark.unit
def test_monthly_dashboard_month_names(app):

    MONTHLY_DASHBOARD_CACHE['data'].clear()
    m_data, _, tr = get_monthly_dashboard_data(2026, tenant_id='dash-names')
    assert tr[0] == 'Ocak'
    assert tr[11] == 'Aralık'


@pytest.mark.unit
def test_monthly_dashboard_month_keys(app):
    """Her ay dict'inde zorunlu anahtarlar mevcut"""

    MONTHLY_DASHBOARD_CACHE['data'].clear()
    m_data, _, _ = get_monthly_dashboard_data(2026, tenant_id='dash-keys')
    required = ['name', 'inc', 'exp', 'inv', 'net', 'realized_net', 'projected_net']
    for month in m_data:
        for key in required:
            assert key in month, f"Ay '{month['name']}'da eksik anahtar: {key}"


@pytest.mark.unit
def test_monthly_dashboard_cache_works(app):

    MONTHLY_DASHBOARD_CACHE['data'].clear()
    r1 = get_monthly_dashboard_data(2026, tenant_id='dash-cache')
    r2 = get_monthly_dashboard_data(2026, tenant_id='dash-cache')
    assert r1 is r2


@pytest.mark.unit
def test_monthly_dashboard_with_income(app):
    """Gelir işlemi eklenince ilgili ayda inc > 0"""
    from models import Transaction, db

    db.session.add(Transaction(
        date='2026-03-15', category='Maaş', type='Gelir',
        amount=15000, status='Ödendi', description='Maaş', tenant_id='dash-income'
    ))
    db.session.commit()


    MONTHLY_DASHBOARD_CACHE['data'].clear()
    m_data, _, _ = get_monthly_dashboard_data(2026, tenant_id='dash-income')
    march = m_data[2]  # index 2 = Mart
    assert march['inc'] == 15000


@pytest.mark.unit
def test_get_financial_analysis_indefinite_plan_no_debt(app):
    """Süresiz planlar (kira/abonelik vb.) suni borç üretmemelidir (total_debt = 0)."""
    from models import RecurringPlan, db
    from engines.financial_engine import get_financial_analysis, FINANCIAL_ANALYSIS_CACHE

    tenant = 'indefinite-debt-tenant'
    plan = RecurringPlan(
        name='Süresiz Kira',
        category='Konut & Kira',
        amount=15000,
        flow_type='Gider',
        frequency='Aylık',
        plan_type='Kira',
        installments=0,
        payment_day=5,
        status='Aktif',
        tenant_id=tenant,
    )
    db.session.add(plan)
    db.session.commit()

    FINANCIAL_ANALYSIS_CACHE['data'].pop(tenant, None)
    result = get_financial_analysis(tenant_id=tenant)
    assert result['total_debt'] == 0


@pytest.mark.unit
def test_get_financial_analysis_completed_plan_no_debt(app):
    """Tamamlanan planlar borç hanesinde yer almamalıdır (total_debt = 0)."""
    from models import RecurringPlan, db
    from engines.financial_engine import get_financial_analysis, FINANCIAL_ANALYSIS_CACHE

    tenant = 'completed-debt-tenant'
    plan = RecurringPlan(
        name='Biten Kredi',
        category='Kredi Ödemesi',
        amount=5000,
        flow_type='Gider',
        frequency='Aylık',
        plan_type='Taksit',
        installments=12,
        payment_day=10,
        status='Tamamlandı',
        tenant_id=tenant,
    )
    db.session.add(plan)
    db.session.commit()

    FINANCIAL_ANALYSIS_CACHE['data'].pop(tenant, None)
    result = get_financial_analysis(tenant_id=tenant)
    assert result['total_debt'] == 0

