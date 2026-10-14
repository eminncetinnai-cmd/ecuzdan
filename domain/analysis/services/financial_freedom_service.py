"""Financial Freedom and FIRE Analysis Service.

Calculates multi-criteria financial independence metrics based on Trinity Study,
Ramsey emergency fund thresholds, Warren 50/30/20, and FIRE mathematics.
"""
import logging
from datetime import datetime, timedelta

from domain.analysis.services.helpers import _apply_tenant, _as_decimal, _safe_percentage
from infrastructure.database.financial_db_service import get_actual_cash, get_total_assets, get_total_debts
from models import Asset, Transaction
from shared.decimal_precision import to_decimal
from utils.format_utils import format_money

logger = logging.getLogger(__name__)

# --- Finansal Özgürlük (FIRE) sabitleri — akademik referanslar ---
FI_MULTIPLIER = 25          # Trinity Study / 4% güvenli çekim kuralı (Bengen, 1994)
SAFE_WITHDRAWAL_RATE = 0.04  # %4 yıllık portföy çekimi
REAL_RETURN_RATE = 0.07     # Uzun vadeli reel getiri varsayımı (%7) - dinamik olarak güncellenebilir
DEFAULT_EMERGENCY_FUND_MONTHS = 6  # Ramsey / Fed: 3-6 ay; muhafazakâr hedef 6 ay


def _resolve_freedom_assumptions(preferences):
    """Kullanıcı tercihlerini analiz varsayımlarına çevirir.

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
    """Dinamik reel getiri oranını piyasa verisinden çeker.

    Varsayılan %7, piyasa verisi varsa güncel değer kullanılır.
    """
    try:
        from market_data_service import get_macro_economic_data
        macro_data = get_macro_economic_data()
        if macro_data and 'real_return_rate' in macro_data:
            return macro_data['real_return_rate'] / 100  # %'yi decimal'e çevir
    except Exception as e:
        logger.warning(f"Dynamic return rate fetch failed, using default: {e}")
    return REAL_RETURN_RATE


def _years_to_financial_independence(
    portfolio,
    monthly_savings,
    monthly_expenses,
    annual_return=None,
    fi_multiplier=FI_MULTIPLIER,
):
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


def calculate_financial_freedom_analysis(tenant_id=None, preferences=None):
    """Finansal özgürlük analizi — küresel FIRE/FI literatürüne dayalı çok kriterli değerlendirme.

    preferences: UserPreference satırı (opsiyonel). Verilmezse ya da alanları
    boşsa modül sabitleri (Trinity %4, 6 ay acil fon) kullanılır.
    """
    assumptions = _resolve_freedom_assumptions(preferences)
    swr_decimal = to_decimal(assumptions['safe_withdrawal_rate'], scale=4)
    fi_multiplier_decimal = to_decimal(assumptions['fi_multiplier'], scale=4)
    emergency_target_months = assumptions['emergency_fund_target_months']
    twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    recent_query = Transaction.query.filter(
        Transaction.date >= twelve_months_ago,
        Transaction.status == 'Ödendi',
        Transaction.is_deleted.is_(False),
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
