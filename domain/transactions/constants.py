"""Canonical transaction and ledger semantic codes.

These values are persisted in the database and are therefore intentionally
stable. User-facing labels belong to the i18n layer and must not be inferred
from these codes in domain code.
"""

from typing import Final

TRANSACTION_TYPE_INCOME: Final = "Gelir"
TRANSACTION_TYPE_EXPENSE: Final = "Gider"
TRANSACTION_TYPE_INVESTMENT: Final = "Yatırım"
TRANSACTION_TYPE_TRANSFER: Final = "Transfer"
TRANSACTION_TYPES: Final = (
    TRANSACTION_TYPE_INCOME,
    TRANSACTION_TYPE_EXPENSE,
    TRANSACTION_TYPE_INVESTMENT,
    TRANSACTION_TYPE_TRANSFER,
)

TRANSACTION_STATUS_PAID: Final = "Ödendi"
TRANSACTION_STATUS_PENDING: Final = "Bekliyor"
TRANSACTION_STATUSES: Final = (
    TRANSACTION_STATUS_PAID,
    TRANSACTION_STATUS_PENDING,
)

SOURCE_TYPE_MANUAL: Final = "manual"
SOURCE_TYPE_PLAN: Final = "plan"
SOURCE_TYPE_ASSET: Final = "asset"
SOURCE_TYPE_ASSET_SALE: Final = "asset_sale"
SOURCE_TYPE_ASSET_DIVIDEND: Final = "asset_dividend"
SOURCE_TYPE_ASSET_INTEREST: Final = "asset_interest"
SOURCE_TYPE_ADJUSTMENT: Final = "adjustment"
SOURCE_TYPE_REVERSAL: Final = "reversal"

ASSET_LINKED_SOURCE_TYPES: Final = (
    SOURCE_TYPE_ASSET,
    SOURCE_TYPE_ASSET_SALE,
    SOURCE_TYPE_ASSET_DIVIDEND,
    SOURCE_TYPE_ASSET_INTEREST,
)
PRESERVE_CASH_SOURCE_TYPES: Final = (
    SOURCE_TYPE_ASSET_SALE,
    SOURCE_TYPE_ASSET_DIVIDEND,
    SOURCE_TYPE_ASSET_INTEREST,
)

LEDGER_LAYER_CASH_EVENT: Final = "nakit_olay"

LEDGER_ADJUSTMENT_KIND_ADJUSTMENT: Final = "adjustment"
LEDGER_ADJUSTMENT_KIND_REVERSAL: Final = "reversal"
LEDGER_ADJUSTMENT_STATUS_REQUESTED: Final = "requested"
LEDGER_ADJUSTMENT_STATUS_APPLIED: Final = "applied"
IMMUTABLE_REASON_CODE_OTHER: Final = "other"

ASSET_UPDATE_TYPE_MANUAL: Final = "manual"
ASSET_UPDATE_TYPE_TRANSFER: Final = "transfer"
