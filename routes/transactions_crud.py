"""
Transaction CRUD & UI Routes — routes/transactions_crud.py

İşlem (Transaction) listeleme, ekleme, güncelleme, silme, hızlı ödeme
ve explorer UI endpoint'lerini yönetir.
"""

import logging

from flask import flash, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound

from bootstrap import get_container
from domain.reconciliation import list_bank_accounts
from domain.transactions.constants import (
    TRANSACTION_STATUS_PAID,
    TRANSACTION_STATUS_PENDING,
)
from domain.transactions.services import (
    LedgerError,
    calculate_transaction_batch_summary,
)
from engines.financial_engine import invalidate_financial_cache, today_display
from infrastructure.i18n import i18n
from shared.decimal_precision import to_decimal
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.db_session import rollback_session
from validators.request_validators import transaction_form_from_request

logger = logging.getLogger(__name__)


def register_transaction_crud_routes(bp, ui_options_fn, request_payload_fn):
    """Register UI and CRUD routes on the transactions blueprint."""
    container = get_container()
    outbox = container.infrastructure.outbox()
    queries = container.applications.transaction_queries()
    commands = container.applications.transaction_commands(outbox)

    @bp.route('/transactions', methods=['GET'])
    def transactions():
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 100, type=int)
            per_page = max(10, min(per_page, 1000))
            edit_id = request.args.get('edit', type=int)
            tenant_id = g.get('tenant_id')
            context = queries['get_transaction_page'].execute(
                page=page, edit_id=edit_id, tenant_id=tenant_id, per_page=per_page
            )
            bank_accounts = list_bank_accounts(tenant_id)
            tx_items = context['last_t'].items if context.get('last_t') else []

            tx_summary = context.get('tx_summary') or calculate_transaction_batch_summary(tx_items)
            plan_names = context.get('plan_names') or {}

            active_tab = request.args.get('tab', '')
            if not active_tab:
                status_arg = request.args.get('status')
                if status_arg == TRANSACTION_STATUS_PENDING:
                    active_tab = 'pending'
                elif status_arg == TRANSACTION_STATUS_PAID:
                    active_tab = 'paid'
                else:
                    active_tab = 'all'

            if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
                paginator = context.get('last_t')
                return jsonify({
                    'success': True,
                    'page': paginator.page if paginator else page,
                    'pages': paginator.pages if paginator else 1,
                    'total': paginator.total if paginator else 0,
                    'items': [
                        {
                            'id': t.id,
                            'date': t.date,
                            'amount': float(t.amount or 0),
                            'type': t.type,
                            'category': t.category,
                            'description': t.description,
                            'status': t.status,
                            'source_type': getattr(t, 'source_type', None),
                            'plan_name': plan_names.get(getattr(t, 'source_id', None)),
                        }
                        for t in tx_items
                    ],
                    'summary': {
                        k: (float(v) if hasattr(v, '__float__') and not isinstance(v, (int, str)) else v)
                        for k, v in tx_summary.items()
                    },
                })

            return render_template(
                'transactions.html',
                last_t=context['last_t'],
                cats=context['cats'],
                today_display=today_display(),
                edit_tx=context['edit_tx'],
                bank_accounts=bank_accounts,
                bank_account_names={account.id: account.name for account in bank_accounts},
                bank_account_currencies={account.id: account.currency for account in bank_accounts},
                tx_summary=tx_summary,
                plan_names=plan_names,
                active_tab=active_tab,
                **ui_options_fn(),
            )

        except Exception as e:
            logger.exception(f"Transactions list error: {e}")
            flash(i18n.gettext("ui_auto_366b8991796f"), 'error')
            empty_summary = {
                'total_count': 0,
                'paid_count': 0,
                'pending_count': 0,
                'plan_count': 0,
                'paid_income_total': to_decimal(0),
                'paid_expense_total': to_decimal(0),
                'paid_net_total': to_decimal(0),
                'pending_expense_total': to_decimal(0),
                'pending_income_total': to_decimal(0),
            }
            return render_template(
                'transactions.html',
                last_t=None,
                cats=[],
                today_display=today_display(),
                edit_tx=None,
                bank_accounts=[],
                bank_account_names={},
                bank_account_currencies={},
                tx_summary=empty_summary,
                plan_names={},
                active_tab='all',
                **ui_options_fn(),
            )

    @bp.route('/new_transaction', methods=['GET', 'POST'])
    def new_transaction():
        if request.method == 'POST':
            is_ajax = is_ajax_request()
            try:
                commands['create'].execute(transaction_form_from_request(request_payload_fn()))
                invalidate_financial_cache(g.get('tenant_id'))
                if is_ajax:
                    return jsonify({'success': True, 'message': i18n.gettext('tx_transactions_create_success')})
                flash(i18n.gettext("ui_auto_d55417356e97"), 'success')
                return redirect(url_for('dashboard.index'))
            except (ValueError, LedgerError) as e:
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': f'Kayıt başarısız: {str(e)}'})
                flash(i18n.gettext("ui_auto_b25d75a9757a", **{"str(e)": str(e)}), 'error')
            except IntegrityError as e:
                logger.warning("Duplicate transaction submission prevented: %s", e)
                rollback_session()
                duplicate_msg = 'Bu işlem zaten sisteme kaydedilmiş veya mükerrer gönderildi.'
                if is_ajax:
                    return jsonify({'success': False, 'message': duplicate_msg})
                flash(duplicate_msg, 'warning')
                return redirect(url_for('dashboard.index'))
            except Exception as e:
                logger.exception(f"New transaction error: {e}")
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': f'Kayıt sırasında beklenmeyen bir hata oluştu: {str(e)}'})
                flash(i18n.gettext("ui_auto_ea2754889d5c"), 'error')

            if is_ajax:
                return jsonify({'success': False, 'message': i18n.gettext('tx_transactions_error_generic')})
            return redirect(url_for('dashboard.index'))

        return redirect(url_for('dashboard.index'))

    @bp.route('/edit_t/<int:id>', methods=['POST'])
    def edit_t(id):
        is_ajax = is_ajax_request()
        try:
            commands['update'].execute(
                id,
                transaction_form_from_request(request_payload_fn())
            )
            invalidate_financial_cache(g.get('tenant_id'))
            response = handle_ajax_or_flash(True, i18n.gettext('tx_transactions_update_success'), i18n.gettext('tx_transactions_not_found'))
            if response:
                return response
        except (ValueError, LedgerError) as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f"{i18n.gettext('tx_transactions_error_generic')}: {str(e)}")
            if response:
                return response
        except Exception as e:
            logger.exception(f"Edit transaction error: {e}")
            rollback_session()
            response = handle_ajax_or_flash(False, None, i18n.gettext('tx_transactions_error_generic'))
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': i18n.gettext('tx_transactions_error_generic')})
        return redirect(url_for('dashboard.index'))

    @bp.route('/delete_t/<int:id>', methods=['POST'])
    def delete_t(id):
        try:
            result = commands['delete'].execute(id)
            if result.get('success'):
                invalidate_financial_cache(g.get('tenant_id'))
                if is_ajax_request() or request.is_json:
                    return jsonify({'success': True, 'message': result['message']})
                flash(result['message'], 'success')
            else:
                if is_ajax_request() or request.is_json:
                    return jsonify({'success': False, 'message': result['message']})
                flash(result['message'], 'error')
        except LedgerError as e:
            rollback_session()
            if is_ajax_request() or request.is_json:
                return jsonify({'success': False, 'message': str(e)})
            flash(str(e), 'error')
        except Exception as e:
            logger.exception(f"Delete transaction error: {e}")
            rollback_session()
            if is_ajax_request() or request.is_json:
                return jsonify({'success': False, 'message': i18n.gettext('tx_transactions_delete_error')})
            flash(i18n.gettext("ui_auto_746bef834771"), 'error')

        return redirect(request.referrer or url_for('dashboard.index'))

    @bp.route('/transactions/<int:id>/quick-pay', methods=['POST'])
    @bp.route('/transactions/<int:id>/quick_pay', methods=['POST'])
    def quick_pay(id):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Oturum gerekli.'}), 401
        tenant_id = g.get('tenant_id')
        try:
            repo = container.domains.repositories.financial()
            tx = repo.quick_pay_transaction(id, tenant_id=tenant_id)
            invalidate_financial_cache(tenant_id)
            from utils.audit import audit_log
            audit_log(
                'TRANSACTION_QUICK_PAID',
                user_id=session.get('user_id'),
                tenant_id=tenant_id,
                entity_type='transaction',
                entity_id=tx.id,
                details={'amount': str(tx.amount), 'status': tx.status},
            )
            if is_ajax_request() or request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'İşlem başarıyla ödendi olarak işaretlendi.',
                    'data': {
                        'id': tx.id,
                        'status': tx.status,
                        'date': tx.date,
                        'amount': str(tx.amount),
                    },
                })
            flash('İşlem başarıyla ödendi olarak işaretlendi.', 'success')
            return redirect(url_for('transactions.transactions'))
        except NotFound as e:
            if is_ajax_request() or request.is_json:
                return jsonify({'success': False, 'message': str(e)}), 404
            flash(str(e), 'error')
            return redirect(url_for('transactions.transactions'))
        except Exception as e:
            logger.exception(f"Quick pay error: {e}")
            rollback_session()
            if is_ajax_request() or request.is_json:
                return jsonify({'success': False, 'message': f'Ödeme işlemi sırasında hata oluştu: {str(e)}'}), 500
            flash(f'Ödeme işlemi sırasında hata oluştu: {str(e)}', 'error')
            return redirect(url_for('transactions.transactions'))

    @bp.route('/transactions/explorer', methods=['GET'])
    def transactions_explorer():
        """Transaction Explorer page - modern UI with filters and infinite scroll"""
        try:
            tenant_id = g.get('tenant_id')
            context = queries['get_transaction_page'].execute(page=1, edit_id=None, tenant_id=tenant_id)
            return render_template(
                'transactions_explorer.html',
                cats=context['cats'],
                **ui_options_fn(),
                today_display=today_display(),
                bank_accounts=list_bank_accounts(g.get('tenant_id')),
            )

        except Exception as e:
            logger.exception(f"Transaction Explorer error: {e}")
            flash(i18n.gettext("ui_auto_0f869e84191f"), 'error')
            return render_template(
                'transactions_explorer.html',
                cats=[],
                today_display=today_display(),
                bank_accounts=[],
                **ui_options_fn(),
            )
