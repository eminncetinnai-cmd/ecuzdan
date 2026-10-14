"""Cash Flow and Monthly Dashboard Calculation Service.

Handles daily cash projections, cash trend calculations, and yearly monthly breakdowns.
"""
import calendar
from datetime import datetime, timedelta

from domain.analysis.services.helpers import _apply_tenant, _safe_percentage
from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer
from models import Asset, AssetUpdate, Transaction


def calculate_cash_trend(now, all_transactions, days_count):
    """Belirtilen gün sayısı için nakit trendini hesaplar.

    Gelecekteki bekleyen işlemleri de dahil eder.
    Günlük olarak işlemleri filtreleyerek dinamik trend oluşturur.
    Sadece o yıla ait işlemleri dahil eder.
    Transfer'leri nakit akışından hariç tutar (Phase 2).
    """
    data = []

    # Transfer'leri hariç tut
    cash_flow_transactions = [t for t in all_transactions if not CashFlowAnalyzer.is_transfer(t)]

    # Her gün için nakit bakiyesini hesapla
    for i in range(days_count):
        current_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")

        day_cash = sum(
            t.amount if t.type == 'Gelir' else -t.amount
            for t in cash_flow_transactions
            if t.date <= current_date and t.status in ('Ödendi', 'Bekliyor')
        )
        data.append(day_cash)

    return data


def calculate_monthly_daily_balance(year, month, all_transactions):
    """Belirtilen ay için günlük nakit bakiyesini hesaplar.

    Eğer içinde bulunduğumuz ay ise, sadece bugünden sonraki günleri gösterir.
    Gelecek aylar için tüm ayı gösterir.
    """
    now = datetime.now()
    is_current_month = (year == now.year and month == now.month)

    days_in_month = calendar.monthrange(year, month)[1]
    data = []
    labels = []

    # Başlangıç gününü belirle
    start_day = now.day if is_current_month else 1

    # Her gün için nakit bakiyesini hesapla
    for day in range(start_day, days_in_month + 1):
        current_date = f"{year}-{month:02d}-{day:02d}"
        labels.append(current_date)

        day_cash = sum(
            t.amount if t.type == 'Gelir' else -t.amount
            for t in all_transactions
            if t.date <= current_date and t.status in ('Ödendi', 'Bekliyor')
        )
        data.append(day_cash)

    return labels, data


def calculate_monthly_dashboard_data(year, tenant_id=None):
    """Yıllık aylık dashboard verilerini hesaplar.

    Her ay için gelir, gider, yatırım ve net değer döner.
    """
    tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    m_data = []
    i_data = []
    valuation_by_month = {i: 0 for i in range(1, 13)}
    valuation_query = AssetUpdate.query.join(Asset, AssetUpdate.asset_id == Asset.id).filter(
        AssetUpdate.updated_at >= datetime(year, 1, 1),
        AssetUpdate.updated_at < datetime(year + 1, 1, 1),
    )
    valuation_updates = _apply_tenant(valuation_query, Asset, tenant_id).all()
    for update in valuation_updates:
        valuation_by_month[update.updated_at.month] += (update.new_value or 0) - (update.old_value or 0)

    for i in range(1, 13):
        start = f"{year}-{i:02d}-01"
        end = f"{year}-{i:02d}-{calendar.monthrange(year, i)[1]:02d}"
        query = Transaction.query.filter(
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.is_deleted.is_(False),
        )
        all_m = _apply_tenant(query, Transaction, tenant_id).all()

        inc = sum(t.amount for t in all_m if t.type == 'Gelir')
        exp = sum(t.amount for t in all_m if t.type == 'Gider')
        inv = sum(t.amount for t in all_m if t.type == 'Yatırım')
        inc_paid = sum(t.amount for t in all_m if t.type == 'Gelir' and t.status == 'Ödendi')
        exp_paid = sum(t.amount for t in all_m if t.type == 'Gider' and t.status == 'Ödendi')
        inv_paid = sum(t.amount for t in all_m if t.type == 'Yatırım' and t.status == 'Ödendi')
        inc_pending = sum(t.amount for t in all_m if t.type == 'Gelir' and t.status == 'Bekliyor')
        exp_pending = sum(t.amount for t in all_m if t.type == 'Gider' and t.status == 'Bekliyor')
        inv_pending = sum(t.amount for t in all_m if t.type == 'Yatırım' and t.status == 'Bekliyor')
        realized_net = inc_paid - exp_paid - inv_paid
        projected_net = inc - exp - inv
        inv_share = _safe_percentage(inv, inc)
        inv_paid_share = _safe_percentage(inv_paid, inc_paid)
        inv_pending_share = _safe_percentage(inv_pending, inc_pending)

        m_data.append({
            "name": tr[i-1],
            "inc": inc,
            "exp": exp,
            "inv": inv,
            "net": projected_net,
            "inc_paid": inc_paid,
            "exp_paid": exp_paid,
            "inv_paid": inv_paid,
            "inc_pending": inc_pending,
            "exp_pending": exp_pending,
            "inv_pending": inv_pending,
            "realized_net": realized_net,
            "projected_net": projected_net,
            "pending_net": inc_pending - exp_pending - inv_pending,
            "valuation_delta": valuation_by_month[i],
            "inv_share": inv_share,
            "inv_paid_share": inv_paid_share,
            "inv_pending_share": inv_pending_share,
        })
        i_data.append(inv)

    return (m_data, i_data, tr)
