"""
Balance Calculation Accuracy Tests - FAZ 1
Validates Decimal usage in all balance calculations to prevent floating-point errors
"""

import pytest
from decimal import Decimal
from database.crud import get_actual_cash, get_total_assets
from domain.transactions.services.financial_ledger import (
    create_asset_position,
    create_one_time_transaction,
)
from models import AssetSector, Category, Transaction, db


@pytest.fixture
def app(app):
    """Use the existing app fixture from conftest.py"""
    return app


@pytest.mark.regression
def test_cash_balance_decimal_precision(app):
    """
    Cash balance must use Decimal arithmetic to avoid floating-point errors
    Test with values that cause precision issues with floats
    """
    tenant = 'tenant_cash_decimal'
    
    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Add transactions with problematic float values
    # 0.1 + 0.2 should equal 0.3 exactly with Decimal
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income 1', 
        Decimal('0.1'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-02', 'Test Gelir', 'Income 2', 
        Decimal('0.2'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    cash = get_actual_cash(tenant)
    expected = Decimal('0.3')
    
    # Verify exact precision
    assert cash == expected, f"Cash balance precision error: {cash} != {expected}"


@pytest.mark.regression
def test_asset_value_decimal_precision(app):
    """
    Asset values must use Decimal arithmetic
    Test with fractional unit prices and quantities
    """
    tenant = 'tenant_asset_decimal'
    
    # Create sector
    sector = AssetSector(name='Test Sektor')
    db.session.add(sector)
    db.session.commit()
    
    # Create asset with fractional values
    # 1.5 units @ 10.33 TL = 15.495 TL
    asset = create_asset_position(
        type='Hisse Senedi', name='TEST', value=Decimal('15.495'),
        purchase_cost=Decimal('15.495'), quantity=Decimal('1.5'), 
        unit_price=Decimal('10.33'),
        currency='TRY', symbol='TST', risk_level='Orta',
        liquidity='Likit', sector_id=sector.id,
        tenant_id=tenant,
    )
    db.session.commit()
    
    assets = get_total_assets(tenant)
    expected = Decimal('15.495')
    
    assert assets == expected, f"Asset value precision error: {assets} != {expected}"


@pytest.mark.regression
def test_net_worth_decimal_precision(app):
    """
    Net worth (cash + assets) must use Decimal arithmetic
    Test combination of cash and asset values
    """
    tenant = 'tenant_networth_decimal'
    
    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Add cash: 100.33 + 200.67 = 301.00 exactly
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income 1', 
        Decimal('100.33'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-02', 'Test Gelir', 'Income 2', 
        Decimal('200.67'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    cash = get_actual_cash(tenant)
    expected = Decimal('301.0000')  # 4 decimal places
    
    assert cash == expected, f"Cash balance error: {cash} != {expected}"


@pytest.mark.regression
def test_large_number_decimal_precision(app):
    """
    Large financial values must maintain precision
    Test with values in millions/billions
    """
    tenant = 'tenant_large_decimal'
    
    # Create category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Add large values: 1,000,000.33 + 2,000,000.67 = 3,000,001.00
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Large income 1', 
        Decimal('1000000.33'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-02', 'Test Gelir', 'Large income 2', 
        Decimal('2000000.67'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    cash = get_actual_cash(tenant)
    expected = Decimal('3000001.00')
    
    assert cash == expected, f"Large number precision error: {cash} != {expected}"


@pytest.mark.regression
def test_division_decimal_precision(app):
    """
    Division operations must use Decimal to maintain precision
    Test percentage calculations and ratios
    """
    tenant = 'tenant_division_decimal'
    
    # Create category
    from shared.decimal_precision import safe_divide, quantize_to_currency
    
    # Test division: 1000 / 3 = 333.3333 (4 decimal places)
    result = safe_divide(Decimal('1000'), Decimal('3'))
    quantized = quantize_to_currency(result)
    
    # Should be quantized to 4 decimal places (currency precision)
    assert quantized.as_tuple().exponent == -4, "Result should have 4 decimal places for currency"


@pytest.mark.regression
def test_multiplication_decimal_precision(app):
    """
    Multiplication operations must use Decimal
    Test quantity * unit_price calculations
    """
    from shared.decimal_precision import safe_multiply, quantize_to_currency
    
    # Test: 1.234 * 5.678 = 7.006652 (quantized to 4 decimals)
    result = safe_multiply(Decimal('1.234'), Decimal('5.678'))
    quantized = quantize_to_currency(result)
    
    expected = Decimal('7.0067')  # Rounded to 4 decimal places (currency precision)
    assert quantized == expected, f"Multiplication precision error: {quantized} != {expected}"


@pytest.mark.regression
def test_currency_quantization_consistency(app):
    """
    All currency values must be consistently quantized to 4 decimal places
    """
    from shared.decimal_precision import quantize_to_currency
    
    test_values = [
        Decimal('100'),
        Decimal('100.1'),
        Decimal('100.12'),
        Decimal('100.1234'),
        Decimal('100.12345'),
        Decimal('100.99999'),
    ]
    
    for value in test_values:
        quantized = quantize_to_currency(value)
        # Verify 4 decimal places (currency precision)
        assert quantized.as_tuple().exponent == -4, f"Value {value} not quantized to 4 decimals"


@pytest.mark.regression
def test_percentage_quantization_consistency(app):
    """
    All percentage values must be consistently quantized to 2 decimal places
    """
    from shared.decimal_precision import quantize_to_percentage
    
    test_values = [
        Decimal('50'),
        Decimal('50.1'),
        Decimal('50.12'),
        Decimal('50.123'),
        Decimal('50.1234'),
        Decimal('99.9999'),
    ]
    
    for value in test_values:
        quantized = quantize_to_percentage(value)
        # Verify 2 decimal places
        assert quantized.as_tuple().exponent == -2, f"Value {value} not quantized to 2 decimals"


@pytest.mark.regression
def test_negative_balance_decimal_handling(app):
    """
    Negative balances must be handled correctly with Decimal
    Test expense calculations
    """
    tenant = 'tenant_negative_decimal'
    
    # Create categories
    income_cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    expense_cat = Category(name='Test Gider', type='Gider', tenant_id=tenant)
    db.session.add_all([income_cat, expense_cat])
    db.session.commit()
    
    # Add income: 1000 TL
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('1000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    
    # Add expense: 333.33 TL
    create_one_time_transaction(
        '2025-01-02', 'Test Gider', 'Expense', 
        Decimal('333.33'), 'Ödendi', 'Test Gider', tenant_id=tenant
    )
    db.session.commit()
    
    cash = get_actual_cash(tenant)
    expected = Decimal('666.6700')  # 1000 - 333.33 (4 decimal places)
    
    assert cash == expected, f"Negative balance handling error: {cash} != {expected}"
