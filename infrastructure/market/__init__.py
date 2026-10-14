"""Infrastructure Market Package.

Contains external market data integrations, economic indicators, and pricing providers.
"""

from .market_data_service import (
    CACHE_TTL,
    MARKET_ASSETS,
    MarketDataService,
    get_macro_economic_data,
    get_market_data_summary,
)

__all__ = [
    "CACHE_TTL",
    "MARKET_ASSETS",
    "MarketDataService",
    "get_macro_economic_data",
    "get_market_data_summary",
]
