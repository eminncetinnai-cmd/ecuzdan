"""
Unit Tests - Currency Precision
Currency-specific decimal precision for different asset types
"""

import pytest

from shared.currency_precision import (
    SUPPORTED_CRYPTO,
    SUPPORTED_FIAT,
    SUPPORTED_FUNDS,
    SUPPORTED_GOLD,
    SUPPORTED_STOCKS,
    CurrencyPrecision,
    CurrencyType,
    get_asset_type_scale,
    get_currency_scale,
    get_currency_symbol,
)


@pytest.mark.unit
def test_currency_precision_get_scale_fiat():
    """Test getting scale for fiat currencies"""
    assert get_currency_scale('TRY') == 2
    assert get_currency_scale('USD') == 2
    assert get_currency_scale('EUR') == 2
    assert get_currency_scale('GBP') == 2


@pytest.mark.unit
def test_currency_precision_get_scale_jpy():
    """Test getting scale for JPY (no decimal places)"""
    assert get_currency_scale('JPY') == 0


@pytest.mark.unit
def test_currency_precision_get_scale_crypto():
    """Test getting scale for cryptocurrencies"""
    assert get_currency_scale('BTC') == 8
    assert get_currency_scale('ETH') == 8
    assert get_currency_scale('XRP') == 6
    assert get_currency_scale('DOT') == 10
    assert get_currency_scale('SOL') == 9


@pytest.mark.unit
def test_currency_precision_get_scale_gold():
    """Test getting scale for gold"""
    assert get_currency_scale('GRAM') == 3
    assert get_currency_scale('GR') == 3
    assert get_currency_scale('ONS') == 4
    assert get_currency_scale('OZ') == 4
    assert get_currency_scale('KG') == 2


@pytest.mark.unit
def test_currency_precision_get_scale_stocks():
    """Test getting scale for stock markets"""
    assert get_currency_scale('BIST') == 2
    assert get_currency_scale('NYSE') == 2
    assert get_currency_scale('NASDAQ') == 2


@pytest.mark.unit
def test_currency_precision_get_scale_funds():
    """Test getting scale for funds"""
    assert get_currency_scale('YATIRIM_FONU') == 4
    assert get_currency_scale('ETF') == 4


@pytest.mark.unit
def test_currency_precision_get_scale_default():
    """Test getting scale for unknown currency (default 4)"""
    assert get_currency_scale('UNKNOWN') == 4


@pytest.mark.unit
def test_currency_precision_get_scale_case_insensitive():
    """Test currency code is case insensitive"""
    assert get_currency_scale('try') == 2
    assert get_currency_scale('Try') == 2
    assert get_currency_scale('TRY') == 2


@pytest.mark.unit
def test_currency_precision_get_asset_type_scale():
    """Test getting scale for asset types"""
    assert get_asset_type_scale('Kripto') == 8
    assert get_asset_type_scale('Crypto') == 8
    assert get_asset_type_scale('Altın') == 3
    assert get_asset_type_scale('Gold') == 3
    assert get_asset_type_scale('Hisse Senedi') == 2
    assert get_asset_type_scale('Yatırım Fonu') == 4


@pytest.mark.unit
def test_currency_precision_get_asset_type_scale_default():
    """Test getting scale for unknown asset type (default 4)"""
    assert get_asset_type_scale('Unknown') == 4


@pytest.mark.unit
def test_currency_precision_get_currency_type_fiat():
    """Test getting currency type for fiat"""
    assert CurrencyPrecision.get_currency_type('TRY') == CurrencyType.FIAT
    assert CurrencyPrecision.get_currency_type('USD') == CurrencyType.FIAT


@pytest.mark.unit
def test_currency_precision_get_currency_type_crypto():
    """Test getting currency type for crypto"""
    assert CurrencyPrecision.get_currency_type('BTC') == CurrencyType.CRYPTO
    assert CurrencyPrecision.get_currency_type('ETH') == CurrencyType.CRYPTO


@pytest.mark.unit
def test_currency_precision_get_currency_type_gold_gram():
    """Test getting currency type for gold in grams"""
    assert CurrencyPrecision.get_currency_type('GRAM') == CurrencyType.GOLD_GRAM
    assert CurrencyPrecision.get_currency_type('GR') == CurrencyType.GOLD_GRAM


@pytest.mark.unit
def test_currency_precision_get_currency_type_gold_ounce():
    """Test getting currency type for gold in ounces"""
    assert CurrencyPrecision.get_currency_type('ONS') == CurrencyType.GOLD_OUNCE
    assert CurrencyPrecision.get_currency_type('OZ') == CurrencyType.GOLD_OUNCE


@pytest.mark.unit
def test_currency_precision_get_currency_type_stock():
    """Test getting currency type for stocks"""
    assert CurrencyPrecision.get_currency_type('BIST') == CurrencyType.STOCK


@pytest.mark.unit
def test_currency_precision_get_currency_type_fund():
    """Test getting currency type for funds"""
    assert CurrencyPrecision.get_currency_type('YATIRIM_FONU') == CurrencyType.FUND


@pytest.mark.unit
def test_currency_precision_get_currency_type_commodity():
    """Test getting currency type for commodity (default)"""
    assert CurrencyPrecision.get_currency_type('UNKNOWN') == CurrencyType.COMMODITY


@pytest.mark.unit
def test_currency_precision_is_fiat():
    """Test checking if currency is fiat"""
    assert CurrencyPrecision.is_fiat('TRY') is True
    assert CurrencyPrecision.is_fiat('USD') is True
    assert CurrencyPrecision.is_fiat('BTC') is False


@pytest.mark.unit
def test_currency_precision_is_crypto():
    """Test checking if currency is crypto"""
    assert CurrencyPrecision.is_crypto('BTC') is True
    assert CurrencyPrecision.is_crypto('ETH') is True
    assert CurrencyPrecision.is_crypto('TRY') is False


@pytest.mark.unit
def test_currency_precision_is_gold():
    """Test checking if currency is gold"""
    assert CurrencyPrecision.is_gold('GRAM') is True
    assert CurrencyPrecision.is_gold('ONS') is True
    assert CurrencyPrecision.is_gold('TRY') is False


@pytest.mark.unit
def test_get_currency_symbol():
    """Test getting currency symbols"""
    assert get_currency_symbol('TRY') == '₺'
    assert get_currency_symbol('USD') == '$'
    assert get_currency_symbol('EUR') == '€'
    assert get_currency_symbol('GBP') == '£'
    assert get_currency_symbol('JPY') == '¥'


@pytest.mark.unit
def test_get_currency_symbol_crypto():
    """Test getting crypto currency symbols"""
    assert get_currency_symbol('BTC') == '₿'
    assert get_currency_symbol('ETH') == 'Ξ'


@pytest.mark.unit
def test_get_currency_symbol_gold():
    """Test getting gold unit symbols"""
    assert get_currency_symbol('GRAM') == 'g'
    assert get_currency_symbol('ONS') == 'oz'


@pytest.mark.unit
def test_get_currency_symbol_unknown():
    """Test getting symbol for unknown currency returns empty"""
    assert get_currency_symbol('UNKNOWN') == ''


@pytest.mark.unit
def test_get_currency_symbol_case_insensitive():
    """Test currency symbol is case insensitive"""
    assert get_currency_symbol('try') == '₺'
    assert get_currency_symbol('Try') == '₺'
    assert get_currency_symbol('TRY') == '₺'


@pytest.mark.unit
def test_supported_fiat_list():
    """Test supported fiat currencies list"""
    assert 'TRY' in SUPPORTED_FIAT
    assert 'USD' in SUPPORTED_FIAT
    assert 'EUR' in SUPPORTED_FIAT
    assert len(SUPPORTED_FIAT) > 0


@pytest.mark.unit
def test_supported_crypto_list():
    """Test supported crypto currencies list"""
    assert 'BTC' in SUPPORTED_CRYPTO
    assert 'ETH' in SUPPORTED_CRYPTO
    assert len(SUPPORTED_CRYPTO) > 0


@pytest.mark.unit
def test_supported_gold_list():
    """Test supported gold units list"""
    assert 'GRAM' in SUPPORTED_GOLD
    assert 'ONS' in SUPPORTED_GOLD
    assert len(SUPPORTED_GOLD) > 0


@pytest.mark.unit
def test_supported_stocks_list():
    """Test supported stock markets list"""
    assert 'BIST' in SUPPORTED_STOCKS
    assert 'NYSE' in SUPPORTED_STOCKS
    assert len(SUPPORTED_STOCKS) > 0


@pytest.mark.unit
def test_supported_funds_list():
    """Test supported fund types list"""
    assert 'YATIRIM_FONU' in SUPPORTED_FUNDS
    assert 'ETF' in SUPPORTED_FUNDS
    assert len(SUPPORTED_FUNDS) > 0


@pytest.mark.unit
def test_currency_precision_class_get_scale():
    """Test CurrencyPrecision class method get_scale"""
    assert CurrencyPrecision.get_scale('TRY') == 2
    assert CurrencyPrecision.get_scale('BTC') == 8


@pytest.mark.unit
def test_currency_precision_class_get_asset_type_scale():
    """Test CurrencyPrecision class method get_asset_type_scale"""
    assert CurrencyPrecision.get_asset_type_scale('Kripto') == 8
    assert CurrencyPrecision.get_asset_type_scale('Altın') == 3
