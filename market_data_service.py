"""Market Data Service - Backward Compatibility Facade.

The canonical implementation has been relocated to `infrastructure.market.market_data_service`
to adhere to the EAFGS Clean Architecture standard for external infrastructure services.

This facade maintains complete backwards compatibility for existing imports and tests.
"""

from __future__ import annotations

import infrastructure.market.market_data_service as _canonical

# Expose all symbols and sub-imports from canonical module for 100% backward compatibility
for _k, _v in _canonical.__dict__.items():
    if not _k.startswith('__'):
        globals()[_k] = _v

# Explicit exports for static type checkers & linters
from infrastructure.market.market_data_service import (  # noqa: F401
    CACHE_TTL,
    MACRO_CACHE,
    MACRO_CACHE_TTL,
    MACRO_FAILURE_BACKOFF,
    MACRO_FAILURE_CACHE,
    MARKET_ASSETS,
    MarketDataService,
    datetime,
    get_macro_economic_data,
    get_market_data_summary,
    logger,
    logging,
    market_data_service,
    requests,
    time,
    yf,
    _fetch_macro_from_evds,
    _fetch_macro_from_investing,
    _fetch_macro_from_tcmb,
    _macro_failure_cache_is_valid,
)
