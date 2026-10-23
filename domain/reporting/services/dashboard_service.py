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

        # --- Borçsuzluk Günü & Taksit Takibi ---
        debt_freedom = {'has_debt': False}
        try:
            if hasattr(self.financial_repository, 'list_recurring_plans'):
                from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanStatus
                model_plans = self.financial_repository.list_recurring_plans(tenant_id=tenant_id)
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
                if debt_plans:
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
                    m = now.month + max_months
                    y = now.year + (m - 1) // 12
                    m = (m - 1) % 12 + 1
                    months_tr = [
                        '', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                        'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
                    ]
                    final_freedom_date_str = f"{months_tr[m]} {y}"
                    debt_freedom = {
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
        except Exception:
            pass

        # --- FAZ 5: Smart Feed & Actionable Insights ---
        smart_insights = []

        if debt_freedom.get('has_debt'):
            smart_insights.append({
                'type': 'success',
                'title': f'🎯 Borçsuzluk Yolculuğu: {debt_freedom["final_freedom_months"]} Ay Kaldı',
                'description': f'Tüm taksitleriniz {debt_freedom["final_freedom_date_str"]} tarihinde sıfırlanıyor! İlk rahatlama: {debt_freedom["nearest_name"]} ({debt_freedom["nearest_months"]} ay sonra, bütçenize +{debt_freedom["nearest_amount"]:,.2f} TL/ay kalacak).',
                'action_label': 'Planları İncele',
                'action_url': '/plans',
                'icon': 'award',
            })

        # 1. Yaklaşan Ödemeler (Önümüzdeki 7 gün içindeki bekleyen giderler)
        in_7_days = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        upcoming_expenses = [
            t for t in cash_flow_transactions
            if t.type == 'Gider' and t.status == 'Bekliyor' and today <= t.date <= in_7_days
        ]
        if upcoming_expenses:
            upcoming_total = sum(t.amount for t in upcoming_expenses)
            smart_insights.append({
                'type': 'warning',
                'title': f'Önümüzdeki 7 Günde {len(upcoming_expenses)} Ödeme Var',
                'description': f'Toplam {upcoming_total:,.2f} TL tutarında yaklaşan gideriniz bulunuyor. Nakit akışınızı kontrol edin.',
                'action_label': 'Ödeme Takvimine Git',
                'action_url': '/payment_calendar',
                'icon': 'calendar',
            })

        # 2. Ay Sonu Nakit Delta Uyarısı veya Pozitif Bildirim
        net_monthly_delta = month_data[-1] - actual_cash
        if net_monthly_delta < 0:
            smart_insights.append({
                'type': 'danger',
                'title': 'Ay Sonu Nakit Çıkışı Bekleniyor',
                'description': f'Bu ay sonuna kadar net nakdiniz {abs(net_monthly_delta):,.2f} TL azalma eğiliminde. Harcamalarınızı gözden geçirin.',
                'action_label': 'Aylık Analize Git',
                'action_url': '/monthly_dashboard',
                'icon': 'alert-circle',
            })
        elif net_monthly_delta > 0:
            smart_insights.append({
                'type': 'success',
                'title': 'Pozitif Ay Sonu Nakit Projeksiyonu',
                'description': f'Bu ay beklenen tahsilatlarla net nakdiniz {net_monthly_delta:,.2f} TL artacak görünüyor.',
                'action_label': 'Nakit Akışını Gör',
                'action_url': '/monthly_dashboard',
                'icon': 'trending-up',
            })

        # 3. Varlık Portföyü Durumu
        if not open_assets:
            smart_insights.append({
                'type': 'info',
                'title': 'Portföyünüzü Büyütün',
                'description': 'Henüz kayıtlı bir yatırım varlığınız bulunmuyor. Birikimlerinizi takip etmek için varlık ekleyin.',
                'action_label': 'Varlık Ekle',
                'action_url': '/assets?modal=new',
                'icon': 'briefcase',
            })
        elif cash_pct > 70:
            smart_insights.append({
                'type': 'info',
                'title': 'Yüksek Nakit Oranı (%' + f'{cash_pct:.0f})',
                'description': 'Varlıklarınızın büyük kısmı nakitte duruyor. Enflasyona karşı yatırım sepetinizi değerlendirebilirsiniz.',
                'action_label': 'Portföyü İncele',
                'action_url': '/assets',
                'icon': 'pie-chart',
            })

        # 4. Kategori Bütçe Limit Kontrolleri (bu ayki harcamalar)
        cur_month_start = f"{now.year}-{now.month:02d}-01"
        monthly_expenses = [
            t for t in cash_flow_transactions
            if t.type == 'Gider' and cur_month_start <= t.date <= today
        ]
        cat_expense_sums = {}
        for t in monthly_expenses:
            cat_expense_sums[t.category] = cat_expense_sums.get(t.category, Decimal('0')) + t.amount

        for cat in all_cats:
            limit = getattr(cat, 'monthly_budget_limit', None)
            if limit and Decimal(str(limit)) > 0:
                limit_dec = Decimal(str(limit))
                spent = cat_expense_sums.get(cat.name, Decimal('0'))
                ratio = (spent / limit_dec) * 100
                if ratio >= 100:
                    smart_insights.append({
                        'type': 'danger',
                        'title': f'{cat.name} Bütçe Limiti Aşıldı',
                        'description': f'Aylık limit ({limit_dec:,.2f} TL) aşıldı! Harcanan: {spent:,.2f} TL (%{ratio:.0f}).',
                        'action_label': 'Kategorileri Düzenle',
                        'action_url': '/categories',
                        'icon': 'alert-triangle',
                    })
                    break
                elif ratio >= 80:
                    smart_insights.append({
                        'type': 'warning',
                        'title': f'{cat.name} Bütçe Limitine Yaklaşıldı',
                        'description': f'Aylık limitin %{ratio:.0f}\'i kullanıldı ({spent:,.2f} / {limit_dec:,.2f} TL).',
                        'action_label': 'Kategorileri Gör',
                        'action_url': '/categories',
                        'icon': 'alert-circle',
                    })
                    break

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
            'open_assets': [
                {
                    'id': getattr(a, 'id', None),
                    'name': getattr(a, 'name', '') or getattr(a, 'type', 'Varlık'),
                    'type': getattr(a, 'type', 'Diğer') or 'Diğer',
                    'currency': getattr(a, 'currency', 'TRY') or 'TRY',
                    'unit_price': _to_float(getattr(a, 'unit_price', 0)),
                    'value': _to_float(getattr(a, 'value', 0)),
                }
                for a in open_assets
            ],
            'net_monthly_delta': net_monthly_delta,
            'smart_insights': smart_insights[:4],
            'debt_freedom': debt_freedom,
        }

