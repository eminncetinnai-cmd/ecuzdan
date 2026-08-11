"""
Unit Tests - Money Class
Financial operations with proper precision and currency support
"""

import pytest
from decimal import Decimal
from shared.money import Money, money, sum_money


@pytest.mark.unit
def test_money_init_string():
    """Test Money initialization with string amount"""
    m = Money('100.50', 'TRY')
    assert m.amount == Decimal('100.50')
    assert m.currency == 'TRY'


@pytest.mark.unit
def test_money_init_int():
    """Test Money initialization with int amount"""
    m = Money(100, 'USD')
    assert m.amount == Decimal('100')
    assert m.currency == 'USD'


@pytest.mark.unit
def test_money_init_float():
    """Test Money initialization with float amount"""
    m = Money(100.50, 'EUR')
    assert m.amount == Decimal('100.50')
    assert m.currency == 'EUR'


@pytest.mark.unit
def test_money_init_decimal():
    """Test Money initialization with Decimal amount"""
    m = Money(Decimal('100.50'), 'GBP')
    assert m.amount == Decimal('100.50')
    assert m.currency == 'GBP'


@pytest.mark.unit
def test_money_init_default_currency():
    """Test Money initialization with default currency"""
    m = Money('100')
    assert m.currency == 'TRY'


@pytest.mark.unit
def test_money_init_currency_uppercase():
    """Test Money initialization converts currency to uppercase"""
    m = Money('100', 'try')
    assert m.currency == 'TRY'


@pytest.mark.unit
def test_money_scale_property():
    """Test Money scale property"""
    m_try = Money('100.50', 'TRY')
    assert m_try.scale == 2
    
    m_btc = Money('0.5', 'BTC')
    assert m_btc.scale == 8


@pytest.mark.unit
def test_money_add_same_currency():
    """Test adding Money objects with same currency"""
    m1 = Money('100.50', 'TRY')
    m2 = Money('50.25', 'TRY')
    result = m1 + m2
    assert result.amount == Decimal('150.75')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_add_different_currency_raises():
    """Test adding Money objects with different currency raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('50', 'USD')
    with pytest.raises(ValueError, match="Cannot add TRY to USD"):
        m1 + m2


@pytest.mark.unit
def test_money_add_non_money_raises():
    """Test adding Money to non-Money raises error"""
    m = Money('100', 'TRY')
    with pytest.raises(TypeError, match="Can only add Money to Money"):
        m + 50


@pytest.mark.unit
def test_money_subtract_same_currency():
    """Test subtracting Money objects with same currency"""
    m1 = Money('100.50', 'TRY')
    m2 = Money('50.25', 'TRY')
    result = m1 - m2
    assert result.amount == Decimal('50.25')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_subtract_different_currency_raises():
    """Test subtracting Money objects with different currency raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('50', 'USD')
    with pytest.raises(ValueError, match="Cannot subtract USD from TRY"):
        m1 - m2


@pytest.mark.unit
def test_money_subtract_non_money_raises():
    """Test subtracting non-Money from Money raises error"""
    m = Money('100', 'TRY')
    with pytest.raises(TypeError, match="Can only subtract Money from Money"):
        m - 50


@pytest.mark.unit
def test_money_multiply_scalar():
    """Test multiplying Money by scalar"""
    m = Money('100', 'TRY')
    result = m * 2
    assert result.amount == Decimal('200')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_multiply_float():
    """Test multiplying Money by float"""
    m = Money('100', 'TRY')
    result = m * 1.5
    assert result.amount == Decimal('150')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_multiply_money_raises():
    """Test multiplying Money by Money raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('2', 'TRY')
    with pytest.raises(TypeError, match="Cannot multiply Money by Money"):
        m1 * m2


@pytest.mark.unit
def test_money_divide_scalar():
    """Test dividing Money by scalar"""
    m = Money('100', 'TRY')
    result = m / 2
    assert result.amount == Decimal('50')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_divide_zero_raises():
    """Test dividing Money by zero raises error"""
    m = Money('100', 'TRY')
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
        m / 0


@pytest.mark.unit
def test_money_divide_money_raises():
    """Test dividing Money by Money raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('2', 'TRY')
    with pytest.raises(TypeError, match="Cannot divide Money by Money"):
        m1 / m2


@pytest.mark.unit
def test_money_equality():
    """Test Money equality"""
    m1 = Money('100', 'TRY')
    m2 = Money('100', 'TRY')
    assert m1 == m2


@pytest.mark.unit
def test_money_inequality_different_amount():
    """Test Money inequality with different amount"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'TRY')
    assert m1 != m2


@pytest.mark.unit
def test_money_inequality_different_currency():
    """Test Money inequality with different currency"""
    m1 = Money('100', 'TRY')
    m2 = Money('100', 'USD')
    assert m1 != m2


@pytest.mark.unit
def test_money_equality_non_money():
    """Test Money equality with non-Money returns False"""
    m = Money('100', 'TRY')
    assert m != 100


@pytest.mark.unit
def test_money_less_than():
    """Test Money less than comparison"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'TRY')
    assert m1 < m2


@pytest.mark.unit
def test_money_less_than_different_currency_raises():
    """Test Money less than with different currency raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'USD')
    with pytest.raises(ValueError, match="Cannot compare TRY to USD"):
        m1 < m2


@pytest.mark.unit
def test_money_less_than_non_money_raises():
    """Test Money less than with non-Money raises error"""
    m = Money('100', 'TRY')
    with pytest.raises(TypeError, match="Can only compare Money to Money"):
        m < 200


@pytest.mark.unit
def test_money_less_than_or_equal():
    """Test Money less than or equal comparison"""
    m1 = Money('100', 'TRY')
    m2 = Money('100', 'TRY')
    m3 = Money('200', 'TRY')
    assert m1 <= m2
    assert m1 <= m3


@pytest.mark.unit
def test_money_greater_than():
    """Test Money greater than comparison"""
    m1 = Money('200', 'TRY')
    m2 = Money('100', 'TRY')
    assert m1 > m2


@pytest.mark.unit
def test_money_greater_than_or_equal():
    """Test Money greater than or equal comparison"""
    m1 = Money('200', 'TRY')
    m2 = Money('200', 'TRY')
    m3 = Money('100', 'TRY')
    assert m1 >= m2
    assert m1 >= m3


@pytest.mark.unit
def test_money_repr():
    """Test Money string representation"""
    m = Money('100.50', 'TRY')
    assert repr(m) == "Money(100.50, 'TRY')"


@pytest.mark.unit
def test_money_str():
    """Test Money formatted string"""
    m = Money('100.50', 'TRY')
    assert '100.50' in str(m)


@pytest.mark.unit
def test_money_format_with_symbol():
    """Test Money formatting with symbol"""
    m = Money('1000.50', 'TRY')
    formatted = m.format(show_symbol=True, locale='tr')
    assert '₺' in formatted
    assert '1.000,50' in formatted


@pytest.mark.unit
def test_money_format_without_symbol():
    """Test Money formatting without symbol"""
    m = Money('1000.50', 'TRY')
    formatted = m.format(show_symbol=False, locale='tr')
    assert 'TRY' in formatted
    assert '1.000,50' in formatted


@pytest.mark.unit
def test_money_format_international():
    """Test Money formatting with international locale"""
    m = Money('1000.50', 'USD')
    formatted = m.format(show_symbol=True, locale='en')
    assert '$' in formatted
    assert '1,000.50' in formatted


@pytest.mark.unit
def test_money_convert_to_same_currency():
    """Test converting to same currency returns new Money"""
    m = Money('100', 'TRY')
    result = m.convert_to('TRY')
    assert result.amount == Decimal('100')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_convert_to_with_rate():
    """Test currency conversion with rate"""
    m = Money('100', 'USD')
    result = m.convert_to('TRY', rate=Decimal('32'))
    assert result.amount == Decimal('3200')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_convert_to_without_rate_raises():
    """Test currency conversion without rate raises error"""
    m = Money('100', 'USD')
    with pytest.raises(ValueError, match="Exchange rate required"):
        m.convert_to('TRY')


@pytest.mark.unit
def test_money_to_float():
    """Test converting Money to float"""
    m = Money('100.50', 'TRY')
    result = m.to_float()
    assert result == 100.50


@pytest.mark.unit
def test_money_to_decimal():
    """Test converting Money to Decimal"""
    m = Money('100.50', 'TRY')
    result = m.to_decimal()
    assert result == Decimal('100.50')


@pytest.mark.unit
def test_money_is_zero():
    """Test checking if Money is zero"""
    m = Money('0', 'TRY')
    assert m.is_zero()


@pytest.mark.unit
def test_money_is_positive():
    """Test checking if Money is positive"""
    m = Money('100', 'TRY')
    assert m.is_positive()


@pytest.mark.unit
def test_money_is_negative():
    """Test checking if Money is negative"""
    m = Money('-100', 'TRY')
    assert m.is_negative()


@pytest.mark.unit
def test_money_abs():
    """Test absolute value of Money"""
    m = Money('-100', 'TRY')
    result = m.abs()
    assert result.amount == Decimal('100')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_negate():
    """Test negating Money"""
    m = Money('100', 'TRY')
    result = m.negate()
    assert result.amount == Decimal('-100')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_zero_classmethod():
    """Test Money.zero classmethod"""
    m = Money.zero('TRY')
    assert m.amount == Decimal('0')
    assert m.currency == 'TRY'


@pytest.mark.unit
def test_money_sum_classmethod():
    """Test Money.sum classmethod"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'TRY')
    m3 = Money('300', 'TRY')
    result = Money.sum([m1, m2, m3])
    assert result.amount == Decimal('600')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_sum_empty_list_raises():
    """Test Money.sum with empty list raises error"""
    with pytest.raises(ValueError, match="Cannot sum empty list"):
        Money.sum([])


@pytest.mark.unit
def test_money_sum_different_currencies_raises():
    """Test Money.sum with different currencies raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'USD')
    with pytest.raises(ValueError, match="All Money objects must have same currency"):
        Money.sum([m1, m2])


@pytest.mark.unit
def test_money_from_string_with_symbol():
    """Test parsing Money from string with symbol"""
    m = Money.from_string('₺1234')
    assert m.currency == 'TRY'
    assert m.amount == Decimal('1234')


@pytest.mark.unit
def test_money_from_string_with_currency_code():
    """Test parsing Money from string with currency code"""
    m = Money.from_string('1234 USD')
    assert m.currency == 'USD'
    assert m.amount == Decimal('1234')


@pytest.mark.unit
def test_money_from_string_simple():
    """Test parsing Money from simple string"""
    m = Money.from_string('1234')
    assert m.currency == 'TRY'
    assert m.amount == Decimal('1234')


@pytest.mark.unit
def test_money_convenience_function():
    """Test money convenience function"""
    m = money('100', 'TRY')
    assert isinstance(m, Money)
    assert m.amount == Decimal('100')
    assert m.currency == 'TRY'


@pytest.mark.unit
def test_sum_money_convenience_function():
    """Test sum_money convenience function"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'TRY')
    result = sum_money([m1, m2])
    assert result.amount == Decimal('300')
    assert result.currency == 'TRY'


@pytest.mark.unit
def test_money_quantization():
    """Test Money quantization to currency scale"""
    m = Money('100.5678', 'TRY')
    assert m.amount == Decimal('100.57')  # 2 decimal places for TRY


@pytest.mark.unit
def test_money_btc_scale():
    """Test Money with BTC currency (8 decimal places)"""
    m = Money('0.123456789', 'BTC')
    # The quantization rounds to 8 decimal places
    assert m.scale == 8  # BTC has 8 decimal places


@pytest.mark.unit
def test_money_gram_scale():
    """Test Money with GRAM currency (3 decimal places)"""
    m = Money('100.5', 'GRAM')
    assert m.amount == Decimal('100.500')  # 3 decimal places for GRAM


@pytest.mark.unit
def test_money_greater_than_different_currency_raises():
    """Test Money greater than with different currency raises error"""
    m1 = Money('100', 'TRY')
    m2 = Money('200', 'USD')
    with pytest.raises(ValueError, match="Cannot compare TRY to USD"):
        m1 > m2


@pytest.mark.unit
def test_money_greater_than_non_money_raises():
    """Test Money greater than with non-Money raises error"""
    m = Money('100', 'TRY')
    with pytest.raises(TypeError, match="Can only compare Money to Money"):
        m > 200


@pytest.mark.unit
def test_money_format_default_locale():
    """Test Money formatting with default locale"""
    m = Money('1000.50', 'TRY')
    formatted = m.format()
    assert '₺' in formatted or 'TRY' in formatted


@pytest.mark.unit
def test_money_format_international_without_symbol():
    """Test Money formatting with international locale without symbol"""
    m = Money('1000.50', 'USD')
    formatted = m.format(show_symbol=False, locale='en')
    assert 'USD' in formatted
    assert '1,000.50' in formatted
