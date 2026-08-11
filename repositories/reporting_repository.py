"""Repository for reporting and analytics queries."""

from sqlalchemy import case, func, text

from models import Asset, RecurringPlan, Transaction, db

from .base import BaseRepository
from .contracts import ReportingRepositoryContract


class ReportingRepository(BaseRepository, ReportingRepositoryContract):
    def get_monthly_balance(self, year, month, tenant_id=None):
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-31"

        rows = (
            db.session.query(Transaction.type, func.sum(Transaction.amount))
            .filter(Transaction.date >= start, Transaction.date <= end)
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
            Transaction.status == 'Ödendi'
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
        query = db.session.query(
            func.sum(RecurringPlan.amount * RecurringPlan.installments)
        ).filter(RecurringPlan.flow_type == 'Gider')
        if tenant_id:
            query = query.filter(RecurringPlan.tenant_id == tenant_id)

        from decimal import Decimal
        result = query.scalar()
        return result or Decimal('0.0')

    def get_transactions_by_date_range(self, start_date, end_date, tenant_id=None):
        query = Transaction.query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()

    def _serialize_calendar_tx(self, t):
        from utils.format_utils import format_money

        return {
            'id': t.id,
            'category': t.category,
            'description': t.description or '',
            'note': t.note or '',
            'type': t.type,
            'status': t.status,
            'amount': t.amount,
            'amount_fmt': format_money(t.amount),
            'origin': t.origin,
        }

    def get_calendar_month_data(self, year, month, tenant_id=None):
        import calendar as cal_mod
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-{cal_mod.monthrange(year, month)[1]:02d}"
        query = Transaction.query.filter(
            Transaction.date >= start,
            Transaction.date <= end
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
        for d in days.values():
            if 'net' not in d:
                d['net'] = d['income_total'] - d['expense_total'] - d['investment_total']
        return days

    def get_pending_payments(self, start_date, end_date, tenant_id=None):
        query = Transaction.query.filter(
            Transaction.type.in_(['Gider', 'Yatırım']),
            Transaction.status == 'Bekliyor',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Transaction.date).all()
