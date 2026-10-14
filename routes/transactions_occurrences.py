"""
Transaction Plan Occurrences Routes — routes/transactions_occurrences.py

Periyodik plan taksit/gerçekleşme (PlanOccurrence) yönetimi,
ödeme, atlama (skip) ve iptal (cancel) API endpoint'lerini yönetir.
"""

import logging

from flask import g, jsonify, request

from domain.transactions.services import LedgerError
from models import Transaction
from shared.db import db
from utils.capabilities import Capability
from utils.db_session import rollback_session

logger = logging.getLogger(__name__)


def register_transaction_occurrence_routes(
    bp,
    error_fn,
    require_capability_fn,
    json_body_fn,
    serialize_occurrence_fn,
    serialize_payment_fn,
    serialize_transaction_fn,
):
    """Register plan occurrence API routes on the transactions blueprint."""

    @bp.route('/api/plans/<int:plan_id>/occurrences', methods=['GET'])
    def api_plan_occurrences(plan_id):
        from domain.planning.services.occurrence_repository import OccurrenceRepository

        tenant_id = g.get('tenant_id')
        from repositories import RecurringPlanRepository
        plan = RecurringPlanRepository().get_recurring_plan_for_tenant(plan_id, tenant_id)
        if plan is None:
            return error_fn('Kayıt bulunamadı.', 'resource_not_found', 404)
        try:
            status = (request.args.get('status') or '').strip() or None
            occurrences = OccurrenceRepository().list_for_plan(plan_id, tenant_id, status=status)
            counts = {key: 0 for key in ('scheduled', 'paid', 'skipped', 'cancelled')}
            for occurrence in occurrences:
                counts[occurrence.status] += 1
            return jsonify({
                'success': True,
                'data': {
                    'plan_id': plan_id,
                    'items': [serialize_occurrence_fn(item) for item in occurrences],
                    'summary': {'total': len(occurrences), **counts},
                },
                'message': '',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except LedgerError as exc:
            return error_fn(str(exc), 'validation_error', 400)
        except Exception:
            logger.exception('Occurrence list API error')
            return error_fn('Occurrence listesi oluşturulamadı.', 'unexpected_error', 500)

    @bp.route('/api/occurrences/<int:occurrence_id>/pay', methods=['POST'])
    def api_pay_occurrence(occurrence_id):
        guard = require_capability_fn(Capability.OCCURRENCE_PAY)
        if guard:
            return guard
        from domain.transactions.services import mark_occurrence_paid

        tenant_id = g.get('tenant_id')
        body = json_body_fn()
        idempotency_key = (request.headers.get('Idempotency-Key') or '').strip()[:64]
        if not idempotency_key:
            return error_fn('Idempotency-Key zorunludur.', 'validation_error', 400)
        from domain.planning.services.occurrence_repository import OccurrenceRepository
        occurrence = OccurrenceRepository().get_for_tenant(occurrence_id, tenant_id)
        if occurrence is None:
            return error_fn('Kayıt bulunamadı.', 'resource_not_found', 404)
        try:
            payment = mark_occurrence_paid(
                occurrence_id,
                {
                    'amount': body.get('amount', occurrence.amount),
                    'payment_date': body.get('payment_date', occurrence.scheduled_date),
                    'notes': body.get('notes'),
                },
                tenant_id,
            )
            db.session.refresh(occurrence)
            transaction = db.session.get(Transaction, payment.transaction_id)
            return jsonify({
                'success': True,
                'data': {
                    'occurrence': serialize_occurrence_fn(occurrence),
                    'payment': serialize_payment_fn(payment),
                    'transaction': serialize_transaction_fn(transaction),
                    'audit_reference': request.headers.get('X-Request-ID', idempotency_key),
                },
                'message': 'Ödeme başarıyla kaydedildi.',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except LookupError as exc:
            rollback_session()
            return error_fn(str(exc), 'resource_not_found', 404)
        except (LedgerError, ValueError, ArithmeticError) as exc:
            rollback_session()
            return error_fn(str(exc), 'financial_invariant_violation', 422)
        except Exception:
            logger.exception('Occurrence payment API error')
            rollback_session()
            return error_fn('Occurrence ödemesi uygulanamadı.', 'unexpected_error', 500)

    @bp.route('/api/occurrences/<int:occurrence_id>/skip', methods=['POST'])
    def api_skip_occurrence(occurrence_id):
        guard = require_capability_fn(Capability.OCCURRENCE_SKIP)
        if guard:
            return guard
        from domain.planning.services.occurrence_repository import OccurrenceRepository

        tenant_id = g.get('tenant_id')
        body = json_body_fn()
        reason = str(body.get('reason') or '').strip()
        if not reason:
            return error_fn('Atlama nedeni zorunludur.', 'validation_error', 400)
        try:
            occurrence = OccurrenceRepository().mark_skipped(
                occurrence_id,
                tenant_id,
                reason=reason,
            )
            return jsonify({
                'success': True,
                'data': serialize_occurrence_fn(occurrence),
                'message': 'Occurrence atlandı.',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except LookupError as exc:
            rollback_session()
            return error_fn(str(exc), 'resource_not_found', 404)
        except (LedgerError, ValueError) as exc:
            rollback_session()
            return error_fn(str(exc), 'financial_invariant_violation', 422)
        except Exception:
            logger.exception('Occurrence skip API error')
            rollback_session()
            return error_fn('Occurrence atlanamadı.', 'unexpected_error', 500)

    @bp.route('/api/occurrences/<int:occurrence_id>/cancel', methods=['POST'])
    def api_cancel_occurrence(occurrence_id):
        guard = require_capability_fn(Capability.OCCURRENCE_SKIP)
        if guard:
            return guard
        from domain.planning.services.occurrence_repository import OccurrenceRepository

        tenant_id = g.get('tenant_id')
        body = json_body_fn()
        reason = str(body.get('reason') or '').strip() or 'Kullanıcı tarafından iptal edildi.'
        try:
            occurrence = OccurrenceRepository().mark_cancelled(
                occurrence_id,
                tenant_id,
                reason=reason,
            )
            return jsonify({
                'success': True,
                'data': serialize_occurrence_fn(occurrence),
                'message': 'Occurrence iptal edildi.',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except LookupError as exc:
            rollback_session()
            return error_fn(str(exc), 'resource_not_found', 404)
        except (LedgerError, ValueError) as exc:
            rollback_session()
            return error_fn(str(exc), 'financial_invariant_violation', 422)
        except Exception:
            logger.exception('Occurrence cancel API error')
            rollback_session()
            return error_fn('Occurrence iptal edilemedi.', 'unexpected_error', 500)
