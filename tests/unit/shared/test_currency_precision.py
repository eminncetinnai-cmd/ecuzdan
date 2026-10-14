"""
Unit tests for shared.currency_precision module - Critical financial operations
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
def test_get_scale_fiat_currency():
    """Test get_scale for fiat currencies"""
    assert get_currency_scale('TRY') == 2
    assert get_currency_scale('USD') == 2
    assert get_currency_scale('EUR') == 2
    assert get_currency_scale('GBP') == 2
    assert get_currency_scale('JPY') == 0


@pytest.mark.unit
def test_get_scale_crypto_currency():
    """Test get_scale for crypto currencies"""
    assert get_currency_scale('BTC') == 8
    assert get_currency_scale('ETH') == 8
    assert get_currency_scale('XRP') == 6
    assert get_currency_scale('LTC') == 8
    assert get_currency_scale('BCH') == 8
    assert get_currency_scale('ADA') == 6
    assert get_currency_scale('DOT') == 10
    assert get_currency_scale('SOL') == 9
    assert get_currency_scale('DOGE') == 8
    assert get_currency_scale('USDT') == 6
    assert get_currency_scale('USDC') == 6


@pytest.mark.unit
def test_get_scale_gold_precision():
    """Test get_scale for gold precision"""
    assert get_currency_scale('GRAM') == 3
    assert get_currency_scale('GR') == 3
    assert get_currency_scale('ONS') == 4
    assert get_currency_scale('OZ') == 4
    assert get_currency_scale('KG') == 2


@pytest.mark.unit
def test_get_scale_stock_markets():
    """Test get_scale for stock markets"""
    assert get_currency_scale('BIST') == 2
    assert get_currency_scale('NYSE') == 2
    assert get_currency_scale('NASDAQ') == 2
    assert get_currency_scale('LSE') == 2
    assert get_currency_scale('XETRA') == 2


@pytest.mark.unit
def test_get_scale_fund_types():
    """Test get_scale for fund types"""
    assert get_currency_scale('YATIRIM_FONU') == 4
    assert get_currency_scale('ETF') == 4
    assert get_currency_scale('MUTUAL_FUND') == 4
    assert get_currency_scale('HEDGE_FUND') == 4


@pytest.mark.unit
def test_get_scale_unknown_currency():
    """Test get_scale for unknown currency returns default"""
    assert get_currency_scale('UNKNOWN') == 4
    assert get_currency_scale('XYZ') == 4


@pytest.mark.unit
def test_get_scale_case_insensitive():
    """Test get_scale is case insensitive"""
    assert get_currency_scale('try') == 2
    assert get_currency_scale('Try') == 2
    assert get_currency_scale('btc') == 8
    assert get_currency_scale('Btc') == 8


@pytest.mark.unit
def test_get_asset_type_scale_crypto():
    """Test get_asset_type_scale for crypto"""
    assert get_asset_type_scale('Kripto') == 8
    assert get_asset_type_scale('Crypto') == 8
    assert get_asset_type_scale('Bitcoin') == 8
    assert get_asset_type_scale('Ethereum') == 8


@pytest.mark.unit
def test_get_asset_type_scale_gold():
    """Test get_asset_type_scale for gold"""
    assert get_asset_type_scale('Altın') == 3
    assert get_asset_type_scale('Gold') == 3
    assert get_asset_type_scale('Gram Altın') == 3
    assert get_asset_type_scale('Ons Altın') == 4


@pytest.mark.unit
def test_get_asset_type_scale_stocks():
    """Test get_asset_type_scale for stocks"""
    assert get_asset_type_scale('Hisse Senedi') == 2
    assert get_asset_type_scale('Stock') == 2
    assert get_asset_type_scale('Equity') == 2


@pytest.mark.unit
def test_get_asset_type_scale_funds():
    """Test get_asset_type_scale for funds"""
    assert get_asset_type_scale('Yatırım Fonu') == 4
    assert get_asset_type_scale('Fund') == 4
    assert get_asset_type_scale('ETF') == 4


@pytest.mark.unit
def test_get_asset_type_scale_real_estate():
    """Test get_asset_type_scale for real estate"""
    assert get_asset_type_scale('Gayrimenkul') == 4
    assert get_asset_type_scale('Real Estate') == 4


@pytest.mark.unit
def test_get_asset_type_scale_unknown():
    """Test get_asset_type_scale for unknown asset type returns default"""
    assert get_asset_type_scale('Unknown') == 4
    assert get_asset_type_scale('XYZ') == 4


@pytest.mark.unit
def test_get_currency_type_fiat():
    """Test get_currency_type for fiat currencies"""
    assert CurrencyPrecision.get_currency_type('TRY') == CurrencyType.FIAT
    assert CurrencyPrecision.get_currency_type('USD') == CurrencyType.FIAT
    assert CurrencyPrecision.get_currency_type('EUR') == CurrencyType.FIAT
    assert CurrencyPrecision.get_currency_type('GBP') == CurrencyType.FIAT
    assert CurrencyPrecision.get_currency_type('JPY') == CurrencyType.FIAT


@pytest.mark.unit
def test_get_currency_type_crypto():
    """Test get_currency_type for crypto currencies"""
    assert CurrencyPrecision.get_currency_type('BTC') == CurrencyType.CRYPTO
    assert CurrencyPrecision.get_currency_type('ETH') == CurrencyType.CRYPTO
    assert CurrencyPrecision.get_currency_type('XRP') == CurrencyType.CRYPTO
    assert CurrencyPrecision.get_currency_type('LTC') == CurrencyType.CRYPTO


@pytest.mark.unit
def test_get_currency_type_gold_gram():
    """Test get_currency_type for gold in grams"""
    assert CurrencyPrecision.get_currency_type('GRAM') == CurrencyType.GOLD_GRAM
    assert CurrencyPrecision.get_currency_type('GR') == CurrencyType.GOLD_GRAM


@pytest.mark.unit
def test_get_currency_type_gold_ounce():
    """Test get_currency_type for gold in ounces"""
    assert CurrencyPrecision.get_currency_type('ONS') == CurrencyType.GOLD_OUNCE
    assert CurrencyPrecision.get_currency_type('OZ') == CurrencyType.GOLD_OUNCE


@pytest.mark.unit
def test_get_currency_type_stock():
    """Test get_currency_type for stock markets"""
    assert CurrencyPrecision.get_currency_type('BIST') == CurrencyType.STOCK
    assert CurrencyPrecision.get_currency_type('NYSE') == CurrencyType.STOCK
    assert CurrencyPrecision.get_currency_type('NASDAQ') == CurrencyType.STOCK


@pytest.mark.unit
def test_get_currency_type_fund():
    """Test get_currency_type for fund types"""
    assert CurrencyPrecision.get_currency_type('YATIRIM_FONU') == CurrencyType.FUND
    assert CurrencyPrecision.get_currency_type('ETF') == CurrencyType.FUND


@pytest.mark.unit
def test_get_currency_type_unknown():
    """Test get_currency_type for unknown currency returns commodity"""
    assert CurrencyPrecision.get_currency_type('UNKNOWN') == CurrencyType.COMMODITY
    assert CurrencyPrecision.get_currency_type('XYZ') == CurrencyType.COMMODITY


@pytest.mark.unit
def test_get_currency_type_case_insensitive():
    """Test get_currency_type is case insensitive"""
    assert CurrencyPrecision.get_currency_type('try') == CurrencyType.FIAT
    assert CurrencyPrecision.get_currency_type('btc') == CurrencyType.CRYPTO
    assert CurrencyPrecision.get_currency_type('gram') == CurrencyType.GOLD_GRAM


@pytest.mark.unit
def test_is_fiat():
    """Test is_fiat method"""
    assert CurrencyPrecision.is_fiat('TRY')
    assert CurrencyPrecision.is_fiat('USD')
    assert CurrencyPrecision.is_fiat('EUR')
    assert not CurrencyPrecision.is_fiat('BTC')
    assert not CurrencyPrecision.is_fiat('ETH')
    assert not CurrencyPrecision.is_fiat('GRAM')


@pytest.mark.unit
def test_is_crypto():
    """Test is_crypto method"""
    assert CurrencyPrecision.is_crypto('BTC')
    assert CurrencyPrecision.is_crypto('ETH')
    assert CurrencyPrecision.is_crypto('XRP')
    assert not CurrencyPrecision.is_crypto('TRY')
    assert not CurrencyPrecision.is_crypto('USD')
    assert not CurrencyPrecision.is_crypto('GRAM')


@pytest.mark.unit
def test_is_gold():
    """Test is_gold method"""
    assert CurrencyPrecision.is_gold('GRAM')
    assert CurrencyPrecision.is_gold('GR')
    assert CurrencyPrecision.is_gold('ONS')
    assert CurrencyPrecision.is_gold('OZ')
    assert not CurrencyPrecision.is_gold('TRY')
    assert not CurrencyPrecision.is_gold('BTC')
    assert not CurrencyPrecision.is_gold('USD')


@pytest.mark.unit
def test_get_currency_symbol_fiat():
    """Test get_currency_symbol for fiat currencies"""
    assert get_currency_symbol('TRY') == '₺'
    assert get_currency_symbol('USD') == '$'
    assert get_currency_symbol('EUR') == '€'
    assert get_currency_symbol('GBP') == '£'
    assert get_currency_symbol('JPY') == '¥'


@pytest.mark.unit
def test_get_currency_symbol_crypto():
    """Test get_currency_symbol for crypto currencies"""
    assert get_currency_symbol('BTC') == '₿'
    assert get_currency_symbol('ETH') == 'Ξ'


@pytest.mark.unit
def test_get_currency_symbol_gold():
    """Test get_currency_symbol for gold"""
    assert get_currency_symbol('GRAM') == 'g'
    assert get_currency_symbol('GR') == 'g'
    assert get_currency_symbol('ONS') == 'oz'
    assert get_currency_symbol('OZ') == 'oz'
    assert get_currency_symbol('KG') == 'kg'


@pytest.mark.unit
def test_get_currency_symbol_unknown():
    """Test get_currency_symbol for unknown currency returns empty string"""
    assert get_currency_symbol('UNKNOWN') == ''
    assert get_currency_symbol('XYZ') == ''


@pytest.mark.unit
def test_get_currency_symbol_case_insensitive():
    """Test get_currency_symbol is case insensitive"""
    assert get_currency_symbol('try') == '₺'
    assert get_currency_symbol('Try') == '₺'
    assert get_currency_symbol('btc') == '₿'


@pytest.mark.unit
def test_supported_fiat_list():
    """Test SUPPORTED_FIAT list"""
    assert isinstance(SUPPORTED_FIAT, list)
    assert 'TRY' in SUPPORTED_FIAT
    assert 'USD' in SUPPORTED_FIAT
    assert 'EUR' in SUPPORTED_FIAT


@pytest.mark.unit
def test_supported_crypto_list():
    """Test SUPPORTED_CRYPTO list"""
    assert isinstance(SUPPORTED_CRYPTO, list)
    assert 'BTC' in SUPPORTED_CRYPTO
    assert 'ETH' in SUPPORTED_CRYPTO


@pytest.mark.unit
def test_supported_gold_list():
    """Test SUPPORTED_GOLD list"""
    assert isinstance(SUPPORTED_GOLD, list)
    assert 'GRAM' in SUPPORTED_GOLD
    assert 'ONS' in SUPPORTED_GOLD


@pytest.mark.unit
def test_supported_stocks_list():
    """Test SUPPORTED_STOCKS list"""
    assert isinstance(SUPPORTED_STOCKS, list)
    assert 'BIST' in SUPPORTED_STOCKS
    assert 'NYSE' in SUPPORTED_STOCKS


@pytest.mark.unit
def test_supported_funds_list():
    """Test SUPPORTED_FUNDS list"""
    assert isinstance(SUPPORTED_FUNDS, list)
    assert 'YATIRIM_FONU' in SUPPORTED_FUNDS
    assert 'ETF' in SUPPORTED_FUNDS


@pytest.mark.unit
def test_currency_type_enum():
    """Test CurrencyType enum values"""
    assert CurrencyType.FIAT.value == "fiat"
    assert CurrencyType.CRYPTO.value == "crypto"
    assert CurrencyType.GOLD_GRAM.value == "gold_gram"
    assert CurrencyType.GOLD_OUNCE.value == "gold_ounce"
    assert CurrencyType.STOCK.value == "stock"
    assert CurrencyType.FUND.value == "fund"
    assert CurrencyType.COMMODITY.value == "commodity"
