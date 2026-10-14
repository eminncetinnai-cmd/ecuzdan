"""
Transaction Reconciliation Routes — routes/transactions_reconciliation.py

Banka hesapları, ekstre snapshot'ları ve mutabakat (reconciliation)
API endpoint'lerini yönetir.
"""

import logging
from datetime import datetime

from flask import g, jsonify, render_template, request, session

from domain.reconciliation import (
    ReconciliationAccountNotFoundError,
    ReconciliationInputError,
    build_reconciliation,
    create_bank_account,
    get_bank_account,
    list_statement_snapshots,
    parse_reconciliation_params,
    save_statement_snapshot,
)
from shared.decimal_precision import to_decimal
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _serialize_bank_account(account):
    return {
        'id': account.id,
        'name': account.name,
        'institution': account.institution,
        'account_type': account.account_type,
        'currency': account.currency,
        'is_active': bool(account.is_active),
        'created_at': account.created_at.isoformat() if account.created_at else None,
    }


def _serialize_statement_snapshot(snapshot):
    return {
        'id': snapshot.id,
        'bank_account_id': snapshot.bank_account_id,
        'as_of': snapshot.as_of,
        'balance': str(snapshot.balance),
        'currency': snapshot.currency,
        'source': snapshot.source,
        'note': snapshot.note,
        'created_at': snapshot.created_at.isoformat() if snapshot.created_at else None,
    }


def register_transaction_reconciliation_routes(bp, error_fn):
    """Register reconciliation API routes on the transactions blueprint."""

    @bp.route('/reconciliation', methods=['GET'])
    @login_required
    def reconciliation_page():
        """Render bank balance reconciliation UI."""
        return render_template('reconciliation.html')

    def _reconciliation_request_payload(include_unassigned=False):
        if 'user_id' not in session:
            return None, error_fn('Oturum gerekli.', 'authentication_required', 401)
        tenant_id = g.get('tenant_id')
        if not tenant_id:
            return None, error_fn('Tenant bağlamı bulunamadı.', 'tenant_context_required', 403)
        params = parse_reconciliation_params(request.args)
        payload = build_reconciliation(
            tenant_id,
            as_of=params['as_of'],
            statement_balance=params['statement_balance'],
            pending_limit=params['pending_limit'],
            bank_account_id=params['account_id'],
            currency=params['currency'],
            include_unassigned=include_unassigned,
        )
        return payload, None

    @bp.route('/api/reconciliation', methods=['GET'])
    def api_reconciliation():
        """Canonical account-aware, read-only reconciliation worksheet."""
        try:
            payload, error = _reconciliation_request_payload()
            if error:
                return error
            return jsonify(payload)
        except ReconciliationAccountNotFoundError as exc:
            return error_fn(str(exc), 'resource_not_found', 404)
        except ReconciliationInputError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 400
        except Exception as exc:
            logger.exception('Reconciliation API error: %s', exc)
            return jsonify({'success': False, 'message': 'Mutabakat özeti oluşturulamadı.'}), 500

    @bp.route('/api/transactions/reconciliation', methods=['GET'])
    def api_transactions_reconciliation():
        """Backward-compatible tenant-wide reconciliation API shim."""
        try:
            payload, error = _reconciliation_request_payload(include_unassigned=True)
            if error:
                return error
            return jsonify(payload)
        except ReconciliationAccountNotFoundError as exc:
            return error_fn(str(exc), 'resource_not_found', 404)
        except ReconciliationInputError as exc:
            return jsonify({'success': False, 'message': f'Geçersiz mutabakat parametresi: {exc}'}), 400
        except Exception as exc:
            logger.exception('Legacy reconciliation API error: %s', exc)
            return jsonify({'success': False, 'message': 'Mutabakat özeti oluşturulamadı.'}), 500

    @bp.route('/api/reconciliation/accounts', methods=['POST'])
    def api_reconciliation_create_account():
        """Create one tenant-owned bank account; no balance is synthesized."""
        if 'user_id' not in session:
            return error_fn('Oturum gerekli.', 'authentication_required', 401)
        tenant_id = g.get('tenant_id')
        if not tenant_id:
            return error_fn('Tenant bağlamı bulunamadı.', 'tenant_context_required', 403)
        body = request.get_json(silent=True) or request.form.to_dict(flat=True)
        name = str(body.get('name') or '').strip()
        institution = str(body.get('institution') or '').strip() or None
        account_type = str(body.get('account_type') or 'checking').strip().lower()
        currency = str(body.get('currency') or 'TRY').strip().upper()
        if not name or len(name) > 100:
            return jsonify({'success': False, 'message': 'Hesap adı 1-100 karakter olmalıdır.'}), 400
        if institution and len(institution) > 100:
            return jsonify({'success': False, 'message': 'Banka adı en fazla 100 karakter olabilir.'}), 400
        if account_type not in {'checking', 'savings', 'credit_card', 'cash'}:
            return jsonify({'success': False, 'message': 'Geçersiz hesap türü.'}), 400
        if len(currency) != 3 or not currency.isalpha():
            return jsonify({'success': False, 'message': 'Para birimi ISO 4217 formatında olmalıdır.'}), 400
        try:
            account = create_bank_account(
                tenant_id=tenant_id,
                name=name,
                institution=institution,
                account_type=account_type,
                currency=currency,
                created_by=session.get('user_id'),
            )
            return jsonify({'success': True, 'account': _serialize_bank_account(account)}), 201
        except Exception as exc:
            logger.exception('Bank account create error: %s', exc)
            return jsonify({'success': False, 'message': 'Banka hesabı oluşturulamadı.'}), 500

    @bp.route('/api/reconciliation/statements', methods=['GET'])
    def api_reconciliation_statements():
        """List saved statement snapshots for one tenant-owned account."""
        if 'user_id' not in session:
            return error_fn('Oturum gerekli.', 'authentication_required', 401)
        tenant_id = g.get('tenant_id')
        if not tenant_id:
            return error_fn('Tenant bağlamı bulunamadı.', 'tenant_context_required', 403)
        try:
            account_id = int(request.args.get('account_id', ''))
            limit = int(request.args.get('limit', '20'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'account_id ve limit geçerli olmalıdır.'}), 400
        if not 1 <= limit <= 100:
            return jsonify({'success': False, 'message': 'limit 1 ile 100 arasında olmalıdır.'}), 400
        account = get_bank_account(account_id, tenant_id)
        if not account:
            return jsonify({'success': False, 'message': 'Banka hesabı bulunamadı.'}), 404
        snapshots = list_statement_snapshots(account.id, tenant_id, limit=limit)
        return jsonify({
            'success': True,
            'account': _serialize_bank_account(account),
            'statements': [_serialize_statement_snapshot(snapshot) for snapshot in snapshots],
        })

    @bp.route('/api/reconciliation/statements', methods=['POST'])
    def api_reconciliation_save_statement():
        """Upsert an explicit user-entered statement closing balance."""
        if 'user_id' not in session:
            return error_fn('Oturum gerekli.', 'authentication_required', 401)
        tenant_id = g.get('tenant_id')
        if not tenant_id:
            return error_fn('Tenant bağlamı bulunamadı.', 'tenant_context_required', 403)
        body = request.get_json(silent=True) or request.form.to_dict(flat=True)
        try:
            account_id = int(body.get('account_id', ''))
            as_of = str(body.get('as_of') or '')
            parsed_as_of = datetime.strptime(as_of, '%Y-%m-%d')
            if parsed_as_of.strftime('%Y-%m-%d') != as_of:
                raise ValueError('as_of YYYY-MM-DD formatında olmalıdır')
            balance_raw = body.get('balance')
            if balance_raw in (None, ''):
                raise ValueError('balance zorunludur')
            balance = to_decimal(balance_raw)
            if not balance.is_finite():
                raise ValueError('balance sonlu bir sayı olmalıdır')
        except (TypeError, ValueError, ArithmeticError) as exc:
            return jsonify({'success': False, 'message': f'Geçersiz statement bilgisi: {exc}'}), 400
        account = get_bank_account(account_id, tenant_id)
        if not account:
            return jsonify({'success': False, 'message': 'Banka hesabı bulunamadı.'}), 404
        currency = str(body.get('currency') or account.currency).strip().upper()
        if currency != account.currency:
            return jsonify({'success': False, 'message': 'Statement para birimi hesap para birimiyle aynı olmalıdır.'}), 400
        try:
            snapshot = save_statement_snapshot(
                tenant_id=tenant_id,
                bank_account_id=account.id,
                as_of=as_of,
                balance=balance,
                currency=currency,
                note=str(body.get('note') or '').strip()[:300] or None,
                source='manual',
            )
            result = build_reconciliation(
                tenant_id,
                as_of=as_of,
                pending_limit=50,
                bank_account_id=account.id,
                currency=currency,
            )
            return jsonify({
                'success': True,
                'statement': _serialize_statement_snapshot(snapshot),
                'reconciliation': result,
            }), 200
        except Exception as exc:
            logger.exception('Bank statement save error: %s', exc)
            return jsonify({'success': False, 'message': 'Statement bakiyesi kaydedilemedi.'}), 500
