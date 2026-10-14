"""
Birleşik Finans Defteri Servisi (Facade)
=========================================
Nakit akışı, planlı gelir/gider ve varlık yönetimini aynı mimaride birleştirir.
Alt servisler:
  - ledger_position_service: Varlık pozisyonları, değerlemeler, nakit transferleri ve işlem yönetimi
  - ledger_adjustment_service: Düzeltme (adjustment), iptal (reversal), denetim izi ve occurrence ödemeleri
  - ledger_summary_service: Varlık defter özetleri ve toplu sorgular
"""

from domain.transactions.exceptions import LedgerError, OptimisticConcurrencyError

from . import ledger_position_service
from .helpers import _resolve_tenant_id
from .ledger_adjustment_service import (
    _create_compensating_transaction,
    _current_actor_id,
    _current_request_id,
    _immutable_idempotency_key,
    _opposite_cash_type,
    _payment_value,
    _record_ledger_audit,
    _require_paid_transaction,
    create_adjustment_transaction,
    create_reversal_transaction,
    get_adjustment_audit,
    get_transaction_lineage,
    mark_occurrence_paid,
)
from .ledger_position_service import (
    _check_and_cleanup_plan_after_transaction_deletion,
    _create_buy_asset_transaction,
    _create_purchase_transaction,
    _create_sale_transaction,
    _detach_asset_ledger_references,
    _investment_category,
    _validate_asset_amounts,
    create_one_time_transaction,
    create_recurring_plan,
    delete_asset_position,
    delete_one_time_transaction,
    delete_recurring_plan,
    parse_asset_payload,
    sell_asset_position,
    transfer_cash_to_asset,
    update_asset_valuation,
    update_one_time_transaction,
    update_recurring_plan_entry,
)


def create_asset_position(*args, **kwargs):
    """Facade for ledger_position_service.create_asset_position with test-hook compatibility."""
    orig_purchase = ledger_position_service._create_purchase_transaction
    try:
        # Propagate monkeypatches applied on this module (financial_ledger) to the delegate
        current_func = globals().get("_create_purchase_transaction", orig_purchase)
        ledger_position_service._create_purchase_transaction = current_func
        return ledger_position_service.create_asset_position(*args, **kwargs)
    finally:
        ledger_position_service._create_purchase_transaction = orig_purchase

from .ledger_summary_service import (
    calculate_transaction_batch_summary,
    get_asset_ledger_summaries,
    get_asset_ledger_summary,
)

__all__ = [
    # Exceptions
    "LedgerError",
    "OptimisticConcurrencyError",
    # Tenant resolution
    "_resolve_tenant_id",
    # Position & Asset operations
    "_validate_asset_amounts",
    "parse_asset_payload",
    "_investment_category",
    "_create_purchase_transaction",
    "_create_buy_asset_transaction",
    "_create_sale_transaction",
    "create_asset_position",
    "sell_asset_position",
    "update_asset_valuation",
    "_detach_asset_ledger_references",
    "delete_asset_position",
    "create_one_time_transaction",
    "create_recurring_plan",
    "update_recurring_plan_entry",
    "delete_recurring_plan",
    "_check_and_cleanup_plan_after_transaction_deletion",
    "delete_one_time_transaction",
    "update_one_time_transaction",
    "transfer_cash_to_asset",
    # Summary operations
    "calculate_transaction_batch_summary",
    "get_asset_ledger_summary",
    "get_asset_ledger_summaries",
    # Adjustment & Audit operations
    "_opposite_cash_type",
    "_require_paid_transaction",
    "_current_actor_id",
    "_current_request_id",
    "_record_ledger_audit",
    "_immutable_idempotency_key",
    "_create_compensating_transaction",
    "create_adjustment_transaction",
    "create_reversal_transaction",
    "get_transaction_lineage",
    "get_adjustment_audit",
    "_payment_value",
    "mark_occurrence_paid",
]
