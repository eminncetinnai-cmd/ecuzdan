"""Plan and payment calendar routes."""

import logging
from datetime import datetime

from flask import flash, g, jsonify, redirect, render_template, request, url_for

from bootstrap.container import get_container
from domain.tenant.accessor import get_tenant as get_tenant_id
from domain.transactions.services import LedgerError, delete_recurring_plan
from utils.ajax_helpers import is_ajax_request
from utils.db_session import rollback_session
from utils.decorators import login_required
from validators.request_validators import payment_form_from_request, plan_form_from_request

logger = logging.getLogger(__name__)


def _get_planning_app():
    from bootstrap.container import get_container
    return get_container().applications.planning()


def register_plan_routes(bp):
    planning_app = _get_planning_app()

    @bp.route('/plans', methods=['GET', 'POST'])
    def plans():
        if request.method == 'POST':
            is_ajax = is_ajax_request()
            try:
                message = planning_app.save_plan(plan_form_from_request(request.form))
                if is_ajax:
                    return jsonify({'success': True, 'message': message})
                flash(message, 'success')
            except (ValueError, LedgerError) as e:
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': f'Plan eklenirken hata: {str(e)}'})
                flash(f'Plan eklenirken hata: {str(e)}', 'error')
            except Exception as e:
                logger.exception(f"Add plan error: {e}")
                rollback_session()
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Plan eklenirken beklenmeyen bir hata oluştu.'})
                flash('Plan eklenirken beklenmeyen bir hata oluştu.', 'error')

            if is_ajax:
                return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
            return redirect(url_for('plans.plans'))

        try:
            return render_template('plans.html', **planning_app.plans_context(g.get('tenant_id')))
        except Exception as e:
            logger.exception(f"Plans page error: {e}")
            flash('Planlar yüklenirken hata oluştu.', 'error')
            return render_template(
                'plans.html',
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
            )

    @bp.route('/payment_calendar')
    @login_required
    def payment_calendar():
        try:
            return render_template('payment_calendar.html', **planning_app.payment_calendar_context())
        except Exception as e:
            logger.exception(f"Payment calendar error: {e}")
            flash('Ödeme takvimi yüklenirken hata oluştu.', 'error')
            now = datetime.now()
            return render_template(
                'payment_calendar.html',
                today_cash=0,
                week_p=[],
                month_p=[],
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
            from models import Transaction
            tenant_id = g.get('tenant_id')
            plan = planning_app.financial_repository.get_recurring_plan_for_tenant(id, tenant_id)
            if not plan:
                return jsonify({'success': False, 'message': 'Plan bulunamadı.'}), 404

            transactions = Transaction.query.filter_by(
                source_id=id, source_type='plan', tenant_id=tenant_id
            ).all()
            paid_count = sum(1 for t in transactions if t.status == 'Ödendi')
            pending_count = sum(1 for t in transactions if t.status == 'Bekliyor')

            return jsonify({
                'success': True,
                'has_paid': paid_count > 0,
                'paid_count': paid_count,
                'pending_count': pending_count
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
            from models import Transaction, db
            plan = planning_app.financial_repository.get_recurring_plan_for_tenant(id, tenant_id)
            if not plan:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Plan bulunamadı.'}), 404
                flash('Plan bulunamadı.', 'error')
                return redirect(url_for('plans.plans'))

            if mode == 'pending':
                # Yalnızca bu tenant'ın bekleyen işlemlerini sil
                Transaction.query.filter_by(
                    source_id=id, source_type='plan',
                    status='Bekliyor', tenant_id=tenant_id
                ).delete(synchronize_session=False)
                db.session.commit()
                message = 'Bekleyen kayıtlar başarıyla silindi.'
            else:
                # Tüm planı sil (repository zaten tenant-aware)
                result = delete_recurring_plan(id)
                message = result['message']

            if is_ajax:
                return jsonify({'success': True, 'message': message})
            flash(message, 'success')
        except Exception as e:
            logger.exception(f"Delete plan error: {e}")
            rollback_session()
            if is_ajax:
                return jsonify({'success': False, 'message': f'Plan silinirken hata: {str(e)}'}), 500
            flash(f'Plan silinirken hata: {str(e)}', 'error')

        if is_ajax:
            return jsonify({'success': False, 'message': 'Bilinmeyen bir hata oluştu.'})
        return redirect(url_for('plans.plans'))


    @bp.route('/add_payment', methods=['POST'])
    def add_payment():
        try:
            planning_app.add_payment(payment_form_from_request(request.form), g.get('tenant_id'))
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
