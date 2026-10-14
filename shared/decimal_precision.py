"""
Financial Precision Module - Decimal Context for Financial Calculations

This module provides a centralized Decimal context for all financial calculations
following banking-grade precision standards.

Standard: ROUND_HALF_EVEN (Banker's Rounding)
Precision: 28 digits (Python Decimal default)
Scale: 4 decimal places for currency (supports 0.0001 precision)

Usage:
    from shared.decimal_precision import Decimal, get_decimal_context

    # Use Decimal for all financial values
    amount = Decimal('100.50')
    result = amount * Decimal('0.18')  # VAT calculation

    # For currency display (4 decimal places)
    formatted = quantize_to_currency(amount)
"""

from decimal import ROUND_HALF_EVEN, Context, Decimal, getcontext
from typing import Union

# Financial Decimal Context - Banking Grade Standards
# ROUND_HALF_EVEN: Banker's rounding (rounds to nearest even number on .5)
# This is the standard for financial calculations to avoid systematic bias
FINANCIAL_CONTEXT = Context(
    prec=28,  # 28 digits precision (Python Decimal default)
    rounding=ROUND_HALF_EVEN,
    Emin=-999999,
    Emax=999999,
    capitals=1,
    clamp=0,
    flags=[],
    traps=[],
)

# Set as global context for this module
ctx = getcontext()
ctx.prec = FINANCIAL_CONTEXT.prec
ctx.rounding = FINANCIAL_CONTEXT.rounding
ctx.Emin = FINANCIAL_CONTEXT.Emin
ctx.Emax = FINANCIAL_CONTEXT.Emax
ctx.capitals = FINANCIAL_CONTEXT.capitals
ctx.clamp = FINANCIAL_CONTEXT.clamp


def get_decimal_context() -> Context:
    """Get the financial Decimal context."""
    return FINANCIAL_CONTEXT


def to_decimal(value: Union[str, int, float, Decimal], scale: int = 4) -> Decimal:
    """
    Convert a value to Decimal with proper precision.

    Args:
        value: Value to convert (string, int, float, or Decimal)
        scale: Number of decimal places (default: 4 for currency)

    Returns:
        Decimal: Quantized Decimal value

    Examples:
        >>> to_decimal('100.50')
        Decimal('100.5000')
        >>> to_decimal(100.50)
        Decimal('100.5000')
        >>> to_decimal('0.1') + to_decimal('0.2')
        Decimal('0.3000')  # Not 0.30000000000000004 like float
    """
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, str):
        decimal_value = Decimal(value)
    elif isinstance(value, (int, float)):
        # Convert float to string first to avoid float precision issues
        decimal_value = Decimal(str(value))
    else:
        raise TypeError(f"Cannot convert {type(value)} to Decimal")

    return quantize(decimal_value, scale=scale)


def quantize(value: Decimal, scale: int = 4) -> Decimal:
    """
    Quantize a Decimal to specified scale using financial rounding.

    Args:
        value: Decimal value to quantize
        scale: Number of decimal places

    Returns:
        Decimal: Quantized value
    """
    quantizer = Decimal('1').scaleb(-scale)
    return value.quantize(quantizer, rounding=ROUND_HALF_EVEN)


def quantize_to_currency(value: Union[str, int, float, Decimal]) -> Decimal:
    """
    Quantize value to currency precision (4 decimal places).

    Args:
        value: Value to quantize

    Returns:
        Decimal: Value quantized to 4 decimal places
    """
    return to_decimal(value, scale=4)


def quantize_to_percentage(value: Union[str, int, float, Decimal]) -> Decimal:
    """
    Quantize value to percentage precision (2 decimal places).

    Args:
        value: Value to quantize

    Returns:
        Decimal: Value quantized to 2 decimal places
    """
    return to_decimal(value, scale=2)


def safe_divide(numerator: Union[str, int, float, Decimal],
                denominator: Union[str, int, float, Decimal],
                scale: int = 4) -> Decimal:
    """
    Safe division with Decimal precision.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        scale: Result scale

    Returns:
        Decimal: Division result

    Raises:
        ZeroDivisionError: If denominator is zero
    """
    num = to_decimal(numerator, scale)
    den = to_decimal(denominator, scale)

    if den == 0:
        raise ZeroDivisionError("Cannot divide by zero")

    result = num / den
    return quantize(result, scale=scale)


def safe_multiply(a: Union[str, int, float, Decimal],
                  b: Union[str, int, float, Decimal],
                  scale: int = 4) -> Decimal:
    """
    Safe multiplication with Decimal precision.

    Args:
        a: First operand
        b: Second operand
        scale: Result scale

    Returns:
        Decimal: Multiplication result
    """
    dec_a = to_decimal(a, scale)
    dec_b = to_decimal(b, scale)
    result = dec_a * dec_b
    return quantize(result, scale=scale)


def safe_add(a: Union[str, int, float, Decimal],
             b: Union[str, int, float, Decimal],
             scale: int = 4) -> Decimal:
    """
    Safe addition with Decimal precision.

    Args:
        a: First operand
        b: Second operand
        scale: Result scale

    Returns:
        Decimal: Addition result
    """
    dec_a = to_decimal(a, scale)
    dec_b = to_decimal(b, scale)
    result = dec_a + dec_b
    return quantize(result, scale=scale)


def safe_subtract(a: Union[str, int, float, Decimal],
                  b: Union[str, int, float, Decimal],
                  scale: int = 4) -> Decimal:
    """
    Safe subtraction with Decimal precision.

    Args:
        a: First operand
        b: Second operand
        scale: Result scale

    Returns:
        Decimal: Subtraction result
    """
    dec_a = to_decimal(a, scale)
    dec_b = to_decimal(b, scale)
    result = dec_a - dec_b
    return quantize(result, scale=scale)


# Re-export Decimal for convenience
__all__ = [
    'Decimal',
    'get_decimal_context',
    'to_decimal',
    'quantize',
    'quantize_to_currency',
    'quantize_to_percentage',
    'safe_divide',
    'safe_multiply',
    'safe_add',
    'safe_subtract',
]
