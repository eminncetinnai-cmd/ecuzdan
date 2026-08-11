"""
Unit Tests - Financial Engine
Financial engine fonksiyonları için testler
"""

import pytest

from engines.financial_engine import format_date, format_money, parse_date_input, today_display, today_storage


def test_format_money():
    """Para formatlama testi"""
    assert format_money(1000) == "1.000,00"
    assert format_money(1000.50) == "1.000,50"
    assert format_money(0) == "0,00"
    assert format_money(1000000) == "1.000.000,00"

def test_format_date():
    """Tarih formatlama testi"""
    assert format_date("2025-01-01") == "01/01/2025"
    assert format_date("2025-12-31") == "31/12/2025"
    assert format_date("") == ""
    assert format_date(None) == ""

def test_parse_date_input():
    """Tarih parse etme testi"""
    assert parse_date_input("01/01/2025") == "2025-01-01"
    assert parse_date_input("01.01.2025") == "2025-01-01"
    assert parse_date_input("2025-01-01") == "2025-01-01"

    with pytest.raises(ValueError):
        parse_date_input("")

    with pytest.raises(ValueError):
        parse_date_input("invalid")

def test_today_storage():
    """Bugünün tarihi storage formatında testi"""
    today = today_storage()
    assert len(today) == 10  # YYYY-MM-DD formatı
    assert today[4] == '-'
    assert today[7] == '-'

def test_today_display():
    """Bugünün tarihi display formatında testi"""
    today = today_display()
    assert len(today) == 10  # DD/MM/YYYY formatı
    assert today[2] == '/'
    assert today[5] == '/'


def test_years_to_financial_independence():
  from engines.financial_engine import _years_to_financial_independence
  assert _years_to_financial_independence(0, 5000, 10000) is not None
  assert _years_to_financial_independence(3_000_000, 0, 10000) == 0.0
  assert _years_to_financial_independence(0, 0, 10000) is None


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


def test_empty_freedom_analysis():
  from engines.financial_engine import get_empty_freedom_analysis
  empty = get_empty_freedom_analysis()
  assert empty['freedom_score'] == 0
  assert empty['criteria'] == []
