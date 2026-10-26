"""
Transaction REST API Routes — routes/transactions_api.py

İşlem (Transaction) explorer API, işlem detay, soy ağacı (lineage),
düzeltme (adjustment), ters kayıt (reversal) ve denetim izi (audit)
REST API endpoint'lerini yönetir.
"""

import json
import logging
from datetime import date

from flask import g, jsonify, request, session
from sqlalchemy import case, func, or_

from domain.reconciliation import list_bank_accounts
from domain.transactions.constants import (
    TRANSACTION_STATUS_PENDING,
    TRANSACTION_STATUSES,
    TRANSACTION_TYPE_EXPENSE,
    TRANSACTION_TYPE_INCOME,
    TRANSACTION_TYPES,
)
from domain.transactions.services import (
    LedgerError,
    create_adjustment_transaction,
    create_reversal_transaction,
    get_adjustment_audit,
    get_transaction_lineage,
)
from infrastructure.i18n import i18n
from models import BankAccount, LedgerAdjustment, Transaction
from shared.decimal_precision import to_decimal
from utils.capabilities import Capability
from utils.db_session import rollback_session

logger = logging.getLogger(__name__)


def register_transaction_api_routes(
    bp,
    error_fn,
    require_capability_fn,
    json_body_fn,
    serialize_transaction_fn,
    serialize_occurrence_fn,
    serialize_payment_fn,
    serialize_adjustment_fn,
    serialize_audit_event_fn,
):
    """Register REST API routes on the transactions blueprint."""

    @bp.route('/api/transactions', methods=['GET'])
    def api_transactions():
        """Tenant-scoped, deterministic and filter-aware Transaction Explorer API."""
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error_code': 'authentication_required',
                'message': 'Oturum gerekli.',
            }), 401
        tenant_id = g.get('tenant_id')
        if not tenant_id:
            return jsonify({
                'success': False,
                'error_code': 'tenant_context_required',
                'message': 'Tenant bağlamı bulunamadı.',
            }), 403
        try:
            page = max(request.args.get('page', 1, type=int), 1)
            requested_per_page = request.args.get('per_page', 50, type=int)
            per_page = min(max(requested_per_page or 50, 1), 100)
            filters_json = request.args.get('filters')
            if filters_json:
                try:
                    filters = json.loads(filters_json)
                except json.JSONDecodeError:
                    return jsonify({
                        'success': False,
                        'error_code': 'invalid_filters',
                        'message': 'Filtre biçimi geçersiz.',
                    }), 400
                if not isinstance(filters, dict):
                    return jsonify({
                        'success': False,
                        'error_code': 'invalid_filters',
                        'message': 'Filtre biçimi geçersiz.',
                    }), 400
            else:
                filters = {}

            # Support flat query parameters as fallback/convenience
            if not filters.get('search'):
                flat_search = request.args.get('search') or request.args.get('q')
                if flat_search:
                    filters['search'] = flat_search
            if not filters.get('category') and request.args.get('category'):
                filters['category'] = request.args.get('category')
            if not filters.get('dateFrom') and (request.args.get('dateFrom') or request.args.get('date_from')):
                filters['dateFrom'] = request.args.get('dateFrom') or request.args.get('date_from')
            if not filters.get('dateTo') and (request.args.get('dateTo') or request.args.get('date_to')):
                filters['dateTo'] = request.args.get('dateTo') or request.args.get('date_to')
            if not filters.get('types'):
                flat_types = request.args.getlist('types') or request.args.getlist('type')
                if not flat_types and request.args.get('type'):
                    flat_types = [t.strip() for t in request.args.get('type').split(',') if t.strip()]
                if flat_types:
                    filters['types'] = flat_types
            if not filters.get('statuses'):
                flat_statuses = request.args.getlist('statuses') or request.args.getlist('status')
                if not flat_statuses and request.args.get('status'):
                    flat_statuses = [s.strip() for s in request.args.get('status').split(',') if s.strip()]
                if flat_statuses:
                    filters['statuses'] = flat_statuses
            if not filters.get('minAmount') and (request.args.get('minAmount') or request.args.get('min_amount')):
                filters['minAmount'] = request.args.get('minAmount') or request.args.get('min_amount')
            if not filters.get('maxAmount') and (request.args.get('maxAmount') or request.args.get('max_amount')):
                filters['maxAmount'] = request.args.get('maxAmount') or request.args.get('max_amount')
            if not filters.get('bankAccountId'):
                flat_acc = request.args.get('bankAccountId') or request.args.get('bank_account_id') or request.args.get('account_id')
                if flat_acc:
                    filters['bankAccountId'] = flat_acc

            query = Transaction.query.filter(
                Transaction.tenant_id == tenant_id,
                Transaction.is_deleted.is_(False),
            )
            normalized = {}

            search = str(filters.get('search') or '').strip()[:120]
            if search:
                search_term = f'%{search}%'
                query = query.filter(or_(
                    Transaction.description.ilike(search_term),
                    Transaction.note.ilike(search_term),
                    Transaction.category.ilike(search_term),
                ))
                normalized['search'] = search

            date_from = str(filters.get('dateFrom') or '').strip()
            date_to = str(filters.get('dateTo') or '').strip()
            try:
                if date_from:
                    date.fromisoformat(date_from)
                if date_to:
                    date.fromisoformat(date_to)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_date_range',
                    'message': 'Tarih aralığı geçersiz.',
                }), 400
            if date_from and date_to and date_from > date_to:
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_date_range',
                    'message': 'Başlangıç tarihi bitiş tarihinden sonra olamaz.',
                }), 400
            if date_from:
                query = query.filter(Transaction.date >= date_from)
                normalized['dateFrom'] = date_from
            if date_to:
                query = query.filter(Transaction.date <= date_to)
                normalized['dateTo'] = date_to

            allowed_types = set(TRANSACTION_TYPES)
            raw_types = filters.get('types') or []
            if not isinstance(raw_types, list):
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_types',
                    'message': 'İşlem türü filtresi geçersiz.',
                }), 400
            types = [str(value) for value in raw_types]
            if any(value not in allowed_types for value in types):
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_types',
                    'message': 'İşlem türü filtresi geçersiz.',
                }), 400
            if types:
                query = query.filter(Transaction.type.in_(types))
                normalized['types'] = types

            category = str(filters.get('category') or '').strip()[:50]
            if category:
                query = query.filter(Transaction.category == category)
                normalized['category'] = category

            allowed_statuses = set(TRANSACTION_STATUSES)
            raw_statuses = filters.get('statuses') or []
            if not isinstance(raw_statuses, list):
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_statuses',
                    'message': 'İşlem durumu filtresi geçersiz.',
                }), 400
            statuses = [str(value) for value in raw_statuses]
            if any(value not in allowed_statuses for value in statuses):
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_statuses',
                    'message': 'İşlem durumu filtresi geçersiz.',
                }), 400
            if statuses:
                query = query.filter(Transaction.status.in_(statuses))
                normalized['statuses'] = statuses

            min_amount = str(filters.get('minAmount') or '').strip()
            max_amount = str(filters.get('maxAmount') or '').strip()
            try:
                min_decimal = to_decimal(min_amount) if min_amount else None
                max_decimal = to_decimal(max_amount) if max_amount else None
            except (TypeError, ValueError, ArithmeticError):
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_amount_range',
                    'message': 'Tutar aralığı geçersiz.',
                }), 400
            if min_decimal is not None and max_decimal is not None and min_decimal > max_decimal:
                return jsonify({
                    'success': False,
                    'error_code': 'invalid_amount_range',
                    'message': 'Minimum tutar maksimum tutardan büyük olamaz.',
                }), 400
            if min_decimal is not None:
                query = query.filter(Transaction.amount >= min_decimal)
                normalized['minAmount'] = min_amount
            if max_decimal is not None:
                query = query.filter(Transaction.amount <= max_decimal)
                normalized['maxAmount'] = max_amount

            raw_account_id = filters.get('bankAccountId', filters.get('account_id'))
            account_id = None
            if raw_account_id not in (None, '', 0, '0'):
                try:
                    account_id = int(raw_account_id)
                except (TypeError, ValueError):
                    return jsonify({
                        'success': False,
                        'error_code': 'invalid_account',
                        'message': 'Banka hesabı filtresi geçersiz.',
                    }), 400
                if account_id < 1:
                    return jsonify({
                        'success': False,
                        'error_code': 'invalid_account',
                        'message': 'Banka hesabı filtresi geçersiz.',
                    }), 400
                query = query.filter(Transaction.bank_account_id == account_id)
                normalized['bankAccountId'] = account_id

            query = query.order_by(Transaction.date.desc(), Transaction.id.desc())

            summary_row = query.with_entities(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
                func.coalesce(func.sum(case((Transaction.type == TRANSACTION_TYPE_INCOME, Transaction.amount), else_=0)), 0),
                func.coalesce(func.sum(case((Transaction.type == TRANSACTION_TYPE_EXPENSE, Transaction.amount), else_=0)), 0),
                func.coalesce(func.sum(case((Transaction.status == TRANSACTION_STATUS_PENDING, 1), else_=0)), 0),
            ).one()
            total_count, total_amount, total_income, total_expense, total_pending = summary_row

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            accounts = list_bank_accounts(tenant_id)
            account_names = {account.id: account.name for account in accounts}
            account_currencies = {account.id: account.currency for account in accounts}
            summary_currency = account_currencies.get(account_id) if account_id is not None else None
            transactions_data = []
            for tx in pagination.items:
                transactions_data.append({
                    'id': tx.id,
                    'date': tx.date or None,
                    'category': tx.category,
                    'description': tx.description,
                    'note': tx.note,
                    'amount': str(tx.amount) if tx.amount is not None else '0',
                    'type': tx.type,
                    'status': tx.status,
                    'source_id': tx.source_id,
                    'source_type': tx.source_type,
                    'bank_account_id': tx.bank_account_id,
                    'bank_account_name': account_names.get(tx.bank_account_id),
                    'bank_account_currency': account_currencies.get(tx.bank_account_id),
                    'is_generated': bool(tx.source_type),
                })

            return jsonify({
                'success': True,
                'transactions': transactions_data,
                'summary': {
                    'total_count': int(total_count or 0),
                    'total_amount': str(total_amount or 0),
                    'total_income': str(total_income or 0),
                    'total_expense': str(total_expense or 0),
                    'total_net': str((total_income or 0) - (total_expense or 0)),
                    'total_pending': int(total_pending or 0),
                    'currency': summary_currency,
                },
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': int(total_count or 0),
                    'has_next': pagination.has_next,
                },
                'filters': normalized,
                'accounts': [{
                    'id': account.id,
                    'name': account.name,
                    'currency': account.currency,
                    'account_type': account.account_type,
                } for account in accounts],
                'has_more': pagination.has_next,
            })

        except Exception as exc:
            logger.exception(f'API transactions error: {exc}')
            return jsonify({
                'success': False,
                'error_code': 'unexpected_error',
                'message': 'İşlemler yüklenemedi.',
            }), 500

    @bp.route('/api/transactions/<int:id>', methods=['GET'])
    def api_transaction_detail(id):
        """Return tenant-scoped, read-only transaction detail context."""
        tenant_id = g.get('tenant_id')
        if not tenant_id:
            return error_fn('Tenant bağlamı bulunamadı.', 'tenant_context_required', 403)
        try:
            transaction = Transaction.query.filter_by(
                id=id,
                tenant_id=tenant_id,
                is_deleted=False,
            ).first()

            if not transaction:
                return error_fn(i18n.gettext('tx_transactions_not_found'), 'resource_not_found', 404)

            account = None
            if transaction.bank_account_id:
                account = BankAccount.query.filter_by(
                    id=transaction.bank_account_id,
                    tenant_id=tenant_id,
                ).first()

            return jsonify({
                'success': True,
                'id': transaction.id,
                'date': transaction.date or None,
                'category': transaction.category,
                'description': transaction.description,
                'note': transaction.note,
                'amount': str(transaction.amount) if transaction.amount is not None else '0',
                'type': transaction.type,
                'status': transaction.status,
                'source_id': transaction.source_id,
                'source_type': transaction.source_type,
                'source_label': transaction.origin,
                'bank_account_id': transaction.bank_account_id,
                'bank_account_name': account.name if account else None,
                'bank_account_currency': account.currency if account else None,
                'ledger_layer': transaction.ledger_layer,
                'is_generated': bool(transaction.source_type),
                'is_immutable': True,
                'reconciliation_available': bool(account),
            })

        except Exception as e:
            logger.exception(f"API transaction detail error: {e}")
            return error_fn(i18n.gettext('tx_explorer_error_description'), 'unexpected_error', 500)

    @bp.route('/api/transactions/<int:transaction_id>/lineage', methods=['GET'])
    def api_transaction_lineage(transaction_id):
        if 'user_id' not in session:
            return error_fn('Oturum gerekli.', 'authentication_required', 401)
        try:
            lineage = get_transaction_lineage(transaction_id, g.get('tenant_id'))
            return jsonify({
                'success': True,
                'data': {
                    'original': serialize_transaction_fn(lineage['original']),
                    'occurrence': (
                        serialize_occurrence_fn(lineage['occurrence'])
                        if lineage['occurrence'] else None
                    ),
                    'payments': [serialize_payment_fn(item) for item in lineage['payments']],
                    'adjustments': [serialize_adjustment_fn(item) for item in lineage['adjustments']],
                    'audit_events': [serialize_audit_event_fn(item) for item in lineage['audit_events']],
                },
                'message': '',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except LookupError as exc:
            return error_fn(str(exc), 'resource_not_found', 404)
        except Exception:
            logger.exception('Transaction lineage API error')
            return error_fn('Transaction lineage oluşturulamadı.', 'unexpected_error', 500)

    @bp.route('/api/transactions/<int:transaction_id>/adjustments', methods=['POST'])
    @bp.route('/api/transactions/<int:transaction_id>/adjustment', methods=['POST'])
    @bp.route('/transactions/<int:transaction_id>/adjustments', methods=['POST'])
    @bp.route('/transactions/<int:transaction_id>/adjustment', methods=['POST'])
    def api_create_adjustment(transaction_id):
        guard = require_capability_fn(Capability.LEDGER_ADJUST)
        if guard:
            return guard
        tenant_id = g.get('tenant_id')
        original_transaction = Transaction.query.filter_by(
            id=transaction_id,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()
        if original_transaction is None:
            return error_fn('Kayıt bulunamadı.', 'resource_not_found', 404)
        body = json_body_fn()
        idempotency_key = (request.headers.get('Idempotency-Key') or body.get('idempotency_key') or '').strip()[:64]
        if not idempotency_key:
            import secrets
            idempotency_key = f"adj:{transaction_id}:{secrets.token_hex(8)}"
        reason_code = str(body.get('reason_code') or '').strip()
        reason_text = str(body.get('reason_text') or '').strip()
        if not reason_code or not reason_text:
            return error_fn(
                'Neden kodu ve açıklama zorunludur.',
                'validation_error',
                400,
            )
        existing = LedgerAdjustment.query.filter_by(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        ).first()
        try:
            delta = to_decimal(body.get('amount_delta'))
            compensating = create_adjustment_transaction(
                transaction_id,
                delta,
                reason_text,
                tenant_id,
                reason_code=reason_code,
                metadata=body.get('metadata'),
                idempotency_key=idempotency_key,
            )
            adjustment = LedgerAdjustment.query.filter_by(
                tenant_id=tenant_id,
                idempotency_key=idempotency_key,
            ).first()
            if adjustment is None:
                adjustment = LedgerAdjustment.query.filter_by(
                    tenant_id=tenant_id,
                    original_transaction_id=transaction_id,
                    kind='adjustment',
                ).order_by(LedgerAdjustment.created_at.desc()).first()
            if adjustment is None:
                raise LedgerError('Adjustment kaydı oluşturulamadı.')
            status_code = 200 if existing else 201
            return jsonify({
                'success': True,
                'data': {
                    'adjustment': serialize_adjustment_fn(adjustment),
                    'compensating_transaction': serialize_transaction_fn(compensating),
                    'audit_reference': adjustment.correlation_id,
                },
                'message': 'Düzeltme uygulandı.',
                'request_id': request.headers.get('X-Request-ID', ''),
                'idempotency_replayed': bool(existing),
            }), status_code
        except LookupError as exc:
            rollback_session()
            return error_fn(str(exc), 'resource_not_found', 404)
        except (LedgerError, ValueError, ArithmeticError) as exc:
            rollback_session()
            if 'bulunamadı veya yetkisiz' in str(exc):
                return error_fn('Kayıt bulunamadı.', 'resource_not_found', 404)
            return error_fn(str(exc), 'financial_invariant_violation', 422)
        except Exception:
            logger.exception('Adjustment API error')
            rollback_session()
            return error_fn('Düzeltme uygulanamadı.', 'unexpected_error', 500)

    @bp.route('/api/transactions/<int:transaction_id>/reversal', methods=['POST'])
    @bp.route('/transactions/<int:transaction_id>/reversal', methods=['POST'])
    def api_create_reversal(transaction_id):
        guard = require_capability_fn(Capability.LEDGER_REVERSE)
        if guard:
            return guard
        tenant_id = g.get('tenant_id')
        original_transaction = Transaction.query.filter_by(
            id=transaction_id,
            tenant_id=tenant_id,
            is_deleted=False,
        ).first()
        if original_transaction is None:
            return error_fn('Kayıt bulunamadı.', 'resource_not_found', 404)
        body = json_body_fn()
        idempotency_key = (request.headers.get('Idempotency-Key') or body.get('idempotency_key') or '').strip()[:64]
        if not idempotency_key:
            import secrets
            idempotency_key = f"rev:{transaction_id}:{secrets.token_hex(8)}"
        reason_code = str(body.get('reason_code') or 'CANCELLED').strip()
        reason_text = str(body.get('reason_text') or 'İptal / Ters Kayıt').strip()
        if not reason_code or not reason_text:
            return error_fn(
                'Neden kodu ve açıklama zorunludur.',
                'validation_error',
                400,
            )
        existing = LedgerAdjustment.query.filter_by(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        ).first()
        if not existing:
            existing = LedgerAdjustment.query.filter_by(
                tenant_id=tenant_id,
                original_transaction_id=transaction_id,
                kind='reversal',
            ).first()
        try:
            compensating = create_reversal_transaction(
                transaction_id,
                reason_text,
                tenant_id,
                reason_code=reason_code,
                metadata=body.get('metadata'),
                idempotency_key=idempotency_key,
            )
            adjustment = LedgerAdjustment.query.filter_by(
                tenant_id=tenant_id,
                idempotency_key=idempotency_key,
            ).first()
            if adjustment is None:
                adjustment = LedgerAdjustment.query.filter_by(
                    tenant_id=tenant_id,
                    original_transaction_id=transaction_id,
                    kind='reversal',
                ).order_by(LedgerAdjustment.created_at.desc()).first()
            if adjustment is None:
                raise LedgerError('Reversal kaydı oluşturulamadı.')
            status_code = 200 if existing else 201
            return jsonify({
                'success': True,
                'data': {
                    'adjustment': serialize_adjustment_fn(adjustment),
                    'compensating_transaction': serialize_transaction_fn(compensating),
                    'audit_reference': adjustment.correlation_id,
                    'original_status': original_transaction.status,
                },
                'message': 'Ters kayıt uygulandı. İşlem tekrar bekleyen durumuna alındı.',
                'request_id': request.headers.get('X-Request-ID', ''),
                'idempotency_replayed': bool(existing),
            }), status_code
        except LookupError as exc:
            rollback_session()
            return error_fn(str(exc), 'resource_not_found', 404)
        except (LedgerError, ValueError, ArithmeticError) as exc:
            rollback_session()
            if 'bulunamadı veya yetkisiz' in str(exc):
                return error_fn('Kayıt bulunamadı.', 'resource_not_found', 404)
            return error_fn(str(exc), 'financial_invariant_violation', 422)
        except Exception:
            logger.exception('Reversal API error')
            rollback_session()
            return error_fn('Ters kayıt uygulanamadı.', 'unexpected_error', 500)

    @bp.route('/api/ledger-adjustments/<int:adjustment_id>/audit', methods=['GET'])
    def api_adjustment_audit(adjustment_id):
        guard = require_capability_fn(Capability.LEDGER_AUDIT_READ)
        if guard:
            return guard
        try:
            adjustment, events = get_adjustment_audit(adjustment_id, g.get('tenant_id'))
            return jsonify({
                'success': True,
                'data': {
                    'adjustment_id': adjustment.id,
                    'events': [serialize_audit_event_fn(item) for item in events],
                },
                'message': '',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except LookupError as exc:
            return error_fn(str(exc), 'resource_not_found', 404)
        except Exception:
            logger.exception('Adjustment audit API error')
            return error_fn('Audit geçmişi oluşturulamadı.', 'unexpected_error', 500)
