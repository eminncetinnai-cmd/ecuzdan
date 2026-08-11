from datetime import datetime

from models import Asset, AssetSector, AssetUpdate, Tenant, Transaction, db


def _add_tenant(id_, name):
    tenant = Tenant(id=id_, name=name)
    db.session.add(tenant)
    db.session.flush()
    return tenant


def _add_paid_tx(tenant_id, date, category, type_, amount, status='Ödendi'):
    db.session.add(Transaction(
        tenant_id=tenant_id,
        date=date,
        category=category,
        description=category,
        type=type_,
        amount=amount,
        status=status,
    ))


def _sector_id():
    sector = AssetSector.query.filter_by(name='Teknoloji').first()
    if not sector:
        sector = AssetSector(name='Teknoloji')
        db.session.add(sector)
        db.session.flush()
    return sector.id


def _add_asset(tenant_id, name, value, cost):
    db.session.add(Asset(
        tenant_id=tenant_id,
        type='Hisse Senedi',
        name=name,
        value=value,
        description=name,
        purchase_date='2025-01-01',
        purchase_cost=cost,
        quantity=1,
        unit_price=value,
        currency='TRY',
        symbol=name[:20],
        risk_level='Orta',
        liquidity='Likit',
        sector_id=_sector_id(),
    ))


def test_financial_analysis_is_tenant_scoped(app):
    tenant_a = _add_tenant('analytics_a', 'Analytics A')
    tenant_b = _add_tenant('analytics_b', 'Analytics B')
    _add_paid_tx(tenant_a.id, '2025-06-01', 'Maaş', 'Gelir', 1000)
    _add_paid_tx(tenant_b.id, '2025-06-01', 'Maaş', 'Gelir', 9000)
    _add_asset(tenant_a.id, 'A_ASSET', 2000, 1500)
    _add_asset(tenant_b.id, 'B_ASSET', 8000, 7000)
    db.session.commit()

    from engines.financial_engine import get_financial_analysis

    result = get_financial_analysis(tenant_a.id)

    assert result['actual_cash'] == 1000
    assert result['total_servet'] == 3000


def test_monthly_dashboard_data_is_tenant_scoped(app):
    tenant_a = _add_tenant('monthly_a', 'Monthly A')
    tenant_b = _add_tenant('monthly_b', 'Monthly B')
    _add_paid_tx(tenant_a.id, '2025-01-05', 'Maaş', 'Gelir', 1000)
    _add_paid_tx(tenant_b.id, '2025-01-05', 'Maaş', 'Gelir', 9000)
    db.session.commit()

    from engines.financial_engine import get_monthly_dashboard_data

    months, _, _ = get_monthly_dashboard_data(2025, tenant_a.id)

    assert months[0]['inc'] == 1000


def test_monthly_dashboard_data_separates_paid_pending_and_valuation(app):
    tenant = _add_tenant('monthly_split', 'Monthly Split')
    _add_paid_tx(tenant.id, '2025-01-05', 'Maaş', 'Gelir', 5000)
    _add_paid_tx(tenant.id, '2025-01-10', 'Kira', 'Gider', 1000)
    _add_paid_tx(tenant.id, '2025-01-12', 'Yatırıma Aktarılan', 'Yatırım', 750)
    _add_paid_tx(tenant.id, '2025-01-20', 'Maaş', 'Gelir', 2000, status='Bekliyor')
    _add_paid_tx(tenant.id, '2025-01-22', 'Kira', 'Gider', 300, status='Bekliyor')
    _add_asset(tenant.id, 'VALUED', 1200, 1000)
    db.session.flush()
    asset = Asset.query.filter_by(tenant_id=tenant.id, name='VALUED').first()
    db.session.add(AssetUpdate(
        asset_id=asset.id,
        old_value=1000,
        new_value=1200,
        old_unit_price=1000,
        new_unit_price=1200,
        update_type='manual',
        updated_at=datetime(2025, 1, 15),
    ))
    db.session.commit()

    from engines.financial_engine import get_monthly_dashboard_data

    months, _, _ = get_monthly_dashboard_data(2025, tenant.id)
    january = months[0]

    assert january['inc_paid'] == 5000
    assert january['exp_paid'] == 1000
    assert january['inv_paid'] == 750
    assert january['inc_pending'] == 2000
    assert january['exp_pending'] == 300
    assert january['realized_net'] == 3250
    assert january['pending_net'] == 1700
    assert january['projected_net'] == january['net'] == 4950
    assert january['valuation_delta'] == 200


def test_investment_performance_is_tenant_scoped(app):
    tenant_a = _add_tenant('perf_a', 'Performance A')
    tenant_b = _add_tenant('perf_b', 'Performance B')
    _add_asset(tenant_a.id, 'PERF_A', 1200, 1000)
    _add_asset(tenant_b.id, 'PERF_B', 9000, 1000)
    db.session.commit()

    from domain.portfolio.services.investment_performance import get_yearly_performance

    result = get_yearly_performance(tenant_a.id)
    year = 2025

    assert result['yearly_data'][year]['total_value'] == 1200
    assert result['yearly_data'][year]['total_cost'] == 1000


def test_cash_trend_carries_forward_prior_year_balance(app):
    tenant = _add_tenant('carry_cash', 'Carry Cash')
    _add_paid_tx(tenant.id, '2024-12-20', 'Maaş', 'Gelir', 1000)
    _add_paid_tx(tenant.id, '2025-01-05', 'Kira', 'Gider', 200)
    _add_paid_tx(tenant.id, '2025-01-12', 'Maaş', 'Gelir', 300, status='Bekliyor')
    db.session.commit()

    from engines.financial_engine import calculate_cash_trend

    txs = Transaction.query.filter_by(tenant_id=tenant.id).all()
    trend = calculate_cash_trend(datetime(2025, 1, 10), txs, 5)

    assert trend[0] == 800
    assert trend[1] == 800
    assert trend[2] == 1100


def test_monthly_daily_balance_carries_forward_prior_balance(app):
    tenant = _add_tenant('carry_month', 'Carry Month')
    _add_paid_tx(tenant.id, '2024-12-15', 'Maaş', 'Gelir', 2000)
    _add_paid_tx(tenant.id, '2025-01-03', 'Kira', 'Gider', 500, status='Bekliyor')
    db.session.commit()

    from engines.financial_engine import calculate_monthly_daily_balance

    txs = Transaction.query.filter_by(tenant_id=tenant.id).all()
    labels, data = calculate_monthly_daily_balance(2025, 1, txs)

    assert labels[0] == '2025-01-01'
    assert data[0] == 2000
    assert data[2] == 1500


def test_financial_freedom_uses_real_passive_income_not_roi(app):
    tenant = _add_tenant('freedom_passive', 'Freedom Passive')
    _add_paid_tx(tenant.id, '2025-01-05', 'Kira', 'Gider', 1200)
    db.session.add(Asset(
        tenant_id=tenant.id,
        type='Gayrimenkul',
        name='Değer Artan Varlık',
        value=240000,
        description='Pasif gelir üretmeyen değer artışı',
        purchase_date='2024-01-01',
        purchase_cost=120000,
        quantity=1,
        unit_price=240000,
        currency='TRY',
        symbol='HOUSE1',
        risk_level='Orta',
        liquidity='Yarı-Likit',
        sector_id=_sector_id(),
        monthly_rent=None,
    ))
    db.session.commit()

    from engines.financial_engine import get_financial_freedom_analysis

    result = get_financial_freedom_analysis(tenant.id)

    assert result['passive_income_potential'] == 0
    assert result['rental_income_monthly'] == 0
    assert result['income_replacement_pct'] == 0
    assert result['safe_withdrawal_monthly'] > 0
