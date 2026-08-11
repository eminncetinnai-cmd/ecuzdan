"""Dashboard application service."""

import calendar
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from engines.financial_engine import calculate_cash_trend
from utils.format_utils import format_date

if TYPE_CHECKING:
    pass


class _DecimalEncoder(json.JSONEncoder):
    """Decimal değerleri float olarak serialize eder."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def _dumps(obj):
    """Decimal-safe json.dumps kısayolu."""
    return json.dumps(obj, cls=_DecimalEncoder)


def _to_float(val):
    """Decimal ya da diğer sayısal türleri güvenli float'a çevirir."""
    try:
        return float(val) if val is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


class DashboardService:
    def __init__(self, financial_repository=None, catalog_repository=None):
        self.financial_repository = financial_repository
        self.catalog_repository = catalog_repository

    def index_context(self, tenant_id=None, now=None):
        now = now or datetime.now()
        today = now.strftime("%Y-%m-%d")
        year_start = f"{now.year}-01-01"
        year_end = f"{now.year}-12-31"
        transactions = self.financial_repository.list_transactions(tenant_id=tenant_id)
        
        # Phase 2: Transfer'leri nakit akışından hariç tut
        from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer
        cash_flow_transactions = [t for t in transactions if not CashFlowAnalyzer.is_transfer(t)]

        actual_cash = sum(
            t.amount if t.type == 'Gelir' else -t.amount
            for t in cash_flow_transactions
            if t.status == 'Ödendi' and t.date <= today
        )
        year_paid_cash = sum(
            t.amount if t.type == 'Gelir' else -t.amount
            for t in cash_flow_transactions
            if t.status == 'Ödendi' and year_start <= t.date <= today
        )
        pending_year_cash = sum(
            t.amount if t.type == 'Gelir' else -t.amount
            for t in cash_flow_transactions
            if t.status == 'Bekliyor' and today <= t.date <= year_end
        )
        paid_investment_transfers = sum(
            t.amount for t in cash_flow_transactions
            if t.type == 'Yatırım' and t.status == 'Ödendi' and year_start <= t.date <= today
        )
        pending_investment_transfers = sum(
            t.amount for t in cash_flow_transactions
            if t.type == 'Yatırım' and t.status == 'Bekliyor' and today <= t.date <= year_end
        )
        year_gross_income = sum(
            t.amount for t in cash_flow_transactions
            if t.type == 'Gelir' and t.status == 'Ödendi' and year_start <= t.date <= today
        )
        week_data = calculate_cash_trend(now, transactions, 7)
        month_days = calendar.monthrange(now.year, now.month)[1] - now.day + 1
        month_data = calculate_cash_trend(now, transactions, month_days)

        # --- FAZ 4: Net Servet & Varlık Dağılımı ---
        total_asset_value = Decimal('0')
        asset_type_breakdown = {}  # {'Hisse': 125000, 'Altın': 50000, ...}
        open_assets = []
        try:
            assets = self.financial_repository.list_assets(tenant_id=tenant_id)
            for asset in assets:
                if getattr(asset, 'is_closed', False):
                    continue
                val = Decimal(str(asset.value or 0))
                total_asset_value += val
                atype = asset.type or 'Diğer'
                asset_type_breakdown[atype] = asset_type_breakdown.get(atype, Decimal('0')) + val
                open_assets.append(asset)
        except Exception:
            pass

        # Net Servet = Nakit Pozisyon + Toplam Varlık Değeri
        net_worth = actual_cash + total_asset_value

        # Varlık tipi dağılımı JSON (pie chart için)
        asset_labels = list(asset_type_breakdown.keys())
        asset_values = [_to_float(v) for v in asset_type_breakdown.values()]

        # Nakit vs Yatırım dağılımı (stacked bar / donut için)
        cash_pct = 0.0
        investment_pct = 0.0
        if net_worth and net_worth > 0:
            cash_pct = round(_to_float(actual_cash) / _to_float(net_worth) * 100, 1)
            investment_pct = round(_to_float(total_asset_value) / _to_float(net_worth) * 100, 1)

        # Prepare category lists for quick transaction modal
        all_cats = self.catalog_repository.list_visible_categories(tenant_id)
        global_income_cats = [c.name for c in all_cats if c.type == 'Gelir']
        global_expense_cats = [c.name for c in all_cats if c.type == 'Gider']
        global_investment_cats = [c.name for c in all_cats if c.type == 'Yatırım']

        return {
            'today_cash': actual_cash,
            'year_paid_cash': year_paid_cash,
            'week_cash': week_data[-1],
            'month_cash': month_data[-1],
            'year_end_cash': actual_cash + pending_year_cash,
            'pending_year_cash': pending_year_cash,
            'paid_investment_transfers': paid_investment_transfers,
            'pending_investment_transfers': pending_investment_transfers,
            'investment_ratio': round((paid_investment_transfers / year_gross_income * 100), 2) if year_gross_income else 0,
            'last_t': transactions,
            'cats': all_cats,
            'global_income_cats': global_income_cats,
            'global_expense_cats': global_expense_cats,
            'global_investment_cats': global_investment_cats,
            'filter_categories': sorted({t.category for t in transactions}),
            'filter_origins': sorted({t.origin for t in transactions}),
            'filter_types': sorted({t.type for t in transactions}),
            'week_labels': _dumps([format_date((now + timedelta(days=i)).strftime("%Y-%m-%d")) for i in range(7)]),
            'month_labels': _dumps([format_date((now + timedelta(days=i)).strftime("%Y-%m-%d")) for i in range(month_days)]),
            'week_data': _dumps(week_data),
            'month_data': _dumps(month_data),
            # Faz 4 yeni değişkenler
            'net_worth': net_worth,
            'total_asset_value': total_asset_value,
            'asset_labels': _dumps(asset_labels),
            'asset_values': _dumps(asset_values),
            'cash_pct': cash_pct,
            'investment_pct': investment_pct,
            'open_asset_count': len(open_assets),
        }
