"""Transaction routes."""

import json
import logging
from datetime import datetime

from flask import flash, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import and_, or_

from bootstrap import get_container
from engines.financial_engine import today_display
from models import Transaction
from shared.db import db
from utils.ajax_helpers import handle_ajax_or_flash, is_ajax_request
from utils.db_session import rollback_session
from validators.request_validators import transaction_form_from_request
from domain.transactions.services import LedgerError
from shared.decimal_precision import to_decimal
from decimal import Decimal

logger = logging.getLogger(__name__)

_container = get_container()
_outbox = _container.infrastructure.outbox()
_queries = _container.applications.transaction_queries()
_commands = _container.applications.transaction_commands(_outbox)



def register_transaction_routes(bp):
    @bp.route('/transactions', methods=['GET'])
    def transactions():
        try:
            page = request.args.get('page', 1, type=int)
            edit_id = request.args.get('edit', type=int)
            context = _queries['get_transaction_page'].execute(page=page, edit_id=edit_id)
            return render_template(
                'transactions.html',
                last_t=context['last_t'],
                cats=context['cats'],
                today_display=today_display(),
                edit_tx=context['edit_tx'],
            )
        except Exception as e:
            logger.exception(f"Transactions list error: {e}")
            flash('İşlem listesi yüklenirken hata oluştu.', 'error')
            return render_template(
                'transactions.html',
                last_t=None,
                cats=[],
                today_display=today_display(),
                edit_tx=None,
            )

    @bp.route('/new_transaction', methods=['GET', 'POST'])
    def new_transaction():
        if request.method == 'POST':
            is_ajax = is_ajax_request()
            try:
                _commands['create'].execute(transaction_form_from_request(request.form))
                if is_ajax:
                    return jsonify({'success': True, 'message': 'İşlem başarıyla eklendi!'})
                flash('İşlem başarıyla eklendi!', 'success')
                return redirect(url_for('dashboard.index'))
            except (ValueError, LedgerError) as e:
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': f'Kayıt başarısız: {str(e)}'})
                flash(f'Kayıt başarısız: {str(e)}', 'error')
            except Exception as e:
                logger.exception(f"New transaction error: {e}")
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': f'Kayıt sırasında beklenmeyen bir hata oluştu: {str(e)}'})
                flash('Kayıt sırasında beklenmeyen bir hata oluştu.', 'error')

            if is_ajax:
                return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
            return redirect(url_for('dashboard.index'))

        return redirect(url_for('dashboard.index'))

    @bp.route('/edit_t/<int:id>', methods=['POST'])
    def edit_t(id):
        is_ajax = is_ajax_request()
        try:
            _commands['update'].execute(
                id,
                transaction_form_from_request(request.form)
            )
            response = handle_ajax_or_flash(True, 'İşlem güncellendi!', 'İşlem bulunamadı.')
            if response:
                return response
        except (ValueError, LedgerError) as e:
            rollback_session()
            response = handle_ajax_or_flash(False, None, f'Güncelleme hatası: {str(e)}')
            if response:
                return response
        except Exception as e:
            logger.exception(f"Edit transaction error: {e}")
            rollback_session()
            response = handle_ajax_or_flash(False, None, 'Güncelleme sırasında beklenmeyen bir hata oluştu.')
            if response:
                return response

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('dashboard.index'))

    @bp.route('/delete_t/<int:id>')
    def delete_t(id):
        try:
            result = _commands['delete'].execute(id)
            if result.get('success'):
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({'success': True, 'message': result['message']})
                flash(result['message'], 'success')
            else:
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({'success': False, 'message': result['message']})
                flash(result['message'], 'error')
        except LedgerError as e:
            rollback_session()
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': str(e)})
            flash(str(e), 'error')
        except Exception as e:
            logger.exception(f"Delete transaction error: {e}")
            rollback_session()
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': 'Silme hatası: İşlem silinemedi.'})
            flash('Silme hatası: İşlem silinemedi.', 'error')

        return redirect(request.referrer or url_for('dashboard.index'))

    @bp.route('/transactions/explorer', methods=['GET'])
    def transactions_explorer():
        """Transaction Explorer page - modern UI with filters and infinite scroll"""
        try:
            context = _queries['get_transaction_page'].execute(page=1, edit_id=None)
            return render_template(
                'transactions_explorer.html',
                cats=context['cats'],
                today_display=today_display(),
            )
        except Exception as e:
            logger.exception(f"Transaction Explorer error: {e}")
            flash('İşlem gezgini yüklenirken hata oluştu.', 'error')
            return render_template(
                'transactions_explorer.html',
                cats=[],
                today_display=today_display(),
            )

    @bp.route('/api/transactions', methods=['GET'])
    def api_transactions():
        """API endpoint for Transaction Explorer - paginated transactions with filters"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 50
            filters_json = request.args.get('filters', '{}')
            
            try:
                filters = json.loads(filters_json)
            except json.JSONDecodeError:
                filters = {}
            
            # Build query with filters
            query = Transaction.query.filter_by(tenant_id=g.tenant_id if hasattr(g, 'tenant_id') else None)
            
            # Search filter
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Transaction.description.ilike(search_term),
                        Transaction.note.ilike(search_term),
                        Transaction.category.ilike(search_term)
                    )
                )
            
            # Date range filter
            if filters.get('dateFrom'):
                query = query.filter(Transaction.date >= filters['dateFrom'])
            if filters.get('dateTo'):
                query = query.filter(Transaction.date <= filters['dateTo'])
            
            # Type filter
            if filters.get('types'):
                query = query.filter(Transaction.type.in_(filters['types']))
            
            # Category filter
            if filters.get('category'):
                query = query.filter(Transaction.category == filters['category'])
            
            # Status filter
            if filters.get('statuses'):
                query = query.filter(Transaction.status.in_(filters['statuses']))
            
            # Amount range filter
            if filters.get('minAmount'):
                min_amount = to_decimal(str(filters['minAmount']))
                query = query.filter(Transaction.amount >= min_amount)
            if filters.get('maxAmount'):
                max_amount = to_decimal(str(filters['maxAmount']))
                query = query.filter(Transaction.amount <= max_amount)
            
            # Order by date descending
            query = query.order_by(Transaction.date.desc())
            
            # Get total count first (more efficient than counting after pagination)
            total_count = query.count()
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # Calculate summary from paginated items only for performance
            # For full summary, use a separate optimized query
            total_amount = sum((t.amount for t in pagination.items), to_decimal(0))
            total_income = sum((t.amount for t in pagination.items if t.type == 'Gelir'), to_decimal(0))
            total_expense = sum((t.amount for t in pagination.items if t.type == 'Gider'), to_decimal(0))
            
            transactions_data = []
            for tx in pagination.items:
                transactions_data.append({
                    'id': tx.id,
                    # Transaction.date String(10) 'YYYY-MM-DD' olarak saklanır (models.py:193);
                    # isoformat() burada AttributeError veriyordu.
                    'date': tx.date or None,
                    'category': tx.category,
                    'description': tx.description,
                    'note': tx.note,
                        'amount': str(tx.amount) if tx.amount is not None else '0',
                    'type': tx.type,
                    'status': tx.status
                })
            
            return jsonify({
                'transactions': transactions_data,
                'summary': {
                    'total_count': total_count,
                    'total_amount': str(total_amount),
                    'total_income': str(total_income),
                    'total_expense': str(total_expense)
                },
                'has_more': pagination.has_next
            })
            
        except Exception as e:
            logger.exception(f"API transactions error: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/transactions/<int:id>', methods=['GET'])
    def api_transaction_detail(id):
        """API endpoint for single transaction details"""
        try:
            transaction = Transaction.query.filter_by(id=id).first()
            
            if not transaction:
                return jsonify({'error': 'Transaction not found'}), 404
            
            return jsonify({
                'id': transaction.id,
                'date': transaction.date or None,
                'category': transaction.category,
                'description': transaction.description,
                'note': transaction.note,
                'amount': str(transaction.amount) if transaction.amount is not None else '0',
                'type': transaction.type,
                'status': transaction.status
            })
            
        except Exception as e:
            logger.exception(f"API transaction detail error: {e}")
            return jsonify({'error': str(e)}), 500

