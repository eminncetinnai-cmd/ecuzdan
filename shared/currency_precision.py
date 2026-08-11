"""
Currency Precision Engine

Provides currency-specific decimal precision for different asset types.
Different currencies and assets require different decimal scales:

- Fiat Currencies (TRY, USD, EUR): 2 decimal places
- Crypto (BTC, ETH): 8 decimal places (satoshi precision)
- Gold (Gram): 3 decimal places
- Gold (Ounce): 4 decimal places
- Funds: 4 decimal places
- Stocks: 2 decimal places

Usage:
    from shared.currency_precision import CurrencyPrecision, get_currency_scale
    
    # Get scale for currency
    scale = get_currency_scale('BTC')  # Returns 8
    
    # Quantize to currency precision
    from shared.decimal_precision import to_decimal, quantize
    amount = to_decimal('0.12345678')
    quantized = quantize(amount, scale=get_currency_scale('BTC'))
"""

from decimal import Decimal
from typing import Dict, Optional
from enum import Enum


class CurrencyType(Enum):
    """Currency type categories."""
    FIAT = "fiat"           # Traditional currencies (TRY, USD, EUR)
    CRYPTO = "crypto"       # Cryptocurrencies (BTC, ETH)
    GOLD_GRAM = "gold_gram" # Gold in grams
    GOLD_OUNCE = "gold_ounce" # Gold in ounces
    STOCK = "stock"         # Stocks/equities
    FUND = "fund"           # Investment funds
    COMMODITY = "commodity" # Other commodities


class CurrencyPrecision:
    """
    Currency precision configuration.
    
    Maps currency codes to their required decimal scales.
    """
    
    # Fiat currencies - 2 decimal places (cents)
    FIAT_CURRENCIES = {
        'TRY': 2,  # Turkish Lira
        'USD': 2,  # US Dollar
        'EUR': 2,  # Euro
        'GBP': 2,  # British Pound
        'JPY': 0,  # Japanese Yen (no decimal places)
        'CHF': 2,  # Swiss Franc
        'CAD': 2,  # Canadian Dollar
        'AUD': 2,  # Australian Dollar
        'CNY': 2,  # Chinese Yuan
        'RUB': 2,  # Russian Ruble
        'SAR': 2,  # Saudi Riyal
        'AED': 2,  # UAE Dirham
    }
    
    # Cryptocurrencies - 8 decimal places (satoshi precision)
    CRYPTO_CURRENCIES = {
        'BTC': 8,  # Bitcoin
        'ETH': 8,  # Ethereum
        'XRP': 6,  # Ripple
        'LTC': 8,  # Litecoin
        'BCH': 8,  # Bitcoin Cash
        'ADA': 6,  # Cardano
        'DOT': 10, # Polkadot
        'SOL': 9,  # Solana
        'DOGE': 8, # Dogecoin
        'USDT': 6, # Tether
        'USDC': 6, # USD Coin
    }
    
    # Gold - different scales for different units
    GOLD_PRECISION = {
        'GRAM': 3,    # Gold in grams (2500.500)
        'GR': 3,      # Gold in grams (abbreviation)
        'ONS': 4,     # Gold in ounces (2500.5000)
        'OZ': 4,      # Gold in ounces (abbreviation)
        'KG': 2,      # Gold in kilograms (2500.50)
    }
    
    # Stocks - 2 decimal places
    STOCK_MARKETS = {
        'BIST': 2,    # Borsa Istanbul
        'NYSE': 2,    # New York Stock Exchange
        'NASDAQ': 2,  # NASDAQ
        'LSE': 2,     # London Stock Exchange
        'XETRA': 2,   # Xetra
    }
    
    # Funds - 4 decimal places
    FUND_TYPES = {
        'YATIRIM_FONU': 4,  # Turkish Investment Fund
        'ETF': 4,            # Exchange Traded Fund
        'MUTUAL_FUND': 4,    # Mutual Fund
        'HEDGE_FUND': 4,     # Hedge Fund
    }
    
    # Asset type mappings
    ASSET_TYPE_PRECISION = {
        # Crypto
        'Kripto': 8,
        'Crypto': 8,
        'Bitcoin': 8,
        'Ethereum': 8,
        
        # Gold
        'Altın': 3,
        'Gold': 3,
        'Gram Altın': 3,
        'Ons Altın': 4,
        
        # Stocks
        'Hisse Senedi': 2,
        'Stock': 2,
        'Equity': 2,
        
        # Funds
        'Yatırım Fonu': 4,
        'Fund': 4,
        'ETF': 4,
        
        # Real Estate (4 decimal for large amounts)
        'Gayrimenkul': 4,
        'Real Estate': 4,
        
        # Default for other assets
        'default': 4,
    }
    
    @classmethod
    def get_scale(cls, currency_code: str) -> int:
        """
        Get decimal scale for a currency code.
        
        Args:
            currency_code: Currency code (e.g., 'BTC', 'TRY', 'USD')
        
        Returns:
            int: Decimal scale (number of decimal places)
        
        Examples:
            >>> CurrencyPrecision.get_scale('BTC')
            8
            >>> CurrencyPrecision.get_scale('TRY')
            2
            >>> CurrencyPrecision.get_scale('GRAM')
            3
        """
        currency_upper = currency_code.upper()
        
        # Check fiat currencies
        if currency_upper in cls.FIAT_CURRENCIES:
            return cls.FIAT_CURRENCIES[currency_upper]
        
        # Check crypto currencies
        if currency_upper in cls.CRYPTO_CURRENCIES:
            return cls.CRYPTO_CURRENCIES[currency_upper]
        
        # Check gold precision
        if currency_upper in cls.GOLD_PRECISION:
            return cls.GOLD_PRECISION[currency_upper]
        
        # Check stock markets
        if currency_upper in cls.STOCK_MARKETS:
            return cls.STOCK_MARKETS[currency_upper]
        
        # Check fund types
        if currency_upper in cls.FUND_TYPES:
            return cls.FUND_TYPES[currency_upper]
        
        # Default to 4 decimal places
        return 4
    
    @classmethod
    def get_asset_type_scale(cls, asset_type: str) -> int:
        """
        Get decimal scale for an asset type.
        
        Args:
            asset_type: Asset type (e.g., 'Kripto', 'Altın', 'Hisse Senedi')
        
        Returns:
            int: Decimal scale (number of decimal places)
        
        Examples:
            >>> CurrencyPrecision.get_asset_type_scale('Kripto')
            8
            >>> CurrencyPrecision.get_asset_type_scale('Altın')
            3
            >>> CurrencyPrecision.get_asset_type_scale('Hisse Senedi')
            2
        """
        return cls.ASSET_TYPE_PRECISION.get(asset_type, cls.ASSET_TYPE_PRECISION['default'])
    
    @classmethod
    def get_currency_type(cls, currency_code: str) -> CurrencyType:
        """
        Get currency type category.
        
        Args:
            currency_code: Currency code
        
        Returns:
            CurrencyType: Currency type category
        """
        currency_upper = currency_code.upper()
        
        if currency_upper in cls.FIAT_CURRENCIES:
            return CurrencyType.FIAT
        elif currency_upper in cls.CRYPTO_CURRENCIES:
            return CurrencyType.CRYPTO
        elif currency_upper in cls.GOLD_PRECISION:
            if currency_upper in ['GRAM', 'GR']:
                return CurrencyType.GOLD_GRAM
            else:
                return CurrencyType.GOLD_OUNCE
        elif currency_upper in cls.STOCK_MARKETS:
            return CurrencyType.STOCK
        elif currency_upper in cls.FUND_TYPES:
            return CurrencyType.FUND
        else:
            return CurrencyType.COMMODITY
    
    @classmethod
    def is_fiat(cls, currency_code: str) -> bool:
        """Check if currency is a fiat currency."""
        return cls.get_currency_type(currency_code) == CurrencyType.FIAT
    
    @classmethod
    def is_crypto(cls, currency_code: str) -> bool:
        """Check if currency is a cryptocurrency."""
        return cls.get_currency_type(currency_code) == CurrencyType.CRYPTO
    
    @classmethod
    def is_gold(cls, currency_code: str) -> bool:
        """Check if currency is gold."""
        return cls.get_currency_type(currency_code) in [CurrencyType.GOLD_GRAM, CurrencyType.GOLD_OUNCE]


def get_currency_scale(currency_code: str) -> int:
    """
    Convenience function to get currency scale.
    
    Args:
        currency_code: Currency code
    
    Returns:
        int: Decimal scale
    """
    return CurrencyPrecision.get_scale(currency_code)


def get_asset_type_scale(asset_type: str) -> int:
    """
    Convenience function to get asset type scale.
    
    Args:
        asset_type: Asset type
    
    Returns:
        int: Decimal scale
    """
    return CurrencyPrecision.get_asset_type_scale(asset_type)


def get_currency_symbol(currency_code: str) -> str:
    """
    Get currency symbol for display.
    
    Args:
        currency_code: Currency code (e.g., 'TRY', 'USD', 'EUR')
    
    Returns:
        str: Currency symbol (e.g., '₺', '$', '€')
    """
    CURRENCY_SYMBOLS = {
        'TRY': '₺',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CHF': 'Fr',
        'CAD': 'C$',
        'AUD': 'A$',
        'CNY': '¥',
        'RUB': '₽',
        'SAR': '﷼',
        'AED': 'د.إ',
        'BTC': '₿',
        'ETH': 'Ξ',
        'GRAM': 'g',
        'GR': 'g',
        'ONS': 'oz',
        'OZ': 'oz',
        'KG': 'kg',
    }
    
    return CURRENCY_SYMBOLS.get(currency_code.upper(), '')


# Supported currencies list
SUPPORTED_FIAT = list(CurrencyPrecision.FIAT_CURRENCIES.keys())
SUPPORTED_CRYPTO = list(CurrencyPrecision.CRYPTO_CURRENCIES.keys())
SUPPORTED_GOLD = list(CurrencyPrecision.GOLD_PRECISION.keys())
SUPPORTED_STOCKS = list(CurrencyPrecision.STOCK_MARKETS.keys())
SUPPORTED_FUNDS = list(CurrencyPrecision.FUND_TYPES.keys())

__all__ = [
    'CurrencyPrecision',
    'CurrencyType',
    'get_currency_scale',
    'get_asset_type_scale',
    'get_currency_symbol',
    'SUPPORTED_FIAT',
    'SUPPORTED_CRYPTO',
    'SUPPORTED_GOLD',
    'SUPPORTED_STOCKS',
    'SUPPORTED_FUNDS',
]
