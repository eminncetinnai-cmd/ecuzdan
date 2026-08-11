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


def evaluate_all(tenant_id, preferences=None, today=None):
    """
    Tüm kuralları kullanıcı tercihlerine göre çalıştırır.

    preferences None ise varsayılan (her iki kural açık, 3 gün) kabul edilir.
    """
    notify_budget = True
    notify_payments = True
    reminder_days = 3
    if preferences is not None:
        notify_budget = bool(preferences.notify_budget)
        notify_payments = bool(preferences.notify_payments)
        reminder_days = preferences.payment_reminder_days or 3

    drafts = []
    if notify_budget:
        drafts.extend(evaluate_budget_alerts(tenant_id, today=today))
    if notify_payments:
        drafts.extend(evaluate_payment_alerts(tenant_id, reminder_days=reminder_days, today=today))
    return drafts
