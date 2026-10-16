"""
Transaction Blueprint — routes/transactions.py

İşlem (Transaction) yönetimi için orchestrator ve route registration modülü.

Route modülleri:
  - routes/transactions_crud.py           → UI görünümleri (/transactions, /new_transaction, /edit_t, /delete_t, /transactions/<id>/quick-pay, /transactions/explorer)
  - routes/transactions_api.py            → REST API (/api/transactions, /api/transactions/<int:id>, lineage, adjustments, reversal, audit)
  - routes/transactions_occurrences.py    → Plan gerçekleşmeleri (/api/plans/<int:plan_id>/occurrences, pay, skip, cancel)

Filtreleme & Sayfalama:
  - filters, paginate desteği API katmanında sağlanır.

Güvenlik & Hata Yönetimi:
  - Oturum kontrolü, CSRF, try: ... except Exception: ve rollback_session yönetimi.
"""

import json  # noqa: F401
import logging
from datetime import datetime  # noqa: F401

from flask import flash, g, jsonify, redirect, render_template, request, session, url_for  # noqa: F401
from werkzeug.exceptions import NotFound  # noqa: F401

from bootstrap import get_container
from domain.transactions.constants import (
    TRANSACTION_STATUS_PAID,
    TRANSACTION_STATUS_PENDING,
    TRANSACTION_TYPE_EXPENSE,
    TRANSACTION_TYPE_INCOME,
    TRANSACTION_TYPE_INVESTMENT,
    TRANSACTION_TYPE_TRANSFER,
)
from domain.transactions.exceptions import LedgerError  # noqa: F401
from domain.transactions.services import (
    create_adjustment_transaction,  # noqa: F401
    create_reversal_transaction,  # noqa: F401
    get_adjustment_audit,  # noqa: F401
    get_transaction_lineage,  # noqa: F401
)
from models import BankAccount, BankStatementSnapshot, LedgerAdjustment, PlanOccurrence, Transaction  # noqa: F401
from shared.db import db  # noqa: F401
from shared.decimal_precision import to_decimal  # noqa: F401
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request  # noqa: F401
from utils.capabilities import has_capability
from utils.db_session import rollback_session  # noqa: F401
from utils.format_utils import today_display  # noqa: F401
from validators.request_validators import transaction_form_from_request  # noqa: F401

from .transactions_api import register_transaction_api_routes
from .transactions_crud import register_transaction_crud_routes
from .transactions_occurrences import register_transaction_occurrence_routes

logger = logging.getLogger(__name__)

_TRANSACTION_TYPE_OPTIONS = (
    ('Income', TRANSACTION_TYPE_INCOME, 'tx_type_income'),
    ('Expense', TRANSACTION_TYPE_EXPENSE, 'tx_type_expense'),
    ('Investment', TRANSACTION_TYPE_INVESTMENT, 'tx_type_investment'),
    ('Transfer', TRANSACTION_TYPE_TRANSFER, 'tx_type_transfer'),
)
_TRANSACTION_STATUS_OPTIONS = (
    ('Paid', TRANSACTION_STATUS_PAID, 'tx_status_paid'),
    ('Pending', TRANSACTION_STATUS_PENDING, 'tx_status_pending'),
)


def _transaction_ui_options():
    return {
        'type_options': [
            {'dom_key': dom_key, 'value': value, 'label_key': label_key}
            for dom_key, value, label_key in _TRANSACTION_TYPE_OPTIONS
        ],
        'status_options': [
            {'dom_key': dom_key, 'value': value, 'label_key': label_key}
            for dom_key, value, label_key in _TRANSACTION_STATUS_OPTIONS
        ],
        'type_values': {
            'income': TRANSACTION_TYPE_INCOME,
            'expense': TRANSACTION_TYPE_EXPENSE,
            'investment': TRANSACTION_TYPE_INVESTMENT,
            'transfer': TRANSACTION_TYPE_TRANSFER,
        },
        'status_values': {
            'paid': TRANSACTION_STATUS_PAID,
            'pending': TRANSACTION_STATUS_PENDING,
        },
        'type_label_keys': {
            value: label_key for _, value, label_key in _TRANSACTION_TYPE_OPTIONS
        },
        'status_label_keys': {
            value: label_key for _, value, label_key in _TRANSACTION_STATUS_OPTIONS
        },
    }


_container = get_container()
_outbox = _container.infrastructure.outbox()
_queries = _container.applications.transaction_queries()
_commands = _container.applications.transaction_commands(_outbox)


def _transaction_request_payload():
    """Merge retry and concurrency headers into the form payload."""
    payload = request.form.copy()
    idempotency_key = (request.headers.get("Idempotency-Key") or "").strip()
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key[:64]
    if_match = (request.headers.get("If-Match") or "").strip().strip(chr(34))
    if if_match.isdigit():
        payload["version"] = if_match
    return payload


def _phase4_json_body():
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return request.form.to_dict(flat=True)


def _phase4_error(message, error_code, status):
    return jsonify({
        'success': False,
        'error_code': error_code,
        'message': message,
        'request_id': request.headers.get('X-Request-ID', ''),
    }), status


def _phase4_require_capability(capability):
    if 'user_id' not in session:
        return _phase4_error('Oturum gerekli.', 'authentication_required', 401)
    user = g.get('current_user')
    if not has_capability(user, capability):
        return _phase4_error('Bu işlem için gerekli yetkiniz bulunmuyor.', 'capability_denied', 403)
    return None


def _serialize_occurrence(occurrence):
    return {
        'id': occurrence.id,
        'plan_id': occurrence.plan_id,
        'tenant_id': occurrence.tenant_id,
        'occurrence_number': occurrence.occurrence_number,
        'scheduled_date': occurrence.scheduled_date,
        'status': occurrence.status,
        'amount': str(occurrence.amount) if occurrence.amount is not None else None,
        'transaction_id': occurrence.transaction_id,
        'paid_at': occurrence.paid_at.isoformat() if occurrence.paid_at else None,
        'notes': occurrence.notes,
    }


def _serialize_transaction(transaction):
    return {
        'id': transaction.id,
        'tenant_id': transaction.tenant_id,
        'date': transaction.date,
        'category': transaction.category,
        'description': transaction.description,
        'note': transaction.note,
        'type': transaction.type,
        'status': transaction.status,
        'amount': str(transaction.amount) if transaction.amount is not None else '0',
        'source_type': transaction.source_type,
        'source_id': transaction.source_id,
        'bank_account_id': transaction.bank_account_id,
        'installment_number': transaction.installment_number,
        'version': transaction.version,
        'is_deleted': bool(transaction.is_deleted),
    }


def _serialize_payment(payment):
    return {
        'id': payment.id,
        'plan_id': payment.plan_id,
        'tenant_id': payment.tenant_id,
        'amount': str(payment.amount),
        'payment_date': payment.payment_date,
        'installment_number': payment.installment_number,
        'transaction_id': payment.transaction_id,
        'notes': payment.notes,
    }


def _serialize_adjustment(adjustment):
    return {
        'id': adjustment.id,
        'tenant_id': adjustment.tenant_id,
        'original_transaction_id': adjustment.original_transaction_id,
        'compensating_transaction_id': adjustment.compensating_transaction_id,
        'kind': adjustment.kind,
        'status': adjustment.status,
        'amount_delta': str(adjustment.amount_delta),
        'original_amount_snapshot': str(adjustment.original_amount_snapshot),
        'original_type_snapshot': adjustment.original_type_snapshot,
        'original_category_snapshot': adjustment.original_category_snapshot,
        'original_date_snapshot': adjustment.original_date_snapshot,
        'original_version': adjustment.original_version,
        'reason_code': adjustment.reason_code,
        'reason_text': adjustment.reason_text,
        'requested_by': adjustment.requested_by,
        'approved_by': adjustment.approved_by,
        'requested_at': adjustment.requested_at.isoformat() if adjustment.requested_at else None,
        'applied_at': adjustment.applied_at.isoformat() if adjustment.applied_at else None,
        'failure_code': adjustment.failure_code,
        'failure_message': adjustment.failure_message,
        'idempotency_key': adjustment.idempotency_key,
        'correlation_id': adjustment.correlation_id,
        'metadata': adjustment.metadata_json,
    }


def _serialize_audit_event(event):
    return {
        'id': event.id,
        'tenant_id': event.tenant_id,
        'adjustment_id': event.adjustment_id,
        'transaction_id': event.transaction_id,
        'event_type': event.event_type,
        'actor_user_id': event.actor_user_id,
        'correlation_id': event.correlation_id,
        'request_id': event.request_id,
        'occurred_at': event.occurred_at.isoformat() if event.occurred_at else None,
        'previous_hash': event.previous_hash,
        'event_hash': event.event_hash,
        'payload': event.payload,
    }


def register_transaction_routes(bp):
    """
    Transactions blueprint için tüm alt modül route'larını kaydeder.
    """
    register_transaction_crud_routes(bp, _transaction_ui_options, _transaction_request_payload)
    register_transaction_occurrence_routes(
        bp,
        _phase4_error,
        _phase4_require_capability,
        _phase4_json_body,
        _serialize_occurrence,
        _serialize_payment,
        _serialize_transaction,
    )
    register_transaction_api_routes(
        bp,
        _phase4_error,
        _phase4_require_capability,
        _phase4_json_body,
        _serialize_transaction,
        _serialize_occurrence,
        _serialize_payment,
        _serialize_adjustment,
        _serialize_audit_event,
    )
