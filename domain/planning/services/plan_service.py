"""Plan and payment calendar service layer."""

import calendar
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from database import get_calendar_month_data
from domain.transactions.services.financial_ledger import create_recurring_plan, update_recurring_plan_entry
from engines.financial_engine import calculate_monthly_daily_balance, format_date
from shared.constants import MONTH_NAMES_TR


if TYPE_CHECKING:
    pass

class PlanService:
    def __init__(self, financial_repository=None, catalog_repository=None):
        self.financial_repository = financial_repository
        self.catalog_repository = catalog_repository

    def save_plan(self, dto):
        from flask import g
        tenant_id = g.get('tenant_id')
        
        # Action'a göre akış yönünü belirle
        flow_type = 'Gelir'
        if dto.action == 'add_expense_plan':
            flow_type = 'Gider'
        elif dto.action == 'add_investment_plan':
            flow_type = 'Yatırım'
            
        if dto.plan_id:
            self.financial_repository.update_recurring_plan(
                dto.plan_id,
                dto.name,
                dto.category,
                dto.amount,
                dto.installments,
                dto.payment_day,
                dto.note,
                dto.start_date,
                tenant_id, # update_recurring_plan might not need this if it filters by plan_id
                plan_type=dto.plan_type,
                frequency=dto.frequency,
                end_date=dto.end_date,
                target_asset_id=dto.target_asset_id
            )
            return 'Plan başarıyla güncellendi.'
            
        self.financial_repository.add_recurring_plan(
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
            status='Aktif'
        )
        return 'Yeni plan başarıyla eklendi.'

    def plans_context(self, tenant_id=None):
        # Tüm planları al
        income_plans = self.financial_repository.list_recurring_plans('Gelir', tenant_id)
        expense_plans = self.financial_repository.list_recurring_plans('Gider', tenant_id)
        investment_plans = self.financial_repository.list_recurring_plans('Yatırım', tenant_id)
        
        all_plans = income_plans + expense_plans + investment_plans
        
        subscription_plans = [p for p in all_plans if p.plan_type == 'Abonelik']
        installment_plans = [p for p in all_plans if p.plan_type == 'Taksit']
        dca_plans = [p for p in all_plans if p.plan_type == 'DCA']
        periodic_plans = [p for p in all_plans if p.plan_type == 'Dönemsel']

        income_total = sum(p.amount for p in income_plans)
        expense_total = sum(p.amount for p in expense_plans)
        dca_total = sum(p.amount for p in dca_plans) # DCA genelde gider/yatırım çıkışıdır
        
        return {
            'subscription_plans': subscription_plans,
            'installment_plans': installment_plans,
            'dca_plans': dca_plans,
            'periodic_plans': periodic_plans,
            
            # Geriye dönük uyumluluk ve modal select'leri için
            'income_cats': self.catalog_repository.list_categories_by_type('Gelir', tenant_id),
            'expense_cats': self.catalog_repository.list_categories_by_type('Gider', tenant_id),
            'investment_cats': self.catalog_repository.list_categories_by_type('Yatırım', tenant_id),
            
            'income_total': income_total,
            'expense_total': expense_total,
            'dca_total': dca_total,
            'net_total': income_total - expense_total,
            'plan_count': len(all_plans),
        }

    def payment_calendar_context(self, now=None):
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
        return {
            'today_cash': today_cash,
            'week_p': self.financial_repository.pending_transactions_between(today, next_week),
            'month_p': self.financial_repository.pending_transactions_between(today, month_end),
            'cal_year': now.year,
            'cal_month': now.month,
            'cal_month_name': MONTH_NAMES_TR[now.month - 1],
            'today_iso': today,
        }

    def month_data(self, year, month, tenant_id=None):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"month_data called with year={year}, month={month}, tenant_id={tenant_id}")
        result = {
            'year': year,
            'month': month,
            'month_name': MONTH_NAMES_TR[month - 1],
            'today': datetime.now().strftime("%Y-%m-%d"),
            'days': get_calendar_month_data(year, month, tenant_id),
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
        """
        Handle DCA plan payment with asset transfer.
        
        Args:
            plan: Recurring plan instance
            amount: Payment amount
            payment_date: Payment date string (YYYY-MM-DD)
            tenant_id: Tenant ID
        """
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
        
        # Handle DCA plan payment with asset transfer
        self._handle_dca_payment(plan, dto.amount, payment_date, tenant_id)
        
        return self.financial_repository.create_payment(
            dto.plan_id,
            dto.amount,
            payment_date,
            dto.installment_number,
            notes=dto.notes,
            tenant_id=tenant_id,
        )

