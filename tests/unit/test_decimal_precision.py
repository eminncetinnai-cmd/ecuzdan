"""
Unit Tests - Decimal Precision
Financial Precision Module - Decimal Context for Financial Calculations tests
"""

from decimal import ROUND_HALF_EVEN, Decimal

import pytest

from shared.decimal_precision import (
    FINANCIAL_CONTEXT,
    get_decimal_context,
    quantize,
    quantize_to_currency,
    quantize_to_percentage,
    safe_add,
    safe_divide,
    safe_multiply,
    safe_subtract,
    to_decimal,
)


@pytest.mark.unit
def test_decimal_precision_module_imports():
    """Test decimal_precision module can be imported"""
    from shared.decimal_precision import Decimal, get_decimal_context
    assert Decimal is not None
    assert get_decimal_context is not None


@pytest.mark.unit
def test_decimal_precision_module_structure():
    """Test decimal_precision module structure"""
    import shared.decimal_precision as precision_module

    # Check for expected exports
    assert hasattr(precision_module, 'Decimal')
    assert hasattr(precision_module, 'get_decimal_context')
    assert hasattr(precision_module, 'to_decimal')
    assert hasattr(precision_module, 'quantize')
    assert hasattr(precision_module, 'quantize_to_currency')
    assert hasattr(precision_module, 'quantize_to_percentage')
    assert hasattr(precision_module, 'safe_divide')
    assert hasattr(precision_module, 'safe_multiply')
    assert hasattr(precision_module, 'safe_add')
    assert hasattr(precision_module, 'safe_subtract')


@pytest.mark.unit
def test_financial_context_exists():
    """Test FINANCIAL_CONTEXT is defined"""
    assert FINANCIAL_CONTEXT is not None


@pytest.mark.unit
def test_financial_context_properties():
    """Test FINANCIAL_CONTEXT has correct properties"""
    assert FINANCIAL_CONTEXT.prec == 28
    assert FINANCIAL_CONTEXT.rounding == ROUND_HALF_EVEN


@pytest.mark.unit
def test_get_decimal_context():
    """Test get_decimal_context returns FINANCIAL_CONTEXT"""
    result = get_decimal_context()
    assert result is FINANCIAL_CONTEXT


@pytest.mark.unit
def test_to_decimal_from_string():
    """Test to_decimal converts string to Decimal"""
    result = to_decimal('100.50')
    assert result == Decimal('100.5000')


@pytest.mark.unit
def test_to_decimal_from_int():
    """Test to_decimal converts int to Decimal"""
    result = to_decimal(100)
    assert result == Decimal('100.0000')


@pytest.mark.unit
def test_to_decimal_from_float():
    """Test to_decimal converts float to Decimal"""
    result = to_decimal(100.50)
    assert result == Decimal('100.5000')


@pytest.mark.unit
def test_to_decimal_from_decimal():
    """Test to_decimal handles Decimal input"""
    input_decimal = Decimal('100.50')
    result = to_decimal(input_decimal)
    assert result == Decimal('100.5000')


@pytest.mark.unit
def test_to_decimal_custom_scale():
    """Test to_decimal with custom scale"""
    result = to_decimal('100.50', scale=2)
    assert result == Decimal('100.50')


@pytest.mark.unit
def test_to_decimal_invalid_type():
    """Test to_decimal raises TypeError for invalid type"""
    with pytest.raises(TypeError):
        to_decimal([100, 50])


@pytest.mark.unit
def test_to_decimal_float_precision():
    """Test to_decimal avoids float precision issues"""
    result = to_decimal('0.1') + to_decimal('0.2')
    assert result == Decimal('0.3000')


@pytest.mark.unit
def test_quantize():
    """Test quantize function"""
    value = Decimal('100.123456')
    result = quantize(value, scale=4)
    assert result == Decimal('100.1235')


@pytest.mark.unit
def test_quantize_default_scale():
    """Test quantize with default scale"""
    value = Decimal('100.123456')
    result = quantize(value)
    assert result == Decimal('100.1235')


@pytest.mark.unit
def test_quantize_rounding():
    """Test quantize uses ROUND_HALF_EVEN"""
    value = Decimal('100.12345')
    result = quantize(value, scale=4)
    assert result == Decimal('100.1234')


@pytest.mark.unit
def test_quantize_to_currency():
    """Test quantize_to_currency quantizes to 4 decimal places"""
    result = quantize_to_currency('100.123456')
    assert result == Decimal('100.1235')


@pytest.mark.unit
def test_quantize_to_currency_from_decimal():
    """Test quantize_to_currency with Decimal input"""
    result = quantize_to_currency(Decimal('100.123456'))
    assert result == Decimal('100.1235')


@pytest.mark.unit
def test_quantize_to_percentage():
    """Test quantize_to_percentage quantizes to 2 decimal places"""
    result = quantize_to_percentage('100.123456')
    assert result == Decimal('100.12')


@pytest.mark.unit
def test_quantize_to_percentage_from_decimal():
    """Test quantize_to_percentage with Decimal input"""
    result = quantize_to_percentage(Decimal('100.123456'))
    assert result == Decimal('100.12')


@pytest.mark.unit
def test_safe_divide():
    """Test safe_divide performs division"""
    result = safe_divide('100', '4')
    assert result == Decimal('25.0000')


@pytest.mark.unit
def test_safe_divide_custom_scale():
    """Test safe_divide with custom scale"""
    result = safe_divide('100', '3', scale=2)
    assert result == Decimal('33.33')


@pytest.mark.unit
def test_safe_divide_zero_denominator():
    """Test safe_divide raises ZeroDivisionError for zero denominator"""
    with pytest.raises(ZeroDivisionError):
        safe_divide('100', '0')


@pytest.mark.unit
def test_safe_divide_decimal_inputs():
    """Test safe_divide with Decimal inputs"""
    result = safe_divide(Decimal('100'), Decimal('4'))
    assert result == Decimal('25.0000')


@pytest.mark.unit
def test_safe_multiply():
    """Test safe_multiply performs multiplication"""
    result = safe_multiply('10', '5')
    assert result == Decimal('50.0000')


@pytest.mark.unit
def test_safe_multiply_custom_scale():
    """Test safe_multiply with custom scale"""
    result = safe_multiply('10.5', '2', scale=2)
    assert result == Decimal('21.00')


@pytest.mark.unit
def test_safe_multiply_decimal_inputs():
    """Test safe_multiply with Decimal inputs"""
    result = safe_multiply(Decimal('10'), Decimal('5'))
    assert result == Decimal('50.0000')


@pytest.mark.unit
def test_safe_add():
    """Test safe_add performs addition"""
    result = safe_add('10', '5')
    assert result == Decimal('15.0000')


@pytest.mark.unit
def test_safe_add_custom_scale():
    """Test safe_add with custom scale"""
    result = safe_add('10.5', '2.3', scale=2)
    assert result == Decimal('12.80')


@pytest.mark.unit
def test_safe_add_decimal_inputs():
    """Test safe_add with Decimal inputs"""
    result = safe_add(Decimal('10'), Decimal('5'))
    assert result == Decimal('15.0000')


@pytest.mark.unit
def test_safe_subtract():
    """Test safe_subtract performs subtraction"""
    result = safe_subtract('10', '5')
    assert result == Decimal('5.0000')


@pytest.mark.unit
def test_safe_subtract_custom_scale():
    """Test safe_subtract with custom scale"""
    result = safe_subtract('10.5', '2.3', scale=2)
    assert result == Decimal('8.20')


@pytest.mark.unit
def test_safe_subtract_decimal_inputs():
    """Test safe_subtract with Decimal inputs"""
    result = safe_subtract(Decimal('10'), Decimal('5'))
    assert result == Decimal('5.0000')


@pytest.mark.unit
def test_to_decimal_negative_value():
    """Test to_decimal handles negative values"""
    result = to_decimal('-100.50')
    assert result == Decimal('-100.5000')


@pytest.mark.unit
def test_to_decimal_zero():
    """Test to_decimal handles zero"""
    result = to_decimal('0')
    assert result == Decimal('0.0000')


@pytest.mark.unit
def test_quantize_negative_value():
    """Test quantize handles negative values"""
    value = Decimal('-100.123456')
    result = quantize(value, scale=4)
    assert result == Decimal('-100.1235')


@pytest.mark.unit
def test_safe_divide_negative_values():
    """Test safe_divide handles negative values"""
    result = safe_divide('-100', '4')
    assert result == Decimal('-25.0000')


@pytest.mark.unit
def test_safe_multiply_negative_values():
    """Test safe_multiply handles negative values"""
    result = safe_multiply('-10', '5')
    assert result == Decimal('-50.0000')


@pytest.mark.unit
def test_safe_add_negative_values():
    """Test safe_add handles negative values"""
    result = safe_add('-10', '5')
    assert result == Decimal('-5.0000')


@pytest.mark.unit
def test_safe_subtract_negative_values():
    """Test safe_subtract handles negative values"""
    result = safe_subtract('-10', '5')
    assert result == Decimal('-15.0000')


@pytest.mark.unit
def test_global_context_setup():
    """Test global context is properly configured"""
    from decimal import getcontext
    ctx = getcontext()
    assert ctx.prec == 28
    assert ctx.rounding == ROUND_HALF_EVEN


@pytest.mark.unit
def test_to_decimal_string_conversion():
    """Test to_decimal string conversion path"""
    result = to_decimal('123.456')
    assert result == Decimal('123.4560')


@pytest.mark.unit
def test_to_decimal_int_conversion():
    """Test to_decimal int conversion path"""
    result = to_decimal(42)
    assert result == Decimal('42.0000')


@pytest.mark.unit
def test_to_decimal_float_conversion():
    """Test to_decimal float conversion path"""
    result = to_decimal(3.14159)
    assert result == Decimal('3.1416')


@pytest.mark.unit
def test_to_decimal_decimal_passthrough():
    """Test to_decimal Decimal passthrough path"""
    result = to_decimal(Decimal('99.99'))
    assert result == Decimal('99.9900')


@pytest.mark.unit
def test_quantize_scaleb():
    """Test quantize uses scaleb correctly"""
    value = Decimal('100.123456')
    result = quantize(value, scale=6)
    assert result == Decimal('100.123456')


@pytest.mark.unit
def test_quantize_to_currency_scale():
    """Test quantize_to_currency uses scale 4"""
    result = quantize_to_currency('123.456789')
    assert result == Decimal('123.4568')


@pytest.mark.unit
def test_quantize_to_percentage_scale():
    """Test quantize_to_percentage uses scale 2"""
    result = quantize_to_percentage('123.456789')
    assert result == Decimal('123.46')


@pytest.mark.unit
def test_safe_divide_conversion():
    """Test safe_divide converts inputs properly"""
    result = safe_divide(100, 4)
    assert result == Decimal('25.0000')


@pytest.mark.unit
def test_safe_divide_result_quantization():
    """Test safe_divide quantizes result"""
    result = safe_divide('100', '3', scale=4)
    assert result == Decimal('33.3333')


@pytest.mark.unit
def test_safe_multiply_conversion():
    """Test safe_multiply converts inputs properly"""
    result = safe_multiply(10, 5)
    assert result == Decimal('50.0000')


@pytest.mark.unit
def test_safe_multiply_result_quantization():
    """Test safe_multiply quantizes result"""
    result = safe_multiply('10.12345', '2', scale=4)
    assert result == Decimal('20.2468')


@pytest.mark.unit
def test_safe_add_conversion():
    """Test safe_add converts inputs properly"""
    result = safe_add(10, 5)
    assert result == Decimal('15.0000')


@pytest.mark.unit
def test_safe_add_result_quantization():
    """Test safe_add quantizes result"""
    result = safe_add('10.12345', '2.12345', scale=4)
    assert result == Decimal('12.2468')


@pytest.mark.unit
def test_safe_subtract_conversion():
    """Test safe_subtract converts inputs properly"""
    result = safe_subtract(10, 5)
    assert result == Decimal('5.0000')


@pytest.mark.unit
def test_safe_subtract_result_quantization():
    """Test safe_subtract quantizes result"""
    result = safe_subtract('10.12345', '2.12345', scale=4)
    assert result == Decimal('8.0000')


# Sprint01 Financial Calculation Scenarios
@pytest.mark.unit
def test_classic_float_issue():
    """Test 0.1 + 0.2 - classic float precision issue."""
    # Float version (fails): 0.1 + 0.2 == 0.30000000000000004
    float_result = 0.1 + 0.2
    assert float_result != 0.3, "Float has precision issue"

    # Decimal version (passes)
    dec_result = to_decimal('0.1') + to_decimal('0.2')
    assert dec_result == to_decimal('0.3'), "Decimal has exact precision"


@pytest.mark.unit
def test_large_number_with_decimals():
    """Test 999999999.9999 - large number with decimals."""
    value = to_decimal('999999999.9999')
    assert value == Decimal('999999999.9999')
    assert quantize_to_currency(value) == Decimal('999999999.9999')


@pytest.mark.unit
def test_small_precision():
    """Test 0.0001 - small precision."""
    value = to_decimal('0.0001')
    assert value == Decimal('0.0001')
    assert quantize_to_currency(value) == Decimal('0.0001')


@pytest.mark.unit
def test_very_large_number():
    """Test 100000000000 - very large number."""
    value = to_decimal('100000000000')
    assert value == Decimal('100000000000')
    assert quantize_to_currency(value) == Decimal('100000000000.0000')


@pytest.mark.unit
def test_division_repeating_decimals():
    """Test 10/3 - division with repeating decimals."""
    result = safe_divide('10', '3', scale=4)
    assert result == Decimal('3.3333')


@pytest.mark.unit
def test_rounding_edge_case():
    """Test 1.005 - rounding edge case."""
    value = to_decimal('1.005')
    quantized = quantize(value, scale=2)
    # Should round to even number (1.00 or 1.01)
    assert quantized in [Decimal('1.00'), Decimal('1.01')]


@pytest.mark.unit
def test_kdv_calculation():
    """Test KDV (VAT) calculation - 18% tax."""
    amount = to_decimal('100')
    tax_rate = to_decimal('0.18')
    tax = safe_multiply(amount, tax_rate)
    total = safe_add(amount, tax)

    assert tax == Decimal('18.0000')
    assert total == Decimal('118.0000')


@pytest.mark.unit
def test_commission_calculation():
    """Test commission calculation - 0.5% commission."""
    amount = to_decimal('10000')
    commission_rate = to_decimal('0.005')
    commission = safe_multiply(amount, commission_rate)
    net_amount = safe_subtract(amount, commission)

    assert commission == Decimal('50.0000')
    assert net_amount == Decimal('9950.0000')


@pytest.mark.unit
def test_interest_calculation():
    """Test interest calculation - 40% annual interest."""
    principal = to_decimal('10000')
    rate = to_decimal('0.40')
    interest = safe_multiply(principal, rate)
    total = safe_add(principal, interest)

    assert interest == Decimal('4000.0000')
    assert total == Decimal('14000.0000')


@pytest.mark.unit
def test_currency_conversion():
    """Test currency conversion - USD to TRY."""
    usd_amount = to_decimal('100')
    exchange_rate = to_decimal('32.50')
    try_amount = safe_multiply(usd_amount, exchange_rate)

    assert try_amount == Decimal('3250.0000')


@pytest.mark.unit
def test_gold_gram_calculation():
    """Test gold gram calculation."""
    gram_price = to_decimal('2500.50')
    grams = to_decimal('5.5')
    total = safe_multiply(gram_price, grams)

    assert total == Decimal('13752.7500')


@pytest.mark.unit
def test_fund_calculation():
    """Test fund unit calculation."""
    fund_price = to_decimal('15.75')
    units = to_decimal('100.5')
    total = safe_multiply(fund_price, units)

    assert total == Decimal('1582.8750')


@pytest.mark.unit
def test_crypto_calculation():
    """Test crypto calculation - BTC."""
    btc_price = to_decimal('60000')
    btc_amount = to_decimal('0.5')
    total = safe_multiply(btc_price, btc_amount)

    assert total == Decimal('30000.0000')


@pytest.mark.unit
def test_stock_calculation():
    """Test stock calculation."""
    stock_price = to_decimal('150.25')
    shares = to_decimal('100')
    total = safe_multiply(stock_price, shares)

    assert total == Decimal('15025.0000')


@pytest.mark.unit
def test_weighted_average_cost():
    """Test weighted average cost calculation."""
    # Buy 100 units at 10
    buy1_qty = to_decimal('100')
    buy1_price = to_decimal('10')
    buy1_cost = safe_multiply(buy1_qty, buy1_price)

    # Buy 50 units at 15
    buy2_qty = to_decimal('50')
    buy2_price = to_decimal('15')
    buy2_cost = safe_multiply(buy2_qty, buy2_price)

    # Calculate weighted average
    total_qty = safe_add(buy1_qty, buy2_qty)
    total_cost = safe_add(buy1_cost, buy2_cost)
    avg_cost = safe_divide(total_cost, total_qty)

    assert avg_cost == Decimal('11.6667')


@pytest.mark.unit
def test_roi_calculation():
    """Test ROI calculation."""
    purchase_cost = to_decimal('50000')
    current_value = to_decimal('60000')
    profit = safe_subtract(current_value, purchase_cost)
    roi = safe_divide(profit, purchase_cost, scale=4)
    roi_pct = safe_multiply(roi, to_decimal('100'))

    assert roi_pct == Decimal('20.0000')


@pytest.mark.unit
def test_realized_gain():
    """Test realized gain calculation."""
    buy_price = to_decimal('100')
    sell_price = to_decimal('120')
    quantity = to_decimal('10')

    buy_cost = safe_multiply(buy_price, quantity)
    sell_revenue = safe_multiply(sell_price, quantity)
    gain = safe_subtract(sell_revenue, buy_cost)

    assert gain == Decimal('200.0000')


@pytest.mark.unit
def test_round_half_even_1():
    """Test 2.5 rounds to 2 (even)."""
    value = to_decimal('2.5')
    quantized = quantize(value, scale=0)
    assert quantized == Decimal('2')


@pytest.mark.unit
def test_round_half_even_2():
    """Test 3.5 rounds to 4 (even)."""
    value = to_decimal('3.5')
    quantized = quantize(value, scale=0)
    assert quantized == Decimal('4')


@pytest.mark.unit
def test_round_half_even_3():
    """Test 2.4 rounds to 2 (down)."""
    value = to_decimal('2.4')
    quantized = quantize(value, scale=0)
    assert quantized == Decimal('2')


@pytest.mark.unit
def test_round_half_even_4():
    """Test 2.6 rounds to 3 (up)."""
    value = to_decimal('2.6')
    quantized = quantize(value, scale=0)
    assert quantized == Decimal('3')


@pytest.mark.unit
def test_complex_calculation():
    """Test complex financial calculation."""
    # Portfolio value calculation
    asset1_value = to_decimal('10000')
    asset2_value = to_decimal('25000')
    asset3_value = to_decimal('15000')

    total = safe_add(asset1_value, asset2_value)
    total = safe_add(total, asset3_value)

    assert total == Decimal('50000.0000')

    # Calculate percentages
    pct1 = safe_divide(asset1_value, total, scale=4)
    pct1 = safe_multiply(pct1, to_decimal('100'))

    assert pct1 == Decimal('20.0000')
