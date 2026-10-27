"""Repository for reporting and analytics queries."""

import time
from sqlalchemy import case, func, text

from models import Asset, PlanOccurrence, RecurringPlan, Transaction, db

from .base import BaseRepository
from .contracts import ReportingRepositoryContract

_synced_targets: dict[tuple, float] = {}


def clear_sync_targets(tenant_id=None):
    if tenant_id is None:
        _synced_targets.clear()
    else:
        for k in [k for k in _synced_targets if k[0] == tenant_id]:
            _synced_targets.pop(k, None)


class ReportingRepository(BaseRepository, ReportingRepositoryContract):
    def get_monthly_balance(self, year, month, tenant_id=None):
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-31"

        rows = (
            db.session.query(Transaction.type, func.sum(Transaction.amount))
            .filter(Transaction.date >= start, Transaction.date <= end, Transaction.is_deleted.is_(False))
            .filter(Transaction.tenant_id == tenant_id if tenant_id else text('1=1'))
            .group_by(Transaction.type)
            .all()
        )

        from decimal import Decimal
        totals = {row[0]: row[1] or Decimal('0.0') for row in rows}
        income = totals.get('Gelir', Decimal('0.0'))
        expense = totals.get('Gider', Decimal('0.0'))
        return income, expense

    def get_actual_cash(self, tenant_id=None):
        signed_amount = case(
            (Transaction.type == 'Gelir', Transaction.amount),
            else_=-Transaction.amount
        )
        query = db.session.query(func.sum(signed_amount)).filter(
            Transaction.status == 'Ödendi',
            Transaction.is_deleted.is_(False),
        )
        if tenant_id:
            query = query.filter(Transaction.tenant_id == tenant_id)

        from decimal import Decimal
        result = query.scalar()
        return result or Decimal('0.0')

    def get_total_assets(self, tenant_id=None):
        query = db.session.query(func.sum(Asset.value))
        if tenant_id:
            query = query.filter(Asset.tenant_id == tenant_id)

        from decimal import Decimal
        result = query.scalar()
        return result or Decimal('0.0')

    def get_total_debts(self, tenant_id=None):
        from decimal import Decimal

        from sqlalchemy import case

        debt_expr = case(
            (RecurringPlan.status.in_(['Tamamlandı', 'İptal', 'Durduruldu']), 0),
            (RecurringPlan.plan_type.in_(['Abonelik', 'Kira']), 0),
            (RecurringPlan.installments <= 0, 0),
            else_=RecurringPlan.amount * RecurringPlan.installments,
        )
        query = db.session.query(func.sum(debt_expr)).filter(RecurringPlan.flow_type == 'Gider')
        if tenant_id:
            query = query.filter(RecurringPlan.tenant_id == tenant_id)

        result = query.scalar()
        return result or Decimal('0.0')

    def get_transactions_by_date_range(self, start_date, end_date, tenant_id=None):
        query = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted.is_(False),
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()

    def _serialize_calendar_tx(self, t):
        from utils.format_utils import format_money

        amt = float(t.amount) if t.amount is not None else 0.0
        return {
            'id': t.id,
            'category': t.category,
            'description': t.description or '',
            'note': t.note or '',
            'type': t.type,
            'status': t.status,
            'amount': amt,
            'amount_fmt': format_money(t.amount),
            'origin': t.origin,
        }

    def _serialize_calendar_occ(self, occ, plan):
        from utils.format_utils import format_money

        t_type = "Gelir" if plan.flow_type == "Gelir" else ("Yatırım" if plan.plan_type == "DCA" else "Gider")
        amt = float(occ.amount or plan.amount or 0)
        return {
            'id': f"occ_{occ.id}",
            'category': plan.category,
            'description': f"{plan.name} ({occ.occurrence_number}. Taksit/Dönem)",
            'note': getattr(occ, 'notes', None) or '',
            'type': t_type,
            'status': 'Bekliyor',
            'amount': amt,
            'amount_fmt': format_money(amt),
            'origin': 'plan',
            'occurrence_id': occ.id,
        }

    def get_calendar_month_data(self, year, month, tenant_id=None):
        import calendar as cal_mod
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-{cal_mod.monthrange(year, month)[1]:02d}"
        query = Transaction.query.filter(
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.is_deleted.is_(False),
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        transactions = query.order_by(Transaction.date, Transaction.type).all()

        days = {}
        for t in transactions:
            day = days.setdefault(t.date, {
                'income': [], 'expense': [], 'investment': [],
                'income_total': 0, 'expense_total': 0, 'investment_total': 0,
            })
            item = self._serialize_calendar_tx(t)
            if t.type == 'Gelir':
                day['income'].append(item)
                day['income_total'] += float(t.amount)
            elif t.type == 'Gider':
                day['expense'].append(item)
                day['expense_total'] += float(t.amount)
            else:
                day['investment'].append(item)
                day['investment_total'] += float(t.amount)
            day['net'] = day['income_total'] - day['expense_total'] - day['investment_total']

        # Consolidate scheduled PlanOccurrences not yet represented in transactions
        from datetime import date
        target_month_end = date(year, month, cal_mod.monthrange(year, month)[1])
        if target_month_end >= date.today():
            now_ts = time.time()
            sync_key = (tenant_id, target_month_end)
            if sync_key not in _synced_targets or (now_ts - _synced_targets[sync_key] >= 300):
                from domain.planning.services.occurrence_service import OccurrenceLifecycleService
                lifecycle = OccurrenceLifecycleService()
                active_plans_query = RecurringPlan.query.filter_by(status='Aktif')
                if tenant_id:
                    active_plans_query = active_plans_query.filter_by(tenant_id=tenant_id)
                for p in active_plans_query.all():
                    lifecycle.sync_plan(p, tenant_id=tenant_id, until_date=target_month_end)
                _synced_targets[sync_key] = now_ts

        occ_query = PlanOccurrence.query.filter(
            PlanOccurrence.scheduled_date >= start,
            PlanOccurrence.scheduled_date <= end,
            PlanOccurrence.status == "scheduled",
            PlanOccurrence.transaction_id.is_(None),
        )
        if tenant_id:
            occ_query = occ_query.filter_by(tenant_id=tenant_id)
        occurrences = occ_query.all()

        if occurrences:
            existing_plan_keys = {
                (t.source_id, t.installment_number)
                for t in transactions
                if t.source_type == 'plan' and t.source_id and t.installment_number is not None
            }
            existing_plan_dates = {
                (t.source_id, str(t.date))
                for t in transactions
                if t.source_type == 'plan' and t.source_id and t.date
            }
            plan_ids = {occ.plan_id for occ in occurrences}
            plans_by_id = {
                p.id: p
                for p in RecurringPlan.query.filter(RecurringPlan.id.in_(plan_ids)).all()
            }
            for occ in occurrences:
                if (occ.plan_id, occ.occurrence_number) in existing_plan_keys:
                    continue
                if (occ.plan_id, str(occ.scheduled_date)) in existing_plan_dates:
                    continue
                plan = plans_by_id.get(occ.plan_id)
                if not plan or plan.status != 'Aktif':
                    continue
                item = self._serialize_calendar_occ(occ, plan)
                amt = float(item['amount'])
                day = days.setdefault(str(occ.scheduled_date), {
                    'income': [], 'expense': [], 'investment': [],
                    'income_total': 0, 'expense_total': 0, 'investment_total': 0,
                })
                if item['type'] == 'Gelir':
                    day['income'].append(item)
                    day['income_total'] += amt
                elif item['type'] == 'Gider':
                    day['expense'].append(item)
                    day['expense_total'] += amt
                else:
                    day['investment'].append(item)
                    day['investment_total'] += amt
                day['net'] = day['income_total'] - day['expense_total'] - day['investment_total']

        for d in days.values():
            if 'net' not in d:
                d['net'] = d['income_total'] - d['expense_total'] - d['investment_total']
        return days

    def get_pending_payments(self, start_date, end_date, tenant_id=None):
        query = Transaction.query.filter(
            Transaction.type.in_(['Gider', 'Yatırım']),
            Transaction.status == 'Bekliyor',
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted.is_(False),
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Transaction.date).all()
