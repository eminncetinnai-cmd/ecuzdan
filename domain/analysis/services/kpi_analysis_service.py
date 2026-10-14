"""KPI and Financial Health Analysis Service.

Calculates liquidity, debt ratio, savings rate, emergency runway, and financial health score.
"""
from datetime import datetime

from domain.analysis.services.helpers import _apply_tenant, _as_decimal, _safe_percentage
from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer
from models import Asset, RecurringPlan, Transaction
from shared.decimal_precision import to_decimal


def calculate_financial_analysis(tenant_id: str | None = None) -> dict:
    """Kapsamlı finansal analiz hesaplamaları yapar.

    Likidite, borç oranı, tasarruf oranı, dayanıklılık ve finansal skor hesaplar.
    """
    now = datetime.now()

    all_t = _apply_tenant(Transaction.query.filter(Transaction.is_deleted.is_(False)), Transaction, tenant_id).all()
    assets = _apply_tenant(Asset.query, Asset, tenant_id).all()
    debt_plans = _apply_tenant(
        RecurringPlan.query.filter_by(flow_type='Gider'),
        RecurringPlan,
        tenant_id,
    ).all()

    # Temel değerler
    total_asset_val = sum((_as_decimal(a.value) for a in assets), _as_decimal(0))

    # Cash flow analysis excluding transfers (Phase 2)
    cash_flow_tx = [t for t in all_t if not CashFlowAnalyzer.is_transfer(t)]
    actual_cash = sum(
        (_as_decimal(t.amount) if t.type == 'Gelir' else -_as_decimal(t.amount) for t in cash_flow_tx if t.status == 'Ödendi'),
        _as_decimal(0),
    )

    total_servet = total_asset_val + actual_cash

    from decimal import Decimal

    def _calc_plan_debt(p):
        if getattr(p, 'status', None) in ('Tamamlandı', 'İptal', 'Durduruldu'):
            return _as_decimal(0)
        if getattr(p, 'plan_type', None) in ('Abonelik', 'Kira'):
            return _as_decimal(0)
        if getattr(p, 'is_indefinite', None) is True:
            return _as_decimal(0)
        rem = getattr(p, 'remaining_total_amount', None)
        if isinstance(rem, (int, float, Decimal)):
            return _as_decimal(rem)
        inst = getattr(p, 'installments', 0) or 0
        try:
            inst_val = int(inst)
        except (TypeError, ValueError):
            inst_val = 0
        if inst_val <= 0:
            return _as_decimal(0)
        try:
            amt_val = _as_decimal(p.amount or 0)
        except (TypeError, ValueError):
            amt_val = _as_decimal(0)
        return amt_val * inst_val

    total_debt = sum((_calc_plan_debt(p) for p in debt_plans), _as_decimal(0))

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

    return {
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
