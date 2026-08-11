"""
Unit Tests - Routes Utilities
Routes ve utilities için unit testleri
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
def test_format_utils_format_money():
    """Para formatlama testi"""
    from utils.format_utils import format_money
    
    result = format_money(1000.50)
    assert '1000.50' in result or '1.000,50' in result


@pytest.mark.unit
def test_format_utils_format_date():
    """Tarih formatlama testi"""
    from utils.format_utils import format_date
    
    result = format_date('2025-01-15')
    assert '15' in result or '01' in result or '2025' in result


@pytest.mark.unit
def test_format_utils_parse_date_input():
    """Tarih parse testi"""
    from utils.format_utils import parse_date_input
    
    result = parse_date_input('15/01/2025')
    assert result == '2025-01-15'


@pytest.mark.unit
def test_format_utils_today_storage():
    """Bugünün tarihi storage formatında testi"""
    from utils.format_utils import today_storage
    
    result = today_storage()
    assert len(result) == 10  # yyyy-mm-dd format
    assert '-' in result


@pytest.mark.unit
def test_format_utils_today_display():
    """Bugünün tarihi display formatında testi"""
    from utils.format_utils import today_display
    
    result = today_display()
    assert '/' in result  # gg/aa/yyyy format


@pytest.mark.unit
def test_format_utils_format_money_zero():
    """Sıfır para formatlama testi"""
    from utils.format_utils import format_money
    
    result = format_money(0)
    assert '0,00' in result or '0.00' in result


@pytest.mark.unit
def test_format_utils_format_money_none():
    """None para formatlama testi"""
    from utils.format_utils import format_money
    
    result = format_money(None)
    assert '0,00' in result or '0.00' in result


@pytest.mark.unit
def test_format_utils_format_date_none():
    """None tarih formatlama testi"""
    from utils.format_utils import format_date
    
    result = format_date(None)
    assert result == ''


@pytest.mark.unit
def test_format_utils_parse_date_invalid():
    """Geçersiz tarih parse testi"""
    from utils.format_utils import parse_date_input
    
    try:
        parse_date_input('invalid_date')
        assert False  # Should raise ValueError
    except ValueError:
        assert True  # Expected to raise ValueError
