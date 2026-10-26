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
    O(N + D) prefix-sum yaklaşımıyla optimize edilmiştir.
    """
    if days_count <= 0:
        return []

    from collections import defaultdict
    from decimal import Decimal

    cash_flow_transactions = [t for t in all_transactions if not CashFlowAnalyzer.is_transfer(t)]
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=days_count - 1)).strftime("%Y-%m-%d")

    daily_delta = defaultdict(lambda: Decimal('0'))
    base_cash = Decimal('0')

    for t in cash_flow_transactions:
        status = getattr(t, 'status', None)
        if status not in ('Ödendi', 'Bekliyor'):
            continue
        amt = Decimal(str(t.amount or 0)) if t.type == 'Gelir' else -Decimal(str(t.amount or 0))
        t_date = str(t.date)
        if t_date < start_date:
            base_cash += amt
        elif start_date <= t_date <= end_date:
            daily_delta[t_date] += amt

    data = []
    current_cash = base_cash
    for i in range(days_count):
        current_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        current_cash += daily_delta[current_date]
        data.append(current_cash)

    return data


def calculate_monthly_daily_balance(year, month, all_transactions):
    """Belirtilen ay için günlük nakit bakiyesini hesaplar.

    Eğer içinde bulunduğumuz ay ise, sadece bugünden sonraki günleri gösterir.
    Gelecek aylar için tüm ayı gösterir.
    O(N + D) prefix-sum yaklaşımıyla optimize edilmiştir.
    """
    now = datetime.now()
    is_current_month = (year == now.year and month == now.month)

    days_in_month = calendar.monthrange(year, month)[1]
    start_day = now.day if is_current_month else 1

    start_date = f"{year}-{month:02d}-{start_day:02d}"
    end_date = f"{year}-{month:02d}-{days_in_month:02d}"

    from collections import defaultdict
    from decimal import Decimal

    daily_delta = defaultdict(lambda: Decimal('0'))
    base_cash = Decimal('0')

    for t in all_transactions:
        status = getattr(t, 'status', None)
        if status not in ('Ödendi', 'Bekliyor'):
            continue
        amt = Decimal(str(t.amount or 0)) if t.type == 'Gelir' else -Decimal(str(t.amount or 0))
        t_date = str(t.date)
        if t_date < start_date:
            base_cash += amt
        elif start_date <= t_date <= end_date:
            daily_delta[t_date] += amt

    labels = []
    data = []
    current_cash = base_cash
    for day in range(start_day, days_in_month + 1):
        current_date = f"{year}-{month:02d}-{day:02d}"
        labels.append(current_date)
        current_cash += daily_delta[current_date]
        data.append(current_cash)

    return labels, data


def calculate_monthly_dashboard_data(year, tenant_id=None):
    """Yıllık aylık dashboard verilerini hesaplar.

    Her ay için gelir, gider, yatırım ve net değer döner.
    12 ayrı sorgu yerine tek konsolide yıllık SQL sorgusuyla optimize edilmiştir.
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

    # 12 ayrı döngü sorgusu yerine tüm yılı tek seferde sorgula ve bellekte grupla
    start_year = f"{year}-01-01"
    end_year = f"{year}-12-31"
    query = Transaction.query.filter(
        Transaction.date >= start_year,
        Transaction.date <= end_year,
        Transaction.is_deleted.is_(False),
    )
    all_year_txs = _apply_tenant(query, Transaction, tenant_id).all()

    txs_by_month = {m: [] for m in range(1, 13)}
    for t in all_year_txs:
        try:
            m = int(str(t.date).split('-')[1])
            if 1 <= m <= 12:
                txs_by_month[m].append(t)
        except (IndexError, ValueError):
            continue

    for i in range(1, 13):
        all_m = txs_by_month[i]

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
