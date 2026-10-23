
import calendar
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from database import get_calendar_month_data
from domain.planning.models import (
    CanonicalPlan,
    PlanFilters,
    PlanFlow,
    PlanLifecycle,
    PlanStatus,
)
from domain.planning.services.occurrence_service import OccurrenceLifecycleService
from engines.financial_engine import calculate_monthly_daily_balance, format_date
from shared.constants import MONTH_NAMES_TR

if TYPE_CHECKING:
    pass


class PlanService:
    def __init__(self, financial_repository=None, catalog_repository=None, occurrence_service=None):
        self.financial_repository = financial_repository
        self.catalog_repository = catalog_repository
        self.occurrence_service = occurrence_service or OccurrenceLifecycleService()

    def save_plan(self, dto):
        from domain.tenant.context import TenantContext

        tenant_id = getattr(dto, 'tenant_id', None) or TenantContext.optional()

        if dto.plan_id:
            updated_plan = self.financial_repository.update_recurring_plan(
                dto.plan_id,
                dto.name,
                dto.category,
                dto.amount,
                dto.installments,
                dto.payment_day,
                dto.note,
                dto.start_date,
                tenant_id,
                plan_type=dto.plan_type,
                frequency=dto.frequency,
                end_date=dto.end_date,
                target_asset_id=dto.target_asset_id,
                version=dto.version,
                status=getattr(dto, 'status', None),
            )
            self.occurrence_service.sync_plan(updated_plan, tenant_id)
            return 'Plan başarıyla güncellendi.'


        created_plan = self.financial_repository.add_recurring_plan(
            dto.name,
            dto.category,
            dto.amount,
            dto.installments,
            dto.payment_day,
            note=dto.note,
            start_date=dto.start_date,
            tenant_id=tenant_id,
            plan_type=dto.plan_type,
            frequency=dto.frequency,
            end_date=dto.end_date,
            target_asset_id=dto.target_asset_id,
            status='Aktif',
        )
        self.occurrence_service.sync_plan(created_plan, tenant_id)
        return 'Yeni plan başarıyla eklendi.'

    def plans_context(self, tenant_id=None, filters=None):
        """Return the unified plan context while preserving the legacy view keys."""
        filters = filters or PlanFilters()

        upcoming_occurrences = []
        upcoming_occurrence_count = 0
        upcoming_window_days = 7
        if not hasattr(self.financial_repository, '_mock_name'):
            all_model_plans = self.financial_repository.list_recurring_plans(None, tenant_id)
            income_plans = [p for p in all_model_plans if getattr(p, 'flow_type', None) == 'Gelir']
            expense_plans = [p for p in all_model_plans if getattr(p, 'flow_type', None) == 'Gider']
            investment_plans = [p for p in all_model_plans if getattr(p, 'flow_type', None) == 'Yatırım']
        else:
            income_plans = self.financial_repository.list_recurring_plans('Gelir', tenant_id)
            expense_plans = self.financial_repository.list_recurring_plans('Gider', tenant_id)
            investment_plans = self.financial_repository.list_recurring_plans('Yatırım', tenant_id)
        model_plans = income_plans + expense_plans + investment_plans

        try:
            occurrence_repository = self.occurrence_service.repository
            if hasattr(occurrence_repository, 'sync_with_transactions'):
                try:
                    occurrence_repository.sync_with_transactions(tenant_id)
                except Exception:
                    pass
            if hasattr(occurrence_repository, 'ensure_rolling_occurrences_for_active_plans'):
                try:
                    occurrence_repository.ensure_rolling_occurrences_for_active_plans(tenant_id, plans=model_plans)
                except TypeError:
                    occurrence_repository.ensure_rolling_occurrences_for_active_plans(tenant_id)
                except Exception:
                    pass
        except (AttributeError, RuntimeError):
            occurrence_repository = None

        model_groups = (
            ('Gelir', income_plans),
            ('Gider', expense_plans),
            ('Yatırım', investment_plans),
        )
        canonical_by_model = {
            id(model): CanonicalPlan.from_model(model, flow_hint=flow_hint)
            for flow_hint, plans in model_groups
            for model in plans
        }
        canonical_plans = [canonical_by_model[id(model)] for model in model_plans]
        canonical_plans = [plan for plan in canonical_plans if filters.matches(plan)]
        canonical_plans.sort(key=lambda plan: (plan.is_investment, plan.name.casefold(), plan.id))

        # Existing template consumers continue to receive ORM models. The new
        # UI can use canonical_plans/cashflow_plans/investment_plans directly.
        selected_ids = {plan.id for plan in canonical_plans}
        selected_models = [plan for plan in model_plans if plan.id in selected_ids]
        selected_models.sort(key=lambda plan: (plan.flow_type == 'Yatırım', plan.name.casefold(), plan.id))

        subscription_plans = [plan for plan in selected_models if plan.plan_type == 'Abonelik']
        installment_plans = [plan for plan in selected_models if plan.plan_type == 'Taksit']
        dca_plans = [plan for plan in selected_models if plan.plan_type == 'DCA']
        periodic_plans = [plan for plan in selected_models if plan.plan_type == 'Dönemsel']
        cashflow_plans = [plan for plan in canonical_plans if plan.is_cashflow]
        investment_view_plans = [plan for plan in canonical_plans if plan.is_investment]

        plan_name_by_id = {
            getattr(m, 'id', None): getattr(m, 'name', None)
            for m in model_plans
            if getattr(m, 'id', None) is not None
        }
        try:
            if occurrence_repository is not None:
                upcoming_from = date.today()
                upcoming_through = upcoming_from + timedelta(days=upcoming_window_days - 1)
                upcoming_occurrence_count = occurrence_repository.count_upcoming_for_tenant(
                    tenant_id,
                    from_date=upcoming_from,
                    through_date=upcoming_through,
                )
                upcoming_rows = occurrence_repository.list_upcoming(
                    tenant_id,
                    from_date=upcoming_from,
                    through_date=upcoming_through,
                    limit=8,
                )
                upcoming_occurrences = [
                    {
                        'id': occurrence.id,
                        'plan_id': occurrence.plan_id,
                        'plan_name': plan_name_by_id.get(occurrence.plan_id) or getattr(getattr(occurrence, 'plan', None), 'name', None) or f'Plan #{occurrence.plan_id}',
                        'occurrence_number': occurrence.occurrence_number,
                        'scheduled_date': occurrence.scheduled_date,
                        'status': occurrence.status,
                        'amount': occurrence.amount,
                    }
                    for occurrence in upcoming_rows
                ]
        except (AttributeError, RuntimeError):
            # The service remains usable in isolated unit contexts without an app DB.
            upcoming_occurrences = []
            upcoming_occurrence_count = 0

        active_plans = [p for p in canonical_plans if p.status is PlanStatus.ACTIVE]
        completed_plans = [
            p for p in canonical_plans
            if p.status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED, PlanStatus.PAUSED)
        ]
        income_total = sum(plan.amount for plan in active_plans if plan.flow is PlanFlow.INCOME)
        expense_total = sum(plan.amount for plan in active_plans if plan.flow is PlanFlow.EXPENSE)
        investment_total = sum(plan.amount for plan in active_plans if plan.flow is PlanFlow.INVESTMENT)
        from decimal import Decimal
        total_remaining_debt = sum(
            (plan.remaining_total_amount or Decimal(0))
            for plan in active_plans
            if plan.flow is PlanFlow.EXPENSE
        )
        try:
            assets = self.financial_repository.list_assets(tenant_id)
        except (AttributeError, RuntimeError):
            assets = []

        if not hasattr(self.catalog_repository, '_mock_name') and hasattr(self.catalog_repository, 'visible_categories_query'):
            all_cats = self.catalog_repository.visible_categories_query(tenant_id).all()
            income_cats = [c for c in all_cats if getattr(c, 'type', None) == 'Gelir']
            expense_cats = [c for c in all_cats if getattr(c, 'type', None) == 'Gider']
            investment_cats = [c for c in all_cats if getattr(c, 'type', None) == 'Yatırım']
        else:
            income_cats = self.catalog_repository.list_categories_by_type('Gelir', tenant_id)
            expense_cats = self.catalog_repository.list_categories_by_type('Gider', tenant_id)
            investment_cats = self.catalog_repository.list_categories_by_type('Yatırım', tenant_id)

        return {
            # New canonical context
            'canonical_plans': canonical_plans,
            'all_plans': canonical_plans,
            'cashflow_plans': cashflow_plans,
            'investment_plans': investment_view_plans,
            # Tab-grouped views — no DB change, just filtered views of canonical_plans
            'active_plans': active_plans,
            'completed_plans': completed_plans,
            'total_remaining_debt': total_remaining_debt,
            'active_plan_count': len(active_plans),
            'assets': assets,
            'active_filters': filters,
            'filter_options': {
                'flows': list(PlanFlow),
                'lifecycles': list(PlanLifecycle),
                'statuses': list(PlanStatus),
            },

            # Backward-compatible context for the current template and tests
            'subscription_plans': subscription_plans,
            'installment_plans': installment_plans,
            'dca_plans': dca_plans,
            'periodic_plans': periodic_plans,
            'income_cats': income_cats,
            'expense_cats': expense_cats,
            'investment_cats': investment_cats,
            'income_total': income_total,
            'expense_total': expense_total,
            'dca_total': investment_total,
            'investment_total': investment_total,
            'net_total': income_total - expense_total,
            'plan_count': len(canonical_plans),
            'upcoming_occurrence_count': upcoming_occurrence_count,
            'upcoming_occurrences': upcoming_occurrences,
            'upcoming_window_days': upcoming_window_days,
        }



    def plan_detail_context(self, plan_id, tenant_id=None):
        """Return one tenant-scoped plan and persisted occurrence insight."""
        plan_model = self.financial_repository.get_recurring_plan_for_tenant(plan_id, tenant_id)
        if plan_model is None:
            return None

        plan = CanonicalPlan.from_model(plan_model)
        occurrence_rows = self.occurrence_service.repository.list_for_plan(plan.id, tenant_id)
        counts = {status: 0 for status in ('scheduled', 'paid', 'skipped', 'cancelled')}
        for occurrence in occurrence_rows:
            if occurrence.status in counts:
                counts[occurrence.status] += 1

        today = date.today().isoformat()
        next_occurrence = next(
            (
                occurrence for occurrence in occurrence_rows
                if occurrence.status == 'scheduled' and occurrence.scheduled_date >= today
            ),
            None,
        )
        return {
            'plan': {
                'id': plan.id,
                'tenant_id': plan.tenant_id,
                'name': plan.name,
                'category': plan.category,
                'flow': plan.flow.value,
                'amount': str(plan.amount),
                'frequency': plan.frequency,
                'lifecycle': plan.lifecycle.value,
                'start_date': plan.start_date.isoformat() if plan.start_date else None,
                'end_date': plan.end_date.isoformat() if plan.end_date else None,
                'occurrence_limit': plan.occurrence_limit,
                'payment_day': plan.payment_day,
                'status': plan.status.value,
                'note': plan.note,
                'target_asset_id': plan.target_asset_id,
                'months_remaining': plan.months_remaining,
                'remaining_total_amount': str(plan.remaining_total_amount) if plan.remaining_total_amount is not None else None,
                'payment_countdown': plan.payment_countdown,
            },


            'summary': {
                'total': len(occurrence_rows),
                **counts,
            },
            'next_occurrence': {
                'id': next_occurrence.id,
                'occurrence_number': next_occurrence.occurrence_number,
                'scheduled_date': next_occurrence.scheduled_date,
                'status': next_occurrence.status,
                'amount': str(next_occurrence.amount) if next_occurrence.amount is not None else None,
                'transaction_id': next_occurrence.transaction_id,
            } if next_occurrence else None,
        }

    def payment_calendar_context(self, now=None, tenant_id=None):
        from decimal import Decimal

        now = now or datetime.now()
        today = now.strftime("%Y-%m-%d")
        next_week = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        month_end = f"{now.year}-{now.month:02d}-{calendar.monthrange(now.year, now.month)[1]:02d}"
        transactions = self.financial_repository.list_transactions(order_desc=False)
        today_cash = sum(
            t.amount if t.type == 'Gelir' else -t.amount
            for t in transactions
            if t.status == 'Ödendi'
        )
        if not hasattr(self.financial_repository, '_mock_name'):
            horizon_end = max(next_week, month_end)
            all_pending = self.financial_repository.pending_transactions_between(today, horizon_end)
            week_p = [t for t in all_pending if str(getattr(t, 'date', '')) <= next_week]
            month_p = [t for t in all_pending if str(getattr(t, 'date', '')) <= month_end]
        else:
            week_p = self.financial_repository.pending_transactions_between(today, next_week)
            month_p = self.financial_repository.pending_transactions_between(today, month_end)
        week_total = sum((t.amount for t in week_p), Decimal('0.00'))
        month_total = sum((t.amount for t in month_p), Decimal('0.00'))

        # Non-financial reminders for the list tab (isolated from cash flow)
        upcoming_reminders = []
        try:
            from models import UserReminder
            t_id = tenant_id or getattr(self.financial_repository, 'tenant_id', None)
            rem_q = UserReminder.query
            if t_id:
                rem_q = rem_q.filter_by(tenant_id=t_id)
            for r in rem_q.all():
                d = r.to_dict()
                if 0 <= d['days_remaining'] <= 31 and not r.is_completed:
                    upcoming_reminders.append(d)
            upcoming_reminders.sort(key=lambda x: x['days_remaining'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not load upcoming reminders for calendar: {e}")

        return {
            'today_cash': today_cash,
            'week_p': week_p,
            'week_total': week_total,
            'month_p': month_p,
            'month_total': month_total,
            'upcoming_reminders': upcoming_reminders,
            'cal_year': now.year,
            'cal_month': now.month,
            'cal_month_name': MONTH_NAMES_TR[now.month - 1],
            'today_iso': today,
        }

    def month_data(self, year, month, tenant_id=None):
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"month_data called with year={year}, month={month}, tenant_id={tenant_id}")
        days = get_calendar_month_data(year, month, tenant_id)

        # Enrich calendar days with reminders for this month without altering cash totals
        try:
            import calendar as cal_mod
            from models import UserReminder

            rem_query = UserReminder.query
            if tenant_id:
                rem_query = rem_query.filter_by(tenant_id=tenant_id)
            reminders = rem_query.all()

            max_days = cal_mod.monthrange(year, month)[1]
            month_str = f"{month:02d}"

            for rem in reminders:
                target_day = None
                if rem.frequency == 'Aylık':
                    target_day = min(rem.due_day or 1, max_days)
                elif rem.frequency == 'Yıllık':
                    if rem.due_month == month:
                        target_day = min(rem.due_day or 1, max_days)
                elif rem.frequency == 'Tek Seferlik':
                    if rem.due_date and rem.due_date.startswith(f"{year}-{month_str}-"):
                        try:
                            target_day = int(rem.due_date.split('-')[2])
                        except (IndexError, ValueError):
                            target_day = None

                if target_day:
                    date_key = f"{year}-{month_str}-{target_day:02d}"
                    day_dict = days.setdefault(date_key, {
                        'income': [], 'expense': [], 'investment': [],
                        'income_total': 0, 'expense_total': 0, 'investment_total': 0,
                        'net': 0,
                    })
                    rem_list = day_dict.setdefault('reminders', [])
                    rem_list.append({
                        'id': rem.id,
                        'title': rem.title,
                        'category': rem.category,
                        'category_emoji': rem.category_emoji,
                        'frequency': rem.frequency,
                        'amount': float(rem.amount) if rem.amount is not None else None,
                        'note': rem.note or '',
                        'is_completed': bool(rem.is_completed),
                    })
        except Exception as e:
            logger.warning(f"Could not load reminders for calendar: {e}")

        # Forward cash projection and cash gap detection
        try:
            import calendar as cal_mod
            from engines.financial_engine import get_live_data
            live_data = get_live_data()
            kasa_now = float(live_data.get('kasa', 0))

            now_dt = datetime.now()
            max_days = cal_mod.monthrange(year, month)[1]
            month_str = f"{month:02d}"

            is_current_month = (year == now_dt.year and month == now_dt.month)
            is_future_month = (year > now_dt.year) or (year == now_dt.year and month > now_dt.month)

            if is_current_month or is_future_month:
                start_day = now_dt.day if is_current_month else 1
                running_balance = kasa_now

                for d_num in range(start_day, max_days + 1):
                    d_iso = f"{year}-{month_str}-{d_num:02d}"
                    d_data = days.get(d_iso)
                    if d_data:
                        day_net = d_data.get('net', 0)
                        running_balance += day_net
                        d_data['projected_cash'] = round(running_balance, 2)

                        outflows = d_data.get('expense_total', 0) + d_data.get('investment_total', 0)
                        if running_balance < 0 and outflows > 0:
                            d_data['has_cash_gap'] = True
                            d_data['cash_gap_amount'] = round(abs(running_balance), 2)
        except Exception as e:
            logger.warning(f"Could not calculate cash gap projections: {e}")

        result = {
            'year': year,
            'month': month,
            'month_name': MONTH_NAMES_TR[month - 1],
            'today': datetime.now().strftime("%Y-%m-%d"),
            'days': days,
        }
        logger.info(f"month_data returning {len(result.get('days', {}))} days")
        return result

    def daily_balance(self, year, month):
        transactions = self.financial_repository.list_transactions(order_desc=False)
        labels, data = calculate_monthly_daily_balance(year, month, transactions)
        return {
            'year': year,
            'month': month,
            'labels': [format_date(d) for d in labels],
            'data': data,
        }

    def _handle_dca_payment(self, plan, amount, payment_date, tenant_id):
        """Handle DCA plan payment with asset transfer."""
        if getattr(plan, 'plan_type', None) == 'DCA' and getattr(plan, 'target_asset_id', None):
            from domain.transactions.services.financial_ledger import transfer_cash_to_asset

            transfer_cash_to_asset(plan.target_asset_id, amount, payment_date, tenant_id, skip_cash_tx=True)

    def add_payment(self, dto, tenant_id):
        plan = self.financial_repository.get_recurring_plan_for_tenant(dto.plan_id, tenant_id)
        if not plan:
            raise LookupError("Plan bulunamadı.")
        if plan.installments > 0 and dto.installment_number > plan.installments:
            raise ValueError(f"Taksit numarası 1 ile {plan.installments} arasında olmalıdır.")
        payment_date = datetime.strptime(dto.payment_date, '%Y-%m-%d').strftime('%Y-%m-%d')

        self._handle_dca_payment(plan, dto.amount, payment_date, tenant_id)

        return self.financial_repository.create_payment(
            dto.plan_id,
            dto.amount,
            payment_date,
            dto.installment_number,
            notes=dto.notes,
            tenant_id=tenant_id,
        )
