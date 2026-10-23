"""Plan and payment calendar routes."""

import logging
from datetime import datetime

from flask import flash, g, jsonify, redirect, render_template, request, url_for

from domain.planning.models import PlanFilters, PlanFlow, PlanLifecycle, PlanStatus
from domain.tenant.accessor import get_tenant as get_tenant_id
from domain.transactions.services import LedgerError, delete_recurring_plan
from engines.financial_engine import invalidate_financial_cache
from infrastructure.i18n import i18n
from shared.currency_precision import get_currency_symbol
from utils.ajax_helpers import is_ajax_request
from utils.db_session import rollback_session
from utils.decorators import login_required
from validators.request_validators import payment_form_from_request, plan_form_from_request

logger = logging.getLogger(__name__)


def _get_planning_app():
    from bootstrap.container import get_container
    return get_container().domain.plan()


def _plan_request_payload():
    payload = request.form.copy()
    if_match = (request.headers.get("If-Match") or "").strip().strip(chr(34))
    if if_match.isdigit():
        payload["version"] = if_match
    return payload


def _plan_ui_options():
    return {
        'flow_label_keys': {
            PlanFlow.INCOME.value: 'plans_flow_income',
            PlanFlow.EXPENSE.value: 'plans_flow_expense',
            PlanFlow.INVESTMENT.value: 'plans_flow_investment',
        },
        'lifecycle_label_keys': {
            PlanLifecycle.INDEFINITE.value: 'plans_lifecycle_indefinite',
            PlanLifecycle.INSTALLMENT.value: 'plans_lifecycle_installment',
            PlanLifecycle.END_DATED.value: 'plans_lifecycle_end_dated',
        },
        'status_label_keys': {
            PlanStatus.ACTIVE.value: 'plans_status_active',
            PlanStatus.PAUSED.value: 'plans_status_paused',
            PlanStatus.COMPLETED.value: 'plans_status_completed',
            PlanStatus.CANCELLED.value: 'plans_status_cancelled',
        },
        'plan_type_label_keys': {
            'Taksit': 'plans_type_installment',
            'Abonelik': 'plans_type_subscription',
            'DCA': 'plans_type_dca',
            'Dönemsel': 'plans_type_periodic',
        },
        'frequency_label_keys': {
            'Aylık': 'plans_frequency_monthly',
            '3-Aylık': 'plans_frequency_quarterly',
            'Yıllık': 'plans_frequency_yearly',
            'Haftalık': 'plans_frequency_weekly',
        },
    }


def _plan_currency_context():
    user = getattr(g, 'current_user', None)
    tenant = getattr(user, 'tenant', None)
    code = (getattr(user, 'base_currency', None) or getattr(tenant, 'base_currency', None) or 'TRY').upper()
    return {
        'plan_currency_code': code,
        'plan_currency_symbol': get_currency_symbol(code) or code,
    }


def _plan_filters_from_request():

    """Parse unified Plans filters while ignoring unsupported query values."""
    def _enum_value(enum_type, key):
        value = (request.args.get(key) or '').strip()
        try:
            return enum_type(value) if value else None
        except ValueError:
            return None

    return PlanFilters(
        flow=_enum_value(PlanFlow, 'flow'),
        lifecycle=_enum_value(PlanLifecycle, 'lifecycle'),
        status=_enum_value(PlanStatus, 'status'),
        search=(request.args.get('q') or '').strip()[:100],
        investment_only=request.args.get('investment') == '1',
    )

def register_plan_routes(bp):
    planning_app = _get_planning_app()

    @bp.route('/plans', methods=['GET', 'POST'])
    @login_required
    def plans():
        if request.method == 'POST':
            is_ajax = is_ajax_request()
            try:
                message = planning_app.save_plan(plan_form_from_request(_plan_request_payload()))
                invalidate_financial_cache(g.get('tenant_id'))
                if is_ajax:
                    return jsonify({'success': True, 'message': message})
                flash(message, 'success')
            except (ValueError, LedgerError) as e:
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': f'Plan eklenirken hata: {str(e)}'})
                flash(i18n.gettext("ui_auto_610949cf8c74", **{"str(e)": str(e)}), 'error')
            except Exception as e:
                logger.exception(f"Add plan error: {e}")
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Plan eklenirken beklenmeyen bir hata oluştu.'})
                flash(i18n.gettext("ui_auto_c7319ad0996e"), 'error')

            if is_ajax:
                return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
            return redirect(url_for('plans.plans'))

        try:
            filters = _plan_filters_from_request()
            context = planning_app.plans_context(g.get('tenant_id'), filters=filters)
            context.update(_plan_ui_options())
            context.update(_plan_currency_context())
            return render_template('plans.html', **context)

        except Exception as e:

            logger.exception(f"Plans page error: {e}")
            flash(i18n.gettext("ui_auto_55e6ceb618f5"), 'error')
            return render_template(
                'plans.html',
                canonical_plans=[],
                all_plans=[],
                active_plans=[],
                completed_plans=[],
                cashflow_plans=[],
                investment_plans=[],
                assets=[],
                active_filters=PlanFilters(),
                filter_options={
                    'flows': list(PlanFlow),
                    'lifecycles': list(PlanLifecycle),
                    'statuses': list(PlanStatus),
                },
                subscription_plans=[],

                installment_plans=[],
                dca_plans=[],
                periodic_plans=[],

                income_cats=[],
                expense_cats=[],
                investment_cats=[],
                plan_count=0,
                income_total=0,
                expense_total=0,
                net_total=0,
                upcoming_occurrence_count=0,
                upcoming_occurrences=[],
                upcoming_window_days=7,
                **_plan_ui_options(),
                **_plan_currency_context(),
            )

    @bp.route('/api/plans/<int:plan_id>', methods=['GET'])
    @login_required
    def api_plan_detail(plan_id):
        """Return a tenant-scoped, read-only plan insight payload."""
        try:
            detail = planning_app.plan_detail_context(plan_id, g.get('tenant_id'))
            if detail is None:
                return jsonify({
                    'success': False,
                    'error_code': 'resource_not_found',
                    'message': i18n.gettext('plans_detail_not_found'),
                    'request_id': request.headers.get('X-Request-ID', ''),
                }), 404
            return jsonify({
                'success': True,
                'data': detail,
                'message': '',
                'request_id': request.headers.get('X-Request-ID', ''),
            })
        except Exception:
            logger.exception('Plan detail API error')
            return jsonify({
                'success': False,
                'error_code': 'unexpected_error',
                'message': i18n.gettext('plans_detail_error'),
                'request_id': request.headers.get('X-Request-ID', ''),
            }), 500

    @bp.route('/payment_calendar')
    @login_required
    def payment_calendar():

        try:
            tenant_id = get_tenant_id()
            return render_template('payment_calendar.html', **planning_app.payment_calendar_context(tenant_id=tenant_id))
        except Exception as e:
            logger.exception(f"Payment calendar error: {e}")
            flash(i18n.gettext("ui_auto_32d6da6a1dd7"), 'error')
            now = datetime.now()
            return render_template(
                'payment_calendar.html',
                today_cash=0,
                week_p=[],
                month_p=[],
                upcoming_reminders=[],
                cal_year=now.year,
                cal_month=now.month,
            )

    @bp.route('/payment_calendar/month_data')
    def payment_calendar_month_data():
        try:
            year = int(request.args.get('year', datetime.now().year))
            month = int(request.args.get('month', datetime.now().month))
            if month < 1 or month > 12:
                raise ValueError()
        except (TypeError, ValueError):
            return {'error': 'Geçersiz ay veya yıl'}, 400

        try:
            tenant_id = get_tenant_id()
            logger.info(f"Month data request: year={year}, month={month}, tenant_id={tenant_id}")
            result = planning_app.month_data(year, month, tenant_id)
            logger.info(f"Month data result: {len(result.get('days', {}))} days")
            return result
        except Exception as e:
            logger.exception(f"Month data error: {e}")
            return {'error': 'Veri yüklenirken hata oluştu'}, 500

    @bp.route('/payment_calendar/daily_balance')
    def payment_calendar_daily_balance():
        try:
            year = int(request.args.get('year', datetime.now().year))
            month = int(request.args.get('month', datetime.now().month))
            if month < 1 or month > 12:
                raise ValueError()
        except (TypeError, ValueError):
            return {'error': 'Geçersiz ay veya yıl'}, 400

        try:
            return planning_app.daily_balance(year, month)
        except Exception as e:
            logger.exception(f"Daily balance error: {e}")
            return {'error': 'Veri yüklenirken hata oluştu'}, 500

    @bp.route('/<int:id>/check-delete')
    def check_delete(id):
        try:
            tenant_id = g.get('tenant_id')
            plan = planning_app.financial_repository.get_recurring_plan_for_tenant(id, tenant_id)
            if not plan:
                return jsonify({'success': False, 'message': 'Plan bulunamadı.'}), 404

            counts = planning_app.financial_repository.get_plan_transaction_counts(id, tenant_id)

            return jsonify({
                'success': True,
                'has_paid': counts['has_paid'],
                'paid_count': counts['paid_count'],
                'pending_count': counts['pending_count']
            })
        except Exception as e:
            logger.exception(f"Check delete error: {e}")
            return jsonify({'success': False, 'message': 'Kontrol sırasında hata oluştu.'}), 500

    @bp.route('/<int:id>/delete', methods=['POST'])
    def delete_plan(id):
        is_ajax = is_ajax_request()
        mode = request.form.get('mode', 'all')
        tenant_id = g.get('tenant_id')

        try:
            plan = planning_app.financial_repository.get_recurring_plan_for_tenant(id, tenant_id)
            if not plan:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Plan bulunamadı.'}), 404
                flash(i18n.gettext("ui_auto_39643aaf8d10"), 'error')
                return redirect(url_for('plans.plans'))

            if mode == 'pending':
                # Yalnızca bu tenant'ın bekleyen işlemlerini sil
                planning_app.financial_repository.delete_plan_pending_transactions(id, tenant_id)
                invalidate_financial_cache(tenant_id)
                message = 'Bekleyen kayıtlar başarıyla silindi.'
            else:
                # Tüm planı sil (repository zaten tenant-aware)
                result = delete_recurring_plan(id, tenant_id=tenant_id)
                invalidate_financial_cache(tenant_id)
                message = result['message']

            if is_ajax:
                return jsonify({'success': True, 'message': message})
            flash(message, 'success')
        except Exception as e:
            logger.exception(f"Delete plan error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': f'Plan silinirken hata: {str(e)}'}), 500
            flash(i18n.gettext("ui_auto_1325c38c045e", **{"str(e)": str(e)}), 'error')

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('plans.plans'))


    @bp.route('/plans/<int:id>/status', methods=['POST'])
    @bp.route('/<int:id>/status', methods=['POST'])
    @login_required
    def set_plan_status(id):
        tenant_id = g.get('tenant_id')
        req_json = request.get_json(silent=True) if request.is_json else {}
        status = (request.form.get('status') or (req_json.get('status') if isinstance(req_json, dict) else None) or '').strip()
        if status not in {'Aktif', 'Duraklatıldı', 'Tamamlandı', 'İptal'}:
            return jsonify({'success': False, 'message': 'Geçersiz plan durumu.'}), 400

        try:
            plan = planning_app.financial_repository.get_recurring_plan_for_tenant(id, tenant_id)
            if not plan:
                return jsonify({'success': False, 'message': 'Plan bulunamadı.'}), 404

            updated_plan = planning_app.financial_repository.update_recurring_plan(
                plan_id=id,
                name=plan.name,
                category=plan.category,
                amount=plan.amount,
                installments=plan.installments,
                payment_day=plan.payment_day,
                note=plan.note,
                start_date=plan.start_date.isoformat() if hasattr(plan.start_date, 'isoformat') else (str(plan.start_date) if plan.start_date else None),
                tenant_id=tenant_id,
                plan_type=plan.plan_type,
                frequency=plan.frequency,
                end_date=plan.end_date.isoformat() if hasattr(plan.end_date, 'isoformat') else (str(plan.end_date) if plan.end_date else None),
                target_asset_id=plan.target_asset_id,
                status=status,
            )
            planning_app.occurrence_service.sync_plan(updated_plan, tenant_id)
            invalidate_financial_cache(tenant_id)

            status_messages = {
                'İptal': 'Plan başarıyla iptal edildi.',
                'Duraklatıldı': 'Plan duraklatıldı.',
                'Tamamlandı': 'Plan tamamlandı olarak işaretlendi.',
                'Aktif': 'Plan başarıyla aktife alındı.',
            }
            message = status_messages.get(status, 'Plan durumu güncellendi.')
            return jsonify({'success': True, 'message': message, 'status': status})
        except Exception as e:
            logger.exception(f'Set plan status error: {e}')
            rollback_session()
            return jsonify({'success': False, 'message': f'Durum güncellenirken hata: {str(e)}'}), 500

    @bp.route('/add_payment', methods=['POST'])
    def add_payment():
        try:
            planning_app.add_payment(payment_form_from_request(request.form), g.get('tenant_id'))
            invalidate_financial_cache(g.get('tenant_id'))
            return jsonify({'success': True, 'message': 'Ödeme başarıyla kaydedildi.'})
        except LookupError as e:
            rollback_session()
            return jsonify({'success': False, 'message': str(e)}), 404
        except ValueError as e:
            logger.exception(f"Add payment validation error: {e}")
            rollback_session()
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.exception(f"Add payment error: {e}")
            rollback_session()
            return jsonify({'success': False, 'message': f'Ödeme kaydedilirken hata: {str(e)}'}), 500
