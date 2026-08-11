import calendar
import logging
from datetime import datetime, timedelta

from infrastructure.database.financial_db_service import get_actual_cash, get_total_assets, get_total_debts
from models import Asset, AssetUpdate, RecurringPlan, Transaction, db
from shared.decimal_precision import to_decimal
from utils.format_utils import format_date, format_money, parse_date_input, today_display, today_storage

logger = logging.getLogger(__name__)

# Canlı veri önbelleği
LIVE_DATA_CACHE = {
    "data": None,
    "last_fetched": 0
}

# Finansal analiz önbelleği
FINANCIAL_ANALYSIS_CACHE = {
    "data": {},
    "last_fetched": {}
}

# Aylık dashboard önbelleği
MONTHLY_DASHBOARD_CACHE = {
    "data": {},
    "last_fetched": {}
}

CACHE_TTL = 300  # 5 dakika önbellek süresi


def _resolve_tenant_id(tenant_id=None):
    if tenant_id:
        return tenant_id
    try:
        from flask import g, has_request_context
        if has_request_context():
            return g.get('tenant_id')
    except RuntimeError:
        pass
    return None


def _apply_tenant(query, model, tenant_id):
    return query.filter(model.tenant_id == tenant_id) if tenant_id else query


def _as_decimal(value, scale=4):
    return to_decimal(0 if value is None else value, scale=scale)


def _safe_percentage(numerator, denominator):
    if denominator and denominator > 0:
        return _as_decimal(numerator) / _as_decimal(denominator) * 100
    return 0

def get_live_data():
    """Canlı verileri (hava durumu, döviz, altın) arka plan servisinden getirir"""
    try:
        from infrastructure.background.background_service import get_background_service
        return get_background_service().get_live_data()
    except Exception as e:
        logger.error(f"Canlı veri servisinden alınamadı: {e}")
        return {"weather": "--°C", "usd": "--", "eur": "--", "gold": "--", "last_updated": ""}

def get_financial_analysis(tenant_id=None):
    """
    Kapsamlı finansal analiz hesaplamaları yapar.
    Likidite, borç oranı, tasarruf oranı, dayanıklılık ve finansal skor hesaplar.
    Önbellek kullanarak performansı optimize eder.
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    now = datetime.now()
    current_time = now.timestamp()
    
    # Önbellek kontrolü
    if tenant_id in FINANCIAL_ANALYSIS_CACHE["data"]:
        cached_data, cached_time = FINANCIAL_ANALYSIS_CACHE["data"][tenant_id], FINANCIAL_ANALYSIS_CACHE["last_fetched"].get(tenant_id, 0)
        if current_time - cached_time < CACHE_TTL:
            return cached_data
    
    all_t = _apply_tenant(Transaction.query, Transaction, tenant_id).all()
    assets = _apply_tenant(Asset.query, Asset, tenant_id).all()
    debt_plans = _apply_tenant(
        RecurringPlan.query.filter_by(flow_type='Gider'),
        RecurringPlan,
        tenant_id,
    ).all()

    # Temel değerler
    total_asset_val = sum(a.value for a in assets)

    # Cash flow analysis excluding transfers (Phase 2)
    from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer
    cash_flow_tx = [t for t in all_t if not CashFlowAnalyzer.is_transfer(t)]
    actual_cash = sum(t.amount if t.type == 'Gelir' else -t.amount for t in cash_flow_tx if t.status == 'Ödendi')

    total_servet = total_asset_val + actual_cash
    total_debt = sum(p.amount * p.installments for p in debt_plans)

    # Aylık değerler (excluding transfers)
    cur_m = now.strftime("%Y-%m")
    m_exp = sum(t.amount for t in cash_flow_tx if t.type == 'Gider' and t.date.startswith(cur_m))
    m_inc = sum(t.amount for t in cash_flow_tx if t.type == 'Gelir' and t.date.startswith(cur_m))

    # Finansal metrikler
    liq = _as_decimal(actual_cash) / (_as_decimal(m_exp) if m_exp > 0 else _as_decimal(1))
    dr = _safe_percentage(total_debt, total_servet)
    sr = _safe_percentage(m_inc - m_exp, m_inc if m_inc > 0 else 1)
    sus = _as_decimal(actual_cash) / (_as_decimal(m_exp) if m_exp > 0 else _as_decimal(30))

    # Finansal skor (0-100)
    score = max(
        0,
        min(100, int(100 - (dr * to_decimal(1.5, scale=1)) + (sr * to_decimal(0.5, scale=1)))),
    )

    # Flag'ler ve öneriler
    flags = []
    recs = []

    # 1. Likidite analizi
    if liq >= to_decimal(1.5, scale=1):
        liq_status, liq_msg = "success", "Mükemmel: Kısa vadeli harcamalarınızı karşılayacak fazlasıyla nakdiniz var."
    elif liq >= 1:
        liq_status, liq_msg = "warning", "Sınırda: Kısa vadeli nakit akışınız dengeli ancak beklenmedik harcamalara karşı dikkatli olun."
    else:
        liq_status, liq_msg = "danger", "Kritik Risk! Nakit rezervleriniz aylık harcamalarınızın altında. Nakit sıkışıklığı kapıda."
        flags.append("Düşük Likidite")
        recs.append("Nakit rezervlerinizi artırmak için acilen zorunlu olmayan giderlerinizi dondurun.")

    # 2. Borç oranı analizi
    if dr < 30:
        dr_status, dr_msg = "success", "Sağlıklı: Toplam borç yükünüz servetinizin %30'unun altında."
    elif dr <= 40:
        dr_status, dr_msg = "warning", "Dikkat: Borç yükünüz artıyor (%30 - %40). Yeni borç almaktan kaçının."
    else:
        dr_status, dr_msg = "danger", "Yüksek Risk! Borçlar servetinizin %40'ından fazla. Borç ödeme yükü bütçenizi zorluyor."
        flags.append("Yüksek Borç Oranı")
        recs.append("Kredi kartı borçlarını azaltmak için yüksek faizli kart ödemelerini hızlandırın.")

    # 3. Tasarruf oranı analizi
    if sr >= 20:
        sr_status, sr_msg = "success", "Harika: Gelirinizin %20'sinden fazlasını tasarruf edebiliyorsunuz."
    elif sr >= 0:
        sr_status, sr_msg = "warning", "Orta Seviye: Tasarruf oranınız pozitif ancak servet artışı için %20 hedefine odaklanın."
    else:
        sr_status, sr_msg = "danger", "Bütçe Açığı! Gelirinizden fazla harcıyorsunuz. Acilen bütçe kontrolü yapın."
        flags.append("Bütçe Açığı")
        recs.append("Lüks harcamaları sıfırlayın ve abonelik iptalleri gibi tasarruf yöntemlerini devreye alın.")

    # 4. Dayanıklılık analizi
    if sus >= 6:
        sus_status, sus_msg = "success", "Güvenli: Eldeki nakit sizi 6 aydan fazla gelir olmadan yaşatabilir."
    elif sus >= 3:
        sus_status, sus_msg = "warning", "Yeterli: 3-6 aylık acil durum bütçesine sahipsiniz. Hedefiniz 6 ay olmalı."
    else:
        sus_status, sus_msg = "danger", "Kırılgan! Nakdiniz 3 aydan az bir süre için yeterli. Olası bir kriz durumunda hazırlıksızsınız."
        flags.append("Zayıf Acil Durum Fonu")
        recs.append("En az 3-6 aylık giderinize eşit bir acil durum fonu oluşturup dokunulmaz bir hesapta saklayın.")

    # Uzman strateji önerisi
    if score > 75:
        strategy = "Finansal sağlığınız çok iyi durumda. Portföyünüzü enflasyona karşı korumak ve büyütmek amacıyla hisse senedi, fon veya altın gibi yatırım araçlarına daha fazla pay ayırabilirsiniz."
    elif score > 50:
        strategy = "Finansal dengeniz stabil ancak kırılganlıklar var. Öncelikle acil durum fonunuzu en az 3 aylık harcamanıza sabitleyin, ardından yüksek faizli borçları erken kapatarak borç yükünü hafifletin."
    else:
        strategy = "ACİL EYLEM GEREKLİ: Finansal durumunuz ciddi risk altında. Kredi kartı kullanımını tamamen durdurun, bütçe açığını kapatmak için tüm isteğe bağlı harcamaları askıya alın ve likiditenizi artırın."

    result = {
        "score": score,
        "strategy": strategy,
        "flags": flags,
        "recs": recs,
        "liquidity": round(liq, 2),
        "liq_status": liq_status,
        "liq_msg": liq_msg,
        "debt_ratio": round(dr, 1),
        "dr_status": dr_status,
        "dr_msg": dr_msg,
        "savings": round(sr, 1),
        "sr_status": sr_status,
        "sr_msg": sr_msg,
        "sustain": round(sus, 1),
        "sus_status": sus_status,
        "sus_msg": sus_msg,
        "total_servet": total_servet,
        "total_debt": total_debt,
        "net_worth": total_servet - total_debt,
        "actual_cash": actual_cash
    }
    
    # Önbelleğe kaydet
    FINANCIAL_ANALYSIS_CACHE["data"][tenant_id] = result
    FINANCIAL_ANALYSIS_CACHE["last_fetched"][tenant_id] = current_time
    
    return result

def calculate_cash_trend(now, all_transactions, days_count):
    """
    Belirtilen gün sayısı için nakit trendini hesaplar.
    Gelecekteki bekleyen işlemleri de dahil eder.
    Günlük olarak işlemleri filtreleyerek dinamik trend oluşturur.
    Sadece o yıla ait işlemleri dahil eder.
    Transfer'leri nakit akışından hariç tutar (Phase 2).
    """
    from datetime import timedelta
    from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer
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
    """
    Belirtilen ay için günlük nakit bakiyesini hesaplar.
    Eğer içinde bulunduğumuz ay ise, sadece bugünden sonraki günleri gösterir.
    Gelecek aylar için tüm ayı gösterir.
    """
    import calendar as cal_mod
    from datetime import datetime as dt

    now = dt.now()
    is_current_month = (year == now.year and month == now.month)

    days_in_month = cal_mod.monthrange(year, month)[1]
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

def get_monthly_dashboard_data(year, tenant_id=None):
    """
    Yıllık aylık dashboard verilerini hesaplar.
    Her ay için gelir, gider, yatırım ve net değer döner.
    Önbellek kullanarak performansı optimize eder.
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    cache_key = f"{tenant_id}_{year}"
    current_time = datetime.now().timestamp()
    
    # Önbellek kontrolü
    if cache_key in MONTHLY_DASHBOARD_CACHE["data"]:
        cached_data, cached_time = MONTHLY_DASHBOARD_CACHE["data"][cache_key], MONTHLY_DASHBOARD_CACHE["last_fetched"].get(cache_key, 0)
        if current_time - cached_time < CACHE_TTL:
            return cached_data
    
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
        query = Transaction.query.filter(Transaction.date >= start, Transaction.date <= end)
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

    result = (m_data, i_data, tr)
    
    # Önbelleğe kaydet
    MONTHLY_DASHBOARD_CACHE["data"][cache_key] = result
    MONTHLY_DASHBOARD_CACHE["last_fetched"][cache_key] = current_time
    
    return result


# Re-export for backward compatibility
__all__ = ['format_money', 'format_date', 'parse_date_input', 'today_storage', 'today_display']

def get_asset_analysis(tenant_id=None):
    """
    Profesyonel varlık analizi hesaplamaları.
    Portföy performansı, diversification, risk analizi gibi metrikleri döner.
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    assets = _apply_tenant(Asset.query, Asset, tenant_id).all()
    if not assets:
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_gain_loss': 0,
            'overall_roi': 0,
            'asset_count': 0,
            'by_type': {},
            'by_risk': {},
            'by_liquidity': {},
            'by_sector': {},
            'top_performers': [],
            'worst_performers': [],
            'portfolio_concentration': {},
            'risk_score': 0,
            'liquidity_score': 0
        }

    total_value = _as_decimal(sum(a.value for a in assets))
    total_cost = _as_decimal(sum(a.purchase_cost or 0 for a in assets))
    total_gain_loss = total_value - total_cost
    overall_roi = _safe_percentage(total_gain_loss, total_cost)

    # Varlık tipine göre gruplama
    by_type = {}
    for a in assets:
        if a.type not in by_type:
            by_type[a.type] = {'count': 0, 'value': 0, 'weight': 0}
        by_type[a.type]['count'] += 1
        by_type[a.type]['value'] += a.value

    for t in by_type:
        by_type[t]['weight'] = _safe_percentage(by_type[t]['value'], total_value)

    # Risk seviyesine göre gruplama
    by_risk = {'Düşük': {'count': 0, 'value': 0, 'weight': 0},
               'Orta': {'count': 0, 'value': 0, 'weight': 0},
               'Yüksek': {'count': 0, 'value': 0, 'weight': 0}}
    for a in assets:
        risk = a.risk_level or 'Orta'
        if risk in by_risk:
            by_risk[risk]['count'] += 1
            by_risk[risk]['value'] += a.value

    for r in by_risk:
        by_risk[r]['weight'] = _safe_percentage(by_risk[r]['value'], total_value)

    # Likiditeye göre gruplama
    by_liquidity = {'Likit': {'count': 0, 'value': 0, 'weight': 0},
                    'Yarı-Likit': {'count': 0, 'value': 0, 'weight': 0},
                    'İ-Likit': {'count': 0, 'value': 0, 'weight': 0}}
    for a in assets:
        liq = a.liquidity or 'Likit'
        if liq in by_liquidity:
            by_liquidity[liq]['count'] += 1
            by_liquidity[liq]['value'] += a.value

    for l in by_liquidity:
        by_liquidity[l]['weight'] = _safe_percentage(by_liquidity[l]['value'], total_value)

    # Sektöre göre gruplama
    by_sector = {}
    for a in assets:
        from models import AssetSector
        sector_obj = db.session.get(AssetSector, a.sector_id) if a.sector_id else None
        sector = sector_obj.name if sector_obj else 'Diğer'
        if sector not in by_sector:
            by_sector[sector] = {'count': 0, 'value': 0, 'weight': 0}
        by_sector[sector]['count'] += 1
        by_sector[sector]['value'] += a.value

    for s in by_sector:
        by_sector[s]['weight'] = _safe_percentage(by_sector[s]['value'], total_value)

    # En iyi ve en kötü performans gösteren varlıklar (total_gain_loss'a göre sırala)
    assets_with_gain = [(a, a.total_gain_loss) for a in assets if a.value and a.value > 0]
    assets_with_gain.sort(key=lambda x: x[1], reverse=True)

    # En iyi performanslar: Sadece pozitif gain_loss olan varlıklar
    top_performers = [{'name': a.name, 'type': a.type, 'roi': a.roi, 'gain_loss': gain, 'value': a.value} for a, gain in assets_with_gain if gain > 0][:5]

    # En kötü performanslar: Sadece negatif gain_loss olan varlıklar (en düşükten başla)
    worst_performers = [{'name': a.name, 'type': a.type, 'roi': a.roi, 'gain_loss': gain, 'value': a.value} for a, gain in assets_with_gain if gain < 0][-5:][::-1]

    # Portföy konsantrasyonu (Herhangi bir varlığın %20'den fazla olması riskli)
    portfolio_concentration = {
        'high_concentration_assets': [{'name': a.name, 'weight': a.portfolio_weight} for a in assets if a.portfolio_weight > 20],
        'concentration_risk': any(a.portfolio_weight > 20 for a in assets)
    }

    # Risk skoru hesaplama (0-100)
    risk_score = 0
    if by_risk['Yüksek']['weight'] > 30:
        risk_score += 30
    elif by_risk['Yüksek']['weight'] > 10:
        risk_score += 15
    if by_risk['Orta']['weight'] > 50:
        risk_score += 20
    if portfolio_concentration['concentration_risk']:
        risk_score += 25
    if by_liquidity['İ-Likit']['weight'] > 30:
        risk_score += 15
    risk_score = min(100, risk_score)

    # Likidite skoru hesaplama (0-100)
    liquidity_score = by_liquidity['Likit']['weight']
    liquidity_score += by_liquidity['Yarı-Likit']['weight'] * to_decimal(0.5, scale=1)
    liquidity_score = min(100, liquidity_score)

    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_gain_loss,
        'overall_roi': overall_roi,
        'asset_count': len(assets),
        'by_type': by_type,
        'by_risk': by_risk,
        'by_liquidity': by_liquidity,
        'by_sector': by_sector,
        'top_performers': top_performers,
        'worst_performers': worst_performers,
        'portfolio_concentration': portfolio_concentration,
        'risk_score': round(risk_score, 1),
        'liquidity_score': round(liquidity_score, 1)
    }

# --- Finansal Özgürlük (FIRE) sabitleri — akademik referanslar ---
FI_MULTIPLIER = 25          # Trinity Study / 4% güvenli çekim kuralı (Bengen, 1994)
SAFE_WITHDRAWAL_RATE = 0.04 # %4 yıllık portföy çekimi
REAL_RETURN_RATE = 0.07     # Uzun vadeli reel getiri varsayımı (%7) - dinamik olarak güncellenebilir
DEFAULT_EMERGENCY_FUND_MONTHS = 6  # Ramsey / Fed: 3-6 ay; muhafazakâr hedef 6 ay


def _resolve_freedom_assumptions(preferences):
    """
    Kullanıcı tercihlerini analiz varsayımlarına çevirir.

    preferences None ise (veya alanlar boş bırakılmışsa) modül sabitlerine
    düşer — böylece tercih girmemiş kullanıcılar için davranış değişmez.
    """
    swr = to_decimal(SAFE_WITHDRAWAL_RATE, scale=4)
    emergency_target = DEFAULT_EMERGENCY_FUND_MONTHS
    passive_income_target = None
    target_year = None

    if preferences is not None:
        if preferences.safe_withdrawal_rate:
            swr = to_decimal(preferences.safe_withdrawal_rate, scale=4)
        if preferences.emergency_fund_target_months:
            emergency_target = int(preferences.emergency_fund_target_months)
        if preferences.target_monthly_passive_income:
            passive_income_target = _as_decimal(preferences.target_monthly_passive_income)
        target_year = preferences.target_retirement_year

    return {
        'safe_withdrawal_rate': swr,
        # FI çarpanı SWR'nin tersidir: %4 → 25×, %3 → 33.3×
        'fi_multiplier': (to_decimal(1, scale=4) / swr) if swr else to_decimal(FI_MULTIPLIER, scale=4),
        'emergency_fund_target_months': emergency_target,
        'target_monthly_passive_income': passive_income_target,
        'target_retirement_year': target_year,
        'is_customized': preferences is not None and any([
            preferences.safe_withdrawal_rate,
            preferences.emergency_fund_target_months,
            preferences.target_monthly_passive_income,
            preferences.target_retirement_year,
        ]),
    }


def get_dynamic_return_rate():
    """
    Dinamik reel getiri oranını piyasa verisinden çeker
    Varsayılan %7, piyasa verisi varsa güncel değer kullanılır
    """
    try:
        from market_data_service import get_macro_economic_data
        macro_data = get_macro_economic_data()
        if macro_data and 'real_return_rate' in macro_data:
            return macro_data['real_return_rate'] / 100  # %'yi decimal'e çevir
    except Exception as e:
        logger.warning(f"Dynamic return rate fetch failed, using default: {e}")
    return REAL_RETURN_RATE


def _years_to_financial_independence(portfolio, monthly_savings, monthly_expenses, annual_return=None,
                                     fi_multiplier=FI_MULTIPLIER):
    """Bileşik getiri + düzenli birikimle FI hedefine kalan yıl (FIRE hesaplayıcı mantığı)."""
    if monthly_expenses <= 0:
        return 0.0
    fi_target = monthly_expenses * 12 * to_decimal(fi_multiplier, scale=4)
    if portfolio >= fi_target:
        return 0.0
    if monthly_savings <= 0:
        return None

    if annual_return is None:
        annual_return = get_dynamic_return_rate()

    monthly_r = to_decimal(annual_return) / 12
    balance = to_decimal(portfolio)
    monthly_savings = to_decimal(monthly_savings)
    fi_target = to_decimal(fi_target)
    months = 0
    while balance < fi_target and months < 1200:
        balance = balance * (1 + monthly_r) + monthly_savings
        months += 1
    if months >= 1200:
        return None
    return round(months / 12, 1)


def _criterion_score(value, thresholds):
    """(limit, points) çiftleri — value yükseldikçe puan artar."""
    score = 0
    for limit, points in thresholds:
        if value >= limit:
            score = points
    return score


def _status_from_score(score, max_score):
    ratio = (_as_decimal(score) / _as_decimal(max_score)) if max_score else 0
    if ratio >= to_decimal(0.85, scale=2):
        return 'success'
    if ratio >= to_decimal(0.5, scale=1):
        return 'warning'
    return 'danger'


def _determine_freedom_stage(fi_progress, savings_rate, emergency_months, income_replacement_pct, is_free):
    if is_free:
        return {
            'level': 7, 'key': 'fire', 'name': 'Finansal Bağımsızlık',
            'description': 'Pasif geliriniz yaşam giderlerinizi sürdürebilecek düzeyde.',
            'icon': '🏆',
        }
    if fi_progress >= 75 or income_replacement_pct >= 75:
        return {
            'level': 6, 'key': 'coast', 'name': 'Yarı Bağımsızlık',
            'description': 'Barista FIRE aşamasına yakınsınız; portföyünüz giderlerin büyük bölümünü karşılıyor.',
            'icon': '🌅',
        }
    if savings_rate >= 20 and fi_progress >= 25:
        return {
            'level': 5, 'key': 'accumulate', 'name': 'Hızlı Birikim',
            'description': 'Yüksek tasarruf oranıyla FI hedefine sistematik ilerliyorsunuz.',
            'icon': '📈',
        }
    if emergency_months >= 3:
        return {
            'level': 4, 'key': 'security', 'name': 'Güvenlik Ağı',
            'description': 'Acil durum fonunuz oluştu; yatırıma odaklanma zamanı.',
            'icon': '🛡️',
        }
    if savings_rate > 0:
        return {
            'level': 3, 'key': 'awareness', 'name': 'Mali Farkındalık',
            'description': 'Gelir-gider dengeniz pozitif; disiplinli birikimle güçleniyorsunuz.',
            'icon': '💡',
        }
    return {
        'level': 2, 'key': 'start', 'name': 'Başlangıç',
        'description': 'Veri girişi ve bütçe disipliniyle ilk adımları atın.',
        'icon': '🌱',
    }


def _determine_fire_profile(fi_progress, income_replacement_pct, monthly_expenses, is_free):
    if is_free:
        return {'key': 'traditional', 'name': 'Geleneksel FIRE', 'detail': 'Portföyünüz 4% kuralına göre giderlerinizi karşılıyor.'}
    if income_replacement_pct >= 50:
        return {'key': 'barista', 'name': 'Barista FIRE', 'detail': 'Kısmi pasif gelir + tamamlayıcı çalışma ile sürdürülebilir.'}
    if fi_progress >= 40:
        return {'key': 'coast', 'name': 'Coast FIRE', 'detail': 'Mevcut portföy büyümesiyle hedefe ulaşma potansiyeli yüksek.'}
    if monthly_expenses > 0 and monthly_expenses < 15000:
        return {'key': 'lean', 'name': 'Lean FIRE Yolu', 'detail': 'Düşük gider profili ile daha erken bağımsızlık mümkün.'}
    return {'key': 'building', 'name': 'Birikim Aşaması', 'detail': 'FI hedefi için sistematik tasarruf ve yatırım sürecindesiniz.'}


def get_empty_freedom_analysis():
    """Hata durumunda şablona gönderilecek boş analiz."""
    return {
        'net_worth': 0, 'total_assets': 0, 'total_cash': 0, 'total_debts': 0,
        'monthly_avg_income': 0, 'monthly_avg_expenses': 0, 'annual_expenses': 0,
        'monthly_savings': 0, 'savings_rate': 0, 'expense_coverage_months': 0,
        'emergency_fund_months': 0, 'passive_income_potential': 0, 'rental_income_monthly': 0,
        'safe_withdrawal_monthly': 0, 'fi_number': 0, 'fi_progress_pct': 0,
        'income_replacement_pct': 0, 'debt_to_income_pct': 0, 'freedom_score': 0,
        'estimated_freedom_date': None, 'years_to_fi': None, 'is_financially_free': False,
        'freedom_stage': _determine_freedom_stage(0, 0, 0, 0, False),
        'fire_profile': _determine_fire_profile(0, 0, 0, False),
        'criteria': [], 'milestones': [], 'interpretation': 'Henüz yeterli veri yok.',
        'references': [],
        'assumptions': _resolve_freedom_assumptions(None),
    }


def get_financial_freedom_analysis(tenant_id=None, preferences=None):
    """
    Finansal özgürlük analizi — küresel FIRE/FI literatürüne dayalı çok kriterli değerlendirme.

    preferences: UserPreference satırı (opsiyonel). Verilmezse ya da alanları
    boşsa modül sabitleri (Trinity %4, 6 ay acil fon) kullanılır.

    Referans çerçevesi:
    - Trinity Study / 4% Rule (Bengen, 1994)
    - Your Money or Your Life (Dominguez & Robin)
    - The Millionaire Next Door (Stanley & Danko)
    - Dave Ramsey acil fon basamakları
    - Elizabeth Warren 50/30/20 kuralı
    - FIRE topluluğu tasarruf oranı matematiği
    """
    from models import Asset, Transaction

    assumptions = _resolve_freedom_assumptions(preferences)
    swr_decimal = to_decimal(assumptions['safe_withdrawal_rate'], scale=4)
    fi_multiplier_decimal = to_decimal(assumptions['fi_multiplier'], scale=4)
    emergency_target_months = assumptions['emergency_fund_target_months']

    tenant_id = _resolve_tenant_id(tenant_id)
    twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    recent_query = Transaction.query.filter(
        Transaction.date >= twelve_months_ago,
        Transaction.status == 'Ödendi',
    )
    recent_transactions = _apply_tenant(recent_query, Transaction, tenant_id).all()

    total_income = _as_decimal(sum(t.amount for t in recent_transactions if t.type == 'Gelir'))
    total_expenses = _as_decimal(sum(t.amount for t in recent_transactions if t.type == 'Gider'))
    total_investments = _as_decimal(sum(t.amount for t in recent_transactions if t.type == 'Yatırım'))

    monthly_avg_income = total_income / 12 if total_income > 0 else _as_decimal(0)
    monthly_avg_expenses = total_expenses / 12 if total_expenses > 0 else _as_decimal(0)
    monthly_savings = monthly_avg_income - monthly_avg_expenses
    annual_expenses = monthly_avg_expenses * 12
    annual_income = monthly_avg_income * 12

    total_assets = _as_decimal(get_total_assets(tenant_id))
    total_cash = _as_decimal(get_actual_cash(tenant_id))
    total_debts = _as_decimal(get_total_debts(tenant_id))
    net_worth = total_assets + total_cash - total_debts

    savings_rate = _safe_percentage(total_income - total_expenses, total_income)

    fi_number = annual_expenses * fi_multiplier_decimal if annual_expenses > 0 else _as_decimal(0)
    investable = total_assets + total_cash
    fi_progress_pct = min(100, _safe_percentage(investable, fi_number)) if fi_number > 0 else _as_decimal(0)

    safe_withdrawal_monthly = (investable * swr_decimal) / 12
    assets = _apply_tenant(Asset.query, Asset, tenant_id).all()
    rental_income_monthly = _as_decimal(sum((a.monthly_rent or 0) for a in assets)) if assets else _as_decimal(0)
    passive_income_potential = rental_income_monthly

    # Kullanıcı bir hedef pasif gelir belirlediyse karşılama oranı ona göre ölçülür.
    passive_income_benchmark = assumptions['target_monthly_passive_income'] or monthly_avg_expenses
    income_replacement_pct = _safe_percentage(passive_income_potential, passive_income_benchmark)

    emergency_fund_months = (total_cash / monthly_avg_expenses) if monthly_avg_expenses > 0 else _as_decimal(0)
    expense_coverage_months = (investable / monthly_avg_expenses) if monthly_avg_expenses > 0 else _as_decimal(0)
    debt_to_income_pct = _safe_percentage(total_debts, annual_income) if annual_income > 0 else (_as_decimal(100) if total_debts > 0 else _as_decimal(0))

    is_financially_free = monthly_avg_expenses > 0 and (
        passive_income_potential >= monthly_avg_expenses
        or (safe_withdrawal_monthly >= monthly_avg_expenses and fi_progress_pct >= 100)
    )

    years_to_fi = _years_to_financial_independence(
        investable, monthly_savings, monthly_avg_expenses,
        fi_multiplier=assumptions['fi_multiplier'],
    )

    # Makroekonomik verileri çek
    try:
        from market_data_service import get_macro_economic_data
        macro_data = get_macro_economic_data()
    except Exception as e:
        logger.warning(f"Failed to fetch macro data: {e}")
        macro_data = {
            'inflation_rate': 40,
            'interest_rate': 50,
            'real_return_rate': 7,
            'source': 'default'
        }
    estimated_freedom_date = None
    if years_to_fi is not None and years_to_fi > 0:
        est = datetime.now() + timedelta(days=int(years_to_fi * 365.25))
        estimated_freedom_date = est.strftime('%m/%Y')

    freedom_stage = _determine_freedom_stage(
        fi_progress_pct, savings_rate, emergency_fund_months, income_replacement_pct, is_financially_free,
    )
    fire_profile = _determine_fire_profile(
        fi_progress_pct, income_replacement_pct, monthly_avg_expenses, is_financially_free,
    )

    criteria = []

    # 1 — Güvenli çekim kuralı / FI hedefi (Trinity Study)
    fi_pts = _criterion_score(fi_progress_pct, [(100, 25), (75, 20), (50, 15), (25, 8), (0, 0)])
    fi_multiplier_label = f'{assumptions["fi_multiplier"]:.0f}'
    criteria.append({
        'id': 'fi_number',
        'name': f'FI Hedefi ({fi_multiplier_label}× Kuralı)',
        'source': 'Trinity Study — Bengen (1994)',
        'your_value': f'%{fi_progress_pct:.1f} tamamlandı',
        'target': f'{format_money(fi_number)} ₺ (yıllık gider × {fi_multiplier_label})',
        'detail': f'Mevcut: {format_money(investable)} ₺',
        'status': _status_from_score(fi_pts, 25),
        'score': fi_pts, 'max_score': 25,
        'interpretation': (
            'Finansal bağımsızlık eşiğine ulaştınız.'
            if fi_progress_pct >= 100 else
            f'Hedefinize {format_money(max(0, fi_number - investable))} ₺ kaldı.'
        ),
    })

    # 2 — Tasarruf oranı (Warren / FIRE)
    sav_pts = _criterion_score(savings_rate, [(50, 20), (30, 17), (20, 15), (10, 8), (0, 0)])
    criteria.append({
        'id': 'savings_rate',
        'name': 'Tasarruf Oranı',
        'source': 'FIRE matematiği & 50/30/20 (Warren)',
        'your_value': f'%{savings_rate:.1f}',
        'target': '%20+ (ideal %50 FIRE hızlı mod)',
        'detail': f'Aylık tasarruf: {format_money(monthly_savings)} ₺',
        'status': _status_from_score(sav_pts, 20),
        'score': sav_pts, 'max_score': 20,
        'interpretation': (
            'Mükemmel tasarruf disiplini — FIRE literatüründe üst dilim.'
            if savings_rate >= 30 else
            'Sağlıklı tasarruf bandında.' if savings_rate >= 20 else
            'Tasarruf oranını artırmak FI sürenizi kısaltır.'
        ),
    })

    # 3 — Acil fon (Ramsey / Fed) — eşikler kullanıcının hedef ay sayısına göre ölçeklenir
    em_target = emergency_target_months
    em_pts = _criterion_score(emergency_fund_months, [
        (em_target * 2, 15),
        (em_target, 12),
        (em_target / 2, 8),
        (1, 4),
        (0, 0),
    ])
    criteria.append({
        'id': 'emergency_fund',
        'name': 'Acil Durum Fonu',
        'source': 'Dave Ramsey & Fed tüketici araştırmaları',
        'your_value': f'{emergency_fund_months:.1f} ay',
        'target': f'{em_target} ay (hedefiniz)',
        'detail': f'Nakit: {format_money(total_cash)} ₺',
        'status': _status_from_score(em_pts, 15),
        'score': em_pts, 'max_score': 15,
        'interpretation': (
            'Acil fon hedefini karşılıyorsunuz.'
            if emergency_fund_months >= em_target else
            f'{max(0, em_target - emergency_fund_months):.0f} ay daha nakit birikimi önerilir.'
        ),
    })

    # 4 — Pasif gelir karşılama (YMYL)
    inc_pts = _criterion_score(income_replacement_pct, [(100, 20), (75, 16), (50, 12), (25, 6), (0, 0)])
    criteria.append({
        'id': 'passive_income',
        'name': 'Pasif Gelir Karşılama',
        'source': 'Your Money or Your Life — Dominguez & Robin',
        'your_value': f'%{min(income_replacement_pct, 999):.1f}',
        'target': (
            f'{format_money(passive_income_benchmark)} ₺/ay (hedefiniz)'
            if assumptions['target_monthly_passive_income']
            else '%100 (crossover point)'
        ),
        'detail': f'Aylık gerçek pasif gelir: {format_money(passive_income_potential)} ₺',
        'status': _status_from_score(inc_pts, 20),
        'score': inc_pts, 'max_score': 20,
        'interpretation': (
            'Crossover noktasını geçtiniz — iş geliri zorunluluğu azalıyor.'
            if income_replacement_pct >= 100 else
            f'Hedefinizin {format_money(max(0, passive_income_benchmark - passive_income_potential))} ₺\'lik kısmı hâlâ aktif gelir gerektiriyor.'
        ),
    })

    # 5 — Güvenli çekim (SWR)
    swr_pct_label = f'%{assumptions["safe_withdrawal_rate"] * 100:.1f}'.rstrip('0').rstrip(',').rstrip('.')
    sw_pts = _criterion_score(
        (safe_withdrawal_monthly / monthly_avg_expenses * 100) if monthly_avg_expenses > 0 else 0,
        [(100, 10), (75, 8), (50, 6), (25, 3), (0, 0)],
    )
    criteria.append({
        'id': 'safe_withdrawal',
        'name': f'Güvenli Çekim ({swr_pct_label} SWR)',
        'source': 'Trinity Study güvenli çekim oranı',
        'your_value': f'{format_money(safe_withdrawal_monthly)} ₺/ay',
        'target': f'{format_money(monthly_avg_expenses)} ₺/ay gider',
        'detail': f'Yıllık {swr_pct_label} portföy çekimi varsayımı',
        'status': _status_from_score(sw_pts, 10),
        'score': sw_pts, 'max_score': 10,
        'interpretation': 'Portföyünüzden sürdürülebilir aylık çekim gücü.',
    })

    # 6 — Borç yükü
    debt_pts = 10 if debt_to_income_pct <= 20 else (7 if debt_to_income_pct <= 36 else (3 if debt_to_income_pct <= 50 else 0))
    criteria.append({
        'id': 'debt_load',
        'name': 'Borç Yükü',
        'source': 'Bankacılık DTI standardı (%36 eşik)',
        'your_value': f'%{debt_to_income_pct:.1f}',
        'target': '%36 altı',
        'detail': f'Toplam yükümlülük: {format_money(total_debts)} ₺',
        'status': _status_from_score(debt_pts, 10),
        'score': debt_pts, 'max_score': 10,
        'interpretation': (
            'Borç yükünüz düşük — yatırıma ayrılabilir kapasite yüksek.'
            if debt_to_income_pct <= 20 else
            'Borç azaltma önceliği FI sürenizi hızlandırır.' if debt_to_income_pct > 36 else
            'Borç seviyesi yönetilebilir aralıkta.'
        ),
    })

    freedom_score = round(sum(c['score'] for c in criteria), 1)

    milestones = [
        {'name': 'Pozitif net değer', 'done': net_worth > 0, 'icon': '💎'},
        {'name': f'{em_target / 2:.0f} ay acil fon', 'done': emergency_fund_months >= em_target / 2, 'icon': '🛡️'},
        {'name': f'{em_target} ay acil fon', 'done': emergency_fund_months >= em_target, 'icon': '🏦'},
        {'name': '%20+ tasarruf oranı', 'done': savings_rate >= 20, 'icon': '💰'},
        {'name': 'FI hedefinin %50\'si', 'done': fi_progress_pct >= 50, 'icon': '📊'},
        {'name': 'Gerçek pasif gelir ≥ giderlerin %50\'si', 'done': income_replacement_pct >= 50, 'icon': '🌊'},
        {'name': 'Finansal bağımsızlık (FIRE)', 'done': is_financially_free, 'icon': '🏆'},
    ]

    interpretation_parts = [
        f"Finansal özgürlük yolculuğunuzda {freedom_stage['name']} aşamasındasınız.",
        f"Son 12 ayda aylık ortalama geliriniz {format_money(monthly_avg_income)} ₺, gideriniz {format_money(monthly_avg_expenses)} ₺.",
    ]
    if fi_number > 0:
        interpretation_parts.append(
            f"{swr_pct_label} çekim kuralına göre FI hedefiniz {format_money(fi_number)} ₺; portföyünüz bunun %{fi_progress_pct:.0f}'ine ulaşmış durumda."
        )
    if years_to_fi is not None and years_to_fi > 0:
        interpretation_parts.append(
            f"Mevcut tasarruf hızınızla tahmini {years_to_fi:.0f} yıl sonra finansal bağımsızlığa ulaşabilirsiniz ({estimated_freedom_date})."
        )
        target_year = assumptions['target_retirement_year']
        if target_year:
            projected_year = datetime.now().year + years_to_fi
            gap = projected_year - target_year
            if gap <= 0:
                interpretation_parts.append(
                    f"Bu, {target_year} hedefinizin {abs(gap):.0f} yıl önündesiniz demektir."
                )
            else:
                interpretation_parts.append(
                    f"Bu, {target_year} hedefinizin {gap:.0f} yıl gerisinde kalıyor; "
                    "tasarruf oranını artırmak veya hedef yılı revize etmek gerekebilir."
                )
    elif is_financially_free:
        interpretation_parts.append("Tebrikler — portföyünüz sürdürülebilir çekim kuralına göre giderlerinizi karşılayacak büyüklükte.")
    elif monthly_savings <= 0:
        interpretation_parts.append("Giderler geliri aşıyor; önce nakit akışı dengesini kurmak kritik öncelik.")

    references = [
        {'title': 'Trinity Study', 'author': 'Cooley, Hubbard & Walz (1998)', 'note': '%4 güvenli çekim oranı'},
        {'title': 'Your Money or Your Life', 'author': 'Dominguez & Robin', 'note': 'Crossover point & yeterlilik'},
        {'title': 'The Millionaire Next Door', 'author': 'Stanley & Danko', 'note': 'Net değer disiplini'},
        {'title': 'The Total Money Makeover', 'author': 'Dave Ramsey', 'note': 'Acil fon basamakları'},
        {'title': 'All Your Worth', 'author': 'Warren & Tyagi', 'note': '50/30/20 bütçe kuralı'},
    ]

    return {
        'net_worth': net_worth,
        'total_assets': total_assets,
        'total_cash': total_cash,
        'total_debts': total_debts,
        'monthly_avg_income': monthly_avg_income,
        'monthly_avg_expenses': monthly_avg_expenses,
        'annual_expenses': annual_expenses,
        'monthly_savings': monthly_savings,
        'total_investments_12m': total_investments,
        'savings_rate': round(savings_rate, 1),
        'expense_coverage_months': round(expense_coverage_months, 1),
        'emergency_fund_months': round(emergency_fund_months, 1),
        'passive_income_potential': round(passive_income_potential, 2),
        'safe_withdrawal_monthly': round(safe_withdrawal_monthly, 2),
        'rental_income_monthly': round(rental_income_monthly, 2),
        'passive_from_roi': 0,
        'fi_number': fi_number,
        'fi_progress_pct': round(fi_progress_pct, 1),
        'income_replacement_pct': round(min(income_replacement_pct, 999), 1),
        'debt_to_income_pct': round(debt_to_income_pct, 1),
        'freedom_score': freedom_score,
        'estimated_freedom_date': estimated_freedom_date,
        'years_to_fi': years_to_fi,
        'is_financially_free': is_financially_free,
        'freedom_stage': freedom_stage,
        'fire_profile': fire_profile,
        'criteria': criteria,
        'milestones': milestones,
        'interpretation': ' '.join(interpretation_parts),
        'references': references,
        'macro_data': macro_data,
        'assumptions': assumptions,
    }
