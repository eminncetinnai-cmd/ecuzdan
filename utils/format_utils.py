"""Format utility functions for money, date, and display formatting.

Backward compatibility facade.
The canonical implementation has been relocated to `shared.format_utils`
as a domain/cross-cutting utility module.
"""

from __future__ import annotations

from shared.format_utils import (
    DATE_DISPLAY_FMT,
    DATE_INPUT_FORMATS,
    DATE_STORAGE_FMT,
    _validate_date_parts,
    format_date,
    format_money,
    logger,
    logging,
    parse_date_input,
    today_display,
    today_storage,
)

__all__ = [
    "DATE_DISPLAY_FMT",
    "DATE_INPUT_FORMATS",
    "DATE_STORAGE_FMT",
    "_validate_date_parts",
    "format_date",
    "format_money",
    "logger",
    "logging",
    "parse_date_input",
    "today_display",
    "today_storage",
]
