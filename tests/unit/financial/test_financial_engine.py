"""
Unit Tests - Financial Engine
Financial engine fonksiyonları için testler
"""

import pytest
from datetime import datetime
from decimal import Decimal

from engines.financial_engine import (
    format_date,
    format_money,
    parse_date_input,
    today_display,
    today_storage,
    _resolve_tenant_id,
    _apply_tenant,
    _as_decimal,
    _safe_percentage,
    get_live_data,
    CACHE_TTL,
    LIVE_DATA_CACHE,
    FINANCIAL_ANALYSIS_CACHE,
    MONTHLY_DASHBOARD_CACHE
)


@pytest.mark.unit
def test_format_money():
    """Para formatlama testi"""
    assert format_money(1000) == "1.000,00"
    assert format_money(1000.50) == "1.000,50"
    assert format_money(0) == "0,00"
    assert format_money(1000000) == "1.000.000,00"


@pytest.mark.unit
def test_format_date():
    """Tarih formatlama testi"""
    assert format_date("2025-01-01") == "01/01/2025"
    assert format_date("2025-12-31") == "31/12/2025"
    assert format_date("") == ""
    assert format_date(None) == ""


@pytest.mark.unit
def test_parse_date_input():
    """Tarih parse etme testi"""
    assert parse_date_input("01/01/2025") == "2025-01-01"
    assert parse_date_input("01.01.2025") == "2025-01-01"
    assert parse_date_input("2025-01-01") == "2025-01-01"

    with pytest.raises(ValueError):
        parse_date_input("")

    with pytest.raises(ValueError):
        parse_date_input("invalid")


@pytest.mark.unit
def test_today_storage():
    """Bugünün tarihi storage formatında testi"""
    today = today_storage()
    assert len(today) == 10  # YYYY-MM-DD formatı
    assert today[4] == '-'
    assert today[7] == '-'


@pytest.mark.unit
def test_today_display():
    """Bugünün tarihi display formatında testi"""
    today = today_display()
    assert len(today) == 10  # DD/MM/YYYY formatı
    assert today[2] == '/'
    assert today[5] == '/'


@pytest.mark.unit
def test_resolve_tenant_id_with_param():
    """Test _resolve_tenant_id with explicit tenant_id parameter"""
    result = _resolve_tenant_id('test-tenant')
    assert result == 'test-tenant'


@pytest.mark.unit
def test_resolve_tenant_id_without_param():
    """Test _resolve_tenant_id without parameter (returns None outside Flask context)"""
    result = _resolve_tenant_id()
    assert result is None


@pytest.mark.unit
def test_as_decimal_with_value():
    """Test _as_decimal with valid value"""
    result = _as_decimal(100.50)
    assert isinstance(result, Decimal)
    assert result == Decimal('100.5000')


@pytest.mark.unit
def test_as_decimal_with_none():
    """Test _as_decimal with None returns 0"""
    result = _as_decimal(None)
    assert result == Decimal('0')


@pytest.mark.unit
def test_as_decimal_with_zero():
    """Test _as_decimal with 0"""
    result = _as_decimal(0)
    assert result == Decimal('0')


@pytest.mark.unit
def test_as_decimal_with_scale():
    """Test _as_decimal with custom scale"""
    result = _as_decimal(100.50, scale=2)
    assert result == Decimal('100.50')


@pytest.mark.unit
def test_safe_percentage_valid():
    """Test _safe_percentage with valid values"""
    result = _safe_percentage(50, 100)
    assert result == Decimal('50')


@pytest.mark.unit
def test_safe_percentage_zero_denominator():
    """Test _safe_percentage with zero denominator returns 0"""
    result = _safe_percentage(50, 0)
    assert result == 0


@pytest.mark.unit
def test_safe_percentage_negative_denominator():
    """Test _safe_percentage with negative denominator returns 0"""
    result = _safe_percentage(50, -10)
    assert result == 0


@pytest.mark.unit
def test_safe_percentage_zero_numerator():
    """Test _safe_percentage with zero numerator"""
    result = _safe_percentage(0, 100)
    assert result == Decimal('0')


@pytest.mark.unit
def test_get_live_data():
    """Test get_live_data returns dict with expected keys"""
    result = get_live_data()
    assert isinstance(result, dict)
    assert 'weather' in result
    assert 'usd' in result
    assert 'eur' in result
    assert 'gold' in result
    assert 'last_updated' in result


@pytest.mark.unit
def test_cache_constants():
    """Test cache constants are defined"""
    assert CACHE_TTL == 300
    assert isinstance(LIVE_DATA_CACHE, dict)
    assert isinstance(FINANCIAL_ANALYSIS_CACHE, dict)
    assert isinstance(MONTHLY_DASHBOARD_CACHE, dict)
    assert 'data' in LIVE_DATA_CACHE
    assert 'last_fetched' in LIVE_DATA_CACHE


@pytest.mark.unit
def test_years_to_financial_independence():
    from engines.financial_engine import _years_to_financial_independence
    assert _years_to_financial_independence(0, 5000, 10000) is not None
    assert _years_to_financial_independence(3_000_000, 0, 10000) == 0.0
    assert _years_to_financial_independence(0, 0, 10000) is None


@pytest.mark.unit
def test_financial_freedom_analysis(app):
    from datetime import datetime, timedelta

    from engines.financial_engine import get_financial_freedom_analysis
    from models import Transaction, db

    today = datetime.now()
    for i in range(12):
        d = (today - timedelta(days=30 * i)).strftime('%Y-%m-%d')
        db.session.add(Transaction(
            date=d, category='Maaş', type='Gelir',
            amount=30000, status='Ödendi', description='Maaş',
            tenant_id='default'
        ))
        db.session.add(Transaction(
            date=d, category='Kira', type='Gider',
            amount=10000, status='Ödendi', description='Kira',
            tenant_id='default'
        ))
    db.session.commit()

    result = get_financial_freedom_analysis()
    assert result['monthly_avg_income'] == 30000
    assert result['monthly_avg_expenses'] == 10000
    assert result['savings_rate'] > 60
    assert result['fi_number'] == 10000 * 12 * 25
    assert len(result['criteria']) == 6
    assert 'freedom_stage' in result
    assert result['freedom_score'] > 0


@pytest.mark.unit
def test_empty_freedom_analysis():
    from engines.financial_engine import get_empty_freedom_analysis
    empty = get_empty_freedom_analysis()
    assert empty['freedom_score'] == 0
    assert empty['criteria'] == []
