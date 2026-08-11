"""Bildirim kuralları (Faz 21).

Kurallar mevcut veriden türetilir; ayrı bir "kural tanımı" tablosu yoktur:
  - Bütçe aşımı : Category.budget_limit'i olan kategorilerde bu ayın gideri
  - Ödeme       : status='Bekliyor' işlemlerin vadesi (yaklaşan / gecikmiş)

Teslimat kanalı uygulama içidir. dedupe_key sayesinde aynı uyarı her
değerlendirmede yeniden üretilmez; ay/gün değişince yeni kayıt oluşur.
"""

import logging
from datetime import datetime, timedelta

from shared.decimal_precision import to_decimal
from utils.format_utils import format_money

logger = logging.getLogger(__name__)

#: Bütçenin bu oranı aşıldığında uyarı üretilir.
BUDGET_WARN_RATIO = to_decimal(0.80, scale=4)


def _month_bounds(today):
    start = today.replace(day=1).strftime('%Y-%m-%d')
    return start, today.strftime('%Y-%m-%d')


def evaluate_budget_alerts(tenant_id, today=None):
    """Bütçe limiti aşılan/yaklaşılan kategoriler için uyarı taslakları."""
    from domain.catalog.models.catalog_models import Category
    from models import Transaction

    today = today or datetime.now()
    period = today.strftime('%Y-%m')
    start, end = _month_bounds(today)

    categories = Category.query.filter(
        Category.tenant_id == tenant_id,
        Category.budget_limit.isnot(None),
        Category.type == 'Gider',
    ).all()

    drafts = []
    for category in categories:
        limit = to_decimal(category.budget_limit)
        if limit <= 0:
            continue

        spent = to_decimal(sum(
            t.amount for t in Transaction.query.filter(
                Transaction.tenant_id == tenant_id,
                Transaction.category == category.name,
                Transaction.type == 'Gider',
                Transaction.status == 'Ödendi',
                Transaction.date >= start,
                Transaction.date <= end,
            ).all()
        ))
        ratio = spent / limit

        if ratio >= 1:
            severity, label = 'danger', 'aşıldı'
        elif ratio >= BUDGET_WARN_RATIO:
            severity, label = 'warning', 'sınıra yaklaştı'
        else:
            continue

        drafts.append({
            'category': 'budget',
            'severity': severity,
            'title': f'Bütçe {label}: {category.name}',
            'body': (
                f'Bu ay {format_money(spent)} ₺ harcadınız; '
                f'limit {format_money(limit)} ₺ (%{ratio * 100:.0f}).'
            ),
            'link': '/categories',
            # Ay + eşik: aynı ay içinde önce uyarı, sonra aşım bildirimi çıkabilir
            'dedupe_key': f'budget:{category.id}:{period}:{severity}',
        })
    return drafts


def evaluate_payment_alerts(tenant_id, reminder_days=3, today=None):
    """Vadesi yaklaşan ve gecikmiş bekleyen ödemeler."""
    from models import Transaction

    today = today or datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    horizon = (today + timedelta(days=max(0, int(reminder_days)))).strftime('%Y-%m-%d')

    pending = Transaction.query.filter(
        Transaction.tenant_id == tenant_id,
        Transaction.status == 'Bekliyor',
        Transaction.type.in_(['Gider', 'Borç']),
        Transaction.date <= horizon,
    ).order_by(Transaction.date).all()

    drafts = []
    for tx in pending:
        overdue = tx.date < today_str
        name = tx.description or tx.category
        drafts.append({
            'category': 'payment',
            'severity': 'danger' if overdue else 'warning',
            'title': ('Gecikmiş ödeme: ' if overdue else 'Yaklaşan ödeme: ') + name,
            'body': f'{format_money(tx.amount)} ₺ · vade {tx.date}',
            'link': '/payment_calendar',
            'dedupe_key': f'payment:{tx.id}:{"overdue" if overdue else "due"}',
        })
    return drafts


def evaluate_asset_alerts(tenant_id, today=None):
    """Varlık fiyat değişiklikleri ve önemli hareketler için uyarılar."""
    from domain.portfolio.models.portfolio_models import Asset
    
    today = today or datetime.now()
    period_start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    assets = Asset.query.filter(
        Asset.tenant_id == tenant_id,
        Asset.is_active == True,
    ).all()
    
    drafts = []
    for asset in assets:
        if not asset.current_price or not asset.purchase_price:
            continue
        
        # Calculate price change percentage
        price_change_pct = ((asset.current_price - asset.purchase_price) / asset.purchase_price) * 100
        
        # Significant price change alerts
        if abs(price_change_pct) >= 20:  # 20% or more change
            severity = 'danger' if price_change_pct < -20 else 'success'
            direction = 'düşüş' if price_change_pct < 0 else 'artış'
            drafts.append({
                'category': 'asset',
                'severity': severity,
                'title': f'Significant price change: {asset.name}',
                'body': f'{asset.name} fiyatında %{abs(price_change_pct):.1f} {direction} (Satış: {format_money(asset.current_price)} ₺)',
                'link': '/assets',
                'dedupe_key': f'asset_price:{asset.id}:{today.strftime("%Y-%m-%d")}',
            })
    
    return drafts


def evaluate_portfolio_alerts(tenant_id, today=None):
    """Portföy genel performans ve risk uyarıları."""
    from domain.portfolio.models.portfolio_models import Asset
    from shared.decimal_precision import to_decimal
    
    today = today or datetime.now()
    
    assets = Asset.query.filter(
        Asset.tenant_id == tenant_id,
        Asset.is_active == True,
    ).all()
    
    if not assets:
        return []
    
    # Calculate portfolio concentration
    total_value = sum(asset.current_price * asset.quantity if asset.current_price else 0 for asset in assets)
    
    if total_value <= 0:
        return []
    
    drafts = []
    
    # Check for concentration risk (single asset > 40% of portfolio)
    for asset in assets:
        if not asset.current_price:
            continue
        asset_value = asset.current_price * asset.quantity
        concentration = (asset_value / total_value) * 100
        
        if concentration >= 40:
            drafts.append({
                'category': 'portfolio',
                'severity': 'warning',
                'title': f'Concentration risk: {asset.name}',
                'body': f'{asset.name} portföyün %{concentration:.1f}\'ini oluşturuyor. Diversifikasyon önerilir.',
                'link': '/assets',
                'dedupe_key': f'concentration:{asset.id}:{today.strftime("%Y-%m")}',
            })
    
    return drafts


def evaluate_goal_alerts(tenant_id, today=None):
    """Yatırım hedefleri ve ilerleme uyarıları."""
    # Placeholder for goal tracking alerts
    # This would require a goals table/model
    return []


def evaluate_all(tenant_id, preferences=None, today=None):
    """
    Tüm kuralları kullanıcı tercihlerine göre çalıştırır.

    preferences None ise varsayılan (her iki kural açık, 3 gün) kabul edilir.
    """
    notify_budget = True
    notify_payments = True
    notify_assets = True
    notify_portfolio = True
    reminder_days = 3
    if preferences is not None:
        notify_budget = bool(preferences.notify_budget)
        notify_payments = bool(preferences.notify_payments)
        notify_assets = bool(getattr(preferences, 'notify_assets', True))
        notify_portfolio = bool(getattr(preferences, 'notify_portfolio', True))
        reminder_days = preferences.payment_reminder_days or 3

    drafts = []
    if notify_budget:
        drafts.extend(evaluate_budget_alerts(tenant_id, today=today))
    if notify_payments:
        drafts.extend(evaluate_payment_alerts(tenant_id, reminder_days=reminder_days, today=today))
    if notify_assets:
        drafts.extend(evaluate_asset_alerts(tenant_id, today=today))
    if notify_portfolio:
        drafts.extend(evaluate_portfolio_alerts(tenant_id, today=today))
    return drafts
