"""
Money Class - Centralized Financial Operations

A Money class that handles all financial operations with proper precision,
currency support, formatting, and validation. Inspired by Stripe, Wise, and Revolut.

Features:
- Currency-specific precision
- Safe arithmetic operations
- Currency conversion
- Formatting and display
- Comparison operations
- Validation

Usage:
    from shared.money import Money

    amount = Money('100.50', 'TRY')
    total = amount + Money('50.25', 'TRY')
    formatted = total.format()  # "₺150.75"

    btc_amount = Money('0.5', 'BTC')
    btc_value_usd = btc_amount.convert_to('USD', rate=60000)
"""

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional, Union

from shared.currency_precision import get_currency_scale, get_currency_symbol
from shared.decimal_precision import safe_add, safe_divide, safe_multiply, safe_subtract, to_decimal


class Money:
    """
    Money class for centralized financial operations.

    All financial operations should use this class instead of direct Decimal or float.
    This ensures consistent precision, currency handling, and validation.
    """

    def __init__(self, amount: Union[str, int, float, Decimal], currency: str = 'TRY'):
        """
        Initialize a Money object.

        Args:
            amount: The monetary amount (string, int, float, or Decimal)
            currency: Currency code (e.g., 'TRY', 'USD', 'BTC', 'GRAM')

        Raises:
            ValueError: If amount is invalid or currency is not supported
        """
        self.currency = currency.upper()
        self._scale = get_currency_scale(self.currency)

        # Convert amount to Decimal using safe conversion
        self._amount = to_decimal(str(amount))

        # Quantize to currency-specific scale
        self._amount = self._amount.quantize(Decimal('1.' + '0' * self._scale), rounding=ROUND_HALF_EVEN)

    @property
    def amount(self) -> Decimal:
        """Get the amount as Decimal."""
        return self._amount

    @property
    def scale(self) -> int:
        """Get the currency scale (number of decimal places)."""
        return self._scale

    def __add__(self, other: 'Money') -> 'Money':
        """Add two Money objects (must be same currency)."""
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")

        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}. Convert first.")

        result_amount = safe_add(self._amount, other._amount)
        return Money(result_amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract two Money objects (must be same currency)."""
        if not isinstance(other, Money):
            raise TypeError("Can only subtract Money from Money")

        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}. Convert first.")

        result_amount = safe_subtract(self._amount, other._amount)
        return Money(result_amount, self.currency)

    def __mul__(self, other: Union[int, float, Decimal]) -> 'Money':
        """Multiply Money by a scalar (not another Money object)."""
        if isinstance(other, Money):
            raise TypeError("Cannot multiply Money by Money. Use convert_to() instead.")

        result_amount = safe_multiply(self._amount, to_decimal(str(other)))
        return Money(result_amount, self.currency)

    def __truediv__(self, other: Union[int, float, Decimal]) -> 'Money':
        """Divide Money by a scalar (not another Money object)."""
        if isinstance(other, Money):
            raise TypeError("Cannot divide Money by Money. Use convert_to() instead.")

        if to_decimal(str(other)) == 0:
            raise ZeroDivisionError("Cannot divide by zero")

        result_amount = safe_divide(self._amount, to_decimal(str(other)))
        return Money(result_amount, self.currency)

    def __eq__(self, other) -> bool:
        """Compare equality."""
        if not isinstance(other, Money):
            return False

        if self.currency != other.currency:
            return False

        return self._amount == other._amount

    def __ne__(self, other) -> bool:
        """Compare inequality."""
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        """Less than comparison."""
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money to Money")

        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} to {other.currency}")

        return self._amount < other._amount

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money to Money")

        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} to {other.currency}")

        return self._amount > other._amount

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self.__gt__(other) or self.__eq__(other)

    def __repr__(self) -> str:
        """String representation."""
        return f"Money({self._amount}, '{self.currency}')"

    def __str__(self) -> str:
        """Formatted string representation."""
        return self.format()

    def format(self, show_symbol: bool = True, locale: str = 'tr') -> str:
        """
        Format the money value for display.

        Args:
            show_symbol: Whether to show currency symbol
            locale: Locale for formatting ('tr' for Turkish)

        Returns:
            Formatted string (e.g., "₺1.234,56" or "1,234.56 USD")
        """
        symbol = get_currency_symbol(self.currency)

        if locale == 'tr':
            # Turkish formatting: 1.234,56
            formatted = f"{self._amount:,.{self._scale}f}".replace('.', ',').replace(',', '.', 1)
            if show_symbol and symbol:
                return f"{symbol}{formatted}"
            return f"{formatted} {self.currency}"
        else:
            # International formatting: 1,234.56
            formatted = f"{self._amount:,.{self._scale}f}"
            if show_symbol and symbol:
                return f"{symbol}{formatted}"
            return f"{formatted} {self.currency}"

    def convert_to(self, target_currency: str, rate: Optional[Decimal] = None) -> 'Money':
        """
        Convert to another currency.

        Args:
            target_currency: Target currency code
            rate: Exchange rate (1 unit of current currency = rate units of target currency)

        Returns:
            New Money object in target currency

        Raises:
            ValueError: If rate is not provided for currency conversion
        """
        if self.currency == target_currency:
            return Money(self._amount, target_currency)

        if rate is None:
            raise ValueError("Exchange rate required for currency conversion")

        rate_decimal = to_decimal(str(rate))
        converted_amount = safe_multiply(self._amount, rate_decimal)

        return Money(converted_amount, target_currency)

    def to_float(self) -> float:
        """
        Convert to float (for JSON serialization).

        Warning: This may lose precision. Use only for serialization.
        """
        return float(self._amount)

    def to_decimal(self) -> Decimal:
        """Convert to Decimal."""
        return self._amount

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self._amount == 0

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self._amount > 0

    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self._amount < 0

    def abs(self) -> 'Money':
        """Return absolute value."""
        return Money(abs(self._amount), self.currency)

    def negate(self) -> 'Money':
        """Return negated value."""
        return Money(-self._amount, self.currency)

    @classmethod
    def zero(cls, currency: str = 'TRY') -> 'Money':
        """Create a zero Money object."""
        return Money(0, currency)

    @classmethod
    def sum(cls, money_list: list['Money']) -> 'Money':
        """
        Sum a list of Money objects (must be same currency).

        Args:
            money_list: List of Money objects

        Returns:
            Money object with sum of all amounts

        Raises:
            ValueError: If list is empty or currencies differ
        """
        if not money_list:
            raise ValueError("Cannot sum empty list")

        currency = money_list[0].currency
        for money in money_list:
            if money.currency != currency:
                raise ValueError("All Money objects must have same currency")

        total = cls.zero(currency)
        for money in money_list:
            total = total + money

        return total

    @classmethod
    def from_string(cls, value: str) -> 'Money':
        """
        Parse Money from string (e.g., "₺1.234,56" or "1,234.56 USD").

        Args:
            value: String representation of money

        Returns:
            Money object

        Raises:
            ValueError: If string cannot be parsed
        """
        # Remove currency symbols
        value = value.replace('₺', '').replace('$', '').replace('€', '').replace('£', '')

        # Extract currency code if present
        currency = 'TRY'
        for curr in ['TRY', 'USD', 'EUR', 'GBP', 'BTC', 'GRAM']:
            if curr in value.upper():
                currency = curr
                value = value.replace(curr, '').strip()

        # Remove thousand separators
        value = value.replace('.', '').replace(',', '')

        return Money(value, currency)


# Convenience functions for common operations

def money(amount: Union[str, int, float, Decimal], currency: str = 'TRY') -> Money:
    """
    Create a Money object (convenience function).

    Args:
        amount: The monetary amount
        currency: Currency code

    Returns:
        Money object
    """
    return Money(amount, currency)


def sum_money(money_list: list[Money]) -> Money:
    """
    Sum a list of Money objects (convenience function).

    Args:
        money_list: List of Money objects

    Returns:
        Money object with sum
    """
    return Money.sum(money_list)
