import pytest

from domain.transactions.constants import (
    SOURCE_TYPE_ADJUSTMENT,
    SOURCE_TYPE_ASSET,
    SOURCE_TYPE_ASSET_DIVIDEND,
    SOURCE_TYPE_ASSET_INTEREST,
    SOURCE_TYPE_ASSET_SALE,
    SOURCE_TYPE_MANUAL,
    SOURCE_TYPE_PLAN,
    SOURCE_TYPE_REVERSAL,
    TRANSACTION_STATUS_PAID,
    TRANSACTION_STATUS_PENDING,
    TRANSACTION_STATUSES,
    TRANSACTION_TYPE_EXPENSE,
    TRANSACTION_TYPE_INCOME,
    TRANSACTION_TYPE_INVESTMENT,
    TRANSACTION_TYPE_TRANSFER,
    TRANSACTION_TYPES,
)
from routes.transactions import _transaction_ui_options


@pytest.mark.regression
def test_transaction_persisted_codes_are_canonical_and_ordered():
    assert TRANSACTION_TYPES == (
        TRANSACTION_TYPE_INCOME,
        TRANSACTION_TYPE_EXPENSE,
        TRANSACTION_TYPE_INVESTMENT,
        TRANSACTION_TYPE_TRANSFER,
    )
    assert TRANSACTION_STATUSES == (
        TRANSACTION_STATUS_PAID,
        TRANSACTION_STATUS_PENDING,
    )
    assert len(set(TRANSACTION_TYPES)) == len(TRANSACTION_TYPES)
    assert len(set(TRANSACTION_STATUSES)) == len(TRANSACTION_STATUSES)


@pytest.mark.regression
def test_transaction_source_codes_are_stable_and_distinct():
    source_codes = {
        SOURCE_TYPE_MANUAL,
        SOURCE_TYPE_PLAN,
        SOURCE_TYPE_ASSET,
        SOURCE_TYPE_ASSET_SALE,
        SOURCE_TYPE_ASSET_DIVIDEND,
        SOURCE_TYPE_ASSET_INTEREST,
        SOURCE_TYPE_ADJUSTMENT,
        SOURCE_TYPE_REVERSAL,
    }
    assert len(source_codes) == 8
    assert all(code == code.strip().lower() for code in source_codes)


@pytest.mark.regression
def test_transaction_ui_options_use_canonical_codes_and_i18n_keys():
    options = _transaction_ui_options()
    assert [item["value"] for item in options["type_options"]] == list(TRANSACTION_TYPES)
    assert [item["value"] for item in options["status_options"]] == list(TRANSACTION_STATUSES)
    assert options["type_values"] == {
        "income": TRANSACTION_TYPE_INCOME,
        "expense": TRANSACTION_TYPE_EXPENSE,
        "investment": TRANSACTION_TYPE_INVESTMENT,
        "transfer": TRANSACTION_TYPE_TRANSFER,
    }
    assert options["status_values"] == {
        "paid": TRANSACTION_STATUS_PAID,
        "pending": TRANSACTION_STATUS_PENDING,
    }
    assert all(item["label_key"].startswith("tx_") for item in options["type_options"] + options["status_options"])
    assert len({item["dom_key"] for item in options["type_options"] + options["status_options"]}) == 6
