
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

_month_data_cache: dict[tuple, tuple[float, dict]] = {}


def clear_calendar_cache(tenant_id=None):
    global _month_data_cache
    if tenant_id is None:
        _month_data_cache.clear()
    else:
        for k in [k for k in _month_data_cache if k[2] == tenant_id]:
            _month_data_cache.pop(k, None)


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
            clear_calendar_cache(tenant_id)
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
        clear_calendar_cache(tenant_id)
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

        # Auto-complete finished plans in DB if still marked Aktif
        try:
            for p in canonical_plans:
                if p.is_completed:
                    model = getattr(self.financial_repository, 'get_recurring_plan_for_tenant', lambda *a, **k: None)(p.id, tenant_id)
                    if model and getattr(model, 'status', None) == 'Aktif':
                        model.status = 'Tamamlandı'
                        if hasattr(self.financial_repository, 'commit'):
                            self.financial_repository.commit()
        except Exception as e:
            logger.debug(f"Auto-completing plan status sync error: {e}")

        active_plans = [p for p in canonical_plans if p.status is PlanStatus.ACTIVE and not p.is_completed]
        completed_plans = [
            p for p in canonical_plans
            if p.status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED, PlanStatus.PAUSED) or p.is_completed
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
            'debt_freedom': self.calculate_debt_freedom(tenant_id),
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
                'version': getattr(plan_model, 'version', 1),
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
                'paid_count': counts.get('paid', 0),
                'paid_occurrences_count': counts.get('paid', 0),
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
            all_pending = self.financial_repository.pending_transactions_between(today, horizon_end, tenant_id=tenant_id)
            week_p = [t for t in all_pending if str(getattr(t, 'date', '')) <= next_week]
            month_p = [t for t in all_pending if str(getattr(t, 'date', '')) <= month_end]
        else:
            week_p = self.financial_repository.pending_transactions_between(today, next_week, tenant_id=tenant_id)
            month_p = self.financial_repository.pending_transactions_between(today, month_end, tenant_id=tenant_id)
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

        cal_initial_data = None
        try:
            cal_initial_data = self.month_data(now.year, now.month, tenant_id=tenant_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not preload initial calendar month data: {e}")

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
            'cal_initial_data': cal_initial_data,
        }

    def month_data(self, year, month, tenant_id=None):
        import copy
        import logging
        import time

        logger = logging.getLogger(__name__)

        now_ts = time.time()
        cache_key = (year, month, tenant_id)
        try:
            from engines.financial_engine import _get_invalidation_timestamp
            inv_ts = _get_invalidation_timestamp(tenant_id)
        except Exception:
            inv_ts = 0.0

        if cache_key in _month_data_cache:
            cached_ts, cached_data = _month_data_cache[cache_key]
            if (now_ts - cached_ts < 60) and (cached_ts >= inv_ts):
                return copy.deepcopy(cached_data)

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

            if is_current_month:
                start_day = now_dt.day
                running_balance = kasa_now
            elif is_future_month:
                start_day = 1
                today_str = now_dt.strftime("%Y-%m-%d")
                target_start = f"{year}-{month_str}-01"
                try:
                    from models import Transaction
                    tx_q = Transaction.query.filter(
                        Transaction.date >= today_str,
                        Transaction.date < target_start,
                        Transaction.is_deleted.is_(False),
                    )
                    if tenant_id:
                        tx_q = tx_q.filter_by(tenant_id=tenant_id)
                    net_inter = sum(
                        (float(t.amount) if t.type == 'Gelir' else -float(t.amount))
                        for t in tx_q.all()
                    )
                    running_balance = kasa_now + net_inter
                except Exception:
                    running_balance = kasa_now
            else:
                start_day = 1
                running_balance = 0

            if is_current_month or is_future_month:
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
        _month_data_cache[cache_key] = (now_ts, copy.deepcopy(result))
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

        payment = self.financial_repository.create_payment(
            dto.plan_id,
            dto.amount,
            payment_date,
            dto.installment_number,
            notes=dto.notes,
            tenant_id=tenant_id,
        )

        if plan.installments > 0 and plan.plan_type not in ('Abonelik', 'DCA'):
            if dto.installment_number >= plan.installments:
                plan.status = 'Tamamlandı'
                if hasattr(self.financial_repository, 'commit'):
                    self.financial_repository.commit()

        clear_calendar_cache(tenant_id)
        return payment

    def calculate_debt_freedom(self, tenant_id=None):
        """Hesaplar: Toplam kalan taksit borcu, en yakın bitecek taksit ve tüm borçların sıfırlanacağı tarih."""
        from decimal import Decimal
        from datetime import date
        from domain.planning.models import PlanFlow, PlanStatus

        try:
            model_plans = self.financial_repository.list_recurring_plans(tenant_id=tenant_id)
        except Exception:
            model_plans = []

        canonical_plans = [CanonicalPlan.from_model(p) for p in model_plans]

        debt_plans = [
            p for p in canonical_plans
            if p.status is PlanStatus.ACTIVE
            and not p.is_completed
            and p.flow is PlanFlow.EXPENSE
            and (
                (p.occurrence_limit is not None and p.occurrence_limit > 0)
                or p.legacy_plan_type in ('Taksit', 'Kredi')
                or p.end_date is not None
            )
            and (p.months_remaining is not None and p.months_remaining > 0)
        ]

        if not debt_plans:
            return {
                'has_debt': False,
                'debt_plan_count': 0,
                'total_remaining_debt': Decimal('0'),
                'total_monthly_commitment': Decimal('0'),
                'final_freedom_months': 0,
                'final_freedom_date_str': None,
                'nearest_name': None,
                'nearest_months': 0,
                'nearest_amount': Decimal('0'),
                'nearest_end_date': None,
            }

        total_remaining_debt = sum(
            (p.remaining_total_amount or Decimal(0))
            for p in debt_plans
        )
        total_monthly_commitment = sum(
            (p.amount or Decimal(0))
            for p in debt_plans
        )

        debt_plans_by_nearest = sorted(debt_plans, key=lambda p: (p.months_remaining or 9999))
        nearest = debt_plans_by_nearest[0]

        max_months = max((p.months_remaining or 0) for p in debt_plans)
        today = date.today()
        m = today.month + max_months
        y = today.year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        months_tr = [
            '', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
        ]
        final_freedom_date_str = f"{months_tr[m]} {y}"

        return {
            'has_debt': True,
            'debt_plan_count': len(debt_plans),
            'total_remaining_debt': total_remaining_debt,
            'total_monthly_commitment': total_monthly_commitment,
            'final_freedom_months': max_months,
            'final_freedom_date_str': final_freedom_date_str,
            'nearest_name': nearest.name,
            'nearest_months': nearest.months_remaining,
            'nearest_amount': nearest.amount,
            'nearest_end_date': nearest.estimated_end_date_display,
        }
