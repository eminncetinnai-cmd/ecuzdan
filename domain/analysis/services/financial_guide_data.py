"""
Financial Literacy Learning Guide Data Module
Finansal Okuryazarlık Öğrenme Rehberi Veri Modülü

Bu modül, başlangıçtan ileri seviyeye kadar finansal eğitim içeriğini içerir.
Her konu için: konsept tanımı, pratik örnek, matematiksel formül, Python fonksiyonu ve edebi görüşler.
"""

import math
from typing import Any, Callable, Dict

# ============ MATHEMATICAL FORMULA FUNCTIONS ============

def calculate_compound_interest(principal: float, annual_rate: float, times_per_year: int, years: int) -> float:
    """
    Bileşik faiz hesapla
    A = P(1 + r/n)^(nt)

    Args:
        principal: Ana para (P)
        annual_rate: Yıllık faiz oranı (r) - örn: 0.08 için %8
        times_per_year: Yılda bileşikleşme sayısı (n)
        years: Yıl sayısı (t)

    Returns:
        Final amount (A)
    """
    return principal * (1 + annual_rate / times_per_year) ** (times_per_year * years)


def calculate_simple_interest(principal: float, annual_rate: float, years: int) -> float:
    """
    Basit faiz hesapla
    I = P * r * t

    Args:
        principal: Ana para (P)
        annual_rate: Yıllık faiz oranı (r)
        years: Yıl sayısı (t)

    Returns:
        Interest amount (I)
    """
    return principal * annual_rate * years


def calculate_financial_independence_number(annual_expenses: float, withdrawal_rate: float = 0.04) -> float:
    """
    Finansal Bağımsızlık Sayısını hesapla (4% Kuralı)
    FI Number = Annual Expenses / Withdrawal Rate

    Args:
        annual_expenses: Yıllık harcamalar
        withdrawal_rate: Çekim oranı (varsayılan: 0.04 için %4)

    Returns:
        Required portfolio value
    """
    return annual_expenses / withdrawal_rate


def calculate_dollar_cost_averaging(monthly_investment: float, periods: int, prices: list) -> Dict[str, Any]:
    """
    Dolar Maliyet Ortalaması (DCA) hesapla

    Args:
        monthly_investment: Aylık yatırım tutarı
        periods: Dönem sayısı
        prices: Her dönemin fiyat listesi

    Returns:
        Dictionary with total invested, total shares, average cost
    """
    total_invested = monthly_investment * periods
    total_shares = sum(monthly_investment / price for price in prices)
    average_cost = total_invested / total_shares if total_shares > 0 else 0

    return {
        'total_invested': total_invested,
        'total_shares': total_shares,
        'average_cost': average_cost
    }


def calculate_rule_of_72(annual_rate: float) -> float:
    """
    72 Kuralı: Paranın ikiye katlanması için gereken yıl sayısı
    Years = 72 / Annual Rate (%)

    Args:
        annual_rate: Yıllık faiz oranı (örn: 8 için %8)

    Returns:
        Years to double
    """
    return 72 / annual_rate if annual_rate > 0 else float('inf')


def calculate_50_30_20_budget(monthly_income: float) -> Dict[str, float]:
    """
    50/30/20 Bütçe Kuralı hesapla
    - %50 İhtiyaçlar (Needs)
    - %30 İstekler (Wants)
    - %20 Tasarruf/Yatırım (Savings)

    Args:
        monthly_income: Aylık gelir

    Returns:
        Dictionary with needs, wants, savings amounts
    """
    return {
        'needs': monthly_income * 0.50,
        'wants': monthly_income * 0.30,
        'savings': monthly_income * 0.20
    }


def calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.02) -> float:
    """
    Sharpe Oranı hesapla (Risk ayarlı getiri)
    Sharpe = (Portfolio Return - Risk Free Rate) / Portfolio Std Dev

    Args:
        returns: Portföy getirileri listesi
        risk_free_rate: Risksiz faiz oranı

    Returns:
        Sharpe ratio
    """
    if not returns:
        return 0.0

    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = math.sqrt(variance)

    return (avg_return - risk_free_rate) / std_dev if std_dev > 0 else 0.0


def calculate_inflation_adjusted_return(nominal_return: float, inflation_rate: float) -> float:
    """
    Enflasyon ayarlı reel getiri hesapla
    Real Return = (1 + Nominal) / (1 + Inflation) - 1

    Args:
        nominal_return: Nominal getiri
        inflation_rate: Enflasyon oranı

    Returns:
        Real return
    """
    return (1 + nominal_return) / (1 + inflation_rate) - 1


def calculate_bes_return(contribution: float, employer_match: float, annual_return: float, years: int) -> float:
    """
    BES (Bireysel Emeklilik Sistemi) getirisi hesapla
    Args:
        contribution: Aylık katkı payı
        employer_match: İşveren katkısı (örn: 0.25 için %25)
        annual_return: Yıllık getiri
        years: Yıl sayısı
    Returns:
        Final amount
    """
    monthly_contribution = contribution * (1 + employer_match)
    monthly_rate = annual_return / 12
    months = years * 12
    return monthly_contribution * ((1 + monthly_rate) ** months - 1) / monthly_rate


def calculate_mutual_fund_return(initial_investment: float, monthly_contribution: float, annual_return: float, expense_ratio: float, years: int) -> float:
    """
    Yatırım fonu getirisi hesapla (gider kesintisi dahil)
    Args:
        initial_investment: Başlangıç yatırımı
        monthly_contribution: Aylık katkı
        annual_return: Yıllık getiri
        expense_ratio: Gider oranı (örn: 0.01 için %1)
        years: Yıl sayısı
    Returns:
        Final amount
    """
    net_return = annual_return - expense_ratio
    initial_growth = initial_investment * (1 + net_return) ** years
    monthly_rate = net_return / 12
    months = years * 12
    monthly_growth = monthly_contribution * ((1 + monthly_rate) ** months - 1) / monthly_rate
    return initial_growth + monthly_growth


def calculate_bond_yield(face_value: float, coupon_rate: float, current_price: float, years_to_maturity: int) -> float:
    """
    Tahvil getirisi (YTM) hesapla
    Args:
        face_value: Nominal değer
        coupon_rate: Kupon oranı
        current_price: Mevcut fiyat
        years_to_maturity: Vadeye kalan yıl
    Returns:
        Yield to maturity
    """
    annual_coupon = face_value * coupon_rate
    total_coupons = annual_coupon * years_to_maturity
    total_return = (total_coupons + face_value - current_price) / years_to_maturity
    return total_return / ((face_value + current_price) / 2)


def calculate_commodity_future_price(spot_price: float, risk_free_rate: float, storage_cost: float, time_to_maturity: float) -> float:
    """
    Emtia vadeli işlem fiyatı hesapla
    Args:
        spot_price: Spot fiyat
        risk_free_rate: Risksiz faiz oranı
        storage_cost: Depolama maliyeti
        time_to_maturity: Vadeye kalan yıl
    Returns:
        Future price
    """
    return spot_price * math.exp((risk_free_rate + storage_cost) * time_to_maturity)


def calculate_portfolio_beta(asset_weights: list, asset_betas: list) -> float:
    """
    Portföy beta katsayısı hesapla
    Args:
        asset_weights: Varlık ağırlıkları listesi
        asset_betas: Varlık beta katsayıları listesi
    Returns:
        Portfolio beta
    """
    return sum(w * b for w, b in zip(asset_weights, asset_betas))


def calculate_capm_return(risk_free_rate: float, beta: float, market_return: float) -> float:
    """
    CAPM (Capital Asset Pricing Model) beklenen getiri hesapla
    E(R) = Rf + β × (Rm - Rf)
    Args:
        risk_free_rate: Risksiz faiz oranı
        beta: Beta katsayısı
        market_return: Piyasa getirisi
    Returns:
        Expected return
    """
    return risk_free_rate + beta * (market_return - risk_free_rate)


def calculate_sortino_ratio(returns: list, risk_free_rate: float = 0.02) -> float:
    """
    Sortino Oranı hesapla (negatif varyans için risk ayarlı getiri)
    Args:
        returns: Portföy getirileri listesi
        risk_free_rate: Risksiz faiz oranı
    Returns:
        Sortino ratio
    """
    if not returns:
        return 0.0

    avg_return = sum(returns) / len(returns)
    downside_returns = [r for r in returns if r < risk_free_rate]

    if not downside_returns:
        return float('inf') if avg_return > risk_free_rate else 0.0

    downside_variance = sum((r - risk_free_rate) ** 2 for r in downside_returns) / len(downside_returns)
    downside_deviation = math.sqrt(downside_variance)

    return (avg_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0.0


def calculate_information_ratio(portfolio_returns: list, benchmark_returns: list) -> float:
    """
    Information Ratio hesapla (benchmark'a göre aşırı getiri)
    Args:
        portfolio_returns: Portföy getirileri
        benchmark_returns: Benchmark getirileri
    Returns:
        Information ratio
    """
    if len(portfolio_returns) != len(benchmark_returns) or not portfolio_returns:
        return 0.0

    excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
    avg_excess = sum(excess_returns) / len(excess_returns)
    tracking_error = math.sqrt(sum((r - avg_excess) ** 2 for r in excess_returns) / len(excess_returns))

    return avg_excess / tracking_error if tracking_error > 0 else 0.0


def calculate_value_at_risk(returns: list, confidence_level: float = 0.95) -> float:
    """
    Value at Risk (VaR) hesapla
    Args:
        returns: Portföy getirileri
        confidence_level: Güven seviyesi (örn: 0.95 için %95)
    Returns:
        VaR değeri
    """
    if not returns:
        return 0.0

    sorted_returns = sorted(returns)
    index = int((1 - confidence_level) * len(sorted_returns))
    return sorted_returns[index] if index < len(sorted_returns) else sorted_returns[-1]


def calculate_max_drawdown(prices: list) -> float:
    """
    Maksimum düşüş (Max Drawdown) hesapla
    Args:
        prices: Fiyat listesi
    Returns:
        Max drawdown (negatif değer)
    """
    if not prices:
        return 0.0

    peak = prices[0]
    max_dd = 0.0

    for price in prices:
        if price > peak:
            peak = price
        dd = (price - peak) / peak
        if dd < max_dd:
            max_dd = dd

    return max_dd


# ============ GUIDE DATA STRUCTURE ============

# Program-specific calculations and analyses
PROGRAM_CALCULATIONS = {
    'financial_health': {
        'tr': {
            'title': 'Finansal Sağlık Analizi',
            'calculations': [
                {
                    'name': 'Likidite Oranı',
                    'formula': 'Likidite = Mevcut Nakit / Aylık Giderler',
                    'description': 'Kısa vadeli harcamalarınızı karşılayabilme yeteneğinizi gösterir. 1.5 ve üzeri mükemmel, 1.0 sınırda, altı kritik risk.',
                    'purpose': 'Bu hesaplama, acil durumlar veya beklenmedik harcamalar için ne kadar nakit rezerviniz olduğunu değerlendirmenize yardımcı olur. Likidite oranınızı izleyerek, finansal güvenliğinizi sağlamak için gereken nakit seviyesini belirleyebilirsiniz.'
                },
                {
                    'name': 'Borç Oranı',
                    'formula': 'Borç Oranı = (Toplam Borç / Toplam Servet) × 100',
                    'description': 'Borç yükünüzün servetinize oranını gösterir. %30 altı sağlıklı, %30-40 dikkat, %40 üzeri yüksek risk.',
                    'purpose': 'Bu oran, finansal sağlığınızı değerlendirmek için kritik bir göstergedir. Borç oranınızı izleyerek, borç yönetimi stratejilerinizi geliştirebilir ve gelecekteki finansal hedeflerinize ulaşmak için daha iyi planlama yapabilirsiniz.'
                },
                {
                    'name': 'Tasarruf Oranı',
                    'formula': 'Tasarruf Oranı = ((Gelir - Gider) / Gelir) × 100',
                    'description': 'Gelirinizin ne kadarını tasarruf ettiğinizi gösterir. %20+ harika, %0-20 orta, negatif bütçe açığı.',
                    'purpose': 'Tasarruf oranı, finansal özgürlüğe giden yolda en önemli göstergedir. Bu oranı izleyerek, tasarruf alışkanlıklarınızı geliştirebilir ve uzun vadeli finansal hedeflerinize ulaşmak için gerekli disiplini kazanabilirsiniz.'
                },
                {
                    'name': 'Dayanıklılık (Sürdürülebilirlik)',
                    'formula': 'Dayanıklılık = Nakit / (Günlük Gider)',
                    'description': 'Gelirsiz ne kadar süre yaşayabileceğinizi gösterir. 6+ ay güvenli, 3-6 ay yeterli, 3 ay altı kırılgan.',
                    'purpose': 'Bu hesaplama, iş kaybı veya acil durumlar gibi finansal krizlere karşı dayanıklılığınızı ölçmenize yardımcı olur. Dayanıklılık sürenizi bilmek, acil fon hedefinizi belirlemenize ve finansal güvenliğinizi sağlamanıza olanak tanır.'
                },
                {
                    'name': 'Finansal Skor',
                    'formula': 'Skor = 100 - (Borç Oranı × 1.5) + (Tasarruf Oranı × 0.5)',
                    'description': 'Genel finansal sağlığınızı 0-100 arası gösterir. 75+ çok iyi, 50-75 stabil, 50 altı riskli.',
                    'purpose': 'Finansal skor, finansal sağlığınızın genel bir resmini sunar ve iyileştirme alanlarını belirlemenize yardımcı olur. Bu skoru takip ederek, finansal kararlarınızın etkisini izleyebilir ve zaman içinde finansal durumunuzu iyileştirebilirsiniz.'
                }
            ]
        },
        'en': {
            'title': 'Financial Health Analysis',
            'calculations': [
                {
                    'name': 'Liquidity Ratio',
                    'formula': 'Liquidity = Current Cash / Monthly Expenses',
                    'description': 'Shows your ability to cover short-term expenses. 1.5+ excellent, 1.0 borderline, below critical risk.',
                    'purpose': 'This calculation helps you evaluate how much cash reserve you have for emergencies or unexpected expenses. By monitoring your liquidity ratio, you can determine the cash level needed to maintain financial security.'
                },
                {
                    'name': 'Debt Ratio',
                    'formula': 'Debt Ratio = (Total Debt / Total Wealth) × 100',
                    'description': 'Shows your debt load relative to wealth. Below 30% healthy, 30-40 caution, above 40% high risk.',
                    'purpose': 'This ratio is a critical indicator for assessing your financial health. By monitoring your debt ratio, you can develop debt management strategies and better plan to achieve your future financial goals.'
                },
                {
                    'name': 'Savings Rate',
                    'formula': 'Savings Rate = ((Income - Expenses) / Income) × 100',
                    'description': 'Shows what portion of income you save. 20%+ excellent, 0-20 medium, negative budget deficit.',
                    'purpose': 'Savings rate is the most important indicator on the path to financial freedom. By monitoring this rate, you can develop savings habits and gain the discipline needed to achieve long-term financial goals.'
                },
                {
                    'name': 'Sustainability',
                    'formula': 'Sustainability = Cash / (Daily Expenses)',
                    'description': 'Shows how long you can live without income. 6+ months secure, 3-6 months adequate, below 3 months fragile.',
                    'purpose': 'This calculation helps you measure your resilience against financial crises such as job loss or emergencies. Knowing your sustainability duration allows you to set emergency fund targets and ensure your financial security.'
                },
                {
                    'name': 'Financial Score',
                    'formula': 'Score = 100 - (Debt Ratio × 1.5) + (Savings Rate × 0.5)',
                    'description': 'Shows overall financial health 0-100. 75+ very good, 50-75 stable, below 50 risky.',
                    'purpose': 'Financial score provides a general picture of your financial health and helps identify areas for improvement. By tracking this score, you can monitor the impact of your financial decisions and improve your financial situation over time.'
                }
            ]
        }
    },
    'asset_analysis': {
        'tr': {
            'title': 'Varlık Portföy Analizi',
            'calculations': [
                {
                    'name': 'Toplam Portföy Değeri',
                    'formula': 'Toplam Değer = Σ(Tüm Varlık Değerleri)',
                    'description': 'Portföyünüzün toplam piyasa değeri.',
                    'purpose': 'Bu hesaplama, portföyünüzün mevcut piyasa değerini gösterir ve yatırım performansınızı takip etmenize yardımcı olur. Toplam portföy değerini izleyerek, zaman içindeki büyümenizi ölçebilir ve yatırım kararlarınızın etkisini değerlendirebilirsiniz.'
                },
                {
                    'name': 'Toplam Maliyet',
                    'formula': 'Toplam Maliyet = Σ(Tüm Varlık Maliyetleri)',
                    'description': 'Varlıkları satın almak için harcadığınız toplam tutar.',
                    'purpose': 'Bu hesaplama, yatırımlarınız için harcadığınız toplam sermayeyi gösterir ve yatırım verimliliğinizi ölçmenize yardımcı olur. Toplam maliyeti bilerek, gerçek getiri oranlarınızı hesaplayabilir ve yatırım stratejilerinizi optimize edebilirsiniz.'
                },
                {
                    'name': 'Toplam Kar/Zarar',
                    'formula': 'Kar/Zarar = Toplam Değer - Toplam Maliyet',
                    'description': 'Portföyünüzün toplam unrealized karı veya zararı.',
                    'purpose': 'Bu hesaplama, portföyünüzün mevcut kar veya zarar durumunu gösterir ve yatırım performansınızı değerlendirmenize yardımcı olur. Kar/zarar durumunu izleyerek, hangi yatırımların başarılı olduğunu belirleyebilir ve portföyünüzü gerektiğinde yeniden dengeleyebilirsiniz.'
                },
                {
                    'name': 'Genel ROI',
                    'formula': 'ROI = (Kar/Zarar / Toplam Maliyet) × 100',
                    'description': 'Portföyünüzün genel getiri oranı.',
                    'purpose': 'ROI, yatırımınızın verimliliğini ölçen en önemli göstergedir. Bu oranı izleyerek, yatırım performansınızı değerlendirebilir ve farklı varlık sınıflarının getirisini karşılaştırarak daha iyi yatırım kararları alabilirsiniz.'
                },
                {
                    'name': 'Portföy Ağırlığı',
                    'formula': 'Ağırlık = (Varlık Değeri / Toplam Portföy Değeri) × 100',
                    'description': 'Her varlığın portföydeki yüzdesi. %20 üzeri konsantrasyon riski oluşturur.',
                    'purpose': 'Bu hesaplama, portföy çeşitlendirmenizi değerlendirmenize yardımcı olur. Varlık ağırlıklarını izleyerek, konsantrasyon riskini azaltabilir ve portföyünüzü daha dengeli hale getirebilirsiniz.'
                },
                {
                    'name': 'Risk Skoru',
                    'formula': 'Risk Skoru = Yüksek Risk Ağırlığı × 30 + Orta Risk Ağırlığı × 20 + Konsantrasyon Riski × 25 + İlik Likidite × 15',
                    'description': 'Portföy risk seviyesi 0-100. 30 altı düşük, 30-60 orta, 60 üzeri yüksek risk.',
                    'purpose': 'Risk skoru, portföyünüzün genel risk profilini gösterir ve risk yönetimi stratejilerinizi geliştirmenize yardımcı olur. Bu skoru izleyerek, risk seviyenizi yönetebilir ve yatırım hedeflerinize uygun risk seviyesini koruyabilirsiniz.'
                },
                {
                    'name': 'Likidite Skoru',
                    'formula': 'Likidite Skoru = Likit Ağırlık + Yarı-Likit Ağırlık × 0.5',
                    'description': 'Portföyünüzün ne kadar hızlı nakde çevrilebileceğini gösterir. 70+ yüksek, 40-70 orta, 40 altı düşük.',
                    'purpose': 'Likidite skoru, portföyünüzün nakde dönüştürülebilirliğini gösterir ve acil durumlar için finansal esnekliğinizi değerlendirmenize yardımcı olur. Bu skoru izleyerek, portföyünüzün likiditesini optimize edebilir ve gerektiğinde hızlı nakde erişim sağlayabilirsiniz.'
                }
            ]
        },
        'en': {
            'title': 'Asset Portfolio Analysis',
            'calculations': [
                {
                    'name': 'Total Portfolio Value',
                    'formula': 'Total Value = Σ(All Asset Values)',
                    'description': 'Total market value of your portfolio.',
                    'purpose': 'This calculation shows the current market value of your portfolio and helps you track your investment performance. By monitoring total portfolio value, you can measure your growth over time and evaluate the impact of your investment decisions.'
                },
                {
                    'name': 'Total Cost',
                    'formula': 'Total Cost = Σ(All Asset Costs)',
                    'description': 'Total amount spent to purchase assets.',
                    'purpose': 'This calculation shows the total capital you invested and helps you measure investment efficiency. By knowing total cost, you can calculate true return rates and optimize your investment strategies.'
                },
                {
                    'name': 'Total Gain/Loss',
                    'formula': 'Gain/Loss = Total Value - Total Cost',
                    'description': 'Total unrealized profit or loss of your portfolio.',
                    'purpose': 'This calculation shows the current profit or loss status of your portfolio and helps evaluate investment performance. By monitoring gain/loss status, you can identify which investments are successful and rebalance your portfolio when needed.'
                },
                {
                    'name': 'Overall ROI',
                    'formula': 'ROI = (Gain/Loss / Total Cost) × 100',
                    'description': 'Overall return rate of your portfolio.',
                    'purpose': 'ROI is the most important indicator measuring investment efficiency. By monitoring this rate, you can evaluate investment performance and make better investment decisions by comparing returns across different asset classes.'
                },
                {
                    'name': 'Portfolio Weight',
                    'formula': 'Weight = (Asset Value / Total Portfolio Value) × 100',
                    'description': 'Percentage of each asset in portfolio. Above 20% creates concentration risk.',
                    'purpose': 'This calculation helps you evaluate portfolio diversification. By monitoring asset weights, you can reduce concentration risk and make your portfolio more balanced.'
                },
                {
                    'name': 'Risk Score',
                    'formula': 'Risk Score = High Risk Weight × 30 + Medium Risk Weight × 20 + Concentration Risk × 25 + Illiquid Liquidity × 15',
                    'description': 'Portfolio risk level 0-100. Below 30 low, 30-60 medium, above 60 high risk.',
                    'purpose': 'Risk score shows the overall risk profile of your portfolio and helps develop risk management strategies. By monitoring this score, you can manage your risk level and maintain a risk level appropriate to your investment goals.'
                },
                {
                    'name': 'Liquidity Score',
                    'formula': 'Liquidity Score = Liquid Weight + Semi-Liquid Weight × 0.5',
                    'description': 'Shows how quickly your portfolio can be converted to cash. 70+ high, 40-70 medium, below 40 low.',
                    'purpose': 'Liquidity score shows the convertibility of your portfolio to cash and helps evaluate your financial flexibility for emergencies. By monitoring this score, you can optimize portfolio liquidity and ensure quick access to cash when needed.'
                }
            ]
        }
    },
    'fire_analysis': {
        'tr': {
            'title': 'Finansal Özgürlük (FIRE) Analizi',
            'calculations': [
                {
                    'name': 'Net Değer',
                    'formula': 'Net Değer = Toplam Varlıklar + Nakit - Toplam Borçlar',
                    'description': 'Gerçek servetiniz. Pozitif net değer finansal sağlığın temelidir.',
                    'purpose': 'Net değer, finansal sağlığınızın temel göstergesidir. Bu hesaplama, gerçek servetinizi gösterir ve finansal özgürlük yolculuğunuzda ne kadar ilerlediğinizi değerlendirmenize yardımcı olur.'
                },
                {
                    'name': 'FI Sayısı (25× Kuralı)',
                    'formula': 'FI Sayısı = Yıllık Giderler × 25',
                    'description': 'Trinity Study\'e göre finansal bağımsızlık için gereken portföy büyüklüğü. 4% güvenli çekim kuralına dayanır.',
                    'purpose': 'FI sayısı, finansal bağımsızlık hedefinizi belirlemenize yardımcı olur. Bu hesaplama, emeklilik için gereken portföy büyüklüğünü gösterir ve tasarruf hedeflerinizi planlamanıza olanak tanır.'
                },
                {
                    'name': 'FI İlerleme',
                    'formula': 'İlerleme = (Yatırılabilir Varlıklar / FI Sayısı) × 100',
                    'description': 'FI hedefine ne kadar yaklaştığınızı gösterir.',
                    'purpose': 'FI ilerleme oranı, finansal bağımsızlık yolculuğunuzda ne kadar ilerlediğinizi gösterir. Bu göstergeleri izleyerek, hedefinize ulaşmak için gereken süreyi ve çabayı değerlendirebilirsiniz.'
                },
                {
                    'name': 'Tasarruf Oranı',
                    'formula': 'Tasarruf Oranı = ((Gelir - Gider) / Gelir) × 100',
                    'description': 'FIRE hızınızı belirleyen en önemli faktör. %20+ ideal, %50+ hızlı mod.',
                    'purpose': 'Tasarruf oranı, FIRE hızınızı belirleyen en kritik faktördür. Bu oranı izleyerek, finansal bağımsızlığa ne zaman ulaşabileceğinizi tahmin edebilir ve tasarruf stratejilerinizi optimize edebilirsiniz.'
                },
                {
                    'name': 'Pasif Gelir Potansiyeli',
                    'formula': 'Pasif Gelir = max(Portföy × 4% / 12, ROI Geliri)',
                    'description': 'Portföyünüzden aylık çekebileceğiniz güvenli tutar.',
                    'purpose': 'Pasif gelir potansiyeli, portföyünüzden güvenli bir şekilde çekebileceğiniz aylık tutarı gösterir. Bu hesaplama, finansal bağımsızlık sonrası yaşam standartınızı planlamanıza yardımcı olur.'
                },
                {
                    'name': 'Gelir Karşılama Oranı',
                    'formula': 'Karşılama = (Pasif Gelir / Aylık Giderler) × 100',
                    'description': 'Pasif geliriniz giderlerinizi ne kadar karşılıyor. %100 crossover point.',
                    'purpose': 'Gelir karşılama oranı, pasif gelirinizin yaşam giderlerinizi ne kadar karşıladığını gösterir. Bu oranı izleyerek, finansal bağımsızlığa ne kadar yaklaştığınızı değerlendirebilir ve crossover noktasını belirleyebilirsiniz.'
                },
                {
                    'name': 'Acil Fon (Ay)',
                    'formula': 'Acil Fon = Nakit / Aylık Giderler',
                    'description': 'Gelirsiz ne kadar süre yaşayabilirsiniz. 3-6 ay hedef, 12 ay muhafazakâr.',
                    'purpose': 'Acil fon, finansal güvenliğinizin temelidir. Bu hesaplama, iş kaybı veya acil durumlar gibi finansal krizlere karşı dayanıklılığınızı gösterir ve acil fon hedefinizi belirlemenize yardımcı olur.'
                },
                {
                    'name': 'FI\'ye Kalan Yıl',
                    'formula': 'Yıl = Bileşik Getiri + Düzenli Birikim ile FI Hedefine Kalan Yıl',
                    'description': 'Mevcut tasarruf hızıyla FI\'ye ne kadar süre kaldığı.',
                    'purpose': 'FI\'ye kalan yıl, finansal bağımsızlığa ne zaman ulaşabileceğinizi tahmin eder. Bu hesaplama, mevcut tasarruf hızınızla hedefinize ulaşmak için gereken süreyi gösterir ve motivasyon sağlar.'
                },
                {
                    'name': 'Finansal Özgürlük Skoru',
                    'formula': 'Skor = Σ(Kriter Puanları) - 100 puan üzerinden',
                    'description': 'FI yolculuğunuzda ilerlemenizi gösterir. 6 kriter: FI hedefi, tasarruf, acil fon, pasif gelir, güvenli çekim, borç yükü.',
                    'purpose': 'Finansal özgürlük skoru, FI yolculuğunuzda genel ilerlemenizi gösterir. Bu skoru izleyerek, güçlü ve zayıf yönlerinizi belirleyebilir ve finansal stratejilerinizi buna göre optimize edebilirsiniz.'
                }
            ]
        },
        'en': {
            'title': 'Financial Independence (FIRE) Analysis',
            'calculations': [
                {
                    'name': 'Net Worth',
                    'formula': 'Net Worth = Total Assets + Cash - Total Debts',
                    'description': 'Your true wealth. Positive net worth is foundation of financial health.',
                    'purpose': 'Net worth is the fundamental indicator of your financial health. This calculation shows your true wealth and helps evaluate how far you have progressed on your financial freedom journey.'
                },
                {
                    'name': 'FI Number (25× Rule)',
                    'formula': 'FI Number = Annual Expenses × 25',
                    'description': 'Portfolio size needed for financial independence per Trinity Study. Based on 4% safe withdrawal rule.',
                    'purpose': 'FI number helps you determine your financial independence target. This calculation shows the portfolio size needed for retirement and allows you to plan your savings goals.'
                },
                {
                    'name': 'FI Progress',
                    'formula': 'Progress = (Investable Assets / FI Number) × 100',
                    'description': 'Shows how close you are to FI target.',
                    'purpose': 'FI progress rate shows how far you have progressed on your financial independence journey. By monitoring these indicators, you can evaluate the time and effort needed to reach your target.'
                },
                {
                    'name': 'Savings Rate',
                    'formula': 'Savings Rate = ((Income - Expenses) / Income) × 100',
                    'description': 'Most important factor determining FIRE speed. 20%+ ideal, 50%+ fast mode.',
                    'purpose': 'Savings rate is the most critical factor determining your FIRE speed. By monitoring this rate, you can predict when you will reach financial independence and optimize your savings strategies.'
                },
                {
                    'name': 'Passive Income Potential',
                    'formula': 'Passive Income = max(Portfolio × 4% / 12, ROI Income)',
                    'description': 'Safe monthly amount you can withdraw from portfolio.',
                    'purpose': 'Passive income potential shows the safe monthly amount you can withdraw from your portfolio. This calculation helps you plan your standard of living after financial independence.'
                },
                {
                    'name': 'Income Replacement Ratio',
                    'formula': 'Replacement = (Passive Income / Monthly Expenses) × 100',
                    'description': 'How much of your expenses passive income covers. 100% is crossover point.',
                    'purpose': 'Income replacement ratio shows how much of your living expenses your passive income covers. By monitoring this ratio, you can evaluate how close you are to financial independence and identify the crossover point.'
                },
                {
                    'name': 'Emergency Fund (Months)',
                    'formula': 'Emergency Fund = Cash / Monthly Expenses',
                    'description': 'How long you can live without income. 3-6 months target, 12 months conservative.',
                    'purpose': 'Emergency fund is the foundation of your financial security. This calculation shows your resilience against financial crises such as job loss or emergencies and helps you set your emergency fund target.'
                },
                {
                    'name': 'Years to FI',
                    'formula': 'Years = Compound Return + Regular Savings to FI Target',
                    'description': 'How long until FI at current savings rate.',
                    'purpose': 'Years to FI predicts when you will reach financial independence. This calculation shows the time needed to reach your target at your current savings rate and provides motivation.'
                },
                {
                    'name': 'Financial Freedom Score',
                    'formula': 'Score = Σ(Criteria Points) - out of 100',
                    'description': 'Shows your progress on FI journey. 6 criteria: FI target, savings, emergency fund, passive income, safe withdrawal, debt load.',
                    'purpose': 'Financial freedom score shows your overall progress on your FI journey. By monitoring this score, you can identify your strengths and weaknesses and optimize your financial strategies accordingly.'
                }
            ]
        }
    }
}

TECHNICAL_TERMS = {
    'tr': {
        'title': 'Teknik Terimler Sözlüğü',
        'terms': [
            {
                'term': 'FI (Financial Independence)',
                'definition': 'Finansal Bağımsızlık. Çalışmak zorunda kalmadan yaşam giderlerinizi karşılayacak kadar pasif gelire sahip olma durumu. Bu durum, iş gelirine bağımlı olmadan yaşam standartınızı sürdürmenizi sağlar ve zaman özgürlüğü kazandırır. Finansal bağımsızlık, pasif gelir kaynaklarının (kira, temettü, faiz, portföy çekimi) yaşam giderlerinizi tamamen karşıladığı noktadır.',
                'context': 'FI hedefine ulaşmak için yıllık giderlerinizin 25 katı kadar birikim gereklidir (4% kuralı). Bu hedef, Trinity Study çalışmasına dayanır ve 30 yıllık emeklilik döneminde %95 başarı şansı sunar. FI sayısına ulaştığınızda, çalışma zorunluluğu ortadan kalkar ve yaşam tarzınızı tamamen kontrol edebilirsiniz.'
            },
            {
                'term': 'FIRE (Financial Independence, Retire Early)',
                'definition': 'Finansal Bağımsızlık ve Erken Emeklilik. Tasarruf ve yatırımla erken yaşta çalışmadan yaşama hareketi. Bu hareket, yüksek tasarruf oranları (%50+), akıllı yatırımlar ve minimalist yaşam tarzı ile geleneksel emeklilik yaşından önce finansal özgürlüğe ulaşmayı hedefler. FIRE, sadece emeklilik değil, zaman özgürlüğü ve yaşam seçeneklerini artırmak üzerine kuruludur.',
                'context': 'FIRE türleri: Traditional FIRE (tam bağımsızlık), Barista FIRE (kısmi çalışma), Coast FIRE (bileşik faizle büyüme), Lean FIRE (düşük gider). Her tür, farklı risk toleranslarına ve yaşam tarzı tercihlerine göre tasarlanmıştır. FIRE hareketi, finansal bağımsızlığa ulaşmanın farklı yollarını sunar ve kişisel hedeflere göre esneklik sağlar.'
            },
            {
                'term': '4% Kuralı (Safe Withdrawal Rate)',
                'definition': 'Trinity Study\'e göre, yıllık %4 portföy çekimi 30 yıllık dönemde %95 başarı şansı sunar. Bu kural, emeklilik için güvenli bir çekim oranı belirler ve portföyünüzün tükenme riskini minimize eder. 4% kuralı, enflasyon ayarlı çekimleri ve piyasa volatilitesini hesaba katarak sürdürülebilir bir emeklilik stratejisi sunar.',
                'context': 'Yıllık 200.000 TL gider için 5.000.000 TL birikim gereklidir (200.000 / 0.04). Bu hesaplama, finansal bağımsızlık hedefinizi belirlemenize yardımcı olur ve emeklilik için gereken portföy büyüklüğünü gösterir. 4% kuralı, piyasa krizleri ve enflasyon gibi risklere karşı dayanıklı bir emeklilik planı sağlar.'
            },
            {
                'term': 'Trinity Study',
                'definition': '1998 yılında Cooley, Hubbard ve Walz tarafından yapılan çalışma. Farklı portföy tahsislerinin 30 yıllık sürdürülebilirliğini analiz eder. Bu çalışma, tarihsel piyasa verilerini kullanarak farklı çekim oranlarının başarısını simüle eder ve güvenli çekim stratejileri için bilimsel temel sağlar. Trinity Study, emeklilik planlamasında en çok referans alınan çalışmalardan biridir.',
                'context': '4% güvenli çekim oranı bu çalışmaya dayanır ve 30 yıllık emeklilik döneminde %95 başarı şansı sunar. Çalışma, hisse senedi ve tahvil ağırlıklı portföylerin tarihsel performansını analiz eder ve emeklilik planlaması için güvenilir bir çerçeve sunar. Bu çalışma, finansal bağımsızlık hedeflerini belirlerken kritik bir referans noktasıdır.'
            },
            {
                'term': 'Crossover Point',
                'definition': 'Pasif gelirinizin yaşam giderlerinizi tamamen karşıladığı nokta. "Your Money or Your Life" kitabında tanımlanmıştır. Bu noktada, iş gelirine bağımlılık ortadan kalkar ve zaman özgürlüğü kazanılır. Crossover point, finansal bağımsızlık yolculuğunda önemli bir dönüm noktasıdır ve yaşam tarzı seçeneklerini genişletir.',
                'context': 'Crossover point\'ta iş geliri zorunluluğu azalır, zaman özgürlüğü artar. Bu noktaya ulaştığınızda, çalışmayı tamamen bırakabilir veya tutkulu olduğunuz işleri yapabilirsiniz. Crossover point, finansal özgürlüğe giden yolda motivasyon sağlar ve ilerlemenizi gösteren önemli bir göstergedir.'
            },
            {
                'term': 'Net Değer (Net Worth)',
                'definition': 'Toplam varlıklarınızın toplam borçlarınızdan çıkarılmasıyla elde edilen değer. Bu değer, gerçek servetinizi gösterir ve finansal sağlığınızın temel göstergesidir. Net değer, zaman içindeki finansal ilerlemenizi ölçmenize yardımcı olur ve finansal hedeflerinize ulaşma yolunda ne kadar ilerlediğinizi gösterir.',
                'context': 'Net Değer = Varlıklar + Nakit - Borçlar. Pozitif net değer finansal sağlığın temelidir ve borç yükünü yönetme yeteneğinizi gösterir. Net değeri izleyerek, finansal kararlarınızın etkisini değerlendirebilir ve zaman içinde servet birikiminizi takip edebilirsiniz. Net değer, finansal bağımsızlık yolculuğunda kritik bir göstergedir.'
            },
            {
                'term': 'Likidite Oranı',
                'definition': 'Mevcut nakdinizin aylık giderlerinize oranı. Kısa vadeli ödeme gücünü gösterir ve finansal güvenliğinizi değerlendirmenize yardımcı olur. Likidite oranı, acil durumlar veya beklenmedik harcamalar için ne kadar nakit rezerviniz olduğunu gösterir ve finansal krizlere karşı dayanıklılığınızı ölçer.',
                'context': '1.5+ mükemmel, 1.0 sınırda, altı kritik risk. Likidite oranınızı izleyerek, acil fon hedefinizi belirleyebilir ve finansal güvenliğinizi sağlayabilirsiniz. Yüksek likidite oranı, finansal esneklik sağlar ve acil durumlarda stresi azaltır. Bu oran, kısa vadeli finansal planlamanın temel göstergesidir.'
            },
            {
                'term': 'Borç-Gelir Oranı (DTI)',
                'definition': 'Toplam borçlarınızın yıllık gelirinize oranı. Bankacılıkta %36 eşik olarak kullanılır ve borç yönetimi yeteneğinizi gösterir. Bu oran, kredi başvurularında kritik bir faktördür ve finansal sağlığınızı değerlendirmek için kullanılır. Düşük borç-gelir oranı, daha iyi kredi koşulları ve finansal esneklik sağlar.',
                'context': '%36 altı sağlıklı, %50 üzeri yüksek risk. Borç-gelir oranınızı izleyerek, borç yükünüzü yönetebilir ve finansal hedeflerinize ulaşmak için daha iyi planlama yapabilirsiniz. Bu oran, yeni kredi başvurularında onay şansınızı etkiler ve finansal risk seviyenizi gösterir. Düşük oran, finansal güvenlik ve yatırım fırsatları sağlar.'
            },
            {
                'term': 'Tasarruf Oranı',
                'definition': 'Gelirinizin tasarruf edilen kısmının yüzdesi. Finansal bağımsızlığa giden yolda en önemli göstergedir ve FIRE hızınızı belirler. Yüksek tasarruf oranı, daha hızlı servet birikimi ve erken finansal özgürlük sağlar. Tasarruf oranı, finansal disiplininizi gösterir ve uzun vadeli finansal başarınızı belirler.',
                'context': '%20+ sağlıklı, %50+ FIRE hızlı mod. Tasarruf oranınızı izleyerek, finansal bağımsızlığa ne zaman ulaşabileceğinizi tahmin edebilir ve tasarruf stratejilerinizi optimize edebilirsiniz. Yüksek tasarruf oranı, acil durumlar için finansal güvenlik sağlar ve yatırım fırsatlarını artırır. Bu oran, finansal hedeflerinize ulaşma hızını belirler.'
            },
            {
                'term': 'Acil Durum Fonu',
                'definition': 'Beklenmedik harcamalar için ayrılan nakit rezervi. Finansal güvenliğinizin temelidir ve iş kaybı, sağlık sorunları veya beklenmedik harcamalar gibi finansal krizlere karşı koruma sağlar. Acil durum fonu, stresi azaltır ve finansal esneklik kazandırır. Bu fon, borçlanmadan acil durumları yönetmenizi sağlar.',
                'context': '3-6 ay gider hedef, 12 ay muhafazakâr. Acil durum fonunuzun büyüklüğünü belirleyerek, finansal güvenliğinizi sağlayabilir ve beklenmedik durumlara hazırlıklı olabilirsiniz. Yeterli acil fon, finansal planlamanızı korur ve uzun vadeli yatırımlarınızı güvence altına alır. Bu fon, finansal barışın temelidir.'
            },
            {
                'term': 'Pasif Gelir',
                'definition': 'Aktif çalışma olmadan elde edilen gelir (kira, temettü, faiz, portföy çekimi). Finansal bağımsızlığın temelidir ve zaman özgürlüğü sağlar. Pasif gelir kaynakları, iş gelirine bağımlılığı azaltır ve yaşam tarzı seçeneklerini genişletir. Çeşitlendirilmiş pasif gelir kaynakları, finansal güvenlik ve istikrar sağlar.',
                'context': 'Pasif gelir ≥ giderler = finansal özgürlük. Pasif gelirinizi artırarak, çalışma zorunluluğunu azaltabilir ve finansal bağımsızlığa daha hızlı ulaşabilirsiniz. Pasif gelir kaynakları çeşitlendirmek, riski azaltır ve sürdürülebilir finansal özgürlük sağlar. Bu gelir türü, uzun vadeli finansal güvenliğin anahtarıdır.'
            },
            {
                'term': 'ROI (Return on Investment)',
                'definition': 'Yatırım getiri oranı. (Kar / Maliyet) × 100. Yatırım performansını ölçmek için kullanılan temel metriktir ve yatırım kararlarını değerlendirmenize yardımcı olur. ROI, farklı yatırım fırsatlarını karşılaştırmanızı sağlar ve sermayenizi en verimli şekilde kullanmanıza yardımcı olur. Yüksek ROI, daha iyi yatırım performansı gösterir.',
                'context': 'Yatırım performansını ölçmek için kullanılır. ROI\'yi izleyerek, yatırım stratejilerinizi optimize edebilir ve en karlı fırsatları belirleyebilirsiniz. Bu metrik, risk ayarlı getiri ile birlikte kullanıldığında daha doğru yatırım kararları sağlar. ROI, portföy yönetiminin temel göstergelerinden biridir.'
            },
            {
                'term': 'Portföy Konsantrasyonu',
                'definition': 'Tek bir varlığın portföydeki ağırlığı. %20 üzeri risk oluşturur ve çeşitlendirme eksikliğini gösterir. Yüksek konsantrasyon, tek bir varlığın performansına aşırı bağımlılık yaratır ve portföy riskini artırır. Konsantrasyon riskini yönetmek, portföy çeşitlendirmesi ile sağlanır ve daha istikrarlı getiri sağlar.',
                'context': 'Çeşitlendirme eksikliği riskini gösterir. Portföy konsantrasyonunu izleyerek, risk seviyenizi yönetebilir ve portföyünüzü daha dengeli hale getirebilirsiniz. Düşük konsantrasyon, piyasa volatilitesine karşı daha iyi koruma sağlar ve sürdürülebilir getiri sunar. Bu göstergeler, portföy risk yönetiminin temelidir.'
            },
            {
                'term': 'Risk Skoru',
                'definition': 'Portföy risk seviyesi 0-100. Varlık risk dağılımı, konsantrasyon ve likiditeye dayanır. Bu skor, portföyünüzün genel risk profilini gösterir ve risk yönetimi stratejilerinizi geliştirmenize yardımcı olur. Risk skorunu izleyerek, risk seviyenizi yönetebilir ve yatırım hedeflerinize uygun risk seviyesini koruyabilirsiniz.',
                'context': '30 altı düşük, 30-60 orta, 60 üzeri yüksek risk. Risk skorunu takip ederek, portföyünüzü risk toleransınıza göre ayarlayabilir ve finansal hedeflerinize ulaşmak için uygun risk seviyesini koruyabilirsiniz. Bu skor, portföy rebalancing kararlarında kritik bir göstergedir. Risk yönetimi, başarılı yatırımcılığın temelidir.'
            },
            {
                'term': 'Likidite Skoru',
                'definition': 'Portföyün nakde çevrilebilirlik seviyesi 0-100. Acil durumlar için finansal esnekliğinizi gösterir ve nakde hızlı erişim yeteneğinizi değerlendirir. Yüksek likidite skoru, piyasa fırsatlarını hızlı değerlendirme yeteneği sağlar ve finansal krizlere karşı koruma sunar. Likidite, portföy yönetiminin önemli bir yönüdür.',
                'context': '70+ yüksek likidite, 40-70 orta, 40 altı düşük. Likidite skorunu izleyerek, portföyünüzün nakde dönüştürülebilirliğini optimize edebilir ve gerektiğinde hızlı nakde erişim sağlayabilirsiniz. Yüksek likidite, acil durumlar için finansal güvenlik sağlar ve yatırım fırsatlarını kaçırma riskini azaltır. Bu skor, portföy esnekliğinin temel göstergesidir.'
            },
            {
                'term': 'Çeşitlendirme (Diversification)',
                'definition': 'Farklı varlık sınıflarına yatırım yaparak riski azaltma stratejisi. Modern Portföy Teorisi (MPT) temel prensibidir ve portföy volatilitesini azaltır. Çeşitlendirme, tek bir varlık veya sektörün kötü performansından etkilenme riskini azaltır ve daha istikrarlı getiri sağlar. Bu strateji, risk ayarlı getiriyi optimize eder.',
                'context': 'Modern Portföy Teorisi (MPT) temel prensibi. Çeşitlendirme, piyasa riskini yönetmenin en etkili yollarından biridir ve uzun vadeli yatırım başarısı için kritik önem taşır. Doğru çeşitlendirme, risk seviyenizi korurken potansiyel getiriyi maksimize eder. Bu strateji, tüm başarılı yatırımcıların temel prensibidir.'
            },
            {
                'term': 'Varlık Tahsisi (Asset Allocation)',
                'definition': 'Portföyün farklı varlık sınıflarına (hisse, tahvil, emtia) dağıtılması. Risk toleransına ve yatırım hedefine göre belirlenir ve portföy performansını belirleyen en önemli faktördür. Doğru varlık tahsisi, risk-getiri profilini optimize eder ve yatırım hedeflerine ulaşma şansını artırır. Bu strateji, piyasa döngülerine karşı dayanıklılık sağlar.',
                'context': 'Risk toleransına ve yatırım hedefine göre belirlenir. Varlık tahsisini düzenli olarak gözden geçirerek, portföyünüzü hedeflerinize uygun tutabilir ve piyasa koşullarına göre ayarlayabilirsiniz. Doğru tahsis, yaşa göre değişir ve emekliliğe yaklaştıkça daha muhafazakar hale gelir. Bu strateji, başarılı uzun vadeli yatırımların temelidir.'
            },
            {
                'term': 'Sharpe Oranı',
                'definition': 'Risk ayarlı getiri metriği. (Portföy Getirisi - Risksiz Faiz) / Standart Sapma. Yatırım performansını risk düzeyiyle birlikte değerlendirir ve farklı portföyleri karşılaştırmak için kullanılır. Yüksek Sharpe oranı, birim risk başına daha yüksek getiri sağlar ve yatırım verimliliğini gösterir. Bu metrik, modern portföy teorisinin temel göstergelerinden biridir.',
                'context': 'Yüksek Sharpe oranı daha iyi risk ayarlı getiri gösterir. Sharpe oranını izleyerek, portföyünüzün verimliliğini değerlendirebilir ve yatırım stratejilerinizi optimize edebilirsiniz. Bu oran, risk seviyesini artırmadan getiriyi maksimize etmenin bir yolunu sunar. Sharpe oranı, profesyonel portföy yöneticilerinin en çok kullandığı metriklerden biridir.'
            },
            {
                'term': 'Dolar Maliyet Ortalaması (DCA)',
                'definition': 'Piyasa zamanlaması yapmadan düzenli aralıklarla sabit tutar yatırım yapma. Piyasa volatilitesinden etkilenmez ve ortalama maliyeti düşürür. DCA, piyasa zirvelerinde ve diplerinde düzenli yatırım yaparak zamanlama riskini azaltır ve duygusal yatırım kararlarını önler. Bu strateji, uzun vadeli yatırımcılar için idealdir.',
                'context': 'Piyasa volatilitesinden etkilenmez, ortalama maliyet düşer. DCA stratejisi, piyasa zamanlaması yapma stresini ortadan kaldırır ve düzenli yatırım disiplini sağlar. Bu yöntem, piyasa düşüşlerinde daha fazla hisse almanızı sağlar ve uzun vadeli ortalama maliyeti optimize eder. DCA, başarılı uzun vadeli yatırımların temel stratejilerinden biridir.'
            },
            {
                'term': 'Bileşik Faiz',
                'definition': 'Faizin faiz kazanması. Zamanla katlanarak büyüme. Uzun vadeli yatırımda en güçlü faktördür ve servet birikiminin temel mekanizmasıdır. Bileşik faiz, zamanla küçük tasarrufların büyük servetlere dönüşmesini sağlar ve Einstein\'in "dünyanın en büyük keşfi" olarak adlandırdığı bir fenomendir. Bu etki, uzun vadeli yatırımların gücünü gösterir.',
                'context': 'A = P(1 + r/n)^(nt). Uzun vadeli yatırımda en güçlü faktör. Bileşik faiz etkisi, yatırım süresi uzadıkça katlanarak artar ve erken başlamanın önemini gösterir. Bu matematiksel gerçek, düzenli tasarruf ve yatırımla servet birikiminin mümkün olduğunu kanıtlar. Bileşik faiz, finansal bağımsızlığa giden yolda en güçlü araçtır.'
            },
            {
                'term': '72 Kuralı',
                'definition': 'Paranın ikiye katlanması için gereken yıl sayısı = 72 / Yıllık Faiz Oranı. Basit ve etkili bir hesaplama yöntemidir ve yatırım getirisini hızlı değerlendirmek için kullanılır. Bu kural, bileşik faizin gücünü gösterir ve farklı getiri oranlarının etkisini karşılaştırmak için kullanılır. Finansal hedef belirlemede pratik bir araçtır.',
                'context': '%8 getiriyle 9 yılda para ikiye katlanır. 72 kuralı, yatırım hedeflerinize ulaşma süresini hızlı tahmin etmenizi sağlar ve farklı yatırım fırsatlarını karşılaştırmanıza yardımcı olur. Bu basit kural, finansal okuryazarlık için önemli bir araçtır ve yatırım kararlarını hızlı değerlendirmek için kullanılır. Kural, bileşik faizin gücünü basit bir şekilde gösterir.'
            },
            {
                'term': '50/30/20 Kuralı',
                'definition': 'Elizabeth Warren\'ın bütçe kuralı: %50 ihtiyaçlar, %30 istekler, %20 tasarruf. Basit ve etkili bütçe çerçevesi sunar ve finansal dengeyi sağlar. Bu kural, temel ihtiyaçları karşılarken yaşam kalitesini korur ve tasarruf alışkanlığı geliştirir. Bütçe yapmanın en popüler ve basit yöntemlerinden biridir.',
                'context': 'Basit ve etkili bütçe çerçevesi. 50/30/20 kuralı, bütçe yapmayı kolaylaştırır ve finansal hedeflere ulaşmak için net bir yol sunar. Bu kural, gelirinizi dengeli bir şekilde dağıtmanızı sağlar ve finansal stresi azaltır. Kural, finansal okuryazarlık için önemli bir araçtır ve sürdürülebilir bütçe yönetimi sağlar.'
            },
            {
                'term': 'Barista FIRE',
                'definition': 'Kısmi pasif gelir + tamamlayıcı çalışma ile erken emeklilik. Tam bağımsızlık yerine esnek çalışma sunar ve daha düşük tasarruf hedefi gerektirir. Bu yaklaşım, tam emeklilik yerine esnek çalışma düzeni sağlar ve sosyal etkileşimi sürdürür. Daha düşük FI hedefi ile daha erken özgürlük sağlar.',
                'context': 'Tam bağımsızlık yerine esnek çalışma. Barista FIRE, tam finansal bağımsızlığa ulaşmadan esnek çalışma fırsatı sunar ve yaşam tarzı tercihlerine daha fazla esneklik sağlar. Bu yaklaşım, daha düşük tasarruf hedefi ile daha erken özgürlük sağlar ve iş-yaşam dengesini optimize eder. Barista FIRE, geleneksel FIRE\a daha erişilebilir bir alternatiftir.'
            },
            {
                'term': 'Coast FIRE',
                'definition': 'Mevcut portföy büyümesiyle gelecekte FI hedefine ulaşma potansiyeli. Yeni yatırım yapmadan bileşik faizle büyüme sağlar ve erken yaşta yatırım yapmanın gücünü gösterir. Bu yaklaşım, mevcut yatırımların gelecekteki büyümesine güvenerek çalışmayı sürdürür ve finansal stresi azaltır. Zamanın gücünü gösterir.',
                'context': 'Yeni yatırım yapmadan bileşik faizle büyüme. Coast FIRE, erken yaşta yatırım yapmanın önemini gösterir ve mevcut portföyünüzün gelecekteki potansiyelini vurgular. Bu yaklaşım, finansal bağımsızlık yolculuğunda erken başlamanın değerini kanıtlar ve bileşik faizin gücünü gösterir. Coast FIRE, uzun vadeli yatırımcılar için motivasyon sağlar.'
            },
            {
                'term': 'Lean FIRE',
                'definition': 'Düşük gider profili ile daha erken bağımsızlık. Minimalist yaşam tarzı gerektirir ve daha düşük FI hedefi sağlar. Bu yaklaşım, tüketim alışkanlıklarını sorgular ve basit yaşamın değerini vurgular. Daha hızlı finansal özgürlük sağlar ancak yaşam tarzı değişikliği gerektirir.',
                'context': 'Minimalist yaşam tarzı gerektirir. Lean FIRE, düşük giderlerle daha erken finansal bağımsızlık sağlar ve minimalist yaşamın finansal özgürlüğe giden yolda gücünü gösterir. Bu yaklaşım, tüketim kültürünü sorgular ve basit yaşamın finansal faydalarını vurgular. Lean FIRE, yüksek tasarruf oranları ile hızlı özgürlük sağlar.'
            }
        ]
    },
    'en': {
        'title': 'Technical Terms Dictionary',
        'terms': [
            {
                'term': 'FI (Financial Independence)',
                'definition': 'Financial Independence. Having enough passive income to cover living expenses without working. This state allows you to maintain your standard of living without depending on job income and provides time freedom. Financial independence is the point where passive income sources (rent, dividends, interest, portfolio withdrawal) fully cover your living expenses.',
                'context': 'To reach FI target, you need 25× your annual expenses in savings (4% rule). This target is based on the Trinity Study and offers a 95% success rate over a 30-year retirement period. When you reach your FI number, work obligation disappears and you can fully control your lifestyle.'
            },
            {
                'term': 'FIRE (Financial Independence, Retire Early)',
                'definition': 'Financial Independence and Retiring Early. Movement to live without working at young age through saving and investing. This movement aims to achieve financial freedom before traditional retirement age through high savings rates (50%+), smart investments, and minimalist lifestyle. FIRE is not just about retirement but about increasing time freedom and lifestyle options.',
                'context': 'FIRE types: Traditional FIRE (full independence), Barista FIRE (part-time work), Coast FIRE (compound growth), Lean FIRE (low expenses). Each type is designed for different risk tolerances and lifestyle preferences. The FIRE movement offers different paths to financial independence and provides flexibility based on personal goals.'
            },
            {
                'term': '4% Rule (Safe Withdrawal Rate)',
                'definition': 'Per Trinity Study, 4% annual portfolio withdrawal offers 95% success rate over 30-year period. This rule determines a safe withdrawal rate for retirement and minimizes the risk of portfolio depletion. The 4% rule accounts for inflation-adjusted withdrawals and market volatility, providing a sustainable retirement strategy.',
                'context': 'For 200,000 TL annual expenses, 5,000,000 TL savings required (200,000 / 0.04). This calculation helps you determine your financial independence target and shows the portfolio size needed for retirement. The 4% rule provides a resilient retirement plan against market crises and inflation.'
            },
            {
                'term': 'Trinity Study',
                'definition': '1998 study by Cooley, Hubbard and Walz. Analyzes 30-year sustainability of different portfolio allocations. This study uses historical market data to simulate the success of different withdrawal rates and provides a scientific basis for safe withdrawal strategies. The Trinity Study is one of the most referenced studies in retirement planning.',
                'context': '4% safe withdrawal rate is based on this study and offers a 95% success rate over a 30-year retirement period. The study analyzes the historical performance of stock and bond weighted portfolios and provides a reliable framework for retirement planning. This study is a critical reference point when setting financial independence goals.'
            },
            {
                'term': 'Crossover Point',
                'definition': 'Point where passive income fully covers living expenses. Defined in "Your Money or Your Life" book. At this point, dependence on job income disappears and time freedom is gained. Crossover point is an important turning point in the financial independence journey and expands lifestyle options.',
                'context': 'At crossover point, work income necessity decreases, time freedom increases. When you reach this point, you can completely stop working or do work you are passionate about. Crossover point provides motivation on the path to financial freedom and is an important indicator of your progress.'
            },
            {
                'term': 'Net Worth',
                'definition': 'Total assets minus total liabilities. This value shows your true wealth and is the fundamental indicator of financial health. Net worth helps you measure your financial progress over time and shows how far you have progressed on your financial goals.',
                'context': 'Net Worth = Assets + Cash - Debts. Positive net worth is the foundation of financial health and shows your ability to manage debt load. By tracking net worth, you can evaluate the impact of your financial decisions and track your wealth accumulation over time. Net worth is a critical indicator on the financial independence journey.'
            },
            {
                'term': 'Liquidity Ratio',
                'definition': 'Ratio of current cash to monthly expenses. Shows short-term payment power and helps evaluate your financial security. Liquidity ratio shows how much cash reserve you have for emergencies or unexpected expenses and measures your resilience against financial crises.',
                'context': '1.5+ excellent, 1.0 borderline, below critical risk. By monitoring your liquidity ratio, you can set your emergency fund target and ensure your financial security. High liquidity ratio provides financial flexibility and reduces stress in emergencies. This ratio is a fundamental indicator of short-term financial planning.'
            },
            {
                'term': 'Debt-to-Income Ratio (DTI)',
                'definition': 'Ratio of total debt to annual income. Banking uses 36% as threshold and shows your debt management ability. This ratio is a critical factor in credit applications and is used to evaluate financial health. Low debt-to-income ratio provides better credit terms and financial flexibility.',
                'context': 'Below 36% healthy, above 50% high risk. By monitoring your debt-to-income ratio, you can manage your debt load and plan better to achieve your financial goals. This ratio affects your approval chances for new credit applications and shows your financial risk level. Low ratio provides financial security and investment opportunities.'
            },
            {
                'term': 'Savings Rate',
                'definition': 'Percentage of income saved. Most important indicator on the path to financial independence and determines your FIRE speed. High savings rate provides faster wealth accumulation and early financial freedom. Savings rate shows your financial discipline and determines your long-term financial success.',
                'context': '20%+ healthy, 50%+ FIRE fast mode. By monitoring your savings rate, you can predict when you will reach financial independence and optimize your savings strategies. High savings rate provides financial security for emergencies and increases investment opportunities. This rate determines the speed of reaching your financial goals.'
            },
            {
                'term': 'Emergency Fund',
                'definition': 'Cash reserve set aside for unexpected expenses. Foundation of your financial security and provides protection against financial crises such as job loss, health issues, or unexpected expenses. Emergency fund reduces stress and provides financial flexibility. This fund allows you to manage emergencies without going into debt.',
                'context': '3-6 months expenses target, 12 months conservative. By determining the size of your emergency fund, you can ensure your financial security and be prepared for unexpected situations. Adequate emergency fund protects your financial planning and secures your long-term investments. This fund is the foundation of financial peace.'
            },
            {
                'term': 'Passive Income',
                'definition': 'Income earned without active work (rent, dividends, interest, portfolio withdrawal). Foundation of financial independence and provides time freedom. Passive income sources reduce dependence on job income and expand lifestyle options. Diversified passive income sources provide financial security and stability.',
                'context': 'Passive income ≥ expenses = financial freedom. By increasing your passive income, you can reduce work obligation and reach financial independence faster. Diversifying passive income sources reduces risk and provides sustainable financial freedom. This income type is the key to long-term financial security.'
            },
            {
                'term': 'ROI (Return on Investment)',
                'definition': 'Investment return rate. (Profit / Cost) × 100. Fundamental metric used to measure investment performance and helps evaluate investment decisions. ROI allows you to compare different investment opportunities and helps you use your capital most efficiently. High ROI indicates better investment performance.',
                'context': 'Used to measure investment performance. By tracking ROI, you can optimize your investment strategies and identify the most profitable opportunities. This metric provides better investment decisions when used with risk-adjusted return. ROI is one of the fundamental indicators of portfolio management.'
            },
            {
                'term': 'Portfolio Concentration',
                'definition': "Weight of single asset in portfolio. Above 20% creates risk and shows lack of diversification. High concentration creates excessive dependence on a single asset's performance and increases portfolio risk. Managing concentration risk is achieved through portfolio diversification and provides more stable returns.",
                'context': 'Shows lack of diversification risk. By monitoring portfolio concentration, you can manage your risk level and make your portfolio more balanced. Low concentration provides better protection against market volatility and offers sustainable returns. These indicators are fundamental to portfolio risk management.'
            },
            {
                'term': 'Risk Score',
                'definition': 'Portfolio risk level 0-100. Based on asset risk distribution, concentration and liquidity. This score shows the overall risk profile of your portfolio and helps develop risk management strategies. By monitoring risk score, you can manage your risk level and maintain a risk level appropriate to your investment goals.',
                'context': 'Below 30 low, 30-60 medium, above 60 high risk. By tracking risk score, you can adjust your portfolio according to your risk tolerance and maintain an appropriate risk level to reach your financial goals. This score is a critical indicator in portfolio rebalancing decisions. Risk management is fundamental to successful investing.'
            },
            {
                'term': 'Liquidity Score',
                'definition': 'Portfolio convertibility to cash level 0-100. Shows your financial flexibility for emergencies and evaluates your ability to quickly access cash. High liquidity score provides ability to quickly evaluate market opportunities and offers protection against financial crises. Liquidity is an important aspect of portfolio management.',
                'context': "70+ high liquidity, 40-70 medium, below 40 low. By monitoring liquidity score, you can optimize your portfolio's convertibility to cash and ensure quick access to cash when needed. High liquidity provides financial security for emergencies and reduces the risk of missing investment opportunities. This score is a fundamental indicator of portfolio flexibility."
            },
            {
                'term': 'Diversification',
                'definition': 'Strategy to reduce risk by investing in different asset classes. Core principle of Modern Portfolio Theory (MPT) and reduces portfolio volatility. Diversification reduces the risk of being affected by poor performance of a single asset or sector and provides more stable returns. This strategy optimizes risk-adjusted return.',
                'context': 'Core principle of Modern Portfolio Theory (MPT). Diversification is one of the most effective ways to manage market risk and is critical for long-term investment success. Proper diversification maximizes potential return while maintaining your risk level. This strategy is a fundamental principle of all successful investors.'
            },
            {
                'term': 'Asset Allocation',
                'definition': 'Distribution of portfolio across different asset classes (stocks, bonds, commodities). Determined by risk tolerance and investment goals and is the most important factor determining portfolio performance. Proper asset allocation optimizes risk-return profile and increases chances of reaching investment goals. This strategy provides resilience against market cycles.',
                'context': 'Determined by risk tolerance and investment goals. By regularly reviewing asset allocation, you can keep your portfolio aligned with your goals and adjust according to market conditions. Proper allocation changes with age and becomes more conservative as you approach retirement. This strategy is fundamental to successful long-term investments.'
            },
            {
                'term': 'Sharpe Ratio',
                'definition': 'Risk-adjusted return metric. (Portfolio Return - Risk Free Rate) / Standard Deviation. Evaluates investment performance together with risk level and is used to compare different portfolios. High Sharpe ratio provides higher return per unit of risk and shows investment efficiency. This metric is one of the fundamental indicators of modern portfolio theory.',
                'context': "Higher Sharpe ratio indicates better risk-adjusted return. By monitoring Sharpe ratio, you can evaluate your portfolio's efficiency and optimize your investment strategies. This ratio offers a way to maximize return without increasing risk level. Sharpe ratio is one of the most used metrics by professional portfolio managers."
            },
            {
                'term': 'Dollar Cost Averaging (DCA)',
                'definition': 'Investing fixed amount at regular intervals without market timing. Not affected by market volatility and lowers average cost. DCA reduces timing risk by investing regularly at market peaks and troughs and prevents emotional investment decisions. This strategy is ideal for long-term investors.',
                'context': 'Not affected by market volatility, lowers average cost. DCA strategy eliminates the stress of market timing and provides regular investment discipline. This method allows you to buy more shares during market declines and optimizes long-term average cost. DCA is one of the fundamental strategies of successful long-term investments.'
            },
            {
                'term': 'Compound Interest',
                'definition': 'Interest earning interest. Exponential growth over time. Most powerful factor in long-term investing and is the fundamental mechanism of wealth accumulation. Compound interest allows small savings to turn into large wealth over time and is a phenomenon Einstein called "the greatest discovery in the world." This effect shows the power of long-term investments.',
                'context': 'A = P(1 + r/n)^(nt). Most powerful factor in long-term investing. Compound interest effect increases exponentially as investment period extends and shows the importance of starting early. This mathematical reality proves that wealth accumulation through regular saving and investing is possible. Compound interest is the most powerful tool on the path to financial independence.'
            },
            {
                'term': 'Rule of 72',
                'definition': 'Years to double money = 72 / Annual Interest Rate. Simple and effective calculation method and is used to quickly evaluate investment return. This rule shows the power of compound interest and is used to compare the effect of different return rates. It is a practical tool for financial goal setting.',
                'context': 'At 8% return, money doubles in 9 years. The rule of 72 allows you to quickly estimate the time to reach your investment goals and helps you compare different investment opportunities. This simple rule is an important tool for financial literacy and is used to quickly evaluate investment decisions. The rule shows the power of compound interest in a simple way.'
            },
            {
                'term': '50/30/20 Rule',
                'definition': 'Elizabeth Warren\'s budget rule: 50% needs, 30% wants, 20% savings. Provides simple and effective budget framework and ensures financial balance. This rule maintains quality of life while meeting basic needs and develops savings habit. It is one of the most popular and simple methods of budgeting.',
                'context': 'Simple and effective budget framework. The 50/30/20 rule simplifies budgeting and provides a clear path to reach financial goals. This rule allows you to distribute your income in a balanced way and reduces financial stress. The rule is an important tool for financial literacy and provides sustainable budget management.'
            },
            {
                'term': 'Barista FIRE',
                'definition': 'Early retirement with partial passive income + supplementary work. Offers flexible work instead of full independence and requires lower savings target. This approach provides flexible work arrangement instead of full retirement and maintains social interaction. Provides earlier freedom with lower FI target.',
                'context': 'Flexible work instead of full independence. Barista FIRE offers flexible work opportunity before reaching full financial independence and provides more flexibility in lifestyle preferences. This approach provides earlier freedom with lower savings target and optimizes work-life balance. Barista FIRE is a more accessible alternative to traditional FIRE.'
            },
            {
                'term': 'Coast FIRE',
                'definition': 'Potential to reach FI target in future with current portfolio growth. Provides growth through compound interest without new investment and shows the power of investing at an early age. This approach continues working relying on future growth of current investments and reduces financial stress. Shows the power of time.',
                'context': 'Growth through compound interest without new investment. Coast FIRE shows the importance of investing at an early age and emphasizes the future potential of your current portfolio. This approach proves the value of starting early on the financial independence journey and shows the power of compound interest. Coast FIRE provides motivation for long-term investors.'
            },
            {
                'term': 'Lean FIRE',
                'definition': 'Earlier independence with low expense profile. Requires minimalist lifestyle and provides lower FI target. This approach questions consumption habits and emphasizes the value of simple living. Provides faster financial freedom but requires lifestyle change.',
                'context': 'Requires minimalist lifestyle. Lean FIRE provides earlier financial independence with low expenses and shows the power of minimalist living on the path to financial freedom. This approach questions consumption culture and emphasizes the financial benefits of simple living. Lean FIRE provides fast freedom with high savings rates.'
            }
        ]
    }
}

PROGRAM_ANALYSES = {
    'tr': {
        'title': 'Program Analizleri',
        'analyses': [
            {
                'name': 'Finansal Sağlık Analizi',
                'description': 'Genel finansal durumunuzu değerlendiren kapsamlı analiz. Likidite, borç oranı, tasarruf oranı, dayanıklılık ve finansal skor hesaplar.',
                'metrics': [
                    {'metric': 'Likidite Oranı', 'range': '1.5+ mükemmel, 1.0 sınırda, <1.0 kritik'},
                    {'metric': 'Borç Oranı', 'range': '<%30 sağlıklı, %30-40 dikkat, >%40 yüksek risk'},
                    {'metric': 'Tasarruf Oranı', 'range': '%20+ harika, %0-20 orta, negatif bütçe açığı'},
                    {'metric': 'Dayanıklılık', 'range': '6+ ay güvenli, 3-6 ay yeterli, <3 ay kırılgan'},
                    {'metric': 'Finansal Skor', 'range': '75+ çok iyi, 50-75 stabil, <50 riskli'}
                ],
                'actionable_insights': 'Düşük likidite için nakit rezervini artırın. Yüksek borç için yüksek faizli borçları önceliklendirin. Düşük tasarruf için lüks harcamaları azaltın.'
            },
            {
                'name': 'Varlık Portföy Analizi',
                'description': 'Varlık portföyünüzün derinlemesine analizi. Değer, maliyet, kar/zarar, ROI, risk ve likidite skorlarını içerir.',
                'metrics': [
                    {'metric': 'Toplam Portföy Değeri', 'range': 'Piyasa değeri'},
                    {'metric': 'Genel ROI', 'range': 'Yatırım getiri oranı'},
                    {'metric': 'Risk Skoru', 'range': '0-100, 30 altı düşük, 30-60 orta, 60 üzeri yüksek'},
                    {'metric': 'Likidite Skoru', 'range': '0-100, 70+ yüksek, 40-70 orta, 40 altı düşük'},
                    {'metric': 'Portföy Konsantrasyonu', 'range': '%20 üzeri riskli'}
                ],
                'actionable_insights': 'Yüksek risk skoru için çeşitlendirmeyi artırın. Düşük likidite için daha likit varlıklara ağırlık verin. Konsantrasyon riski için portföyü dengeleyin.'
            },
            {
                'name': 'Finansal Özgürlük (FIRE) Analizi',
                'description': 'Finansal bağımsızlık yolculuğunuzu takip eden analiz. FI hedefi, ilerleme, tasarruf oranı, pasif gelir ve özgürlük skorunu içerir.',
                'metrics': [
                    {'metric': 'FI Sayısı (25× Kuralı)', 'range': 'Yıllık gider × 25'},
                    {'metric': 'FI İlerleme', 'range': '%0-100, %100 bağımsızlık'},
                    {'metric': 'Tasarruf Oranı', 'range': '%20+ ideal, %50+ hızlı mod'},
                    {'metric': 'Gelir Karşılama', 'range': '%100 crossover point'},
                    {'metric': 'Finansal Özgürlük Skoru', 'range': '0-100, 6 kriter toplamı'}
                ],
                'actionable_insights': 'FI ilerlemesini hızlandırmak için tasarruf oranını artırın. Pasif geliri artırmak için dividend-paying varlıklara yatırım yapın. Acil fonu güçlendirin.'
            }
        ]
    },
    'en': {
        'title': 'Program Analyses',
        'analyses': [
            {
                'name': 'Financial Health Analysis',
                'description': 'Comprehensive analysis evaluating your overall financial situation. Calculates liquidity, debt ratio, savings rate, sustainability, and financial score.',
                'metrics': [
                    {'metric': 'Liquidity Ratio', 'range': '1.5+ excellent, 1.0 borderline, <1.0 critical'},
                    {'metric': 'Debt Ratio', 'range': '<%30 healthy, %30-40 caution, >%40 high risk'},
                    {'metric': 'Savings Rate', 'range': '%20+ excellent, %0-20 medium, negative budget deficit'},
                    {'metric': 'Sustainability', 'range': '6+ months secure, 3-6 months adequate, <3 months fragile'},
                    {'metric': 'Financial Score', 'range': '75+ very good, 50-75 stable, <50 risky'}
                ],
                'actionable_insights': 'Increase cash reserves for low liquidity. Prioritize high-interest debt for high debt ratio. Reduce luxury spending for low savings rate.'
            },
            {
                'name': 'Asset Portfolio Analysis',
                'description': 'In-depth analysis of your asset portfolio. Includes value, cost, gain/loss, ROI, risk score, and liquidity score.',
                'metrics': [
                    {'metric': 'Total Portfolio Value', 'range': 'Market value'},
                    {'metric': 'Overall ROI', 'range': 'Investment return rate'},
                    {'metric': 'Risk Score', 'range': '0-100, below 30 low, 30-60 medium, above 60 high'},
                    {'metric': 'Liquidity Score', 'range': '0-100, 70+ high, 40-70 medium, below 40 low'},
                    {'metric': 'Portfolio Concentration', 'range': 'Above 20% risky'}
                ],
                'actionable_insights': 'Increase diversification for high risk score. Weight more liquid assets for low liquidity. Balance portfolio for concentration risk.'
            },
            {
                'name': 'Financial Independence (FIRE) Analysis',
                'description': 'Analysis tracking your financial independence journey. Includes FI target, progress, savings rate, passive income, and freedom score.',
                'metrics': [
                    {'metric': 'FI Number (25× Rule)', 'range': 'Annual expenses × 25'},
                    {'metric': 'FI Progress', 'range': '%0-100, %100 independence'},
                    {'metric': 'Savings Rate', 'range': '%20+ ideal, %50+ fast mode'},
                    {'metric': 'Income Replacement', 'range': '%100 crossover point'},
                    {'metric': 'Financial Freedom Score', 'range': '0-100, sum of 6 criteria'}
                ],
                'actionable_insights': 'Increase savings rate to accelerate FI progress. Invest in dividend-paying assets to increase passive income. Strengthen emergency fund.'
            }
        ]
    }
}

FINANCIAL_GUIDE_DATA = {
    'beginner': {
        'income_expenses': {
            'tr': {
                'title': 'Gelir ve Giderler',
                'concept_definition': 'Gelir, paranızın kaynağıdır. Aktif gelir için çalışmanız gerekir (maaş, saatlik ücret). Pasif gelir ise siz çalışmasanız da gelir sağlar (kira, temettü, faiz). Giderler ise paranızın nereye gittiğini gösterir. Bütçe yapmak, gelir ve giderlerinizi takip etmenin en iyi yoludur.',
                'practical_example': 'Ali aylık 10.000 TL kazanıyor. 5.000 TL\'si kira, 2.000 TL\'si yemek, 1.000 TL\'si ulaşım, 1.000 TL\'si eğlence, 1.000 TL\'si tasarruf. Ali her ay gelirinin %10\'unu tasarruf ediyor.',
                'mathematical_formula': 'Tasarruf Oranı = (Tasarruf / Toplam Gelir) × 100',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': '"Babil\'in En Zengin Adamı" kitabında George S. Clason şunu söylüyor: "Paranın bir kısmını kendin için ayır. Gelirinin %10\'unu tasarruf et ve yatırım yap." Bu, finansal özgürlüğün temelidir.'
            },
            'en': {
                'title': 'Income & Expenses',
                'concept_definition': 'Income is the source of your money. Active income requires your work (salary, hourly wage). Passive income generates money without your active effort (rent, dividends, interest). Expenses show where your money goes. Budgeting is the best way to track income and expenses.',
                'practical_example': 'Ali earns 10,000 TL monthly. 5,000 TL for rent, 2,000 TL for food, 1,000 TL for transportation, 1,000 TL for entertainment, 1,000 TL for savings. Ali saves 10% of his income every month.',
                'mathematical_formula': 'Savings Rate = (Savings / Total Income) × 100',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': 'In "The Richest Man in Babylon", George S. Clason says: "A part of all you earn is yours to keep. Save 10% of your income and invest it." This is the foundation of financial freedom.'
            },
            'de': {
                'title': 'Einkommen und Ausgaben',
                'concept_definition': 'Einkommen ist die Quelle Ihres Geldes. Aktives Einkommen erfordert Ihre Arbeit (Gehalt, Stundenlohn). Passives Einkommen generiert Geld ohne Ihre aktive Bemühung (Miete, Dividenden, Zinsen). Ausgaben zeigen, wohin Ihr Geld geht. Budgetierung ist der beste Weg, Einkommen und Ausgaben zu verfolgen.',
                'practical_example': 'Ali verdient monatlich 10.000 TL. 5.000 TL für Miete, 2.000 TL für Essen, 1.000 TL für Transport, 1.000 TL für Unterhaltung, 1.000 TL für Ersparnisse. Ali spart jeden Monat 10% seines Einkommens.',
                'mathematical_formula': 'Sparquote = (Ersparnisse / Gesamteinkommen) × 100',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': 'In "Der Reichste Mann von Babylon" sagt George S. Clason: "Ein Teil all dessen, was Sie verdienen, gehört Ihnen. Sparen Sie 10% Ihres Einkommens und investieren Sie es." Dies ist die Grundlage der finanziellen Freiheit.'
            },
            'it': {
                'title': 'Reddito e Spese',
                'concept_definition': 'Il reddito è la fonte dei tuoi soldi. Il reddito attivo richiede il tuo lavoro (stipendio, paga oraria). Il reddito passivo genera denaro senza il tuo sforzo attivo (affitto, dividendi, interessi). Le spese mostrano dove va il tuo denaro. Il budget è il modo migliore per tracciare reddito e spese.',
                'practical_example': 'Ali guadagna 10.000 TL al mese. 5.000 TL per affitto, 2.000 TL per cibo, 1.000 TL per trasporti, 1.000 TL per intrattenimento, 1.000 TL per risparmio. Ali risparmia il 10% del suo reddito ogni mese.',
                'mathematical_formula': 'Tasso di Risparmio = (Risparmio / Reddito Totale) × 100',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': 'In "L\'Uomo Più Ricco di Babilonia", George S. Clason dice: "Una parte di tutto ciò che guadagni è tua da tenere. Risparmia il 10% del tuo reddito e investilo." Questa è la base della libertà finanziaria.'
            }
        },
        'compound_interest': {
            'tr': {
                'title': 'Bileşik Faiz',
                'concept_definition': 'Bileşik faiz, faizin faiz kazanmasıdır. Zamanla paranız katlanarak büyür. Küçük bir başlangıç tutarı bile uzun vadede büyük bir servete dönüşebilir. Ancak borç için bileşik faiz de çalışır ve borcu hızla büyütebilir.',
                'practical_example': 'Ayşe 18 yaşında her ay 500 TL yatırıyor ve %8 yıllık getiri elde ediyor. 40 yaşında (22 yıl sonra) yaklaşık 350.000 TL birikimi olur. 65 yaşında (47 yıl sonra) yaklaşık 2.5 milyon TL birikimi olur.',
                'mathematical_formula': 'A = P(1 + r/n)^(nt)\nA: Final Tutar\nP: Ana Para\nr: Yıllık Faiz Oranı\nn: Yılda Bileşikleşme Sayısı\nt: Yıl Sayısı',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'Einstein bileşik faizi "dünyanın en büyük güçlerinden biri" olarak tanımlamıştır. "Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Zaman, yatırımdaki en önemli faktördür. Erken başlamak, milyonlarca dolar fark yaratabilir."'
            },
            'en': {
                'title': 'Compound Interest',
                'concept_definition': 'Compound interest is interest earning interest. Your money grows exponentially over time. Even a small starting amount can become a large fortune in the long run. However, compound interest also works for debt and can grow debt rapidly.',
                'practical_example': 'Ayşe invests 500 TL monthly at 8% annual return starting at age 18. By age 40 (22 years later), she has approximately 350,000 TL. By age 65 (47 years later), she has approximately 2.5 million TL.',
                'mathematical_formula': 'A = P(1 + r/n)^(nt)\nA: Final Amount\nP: Principal\nr: Annual Interest Rate\nn: Times Compounded Per Year\nt: Number of Years',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'Einstein described compound interest as "the eighth wonder of the world." In "The Psychology of Money", Morgan Housel says: "Time is the most important factor in investing. Starting early can make a difference of millions of dollars."'
            },
            'de': {
                'title': 'Zinseszins',
                'concept_definition': 'Zinseszins ist Zins, der Zinsen verdient. Ihr Geld wächst exponentiell über die Zeit. Selbst eine kleine Startsumme kann zu einem großen Vermögen werden. Zinseszins funktioniert jedoch auch für Schulden und kann Schulden schnell wachsen lassen.',
                'practical_example': 'Ayşe investiert monatlich 500 TL bei 8% jährlicher Rendite ab dem 18. Lebensjahr. Mit 40 Jahren (22 Jahre später) hat sie etwa 350.000 TL. Mit 65 Jahren (47 Jahre später) hat sie etwa 2,5 Millionen TL.',
                'mathematical_formula': 'A = P(1 + r/n)^(nt)\nA: Endbetrag\nP: Kapital\nr: Jährlicher Zinssatz\nn: Zinseszins pro Jahr\nt: Anzahl der Jahre',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'Einstein bezeichnete Zinseszins als "das achte Weltwunder". In "The Psychology of Money" sagt Morgan Housel: "Zeit ist der wichtigste Faktor beim Investieren. Früh anzufangen kann einen Unterschied von Millionen Dollar machen."'
            },
            'it': {
                'title': 'Interesse Composto',
                'concept_definition': 'L\'interesse composto è interesse che guadagna interessi. I tuoi soldi crescono esponenzialmente nel tempo. Anche una piccola somma iniziale può diventare una grande fortuna a lungo termine. Tuttavia, l\'interesse composto funziona anche per il debito e può farlo crescere rapidamente.',
                'practical_example': 'Ayşe investe 500 TL al mese con un rendimento annuale dell\'8% a partire dai 18 anni. A 40 anni (22 anni dopo), ha circa 350.000 TL. A 65 anni (47 anni dopo), ha circa 2,5 milioni di TL.',
                'mathematical_formula': 'A = P(1 + r/n)^(nt)\nA: Importo Finale\nP: Capitale\nr: Tasso di Interesse Annuale\nn: Volte Composto all\'Anno\nt: Numero di Anni',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'Einstein ha descritto l\'interesse composto come "l\'ottava meraviglia del mondo". In "The Psychology of Money", Morgan Housel dice: "Il tempo è il fattore più importante nell\'investimento. Iniziare presto può fare la differenza di milioni di dollari."'
            }
        },
        'assets': {
            'tr': {
                'title': 'Varlıklar ve Varlık Sınıfları',
                'concept_definition': 'Varlık, size para getiren şeydir. Hisse senetleri (şirket hisseleri), tahviller (borç senetleri), gayrimenkul (ev, arsa), yatırım fonları, ETF\'ler, kıymetli metaller (altın, gümüş) ve kripto paralar farklı varlık sınıflarıdır. Her birinin risk ve getiri profili farklıdır.',
                'practical_example': 'Mehmet 100.000 TL\'si var. 40.000 TL\'si hisse senedi (yüksek risk, yüksek getiri), 30.000 TL\'si tahvil (düşük risk, orta getiri), 20.000 TL\'si altın (orta risk, koruma), 10.000 TL\'si kripto (çok yüksek risk, çok yüksek getiri potansiyeli).',
                'mathematical_formula': 'Portföy Getirisi = Σ(Varlık Ağırlığı × Varlık Getirisi)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Piyasa oylama makinesidir, tartım makinesi değil." Kısa vadeli fiyat dalgalanmaları önemli değil, uzun vadeli değer önemlidir.'
            },
            'en': {
                'title': 'Assets & Asset Classes',
                'concept_definition': 'An asset is something that generates money for you. Stocks (company shares), bonds (debt securities), real estate (property), mutual funds, ETFs, precious metals (gold, silver), and cryptocurrencies are different asset classes. Each has a different risk and return profile.',
                'practical_example': 'Mehmet has 100,000 TL. 40,000 TL in stocks (high risk, high return), 30,000 TL in bonds (low risk, medium return), 20,000 TL in gold (medium risk, protection), 10,000 TL in crypto (very high risk, very high return potential).',
                'mathematical_formula': 'Portfolio Return = Σ(Asset Weight × Asset Return)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "The market is a voting machine, not a weighing machine." Short-term price fluctuations don\'t matter, long-term value matters.'
            },
            'de': {
                'title': 'Vermögenswerte und Anlageklassen',
                'concept_definition': 'Ein Vermögenswert ist etwas, das Geld für Sie generiert. Aktien (Unternehmensanteile), Anleihen (Schuldverschreibungen), Immobilien (Grundstücke), Investmentfonds, ETFs, Edelmetalle (Gold, Silber) und Kryptowährungen sind verschiedene Anlageklassen. Jede hat ein anderes Risiko- und Renditeprofil.',
                'practical_example': 'Mehmet hat 100.000 TL. 40.000 TL in Aktien (hohes Risiko, hohe Rendite), 30.000 TL in Anleihen (geringes Risiko, mittlere Rendite), 20.000 TL in Gold (mittleres Risiko, Schutz), 10.000 TL in Krypto (sehr hohes Risiko, sehr hohes Renditepotenzial).',
                'mathematical_formula': 'Portfoliorendite = Σ(Anlagengewicht × Anlagerendite)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Der Markt ist eine Abstimmungsmaschine, keine Waage." Kurzfristige Preisschwankungen sind nicht wichtig, langfristiger Wert ist wichtig.'
            },
            'it': {
                'title': 'Attività e Classi di Attività',
                'concept_definition': 'Un\'attività è qualcosa che genera denaro per te. Azioni (quote societarie), obbligazioni (titoli di debito), immobili (proprietà), fondi comuni, ETF, metalli preziosi (oro, argento) e criptovalute sono diverse classi di attività. Ognuna ha un profilo di rischio e rendimento diverso.',
                'practical_example': 'Mehmet ha 100.000 TL. 40.000 TL in azioni (alto rischio, alto rendimento), 30.000 TL in obbligazioni (basso rischio, rendimento medio), 20.000 TL in oro (rischio medio, protezione), 10.000 TL in cripto (rischio molto alto, potenziale di rendimento molto alto).',
                'mathematical_formula': 'Rendimento del Portafoglio = Σ(Peso dell\'Attività × Rendimento dell\'Attività)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "Il mercato è una macchina di voto, non una bilancia." Le fluttuazioni dei prezzi a breve termine non contano, il valore a lungo termine conta.'
            }
        },
        'financial_freedom': {
            'tr': {
                'title': 'Finansal Özgürlük',
                'concept_definition': 'Finansal özgürlük, çalışmak zorunda olmadığınız bir yaşam sürdürmek için yeterli pasif gelire sahip olmaktır. FI/RE (Financial Independence, Retire Early) hareketi bu konsept üzerine kuruludur. 4% Kuralı, yıllık harcamalarınızın 25 katı kadar birikiminiz olduğunda finansal olarak özgür olduğunuzu söyler.',
                'practical_example': 'Fatma yıllık 200.000 TL harcıyor. Finansal özgürlük için 200.000 / 0.04 = 5.000.000 TL birikime ihtiyacı var. Bu birikimden yılda 200.000 TL (%4 çekim oranıyla) çekebilir ve çalışmak zorunda kalmaz.',
                'mathematical_formula': 'FI Sayısı = Yıllık Harcamalar / Çekim Oranı (genellikle 0.04)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin ve Joe Dominguez şunu söylüyor: "Para, yaşam enerjinizdir. Her harcama, yaşam enerjinizin bir kısmını harcamaktır." Finansal özgürlük, zamanınızı geri almak demektir.'
            },
            'en': {
                'title': 'Financial Freedom',
                'concept_definition': 'Financial freedom is having enough passive income to live without working. The FI/RE (Financial Independence, Retire Early) movement is built on this concept. The 4% Rule says you are financially free when you have 25 times your annual expenses in savings.',
                'practical_example': 'Fatma spends 200,000 TL annually. For financial freedom, she needs 200,000 / 0.04 = 5,000,000 TL in savings. She can withdraw 200,000 TL annually (at 4% withdrawal rate) from this savings and doesn\'t have to work.',
                'mathematical_formula': 'FI Number = Annual Expenses / Withdrawal Rate (usually 0.04)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin and Joe Dominguez say: "Money is your life energy. Every expenditure is spending a portion of your life energy." Financial freedom is about reclaiming your time.'
            },
            'de': {
                'title': 'Finanzielle Freiheit',
                'concept_definition': 'Finanzielle Freiheit bedeutet, genug passives Einkommen zu haben, um ohne zu arbeiten zu leben. Die FI/RE-Bewegung (Financial Independence, Retire Early) basiert auf diesem Konzept. Die 4%-Regel besagt, dass Sie finanziell frei sind, wenn Sie das 25-fache Ihrer jährlichen Ausgaben gespart haben.',
                'practical_example': 'Fatma gibt jährlich 200.000 TL aus. Für finanzielle Freiheit benötigt sie 200.000 / 0,04 = 5.000.000 TL Ersparnisse. Sie kann jährlich 200.000 TL (bei 4% Entnahmerate) aus diesen Ersparnissen entnehmen und muss nicht arbeiten.',
                'mathematical_formula': 'FI-Zahl = Jährliche Ausgaben / Entnahmerate (normalerweise 0,04)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagen Vicki Robin und Joe Dominguez: "Geld ist Ihre Lebensenergie. Jede Ausgabe ist das Ausgeben eines Teils Ihrer Lebensenergie." Finanzielle Freiheit bedeutet, Ihre Zeit zurückzugewinnen.'
            },
            'it': {
                'title': 'Libertà Finanziaria',
                'concept_definition': 'La libertà finanziaria è avere abbastanza reddito passivo per vivere senza lavorare. Il movimento FI/RE (Financial Independence, Retire Early) è costruito su questo concetto. La regola del 4% dice che sei finanziariamente libero quando hai 25 volte le tue spese annuali in risparmio.',
                'practical_example': 'Fatma spende 200.000 TL all\'anno. Per la libertà finanziaria, ha bisogno di 200.000 / 0,04 = 5.000.000 TL di risparmio. Può prelevare 200.000 TL all\'anno (al 4% di tasso di prelievo) da questi risparmi e non deve lavorare.',
                'mathematical_formula': 'Numero FI = Spese Annuali / Tasso di Prelievo (solitamente 0,04)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin e Joe Dominguez dicono: "Il denaro è la tua energia vitale. Ogni spesa è spendere una parte della tua energia vitale." La libertà finanziaria riguarda il riprendere il tuo tempo.'
            }
        },
        'investing': {
            'tr': {
                'title': 'Yatırım ve Yatırım Araçları',
                'concept_definition': 'Yatırım, gelecekteki getiri için bugün para harcamaktır. Risk ve getiri dengesi önemlidir: yüksek risk genellikle yüksek getiri potansiyeli, düşük risk genellikle düşük getiri potansiyeli getirir. Çeşitlendirme, riski azaltmanın en iyi yoludur. Dolar Maliyet Ortalaması (DCA), piyasa zamanlaması yapmadan düzenli yatırım yapmaktır.',
                'practical_example': 'Can her ay 1.000 TL yatırım yapıyor. Bazen hisse fiyatı yüksek (100 TL/share), bazen düşük (80 TL/share). Zamanlama yapmadığı için ortalama maliyeti düşüyor. 12 ayda toplam 12.000 TL yatırıyor ve ortalama 89 TL/share maliyetle hisse alıyor.',
                'mathematical_formula': 'DCA Ortalama Maliyet = Toplam Yatırılan / Toplam Hisse Sayısı',
                'python_function': 'calculate_dollar_cost_averaging(monthly_investment, periods, prices)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Piyasalar nadir olaylara (tail risk) karşı savunmasızdır." Çeşitlendirme, beklenmedik olaylara karşı koruma sağlar.'
            },
            'en': {
                'title': 'Investing & Investment Vehicles',
                'concept_definition': 'Investing is spending money today for future returns. The risk-return balance is important: high risk usually means high return potential, low risk usually means low return potential. Diversification is the best way to reduce risk. Dollar Cost Averaging (DCA) is investing regularly without trying to time the market.',
                'practical_example': 'Can invests 1,000 TL monthly. Sometimes stock price is high (100 TL/share), sometimes low (80 TL/share). Because he doesn\'t time the market, his average cost is lower. Over 12 months, he invests 12,000 TL total and buys shares at an average cost of 89 TL/share.',
                'mathematical_formula': 'DCA Average Cost = Total Invested / Total Shares',
                'python_function': 'calculate_dollar_cost_averaging(monthly_investment, periods, prices)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Markets are vulnerable to rare events (tail risk)." Diversification provides protection against unexpected events.'
            },
            'de': {
                'title': 'Investieren und Anlageinstrumente',
                'concept_definition': 'Investieren bedeutet, heute Geld für zukünftige Renditen auszugeben. Das Risiko-Rendite-Gleichgewicht ist wichtig: hohes Risiko bedeutet meist hohes Renditepotenzial, geringes Risiko bedeutet meist geringes Renditepotenzial. Diversifizierung ist der beste Weg, das Risiko zu reduzieren. Dollar Cost Averaging (DCA) bedeutet regelmäßig zu investieren, ohne zu versuchen, den Markt zu timen.',
                'practical_example': 'Can investiert monatlich 1.000 TL. Manchmal ist der Aktienkurs hoch (100 TL/Aktie), manchmal niedrig (80 TL/Aktie). Da er den Markt nicht timet, sind seine durchschnittlichen Kosten niedriger. Über 12 Monate investiert er insgesamt 12.000 TL und kauft Aktien zu einem durchschnittlichen Preis von 89 TL/Aktie.',
                'mathematical_formula': 'DCA Durchschnittskosten = Gesamtinvestition / Gesamtaktien',
                'python_function': 'calculate_dollar_cost_averaging(monthly_investment, periods, prices)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Märkte sind anfällig für seltene Ereignisse (Tail Risk)." Diversifizierung bietet Schutz vor unerwarteten Ereignissen.'
            },
            'it': {
                'title': 'Investire e Strumenti di Investimento',
                'concept_definition': 'Investire significa spendere soldi oggi per rendimenti futuri. L\'equilibrio rischio-rendimento è importante: alto rischio di solito significa alto potenziale di rendimento, basso rischio di solito significa basso potenziale di rendimento. La diversificazione è il modo migliore per ridurre il rischio. Dollar Cost Averaging (DCA) significa investire regolarmente senza cercare di time il mercato.',
                'practical_example': 'Can investe 1.000 TL al mese. A volte il prezzo delle azioni è alto (100 TL/azione), a volte basso (80 TL/azione). Poiché non time il mercato, il suo costo medio è inferiore. In 12 mesi, investe 12.000 TL totali e acquista azioni a un costo medio di 89 TL/azione.',
                'mathematical_formula': 'Costo Medio DCA = Totale Investito / Totale Azioni',
                'python_function': 'calculate_dollar_cost_averaging(monthly_investment, periods, prices)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I mercati sono vulnerabili a eventi rari (tail risk)." La diversificazione fornisce protezione contro eventi imprevisti.'
            }
        },
        'risk_management': {
            'tr': {
                'title': 'Risk Yönetimi',
                'concept_definition': 'Risk yönetimi, finansal riskleri anlamak ve yönetmek demektir. Tüm yatırımlar risk içerir, ancak bu riski azaltmanın yolları vardır. Çeşitlendirme, riski azaltmanın en basit yoludur. Acil durum fonu, beklenmedik harcamalar için koruma sağlar.',
                'practical_example': 'Ayşe 100.000 TL\'si var. Tümünü tek bir hisseye yatırırsa, o hisse düşerse büyük kaybeder. Bunun yerine 10 farklı hisseye yatırırsa, biri düşerse diğerleri telafi edebilir. Ayrıca 10.000 TL acil fon ayırır.',
                'mathematical_formula': 'Portföy Riski = Σ(Varlık Ağırlığı × Varlık Riski)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Çeşitlendirme, yatırımcının en iyi arkadaşıdır. Tüm yumurtaları aynı sepete koymayın."'
            },
            'en': {
                'title': 'Risk Management',
                'concept_definition': 'Risk management is about understanding and managing financial risks. All investments carry risk, but there are ways to reduce it. Diversification is the simplest way to reduce risk. Emergency fund provides protection for unexpected expenses.',
                'practical_example': 'Ayşe has 100,000 TL. If she invests all in one stock, she loses big if that stock drops. Instead, if she invests in 10 different stocks, if one drops, others can compensate. She also sets aside 10,000 TL as emergency fund.',
                'mathematical_formula': 'Portfolio Risk = Σ(Asset Weight × Asset Risk)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Diversification is the investor\'s best friend. Don\'t put all your eggs in one basket."'
            },
            'de': {
                'title': 'Risikomanagement',
                'concept_definition': 'Risikomanagement bedeutet, finanzielle Risiken zu verstehen und zu verwalten. Alle Investments tragen Risiken, aber es gibt Wege, diese zu reduzieren. Diversifizierung ist der einfachste Weg, das Risiko zu reduzieren. Notgroschen bieten Schutz für unerwartete Ausgaben.',
                'practical_example': 'Ayşe hat 100.000 TL. Wenn sie alles in eine Aktie investiert, verliert sie viel, wenn diese Aktie fällt. Stattdessen investiert sie in 10 verschiedene Aktien. Wenn eine fällt, können andere ausgleichen. Sie legt auch 10.000 TL als Notgroschen beiseite.',
                'mathematical_formula': 'Portfoliorisiko = Σ(Anlagengewicht × Anlagerisiko)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Diversifizierung ist der beste Freund des Investors. Legen Sie nicht alle Eier in einen Korb."'
            },
            'it': {
                'title': 'Gestione del Rischio',
                'concept_definition': 'La gestione del rischio riguarda la comprensione e la gestione dei rischi finanziari. Tutti gli investimenti comportano rischi, ma ci sono modi per ridurli. La diversificazione è il modo più semplice per ridurre il rischio. Il fondo di emergenza fornisce protezione per le spese impreviste.',
                'practical_example': 'Ayşe ha 100.000 TL. Se investe tutto in un\'azione, perde molto se quell\'azione scende. Invece, investe in 10 azioni diverse. Se una scende, altre possono compensare. Mette anche da parte 10.000 TL come fondo di emergenza.',
                'mathematical_formula': 'Rischio del Portafoglio = Σ(Peso dell\'Attività × Rischio dell\'Attività)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La diversificazione è il migliore amico dell\'investitore. Non mettere tutte le uova nello stesso paniere."'
            }
        },
        'portfolio_optimization': {
            'tr': {
                'title': 'Portföy Optimizasyonu',
                'concept_definition': 'Portföy optimizasyonu, varlıklarınızı en iyi şekilde dağıtmak demektir. Farklı varlıklara yatırım yaparak riski azaltabilir ve getiriyi artırabilirsiniz. Çeşitlendirme, portföy optimizasyonunun temelidir.',
                'practical_example': 'Mehmet 100.000 TL\'si var. %50 hisse, %30 tahvil, %20 altın yatırır. Bu çeşitlendirme, piyasa çöküşlerinde koruma sağlar. Hisse düşerse, tahvil ve altın telafi edebilir.',
                'mathematical_formula': 'Portföy Getirisi = Σ(Varlık Ağırlığı × Varlık Getirisi)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Çeşitlendirme, riski azaltmanın en iyi yoludur."'
            },
            'en': {
                'title': 'Portfolio Optimization',
                'concept_definition': 'Portfolio optimization means distributing your assets in the best way. By investing in different assets, you can reduce risk and increase returns. Diversification is the foundation of portfolio optimization.',
                'practical_example': 'Mehmet has 100,000 TL. He invests 50% stocks, 30% bonds, 20% gold. This diversification provides protection during market crashes. If stocks fall, bonds and gold can compensate.',
                'mathematical_formula': 'Portfolio Return = Σ(Asset Weight × Asset Return)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Diversification is the best way to reduce risk."'
            },
            'de': {
                'title': 'Portfolio-Optimierung',
                'concept_definition': 'Portfolio-Optimierung bedeutet, Ihre Vermögenswerte bestmöglich zu verteilen. Durch Investition in verschiedene Vermögenswerte können Sie das Risiko reduzieren und die Rendite erhöhen. Diversifizierung ist die Grundlage der Portfolio-Optimierung.',
                'practical_example': 'Mehmet hat 100.000 TL. Er investiert 50% Aktien, 30% Anleihen, 20% Gold. Diese Diversifizierung bietet Schutz während Marktzusammenbrüchen. Wenn Aktien fallen, können Anleihen und Gold ausgleichen.',
                'mathematical_formula': 'Portfoliorendite = Σ(Anlagengewicht × Anlagerendite)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Diversifizierung ist der beste Weg, das Risiko zu reduzieren."'
            },
            'it': {
                'title': 'Ottimizzazione del Portafoglio',
                'concept_definition': 'L\'ottimizzazione del portafoglio significa distribuire le tue attività nel modo migliore. Investendo in diverse attività, puoi ridurre il rischio e aumentare il rendimento. La diversificazione è la base dell\'ottimizzazione del portafoglio.',
                'practical_example': 'Mehmet ha 100.000 TL. Investe il 50% in azioni, il 30% in obbligazioni, il 20% in oro. Questa diversificazione fornisce protezione durante i crolli del mercato. Se le azioni scendono, le obbligazioni e l\'oro possono compensare.',
                'mathematical_formula': 'Rendimento del Portafoglio = Σ(Peso dell\'Attività × Rendimento dell\'Attività)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La diversificazione è il modo migliore per ridurre il rischio."'
            }
        },
        'behavioral_finance': {
            'tr': {
                'title': 'Davranışsal Finans',
                'concept_definition': 'Davranışsal finans, insan psikolojisinin finansal kararları nasıl etkilediğini inceler. Kayıp korkusu, aşırı güven ve sürü etkisi yaygın hatalardır. Duygularınızı kontrol etmek, başarılı yatırım için önemlidir.',
                'practical_example': 'Piyasa çöküşünde panik satışı yapmak yaygın bir hatadır. Bunun yerine, düşük fiyattan alım fırsatı olarak görmek daha iyidir. Uzun vadeli düşünmek, kısa vadeli dalgalanmaları görmezden gelmenizi sağlar.',
                'mathematical_formula': 'Kayıp Aversionı = Kayıp Acısı / Kazanç Sevinci',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Finansal kararlarınızın %90\'ı psikolojiktir."'
            },
            'en': {
                'title': 'Behavioral Finance',
                'concept_definition': 'Behavioral finance studies how human psychology affects financial decisions. Fear of loss, overconfidence, and herd behavior are common mistakes. Controlling your emotions is important for successful investing.',
                'practical_example': 'Panic selling during market crashes is a common mistake. Instead, seeing it as a buying opportunity at low prices is better. Thinking long-term helps you ignore short-term fluctuations.',
                'mathematical_formula': 'Loss Aversion = Loss Pain / Gain Pleasure',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "90% of your financial decisions are psychological."'
            },
            'de': {
                'title': 'Verhaltensfinanz',
                'concept_definition': 'Verhaltensfinanz untersucht, wie menschliche Psychologie finanzielle Entscheidungen beeinflusst. Verlustangst, Überkonfidenz und Herdenverhalten sind häufige Fehler. Ihre Emotionen zu kontrollieren ist wichtig für erfolgreiches Investieren.',
                'practical_example': 'Panikverkäufe während Marktzusammenbrüchen sind ein häufiger Fehler. Stattdessen ist es besser, dies als Kaufgelegenheit zu niedrigen Preisen zu sehen. Langfristiges Denken hilft, kurzfristige Schwankungen zu ignorieren.',
                'mathematical_formula': 'Verlustaversion = Verlustschmerz / Gewinnfreude',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "90% Ihrer finanziellen Entscheidungen sind psychologisch."'
            },
            'it': {
                'title': 'Finanza Comportamentale',
                'concept_definition': 'La finanza comportamentale studia come la psicologia umana influenzi le decisioni finanziarie. La paura della perdita, l\'eccessiva fiducia e il comportamento di gregge sono errori comuni. Controllare le tue emozioni è importante per investire con successo.',
                'practical_example': 'Le vendite di panico durante i crolli del mercato sono un errore comune. Invece, vederlo come un\'opportunità di acquisto a prezzi bassi è meglio. Pensare a lungo termine aiuta a ignorare le fluttuazioni a breve termine.',
                'mathematical_formula': 'Avversione alla Perdita = Dolore della Perdita / Piacere del Guadagno',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "Il 90% delle tue decisioni finanziarie è psicologico."'
            }
        },
        'tax_planning': {
            'tr': {
                'title': 'Vergi Planlaması',
                'concept_definition': 'Vergi planlaması, vergi yükünüzü yasal olarak azaltmak demektir. Vergi avantajlı hesaplar (BES, 401k) kullanmak önemlidir. Vergi tasarrufu, yatırım getirilerinizi artırır.',
                'practical_example': 'BES hesabına yıllık 50.000 TL yatırırsanız, %15 vergi indirimi alırsınız. Bu, 7.500 TL vergi tasarrufu demektir. Uzun vadede bu tasarruf bileşik faizle büyür.',
                'mathematical_formula': 'Vergi Tasarrufu = Yatırım × Vergi Oranı',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Zengin Baba, Yoksul Baba" kitabında Robert Kiyosaki şunu söylüyor: "Vergi planlaması, zenginlerin sırrıdır."'
            },
            'en': {
                'title': 'Tax Planning',
                'concept_definition': 'Tax planning means legally reducing your tax burden. Using tax-advantaged accounts (BES, 401k) is important. Tax savings increase your investment returns.',
                'practical_example': 'If you invest 50,000 TL annually in a BES account, you get a 15% tax deduction. This means 7,500 TL tax savings. Over time, this savings grows with compound interest.',
                'mathematical_formula': 'Tax Savings = Investment × Tax Rate',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Rich Dad Poor Dad", Robert Kiyosaki says: "Tax planning is the secret of the rich."'
            },
            'de': {
                'title': 'Steuerplanung',
                'concept_definition': 'Steuerplanung bedeutet, Ihre Steuerlast legal zu reduzieren. Die Nutzung steuerbegünstigter Konten (BES, 401k) ist wichtig. Steuereinsparungen erhöhen Ihre Investmentrenditen.',
                'practical_example': 'Wenn Sie jährlich 50.000 TL in ein BES-Konto investieren, erhalten Sie eine 15% Steuerabzug. Dies bedeutet 7.500 TL Steuereinsparung. Mit der Zeit wachsen diese Einsparungen mit Zinseszins.',
                'mathematical_formula': 'Steuereinsparung = Investition × Steuersatz',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Reicher Vater, armer Vater" sagt Robert Kiyosaki: "Steuerplanung ist das Geheimnis der Reichen."'
            },
            'it': {
                'title': 'Pianificazione Fiscale',
                'concept_definition': 'La pianificazione fiscale significa ridurre legalmente il tuo carico fiscale. L\'utilizzo di conti con vantaggi fiscali (BES, 401k) è importante. Il risparmio fiscale aumenta i tuoi rendimenti sugli investimenti.',
                'practical_example': 'Se investi 50.000 TL all\'anno in un conto BES, ottieni una detrazione fiscale del 15%. Questo significa 7.500 TL di risparmio fiscale. Nel tempo, questo risparmio cresce con l\'interesse composto.',
                'mathematical_formula': 'Risparmio Fiscale = Investimento × Aliquota Fiscale',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Padre Ricco, Padre Povero", Robert Kiyosaki dice: "La pianificazione fiscale è il segreto dei ricchi."'
            }
        },
        'retirement_planning': {
            'tr': {
                'title': 'Emeklilik Planlaması',
                'concept_definition': 'Emeklilik planlaması, emeklilik için yeterli birikim yapmak demektir. Erken başlamak, bileşik faizin gücünden yararlanmanızı sağlar. Emeklilik yaşı ve yaşam beklentisini hesaba katın.',
                'practical_example': '25 yaşında her ay 1.000 TL yatırırsanız ve %8 getiri elde ederseniz, 65 yaşında yaklaşık 3 milyon TL birikiminiz olur. 35 yaşında başlarsanız, sadece 1.2 milyon TL olur.',
                'mathematical_formula': 'Emeklilik Birikimi = Aylık Yatırım × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Erken başlamak, en önemli faktördür."'
            },
            'en': {
                'title': 'Retirement Planning',
                'concept_definition': 'Retirement planning means saving enough for retirement. Starting early allows you to benefit from the power of compound interest. Consider retirement age and life expectancy.',
                'practical_example': 'If you invest 1,000 TL monthly starting at age 25 with 8% return, you will have approximately 3 million TL at age 65. If you start at age 35, you will only have 1.2 million TL.',
                'mathematical_formula': 'Retirement Savings = Monthly Investment × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Starting early is the most important factor."'
            },
            'de': {
                'title': 'Rentenplanung',
                'concept_definition': 'Rentenplanung bedeutet, genug für die Rente zu sparen. Früh anzufangen ermöglicht es Ihnen, die Kraft des Zinseszins zu nutzen. Berücksichtigen Sie Rentenalter und Lebenserwartung.',
                'practical_example': 'Wenn Sie monatlich 1.000 TL ab dem 25. Lebensjahr bei 8% Rendite investieren, haben Sie mit 65 Jahren etwa 3 Millionen TL. Wenn Sie mit 35 Jahren anfangen, haben Sie nur 1,2 Millionen TL.',
                'mathematical_formula': 'Rentenersparnisse = Monatliche Investition × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Früh anzufangen ist der wichtigste Faktor."'
            },
            'it': {
                'title': 'Pianificazione della Pensione',
                'concept_definition': 'La pianificazione della pensione significa risparmiare abbastanza per la pensione. Iniziare presto ti permette di beneficiare del potere dell\'interesse composto. Considera l\'età pensionabile e l\'aspettativa di vita.',
                'practical_example': 'Se investi 1.000 TL al mese a partire dai 25 anni con un rendimento dell\'8%, avrai circa 3 milioni di TL a 65 anni. Se inizi a 35 anni, avrai solo 1,2 milioni di TL.',
                'mathematical_formula': 'Risparmio Pensionistico = Investimento Mensile × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "Iniziare presto è il fattore più importante."'
            }
        },
        'international_investing': {
            'tr': {
                'title': 'Uluslararası Yatırım',
                'concept_definition': 'Uluslararası yatırım, farklı ülkelerde yatırım yaparak riski azaltmak demektir. Küresel ETF\'ler ile kolayca uluslararası yatırım yapabilirsiniz. Döviz riskini göz önünde bulundurun.',
                'practical_example': 'Portföyünüz %60 ABD, %20 Avrupa, %20 Asya hisselerinden oluşabilir. Bu çeşitlendirme, tek bir ülkenin ekonomik sorunlarından korunmanızı sağlar.',
                'mathematical_formula': 'Uluslararası Portföy = Σ(Ülke Ağırlığı × Ülke Getirisi)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Küresel diversifikasyon, ülke riskini azaltır."'
            },
            'en': {
                'title': 'International Investing',
                'concept_definition': 'International investing means reducing risk by investing in different countries. You can easily invest internationally with global ETFs. Consider currency risk.',
                'practical_example': 'Your portfolio can consist of 60% US, 20% Europe, 20% Asia stocks. This diversification protects you from a single country\'s economic problems.',
                'mathematical_formula': 'International Portfolio = Σ(Country Weight × Country Return)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Global diversification reduces country risk."'
            },
            'de': {
                'title': 'Internationales Investieren',
                'concept_definition': 'Internationales Investieren bedeutet, das Risiko durch Investition in verschiedene Länder zu reduzieren. Sie können leicht mit globalen ETFs international investieren. Berücksichtigen Sie das Währungsrisiko.',
                'practical_example': 'Ihr Portfolio kann aus 60% US, 20% Europa, 20% Asien Aktien bestehen. Diese Diversifizierung schützt Sie vor den wirtschaftlichen Problemen eines einzelnen Landes.',
                'mathematical_formula': 'Internationales Portfolio = Σ(Landgewicht × Landesrendite)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Globale Diversifizierung reduziert Länderrisiko."'
            },
            'it': {
                'title': 'Investimento Internazionale',
                'concept_definition': 'L\'investimento internazionale significa ridurre il rischio investendo in diversi paesi. Puoi facilmente investire a livello internazionale con ETF globali. Considera il rischio valutario.',
                'practical_example': 'Il tuo portafoglio può consistere di azioni al 60% USA, 20% Europa, 20% Asia. Questa diversificazione ti protegge dai problemi economici di un singolo paese.',
                'mathematical_formula': 'Portafoglio Internazionale = Σ(Peso Paese × Rendimento Paese)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La diversificazione globale riduce il rischio paese."'
            }
        },
        'derivatives': {
            'tr': {
                'title': 'Türev Araçlar',
                'concept_definition': 'Türev araçlar, varlıkların fiyat hareketlerine dayalı finansal sözleşmelerdir. Opsiyonlar ve vadeli işlemler (futures) yaygın türev araçlardır. Riski yönetmek veya spekülasyon için kullanılırlar.',
                'practical_example': 'Bir hisse senedi opsiyonu satın alarak, hisseyi satın almadan fiyat hareketinden faydalanabilirsiniz. Bu, daha az sermaye ile daha fazla pozisyon almanızı sağlar.',
                'mathematical_formula': 'Opsiyon Primi = İç Değer + Zaman Değeri',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Türev araçlar, güçlü ama tehlikeli araçlardır."'
            },
            'en': {
                'title': 'Derivatives',
                'concept_definition': 'Derivatives are financial contracts based on the price movements of assets. Options and futures are common derivatives. They are used for risk management or speculation.',
                'practical_example': 'By buying a stock option, you can benefit from price movements without buying the stock. This allows you to take larger positions with less capital.',
                'mathematical_formula': 'Option Premium = Intrinsic Value + Time Value',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Derivatives are powerful but dangerous instruments."'
            },
            'de': {
                'title': 'Derivate',
                'concept_definition': 'Derivate sind Finanzkontrakte, die auf Preisbewegungen von Vermögenswerten basieren. Optionen und Futures sind häufige Derivate. Sie werden für Risikomanagement oder Spekulation verwendet.',
                'practical_example': 'Durch den Kauf einer Aktienoption können Sie von Preisbewegungen profitieren, ohne die Aktie zu kaufen. Dies ermöglicht es Ihnen, größere Positionen mit weniger Kapital einzugehen.',
                'mathematical_formula': 'Optionsprämie = Innerer Wert + Zeitwert',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Derivate sind mächtige aber gefährliche Instrumente."'
            },
            'it': {
                'title': 'Derivati',
                'concept_definition': 'I derivati sono contratti finanziari basati sui movimenti di prezzo delle attività. Le opzioni e i futures sono derivati comuni. Vengono utilizzati per la gestione del rischio o la speculazione.',
                'practical_example': 'Acquistando un\'opzione azionaria, puoi beneficiare dei movimenti di prezzo senza acquistare l\'azione. Questo ti permette di prendere posizioni più grandi con meno capitale.',
                'mathematical_formula': 'Premio Opzione = Valore Intrinseco + Valore Tempo',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I derivati sono strumenti potenti ma pericolosi."'
            }
        },
        'alternative_investments': {
            'tr': {
                'title': 'Alternatif Yatırımlar',
                'concept_definition': 'Alternatif yatırımlar, hisse ve tahviller dışındaki yatırım araçlarıdır. Gayrimenkul, emtia, sanat, koleksiyonlar ve özel sermaye alternatif yatırımlardır. Portföy çeşitlendirmesi için önemlidir.',
                'practical_example': 'Portföyünüz %70 hisse, %20 tahvil, %10 gayrimenkul REIT olabilir. Bu, geleneksel varlıklarla korelasyonu düşük olan varlıklar ekler.',
                'mathematical_formula': 'Alternatif Portföy = Σ(Alternatif Ağırlık × Alternatif Getiri)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Alternatif yatırımlar, portföy çeşitlendirmesini artırır."'
            },
            'en': {
                'title': 'Alternative Investments',
                'concept_definition': 'Alternative investments are investment vehicles other than stocks and bonds. Real estate, commodities, art, collectibles, and private equity are alternative investments. Important for portfolio diversification.',
                'practical_example': 'Your portfolio can be 70% stocks, 20% bonds, 10% real estate REIT. This adds assets with low correlation to traditional assets.',
                'mathematical_formula': 'Alternative Portfolio = Σ(Alternative Weight × Alternative Return)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Alternative investments increase portfolio diversification."'
            },
            'de': {
                'title': 'Alternative Investitionen',
                'concept_definition': 'Alternative Investitionen sind Anlageinstrumente außer Aktien und Anleihen. Immobilien, Rohstoffe, Kunst, Sammlerstücke und Private Equity sind alternative Investitionen. Wichtig für Portfolio-Diversifizierung.',
                'practical_example': 'Ihr Portfolio kann 70% Aktien, 20% Anleihen, 10% Immobilien REIT sein. Dies fügt Vermögenswerte mit niedriger Korrelation zu traditionellen Vermögenswerten hinzu.',
                'mathematical_formula': 'Alternatives Portfolio = Σ(Alternatives Gewicht × Alternative Rendite)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Alternative Investitionen erhöhen die Portfolio-Diversifizierung."'
            },
            'it': {
                'title': 'Investimenti Alternativi',
                'concept_definition': 'Gli investimenti alternativi sono strumenti di investimento diversi da azioni e obbligazioni. Immobili, materie prime, arte, collezionabili e private equity sono investimenti alternativi. Importanti per la diversificazione del portafoglio.',
                'practical_example': 'Il tuo portafoglio può essere 70% azioni, 20% obbligazioni, 10% immobili REIT. Questo aggiunge attività con bassa correlazione alle attività tradizionali.',
                'mathematical_formula': 'Portafoglio Alternativo = Σ(Peso Alternativo × Rendimento Alternativo)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Gli investimenti alternativi aumentano la diversificazione del portafoglio."'
            }
        },
        'quantitative_finance': {
            'tr': {
                'title': 'Kuantitatif Finans',
                'concept_definition': 'Kuantitatif finans, matematik ve istatistik kullanarak finansal analiz yapmaktır. Veri analizi ve modelleme, yatırım kararlarını iyileştirir. Monte Carlo simülasyonları risk analizinde kullanılır.',
                'practical_example': 'Monte Carlo simülasyonu ile portföyün gelecekteki performansını tahmin edebilirsiniz. 10.000 farklı senaryo çalıştırarak olasılık dağılımı oluşturursunuz.',
                'mathematical_formula': 'Beklenen Getiri = Σ(Olasılık × Getiri)\nStandart Sapma = √(Σ(Olasılık × (Getiri - Beklenen)^2))',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Kuantitatif modeller, riski anlamak için önemlidir."'
            },
            'en': {
                'title': 'Quantitative Finance',
                'concept_definition': 'Quantitative finance is using mathematics and statistics for financial analysis. Data analysis and modeling improve investment decisions. Monte Carlo simulations are used for risk analysis.',
                'practical_example': 'With Monte Carlo simulation, you can predict the future performance of your portfolio. You run 10,000 different scenarios to create a probability distribution.',
                'mathematical_formula': 'Expected Return = Σ(Probability × Return)\nStandard Deviation = √(Σ(Probability × (Return - Expected)^2))',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Quantitative models are important for understanding risk."'
            },
            'de': {
                'title': 'Quantitative Finance',
                'concept_definition': 'Quantitative Finance ist die Verwendung von Mathematik und Statistik für Finanzanalysen. Datenanalyse und Modellierung verbessern Investmententscheidungen. Monte-Carlo-Simulationen werden für Risikoanalyse verwendet.',
                'practical_example': 'Mit Monte-Carlo-Simulation können Sie die zukünftige Performance Ihres Portfolios vorhersagen. Sie führen 10.000 verschiedene Szenarien aus, um eine Wahrscheinlichkeitsverteilung zu erstellen.',
                'mathematical_formula': 'Erwartete Rendite = Σ(Wahrscheinlichkeit × Rendite)\nStandardabweichung = √(Σ(Wahrscheinlichkeit × (Rendite - Erwartet)^2))',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Quantitative Modelle sind wichtig für das Verständnis von Risiko."'
            },
            'it': {
                'title': 'Finanza Quantitativa',
                'concept_definition': 'La finanza quantitativa è l\'uso di matematica e statistica per l\'analisi finanziaria. L\'analisi dei dati e la modellazione migliorano le decisioni di investimento. Le simulazioni Monte Carlo vengono utilizzate per l\'analisi del rischio.',
                'practical_example': 'Con la simulazione Monte Carlo, puoi prevedere la performance futura del tuo portafoglio. Esegui 10.000 diversi scenari per creare una distribuzione di probabilità.',
                'mathematical_formula': 'Rendimento Atteso = Σ(Probabilità × Rendimento)\nDeviazione Standard = √(Σ(Probabilità × (Rendimento - Atteso)^2))',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I modelli quantitativi sono importanti per comprendere il rischio."'
            }
        },
        'algorithmic_trading': {
            'tr': {
                'title': 'Algoritmik Ticaret',
                'concept_definition': 'Algoritmik ticaret, bilgisayar algoritmaları ile otomatik yatırım yapmaktır. Duygusal hataları önler ve hızlı işlem yapmanızı sağlar. Ancak teknik bilgi gerektirir.',
                'practical_example': 'Basit bir algoritma: Hisse fiyatı 50 günlük ortalamanın üzerine çıkarsa al, altına düşerse sat. Bu, duygusal kararları önler.',
                'mathematical_formula': 'Algoritma Sinyali = Fiyat - Hareketli Ortalama',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Algoritmik ticaret, hız ve veri avantajıdır."'
            },
            'en': {
                'title': 'Algorithmic Trading',
                'concept_definition': 'Algorithmic trading is automatic investing with computer algorithms. It prevents emotional mistakes and allows fast trading. However, it requires technical knowledge.',
                'practical_example': 'Simple algorithm: Buy when stock price rises above 50-day average, sell when it falls below. This prevents emotional decisions.',
                'mathematical_formula': 'Algorithm Signal = Price - Moving Average',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Algorithmic trading is about speed and data advantage."'
            },
            'de': {
                'title': 'Algorithmischer Handel',
                'concept_definition': 'Algorithmischer Handel ist automatisches Investieren mit Computeralgorithmen. Es verhindert emotionale Fehler und ermöglicht schnelles Handeln. Es erfordert jedoch technisches Wissen.',
                'practical_example': 'Einfacher Algorithmus: Kaufen, wenn Aktienkurs über 50-Tage-Durchschnitt steigt, verkaufen, wenn er darunter fällt. Dies verhindert emotionale Entscheidungen.',
                'mathematical_formula': 'Algorithmus-Signal = Preis - Gleitender Durchschnitt',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Algorithmischer Handel ist Geschwindigkeit und Datenvorteil."'
            },
            'it': {
                'title': 'Trading Algoritmico',
                'concept_definition': 'Il trading algoritmico è l\'investimento automatico con algoritmi computerizzati. Previene errori emotivi e permette un trading veloce. Tuttavia, richiede conoscenze tecniche.',
                'practical_example': 'Algoritmo semplice: Acquista quando il prezzo delle azioni sale sopra la media a 50 giorni, vendi quando scende sotto. Questo previene decisioni emotive.',
                'mathematical_formula': 'Segnale Algoritmo = Prezzo - Media Mobile',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il trading algoritmico riguarda velocità e vantaggio dati."'
            }
        },
        'machine_learning_finance': {
            'tr': {
                'title': 'Makine Öğrenmesi ve Finans',
                'concept_definition': 'Makine öğrenmesi, bilgisayarların verilerden öğrenmesini sağlar. Finansal tahminler, risk modelleme ve fraud detection için kullanılır. Veri kalitesi önemlidir.',
                'practical_example': 'Basit bir model: Geçmiş fiyat verilerini kullanarak gelecekteki fiyatları tahmin edebilirsiniz. Ancak geçmiş geleceği garanti etmez.',
                'mathematical_formula': 'Tahmin = Model(Veri)\nHata = Gerçek - Tahmin',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Veri kalitesi, model başarısını belirler."'
            },
            'en': {
                'title': 'Machine Learning in Finance',
                'concept_definition': 'Machine learning enables computers to learn from data. Used for financial predictions, risk modeling, and fraud detection. Data quality is important.',
                'practical_example': 'Simple model: You can predict future prices using historical price data. However, past doesn\'t guarantee future.',
                'mathematical_formula': 'Prediction = Model(Data)\nError = Actual - Prediction',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Data quality determines model success."'
            },
            'de': {
                'title': 'Machine Learning in der Finanzen',
                'concept_definition': 'Machine Learning ermöglicht es Computern, aus Daten zu lernen. Wird für Finanzvorhersagen, Risikomodellierung und Fraud Detection verwendet. Datenqualität ist wichtig.',
                'practical_example': 'Einfaches Modell: Sie können zukünftige Preise mit historischen Preisdaten vorhersagen. Vergangenheit garantiert jedoch nicht Zukunft.',
                'mathematical_formula': 'Vorhersage = Modell(Daten)\nFehler = Tatsächlich - Vorhersage',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Datenqualität bestimmt Modellerfolg."'
            },
            'it': {
                'title': 'Machine Learning nella Finanza',
                'concept_definition': 'Il machine learning permette ai computer di imparare dai dati. Utilizzato per previsioni finanziarie, modellazione del rischio e rilevamento frodi. La qualità dei dati è importante.',
                'practical_example': 'Modello semplice: Puoi prevedere i prezzi futuri usando i dati dei prezzi storici. Tuttavia, il passato non garantisce il futuro.',
                'mathematical_formula': 'Previsione = Modello(Dati)\nErrore = Reale - Previsione',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La qualità dei dati determina il successo del modello."'
            }
        },
        'blockchain_crypto': {
            'tr': {
                'title': 'Blockchain ve Kripto',
                'concept_definition': 'Blockchain, dağıtık bir defter teknolojisidir. Kripto paralar, blockchain tabanlı dijital para birimleridir. Bitcoin ve Ethereum en bilinen kripto paralardır. Volatilite yüksektir.',
                'practical_example': 'Bitcoin, 21 milyon adet ile sınırlıdır. Bu, kıtlık yaratır. Ancak fiyat çok dalgalanır. Sadece kaybetmeyi göze alabileceğiniz kadar yatırım yapın.',
                'mathematical_formula': 'Kripto Getirisi = (Son Fiyat - İlk Fiyat) / İlk Fiyat',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Kripto, yüksek risk yüksek getiridir."'
            },
            'en': {
                'title': 'Blockchain & Crypto',
                'concept_definition': 'Blockchain is a distributed ledger technology. Cryptocurrencies are blockchain-based digital currencies. Bitcoin and Ethereum are the most well-known cryptocurrencies. Volatility is high.',
                'practical_example': 'Bitcoin is limited to 21 million units. This creates scarcity. However, price fluctuates a lot. Only invest what you can afford to lose.',
                'mathematical_formula': 'Crypto Return = (Final Price - Initial Price) / Initial Price',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Crypto is high risk high return."'
            },
            'de': {
                'title': 'Blockchain & Krypto',
                'concept_definition': 'Blockchain ist eine Distributed Ledger Technologie. Kryptowährungen sind blockchain-basierte digitale Währungen. Bitcoin und Ethereum sind die bekanntesten Kryptowährungen. Volatilität ist hoch.',
                'practical_example': 'Bitcoin ist auf 21 Millionen Einheiten begrenzt. Dies schafft Knappheit. Der Preis schwankt jedoch stark. Investieren Sie nur, was Sie verlieren können.',
                'mathematical_formula': 'Krypto-Rendite = (Endpreis - Anfangspreis) / Anfangspreis',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Krypto ist hohes Risiko hohe Rendite."'
            },
            'it': {
                'title': 'Blockchain e Cripto',
                'concept_definition': 'La blockchain è una tecnologia a libro mastro distribuito. Le criptovalute sono valute digitali basate su blockchain. Bitcoin ed Ethereum sono le criptovalute più conosciute. La volatilità è alta.',
                'practical_example': 'Bitcoin è limitato a 21 milioni di unità. Questo crea scarsità. Tuttavia, il prezzo fluttua molto. Investi solo ciò che puoi permetterti di perdere.',
                'mathematical_formula': 'Rendimento Cripto = (Prezzo Finale - Prezzo Iniziale) / Prezzo Iniziale',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La cripto è alto rischio alto rendimento."'
            }
        },
        'esg_investing': {
            'tr': {
                'title': 'ESG Yatırımı',
                'concept_definition': 'ESG yatırımı, çevresel, sosyal ve yönetişim kriterlerini dikkate alır. Sürdürülebilir şirketlere yatırım yapar. Uzun vadeli sürdürülebilirlik önemlidir.',
                'practical_example': 'ESG puanı yüksek şirketler genellikle daha az risklidir. Çevreye duyarlı şirketler, düzenleyici risklerden korunur. Sosyal sorumluluk, marka değerini artırır.',
                'mathematical_formula': 'ESG Skoru = (Çevresel + Sosyal + Yönetişim) / 3',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "ESG, sadece finansal getiri değil, sosyal etki de önemlidir."'
            },
            'en': {
                'title': 'ESG Investing',
                'concept_definition': 'ESG investing considers environmental, social, and governance criteria. Invests in sustainable companies. Long-term sustainability is important.',
                'practical_example': 'Companies with high ESG scores are generally less risky. Environmentally friendly companies are protected from regulatory risks. Social responsibility increases brand value.',
                'mathematical_formula': 'ESG Score = (Environmental + Social + Governance) / 3',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "ESG is not just about financial returns, but also social impact."'
            },
            'de': {
                'title': 'ESG-Investition',
                'concept_definition': 'ESG-Investition berücksichtigt Umwelt-, Sozial- und Unternehmensführungskriterien. Investiert in nachhaltige Unternehmen. Langfristige Nachhaltigkeit ist wichtig.',
                'practical_example': 'Unternehmen mit hohen ESG-Scores sind generally weniger riskant. Umweltfreundliche Unternehmen sind vor regulatorischen Risiken geschützt. Soziale Verantwortung erhöht den Markenwert.',
                'mathematical_formula': 'ESG-Score = (Umwelt + Sozial + Unternehmensführung) / 3',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "ESG ist nicht nur finanzielle Rendite, sondern auch soziale Wirkung."'
            },
            'it': {
                'title': 'Investimento ESG',
                'concept_definition': 'L\'investimento ESG considera criteri ambientali, sociali e di governance. Investe in aziende sostenibili. La sostenibilità a lungo termine è importante.',
                'practical_example': 'Le aziende con punteggi ESG elevati sono generalmente meno rischiose. Le aziende rispettose dell\'ambiente sono protette dai rischi normativi. La responsabilità sociale aumenta il valore del marchio.',
                'mathematical_formula': 'Punteggio ESG = (Ambientale + Sociale + Governance) / 3',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "L\'ESG non riguarda solo i rendimenti finanziari, ma anche l\'impatto sociale."'
            }
        }
    },
    'intermediate': {
        'income_expenses': {
            'tr': {
                'title': 'Gelir ve Giderler - Orta Seviye',
                'concept_definition': 'Orta seviyede gelir ve gider yönetimi, nakit akışı optimizasyonunu içerir. Aktif geliri pasif gelire dönüştürmek, vergi avantajlı hesapları kullanmak ve 50/30/20 bütçe kuralını uygulamak önemlidir. Nakit akışı tablosu oluşturmak, finansal sağlığı anlamak için kritiktir.',
                'practical_example': 'Zeynep aktif geliri 15.000 TL. Pasif geliri (kira + temettü) 2.000 TL. Toplam gelir 17.000 TL. 50/30/20 kuralına göre: 8.500 TL ihtiyaçlar, 5.100 TL istekler, 3.400 TL tasarruf/yatırım.',
                'mathematical_formula': 'Nakit Akışı = (Gelir + Pasif Gelir) - (Giderler + Vergiler)',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Gelir arttıkça harcamalar da artar. Bu lifestyle creep olarak bilinir. Gelir arttıkça yaşam tarzınızı artırmayın, tasarruf oranınızı artırın."'
            },
            'en': {
                'title': 'Income & Expenses - Intermediate',
                'concept_definition': 'Intermediate income and expense management includes cash flow optimization. Converting active income to passive income, using tax-advantaged accounts, and applying the 50/30/20 budget rule are important. Creating a cash flow statement is critical to understanding financial health.',
                'practical_example': 'Zeynep has active income of 15,000 TL. Passive income (rent + dividends) is 2,000 TL. Total income is 17,000 TL. According to 50/30/20 rule: 8,500 TL needs, 5,100 TL wants, 3,400 TL savings/investment.',
                'mathematical_formula': 'Cash Flow = (Income + Passive Income) - (Expenses + Taxes)',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "As income increases, expenses also increase. This is known as lifestyle creep. Don\'t increase your lifestyle as income increases, increase your savings rate."'
            },
            'de': {
                'title': 'Einkommen und Ausgaben - Mittelstufe',
                'concept_definition': 'Einkommens- und Ausgabenmanagement auf mittlerer Stufe umfasst die Cashflow-Optimierung. Die Umwandlung von aktivem Einkommen in passives Einkommen, die Nutzung steuerbegünstigter Konten und die Anwendung der 50/30/20-Budgetregel sind wichtig. Die Erstellung einer Cashflow-Abrechnung ist entscheidend für das Verständnis der finanziellen Gesundheit.',
                'practical_example': 'Zeynep hat ein aktives Einkommen von 15.000 TL. Passives Einkommen (Miete + Dividenden) beträgt 2.000 TL. Gesamteinkommen ist 17.000 TL. Nach der 50/30/20-Regel: 8.500 TL Bedürfnisse, 5.100 TL Wünsche, 3.400 TL Ersparnisse/Investitionen.',
                'mathematical_formula': 'Cashflow = (Einkommen + Passives Einkommen) - (Ausgaben + Steuern)',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "Mit steigendem Einkommen steigen auch die Ausgaben. Dies wird als Lifestyle Creep bezeichnet. Erhöhen Sie nicht Ihren Lebensstil mit steigendem Einkommen, erhöhen Sie Ihre Sparquote."'
            },
            'it': {
                'title': 'Reddito e Spese - Intermedio',
                'concept_definition': 'La gestione del reddito e delle spese a livello intermedio include l\'ottimizzazione del flusso di cassa. Convertire il reddito attivo in reddito passivo, utilizzare conti con vantaggi fiscali e applicare la regola del budget 50/30/20 è importante. Creare un rendiconto del flusso di cassa è fondamentale per comprendere la salute finanziaria.',
                'practical_example': 'Zeynep ha un reddito attivo di 15.000 TL. Il reddito passivo (affitto + dividendi) è 2.000 TL. Il reddito totale è 17.000 TL. Secondo la regola 50/30/20: 8.500 TL bisogni, 5.100 TL desideri, 3.400 TL risparmio/investimento.',
                'mathematical_formula': 'Flusso di Cassa = (Reddito + Reddito Passivo) - (Spese + Tasse)',
                'python_function': 'calculate_50_30_20_budget(monthly_income)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "Con l\'aumento del reddito, aumentano anche le spese. Questo è noto come lifestyle creep. Non aumentare il tuo stile di vita con l\'aumento del reddito, aumenta il tuo tasso di risparmio."'
            }
        },
        'compound_interest': {
            'tr': {
                'title': 'Bileşik Faiz - Orta Seviye',
                'concept_definition': 'Orta seviyede bileşik faiz, enflasyon ayarlı reel getiri ve farklı bileşikleşme frekanslarını içerir. Aylık, üç aylık ve yıllık bileşikleşme farkları önemlidir. Bileşik faizin borç üzerindeki yıkıcı etkisi (kredi kartı borçları) de anlaşılmalıdır.',
                'practical_example': 'Kredi kartı borcu 50.000 TL, yıllık faiz %18. Eğer minimum ödeme yaparsa, borç 10 yılda 150.000 TL\'ye çıkar. Aynı parayı %8 getiriyle yatırırsanız, 10 yılda 107.000 TL olur.',
                'mathematical_formula': 'Reel Getiri = (1 + Nominal Getiri) / (1 + Enflasyon) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Bileşik faiz borç için de çalışır. Bu, finansal kargaşanın en büyük nedenlerinden biridir."'
            },
            'en': {
                'title': 'Compound Interest - Intermediate',
                'concept_definition': 'Intermediate compound interest includes inflation-adjusted real returns and different compounding frequencies. Monthly, quarterly, and annual compounding differences are important. The destructive effect of compound interest on debt (credit card debt) must also be understood.',
                'practical_example': 'Credit card debt is 50,000 TL, annual interest 18%. If you make minimum payments, the debt grows to 150,000 TL in 10 years. If you invest the same money at 8% return, it becomes 107,000 TL in 10 years.',
                'mathematical_formula': 'Real Return = (1 + Nominal Return) / (1 + Inflation) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Compound interest also works for debt. This is one of the biggest causes of financial distress."'
            },
            'de': {
                'title': 'Zinseszins - Mittelstufe',
                'concept_definition': 'Zinseszins auf mittlerer Stufe umfasst inflationsbereinigte reale Renditen und verschiedene Zinseszinsfrequenzen. Unterschiede zwischen monatlicher, vierteljährlicher und jährlicher Verzinsung sind wichtig. Die zerstörerische Wirkung von Zinseszins auf Schulden (Kreditkartenschulden) muss ebenfalls verstanden werden.',
                'practical_example': 'Kreditkartenschuld beträgt 50.000 TL, jährlicher Zins 18%. Wenn Sie Mindestzahlungen leisten, wächst die Schuld in 10 Jahren auf 150.000 TL. Wenn Sie das gleiche Geld bei 8% Rendite investieren, wird es in 10 Jahren zu 107.000 TL.',
                'mathematical_formula': 'Reale Rendite = (1 + Nominale Rendite) / (1 + Inflation) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Zinseszins funktioniert auch für Schulden. Dies ist eine der größten Ursachen für finanzielle Not."'
            },
            'it': {
                'title': 'Interesse Composto - Intermedio',
                'concept_definition': 'L\'interesse composto a livello intermedio include rendimenti reali corretti per l\'inflazione e diverse frequenze di composizione. Le differenze tra composizione mensile, trimestrale e annuale sono importanti. L\'effetto distruttivo dell\'interesse composto sul debito (debito su carta di credito) deve essere compreso.',
                'practical_example': 'Il debito della carta di credito è 50.000 TL, interesse annuale 18%. Se fai pagamenti minimi, il debito cresce a 150.000 TL in 10 anni. Se investi la stessa cifra al 8% di rendimento, diventa 107.000 TL in 10 anni.',
                'mathematical_formula': 'Rendimento Reale = (1 + Rendimento Nominale) / (1 + Inflazione) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "L\'interesse composto funziona anche per il debito. Questa è una delle maggiori cause di disagio finanziario."'
            }
        },
        'assets': {
            'tr': {
                'title': 'Varlıklar ve Varlık Sınıfları - Orta Seviye',
                'concept_definition': 'Orta seviyede varlık yönetimi, varlık tahsisi ve portföy çeşitlendirmesini içerir. Modern Portföy Teorisi (MPT), riski azaltmak için negatif korelasyonlu varlıkları birleştirmeyi önerir. Yatırım fonları ve ETF\'ler, bireysel yatırımcılar için uygun araçlardır.',
                'practical_example': 'Portföy: %40 hisse senedi (S&P 500), %30 tahvil (devlet tahvili), %20 gayrimenkul (REIT), %10 emtia (altın). Bu çeşitlendirme piyasa çöküşlerinde koruma sağlar.',
                'mathematical_formula': 'Portföy Varyansı = Σ(wi² × σi²) + ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Çeşitlendirme, yatırımcının en iyi arkadaşıdır. Tüm yumurtaları aynı sepete koymayın."'
            },
            'en': {
                'title': 'Assets & Asset Classes - Intermediate',
                'concept_definition': 'Intermediate asset management includes asset allocation and portfolio diversification. Modern Portfolio Theory (MPT) suggests combining negatively correlated assets to reduce risk. Mutual funds and ETFs are suitable instruments for individual investors.',
                'practical_example': 'Portfolio: 40% stocks (S&P 500), 30% bonds (government bonds), 20% real estate (REIT), 10% commodities (gold). This diversification provides protection during market crashes.',
                'mathematical_formula': 'Portfolio Variance = Σ(wi² × σi²) + ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Diversification is the investor\'s best friend. Don\'t put all your eggs in one basket."'
            },
            'de': {
                'title': 'Vermögenswerte und Anlageklassen - Mittelstufe',
                'concept_definition': 'Vermögensverwaltung auf mittlerer Stufe umfasst Asset Allocation und Portfolio-Diversifizierung. Die Moderne Portfolio-Theorie (MPT) schlägt vor, negativ korrelierte Vermögenswerte zu kombinieren, um das Risiko zu reduzieren. Investmentfonds und ETFs sind geeignete Instrumente für Einzelanleger.',
                'practical_example': 'Portfolio: 40% Aktien (S&P 500), 30% Anleihen (Staatsanleihen), 20% Immobilien (REIT), 10% Rohstoffe (Gold). Diese Diversifizierung bietet Schutz während Marktzusammenbrüchen.',
                'mathematical_formula': 'Portfolio-Varianz = Σ(wi² × σi²) + ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Diversifizierung ist der beste Freund des Investors. Legen Sie nicht alle Eier in einen Korb."'
            },
            'it': {
                'title': 'Attività e Classi di Attività - Intermedio',
                'concept_definition': 'La gestione delle attività a livello intermedio include l\'allocazione delle attività e la diversificazione del portafoglio. La Teoria del Portafoglio Moderno (MPT) suggerisce di combinare attività correlate negativamente per ridurre il rischio. I fondi comuni e gli ETF sono strumenti adatti per gli investitori individuali.',
                'practical_example': 'Portafoglio: 40% azioni (S&P 500), 30% obbligazioni (titoli di stato), 20% immobili (REIT), 10% materie prime (oro). Questa diversificazione fornisce protezione durante i crolli del mercato.',
                'mathematical_formula': 'Varianza del Portafoglio = Σ(wi² × σi²) + ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La diversificazione è il migliore amico dell\'investitore. Non mettere tutte le uova nello stesso paniere."'
            }
        },
        'financial_freedom': {
            'tr': {
                'title': 'Finansal Özgürlük - Orta Seviye',
                'concept_definition': 'Orta seviyede finansal özgürlük, 4% Kuralının matematiksel temelini ve çekim oranlarının riskini içerir. Çekim oranı %4\'ten düşük olduğunda risk azalır, ancak gerekli birikim artar. Vergi avantajlı hesaplar (BES, 401k) finansal özgürlüğü hızlandırır.',
                'practical_example': 'Yıllık harcama 200.000 TL. %3 çekim oranıyla FI sayısı = 200.000 / 0.03 = 6.666.667 TL. %5 çekim oranıyla FI sayısı = 200.000 / 0.05 = 4.000.000 TL. Çekim oranı seçimi risk toleransına bağlıdır.',
                'mathematical_formula': 'Güvenli Çekim Oranı = (Tarihsel Getiri - Enflasyon) × (1 - Güvenlik Marjı)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Finansal özgürlük bir rakam değil, bir yaşam tarzıdır. Daha az harcamayı öğrenmek, daha çok kazanmaktan daha önemlidir."'
            },
            'en': {
                'title': 'Financial Freedom - Intermediate',
                'concept_definition': 'Intermediate financial freedom includes the mathematical basis of the 4% Rule and the risk of withdrawal rates. When withdrawal rate is lower than 4%, risk decreases, but required savings increase. Tax-advantaged accounts (BES, 401k) accelerate financial freedom.',
                'practical_example': 'Annual expense is 200,000 TL. With 3% withdrawal rate, FI number = 200,000 / 0.03 = 6,666,667 TL. With 5% withdrawal rate, FI number = 200,000 / 0.05 = 4,000,000 TL. Withdrawal rate choice depends on risk tolerance.',
                'mathematical_formula': 'Safe Withdrawal Rate = (Historical Return - Inflation) × (1 - Safety Margin)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Financial freedom is not a number, it\'s a lifestyle. Learning to spend less is more important than learning to earn more."'
            },
            'de': {
                'title': 'Finanzielle Freiheit - Mittelstufe',
                'concept_definition': 'Finanzielle Freiheit auf mittlerer Stufe umfasst die mathematische Grundlage der 4%-Regel und das Risiko von Entnahmeraten. Wenn die Entnahmerate unter 4% liegt, sinkt das Risiko, aber die erforderlichen Ersparnisse steigen. Steuerbegünstigte Konten (BES, 401k) beschleunigen die finanzielle Freiheit.',
                'practical_example': 'Jährliche Ausgabe beträgt 200.000 TL. Mit 3% Entnahmerate beträgt die FI-Zahl = 200.000 / 0,03 = 6.666.667 TL. Mit 5% Entnahmerate beträgt die FI-Zahl = 200.000 / 0,05 = 4.000.000 TL. Die Wahl der Entnahmerate hängt von der Risikotoleranz ab.',
                'mathematical_formula': 'Sichere Entnahmerate = (Historische Rendite - Inflation) × (1 - Sicherheitsmarge)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Finanzielle Freiheit ist keine Zahl, sondern ein Lebensstil. Weniger auszugeben zu lernen, ist wichtiger als mehr zu verdienen."'
            },
            'it': {
                'title': 'Libertà Finanziaria - Intermedio',
                'concept_definition': 'La libertà finanziaria a livello intermedio include la base matematica della regola del 4% e il rischio dei tassi di prelievo. Quando il tasso di prelievo è inferiore al 4%, il rischio diminuisce, ma il risparmio richiesto aumenta. I conti con vantaggi fiscali (BES, 401k) accelerano la libertà finanziaria.',
                'practical_example': 'La spesa annuale è 200.000 TL. Con un tasso di prelievo del 3%, il numero FI = 200.000 / 0,03 = 6.666.667 TL. Con un tasso di prelievo del 5%, il numero FI = 200.000 / 0,05 = 4.000.000 TL. La scelta del tasso di prelievo dipende dalla tolleranza al rischio.',
                'mathematical_formula': 'Tasso di Prelievo Sicuro = (Rendimento Storico - Inflazione) × (1 - Margine di Sicurezza)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "La libertà finanziaria non è un numero, è uno stile di vita. Imparare a spendere meno è più importante di imparare a guadagnare di più."'
            }
        },
        'investing': {
            'tr': {
                'title': 'Yatırım ve Yatırım Araçları - Orta Seviye',
                'concept_definition': 'Orta seviyede yatırım, risk ayarlı getiri metriklerini (Sharpe Oranı, Sortino Oranı) ve portföy rebalancing (dengeleme) stratejilerini içerir. Dolar Maliyet Ortalaması (DCA) ve Value Averaging (Değer Ortalaması) karşılaştırılır. Piyasa zamanlaması yerine düzenli yatırım önerilir.',
                'practical_example': 'Portföy başlangıç: %60 hisse, %40 tahvil. Bir yıl sonra hisse %70, tahvil %30 oldu. Rebalancing ile orijinal %60/%40 oranına dönülür. Bu, düşük fiyatlı varlıkları alıp yüksek fiyatlı varlıkları satmak demektir.',
                'mathematical_formula': 'Sharpe Oranı = (Portföy Getirisi - Risksiz Faiz) / Portföy Standart Sapması',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Piyasa zamanlaması imkansızdır. Düzenli yatırım yapın ve sabırlı olun."'
            },
            'en': {
                'title': 'Investing & Investment Vehicles - Intermediate',
                'concept_definition': 'Intermediate investing includes risk-adjusted return metrics (Sharpe Ratio, Sortino Ratio) and portfolio rebalancing strategies. Dollar Cost Averaging (DCA) and Value Averaging are compared. Regular investing is recommended over market timing.',
                'practical_example': 'Portfolio initial: 60% stocks, 40% bonds. After one year, stocks became 70%, bonds 30%. With rebalancing, return to original 60%/40 ratio. This means buying low-priced assets and selling high-priced assets.',
                'mathematical_formula': 'Sharpe Ratio = (Portfolio Return - Risk Free Rate) / Portfolio Standard Deviation',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "Market timing is impossible. Invest regularly and be patient."'
            },
            'de': {
                'title': 'Investieren und Anlageinstrumente - Mittelstufe',
                'concept_definition': 'Investieren auf mittlerer Stufe umfasst risikobereinigte Renditemetriken (Sharpe Ratio, Sortino Ratio) und Portfolio-Rebalancing-Strategien. Dollar Cost Averaging (DCA) und Value Averaging werden verglichen. Regelmäßiges Investieren wird gegenüber Market Timing empfohlen.',
                'practical_example': 'Portfolio initial: 60% Aktien, 40% Anleihen. Nach einem Jahr wurden Aktien zu 70%, Anleihen zu 30%. Mit Rebalancing wird zum ursprünglichen 60%/40-Verhältnis zurückgekehrt. Dies bedeutet, niedrig bewertete Vermögenswerte zu kaufen und hoch bewertete zu verkaufen.',
                'mathematical_formula': 'Sharpe Ratio = (Portfoliorendite - Risikofreier Zins) / Portfolio-Standardabweichung',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "Market Timing ist unmöglich. Investieren Sie regelmäßig und seien Sie geduldig."'
            },
            'it': {
                'title': 'Investire e Strumenti di Investimento - Intermedio',
                'concept_definition': 'L\'investimento a livello intermedio include metriche di rendimento aggiustate per il rischio (Sharpe Ratio, Sortino Ratio) e strategie di ribilanciamento del portafoglio. Dollar Cost Averaging (DCA) e Value Averaging vengono confrontati. L\'investimento regolare è raccomandato rispetto al time del mercato.',
                'practical_example': 'Portafoglio iniziale: 60% azioni, 40% obbligazioni. Dopo un anno, le azioni sono diventate 70%, le obbligazioni 30%. Con il ribilanciamento, si torna al rapporto originale 60%/40. Questo significa acquistare attività a basso prezzo e vendere attività a prezzo alto.',
                'mathematical_formula': 'Sharpe Ratio = (Rendimento del Portafoglio - Tasso Senza Rischio) / Deviazione Standard del Portafoglio',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "Il time del mercato è impossibile. Investi regolarmente e sii paziente."'
            }
        },
        'risk_management': {
            'tr': {
                'title': 'Risk Yönetimi - Orta Seviye',
                'concept_definition': 'Orta seviyede risk yönetimi, risk ayarlı getiri metriklerini (Sharpe Oranı, Sortino Oranı) ve risk bütçelemesini içerir. Risk limitleri belirlemek ve risk takibi yapmak önemlidir. Stop-loss ve hedging stratejileri riski azaltır.',
                'practical_example': 'Portföy Sharpe Oranı 1.5. Bu, risksiz faize göre 1.5 kat daha iyi performans gösterir. Stop-loss %10 olarak ayarlanır. Hisse %10 düşerse otomatik satılır, daha fazla kayıp önlenir.',
                'mathematical_formula': 'Sortino Oranı = (Portföy Getirisi - Risksiz Faiz) / Negatif Sapma',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Risk, standart sapma değildir. Risk, beklenmedik olayların potansiyel etkisidir."'
            },
            'en': {
                'title': 'Risk Management - Intermediate',
                'concept_definition': 'Intermediate risk management includes risk-adjusted return metrics (Sharpe Ratio, Sortino Ratio) and risk budgeting. Setting risk limits and risk monitoring are important. Stop-loss and hedging strategies reduce risk.',
                'practical_example': 'Portfolio Sharpe Ratio is 1.5. This means it performs 1.5 times better than risk-free rate. Stop-loss is set at 10%. If stock drops 10%, it automatically sells, preventing further loss.',
                'mathematical_formula': 'Sortino Ratio = (Portfolio Return - Risk Free Rate) / Downside Deviation',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Risk is not standard deviation. Risk is the potential impact of unexpected events."'
            },
            'de': {
                'title': 'Risikomanagement - Mittelstufe',
                'concept_definition': 'Risikomanagement auf mittlerer Stufe umfasst risikobereinigte Renditemetriken (Sharpe Ratio, Sortino Ratio) und Risk Budgeting. Risikolimits festzulegen und Risikoüberwachung sind wichtig. Stop-Loss und Hedging-Strategien reduzieren das Risiko.',
                'practical_example': 'Portfolio Sharpe Ratio ist 1,5. Dies bedeutet, es performs 1,5-mal besser als risikofreier Zins. Stop-Loss wird auf 10% gesetzt. Wenn Aktie um 10% fällt, wird sie automatisch verkauft, was weiteren Verlust verhindert.',
                'mathematical_formula': 'Sortino Ratio = (Portfoliorendite - Risikofreier Zins) / Downside-Abweichung',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Risiko ist keine Standardabweichung. Risiko ist die potenzielle Auswirkung unerwarteter Ereignisse."'
            },
            'it': {
                'title': 'Gestione del Rischio - Intermedio',
                'concept_definition': 'La gestione del rischio a livello intermedio include metriche di rendimento aggiustate per il rischio (Sharpe Ratio, Sortino Ratio) e il risk budgeting. Impostare limiti di rischio e il monitoraggio del rischio sono importanti. Le strategie stop-loss e hedging riducono il rischio.',
                'practical_example': 'Il Sharpe Ratio del portafoglio è 1.5. Questo significa che performs 1.5 volte meglio del tasso senza rischio. Lo stop-loss è impostato al 10%. Se l\'azione scende del 10%, viene venduta automaticamente, prevenendo ulteriori perdite.',
                'mathematical_formula': 'Sortino Ratio = (Rendimento del Portafoglio - Tasso Senza Rischio) / Deviazione Negativa',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il rischio non è la deviazione standard. Il rischio è l\'impatto potenziale di eventi imprevisti."'
            }
        },
        'portfolio_optimization': {
            'tr': {
                'title': 'Portföy Optimizasyonu - Orta Seviye',
                'concept_definition': 'Orta seviyede portföy optimizasyonu, Etkili Sınır (Efficient Frontier) ve Modern Portföy Teorisi\'ni içerir. Risk ayarlı getiri maksimizasyonu hedeflenir. Rebalancing stratejileri uygulanır.',
                'practical_example': 'Etkili sınır üzerinde optimal portföy: %50 hisse, %30 tahvil, %20 altın. Bu portföy Sharpe oranı 1.8 ile maksimize eder. Yılda bir rebalancing yapılır.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Rebalancing, disiplinli yatırımın anahtarıdır."'
            },
            'en': {
                'title': 'Portfolio Optimization - Intermediate',
                'concept_definition': 'Intermediate portfolio optimization includes Efficient Frontier and Modern Portfolio Theory. Risk-adjusted return maximization is targeted. Rebalancing strategies are applied.',
                'practical_example': 'Optimal portfolio on efficient frontier: 50% stocks, 30% bonds, 20% gold. This portfolio maximizes Sharpe ratio at 1.8. Rebalancing is done annually.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Rebalancing is the key to disciplined investing."'
            },
            'de': {
                'title': 'Portfolio-Optimierung - Mittelstufe',
                'concept_definition': 'Portfolio-Optimierung auf mittlerer Stufe umfasst Effiziente Grenze und Moderne Portfolio-Theorie. Risikobereinigte Renditemaximierung wird angestrebt. Rebalancing-Strategien werden angewendet.',
                'practical_example': 'Optimales Portfolio auf effizienter Grenze: 50% Aktien, 30% Anleihen, 20% Gold. Dieses Portfolio maximiert Sharpe Ratio bei 1,8. Rebalancing wird jährlich durchgeführt.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Rebalancing ist der Schlüssel zum disziplinierten Investieren."'
            },
            'it': {
                'title': 'Ottimizzazione del Portafoglio - Intermedio',
                'concept_definition': 'L\'ottimizzazione del portafoglio a livello intermedio include la Frontiera Efficiente e la Teoria del Portafoglio Moderno. La massimizzazione del rendimento aggiustato per il rischio è mirata. Le strategie di ribilanciamento vengono applicate.',
                'practical_example': 'Portafoglio ottimale sulla frontiera efficiente: 50% azioni, 30% obbligazioni, 20% oro. Questo portafoglio massimizza il Sharpe ratio a 1.8. Il ribilanciamento viene fatto annualmente.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "Il ribilanciamento è la chiave per investire con disciplina."'
            }
        },
        'behavioral_finance': {
            'tr': {
                'title': 'Davranışsal Finans - Orta Seviye',
                'concept_definition': 'Orta seviyede davranışsal finans, bias tanıma ve yönetimini içerir. Kayıp aversionı, aşırı güven, mental accounting ve anchoring bias\'lar analiz edilir. Duygusal kararları önlemek için stratejiler geliştirilir.',
                'practical_example': 'Kayıp aversionı: 100 TL kaybetmenin acısı, 100 TL kazanmanın sevincinden 2 kat daha fazladır. Bu yüzden yatırımcılar kaybeden pozisyonları çok uzun tutarlar. Stop-loss ile bu bias azaltılır.',
                'mathematical_formula': 'Kayıp Aversion Oranı = (Kazanç Değeri / Kayıp Değeri) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Finansal kararlarınızın %90\'ı psikolojiktir, teknik değildir."'
            },
            'en': {
                'title': 'Behavioral Finance - Intermediate',
                'concept_definition': 'Intermediate behavioral finance includes bias recognition and management. Loss aversion, overconfidence, mental accounting, and anchoring biases are analyzed. Strategies are developed to prevent emotional decisions.',
                'practical_example': 'Loss aversion: The pain of losing 100 TL is twice the pleasure of gaining 100 TL. Therefore, investors hold losing positions too long. Stop-loss reduces this bias.',
                'mathematical_formula': 'Loss Aversion Ratio = (Gain Value / Loss Value) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "90% of your financial decisions are psychological, not technical."'
            },
            'de': {
                'title': 'Verhaltensfinanz - Mittelstufe',
                'concept_definition': 'Verhaltensfinanz auf mittlerer Stufe umfasst Bias-Erkennung und -Management. Verlustaversion, Überkonfidenz, Mental Accounting und Anchoring-Biases werden analysiert. Strategien werden entwickelt, um emotionale Entscheidungen zu verhindern.',
                'practical_example': 'Verlustaversion: Der Schmerz, 100 TL zu verlieren, ist doppelt so groß wie die Freude, 100 TL zu gewinnen. Daher halten Investoren verlustbringende Positionen zu lange. Stop-Loss reduziert diesen Bias.',
                'mathematical_formula': 'Verlustaversion Ratio = (Gewinnwert / Verlustwert) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "90% Ihrer finanziellen Entscheidungen sind psychologisch, nicht technisch."'
            },
            'it': {
                'title': 'Finanza Comportamentale - Intermedio',
                'concept_definition': 'La finanza comportamentale a livello intermedio include il riconoscimento e la gestione dei bias. L\'avversione alla perdita, l\'eccessiva fiducia, il mental accounting e i bias di ancoraggio vengono analizzati. Vengono sviluppate strategie per prevenire decisioni emotive.',
                'practical_example': 'Avversione alla perdita: Il dolore di perdere 100 TL è doppio rispetto al piacere di guadagnare 100 TL. Pertanto, gli investitori mantengono posizioni in perdita troppo a lungo. Lo stop-loss riduce questo bias.',
                'mathematical_formula': 'Avversione alla Perdita Ratio = (Valore Guadagno / Valore Perdita) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "Il 90% delle tue decisioni finanziarie è psicologico, non tecnico."'
            }
        },
        'tax_planning': {
            'tr': {
                'title': 'Vergi Planlaması - Orta Seviye',
                'concept_definition': 'Orta seviyede vergi planlaması, vergi avantajlı hesapları (BES, 401k, IRA) ve vergi tasarruf stratejilerini içerir. Sermaye kazancı vergisi, temettü vergisi ve vergi arbitrajı analiz edilir.',
                'practical_example': 'BES hesabına yıllık 50.000 TL yatırırsanız, %15 vergi indirimi alırsınız. Bu, 7.500 TL vergi tasarrufu demektir. Sermaye kazancı vergisi %20 ise, vergi avantajlı hesaplarla bu vergi ertelenebilir.',
                'mathematical_formula': 'Vergi Tasarrufu = Yatırım × Vergi Oranı\nVergi Arbitrajı = Vergi Farkı × Pozisyon',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Zengin Baba, Yoksul Baba" kitabında Robert Kiyosaki şunu söylüyor: "Vergi planlaması, zenginlerin sırrıdır."'
            },
            'en': {
                'title': 'Tax Planning - Intermediate',
                'concept_definition': 'Intermediate tax planning includes tax-advantaged accounts (BES, 401k, IRA) and tax saving strategies. Capital gains tax, dividend tax, and tax arbitrage are analyzed.',
                'practical_example': 'If you invest 50,000 TL annually in a BES account, you get a 15% tax deduction. This means 7,500 TL tax savings. If capital gains tax is 20%, this tax can be deferred with tax-advantaged accounts.',
                'mathematical_formula': 'Tax Savings = Investment × Tax Rate\nTax Arbitrage = Tax Difference × Position',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Rich Dad Poor Dad", Robert Kiyosaki says: "Tax planning is the secret of the rich."'
            },
            'de': {
                'title': 'Steuerplanung - Mittelstufe',
                'concept_definition': 'Steuerplanung auf mittlerer Stufe umfasst steuerbegünstigte Konten (BES, 401k, IRA) und Steuereinsparungsstrategien. Kapitalertragsteuer, Dividendensteuer und Steuerarbitrage werden analysiert.',
                'practical_example': 'Wenn Sie jährlich 50.000 TL in ein BES-Konto investieren, erhalten Sie eine 15% Steuerabzug. Dies bedeutet 7.500 TL Steuereinsparung. Wenn Kapitalertragsteuer 20% ist, kann diese Steuer mit steuerbegünstigten Konten aufgeschoben werden.',
                'mathematical_formula': 'Steuereinsparung = Investition × Steuersatz\nSteuerarbitrage = Steuerdifferenz × Position',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Reicher Vater, armer Vater" sagt Robert Kiyosaki: "Steuerplanung ist das Geheimnis der Reichen."'
            },
            'it': {
                'title': 'Pianificazione Fiscale - Intermedio',
                'concept_definition': 'La pianificazione fiscale a livello intermedio include conti con vantaggi fiscali (BES, 401k, IRA) e strategie di risparmio fiscale. La tassa sui guadagni in capitale, la tassa sui dividendi e l\'arbitraggio fiscale vengono analizzati.',
                'practical_example': 'Se investi 50.000 TL all\'anno in un conto BES, ottieni una detrazione fiscale del 15%. Questo significa 7.500 TL di risparmio fiscale. Se la tassa sui guadagni in capitale è del 20%, questa tassa può essere differita con conti con vantaggi fiscali.',
                'mathematical_formula': 'Risparmio Fiscale = Investimento × Aliquota Fiscale\nArbitraggio Fiscale = Differenza Fiscale × Posizione',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Padre Ricco, Padre Povero", Robert Kiyosaki dice: "La pianificazione fiscale è il segreto dei ricchi."'
            }
        },
        'retirement_planning': {
            'tr': {
                'title': 'Emeklilik Planlaması - Orta Seviye',
                'concept_definition': 'Orta seviyede emeklilik planlaması, emeklilik yaşı hesaplaması, sosyal güvenlik optimizasyonu ve emeklilik gelir kaynaklarını içerir. 4% kuralının dinamik versiyonları kullanılır.',
                'practical_example': 'Emeklilik yaşı 65, yaşam beklentisi 90. 25 yıl emeklilik. Yıllık harcama 200.000 TL. %3 çekim oranıyla gerekli birikim = 200.000 / 0.03 = 6.666.667 TL. %5 çekim oranıyla = 4.000.000 TL.',
                'mathematical_formula': 'Emeklilik Birikimi = Yıllık Harcama × (1 - (1 + r)^(-n)) / r\nDinamik Çekim = Önceki Çekim × (1 + Enflasyon - Getiri)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Emeklilik, işten ayrılmak değil, finansal özgürlüktür."'
            },
            'en': {
                'title': 'Retirement Planning - Intermediate',
                'concept_definition': 'Intermediate retirement planning includes retirement age calculation, social security optimization, and retirement income sources. Dynamic versions of the 4% rule are used.',
                'practical_example': 'Retirement age 65, life expectancy 90. 25 years of retirement. Annual expense 200,000 TL. With 3% withdrawal rate, required savings = 200,000 / 0.03 = 6,666,667 TL. With 5% withdrawal rate = 4,000,000 TL.',
                'mathematical_formula': 'Retirement Savings = Annual Expense × (1 - (1 + r)^(-n)) / r\nDynamic Withdrawal = Previous Withdrawal × (1 + Inflation - Return)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Retirement is not quitting work, it\'s financial freedom."'
            },
            'de': {
                'title': 'Rentenplanung - Mittelstufe',
                'concept_definition': 'Rentenplanung auf mittlerer Stufe umfasst Rentenalterberechnung, Sozialversicherungs-Optimierung und Renteneinkommensquellen. Dynamische Versionen der 4%-Regel werden verwendet.',
                'practical_example': 'Rentenalter 65, Lebenserwartung 90. 25 Jahre Rente. Jährliche Ausgabe 200.000 TL. Mit 3% Entnahmerate, erforderliche Ersparnisse = 200.000 / 0,03 = 6.666.667 TL. Mit 5% Entnahmerate = 4.000.000 TL.',
                'mathematical_formula': 'Rentenersparnisse = Jährliche Ausgabe × (1 - (1 + r)^(-n)) / r\nDynamische Entnahme = Vorherige Entnahme × (1 + Inflation - Rendite)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Rente ist nicht die Arbeit aufzugeben, sondern finanzielle Freiheit."'
            },
            'it': {
                'title': 'Pianificazione della Pensione - Intermedio',
                'concept_definition': 'La pianificazione della pensione a livello intermedio include il calcolo dell\'età pensionabile, l\'ottimizzazione della sicurezza sociale e le fonti di reddito pensionistico. Vengono utilizzate versioni dinamiche della regola del 4%.',
                'practical_example': 'Età pensionabile 65, aspettativa di vita 90. 25 anni di pensione. Spesa annuale 200.000 TL. Con tasso di prelievo del 3%, risparmio richiesto = 200.000 / 0,03 = 6.666.667 TL. Con tasso del 5% = 4.000.000 TL.',
                'mathematical_formula': 'Risparmio Pensionistico = Spesa Annuale × (1 - (1 + r)^(-n)) / r\nPrelievo Dinamico = Prelievo Precedente × (1 + Inflazione - Rendimento)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "La pensione non è smettere di lavorare, è libertà finanziaria."'
            }
        },
        'international_investing': {
            'tr': {
                'title': 'Uluslararası Yatırım - Orta Seviye',
                'concept_definition': 'Orta seviyede uluslararası yatırım, döviz riski, ülke riski ve küresel diversifikasyonu içerir. ETF ve ADR ile uluslararası yatırımlar yapılır. Gelişmekte olan piyasalar analiz edilir.',
                'practical_example': 'Portföy: %60 ABD (S&P 500), %20 Avrupa (STOXX 600), %10 Asya (MSCI Asia), %10 Gelişmekte Olan (MSCI EM). Döviz riski: USD/TL volatilitesi %15. Döviz hedge ile risk azaltılır.',
                'mathematical_formula': 'Döviz Riski = Fark × Pozisyon\nReel Getiri = (1 + Nominal) × (1 + Döviz) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Küresel diversifikasyon, ülke riskini azaltmanın en iyi yoludur."'
            },
            'en': {
                'title': 'International Investing - Intermediate',
                'concept_definition': 'Intermediate international investing includes currency risk, country risk, and global diversification. International investments are made through ETFs and ADRs. Emerging markets are analyzed.',
                'practical_example': 'Portfolio: 60% US (S&P 500), 20% Europe (STOXX 600), 10% Asia (MSCI Asia), 10% Emerging (MSCI EM). Currency risk: USD/TL volatility 15%. Currency hedges reduce risk.',
                'mathematical_formula': 'Currency Risk = Change × Position\nReal Return = (1 + Nominal) × (1 + Currency) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Global diversification is the best way to reduce country risk."'
            },
            'de': {
                'title': 'Internationales Investieren - Mittelstufe',
                'concept_definition': 'Internationales Investieren auf mittlerer Stufe umfasst Währungsrisiko, Länderrisiko und globale Diversifizierung. Internationale Investitionen werden über ETFs und ADRs getätigt. Schwellenländer werden analysiert.',
                'practical_example': 'Portfolio: 60% US (S&P 500), 20% Europa (STOXX 600), 10% Asien (MSCI Asia), 10% Schwellenländer (MSCI EM). Währungsrisiko: USD/TL Volatilität 15%. Währungshedges reduzieren Risiko.',
                'mathematical_formula': 'Währungsrisiko = Änderung × Position\nReale Rendite = (1 + Nominal) × (1 + Währung) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Globale Diversifizierung ist der beste Weg, um Länderrisiko zu reduzieren."'
            },
            'it': {
                'title': 'Investimento Internazionale - Intermedio',
                'concept_definition': 'L\'investimento internazionale a livello intermedio include il rischio valutario, il rischio paese e la diversificazione globale. Gli investimenti internazionali vengono effettuati tramite ETF e ADR. I mercati emergenti vengono analizzati.',
                'practical_example': 'Portafoglio: 60% USA (S&P 500), 20% Europa (STOXX 600), 10% Asia (MSCI Asia), 10% Emergenti (MSCI EM). Rischio valutario: volatilità USD/TL 15%. Le coperture valutarie riducono il rischio.',
                'mathematical_formula': 'Rischio Valutario = Variazione × Posizione\nRendimento Reale = (1 + Nominale) × (1 + Valuta) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La diversificazione globale è il modo migliore per ridurre il rischio paese."'
            }
        },
        'derivatives': {
            'tr': {
                'title': 'Türev Araçlar - Orta Seviye',
                'concept_definition': 'Orta seviyede türev araçlar, opsiyonlar, futures ve swap\'ları içerir. Delta, gamma, theta, vega Greeks hesaplanır. Hedging stratejileri uygulanır.',
                'practical_example': 'Call opsiyonu: Strike fiyatı 100 TL, prim 5 TL. Hisse fiyatı 110 TL olursa, iç değer = 10 TL, zaman değeri = 0 TL. Kâr = 10 - 5 = 5 TL. Delta = 0.5, hisse %1 artarsa opsiyon %0.5 artar.',
                'mathematical_formula': 'Opsiyon Primi = İç Değer + Zaman Değeri\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Türev araçlar, güçlü ama tehlikeli araçlardır."'
            },
            'en': {
                'title': 'Derivatives - Intermediate',
                'concept_definition': 'Intermediate derivatives includes options, futures, and swaps. Delta, gamma, theta, vega Greeks are calculated. Hedging strategies are applied.',
                'practical_example': 'Call option: Strike price 100 TL, premium 5 TL. If stock price becomes 110 TL, intrinsic value = 10 TL, time value = 0 TL. Profit = 10 - 5 = 5 TL. Delta = 0.5, if stock increases 1%, option increases 0.5%.',
                'mathematical_formula': 'Option Premium = Intrinsic Value + Time Value\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Derivatives are powerful but dangerous instruments."'
            },
            'de': {
                'title': 'Derivate - Mittelstufe',
                'concept_definition': 'Derivate auf mittlerer Stufe umfassen Optionen, Futures und Swaps. Delta, Gamma, Theta, Vega Greeks werden berechnet. Hedging-Strategien werden angewendet.',
                'practical_example': 'Call-Option: Strike-Preis 100 TL, Prämie 5 TL. Wenn Aktienpreis 110 TL wird, innerer Wert = 10 TL, Zeitwert = 0 TL. Gewinn = 10 - 5 = 5 TL. Delta = 0,5, wenn Aktie um 1% steigt, steigt Option um 0,5%.',
                'mathematical_formula': 'Optionsprämie = Innerer Wert + Zeitwert\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Derivate sind mächtige aber gefährliche Instrumente."'
            },
            'it': {
                'title': 'Derivati - Intermedio',
                'concept_definition': 'I derivati a livello intermedio includono opzioni, futures e swap. I Greci Delta, Gamma, Theta, Vega vengono calcolati. Le strategie di hedging vengono applicate.',
                'practical_example': 'Opzione Call: prezzo di esercizio 100 TL, premio 5 TL. Se il prezzo dell\'azione diventa 110 TL, valore intrinseco = 10 TL, valore temporale = 0 TL. Profitto = 10 - 5 = 5 TL. Delta = 0.5, se l\'azione aumenta dell\'1%, l\'opzione aumenta dello 0.5%.',
                'mathematical_formula': 'Premio Opzione = Valore Intrinseco + Valore Tempo\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I derivati sono strumenti potenti ma pericolosi."'
            }
        },
        'alternative_investments': {
            'tr': {
                'title': 'Alternatif Yatırımlar - Orta Seviye',
                'concept_definition': 'Orta seviyede alternatif yatırımlar, gayrimenkul REIT\'ler, emtia, özel sermaye ve hedge fonları içerir. Geleneksel varlıklarla korelasyon analizi yapılır.',
                'practical_example': 'Portföy: %70 hisse, %20 tahvil, %10 gayrimenkul REIT. Gayrimenkul REIT, hisselerle korelasyonu %60 olan bir varlıktır. Bu, portföy riskini azaltır.',
                'mathematical_formula': 'Alternatif Portföy = Σ(Alternatif Ağırlık × Alternatif Getiri)\nKorelasyon = Cov(X, Y) / (σX × σY)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Alternatif yatırımlar, portföy çeşitlendirmesini artırır."'
            },
            'en': {
                'title': 'Alternative Investments - Intermediate',
                'concept_definition': 'Intermediate alternative investments includes real estate REITs, commodities, private equity, and hedge funds. Correlation analysis with traditional assets is done.',
                'practical_example': 'Portfolio: 70% stocks, 20% bonds, 10% real estate REIT. Real estate REIT is an asset with 60% correlation with stocks. This reduces portfolio risk.',
                'mathematical_formula': 'Alternative Portfolio = Σ(Alternative Weight × Alternative Return)\nCorrelation = Cov(X, Y) / (σX × σY)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Alternative investments increase portfolio diversification."'
            },
            'de': {
                'title': 'Alternative Investitionen - Mittelstufe',
                'concept_definition': 'Alternative Investitionen auf mittlerer Stufe umfassen Immobilien-REITs, Rohstoffe, Private Equity und Hedgefonds. Korrelationsanalyse mit traditionellen Vermögenswerten wird durchgeführt.',
                'practical_example': 'Portfolio: 70% Aktien, 20% Anleihen, 10% Immobilien-REIT. Immobilien-REIT ist ein Vermögenswert mit 60% Korrelation mit Aktien. Dies reduziert Portfoliorisiko.',
                'mathematical_formula': 'Alternatives Portfolio = Σ(Alternatives Gewicht × Alternative Rendite)\nKorrelation = Cov(X, Y) / (σX × σY)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Alternative Investitionen erhöhen die Portfolio-Diversifizierung."'
            },
            'it': {
                'title': 'Investimenti Alternativi - Intermedio',
                'concept_definition': 'Gli investimenti alternativi a livello intermedio includono REIT immobiliari, materie prime, private equity e hedge fund. Viene eseguita l\'analisi della correlazione con le attività tradizionali.',
                'practical_example': 'Portafoglio: 70% azioni, 20% obbligazioni, 10% REIT immobiliari. REIT immobiliare è un\'attività con correlazione del 60% con le azioni. Questo riduce il rischio del portafoglio.',
                'mathematical_formula': 'Portafoglio Alternativo = Σ(Peso Alternativo × Rendimento Alternativo)\nCorrelazione = Cov(X, Y) / (σX × σY)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Gli investimenti alternativi aumentano la diversificazione del portafoglio."'
            }
        },
        'quantitative_finance': {
            'tr': {
                'title': 'Kuantitatif Finans - Orta Seviye',
                'concept_definition': 'Orta seviyede kuantitatif finans, Monte Carlo simülasyonları, stokastik süreçler ve risk modellerini içerir. VaR (Value at Risk) ve CVaR hesaplanır.',
                'practical_example': 'Monte Carlo simülasyonu: 10.000 farklı senaryo çalıştırılır. %95 güven seviyesinde VaR = 50.000 TL. Bu, %5 ihtimalle portföyün 50.000 TL veya daha fazla kaybedeceği anlamına gelir.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nMonte Carlo: S(t+1) = S(t) × exp((μ - 0.5σ²)dt + σ√dt × Z)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Kuantitatif modeller, riski anlamak için önemlidir."'
            },
            'en': {
                'title': 'Quantitative Finance - Intermediate',
                'concept_definition': 'Intermediate quantitative finance includes Monte Carlo simulations, stochastic processes, and risk models. VaR (Value at Risk) and CVaR are calculated.',
                'practical_example': 'Monte Carlo simulation: 10,000 different scenarios are run. VaR at 95% confidence = 50,000 TL. This means there is a 5% chance the portfolio will lose 50,000 TL or more.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nMonte Carlo: S(t+1) = S(t) × exp((μ - 0.5σ²)dt + σ√dt × Z)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Quantitative models are important for understanding risk."'
            },
            'de': {
                'title': 'Quantitative Finance - Mittelstufe',
                'concept_definition': 'Quantitative Finance auf mittlerer Stufe umfasst Monte-Carlo-Simulationen, stochastische Prozesse und Risikomodelle. VaR (Value at Risk) und CVaR werden berechnet.',
                'practical_example': 'Monte-Carlo-Simulation: 10.000 verschiedene Szenarien werden ausgeführt. VaR bei 95% Konfidenz = 50.000 TL. Dies bedeutet, dass es eine 5% Chance gibt, dass das Portfolio 50.000 TL oder mehr verliert.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nMonte Carlo: S(t+1) = S(t) × exp((μ - 0.5σ²)dt + σ√dt × Z)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Quantitative Modelle sind wichtig für das Verständnis von Risiko."'
            },
            'it': {
                'title': 'Finanza Quantitativa - Intermedio',
                'concept_definition': 'La finanza quantitativa a livello intermedio include simulazioni Monte Carlo, processi stocastici e modelli di rischio. VaR (Value at Risk) e CVaR vengono calcolati.',
                'practical_example': 'Simulazione Monte Carlo: Vengono eseguiti 10.000 diversi scenari. VaR al 95% di confidenza = 50.000 TL. Questo significa che c\'è una probabilità del 5% che il portafoglio perda 50.000 TL o più.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nMonte Carlo: S(t+1) = S(t) × exp((μ - 0.5σ²)dt + σ√dt × Z)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I modelli quantitativi sono importanti per comprendere il rischio."'
            }
        },
        'algorithmic_trading': {
            'tr': {
                'title': 'Algoritmik Ticaret - Orta Seviye',
                'concept_definition': 'Orta seviyede algoritmik ticaret, arbitraj stratejileri, momentum stratejileri ve mean reversion stratejilerini içerir. Backtesting ve forward testing yapılır.',
                'practical_example': 'Momentum stratejisi: Hisse fiyatı 50 günlük ortalamanın üzerine çıkarsa al, altına düşerse sat. Backtesting ile geçmiş performans test edilir. Sharpe oranı 1.5 ise strateji başarılıdır.',
                'mathematical_formula': 'Momentum = Fiyat - Hareketli Ortalama\nMean Reversion = (Fiyat - Ortalama) / Standart Sapma\nSharpe Oranı = (Getiri - Risksiz) / Volatilite',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Algoritmik ticaret, hız ve veri avantajıdır."'
            },
            'en': {
                'title': 'Algorithmic Trading - Intermediate',
                'concept_definition': 'Intermediate algorithmic trading includes arbitrage strategies, momentum strategies, and mean reversion strategies. Backtesting and forward testing are done.',
                'practical_example': 'Momentum strategy: Buy when stock price rises above 50-day average, sell when it falls below. Backtesting tests past performance. If Sharpe ratio is 1.5, strategy is successful.',
                'mathematical_formula': 'Momentum = Price - Moving Average\nMean Reversion = (Price - Mean) / Standard Deviation\nSharpe Ratio = (Return - Risk Free) / Volatility',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Algorithmic trading is about speed and data advantage."'
            },
            'de': {
                'title': 'Algorithmischer Handel - Mittelstufe',
                'concept_definition': 'Algorithmischer Handel auf mittlerer Stufe umfasst Arbitrage-Strategien, Momentum-Strategien und Mean-Reversion-Strategien. Backtesting und Forward-Testing werden durchgeführt.',
                'practical_example': 'Momentum-Strategie: Kaufen, wenn Aktienkurs über 50-Tage-Durchschnitt steigt, verkaufen, wenn er darunter fällt. Backtesting testet vergangene Performance. Wenn Sharpe Ratio 1,5 ist, ist Strategie erfolgreich.',
                'mathematical_formula': 'Momentum = Preis - Gleitender Durchschnitt\nMean Reversion = (Preis - Mittelwert) / Standardabweichung\nSharpe Ratio = (Rendite - Risikofrei) / Volatilität',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Algorithmischer Handel ist Geschwindigkeit und Datenvorteil."'
            },
            'it': {
                'title': 'Trading Algoritmico - Intermedio',
                'concept_definition': 'Il trading algoritmico a livello intermedio include strategie di arbitraggio, strategie di momentum e strategie di mean reversion. Vengono eseguiti backtesting e forward testing.',
                'practical_example': 'Strategia Momentum: Acquista quando il prezzo delle azioni sale sopra la media a 50 giorni, vendi quando scende sotto. Il backtesting testa la performance passata. Se il Sharpe ratio è 1.5, la strategia è riuscita.',
                'mathematical_formula': 'Momentum = Prezzo - Media Mobile\nMean Reversion = (Prezzo - Media) / Deviazione Standard\nSharpe Ratio = (Rendimento - Senza Rischio) / Volatilità',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il trading algoritmico riguarda velocità e vantaggio dati."'
            }
        },
        'machine_learning_finance': {
            'tr': {
                'title': 'Makine Öğrenmesi ve Finans - Orta Seviye',
                'concept_definition': 'Orta seviyede ML finans, regression, classification ve time series forecasting\'i içerir. Feature engineering ve model selection önemlidir. Overfitting önlenir.',
                'practical_example': 'Linear regression ile hisse fiyat tahmini: Feature\'lar = P/E, P/B, ROE. Model eğitilir ve test edilir. R² = 0.75 ise model başarılıdır. Cross-validation ile overfitting kontrol edilir.',
                'mathematical_formula': 'Linear Regression: y = β0 + β1x1 + β2x2 + ... + ε\nR² = 1 - (SSres / SStot)\nMSE = (1/n) × Σ(yi - ŷi)²',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Veri kalitesi, model başarısını belirler."'
            },
            'en': {
                'title': 'Machine Learning in Finance - Intermediate',
                'concept_definition': 'Intermediate ML finance includes regression, classification, and time series forecasting. Feature engineering and model selection are important. Overfitting is prevented.',
                'practical_example': 'Linear regression for stock price prediction: Features = P/E, P/B, ROE. Model is trained and tested. If R² = 0.75, model is successful. Cross-validation controls overfitting.',
                'mathematical_formula': 'Linear Regression: y = β0 + β1x1 + β2x2 + ... + ε\nR² = 1 - (SSres / SStot)\nMSE = (1/n) × Σ(yi - ŷi)²',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Data quality determines model success."'
            },
            'de': {
                'title': 'Machine Learning in der Finanzen - Mittelstufe',
                'concept_definition': 'Machine Learning in der Finanzen auf mittlerer Stufe umfasst Regression, Klassifikation und Zeitreihenvorhersage. Feature Engineering und Modellauswahl sind wichtig. Overfitting wird verhindert.',
                'practical_example': 'Lineare Regression für Aktienkursvorhersage: Features = KGV, KBV, ROE. Modell wird trainiert und getestet. Wenn R² = 0,75, ist Modell erfolgreich. Cross-Validation kontrolliert Overfitting.',
                'mathematical_formula': 'Lineare Regression: y = β0 + β1x1 + β2x2 + ... + ε\nR² = 1 - (SSres / SStot)\nMSE = (1/n) × Σ(yi - ŷi)²',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Datenqualität bestimmt Modellerfolg."'
            },
            'it': {
                'title': 'Machine Learning nella Finanza - Intermedio',
                'concept_definition': 'Il ML finanziario a livello intermedio include regressione, classificazione e previsione delle serie temporali. Il feature engineering e la selezione del modello sono importanti. L\'overfitting viene prevenuto.',
                'practical_example': 'Regressione lineare per la previsione dei prezzi azionari: Feature = P/E, P/B, ROE. Il modello viene addestrato e testato. Se R² = 0.75, il modello è riuscito. La cross-validation controlla l\'overfitting.',
                'mathematical_formula': 'Regressione Lineare: y = β0 + β1x1 + β2x2 + ... + ε\nR² = 1 - (SSres / SStot)\nMSE = (1/n) × Σ(yi - ŷi)²',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La qualità dei dati determina il successo del modello."'
            }
        },
        'blockchain_crypto': {
            'tr': {
                'title': 'Blockchain ve Kripto - Orta Seviye',
                'concept_definition': 'Orta seviyede blockchain ve kripto, distributed ledger technology, smart contracts ve DeFi\'yi içerir. Proof of Work, Proof of Stake ve consensus mekanizmaları analiz edilir.',
                'practical_example': 'Bitcoin: PoW consensus, blok süresi 10 dakika, maksimum supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming. Tokenomics: inflation rate, vesting schedule.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Blockchain, finansal sistemde devrim yaratabilir."'
            },
            'en': {
                'title': 'Blockchain & Crypto - Intermediate',
                'concept_definition': 'Intermediate blockchain and crypto includes distributed ledger technology, smart contracts, and DeFi. Proof of Work, Proof of Stake, and consensus mechanisms are analyzed.',
                'practical_example': 'Bitcoin: PoW consensus, block time 10 minutes, max supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming. Tokenomics: inflation rate, vesting schedule.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Blockchain can revolutionize the financial system."'
            },
            'de': {
                'title': 'Blockchain & Krypto - Mittelstufe',
                'concept_definition': 'Blockchain und Krypto auf mittlerer Stufe umfasst Distributed Ledger Technology, Smart Contracts und DeFi. Proof of Work, Proof of Stake und Konsensmechanismen werden analysiert.',
                'practical_example': 'Bitcoin: PoW-Konsens, Blockzeit 10 Minuten, Max Supply 21M. Ethereum: PoS, Gas-Gebühr, Smart Contracts. DeFi: Lending, Borrowing, Yield Farming. Tokenomics: Inflationsrate, Vesting-Schedule.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Blockchain kann das Finanzsystem revolutionieren."'
            },
            'it': {
                'title': 'Blockchain e Cripto - Intermedio',
                'concept_definition': 'La blockchain e le cripto a livello intermedio includono distributed ledger technology, smart contracts e DeFi. Proof of Work, Proof of Stake e i meccanismi di consenso vengono analizzati.',
                'practical_example': 'Bitcoin: consenso PoW, tempo blocco 10 minuti, max supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming. Tokenomics: inflation rate, vesting schedule.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La blockchain può rivoluzionare il sistema finanziario."'
            }
        },
        'esg_investing': {
            'tr': {
                'title': 'ESG Yatırımı - Orta Seviye',
                'concept_definition': 'Orta seviyede ESG yatırımı, çevresel, sosyal ve yönetişim kriterlerini içerir. Sürdürülebilir yatırım, impact investing ve green bonds analiz edilir. ESG skorları ve raporlama standartları (GRI, SASB) kullanılır.',
                'practical_example': 'ESG skorlama: Çevresel (karbon ayak izi, enerji verimliliği), Sosyal (işçi hakları, topluluk ilişkileri), Yönetişim (kurumsal yönetim, şeffaflık). MSCI ESG Rating: AAA (lider) - CCC (gecikmiş).',
                'mathematical_formula': 'ESG Skoru = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "ESG yatırımı, sadece finansal getiri değil, sosyal etki de önemlidir."'
            },
            'en': {
                'title': 'ESG Investing - Intermediate',
                'concept_definition': 'Intermediate ESG investing includes environmental, social, and governance criteria. Sustainable investing, impact investing, and green bonds are analyzed. ESG scores and reporting standards (GRI, SASB) are used.',
                'practical_example': 'ESG scoring: Environmental (carbon footprint, energy efficiency), Social (labor rights, community relations), Governance (corporate governance, transparency). MSCI ESG Rating: AAA (leader) - CCC (laggard).',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "ESG investing is not just about financial returns, but also social impact."'
            },
            'de': {
                'title': 'ESG-Investition - Mittelstufe',
                'concept_definition': 'ESG-Investition auf mittlerer Stufe umfasst Umwelt-, Sozial- und Unternehmensführungskriterien. Nachhaltiges Investieren, Impact Investing und Green Bonds werden analysiert. ESG-Scores und Berichtsstandards (GRI, SASB) werden verwendet.',
                'practical_example': 'ESG-Scoring: Umwelt (CO2-Fußabdruck, Energieeffizienz), Sozial (Arbeitsrechte, Gemeindebeziehungen), Unternehmensführung (Corporate Governance, Transparenz). MSCI ESG Rating: AAA (Führer) - CCC (Nachzügler).',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "ESG-Investition ist nicht nur finanzielle Rendite, sondern auch soziale Wirkung."'
            },
            'it': {
                'title': 'Investimento ESG - Intermedio',
                'concept_definition': 'L\'investimento ESG a livello intermedio include criteri ambientali, sociali e di governance. Investimento sostenibile, impact investing e green bonds vengono analizzati. Vengono utilizzati punteggi ESG e standard di reporting (GRI, SASB).',
                'practical_example': 'Punteggio ESG: Ambientale (impronta di carbonio, efficienza energetica), Sociale (diritti dei lavoratori, relazioni comunitarie), Governance (governance aziendale, trasparenza). Rating ESG MSCI: AAA (leader) - CCC (ritardatario).',
                'mathematical_formula': 'Punteggio ESG = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "L\'investimento ESG non riguarda solo i rendimenti finanziari, ma anche l\'impatto sociale."'
            }
        }
    },
    'advanced': {
        'income_expenses': {
            'tr': {
                'title': 'Gelir ve Giderler - İleri Seviye',
                'concept_definition': 'İleri seviyede gelir ve gider yönetimi, nakit akışı tahminlemesi ve senaryo analizi içerir. Enflasyon, vergi ve yaşam tarzı değişiklikleri gelecekteki nakit akışını etkiler. Monte Carlo simülasyonları, farklı senaryolar için olasılık dağılımları oluşturur.',
                'practical_example': 'Gelir artış hızı %5, enflasyon %3, vergi %20. 10 yıl sonra reel gelir artışı = (1.05 / 1.03) - 1 = 1.94%. Vergi sonrası reel gelir artışı = 1.94% × 0.8 = 1.55%.',
                'mathematical_formula': 'Reel Gelir Artışı = ((1 + Nominal Artış) / (1 + Enflasyon)) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Gelecek tahminlemesi imkansızdır. Sadece senaryo analizi yapın ve farklı sonuçlara hazırlıklı olun."'
            },
            'en': {
                'title': 'Income & Expenses - Advanced',
                'concept_definition': 'Advanced income and expense management includes cash flow forecasting and scenario analysis. Inflation, taxes, and lifestyle changes affect future cash flows. Monte Carlo simulations create probability distributions for different scenarios.',
                'practical_example': 'Income growth rate 5%, inflation 3%, tax 20%. After 10 years, real income growth = (1.05 / 1.03) - 1 = 1.94%. After-tax real income growth = 1.94% × 0.8 = 1.55%.',
                'mathematical_formula': 'Real Income Growth = ((1 + Nominal Growth) / (1 + Inflation)) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Future forecasting is impossible. Only do scenario analysis and be prepared for different outcomes."'
            },
            'de': {
                'title': 'Einkommen und Ausgaben - Fortgeschritten',
                'concept_definition': 'Einkommens- und Ausgabenmanagement auf fortgeschrittener Stufe umfasst Cashflow-Prognosen und Szenarioanalysen. Inflation, Steuern und Lebensstiländerungen beeinflussen zukünftige Cashflows. Monte-Carlo-Simulationen erstellen Wahrscheinlichkeitsverteilungen für verschiedene Szenarien.',
                'practical_example': 'Einkommenswachstumsrate 5%, Inflation 3%, Steuer 20%. Nach 10 Jahren reales Einkommenswachstum = (1,05 / 1,03) - 1 = 1,94%. Reales Einkommenswachstum nach Steuern = 1,94% × 0,8 = 1,55%.',
                'mathematical_formula': 'Reales Einkommenswachstum = ((1 + Nominales Wachstum) / (1 + Inflation)) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Zukunftsprognosen sind unmöglich. Führen Sie nur Szenarioanalysen durch und seien Sie auf verschiedene Ergebnisse vorbereitet."'
            },
            'it': {
                'title': 'Reddito e Spese - Avanzato',
                'concept_definition': 'La gestione del reddito e delle spese a livello avanzato include le previsioni del flusso di cassa e l\'analisi degli scenari. L\'inflazione, le tasse e i cambiamenti dello stile di vita influenzano i flussi di cassa futuri. Le simulazioni Monte Carlo creano distribuzioni di probabilità per diversi scenari.',
                'practical_example': 'Tasso di crescita del reddito 5%, inflazione 3%, tassa 20%. Dopo 10 anni, crescita del reddito reale = (1,05 / 1,03) - 1 = 1,94%. Crescita del reddito reale dopo le tasse = 1,94% × 0,8 = 1,55%.',
                'mathematical_formula': 'Crescita del Reddito Reale = ((1 + Crescita Nominale) / (1 + Inflazione)) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Le previsioni future sono impossibili. Fai solo analisi degli scenari e sii preparato per diversi risultati."'
            }
        },
        'compound_interest': {
            'tr': {
                'title': 'Bileşik Faiz - İleri Seviye',
                'concept_definition': 'İleri seviyede bileşik faiz, sürekli bileşikleşme ve logaritmik büyüme analizini içerir. Doğal logaritma (ln) ve e sayısı, sürekli bileşikleşme için kullanılır. Bileşik faizin gücü, zamanla katlanarak artar.',
                'practical_example': 'Sürekli bileşikleşme: A = P × e^(rt). P = 100.000, r = 0.08, t = 10. A = 100.000 × e^(0.8) = 100.000 × 2.2255 = 222.550 TL. Yıllık bileşikleşme ile: A = 100.000 × (1.08)^10 = 215.892 TL.',
                'mathematical_formula': 'Sürekli Bileşikleşme: A = P × e^(rt)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Üstel büyüme, insan zihnini aşar. Küçük farklar zamanla devasa sonuçlar yaratır."'
            },
            'en': {
                'title': 'Compound Interest - Advanced',
                'concept_definition': 'Advanced compound interest includes continuous compounding and logarithmic growth analysis. Natural logarithm (ln) and e number are used for continuous compounding. The power of compound interest increases exponentially over time.',
                'practical_example': 'Continuous compounding: A = P × e^(rt). P = 100,000, r = 0.08, t = 10. A = 100,000 × e^(0.8) = 100,000 × 2.2255 = 222,550 TL. With annual compounding: A = 100,000 × (1.08)^10 = 215,892 TL.',
                'mathematical_formula': 'Continuous Compounding: A = P × e^(rt)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Exponential growth exceeds human comprehension. Small differences create massive results over time."'
            },
            'de': {
                'title': 'Zinseszins - Fortgeschritten',
                'concept_definition': 'Zinseszins auf fortgeschrittener Stufe umfasst kontinuierliche Verzinsung und logarithmische Wachstumsanalyse. Natürlicher Logarithmus (ln) und e-Zahl werden für kontinuierliche Verzinsung verwendet. Die Kraft des Zinseszinses wächst exponentiell über die Zeit.',
                'practical_example': 'Kontinuierliche Verzinsung: A = P × e^(rt). P = 100.000, r = 0,08, t = 10. A = 100.000 × e^(0,8) = 100.000 × 2,2255 = 222.550 TL. Mit jährlicher Verzinsung: A = 100.000 × (1,08)^10 = 215.892 TL.',
                'mathematical_formula': 'Kontinuierliche Verzinsung: A = P × e^(rt)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Exponentielles Wachstum übersteigt das menschliche Verständnis. Kleine Unterschiede schaffen über Zeit massive Ergebnisse."'
            },
            'it': {
                'title': 'Interesse Composto - Avanzato',
                'concept_definition': 'L\'interesse composto a livello avanzato include la composizione continua e l\'analisi della crescita logaritmica. Il logaritmo naturale (ln) e il numero e sono usati per la composizione continua. Il potere dell\'interesse composto aumenta esponenzialmente nel tempo.',
                'practical_example': 'Composizione continua: A = P × e^(rt). P = 100.000, r = 0,08, t = 10. A = 100.000 × e^(0,8) = 100.000 × 2,2255 = 222.550 TL. Con composizione annuale: A = 100.000 × (1,08)^10 = 215.892 TL.',
                'mathematical_formula': 'Composizione Continua: A = P × e^(rt)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La crescita esponenziale supera la comprensione umana. Piccole differenze creano risultati massicci nel tempo."'
            }
        },
        'assets': {
            'tr': {
                'title': 'Varlıklar ve Varlık Sınıfları - İleri Seviye',
                'concept_definition': 'İleri seviyede varlık yönetimi, CAPM (Capital Asset Pricing Model), Beta katsayısı ve alpha getiri analizini içerir. Sharpe Oranı, Sortino Oranı ve Information Ratio gibi risk ayarlı getiri metrikleri kullanılır. Portföy optimizasyonu için matematiksel modeller uygulanır.',
                'practical_example': 'Beta = 1.5 olan hisse, piyasa %1 arttığında %1.5 artar. Alpha = 2% olan hisse, beklenen getirisinden %2 daha fazla getiri sağlar. Sharpe Oranı 2.0 olan portföy, risksiz faize göre 2 kat daha iyi performans gösterir.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Piyasa fiyatı ve iç değer arasındaki fark, fırsat yaratır. Bu farkı anlamak, başarılı yatırımın anahtarıdır."'
            },
            'en': {
                'title': 'Assets & Asset Classes - Advanced',
                'concept_definition': 'Advanced asset management includes CAPM (Capital Asset Pricing Model), Beta coefficient, and alpha return analysis. Risk-adjusted return metrics like Sharpe Ratio, Sortino Ratio, and Information Ratio are used. Mathematical models are applied for portfolio optimization.',
                'practical_example': 'Stock with Beta = 1.5 rises 1.5% when market rises 1%. Stock with Alpha = 2% provides 2% more return than expected return. Portfolio with Sharpe Ratio of 2.0 performs 2 times better than risk-free rate.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "The difference between market price and intrinsic value creates opportunity. Understanding this difference is the key to successful investing."'
            },
            'de': {
                'title': 'Vermögenswerte und Anlageklassen - Fortgeschritten',
                'concept_definition': 'Vermögensverwaltung auf fortgeschrittener Stufe umfasst CAPM (Capital Asset Pricing Model), Beta-Koeffizient und Alpha-Renditeanalyse. Risikobereinigte Renditemetriken wie Sharpe Ratio, Sortino Ratio und Information Ratio werden verwendet. Mathematische Modelle werden für Portfolio-Optimierung angewendet.',
                'practical_example': 'Aktie mit Beta = 1,5 steigt um 1,5%, wenn der Markt um 1% steigt. Aktie mit Alpha = 2% liefert 2% mehr Rendite als erwartet. Portfolio mit Sharpe Ratio von 2,0 performs 2-mal besser als risikofreier Zins.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Der Unterschied zwischen Marktpreis und innerem Wert schafft Gelegenheit. Diesen Unterschied zu verstehen, ist der Schlüssel zum erfolgreichen Investieren."'
            },
            'it': {
                'title': 'Attività e Classi di Attività - Avanzato',
                'concept_definition': 'La gestione delle attività a livello avanzato include CAPM (Capital Asset Pricing Model), coefficiente Beta e analisi del rendimento alpha. Metriche di rendimento aggiustate per il rischio come Sharpe Ratio, Sortino Ratio e Information Ratio vengono utilizzate. I modelli matematici vengono applicati per l\'ottimizzazione del portafoglio.',
                'practical_example': 'Azione con Beta = 1,5 aumenta dell\'1,5% quando il mercato aumenta dell\'1%. Azione con Alpha = 2% fornisce il 2% in più di rendimento rispetto al rendimento previsto. Portafoglio con Sharpe Ratio di 2,0 performs 2 volte meglio del tasso senza rischio.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La differenza tra prezzo di mercato e valore intrinseco crea opportunità. Comprendere questa differenza è la chiave per investire con successo."'
            }
        },
        'financial_freedom': {
            'tr': {
                'title': 'Finansal Özgürlük - İleri Seviye',
                'concept_definition': 'İleri seviyede finansal özgürlük, dinamik çekim stratejileri ve sekans riski (sequence of returns risk) analizini içerir. Emeklilik sırasındaki piyasa çöküşleri, çekim oranını etkiler. Güvenlik marjı ve esneklik, riski azaltır.',
                'practical_example': 'Emeklilik başlangıcında piyasa %20 düşerse, çekim oranı %4\'ten %5\'e çıkar. Bu, portföyün daha hızlı tükenmesini sağlar. Güvenlik marjı %20 ise, çekim oranı %3.2\'ye düşürülür.',
                'mathematical_formula': 'Sekans Riski = (1 - Çekim Oranı) × Piyasa Düşüşü',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Finansal özgürlük, esneklik gerektirir. Piyasa koşullarına göre harcamanızı ayarlayın."'
            },
            'en': {
                'title': 'Financial Freedom - Advanced',
                'concept_definition': 'Advanced financial freedom includes dynamic withdrawal strategies and sequence of returns risk analysis. Market crashes at retirement affect withdrawal rates. Safety margin and flexibility reduce risk.',
                'practical_example': 'If market drops 20% at retirement start, withdrawal rate increases from 4% to 5%. This causes portfolio to deplete faster. With 20% safety margin, withdrawal rate is reduced to 3.2%.',
                'mathematical_formula': 'Sequence Risk = (1 - Withdrawal Rate) × Market Decline',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Financial freedom requires flexibility. Adjust your spending according to market conditions."'
            },
            'de': {
                'title': 'Finanzielle Freiheit - Fortgeschritten',
                'concept_definition': 'Finanzielle Freiheit auf fortgeschrittener Stufe umfasst dynamische Entnahmestrategien und Sequenz-Risikoanalyse. Marktzusammenbrüche zu Rentenbeginn beeinflussen Entnahmeraten. Sicherheitsmarge und Flexibilität reduzieren das Risiko.',
                'practical_example': 'Wenn der Markt zu Rentenbeginn um 20% fällt, steigt die Entnahmerate von 4% auf 5%. Dies führt dazu, dass das Portfolio schneller aufgebraucht wird. Mit 20% Sicherheitsmarge wird die Entnahmerate auf 3,2% reduziert.',
                'mathematical_formula': 'Sequenz-Risiko = (1 - Entnahmerate) × Marktrückgang',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Finanzielle Freiheit erfordert Flexibilität. Passen Sie Ihre Ausgaben an die Marktbedingungen an."'
            },
            'it': {
                'title': 'Libertà Finanziaria - Avanzato',
                'concept_definition': 'La libertà finanziaria a livello avanzato include strategie di prelievo dinamiche e l\'analisi del rischio di sequenza. I crolli del mercato all\'inizio della pensione influenzano i tassi di prelievo. Il margine di sicurezza e la flessibilità riducono il rischio.',
                'practical_example': 'Se il mercato crolla del 20% all\'inizio della pensione, il tasso di prelievo aumenta dal 4% al 5%. Questo fa sì che il portafoglio si esaurisca più velocemente. Con un margine di sicurezza del 20%, il tasso di prelievo viene ridotto al 3,2%.',
                'mathematical_formula': 'Rischio di Sequenza = (1 - Tasso di Prelievo) × Declino del Mercato',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "La libertà finanziaria richiede flessibilità. Adatta le tue spese alle condizioni di mercato."'
            }
        },
        'investing': {
            'tr': {
                'title': 'Yatırım ve Yatırım Araçları - İleri Seviye',
                'concept_definition': 'İleri seviyede yatırım, piyasa volatilitesi metrikleri (VIX, realized volatility), risk yönetimi ve psikolojik risk yönetimini içerir. Piyasa çöküşlerinde panik satışından kaçınmak, başarılı yatırımın anahtarıdır. Kontraryan yatırım stratejileri uygulanır.',
                'practical_example': 'VIX 30 olduğunda piyasa volatil, VIX 15 olduğunda piyasa sakin. Piyasa çöküşünde %20 düşüş olduğunda, panik satışı yerine alım fırsatı olarak görülür. Kontraryan yatırımcı, kalabalığın aksine hareket eder.',
                'mathematical_formula': 'Volatilite = Standart Sapma × √252 (yıllık)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Piyasa çöküşleri beklenmediktir. Hazırlıklı olun ve fırsatları kullanın."'
            },
            'en': {
                'title': 'Investing & Investment Vehicles - Advanced',
                'concept_definition': 'Advanced investing includes market volatility metrics (VIX, realized volatility), risk management, and psychological risk management. Avoiding panic selling during market crashes is the key to successful investing. Contrarian investment strategies are applied.',
                'practical_example': 'When VIX is 30, market is volatile; when VIX is 15, market is calm. During market crash with 20% decline, instead of panic selling, it\'s seen as buying opportunity. Contrarian investor moves opposite to the crowd.',
                'mathematical_formula': 'Volatility = Standard Deviation × √252 (annualized)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Market crashes are unexpected. Be prepared and use opportunities."'
            },
            'de': {
                'title': 'Investieren und Anlageinstrumente - Fortgeschritten',
                'concept_definition': 'Investieren auf fortgeschrittener Stufe umfasst Marktvolatilitätsmetriken (VIX, realisierte Volatilität), Risikomanagement und psychologisches Risikomanagement. Panikverkäufe während Marktzusammenbrüchen zu vermeiden, ist der Schlüssel zum erfolgreichen Investieren. Konträre Investmentstrategien werden angewendet.',
                'practical_example': 'Wenn VIX 30 ist, ist der Markt volatil; wenn VIX 15 ist, ist der Markt ruhig. Während eines Marktzusammenbruchs mit 20% Rückgang wird dies statt Panikverkauf als Kaufgelegenheit gesehen. Konträre Investor bewegen sich entgegengesetzt zur Menge.',
                'mathematical_formula': 'Volatilität = Standardabweichung × √252 (jährlich)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Marktzusammenbrüche sind unerwartet. Seien Sie vorbereitet und nutzen Sie Gelegenheiten."'
            },
            'it': {
                'title': 'Investire e Strumenti di Investimento - Avanzato',
                'concept_definition': 'L\'investimento a livello avanzato include metriche di volatilità del mercato (VIX, volatilità realizzata), gestione del rischio e gestione del rischio psicologico. Evitare le vendite di panico durante i crolli del mercato è la chiave per investire con successo. Vengono applicate strategie di investimento contrarian.',
                'practical_example': 'Quando VIX è 30, il mercato è volatile; quando VIX è 15, il mercato è calmo. Durante un crollo del mercato con un declino del 20%, invece di vendite di panico, questo è visto come opportunità di acquisto. L\'investitore contrarian si muove opposto alla folla.',
                'mathematical_formula': 'Volatilità = Deviazione Standard × √252 (annualizzata)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I crolli del mercato sono inaspettati. Sii preparato e usa le opportunità."'
            }
        },
        'risk_management': {
            'tr': {
                'title': 'Risk Yönetimi',
                'concept_definition': 'İleri seviyede risk yönetimi, Value at Risk (VaR), Conditional VaR, stres testleri ve senaryo analizlerini içerir. Risk bütçeleme, risk limitleri ve risk takibi profesyonel risk yönetiminin temelidir.',
                'practical_example': 'Portföy değeri 1.000.000 TL. %95 güven seviyesinde VaR = 50.000 TL. Bu, %5 ihtimalle portföyün 50.000 TL veya daha fazla kaybedeceği anlamına gelir. CVaR ise en kötü %5 durumda ortalama kaybı gösterir.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Risk, standart sapma değildir. Risk, beklenmedik olayların potansiyel etkisidir."'
            },
            'en': {
                'title': 'Risk Management',
                'concept_definition': 'Advanced risk management includes Value at Risk (VaR), Conditional VaR, stress tests, and scenario analysis. Risk budgeting, risk limits, and risk monitoring are fundamental to professional risk management.',
                'practical_example': 'Portfolio value is 1,000,000 TL. VaR at 95% confidence = 50,000 TL. This means there is a 5% chance the portfolio will lose 50,000 TL or more. CVaR shows the average loss in the worst 5% of cases.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Risk is not standard deviation. Risk is the potential impact of unexpected events."'
            },
            'de': {
                'title': 'Risikomanagement',
                'concept_definition': 'Fortgeschrittenes Risikomanagement umfasst Value at Risk (VaR), Conditional VaR, Stresstests und Szenarioanalysen. Risk Budgeting, Risikolimits und Risikoüberwachung sind grundlegend für professionelles Risikomanagement.',
                'practical_example': 'Portfoliowert ist 1.000.000 TL. VaR bei 95% Konfidenz = 50.000 TL. Dies bedeutet, dass es eine 5% Chance gibt, dass das Portfolio 50.000 TL oder mehr verliert. CVaR zeigt den durchschnittlichen Verlust in den schlechtesten 5% der Fälle.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Risiko ist keine Standardabweichung. Risiko ist die potenzielle Auswirkung unerwarteter Ereignisse."'
            },
            'it': {
                'title': 'Gestione del Rischio',
                'concept_definition': 'La gestione del rischio avanzata include Value at Risk (VaR), Conditional VaR, test di stress e analisi degli scenari. Il risk budgeting, i limiti di rischio e il monitoraggio del rischio sono fondamentali per la gestione del rischio professionale.',
                'practical_example': 'Il valore del portafoglio è 1.000.000 TL. VaR al 95% di confidenza = 50.000 TL. Questo significa che c\'è una probabilità del 5% che il portafoglio perda 50.000 TL o più. CVaR mostra la perdita media nel peggiore 5% dei casi.',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il rischio non è la deviazione standard. Il rischio è l\'impatto potenziale di eventi imprevisti."'
            }
        },
        'portfolio_optimization': {
            'tr': {
                'title': 'Portföy Optimizasyonu',
                'concept_definition': 'İleri seviyede portföy optimizasyonu, Modern Portföy Teorisi (MPT), Etkili Sınır (Efficient Frontier), CAPM ve faktör modellerini içerir. Kararlı optimizasyon, kısıtlı optimizasyon ve dinamik asset allocation kullanılır.',
                'practical_example': '3 varlık: Hisse (β=1.2, σ=20%), Tahvil (β=0.3, σ=5%), Altın (β=0.5, σ=15%). Etkili sınır üzerinde optimal portföy: %40 hisse, %40 tahvil, %20 altın. Bu portföy Sharpe oranı maksimize eder.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Diversifikasyon, riski azaltmanın en iyi yoludur. Ancak aşırı diversifikasyon, getiriyi de azaltır."'
            },
            'en': {
                'title': 'Portfolio Optimization',
                'concept_definition': 'Advanced portfolio optimization includes Modern Portfolio Theory (MPT), Efficient Frontier, CAPM, and factor models. Robust optimization, constrained optimization, and dynamic asset allocation are used.',
                'practical_example': '3 assets: Stocks (β=1.2, σ=20%), Bonds (β=0.3, σ=5%), Gold (β=0.5, σ=15%). Optimal portfolio on efficient frontier: 40% stocks, 40% bonds, 20% gold. This portfolio maximizes Sharpe ratio.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Diversification is the best way to reduce risk. However, excessive diversification also reduces returns."'
            },
            'de': {
                'title': 'Portfolio-Optimierung',
                'concept_definition': 'Fortgeschrittene Portfolio-Optimierung umfasst Moderne Portfolio-Theorie (MPT), Effiziente Grenze, CAPM und Faktormodelle. Robuste Optimierung, eingeschränkte Optimierung und dynamische Asset Allocation werden verwendet.',
                'practical_example': '3 Vermögenswerte: Aktien (β=1.2, σ=20%), Anleihen (β=0.3, σ=5%), Gold (β=0.5, σ=15%). Optimales Portfolio auf effizienter Grenze: 40% Aktien, 40% Anleihen, 20% Gold. Dieses Portfolio maximiert die Sharpe Ratio.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Diversifizierung ist der beste Weg, das Risiko zu reduzieren. Übermäßige Diversifizierung reduziert jedoch auch die Rendite."'
            },
            'it': {
                'title': 'Ottimizzazione del Portafoglio',
                'concept_definition': 'L\'ottimizzazione del portafoglio avanzata include la Teoria del Portafoglio Moderno (MPT), Frontiera Efficiente, CAPM e modelli fattoriali. Vengono utilizzati l\'ottimizzazione robusta, l\'ottimizzazione vincolata e l\'allocazione dinamica delle attività.',
                'practical_example': '3 attività: Azioni (β=1.2, σ=20%), Obbligazioni (β=0.3, σ=5%), Oro (β=0.5, σ=15%). Portafoglio ottimale sulla frontiera efficiente: 40% azioni, 40% obbligazioni, 20% oro. Questo portafoglio massimizza il Sharpe ratio.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La diversificazione è il modo migliore per ridurre il rischio. Tuttavia, una diversificazione eccessiva riduce anche i rendimenti."'
            }
        },
        'behavioral_finance': {
            'tr': {
                'title': 'Davranışsal Finans',
                'concept_definition': 'İleri seviyede davranışsal finans, bilişsel önyargılar (bias), duygusal faktörler ve psikolojik etkileri içerir. Kayıp aversionı, aşırı güven, sürü etkisi ve mental accounting önemli bias\'lardır.',
                'practical_example': 'Kayıp aversionı: 100 TL kaybetmenin acısı, 100 TL kazanmanın sevincinden 2 kat daha fazladır. Bu yüzden yatırımcılar kaybeden pozisyonları çok uzun tutarlar (disposition effect).',
                'mathematical_formula': 'Kayıp Aversion Oranı = (Kazanç Değeri / Kayıp Değeri) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Finansal kararlarınızın %90\'ı psikolojiktir, teknik değildir."'
            },
            'en': {
                'title': 'Behavioral Finance',
                'concept_definition': 'Advanced behavioral finance includes cognitive biases, emotional factors, and psychological effects. Loss aversion, overconfidence, herd behavior, and mental accounting are important biases.',
                'practical_example': 'Loss aversion: The pain of losing 100 TL is twice the pleasure of gaining 100 TL. Therefore, investors hold losing positions too long (disposition effect).',
                'mathematical_formula': 'Loss Aversion Ratio = (Gain Value / Loss Value) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "90% of your financial decisions are psychological, not technical."'
            },
            'de': {
                'title': 'Verhaltensfinanz',
                'concept_definition': 'Fortgeschrittene Verhaltensfinanz umfasst kognitive Verzerrungen, emotionale Faktoren und psychologische Effekte. Verlustaversion, Überkonfidenz, Herdenverhalten und Mental Accounting sind wichtige Verzerrungen.',
                'practical_example': 'Verlustaversion: Der Schmerz, 100 TL zu verlieren, ist doppelt so groß wie die Freude, 100 TL zu gewinnen. Daher halten Investoren verlustbringende Positionen zu lange (Dispositionseffekt).',
                'mathematical_formula': 'Verlustaversion Ratio = (Gewinnwert / Verlustwert) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "90% Ihrer finanziellen Entscheidungen sind psychologisch, nicht technisch."'
            },
            'it': {
                'title': 'Finanza Comportamentale',
                'concept_definition': 'La finanza comportamentale avanzata include bias cognitivi, fattori emotivi ed effetti psicologici. L\'avversione alla perdita, l\'eccessiva fiducia, il comportamento di gregge e il mental accounting sono bias importanti.',
                'practical_example': 'Avversione alla perdita: Il dolore di perdere 100 TL è doppio rispetto al piacere di guadagnare 100 TL. Pertanto, gli investitori mantengono posizioni in perdita troppo a lungo (effetto disposizione).',
                'mathematical_formula': 'Avversione alla Perdita Ratio = (Valore Guadagno / Valore Perdita) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "Il 90% delle tue decisioni finanziarie è psicologico, non tecnico."'
            }
        },
        'tax_planning': {
            'tr': {
                'title': 'Vergi Planlaması',
                'concept_definition': 'İleri seviyede vergi planlaması, vergi avantajlı hesaplar, vergi arbitrajı, vergi loss harvesting ve vergi efektif yatırım stratejilerini içerir. BES, 401k, IRA gibi vergi avantajlı hesaplar önemlidir.',
                'practical_example': 'BES katkısı: Aylık 1.000 TL, işveren katkısı %25, devlet katkısı %30. Toplam aylık katkı = 1.000 × (1 + 0.25 + 0.30) = 1.550 TL. 20 yılda %8 getiriyle yaklaşık 700.000 TL birikim olur.',
                'mathematical_formula': 'Vergi Etkili Getiri = Nominal Getiri × (1 - Vergi Oranı)\nBES Getirisi = Katkı × (1 + İşveren + Devlet) × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_bes_return(contribution, employer_match, annual_return, years)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Vergi, yatırım getirinizin en büyük düşmanıdır. Vergi planlaması, finansal başarının kritik bir parçasıdır."'
            },
            'en': {
                'title': 'Tax Planning',
                'concept_definition': 'Advanced tax planning includes tax-advantaged accounts, tax arbitrage, tax loss harvesting, and tax-efficient investment strategies. Tax-advantaged accounts like BES, 401k, IRA are important.',
                'practical_example': 'BES contribution: Monthly 1,000 TL, employer match 25%, government match 30%. Total monthly contribution = 1,000 × (1 + 0.25 + 0.30) = 1,550 TL. In 20 years at 8% return, approximately 700,000 TL accumulation.',
                'mathematical_formula': 'Tax-Effective Return = Nominal Return × (1 - Tax Rate)\nBES Return = Contribution × (1 + Employer + Government) × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_bes_return(contribution, employer_match, annual_return, years)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Tax is the biggest enemy of your investment returns. Tax planning is a critical part of financial success."'
            },
            'de': {
                'title': 'Steuerplanung',
                'concept_definition': 'Fortgeschrittene Steuerplanung umfasst steuerbegünstigte Konten, Steuerarbitrage, Tax Loss Harvesting und steuereffiziente Anlagestrategien. Steuerbegünstigte Konten wie BES, 401k, IRA sind wichtig.',
                'practical_example': 'BES-Beitrag: Monatlich 1.000 TL, Arbeitgeber-Match 25%, Regierungs-Match 30%. Gesamtmonatlicher Beitrag = 1.000 × (1 + 0,25 + 0,30) = 1.550 TL. In 20 Jahren bei 8% Rendite ca. 700.000 TL Akkumulation.',
                'mathematical_formula': 'Steuereffektive Rendite = Nominale Rendite × (1 - Steuersatz)\nBES-Rendite = Beitrag × (1 + Arbeitgeber + Regierung) × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_bes_return(contribution, employer_match, annual_return, years)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Steuern sind der größte Feind Ihrer Anlagerenditen. Steuerplanung ist ein kritischer Teil des finanziellen Erfolgs."'
            },
            'it': {
                'title': 'Pianificazione Fiscale',
                'concept_definition': 'La pianificazione fiscale avanzata include conti con vantaggi fiscali, arbitraggio fiscale, tax loss harvesting e strategie di investimento efficienti dal punto di vista fiscale. I conti con vantaggi fiscali come BES, 401k, IRA sono importanti.',
                'practical_example': 'Contributo BES: Mensile 1.000 TL, corrispondenza datore di lavoro 25%, corrispondenza governo 30%. Contributo mensile totale = 1.000 × (1 + 0,25 + 0,30) = 1.550 TL. In 20 anni all\'8% di rendimento, circa 700.000 TL di accumulo.',
                'mathematical_formula': 'Rendimento Efficace Fiscale = Rendimento Nominale × (1 - Aliquota Fiscale)\nRendimento BES = Contributo × (1 + Datore di Lavoro + Governo) × ((1 + r)^n - 1) / r',
                'python_function': 'calculate_bes_return(contribution, employer_match, annual_return, years)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "Le tasse sono il nemico più grande dei tuoi rendimenti di investimento. La pianificazione fiscale è una parte critica del successo finanziario."'
            }
        },
        'retirement_planning': {
            'tr': {
                'title': 'Emeklilik Planlaması',
                'concept_definition': 'İleri seviyede emeklilik planlaması, emeklilik yaşı hesaplaması, sosyal güvenlik optimizasyonu, emeklilik gelir kaynakları ve emeklilik harcama stratejilerini içerir. 4% kuralının dinamik versiyonları kullanılır.',
                'practical_example': 'Emeklilik yaşı 65, yaşam beklentisi 90. 25 yıl emeklilik. Yıllık harcama 200.000 TL. %3 çekim oranıyla gerekli birikim = 200.000 / 0.03 = 6.666.667 TL. %5 çekim oranıyla = 4.000.000 TL.',
                'mathematical_formula': 'Emeklilik Birikimi = Yıllık Harcama × (1 - (1 + r)^(-n)) / r\nDinamik Çekim = Önceki Çekim × (1 + Enflasyon - Getiri)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Emeklilik, işten ayrılmak değil, finansal özgürlüktür. Ne zaman emekli olacağınızı siz seçersiniz."'
            },
            'en': {
                'title': 'Retirement Planning',
                'concept_definition': 'Advanced retirement planning includes retirement age calculation, social security optimization, retirement income sources, and retirement spending strategies. Dynamic versions of the 4% rule are used.',
                'practical_example': 'Retirement age 65, life expectancy 90. 25 years of retirement. Annual expense 200,000 TL. With 3% withdrawal rate, required savings = 200,000 / 0.03 = 6,666,667 TL. With 5% withdrawal rate = 4,000,000 TL.',
                'mathematical_formula': 'Retirement Savings = Annual Expense × (1 - (1 + r)^(-n)) / r\nDynamic Withdrawal = Previous Withdrawal × (1 + Inflation - Return)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Retirement is not quitting work, it\'s financial freedom. You choose when to retire."'
            },
            'de': {
                'title': 'Rentenplanung',
                'concept_definition': 'Fortgeschrittene Rentenplanung umfasst Rentenalterberechnung, Sozialversicherungs-Optimierung, Renteneinkommensquellen und Rentenausgabenstrategien. Dynamische Versionen der 4%-Regel werden verwendet.',
                'practical_example': 'Rentenalter 65, Lebenserwartung 90. 25 Jahre Rente. Jährliche Ausgabe 200.000 TL. Mit 3% Entnahmerate, erforderliche Ersparnisse = 200.000 / 0,03 = 6.666.667 TL. Mit 5% Entnahmerate = 4.000.000 TL.',
                'mathematical_formula': 'Rentenersparnisse = Jährliche Ausgabe × (1 - (1 + r)^(-n)) / r\nDynamische Entnahme = Vorherige Entnahme × (1 + Inflation - Rendite)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Rente ist nicht die Arbeit aufzugeben, sondern finanzielle Freiheit. Sie entscheiden, wann Sie in Rente gehen."'
            },
            'it': {
                'title': 'Pianificazione della Pensione',
                'concept_definition': 'La pianificazione della pensione avanzata include il calcolo dell\'età pensionabile, l\'ottimizzazione della sicurezza sociale, le fonti di reddito pensionistico e le strategie di spesa pensionistica. Vengono utilizzate versioni dinamiche della regola del 4%.',
                'practical_example': 'Età pensionabile 65, aspettativa di vita 90. 25 anni di pensione. Spesa annuale 200.000 TL. Con tasso di prelievo del 3%, risparmio richiesto = 200.000 / 0,03 = 6.666.667 TL. Con tasso del 5% = 4.000.000 TL.',
                'mathematical_formula': 'Risparmio Pensionistico = Spesa Annuale × (1 - (1 + r)^(-n)) / r\nPrelievo Dinamico = Prelievo Precedente × (1 + Inflazione - Rendimento)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "La pensione non è smettere di lavorare, è libertà finanziaria. Tu scegli quando andare in pensione."'
            }
        },
        'international_investing': {
            'tr': {
                'title': 'Uluslararası Yatırım',
                'concept_definition': 'İleri seviyede uluslararası yatırım, döviz riski, ülke riski, küresel diversifikasyon ve gelişmekte olan piyasaları içerir. ETF ve ADR ile uluslararası yatırımlar yapılır.',
                'practical_example': 'Portföy: %60 ABD (S&P 500), %20 Avrupa (STOXX 600), %10 Asya (MSCI Asia), %10 Gelişmekte Olan (MSCI EM). Döviz riski: USD/TL volatilitesi %15. Döviz hedge ile risk azaltılır.',
                'mathematical_formula': 'Döviz Riski = Fark × Pozisyon\nReel Getiri = (1 + Nominal) × (1 + Döviz) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Küresel diversifikasyon, ülke riskini azaltmanın en iyi yoludur. Tüm yumurtaları aynı sepete koymayın."'
            },
            'en': {
                'title': 'International Investing',
                'concept_definition': 'Advanced international investing includes currency risk, country risk, global diversification, and emerging markets. International investments are made through ETFs and ADRs.',
                'practical_example': 'Portfolio: 60% US (S&P 500), 20% Europe (STOXX 600), 10% Asia (MSCI Asia), 10% Emerging (MSCI EM). Currency risk: USD/TL volatility 15%. Currency hedges reduce risk.',
                'mathematical_formula': 'Currency Risk = Change × Position\nReal Return = (1 + Nominal) × (1 + Currency) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Global diversification is the best way to reduce country risk. Don\'t put all your eggs in one basket."'
            },
            'de': {
                'title': 'Internationales Investieren',
                'concept_definition': 'Fortgeschrittenes internationales Investieren umfasst Währungsrisiko, Länderrisiko, globale Diversifizierung und Schwellenländer. Internationale Investitionen werden über ETFs und ADRs getätigt.',
                'practical_example': 'Portfolio: 60% USA (S&P 500), 20% Europa (STOXX 600), 10% Asien (MSCI Asia), 10% Schwellenländer (MSCI EM). Währungsrisiko: USD/TL Volatilität 15%. Währungshedges reduzieren das Risiko.',
                'mathematical_formula': 'Währungsrisiko = Änderung × Position\nReale Rendite = (1 + Nominal) × (1 + Währung) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Globale Diversifizierung ist der beste Weg, das Länderrisiko zu reduzieren. Legen Sie nicht alle Eier in einen Korb."'
            },
            'it': {
                'title': 'Investimento Internazionale',
                'concept_definition': 'L\'investimento internazionale avanzato include il rischio di cambio, il rischio paese, la diversificazione globale e i mercati emergenti. Gli investimenti internazionali vengono effettuati tramite ETF e ADR.',
                'practical_example': 'Portafoglio: 60% USA (S&P 500), 20% Europa (STOXX 600), 10% Asia (MSCI Asia), 10% Emergenti (MSCI EM). Rischio valutario: volatilità USD/TL 15%. Le coperture valutarie riducono il rischio.',
                'mathematical_formula': 'Rischio Valutario = Cambiamento × Posizione\nRendimento Reale = (1 + Nominale) × (1 + Valuta) - 1',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La diversificazione globale è il modo migliore per ridurre il rischio paese. Non mettere tutte le uova nello stesso paniere."'
            }
        },
        'derivatives': {
            'tr': {
                'title': 'Türev Araçlar',
                'concept_definition': 'İleri seviyede türev araçlar, opsiyonlar, vadeli işlemler, swaplar ve türev stratejilerini içerir. Hedging, spekülasyon ve arbitraj için kullanılır. Black-Scholes modeli opsiyon fiyatlaması için kullanılır.',
                'practical_example': 'Call opsiyon: Hisse fiyatı 100 TL, strike 95 TL, vade 3 ay, volatilite %20, risksiz faiz %5. Black-Scholes ile opsiyon fiyatı yaklaşık 8.5 TL. Delta = 0.6 (hisse %1 artarsa opsiyon %0.6 artar).',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rT) × N(d2)\nd1 = (ln(S/K) + (r + σ²/2)T) / (σ√T)',
                'python_function': 'calculate_capm_return(risk_free_rate, beta, market_return)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Türev araçlar, risk transferi için güçlü araçlardır. Ancak yanlış kullanıldığında felaket sonuçlar doğurabilir."'
            },
            'en': {
                'title': 'Derivatives',
                'concept_definition': 'Advanced derivatives includes options, futures, swaps, and derivative strategies. Used for hedging, speculation, and arbitrage. Black-Scholes model is used for option pricing.',
                'practical_example': 'Call option: Stock price 100 TL, strike 95 TL, maturity 3 months, volatility 20%, risk-free rate 5%. Black-Scholes option price approximately 8.5 TL. Delta = 0.6 (if stock rises 1%, option rises 0.6%).',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rT) × N(d2)\nd1 = (ln(S/K) + (r + σ²/2)T) / (σ√T)',
                'python_function': 'calculate_capm_return(risk_free_rate, beta, market_return)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Derivatives are powerful tools for risk transfer. However, when misused, they can lead to disastrous results."'
            },
            'de': {
                'title': 'Derivate',
                'concept_definition': 'Fortgeschrittene Derivate umfassen Optionen, Futures, Swaps und Derivatstrategien. Werden für Hedging, Spekulation und Arbitrage verwendet. Black-Scholes-Modell wird für Optionspreisierung verwendet.',
                'practical_example': 'Call-Option: Aktienkurs 100 TL, Strike 95 TL, Laufzeit 3 Monate, Volatilität 20%, risikofreier Zins 5%. Black-Scholes-Optionspreis ca. 8,5 TL. Delta = 0,6 (wenn Aktie um 1% steigt, steigt Option um 0,6%).',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rT) × N(d2)\nd1 = (ln(S/K) + (r + σ²/2)T) / (σ√T)',
                'python_function': 'calculate_capm_return(risk_free_rate, beta, market_return)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Derivate sind mächtige Werkzeuge für Risikotransfer. Bei falscher Verwendung können sie jedoch zu katastrophalen Ergebnissen führen."'
            },
            'it': {
                'title': 'Derivati',
                'concept_definition': 'I derivati avanzati includono opzioni, futures, swap e strategie derivati. Utilizzati per hedging, speculazione e arbitraggio. Il modello Black-Scholes viene utilizzato per la determinazione del prezzo delle opzioni.',
                'practical_example': 'Opzione Call: Prezzo azione 100 TL, strike 95 TL, scadenza 3 mesi, volatilità 20%, tasso privo di rischio 5%. Prezzo opzione Black-Scholes circa 8,5 TL. Delta = 0,6 (se l\'azione aumenta dell\'1%, l\'opzione aumenta dello 0,6%).',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rT) × N(d2)\nd1 = (ln(S/K) + (r + σ²/2)T) / (σ√T)',
                'python_function': 'calculate_capm_return(risk_free_rate, beta, market_return)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I derivati sono potenti strumenti per il trasferimento del rischio. Tuttavia, se usati in modo errato, possono portare a risultati disastrosi."'
            }
        },
        'alternative_investments': {
            'tr': {
                'title': 'Alternatif Yatırımlar',
                'concept_definition': 'İleri seviyede alternatif yatırımlar, private equity, venture capital, hedge funds, gayrimenkul, emtia, sanat, antika ve koleksiyonları içerir. Düşük korelasyon ve yüksek getiri potansiyeli vardır.',
                'practical_example': 'Alternatif portföy: %30 private equity (IRR %18), %20 hedge funds (Sharpe 1.5), %25 gayrimenkul (cap rate %6), %15 emtia (altın %8), %10 sanat (CAGR %10). Portföy korelasyonu 0.3.',
                'mathematical_formula': 'Alternatif Getiri = (1 + r)^n - 1\nPrivate Equity IRR = Σ(CFt / (1 + IRR)^t) = 0',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Alternatif yatırımlar, portföy diversifikasyonu için önemlidir. Ancak yüksek risk ve düşük likidite vardır."'
            },
            'en': {
                'title': 'Alternative Investments',
                'concept_definition': 'Advanced alternative investments includes private equity, venture capital, hedge funds, real estate, commodities, art, antiques, and collectibles. Low correlation and high return potential.',
                'practical_example': 'Alternative portfolio: 30% private equity (IRR 18%), 20% hedge funds (Sharpe 1.5), 25% real estate (cap rate 6%), 15% commodities (gold 8%), 10% art (CAGR 10%). Portfolio correlation 0.3.',
                'mathematical_formula': 'Alternative Return = (1 + r)^n - 1\nPrivate Equity IRR = Σ(CFt / (1 + IRR)^t) = 0',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Alternative investments are important for portfolio diversification. However, they have high risk and low liquidity."'
            },
            'de': {
                'title': 'Alternative Investitionen',
                'concept_definition': 'Fortgeschrittene alternative Investitionen umfassen Private Equity, Venture Capital, Hedge Funds, Immobilien, Rohstoffe, Kunst, Antiquitäten und Sammlerstücke. Niedrige Korrelation und hohes Renditepotenzial.',
                'practical_example': 'Alternatives Portfolio: 30% Private Equity (IRR 18%), 20% Hedge Funds (Sharpe 1,5), 25% Immobilien (Cap Rate 6%), 15% Rohstoffe (Gold 8%), 10% Kunst (CAGR 10%). Portfolio-Korrelation 0,3.',
                'mathematical_formula': 'Alternative Rendite = (1 + r)^n - 1\nPrivate Equity IRR = Σ(CFt / (1 + IRR)^t) = 0',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Alternative Investitionen sind wichtig für Portfolio-Diversifizierung. Sie haben jedoch hohes Risiko und geringe Liquidität."'
            },
            'it': {
                'title': 'Investimenti Alternativi',
                'concept_definition': 'Gli investimenti alternativi avanzati includono private equity, venture capital, hedge fund, immobili, materie prime, arte, antichità e collezionabili. Bassa correlazione e alto potenziale di rendimento.',
                'practical_example': 'Portafoglio alternativo: 30% private equity (IRR 18%), 20% hedge fund (Sharpe 1.5), 25% immobili (cap rate 6%), 15% materie prime (oro 8%), 10% arte (CAGR 10%). Correlazione del portafoglio 0.3.',
                'mathematical_formula': 'Rendimento Alternativo = (1 + r)^n - 1\nPrivate Equity IRR = Σ(CFt / (1 + IRR)^t) = 0',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "Gli investimenti alternativi sono importanti per la diversificazione del portafoglio. Tuttavia, hanno alto rischio e bassa liquidità."'
            }
        }
    },
    'expert': {
        'quantitative_finance': {
            'tr': {
                'title': 'Kuantitatif Finans',
                'concept_definition': 'Uzman seviyede kuantitatif finans, Monte Carlo simülasyonları, stokastik süreçler, Ito lemması, Black-Scholes-Merton modeli ve Greeks hesaplamalarını içerir. Stokastik diferansiyel denklemler ve sayısal yöntemler kullanılır.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Hisse fiyatı 100 TL, μ = 0.10, σ = 0.20, dt = 1/252. Monte Carlo ile 10.000 simülasyon yapılır. %95 güven aralığı hesaplanır.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Kuantitatif modeller, piyasa riskini anlamak için önemlidir. Ancak modellerin sınırlamalarını bilmek kritiktir."'
            },
            'en': {
                'title': 'Quantitative Finance',
                'concept_definition': 'Expert level quantitative finance includes Monte Carlo simulations, stochastic processes, Ito lemma, Black-Scholes-Merton model, and Greeks calculations. Stochastic differential equations and numerical methods are used.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Stock price 100 TL, μ = 0.10, σ = 0.20, dt = 1/252. 10,000 Monte Carlo simulations are performed. 95% confidence interval is calculated.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Quantitative models are important for understanding market risk. However, knowing the limitations of models is critical."'
            },
            'de': {
                'title': 'Quantitative Finance',
                'concept_definition': 'Expertenlevel Quantitative Finance umfasst Monte-Carlo-Simulationen, stochastische Prozesse, Ito-Lemma, Black-Scholes-Merton-Modell und Greeks-Berechnungen. Stochastische Differentialgleichungen und numerische Methoden werden verwendet.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Aktienkurs 100 TL, μ = 0,10, σ = 0,20, dt = 1/252. 10.000 Monte-Carlo-Simulationen werden durchgeführt. 95% Konfidenzintervall wird berechnet.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Quantitative Modelle sind wichtig für das Verständnis des Marktrisikos. Das Wissen um die Grenzen der Modelle ist jedoch kritisch."'
            },
            'it': {
                'title': 'Finanza Quantitativa',
                'concept_definition': 'La finanza quantitativa a livello esperto include simulazioni Monte Carlo, processi stocastici, lemma di Ito, modello Black-Scholes-Merton e calcoli dei Greci. Vengono utilizzate equazioni differenziali stocastiche e metodi numerici.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Prezzo azione 100 TL, μ = 0.10, σ = 0.20, dt = 1/252. Vengono eseguite 10.000 simulazioni Monte Carlo. Viene calcolato l\'intervallo di confidenza al 95%.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I modelli quantitativi sono importanti per comprendere il rischio di mercato. Tuttavia, conoscere le limitazioni dei modelli è critico."'
            }
        },
        'algorithmic_trading': {
            'tr': {
                'title': 'Algoritmik Ticaret',
                'concept_definition': 'Uzman seviyede algoritmik ticaret, high-frequency trading, arbitraj stratejileri, market making ve execution algoritmalarını içerir. Latency, slippage ve transaction cost optimizasyonu önemlidir.',
                'practical_example': 'Statistical arbitrage: İki varlık arasındaki cointegration ilişkisi kullanılır. Spread = Y - βX. Spread ortalamaya döndüğünde long/short pozisyon alınır. Z-score > 2 sinyal verir.',
                'mathematical_formula': 'Cointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Position × Price Change) - Transaction Costs',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Algoritmik ticaret, hız ve veri avantajıdır. Ancak sistemik riskler ve flash crash\'ler potansiyel felaketlerdir."'
            },
            'en': {
                'title': 'Algorithmic Trading',
                'concept_definition': 'Expert level algorithmic trading includes high-frequency trading, arbitrage strategies, market making, and execution algorithms. Latency, slippage, and transaction cost optimization are important.',
                'practical_example': 'Statistical arbitrage: Cointegration relationship between two assets is used. Spread = Y - βX. Long/short positions are taken when spread reverts to mean. Z-score > 2 gives signal.',
                'mathematical_formula': 'Cointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Position × Price Change) - Transaction Costs',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Algorithmic trading is about speed and data advantage. However, systemic risks and flash crashes are potential disasters."'
            },
            'de': {
                'title': 'Algorithmischer Handel',
                'concept_definition': 'Expertenlevel Algorithmischer Handel umfasst High-Frequency-Trading, Arbitrage-Strategien, Market Making und Execution-Algorithmen. Latency, Slippage und Transaction-Cost-Optimierung sind wichtig.',
                'practical_example': 'Statistical Arbitrage: Kointegrationsbeziehung zwischen zwei Vermögenswerten wird verwendet. Spread = Y - βX. Long/Short-Positionen werden eingenommen, wenn Spread zum Mittelwert zurückkehrt. Z-Score > 2 gibt Signal.',
                'mathematical_formula': 'Cointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Position × Preisänderung) - Transaktionskosten',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Algorithmischer Handel ist Geschwindigkeit und Datenvorteil. Systemische Risiken und Flash Crashes sind jedoch potenzielle Katastrophen."'
            },
            'it': {
                'title': 'Trading Algoritmico',
                'concept_definition': 'Il trading algoritmico a livello esperto include high-frequency trading, strategie di arbitraggio, market making e algoritmi di esecuzione. Latency, slippage e ottimizzazione dei costi di transazione sono importanti.',
                'practical_example': 'Arbitraggio statistico: Viene utilizzata la relazione di cointegrazione tra due attività. Spread = Y - βX. Posizioni long/short vengono prese quando lo spread ritorna alla media. Z-score > 2 dà segnale.',
                'mathematical_formula': 'Cointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Positione × Variazione Prezzo) - Costi Transazione',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il trading algoritmico riguarda velocità e vantaggio dati. Tuttavia, i rischi sistemici e i flash crash sono potenziali disastri."'
            }
        },
        'machine_learning_finance': {
            'tr': {
                'title': 'Makine Öğrenmesi ve Finans',
                'concept_definition': 'Uzman seviyede ML finans, neural networks, deep learning, reinforcement learning ve NLP\'nin finansal uygulamalarını içerir. Hisse fiyat tahmini, risk modelleme, fraud detection ve sentiment analysis yapılır.',
                'practical_example': 'LSTM modeli ile hisse fiyat tahmini: 60 gün geçmiş veri, 10 gün ileri tahmin. Dropout ile overfitting önlenir. RMSE ve MAE metrikleri ile değerlendirme. Feature engineering: teknik indikatörler, haberler, sosyal medya.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Machine learning, veri kalitesine bağlıdır. Garbage in, garbage out. Finansal veriler noisy ve non-stationarydir."'
            },
            'en': {
                'title': 'Machine Learning in Finance',
                'concept_definition': 'Expert level ML finance includes neural networks, deep learning, reinforcement learning, and NLP applications in finance. Stock price prediction, risk modeling, fraud detection, and sentiment analysis are performed.',
                'practical_example': 'LSTM model for stock price prediction: 60 days historical data, 10 days forward prediction. Dropout prevents overfitting. Evaluation with RMSE and MAE metrics. Feature engineering: technical indicators, news, social media.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Machine learning depends on data quality. Garbage in, garbage out. Financial data is noisy and non-stationary."'
            },
            'de': {
                'title': 'Machine Learning in der Finanzen',
                'concept_definition': 'Expertenlevel ML Finance umfasst Neural Networks, Deep Learning, Reinforcement Learning und NLP-Anwendungen in der Finanzen. Aktienkursvorhersage, Risikomodellierung, Fraud Detection und Sentiment Analysis werden durchgeführt.',
                'practical_example': 'LSTM-Modell für Aktienkursvorhersage: 60 Tage historische Daten, 10 Tage Vorhersage. Dropout verhindert Overfitting. Bewertung mit RMSE und MAE Metriken. Feature Engineering: technische Indikatoren, Nachrichten, soziale Medien.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Machine Learning hängt von Datenqualität ab. Garbage in, garbage out. Finanzdaten sind verrauscht und nicht-stationär."'
            },
            'it': {
                'title': 'Machine Learning nella Finanza',
                'concept_definition': 'Il ML finanziario a livello esperto include reti neurali, deep learning, reinforcement learning e applicazioni NLP nella finanza. Vengono eseguite previsioni dei prezzi azionari, modellazione del rischio, rilevamento frodi e analisi del sentiment.',
                'practical_example': 'Modello LSTM per la previsione dei prezzi azionari: 60 giorni di dati storici, 10 giorni di previsione. Il dropout previene l\'overfitting. Valutazione con metriche RMSE e MAE. Feature engineering: indicatori tecnici, notizie, social media.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il machine learning dipende dalla qualità dei dati. Garbage in, garbage out. I dati finanziari sono rumorosi e non stazionari."'
            }
        },
        'blockchain_crypto': {
            'tr': {
                'title': 'Blockchain ve Kripto',
                'concept_definition': 'Uzman seviyede blockchain ve kripto, distributed ledger technology, smart contracts, DeFi, NFT ve kripto ekonomisini içerir. Proof of Work, Proof of Stake, consensus mekanizmaları ve tokenomics analiz edilir.',
                'practical_example': 'Bitcoin: PoW consensus, blok süresi 10 dakika, maksimum supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming. Tokenomics: inflation rate, vesting schedule, utility.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Blockchain, finansal sistemde devrim yaratabilir. Ancak volatilite ve düzenleyici riskler önemlidir."'
            },
            'en': {
                'title': 'Blockchain & Crypto',
                'concept_definition': 'Expert level blockchain and crypto includes distributed ledger technology, smart contracts, DeFi, NFT, and crypto economics. Proof of Work, Proof of Stake, consensus mechanisms, and tokenomics are analyzed.',
                'practical_example': 'Bitcoin: PoW consensus, block time 10 minutes, max supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming. Tokenomics: inflation rate, vesting schedule, utility.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Blockchain can revolutionize the financial system. However, volatility and regulatory risks are important."'
            },
            'de': {
                'title': 'Blockchain & Krypto',
                'concept_definition': 'Expertenlevel Blockchain und Krypto umfasst Distributed Ledger Technology, Smart Contracts, DeFi, NFT und Kryptoökonomie. Proof of Work, Proof of Stake, Konsensmechanismen und Tokenomics werden analysiert.',
                'practical_example': 'Bitcoin: PoW-Konsens, Blockzeit 10 Minuten, Max Supply 21M. Ethereum: PoS, Gas-Gebühr, Smart Contracts. DeFi: Lending, Borrowing, Yield Farming. Tokenomics: Inflationsrate, Vesting-Schedule, Utility.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Blockchain kann das Finanzsystem revolutionieren. Volatilität und regulatorische Risiken sind jedoch wichtig."'
            },
            'it': {
                'title': 'Blockchain e Cripto',
                'concept_definition': 'La blockchain e le cripto a livello esperto includono distributed ledger technology, smart contracts, DeFi, NFT e crypto economics. Proof of Work, Proof of Stake, meccanismi di consenso e tokenomics vengono analizzati.',
                'practical_example': 'Bitcoin: consenso PoW, tempo blocco 10 minuti, max supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming. Tokenomics: inflation rate, vesting schedule, utility.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La blockchain può rivoluzionare il sistema finanziario. Tuttavia, la volatilità e i rischi normativi sono importanti."'
            }
        },
        'esg_investing': {
            'tr': {
                'title': 'ESG Yatırımı',
                'concept_definition': 'Uzman seviyede ESG yatırımı, çevresel, sosyal ve yönetişim kriterlerini içerir. Sürdürülebilir yatırım, impact investing ve green bonds analiz edilir. ESG skorları ve raporlama standartları (GRI, SASB) kullanılır.',
                'practical_example': 'ESG skorlama: Çevresel (karbon ayak izi, enerji verimliliği), Sosyal (işçi hakları, topluluk ilişkileri), Yönetişim (kurumsal yönetim, şeffaflık). MSCI ESG Rating: AAA (lider) - CCC (gecikmiş).',
                'mathematical_formula': 'ESG Skoru = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "ESG yatırımı, sadece finansal getiri değil, sosyal etki de önemlidir. Uzun vadeli sürdürülebilirlik kritiktir."'
            },
            'en': {
                'title': 'ESG Investing',
                'concept_definition': 'Expert level ESG investing includes environmental, social, and governance criteria. Sustainable investing, impact investing, and green bonds are analyzed. ESG scores and reporting standards (GRI, SASB) are used.',
                'practical_example': 'ESG scoring: Environmental (carbon footprint, energy efficiency), Social (labor rights, community relations), Governance (corporate governance, transparency). MSCI ESG Rating: AAA (leader) - CCC (laggard).',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "ESG investing is not just about financial returns, but also social impact. Long-term sustainability is critical."'
            },
            'de': {
                'title': 'ESG-Investition',
                'concept_definition': 'Expertenlevel ESG-Investition umfasst Umwelt-, Sozial- und Unternehmensführungskriterien. Nachhaltiges Investieren, Impact Investing und Green Bonds werden analysiert. ESG-Scores und Berichtsstandards (GRI, SASB) werden verwendet.',
                'practical_example': 'ESG-Scoring: Umwelt (CO2-Fußabdruck, Energieeffizienz), Sozial (Arbeitsrechte, Gemeindebeziehungen), Unternehmensführung (Corporate Governance, Transparenz). MSCI ESG Rating: AAA (Führer) - CCC (Nachzügler).',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "ESG-Investition ist nicht nur finanzielle Rendite, sondern auch soziale Wirkung. Langfristige Nachhaltigkeit ist kritisch."'
            },
            'it': {
                'title': 'Investimento ESG',
                'concept_definition': 'L\'investimento ESG a livello esperto include criteri ambientali, sociali e di governance. Investimento sostenibile, impact investing e green bonds vengono analizzati. Vengono utilizzati punteggi ESG e standard di reporting (GRI, SASB).',
                'practical_example': 'Punteggio ESG: Ambientale (impronta di carbonio, efficienza energetica), Sociale (diritti dei lavoratori, relazioni comunitarie), Governance (governance aziendale, trasparenza). Rating ESG MSCI: AAA (leader) - CCC (ritardatario).',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "L\'investimento ESG non riguarda solo i rendimenti finanziari, ma anche l\'impatto sociale. La sostenibilità a lungo termine è critica."'
            }
        }
    },
    'expert': {
        'income_expenses': {
            'tr': {
                'title': 'Gelir ve Giderler - Uzman Seviye',
                'concept_definition': 'Uzman seviyede gelir ve gider yönetimi, çok boyutlu senaryo analizi, stres testleri ve Monte Carlo simülasyonlarını içerir. Enflasyon, vergi, yaşam tarzı değişiklikleri ve beklenmedik olaylar gelecekteki nakit akışını etkiler. Dinamik bütçeleme ve adaptif harcama stratejileri uygulanır.',
                'practical_example': 'Monte Carlo simülasyonu: 10.000 farklı senaryo çalıştırılır. %95 güven aralığında, 10 yıl sonraki nakit akışı 150.000 - 250.000 TL arasındadır. En kötü senaryoda nakit akışı 100.000 TL\'ye düşer. Güvenlik marjı %20 olarak belirlenir.',
                'mathematical_formula': 'Nakit Akışı Dağılımı = Monte Carlo(Senaryo)\nGüvenlik Marjı = (Ortalama - En Kötü) / Ortalama',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Gelecek tahminlemesi imkansızdır. Sadece senaryo analizi yapın ve farklı sonuçlara hazırlıklı olun."'
            },
            'en': {
                'title': 'Income & Expenses - Expert',
                'concept_definition': 'Expert level income and expense management includes multi-dimensional scenario analysis, stress tests, and Monte Carlo simulations. Inflation, taxes, lifestyle changes, and unexpected events affect future cash flows. Dynamic budgeting and adaptive spending strategies are applied.',
                'practical_example': 'Monte Carlo simulation: 10,000 different scenarios are run. At 95% confidence interval, cash flow in 10 years is between 150,000 - 250,000 TL. In worst case, cash flow drops to 100,000 TL. Safety margin is set at 20%.',
                'mathematical_formula': 'Cash Flow Distribution = Monte Carlo(Scenario)\nSafety Margin = (Average - Worst) / Average',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Future forecasting is impossible. Only do scenario analysis and be prepared for different outcomes."'
            },
            'de': {
                'title': 'Einkommen und Ausgaben - Experte',
                'concept_definition': 'Einkommens- und Ausgabenmanagement auf Experte-Niveau umfasst multidimensionale Szenarioanalyse, Stresstests und Monte-Carlo-Simulationen. Inflation, Steuern, Lebensstiländerungen und unerwartete Ereignisse beeinflussen zukünftige Cashflows. Dynamisches Budgeting und adaptive Ausgabenstrategien werden angewendet.',
                'practical_example': 'Monte-Carlo-Simulation: 10.000 verschiedene Szenarien werden ausgeführt. Bei 95% Konfidenzintervall liegt der Cashflow in 10 Jahren zwischen 150.000 - 250.000 TL. Im schlimmsten Fall fällt der Cashflow auf 100.000 TL. Sicherheitsmarge wird auf 20% festgelegt.',
                'mathematical_formula': 'Cashflow-Verteilung = Monte-Carlo(Szenario)\nSicherheitsmarge = (Durchschnitt - Schlechteste) / Durchschnitt',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Zukunftsprognosen sind unmöglich. Führen Sie nur Szenarioanalysen durch und seien Sie auf verschiedene Ergebnisse vorbereitet."'
            },
            'it': {
                'title': 'Reddito e Spese - Esperto',
                'concept_definition': 'La gestione del reddito e delle spese a livello esperto include l\'analisi multidimensionale degli scenari, gli stress test e le simulazioni Monte Carlo. L\'inflazione, le tasse, i cambiamenti dello stile di vita e gli eventi imprevisti influenzano i flussi di cassa futuri. Vengono applicati il budgeting dinamico e le strategie di spesa adattive.',
                'practical_example': 'Simulazione Monte Carlo: Vengono eseguiti 10.000 diversi scenari. Al 95% di intervallo di confidenza, il flusso di cassa in 10 anni è tra 150.000 - 250.000 TL. Nel caso peggiore, il flusso di cassa scende a 100.000 TL. Il margine di sicurezza è impostato al 20%.',
                'mathematical_formula': 'Distribuzione del Flusso di Cassa = Monte Carlo(Scenario)\nMargine di Sicurezza = (Media - Peggiore) / Media',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Le previsioni future sono impossibili. Fai solo analisi degli scenari e sii preparato per diversi risultati."'
            }
        },
        'compound_interest': {
            'tr': {
                'title': 'Bileşik Faiz - Uzman Seviye',
                'concept_definition': 'Uzman seviyede bileşik faiz, sürekli bileşikleşme, logaritmik büyüme ve üstel fonksiyonların analizini içerir. Doğal logaritma (ln), e sayısı ve diferansiyel denklemler kullanılır. Zamanın gücü ve bileşik faizin etkisi matematiksel olarak modellenir.',
                'practical_example': 'Sürekli bileşikleşme: A = P × e^(rt). P = 100.000, r = 0.08, t = 10. A = 100.000 × e^(0.8) = 100.000 × 2.2255 = 222.550 TL. Yıllık bileşikleşme ile: A = 100.000 × (1.08)^10 = 215.892 TL. Fark = 6.658 TL.',
                'mathematical_formula': 'Sürekli Bileşikleşme: A = P × e^(rt)\nBüyüme Oranı: dA/dt = r × A\nÇiftleme Süresi: t = ln(2) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Üstel büyüme, insan zihnini aşar. Küçük farklar zamanla devasa sonuçlar yaratır."'
            },
            'en': {
                'title': 'Compound Interest - Expert',
                'concept_definition': 'Expert level compound interest includes continuous compounding, logarithmic growth, and exponential function analysis. Natural logarithm (ln), e number, and differential equations are used. The power of time and compound interest are mathematically modeled.',
                'practical_example': 'Continuous compounding: A = P × e^(rt). P = 100,000, r = 0.08, t = 10. A = 100,000 × e^(0.8) = 100,000 × 2.2255 = 222,550 TL. With annual compounding: A = 100,000 × (1.08)^10 = 215,892 TL. Difference = 6,658 TL.',
                'mathematical_formula': 'Continuous Compounding: A = P × e^(rt)\nGrowth Rate: dA/dt = r × A\nDoubling Time: t = ln(2) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Exponential growth exceeds human comprehension. Small differences create massive results over time."'
            },
            'de': {
                'title': 'Zinseszins - Experte',
                'concept_definition': 'Zinseszins auf Experte-Niveau umfasst kontinuierliche Verzinsung, logarithmisches Wachstum und Exponentialfunktionsanalyse. Natürlicher Logarithmus (ln), e-Zahl und Differentialgleichungen werden verwendet. Die Kraft von Zeit und Zinseszins werden mathematisch modelliert.',
                'practical_example': 'Kontinuierliche Verzinsung: A = P × e^(rt). P = 100.000, r = 0,08, t = 10. A = 100.000 × e^(0,8) = 100.000 × 2,2255 = 222.550 TL. Mit jährlicher Verzinsung: A = 100.000 × (1,08)^10 = 215.892 TL. Differenz = 6.658 TL.',
                'mathematical_formula': 'Kontinuierliche Verzinsung: A = P × e^(rt)\nWachstumsrate: dA/dt = r × A\nVerdoppelungszeit: t = ln(2) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Exponentielles Wachstum übersteigt das menschliche Verständnis. Kleine Unterschiede schaffen über Zeit massive Ergebnisse."'
            },
            'it': {
                'title': 'Interesse Composto - Esperto',
                'concept_definition': 'L\'interesse composto a livello esperto include la composizione continua, la crescita logaritmica e l\'analisi delle funzioni esponenziali. Il logaritmo naturale (ln), il numero e e le equazioni differenziali vengono utilizzati. Il potere del tempo e dell\'interesse composto vengono modellati matematicamente.',
                'practical_example': 'Composizione continua: A = P × e^(rt). P = 100.000, r = 0.08, t = 10. A = 100.000 × e^(0.8) = 100.000 × 2.2255 = 222.550 TL. Con composizione annuale: A = 100.000 × (1.08)^10 = 215.892 TL. Differenza = 6.658 TL.',
                'mathematical_formula': 'Composizione Continua: A = P × e^(rt)\nTasso di Crescita: dA/dt = r × A\nTempo di Raddoppio: t = ln(2) / r',
                'python_function': 'calculate_compound_interest(principal, annual_rate, 365, years)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La crescita esponenziale supera la comprensione umana. Piccole differenze creano risultati massicci nel tempo."'
            }
        },
        'assets': {
            'tr': {
                'title': 'Varlıklar ve Varlık Sınıfları - Uzman Seviye',
                'concept_definition': 'Uzman seviyede varlık yönetimi, CAPM (Capital Asset Pricing Model), Beta katsayısı, alpha getiri analizi, faktör modelleri (Fama-French 3 faktör, Carhart 4 faktör) ve portföy optimizasyonunu içerir. Sharpe Oranı, Sortino Oranı, Information Ratio, Treynor Oranı ve Jensen\'s Alpha gibi risk ayarlı getiri metrikleri kullanılır.',
                'practical_example': 'Fama-French 3 faktör modeli: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML). Beta = 1.5, SMB faktörü = 0.3, HML faktörü = 0.2. Beklenen getiri = Rf + 1.5(Mkt-Rf) + 0.3(SMB) + 0.2(HML). Alpha = 2% olan hisse, beklenen getirisinden %2 daha fazla getiri sağlar.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)\nFama-French: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML)\nTreynor Oranı = (Rp - Rf) / β',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Piyasa fiyatı ve iç değer arasındaki fark, fırsat yaratır. Bu farkı anlamak, başarılı yatırımın anahtarıdır."'
            },
            'en': {
                'title': 'Assets & Asset Classes - Expert',
                'concept_definition': 'Expert level asset management includes CAPM (Capital Asset Pricing Model), Beta coefficient, alpha return analysis, factor models (Fama-French 3 factor, Carhart 4 factor), and portfolio optimization. Risk-adjusted return metrics like Sharpe Ratio, Sortino Ratio, Information Ratio, Treynor Ratio, and Jensen\'s Alpha are used.',
                'practical_example': 'Fama-French 3 factor model: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML). Beta = 1.5, SMB factor = 0.3, HML factor = 0.2. Expected return = Rf + 1.5(Mkt-Rf) + 0.3(SMB) + 0.2(HML). Stock with Alpha = 2% provides 2% more return than expected.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)\nFama-French: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML)\nTreynor Ratio = (Rp - Rf) / β',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "The difference between market price and intrinsic value creates opportunity. Understanding this difference is the key to successful investing."'
            },
            'de': {
                'title': 'Vermögenswerte und Anlageklassen - Experte',
                'concept_definition': 'Vermögensverwaltung auf Experte-Niveau umfasst CAPM (Capital Asset Pricing Model), Beta-Koeffizient, Alpha-Renditeanalyse, Faktormodelle (Fama-French 3-Faktor, Carhart 4-Faktor) und Portfolio-Optimierung. Risikobereinigte Renditemetriken wie Sharpe Ratio, Sortino Ratio, Information Ratio, Treynor Ratio und Jensen\'s Alpha werden verwendet.',
                'practical_example': 'Fama-French 3-Faktor-Modell: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML). Beta = 1,5, SMB-Faktor = 0,3, HML-Faktor = 0,2. Erwartete Rendite = Rf + 1,5(Mkt-Rf) + 0,3(SMB) + 0,2(HML). Aktie mit Alpha = 2% liefert 2% mehr Rendite als erwartet.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)\nFama-French: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML)\nTreynor Ratio = (Rp - Rf) / β',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Der Unterschied zwischen Marktpreis und innerem Wert schafft Gelegenheit. Diesen Unterschied zu verstehen, ist der Schlüssel zum erfolgreichen Investieren."'
            },
            'it': {
                'title': 'Attività e Classi di Attività - Esperto',
                'concept_definition': 'La gestione delle attività a livello esperto include CAPM (Capital Asset Pricing Model), coefficiente Beta, analisi del rendimento alpha, modelli fattoriali (Fama-French 3 fattori, Carhart 4 fattori) e l\'ottimizzazione del portafoglio. Metriche di rendimento aggiustate per il rischio come Sharpe Ratio, Sortino Ratio, Information Ratio, Treynor Ratio e Jensen\'s Alpha vengono utilizzate.',
                'practical_example': 'Modello Fama-French 3 fattori: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML). Beta = 1.5, fattore SMB = 0.3, fattore HML = 0.2. Rendimento atteso = Rf + 1.5(Mkt-Rf) + 0.3(SMB) + 0.2(HML). Azione con Alpha = 2% fornisce il 2% in più di rendimento rispetto al previsto.',
                'mathematical_formula': 'CAPM: E(R) = Rf + β × (Rm - Rf)\nFama-French: E(R) = Rf + β(Mkt-Rf) + s(SMB) + h(HML)\nTreynor Ratio = (Rp - Rf) / β',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La differenza tra prezzo di mercato e valore intrinseco crea opportunità. Comprendere questa differenza è la chiave per investire con successo."'
            }
        },
        'financial_freedom': {
            'tr': {
                'title': 'Finansal Özgürlük - Uzman Seviye',
                'concept_definition': 'Uzman seviyede finansal özgürlük, dinamik çekim stratejileri (Guyton-Klinger, VPW), sekans riski (sequence of returns risk) analizi ve emeklilik stres testlerini içerir. Emeklilik sırasındaki piyasa çöküşleri, çekim oranını etkiler. Güvenlik marjı, esneklik ve adaptif harcama stratejileri riski azaltır.',
                'practical_example': 'Guyton-Klinger stratejisi: Çekim oranı = Önceki Çekim × (1 + (Portföy Getirisi - Hedef Getiri) / Ayarlama Faktörü). Portföy getirisi %8, hedef %4 ise, çekim oranı artırılır. Sekans riski: Emeklilik başlangıcında piyasa %20 düşerse, çekim oranı %4\'ten %5\'e çıkar.',
                'mathematical_formula': 'Dinamik Çekim = Önceki Çekim × (1 + (Portföy Getirisi - Hedef) / Ayarlama)\nSekans Riski = (1 - Çekim Oranı) × Piyasa Düşüşü\nGüvenlik Marjı = (Portföy - Gerekli) / Gerekli',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Finansal özgürlük, esneklik gerektirir. Piyasa koşullarına göre harcamanızı ayarlayın."'
            },
            'en': {
                'title': 'Financial Freedom - Expert',
                'concept_definition': 'Expert level financial freedom includes dynamic withdrawal strategies (Guyton-Klinger, VPW), sequence of returns risk analysis, and retirement stress tests. Market crashes at retirement affect withdrawal rates. Safety margin, flexibility, and adaptive spending strategies reduce risk.',
                'practical_example': 'Guyton-Klinger strategy: Withdrawal rate = Previous Withdrawal × (1 + (Portfolio Return - Target Return) / Adjustment Factor). If portfolio return is 8%, target is 4%, withdrawal rate increases. Sequence risk: If market drops 20% at retirement start, withdrawal rate increases from 4% to 5%.',
                'mathematical_formula': 'Dynamic Withdrawal = Previous Withdrawal × (1 + (Portfolio Return - Target) / Adjustment)\nSequence Risk = (1 - Withdrawal Rate) × Market Decline\nSafety Margin = (Portfolio - Required) / Required',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Financial freedom requires flexibility. Adjust your spending according to market conditions."'
            },
            'de': {
                'title': 'Finanzielle Freiheit - Experte',
                'concept_definition': 'Finanzielle Freiheit auf Experte-Niveau umfasst dynamische Entnahmestrategien (Guyton-Klinger, VPW), Sequenz-Risikoanalyse und Renten-Stresstests. Marktzusammenbrüche zu Rentenbeginn beeinflussen Entnahmeraten. Sicherheitsmarge, Flexibilität und adaptive Ausgabenstrategien reduzieren das Risiko.',
                'practical_example': 'Guyton-Klinger-Strategie: Entnahmerate = Vorherige Entnahme × (1 + (Portfoliorendite - Zielrendite) / Anpassungsfaktor). Wenn Portfoliorendite 8%, Ziel 4%, wird Entnahmerate erhöht. Sequenz-Risiko: Wenn Markt zu Rentenbeginn um 20% fällt, steigt Entnahmerate von 4% auf 5%.',
                'mathematical_formula': 'Dynamische Entnahme = Vorherige Entnahme × (1 + (Portfoliorendite - Ziel) / Anpassung)\nSequenz-Risiko = (1 - Entnahmerate) × Marktrückgang\nSicherheitsmarge = (Portfolio - Erforderlich) / Erforderlich',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Finanzielle Freiheit erfordert Flexibilität. Passen Sie Ihre Ausgaben an die Marktbedingungen an."'
            },
            'it': {
                'title': 'Libertà Finanziaria - Esperto',
                'concept_definition': 'La libertà finanziaria a livello esperto include strategie di prelievo dinamiche (Guyton-Klinger, VPW), l\'analisi del rischio di sequenza e gli stress test pensionistici. I crolli del mercato all\'inizio della pensione influenzano i tassi di prelievo. Il margine di sicurezza, la flessibilità e le strategie di spesa adattive riducono il rischio.',
                'practical_example': 'Strategia Guyton-Klinger: Tasso di prelievo = Prelievo Precedente × (1 + (Rendimento Portafoglio - Rendimento Obiettivo) / Fattore di Ajustamento). Se il rendimento del portafoglio è 8%, obiettivo 4%, il tasso di prelievo aumenta. Rischio di sequenza: Se il mercato crolla del 20% all\'inizio della pensione, il tasso di prelievo aumenta dal 4% al 5%.',
                'mathematical_formula': 'Prelievo Dinamico = Prelievo Precedente × (1 + (Rendimento Portafoglio - Obiettivo) / Ajustamento)\nRischio di Sequenza = (1 - Tasso di Prelievo) × Declino del Mercato\nMargine di Sicurezza = (Portafoglio - Richiesto) / Richiesto',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "La libertà finanziaria richiede flessibilità. Adatta le tue spese alle condizioni di mercato."'
            }
        },
        'investing': {
            'tr': {
                'title': 'Yatırım ve Yatırım Araçları - Uzman Seviye',
                'concept_definition': 'Uzman seviyede yatırım, piyasa volatilitesi metrikleri (VIX, realized volatility, implied volatility), risk yönetimi, psikolojik risk yönetimi ve kontraryan yatırım stratejilerini içerir. Piyasa çöküşlerinde panik satışından kaçınmak, başarılı yatırımın anahtarıdır. Tail risk hedging ve dinamik asset allocation uygulanır.',
                'practical_example': 'VIX 30 olduğunda piyasa volatil, VIX 15 olduğunda piyasa sakin. Implied volatility, gelecekteki volatiliteyi tahmin eder. Piyasa çöküşünde %20 düşüş olduğunda, panik satışı yerine alım fırsatı olarak görülür. Kontraryan yatırımcı, kalabalığın aksine hareket eder.',
                'mathematical_formula': 'Volatilite = Standart Sapma × √252 (yıllık)\nImplied Volatility = Black-Scholes ters çözümü\nTail Risk = VaR - CVaR',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Piyasa çöküşleri beklenmediktir. Hazırlıklı olun ve fırsatları kullanın."'
            },
            'en': {
                'title': 'Investing & Investment Vehicles - Expert',
                'concept_definition': 'Expert level investing includes market volatility metrics (VIX, realized volatility, implied volatility), risk management, psychological risk management, and contrarian investment strategies. Avoiding panic selling during market crashes is the key to successful investing. Tail risk hedging and dynamic asset allocation are applied.',
                'practical_example': 'When VIX is 30, market is volatile; when VIX is 15, market is calm. Implied volatility predicts future volatility. During market crash with 20% decline, instead of panic selling, it\'s seen as buying opportunity. Contrarian investor moves opposite to the crowd.',
                'mathematical_formula': 'Volatility = Standard Deviation × √252 (annualized)\nImplied Volatility = Black-Scholes inverse solution\nTail Risk = VaR - CVaR',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Market crashes are unexpected. Be prepared and use opportunities."'
            },
            'de': {
                'title': 'Investieren und Anlageinstrumente - Experte',
                'concept_definition': 'Investieren auf Experte-Niveau umfasst Marktvolatilitätsmetriken (VIX, realisierte Volatilität, implizite Volatilität), Risikomanagement, psychologisches Risikomanagement und konträre Investmentstrategien. Panikverkäufe während Marktzusammenbrüchen zu vermeiden, ist der Schlüssel zum erfolgreichen Investieren. Tail-Risk-Hedging und dynamische Asset Allocation werden angewendet.',
                'practical_example': 'Wenn VIX 30 ist, ist der Markt volatil; wenn VIX 15 ist, ist der Markt ruhig. Implizite Volatilität sagt zukünftige Volatilität voraus. Während eines Marktzusammenbruchs mit 20% Rückgang wird dies statt Panikverkauf als Kaufgelegenheit gesehen. Konträre Investor bewegen sich entgegengesetzt zur Menge.',
                'mathematical_formula': 'Volatilität = Standardabweichung × √252 (jährlich)\nImplizite Volatilität = Black-Scholes inverse Lösung\nTail Risk = VaR - CVaR',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Marktzusammenbrüche sind unerwartet. Seien Sie vorbereitet und nutzen Sie Gelegenheiten."'
            },
            'it': {
                'title': 'Investire e Strumenti di Investimento - Esperto',
                'concept_definition': 'L\'investimento a livello esperto include metriche di volatilità del mercato (VIX, volatilità realizzata, volatilità implicita), gestione del rischio, gestione del rischio psicologico e strategie di investimento contrarian. Evitare le vendite di panico durante i crolli del mercato è la chiave per investire con successo. Vengono applicati il tail risk hedging e l\'allocazione dinamica delle attività.',
                'practical_example': 'Quando VIX è 30, il mercato è volatile; quando VIX è 15, il mercato è calmo. La volatilità implicita prevede la volatilità futura. Durante un crollo del mercato con un declino del 20%, invece di vendite di panico, questo è visto come opportunità di acquisto. L\'investitore contrarian si muove opposto alla folla.',
                'mathematical_formula': 'Volatilità = Deviazione Standard × √252 (annualizzata)\nVolatilità Implicita = Soluzione inversa Black-Scholes\nTail Risk = VaR - CVaR',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I crolli del mercato sono inaspettati. Sii preparato e usa le opportunità."'
            }
        },
        'risk_management': {
            'tr': {
                'title': 'Risk Yönetimi - Uzman Seviye',
                'concept_definition': 'Uzman seviyede risk yönetimi, Value at Risk (VaR), Conditional VaR, stres testleri, senaryo analizleri ve tail risk yönetimini içerir. Risk bütçeleme, risk limitleri, risk takibi ve dinamik risk yönetimi profesyonel risk yönetiminin temelidir. Expected Shortfall, Maximum Drawdown ve skewness/kurtosis analiz edilir.',
                'practical_example': 'Portföy değeri 1.000.000 TL. %95 güven seviyesinde VaR = 50.000 TL. Bu, %5 ihtimalle portföyün 50.000 TL veya daha fazla kaybedeceği anlamına gelir. CVaR (Expected Shortfall) = 75.000 TL. Bu, en kötü %5 durumda ortalama kaybı gösterir. Skewness = -0.5 (negatif tail risk).',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nSkewness = E[(X-μ)³] / σ³\nKurtosis = E[(X-μ)⁴] / σ⁴',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Risk, standart sapma değildir. Risk, beklenmedik olayların potansiyel etkisidir."'
            },
            'en': {
                'title': 'Risk Management - Expert',
                'concept_definition': 'Expert level risk management includes Value at Risk (VaR), Conditional VaR, stress tests, scenario analysis, and tail risk management. Risk budgeting, risk limits, risk monitoring, and dynamic risk management are fundamental to professional risk management. Expected Shortfall, Maximum Drawdown, and skewness/kurtosis are analyzed.',
                'practical_example': 'Portfolio value is 1,000,000 TL. VaR at 95% confidence = 50,000 TL. This means there is a 5% chance the portfolio will lose 50,000 TL or more. CVaR (Expected Shortfall) = 75,000 TL. This shows the average loss in the worst 5% of cases. Skewness = -0.5 (negative tail risk).',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nSkewness = E[(X-μ)³] / σ³\nKurtosis = E[(X-μ)⁴] / σ⁴',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Risk is not standard deviation. Risk is the potential impact of unexpected events."'
            },
            'de': {
                'title': 'Risikomanagement - Experte',
                'concept_definition': 'Risikomanagement auf Experte-Niveau umfasst Value at Risk (VaR), Conditional VaR, Stresstests, Szenarioanalysen und Tail-Risk-Management. Risk Budgeting, Risikolimits, Risikoüberwachung und dynamisches Risikomanagement sind grundlegend für professionelles Risikomanagement. Expected Shortfall, Maximum Drawdown und Skewness/Kurtosis werden analysiert.',
                'practical_example': 'Portfoliowert ist 1.000.000 TL. VaR bei 95% Konfidenz = 50.000 TL. Dies bedeutet, dass es eine 5% Chance gibt, dass das Portfolio 50.000 TL oder mehr verliert. CVaR (Expected Shortfall) = 75.000 TL. Dies zeigt den durchschnittlichen Verlust in den schlechtesten 5% der Fälle. Skewness = -0,5 (negativer Tail-Risk).',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nSkewness = E[(X-μ)³] / σ³\nKurtosis = E[(X-μ)⁴] / σ⁴',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Risiko ist keine Standardabweichung. Risiko ist die potenzielle Auswirkung unerwarteter Ereignisse."'
            },
            'it': {
                'title': 'Gestione del Rischio - Esperto',
                'concept_definition': 'La gestione del rischio a livello esperto include Value at Risk (VaR), Conditional VaR, test di stress, analisi degli scenari e la gestione del tail risk. Il risk budgeting, i limiti di rischio, il monitoraggio del rischio e la gestione dinamica del rischio sono fondamentali per la gestione del rischio professionale. Expected Shortfall, Maximum Drawdown e skewness/kurtosis vengono analizzati.',
                'practical_example': 'Il valore del portafoglio è 1.000.000 TL. VaR al 95% di confidenza = 50.000 TL. Questo significa che c\'è una probabilità del 5% che il portafoglio perda 50.000 TL o più. CVaR (Expected Shortfall) = 75.000 TL. Questo mostra la perdita media nel peggiore 5% dei casi. Skewness = -0.5 (tail risk negativo).',
                'mathematical_formula': 'VaR = μ - z × σ\nCVaR = E[Loss | Loss ≥ VaR]\nSkewness = E[(X-μ)³] / σ³\nKurtosis = E[(X-μ)⁴] / σ⁴',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il rischio non è la deviazione standard. Il rischio è l\'impatto potenziale di eventi imprevisti."'
            }
        },
        'portfolio_optimization': {
            'tr': {
                'title': 'Portföy Optimizasyonu - Uzman Seviye',
                'concept_definition': 'Uzman seviyede portföy optimizasyonu, Modern Portföy Teorisi (MPT), Etkili Sınır (Efficient Frontier), CAPM, faktör modelleri (Fama-French, Carhart) ve Black-Litterman modelini içerir. Kararlı optimizasyon, kısıtlı optimizasyon, dinamik asset allocation ve tactical asset allocation kullanılır.',
                'practical_example': '3 varlık: Hisse (β=1.2, σ=20%), Tahvil (β=0.3, σ=5%), Altın (β=0.5, σ=15%). Black-Litterman modeli ile prior view\'lar entegre edilir. Etkili sınır üzerinde optimal portföy: %40 hisse, %40 tahvil, %20 altın. Bu portföy Sharpe oranı maksimize eder.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)\nBlack-Litterman: μ = [(τΣ)^(-1) + P\'Ω(-1)P]^(-1) × [(τΣ)^(-1)π + P\'Ω(-1)Q]',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Akıllı Yatırımcı" kitabında Benjamin Graham şunu söylüyor: "Diversifikasyon, riski azaltmanın en iyi yoludur. Ancak aşırı diversifikasyon, getiriyi de azaltır."'
            },
            'en': {
                'title': 'Portfolio Optimization - Expert',
                'concept_definition': 'Expert level portfolio optimization includes Modern Portfolio Theory (MPT), Efficient Frontier, CAPM, factor models (Fama-French, Carhart), and Black-Litterman model. Robust optimization, constrained optimization, dynamic asset allocation, and tactical asset allocation are used.',
                'practical_example': '3 assets: Stocks (β=1.2, σ=20%), Bonds (β=0.3, σ=5%), Gold (β=0.5, σ=15%). Black-Litterman model integrates prior views. Optimal portfolio on efficient frontier: 40% stocks, 40% bonds, 20% gold. This portfolio maximizes Sharpe ratio.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)\nBlack-Litterman: μ = [(τΣ)^(-1) + P\'Ω(-1)P]^(-1) × [(τΣ)^(-1)π + P\'Ω(-1)Q]',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Intelligent Investor", Benjamin Graham says: "Diversification is the best way to reduce risk. However, excessive diversification also reduces returns."'
            },
            'de': {
                'title': 'Portfolio-Optimierung - Experte',
                'concept_definition': 'Portfolio-Optimierung auf Experte-Niveau umfasst Moderne Portfolio-Theorie (MPT), Effiziente Grenze, CAPM, Faktormodelle (Fama-French, Carhart) und Black-Litterman-Modell. Robuste Optimierung, eingeschränkte Optimierung, dynamische Asset Allocation und taktische Asset Allocation werden verwendet.',
                'practical_example': '3 Vermögenswerte: Aktien (β=1.2, σ=20%), Anleihen (β=0.3, σ=5%), Gold (β=0.5, σ=15%). Black-Litterman-Modell integriert Prior-Views. Optimales Portfolio auf effizienter Grenze: 40% Aktien, 40% Anleihen, 20% Gold. Dieses Portfolio maximiert die Sharpe Ratio.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)\nBlack-Litterman: μ = [(τΣ)^(-1) + P\'Ω(-1)P]^(-1) × [(τΣ)^(-1)π + P\'Ω(-1)Q]',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Intelligente Investor" sagt Benjamin Graham: "Diversifizierung ist der beste Weg, das Risiko zu reduzieren. Übermäßige Diversifizierung reduziert jedoch auch die Rendite."'
            },
            'it': {
                'title': 'Ottimizzazione del Portafoglio - Esperto',
                'concept_definition': 'L\'ottimizzazione del portafoglio a livello esperto include la Teoria del Portafoglio Moderno (MPT), la Frontiera Efficiente, CAPM, i modelli fattoriali (Fama-French, Carhart) e il modello Black-Litterman. Vengono utilizzati l\'ottimizzazione robusta, l\'ottimizzazione vincolata, l\'allocazione dinamica delle attività e l\'allocazione tattica delle attività.',
                'practical_example': '3 attività: Azioni (β=1.2, σ=20%), Obbligazioni (β=0.3, σ=5%), Oro (β=0.5, σ=15%). Il modello Black-Litterman integra le prior view. Portafoglio ottimale sulla frontiera efficiente: 40% azioni, 40% obbligazioni, 20% oro. Questo portafoglio massimizza il Sharpe ratio.',
                'mathematical_formula': 'E(Rp) = Σ(wi × E(Ri))\nσp² = ΣΣ(wi × wj × σi × σj × ρij)\nBlack-Litterman: μ = [(τΣ)^(-1) + P\'Ω(-1)P]^(-1) × [(τΣ)^(-1)π + P\'Ω(-1)Q]',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "L\'Investitore Intelligente", Benjamin Graham dice: "La diversificazione è il modo migliore per ridurre il rischio. Tuttavia, una diversificazione eccessiva riduce anche i rendimenti."'
            }
        },
        'behavioral_finance': {
            'tr': {
                'title': 'Davranışsal Finans - Uzman Seviye',
                'concept_definition': 'Uzman seviyede davranışsal finans, bilişsel önyargılar (bias), duygusal faktörler, psikolojik etkiler ve nörofinansı içerir. Kayıp aversionı, aşırı güven, sürü etkisi, mental accounting, anchoring, availability heuristic, confirmation bias ve disposition effect analiz edilir. Nudge theory ve behavioral design uygulanır.',
                'practical_example': 'Kayıp aversionı: 100 TL kaybetmenin acısı, 100 TL kazanmanın sevincinden 2 kat daha fazladır. Bu yüzden yatırımcılar kaybeden pozisyonları çok uzun tutarlar (disposition effect). Prospect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0). λ ≈ 2.25.',
                'mathematical_formula': 'Kayıp Aversion Oranı = (Kazanç Değeri / Kayıp Değeri) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)\nBehavioral Alpha = (Gerçek Getiri - Beklenen Getiri)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "Finansal kararlarınızın %90\'ı psikolojiktir, teknik değildir."'
            },
            'en': {
                'title': 'Behavioral Finance - Expert',
                'concept_definition': 'Expert level behavioral finance includes cognitive biases, emotional factors, psychological effects, and neurofinance. Loss aversion, overconfidence, herd behavior, mental accounting, anchoring, availability heuristic, confirmation bias, and disposition effect are analyzed. Nudge theory and behavioral design are applied.',
                'practical_example': 'Loss aversion: The pain of losing 100 TL is twice the pleasure of gaining 100 TL. Therefore, investors hold losing positions too long (disposition effect). Prospect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0). λ ≈ 2.25.',
                'mathematical_formula': 'Loss Aversion Ratio = (Gain Value / Loss Value) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)\nBehavioral Alpha = (Actual Return - Expected Return)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "90% of your financial decisions are psychological, not technical."'
            },
            'de': {
                'title': 'Verhaltensfinanz - Experte',
                'concept_definition': 'Verhaltensfinanz auf Experte-Niveau umfasst kognitive Verzerrungen, emotionale Faktoren, psychologische Effekte und Neurofinanz. Verlustaversion, Überkonfidenz, Herdenverhalten, Mental Accounting, Anchoring, Availability Heuristic, Confirmation Bias und Dispositionseffekt werden analysiert. Nudge-Theory und Behavioral Design werden angewendet.',
                'practical_example': 'Verlustaversion: Der Schmerz, 100 TL zu verlieren, ist doppelt so groß wie die Freude, 100 TL zu gewinnen. Daher halten Investoren verlustbringende Positionen zu lange (Dispositionseffekt). Prospect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0). λ ≈ 2,25.',
                'mathematical_formula': 'Verlustaversion Ratio = (Gewinnwert / Verlustwert) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)\nBehavioral Alpha = (Tatsächliche Rendite - Erwartete Rendite)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "90% Ihrer finanziellen Entscheidungen sind psychologisch, nicht technisch."'
            },
            'it': {
                'title': 'Finanza Comportamentale - Esperto',
                'concept_definition': 'La finanza comportamentale a livello esperto include bias cognitivi, fattori emotivi, effetti psicologici e neurofinanza. L\'avversione alla perdita, l\'eccessiva fiducia, il comportamento di gregge, il mental accounting, l\'ancoraggio, l\'availability heuristic, il confirmation bias e l\'effetto disposizione vengono analizzati. La nudge theory e il behavioral design vengono applicati.',
                'practical_example': 'Avversione alla perdita: Il dolore di perdere 100 TL è doppio rispetto al piacere di guadagnare 100 TL. Pertanto, gli investitori mantengono posizioni in perdita troppo a lungo (effetto disposizione). Prospect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0). λ ≈ 2.25.',
                'mathematical_formula': 'Avversione alla Perdita Ratio = (Valore Guadagno / Valore Perdita) < 1\nProspect Theory: U(x) = x^α (x ≥ 0), U(x) = -λ(-x)^α (x < 0)\nBehavioral Alpha = (Rendimento Attuale - Rendimento Atteso)',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "Il 90% delle tue decisioni finanziarie è psicologico, non tecnico."'
            }
        },
        'tax_planning': {
            'tr': {
                'title': 'Vergi Planlaması - Uzman Seviye',
                'concept_definition': 'Uzman seviyede vergi planlaması, vergi avantajlı hesaplar (BES, 401k, IRA, Roth IRA), vergi tasarruf stratejileri, sermaye kazancı vergisi, temettü vergisi, vergi arbitrajı ve uluslararası vergi planlamasını içerir. Tax-loss harvesting, asset location ve tax-efficient investing analiz edilir.',
                'practical_example': 'BES hesabına yıllık 50.000 TL yatırırsanız, %15 vergi indirimi alırsınız. Bu, 7.500 TL vergi tasarrufu demektir. Sermaye kazancı vergisi %20 ise, tax-loss harvesting ile vergi ertelenebilir. Asset location: Yüksek getiri varlıkları vergi avantajlı hesaplarda, düşük getiri varlıkları vergisiz hesaplarda tutulur.',
                'mathematical_formula': 'Vergi Tasarrufu = Yatırım × Vergi Oranı\nVergi Arbitrajı = Vergi Farkı × Pozisyon\nAsset Location = Σ(Varlık Getiri × Vergi Oranı)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Zengin Baba, Yoksul Baba" kitabında Robert Kiyosaki şunu söylüyor: "Vergi planlaması, zenginlerin sırrıdır."'
            },
            'en': {
                'title': 'Tax Planning - Expert',
                'concept_definition': 'Expert level tax planning includes tax-advantaged accounts (BES, 401k, IRA, Roth IRA), tax saving strategies, capital gains tax, dividend tax, tax arbitrage, and international tax planning. Tax-loss harvesting, asset location, and tax-efficient investing are analyzed.',
                'practical_example': 'If you invest 50,000 TL annually in a BES account, you get a 15% tax deduction. This means 7,500 TL tax savings. If capital gains tax is 20%, tax-loss harvesting can defer tax. Asset location: High-return assets in tax-advantaged accounts, low-return assets in taxable accounts.',
                'mathematical_formula': 'Tax Savings = Investment × Tax Rate\nTax Arbitrage = Tax Difference × Position\nAsset Location = Σ(Asset Return × Tax Rate)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Rich Dad Poor Dad", Robert Kiyosaki says: "Tax planning is the secret of the rich."'
            },
            'de': {
                'title': 'Steuerplanung - Experte',
                'concept_definition': 'Steuerplanung auf Experte-Niveau umfasst steuerbegünstigte Konten (BES, 401k, IRA, Roth IRA), Steuereinsparungsstrategien, Kapitalertragsteuer, Dividendensteuer, Steuerarbitrage und internationale Steuerplanung. Tax-Loss Harvesting, Asset Location und tax-efficient Investing werden analysiert.',
                'practical_example': 'Wenn Sie jährlich 50.000 TL in ein BES-Konto investieren, erhalten Sie eine 15% Steuerabzug. Dies bedeutet 7.500 TL Steuereinsparung. Wenn Kapitalertragsteuer 20% ist, kann Tax-Loss Harvesting die Steuer aufschieben. Asset Location: Hochrendite-Vermögenswerte in steuerbegünstigten Konten, Niedrigrendite-Vermögenswerte in steuerpflichtigen Konten.',
                'mathematical_formula': 'Steuereinsparung = Investition × Steuersatz\nSteuerarbitrage = Steuerdifferenz × Position\nAsset Location = Σ(Anlagerendite × Steuersatz)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Reicher Vater, armer Vater" sagt Robert Kiyosaki: "Steuerplanung ist das Geheimnis der Reichen."'
            },
            'it': {
                'title': 'Pianificazione Fiscale - Esperto',
                'concept_definition': 'La pianificazione fiscale a livello esperto include conti con vantaggi fiscali (BES, 401k, IRA, Roth IRA), strategie di risparmio fiscale, tassa sui guadagni in capitale, tassa sui dividendi, arbitraggio fiscale e pianificazione fiscale internazionale. Il tax-loss harvesting, l\'asset location e il tax-efficient investing vengono analizzati.',
                'practical_example': 'Se investi 50.000 TL all\'anno in un conto BES, ottieni una detrazione fiscale del 15%. Questo significa 7.500 TL di risparmio fiscale. Se la tassa sui guadagni in capitale è del 20%, il tax-loss harvesting può differire la tassa. Asset location: attività ad alto rendimento in conti con vantaggi fiscali, attività a basso rendimento in conti tassabili.',
                'mathematical_formula': 'Risparmio Fiscale = Investimento × Aliquota Fiscale\nArbitraggio Fiscale = Differenza Fiscale × Posizione\nAsset Location = Σ(Rendimento Attività × Aliquota Fiscale)',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Padre Ricco, Padre Povero", Robert Kiyosaki dice: "La pianificazione fiscale è il segreto dei ricchi."'
            }
        },
        'retirement_planning': {
            'tr': {
                'title': 'Emeklilik Planlaması - Uzman Seviye',
                'concept_definition': 'Uzman seviyede emeklilik planlaması, emeklilik yaşı hesaplaması, sosyal güvenlik optimizasyonu, emeklilik gelir kaynakları, 4% kuralının dinamik versiyonları ve emeklilik stres testlerini içerir. Longevity risk, healthcare cost inflation ve sequence of returns risk analiz edilir.',
                'practical_example': 'Emeklilik yaşı 65, yaşam beklentisi 90. 25 yıl emeklilik. Yıllık harcama 200.000 TL. %3 çekim oranıyla gerekli birikim = 200.000 / 0.03 = 6.666.667 TL. %5 çekim oranıyla = 4.000.000 TL. Healthcare cost inflation %5 ise, healthcare bütçesi %10 olmalıdır.',
                'mathematical_formula': 'Emeklilik Birikimi = Yıllık Harcama × (1 - (1 + r)^(-n)) / r\nDinamik Çekim = Önceki Çekim × (1 + Enflasyon - Getiri)\nLongevity Risk = P(T > Emeklilik Yaşı)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': '"Your Money or Your Life" kitabında Vicki Robin şunu söylüyor: "Emeklilik, işten ayrılmak değil, finansal özgürlüktür."'
            },
            'en': {
                'title': 'Retirement Planning - Expert',
                'concept_definition': 'Expert level retirement planning includes retirement age calculation, social security optimization, retirement income sources, dynamic versions of the 4% rule, and retirement stress tests. Longevity risk, healthcare cost inflation, and sequence of returns risk are analyzed.',
                'practical_example': 'Retirement age 65, life expectancy 90. 25 years of retirement. Annual expense 200,000 TL. With 3% withdrawal rate, required savings = 200,000 / 0.03 = 6,666,667 TL. With 5% withdrawal rate = 4,000,000 TL. If healthcare cost inflation is 5%, healthcare budget should be 10%.',
                'mathematical_formula': 'Retirement Savings = Annual Expense × (1 - (1 + r)^(-n)) / r\nDynamic Withdrawal = Previous Withdrawal × (1 + Inflation - Return)\nLongevity Risk = P(T > Retirement Age)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Your Money or Your Life", Vicki Robin says: "Retirement is not quitting work, it\'s financial freedom."'
            },
            'de': {
                'title': 'Rentenplanung - Experte',
                'concept_definition': 'Rentenplanung auf Experte-Niveau umfasst Rentenalterberechnung, Sozialversicherungs-Optimierung, Renteneinkommensquellen, dynamische Versionen der 4%-Regel und Renten-Stresstests. Longevity-Risk, Healthcare-Cost-Inflation und Sequenz-Risiko werden analysiert.',
                'practical_example': 'Rentenalter 65, Lebenserwartung 90. 25 Jahre Rente. Jährliche Ausgabe 200.000 TL. Mit 3% Entnahmerate, erforderliche Ersparnisse = 200.000 / 0,03 = 6.666.667 TL. Mit 5% Entnahmerate = 4.000.000 TL. Wenn Healthcare-Cost-Inflation 5%, sollte Healthcare-Budget 10% sein.',
                'mathematical_formula': 'Rentenersparnisse = Jährliche Ausgabe × (1 - (1 + r)^(-n)) / r\nDynamische Entnahme = Vorherige Entnahme × (1 + Inflation - Rendite)\nLongevity Risk = P(T > Rentenalter)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Ihr Geld oder Ihr Leben" sagt Vicki Robin: "Rente ist nicht die Arbeit aufzugeben, sondern finanzielle Freiheit."'
            },
            'it': {
                'title': 'Pianificazione della Pensione - Esperto',
                'concept_definition': 'La pianificazione della pensione a livello esperto include il calcolo dell\'età pensionabile, l\'ottimizzazione della sicurezza sociale, le fonti di reddito pensionistico, versioni dinamiche della regola del 4% e gli stress test pensionistici. Il rischio di longevità, l\'inflazione dei costi sanitari e il rischio di sequenza vengono analizzati.',
                'practical_example': 'Età pensionabile 65, aspettativa di vita 90. 25 anni di pensione. Spesa annuale 200.000 TL. Con tasso di prelievo del 3%, risparmio richiesto = 200.000 / 0,03 = 6.666.667 TL. Con tasso del 5% = 4.000.000 TL. Se l\'inflazione dei costi sanitari è del 5%, il budget sanitario dovrebbe essere del 10%.',
                'mathematical_formula': 'Risparmio Pensionistico = Spesa Annuale × (1 - (1 + r)^(-n)) / r\nPrelievo Dinamico = Prelievo Precedente × (1 + Inflazione - Rendimento)\nLongevity Risk = P(T > Età Pensionabile)',
                'python_function': 'calculate_financial_independence_number(annual_expenses, withdrawal_rate)',
                'literary_insights': 'In "Il Tuo Denaro o la Tua Vita", Vicki Robin dice: "La pensione non è smettere di lavorare, è libertà finanziaria."'
            }
        },
        'international_investing': {
            'tr': {
                'title': 'Uluslararası Yatırım - Uzman Seviye',
                'concept_definition': 'Uzman seviyede uluslararası yatırım, döviz riski, ülke riski, küresel diversifikasyon, gelişmekte olan piyasalar ve uluslararası vergi planlamasını içerir. ETF ve ADR ile uluslararası yatırımlar yapılır. Döviz hedge, country beta ve global tactical asset allocation uygulanır.',
                'practical_example': 'Portföy: %60 ABD (S&P 500), %20 Avrupa (STOXX 600), %10 Asya (MSCI Asia), %10 Gelişmekte Olan (MSCI EM). Döviz riski: USD/TL volatilitesi %15. Döviz hedge ile risk azaltılır. Country beta: Türkiye beta = 1.8, ABD beta = 1.0.',
                'mathematical_formula': 'Döviz Riski = Fark × Pozisyon\nReel Getiri = (1 + Nominal) × (1 + Döviz) - 1\nCountry Beta = Cov(Ri, Rm) / Var(Rm)',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Küresel diversifikasyon, ülke riskini azaltmanın en iyi yoludur."'
            },
            'en': {
                'title': 'International Investing - Expert',
                'concept_definition': 'Expert level international investing includes currency risk, country risk, global diversification, emerging markets, and international tax planning. International investments are made through ETFs and ADRs. Currency hedging, country beta, and global tactical asset allocation are applied.',
                'practical_example': 'Portfolio: 60% US (S&P 500), 20% Europe (STOXX 600), 10% Asia (MSCI Asia), 10% Emerging (MSCI EM). Currency risk: USD/TL volatility 15%. Currency hedges reduce risk. Country beta: Turkey beta = 1.8, US beta = 1.0.',
                'mathematical_formula': 'Currency Risk = Change × Position\nReal Return = (1 + Nominal) × (1 + Currency) - 1\nCountry Beta = Cov(Ri, Rm) / Var(Rm)',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Global diversification is the best way to reduce country risk."'
            },
            'de': {
                'title': 'Internationales Investieren - Experte',
                'concept_definition': 'Internationales Investieren auf Experte-Niveau umfasst Währungsrisiko, Länderrisiko, globale Diversifizierung, Schwellenländer und internationale Steuerplanung. Internationale Investitionen werden über ETFs und ADRs getätigt. Währungshedges, Country Beta und globale taktische Asset Allocation werden angewendet.',
                'practical_example': 'Portfolio: 60% US (S&P 500), 20% Europa (STOXX 600), 10% Asien (MSCI Asia), 10% Schwellenländer (MSCI EM). Währungsrisiko: USD/TL Volatilität 15%. Währungshedges reduzieren Risiko. Country Beta: Türkei Beta = 1,8, US Beta = 1,0.',
                'mathematical_formula': 'Währungsrisiko = Änderung × Position\nReale Rendite = (1 + Nominal) × (1 + Währung) - 1\nCountry Beta = Cov(Ri, Rm) / Var(Rm)',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Globale Diversifizierung ist der beste Weg, um Länderrisiko zu reduzieren."'
            },
            'it': {
                'title': 'Investimento Internazionale - Esperto',
                'concept_definition': 'L\'investimento internazionale a livello esperto include il rischio valutario, il rischio paese, la diversificazione globale, i mercati emergenti e la pianificazione fiscale internazionale. Gli investimenti internazionali vengono effettuati tramite ETF e ADR. Vengono applicati l\'hedge valutario, il country beta e l\'allocazione tattica globale delle attività.',
                'practical_example': 'Portafoglio: 60% USA (S&P 500), 20% Europa (STOXX 600), 10% Asia (MSCI Asia), 10% Emergenti (MSCI EM). Rischio valutario: volatilità USD/TL 15%. Le coperture valutarie riducono il rischio. Country beta: Turchia beta = 1.8, USA beta = 1.0.',
                'mathematical_formula': 'Rischio Valutario = Variazione × Posizione\nRendimento Reale = (1 + Nominale) × (1 + Valuta) - 1\nCountry Beta = Cov(Ri, Rm) / Var(Rm)',
                'python_function': 'calculate_inflation_adjusted_return(nominal_return, inflation_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La diversificazione globale è il modo migliore per ridurre il rischio paese."'
            }
        },
        'derivatives': {
            'tr': {
                'title': 'Türev Araçlar - Uzman Seviye',
                'concept_definition': 'Uzman seviyede türev araçlar, opsiyonlar, futures, swaps, forward contracts ve exotics türevlerini içerir. Delta, gamma, theta, vega, rho Greeks hesaplanır. Black-Scholes-Merton modeli, binomial trees ve Monte Carlo simülasyonları kullanılır. Hedging stratejileri ve arbitraj uygulanır.',
                'practical_example': 'Call opsiyonu: Strike fiyatı 100 TL, prim 5 TL. Hisse fiyatı 110 TL olursa, iç değer = 10 TL, zaman değeri = 0 TL. Kâr = 10 - 5 = 5 TL. Delta = 0.5, gamma = 0.1, theta = -0.05, vega = 0.2. Delta hedging ile risk nötral portföy oluşturulur.',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rt) × N(d2)\nGreeks: Δ = N(d1), Γ = N\'(d1) / (Sσ√t), Θ = -SN\'(d1)σ/(2√t) - rKe^(-rt)N(d2)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Türev araçlar, güçlü ama tehlikeli araçlardır."'
            },
            'en': {
                'title': 'Derivatives - Expert',
                'concept_definition': 'Expert level derivatives includes options, futures, swaps, forward contracts, and exotic derivatives. Delta, gamma, theta, vega, rho Greeks are calculated. Black-Scholes-Merton models, binomial trees, and Monte Carlo simulations are used. Hedging strategies and arbitrage are applied.',
                'practical_example': 'Call option: Strike price 100 TL, premium 5 TL. If stock price becomes 110 TL, intrinsic value = 10 TL, time value = 0 TL. Profit = 10 - 5 = 5 TL. Delta = 0.5, gamma = 0.1, theta = -0.05, vega = 0.2. Delta hedging creates risk-neutral portfolio.',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rt) × N(d2)\nGreeks: Δ = N(d1), Γ = N\'(d1) / (Sσ√t), Θ = -SN\'(d1)σ/(2√t) - rKe^(-rt)N(d2)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Derivatives are powerful but dangerous instruments."'
            },
            'de': {
                'title': 'Derivate - Experte',
                'concept_definition': 'Derivate auf Experte-Niveau umfassen Optionen, Futures, Swaps, Forward-Verträge und exotische Derivate. Delta, Gamma, Theta, Vega, Rho Greeks werden berechnet. Black-Scholes-Merton-Modelle, Binomial-Bäume und Monte-Carlo-Simulationen werden verwendet. Hedging-Strategien und Arbitrage werden angewendet.',
                'practical_example': 'Call-Option: Strike-Preis 100 TL, Prämie 5 TL. Wenn Aktienpreis 110 TL wird, innerer Wert = 10 TL, Zeitwert = 0 TL. Gewinn = 10 - 5 = 5 TL. Delta = 0,5, Gamma = 0,1, Theta = -0,05, Vega = 0,2. Delta-Hedging erstellt risikoneutrales Portfolio.',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rt) × N(d2)\nGreeks: Δ = N(d1), Γ = N\'(d1) / (Sσ√t), Θ = -SN\'(d1)σ/(2√t) - rKe^(-rt)N(d2)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Derivate sind mächtige aber gefährliche Instrumente."'
            },
            'it': {
                'title': 'Derivati - Esperto',
                'concept_definition': 'I derivati a livello esperto includono opzioni, futures, swap, contratti forward e derivati esotici. I Greci Delta, Gamma, Theta, Vega, Rho vengono calcolati. I modelli Black-Scholes-Merton, gli alberi binomiali e le simulazioni Monte Carlo vengono utilizzati. Le strategie di hedging e l\'arbitraggio vengono applicati.',
                'practical_example': 'Opzione Call: prezzo di esercizio 100 TL, premio 5 TL. Se il prezzo dell\'azione diventa 110 TL, valore intrinseco = 10 TL, valore temporale = 0 TL. Profitto = 10 - 5 = 5 TL. Delta = 0.5, gamma = 0.1, theta = -0.05, vega = 0.2. Il delta hedging crea un portafoglio neutro al rischio.',
                'mathematical_formula': 'Black-Scholes: C = S × N(d1) - K × e^(-rt) × N(d2)\nGreeks: Δ = N(d1), Γ = N\'(d1) / (Sσ√t), Θ = -SN\'(d1)σ/(2√t) - rKe^(-rt)N(d2)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I derivati sono strumenti potenti ma pericolosi."'
            }
        },
        'alternative_investments': {
            'tr': {
                'title': 'Alternatif Yatırımlar - Uzman Seviye',
                'concept_definition': 'Uzman seviyede alternatif yatırımlar, gayrimenkul REIT\'ler, emtia, özel sermaye (private equity), hedge fonları, sanat, koleksiyonlar, infrastructure ve venture capital\'i içerir. Geleneksel varlıklarla korelasyon analizi, illikidity premium ve J-curve efekti analiz edilir.',
                'practical_example': 'Portföy: %70 hisse, %20 tahvil, %10 gayrimenkul REIT. Gayrimenkul REIT, hisselerle korelasyonu %60 olan bir varlıktır. Private equity J-curve: İlk 3 yıl negatif getiri, 4-10 yıl pozitif getiri. Illikidity premium = %3-5.',
                'mathematical_formula': 'Alternatif Portföy = Σ(Alternatif Ağırlık × Alternatif Getiri)\nKorelasyon = Cov(X, Y) / (σX × σY)\nIllikidity Premium = (Alternatif Getiri - Geleneksel Getiri)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Alternatif yatırımlar, portföy çeşitlendirmesini artırır."'
            },
            'en': {
                'title': 'Alternative Investments - Expert',
                'concept_definition': 'Expert level alternative investments includes real estate REITs, commodities, private equity, hedge funds, art, collectibles, infrastructure, and venture capital. Correlation analysis with traditional assets, illiquidity premium, and J-curve effect are analyzed.',
                'practical_example': 'Portfolio: 70% stocks, 20% bonds, 10% real estate REIT. Real estate REIT is an asset with 60% correlation with stocks. Private equity J-curve: Negative returns in first 3 years, positive returns in years 4-10. Illiquidity premium = 3-5%.',
                'mathematical_formula': 'Alternative Portfolio = Σ(Alternative Weight × Alternative Return)\nCorrelation = Cov(X, Y) / (σX × σY)\nIlliquidity Premium = (Alternative Return - Traditional Return)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Alternative investments increase portfolio diversification."'
            },
            'de': {
                'title': 'Alternative Investitionen - Experte',
                'concept_definition': 'Alternative Investitionen auf Experte-Niveau umfassen Immobilien-REITs, Rohstoffe, Private Equity, Hedgefonds, Kunst, Sammlerstücke, Infrastruktur und Venture Capital. Korrelationsanalyse mit traditionellen Vermögenswerten, Illiquidity Premium und J-Curve-Effekt werden analysiert.',
                'practical_example': 'Portfolio: 70% Aktien, 20% Anleihen, 10% Immobilien-REIT. Immobilien-REIT ist ein Vermögenswert mit 60% Korrelation mit Aktien. Private Equity J-Curve: Negative Renditen in ersten 3 Jahren, positive Renditen in Jahren 4-10. Illiquidity Premium = 3-5%.',
                'mathematical_formula': 'Alternatives Portfolio = Σ(Alternatives Gewicht × Alternative Rendite)\nKorrelation = Cov(X, Y) / (σX × σY)\nIlliquidity Premium = (Alternative Rendite - Traditionelle Rendite)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Alternative Investitionen erhöhen die Portfolio-Diversifizierung."'
            },
            'it': {
                'title': 'Investimenti Alternativi - Esperto',
                'concept_definition': 'Gli investimenti alternativi a livello esperto includono REIT immobiliari, materie prime, private equity, hedge fund, arte, collezionabili, infrastrutture e venture capital. Viene eseguita l\'analisi della correlazione con le attività tradizionali, l\'illiquidity premium e l\'effetto J-curve.',
                'practical_example': 'Portafoglio: 70% azioni, 20% obbligazioni, 10% REIT immobiliari. REIT immobiliare è un\'attività con correlazione del 60% con le azioni. J-curve del private equity: rendimenti negativi nei primi 3 anni, rendimenti positivi negli anni 4-10. Illiquidity premium = 3-5%.',
                'mathematical_formula': 'Portafoglio Alternativo = Σ(Peso Alternativo × Rendimento Alternativo)\nCorrelazione = Cov(X, Y) / (σX × σY)\nIlliquidity Premium = (Rendimento Alternativo - Rendimento Tradizionale)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Gli investimenti alternativi aumentano la diversificazione del portafoglio."'
            }
        },
        'quantitative_finance': {
            'tr': {
                'title': 'Kuantitatif Finans - Uzman Seviye',
                'concept_definition': 'Uzman seviyede kuantitatif finans, Monte Carlo simülasyonları, stokastik süreçler, Ito Lemma, Black-Scholes-Merton modeli, Greeks hesaplamaları ve stokastik diferansiyel denklemleri içerir. Geometric Brownian Motion, Ornstein-Uhlenbeck ve jump-diffusion süreçleri kullanılır.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Hisse fiyatı 100 TL, μ = 0.10, σ = 0.20, dt = 1/252. 10.000 Monte Carlo simülasyonu çalıştırılır. %95 güven aralığı hesaplanır. Black-Scholes: Call opsiyon fiyatı hesaplanır.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Kuantitatif modeller, riski anlamak için önemlidir. Model limitlerini bilmek kritiktir."'
            },
            'en': {
                'title': 'Quantitative Finance - Expert',
                'concept_definition': 'Expert level quantitative finance includes Monte Carlo simulations, stochastic processes, Ito Lemma, Black-Scholes-Merton models, Greeks calculations, and stochastic differential equations. Geometric Brownian Motion, Ornstein-Uhlenbeck, and jump-diffusion processes are used.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Stock price 100 TL, μ = 0.10, σ = 0.20, dt = 1/252. 10,000 Monte Carlo simulations are run. 95% confidence interval is calculated. Black-Scholes: Call option price is calculated.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Quantitative models are important for understanding market risk. However, knowing the limits of models is critical."'
            },
            'de': {
                'title': 'Quantitative Finance - Experte',
                'concept_definition': 'Expertenlevel Quantitative Finance umfasst Monte-Carlo-Simulationen, stochastische Prozesse, Ito-Lemma, Black-Scholes-Merton-Modelle, Greeks-Berechnungen und stochastische Differentialgleichungen. Geometric Brownian Motion, Ornstein-Uhlenbeck und Jump-Diffusion-Prozesse werden verwendet.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Aktienkurs 100 TL, μ = 0,10, σ = 0,20, dt = 1/252. 10.000 Monte-Carlo-Simulationen werden durchgeführt. 95% Konfidenzintervall wird berechnet. Black-Scholes: Call-Optionspreis wird berechnet.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Quantitative Modelle sind wichtig für das Verständnis des Marktrisikos. Das Wissen um die Grenzen der Modelle ist jedoch kritisch."'
            },
            'it': {
                'title': 'Finanza Quantitativa - Esperto',
                'concept_definition': 'La finanza quantitativa a livello esperto include simulazioni Monte Carlo, processi stocastici, lemma di Ito, modelli Black-Scholes-Merton, calcoli dei Greci e equazioni differenziali stocastiche. Vengono utilizzati il Geometric Brownian Motion, Ornstein-Uhlenbeck e i processi jump-diffusion.',
                'practical_example': 'Geometric Brownian Motion: dS = μSdt + σSdW. Prezzo azione 100 TL, μ = 0.10, σ = 0.20, dt = 1/252. Vengono eseguite 10.000 simulazioni Monte Carlo. Viene calcolato l\'intervallo di confidenza al 95%. Black-Scholes: Viene calcolato il prezzo dell\'opzione Call.',
                'mathematical_formula': 'GBM: dS = μSdt + σSdW\nBlack-Scholes: ∂V/∂t + ½σ²S²∂²V/∂S² + rS∂V/∂S - rV = 0\nDelta = ∂V/∂S, Gamma = ∂²V/∂S², Theta = ∂V/∂t',
                'python_function': 'calculate_value_at_risk(returns, confidence_level)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "I modelli quantitativi sono importanti per comprendere il rischio di mercato. Tuttavia, conoscere i limiti dei modelli è critico."'
            }
        },
        'algorithmic_trading': {
            'tr': {
                'title': 'Algoritmik Ticaret - Uzman Seviye',
                'concept_definition': 'Uzman seviyede algoritmik ticaret, high-frequency trading, arbitraj stratejileri, market making, execution algoritmaları ve quantitative trading sistemlerini içerir. Latency, slippage, transaction cost optimizasyonu ve order book dinamikleri önemlidir.',
                'practical_example': 'Statistical arbitraj: İki varlık arasındaki cointegration ilişkisi kullanılır. Spread = Y - βX. Spread ortalamaya döndüğünde long/short pozisyon alınır. Z-score > 2 sinyal verir. Latency < 1ms, slippage < 0.01%.',
                'mathematical_formula': 'Cointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Position × Price Change) - Transaction Costs',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Algoritmik ticaret, hız ve veri avantajıdır. Ancak sistemik riskler ve flash crash\'ler potansiyel felaketlerdir."'
            },
            'en': {
                'title': 'Algorithmic Trading - Expert',
                'concept_definition': 'Expert level algorithmic trading includes high-frequency trading, arbitrage strategies, market making, execution algorithms, and quantitative trading systems. Latency, slippage, transaction cost optimization, and order book dynamics are important.',
                'practical_example': 'Statistical arbitrage: Cointegration relationship between two assets is used. Spread = Y - βX. Long/short positions are taken when spread reverts to mean. Z-score > 2 gives signal. Latency < 1ms, slippage < 0.01%.',
                'mathematical_formula': 'Cointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Position × Price Change) - Transaction Costs',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Algorithmic trading is about speed and data advantage. However, systemic risks and flash crashes are potential disasters."'
            },
            'de': {
                'title': 'Algorithmischer Handel - Experte',
                'concept_definition': 'Expertenlevel Algorithmischer Handel umfasst High-Frequency-Trading, Arbitrage-Strategien, Market Making, Execution-Algorithmen und quantitative Handelssysteme. Latency, Slippage, Transaction-Cost-Optimierung und Order-Book-Dynamiken sind wichtig.',
                'practical_example': 'Statistical Arbitrage: Kointegrationsbeziehung zwischen zwei Vermögenswerten wird verwendet. Spread = Y - βX. Long/Short-Positionen werden eingenommen, wenn Spread zum Mittelwert zurückkehrt. Z-Score > 2 gibt Signal. Latency < 1ms, Slippage < 0,01%.',
                'mathematical_formula': 'Kointegration: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Position × Preisänderung) - Transaktionskosten',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Algorithmischer Handel ist Geschwindigkeit und Datenvorteil. Systemische Risiken und Flash Crashes sind jedoch potenzielle Katastrophen."'
            },
            'it': {
                'title': 'Trading Algoritmico - Esperto',
                'concept_definition': 'Il trading algoritmico a livello esperto include high-frequency trading, strategie di arbitraggio, market making, algoritmi di esecuzione e sistemi di trading quantitativi. Latency, slippage, ottimizzazione dei costi di transazione e le dinamiche dell\'order book sono importanti.',
                'practical_example': 'Arbitraggio statistico: Viene utilizzata la relazione di cointegrazione tra due attività. Spread = Y - βX. Posizioni long/short vengono prese quando lo spread ritorna alla media. Z-score > 2 dà segnale. Latency < 1ms, slippage < 0.01%.',
                'mathematical_formula': 'Cointegrazione: Y = α + βX + ε\nZ-Score = (Spread - μ) / σ\nPnL = Σ(Positione × Variazione Prezzo) - Costi Transazione',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il trading algoritmico riguarda velocità e vantaggio dati. Tuttavia, i rischi sistemici e i flash crash sono potenziali disastri."'
            }
        },
        'machine_learning_finance': {
            'tr': {
                'title': 'Makine Öğrenmesi ve Finans - Uzman Seviye',
                'concept_definition': 'Uzman seviyede ML finans, neural networks, deep learning, reinforcement learning, NLP ve computer vision\'nin finansal uygulamalarını içerir. Hisse fiyat tahmini, risk modelleme, fraud detection, sentiment analysis, algorithmic trading ve robo-advisory yapılır.',
                'practical_example': 'LSTM modeli ile hisse fiyat tahmini: 60 gün geçmiş veri, 10 gün ileri tahmin. Dropout ile overfitting önlenir. RMSE ve MAE metrikleri ile değerlendirme. Feature engineering: teknik indikatörler, haberler, sosyal medya. Reinforcement learning ile optimal trading policy öğrenilir.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Machine learning, veri kalitesine bağlıdır. Garbage in, garbage out. Finansal veriler noisy ve non-stationarydir."'
            },
            'en': {
                'title': 'Machine Learning in Finance - Expert',
                'concept_definition': 'Expert level ML finance includes neural networks, deep learning, reinforcement learning, NLP, and computer vision applications in finance. Stock price prediction, risk modeling, fraud detection, sentiment analysis, algorithmic trading, and robo-advisory are performed.',
                'practical_example': 'LSTM model for stock price prediction: 60 days historical data, 10 days forward prediction. Dropout prevents overfitting. Evaluation with RMSE and MAE metrics. Feature engineering: technical indicators, news, social media. Reinforcement learning learns optimal trading policy.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Machine learning depends on data quality. Garbage in, garbage out. Financial data is noisy and non-stationary."'
            },
            'de': {
                'title': 'Machine Learning in der Finanzen - Experte',
                'concept_definition': 'Expertenlevel ML Finance umfasst Neural Networks, Deep Learning, Reinforcement Learning, NLP und Computer-Vision-Anwendungen in der Finanzen. Aktienkursvorhersage, Risikomodellierung, Fraud Detection, Sentiment Analysis, Algorithmic Trading und Robo-Advisory werden durchgeführt.',
                'practical_example': 'LSTM-Modell für Aktienkursvorhersage: 60 Tage historische Daten, 10 Tage Vorhersage. Dropout verhindert Overfitting. Bewertung mit RMSE und MAE Metriken. Feature Engineering: technische Indikatoren, Nachrichten, soziale Medien. Reinforcement Learning lernt optimale Trading-Policy.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Machine Learning hängt von Datenqualität ab. Garbage in, garbage out. Finanzdaten sind verrauscht und nicht-stationär."'
            },
            'it': {
                'title': 'Machine Learning nella Finanza - Esperto',
                'concept_definition': 'Il ML finanziario a livello esperto include reti neurali, deep learning, reinforcement learning, NLP e applicazioni di computer vision nella finanza. Vengono eseguite previsioni dei prezzi azionari, modellazione del rischio, rilevamento frodi, analisi del sentiment, trading algoritmico e robo-advisory.',
                'practical_example': 'Modello LSTM per la previsione dei prezzi azionari: 60 giorni di dati storici, 10 giorni di previsione. Il dropout previene l\'overfitting. Valutazione con metriche RMSE e MAE. Feature engineering: indicatori tecnici, notizie, social media. Il reinforcement learning impara la policy di trading ottimale.',
                'mathematical_formula': 'LSTM: ht = tanh(Wh × ht-1 + Wx × xt + b)\nLoss = MSE(y_pred, y_actual)\nAccuracy = (TP + TN) / (TP + TN + FP + FN)',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "Il machine learning dipende dalla qualità dei dati. Garbage in, garbage out. I dati finanziari sono rumorosi e non stazionari."'
            }
        },
        'blockchain_crypto': {
            'tr': {
                'title': 'Blockchain ve Kripto - Uzman Seviye',
                'concept_definition': 'Uzman seviyede blockchain ve kripto, distributed ledger technology, smart contracts, DeFi, NFT, DAO ve kripto ekonomisini içerir. Proof of Work, Proof of Stake, Proof of Authority, consensus mekanizmaları ve tokenomics analiz edilir. Layer 2 solutions ve cross-chain bridges kullanılır.',
                'practical_example': 'Bitcoin: PoW consensus, blok süresi 10 dakika, maksimum supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming, liquidity mining. Tokenomics: inflation rate, vesting schedule, utility, governance. Layer 2: Polygon, Arbitrum.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': '"Kara Kuğu" kitabında Nassim Taleb şunu söylüyor: "Blockchain, finansal sistemde devrim yaratabilir. Ancak volatilite ve düzenleyici riskler önemlidir."'
            },
            'en': {
                'title': 'Blockchain & Crypto - Expert',
                'concept_definition': 'Expert level blockchain and crypto includes distributed ledger technology, smart contracts, DeFi, NFT, DAO, and crypto economics. Proof of Work, Proof of Stake, Proof of Authority, consensus mechanisms, and tokenomics are analyzed. Layer 2 solutions and cross-chain bridges are used.',
                'practical_example': 'Bitcoin: PoW consensus, block time 10 minutes, max supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming, liquidity mining. Tokenomics: inflation rate, vesting schedule, utility, governance. Layer 2: Polygon, Arbitrum.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "The Black Swan", Nassim Taleb says: "Blockchain can revolutionize the financial system. However, volatility and regulatory risks are important."'
            },
            'de': {
                'title': 'Blockchain & Krypto - Experte',
                'concept_definition': 'Expertenlevel Blockchain und Krypto umfasst Distributed Ledger Technology, Smart Contracts, DeFi, NFT, DAO und Kryptoökonomie. Proof of Work, Proof of Stake, Proof of Authority, Konsensmechanismen und Tokenomics werden analysiert. Layer-2-Lösungen und Cross-Chain-Bridges werden verwendet.',
                'practical_example': 'Bitcoin: PoW-Konsens, Blockzeit 10 Minuten, Max Supply 21M. Ethereum: PoS, Gas-Gebühr, Smart Contracts. DeFi: Lending, Borrowing, Yield Farming, Liquidity Mining. Tokenomics: Inflationsrate, Vesting-Schedule, Utility, Governance. Layer 2: Polygon, Arbitrum.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Der Schwarze Schwan" sagt Nassim Taleb: "Blockchain kann das Finanzsystem revolutionieren. Volatilität und regulatorische Risiken sind jedoch wichtig."'
            },
            'it': {
                'title': 'Blockchain e Cripto - Esperto',
                'concept_definition': 'La blockchain e le cripto a livello esperto includono distributed ledger technology, smart contracts, DeFi, NFT, DAO e crypto economics. Proof of Work, Proof of Stake, Proof of Authority, meccanismi di consenso e tokenomics vengono analizzati. Vengono utilizzati le soluzioni Layer 2 e i ponti cross-chain.',
                'practical_example': 'Bitcoin: consenso PoW, tempo blocco 10 minuti, max supply 21M. Ethereum: PoS, gas fee, smart contracts. DeFi: lending, borrowing, yield farming, liquidity mining. Tokenomics: inflation rate, vesting schedule, utility, governance. Layer 2: Polygon, Arbitrum.',
                'mathematical_formula': 'Hash Rate = Hashes / Second\nDifficulty = Target / Current Target\nGas Fee = Gas Used × Gas Price\nAPY = (1 + r/n)^n - 1',
                'python_function': 'calculate_compound_interest(principal, annual_rate, times_per_year, years)',
                'literary_insights': 'In "Il Cigno Nero", Nassim Taleb dice: "La blockchain può rivoluzionare il sistema finanziario. Tuttavia, la volatilità e i rischi normativi sono importanti."'
            }
        },
        'esg_investing': {
            'tr': {
                'title': 'ESG Yatırımı - Uzman Seviye',
                'concept_definition': 'Uzman seviyede ESG yatırımı, çevresel, sosyal ve yönetişim kriterlerini içerir. Sürdürülebilir yatırım, impact investing, green bonds, social bonds ve ESG scoring analiz edilir. ESG skorları, raporlama standartları (GRI, SASB, TCFD) ve ESG integration kullanılır.',
                'practical_example': 'ESG skorlama: Çevresel (karbon ayak izi, enerji verimliliği, su yönetimi), Sosyal (işçi hakları, topluluk ilişkileri, çeşitlilik), Yönetişim (kurumsal yönetim, şeffaflık, yönetici ücretleri). MSCI ESG Rating: AAA (lider) - CCC (gecikmiş). TCFD raporlaması zorunludur.',
                'mathematical_formula': 'ESG Skoru = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': '"Psikoloji Para" kitabında Morgan Housel şunu söylüyor: "ESG yatırımı, sadece finansal getiri değil, sosyal etki de önemlidir. Uzun vadeli sürdürülebilirlik kritiktir."'
            },
            'en': {
                'title': 'ESG Investing - Expert',
                'concept_definition': 'Expert level ESG investing includes environmental, social, and governance criteria. Sustainable investing, impact investing, green bonds, social bonds, and ESG scoring are analyzed. ESG scores, reporting standards (GRI, SASB, TCFD), and ESG integration are used.',
                'practical_example': 'ESG scoring: Environmental (carbon footprint, energy efficiency, water management), Social (labor rights, community relations, diversity), Governance (corporate governance, transparency, executive compensation). MSCI ESG Rating: AAA (leader) - CCC (laggard). TCFD reporting is mandatory.',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel says: "ESG investing is not just about financial returns, but also social impact. Long-term sustainability is critical."'
            },
            'de': {
                'title': 'ESG-Investition - Experte',
                'concept_definition': 'Expertenlevel ESG-Investition umfasst Umwelt-, Sozial- und Unternehmensführungskriterien. Nachhaltiges Investieren, Impact Investing, Green Bonds, Social Bonds und ESG-Scoring werden analysiert. ESG-Scores, Berichtsstandards (GRI, SASB, TCFD) und ESG-Integration werden verwendet.',
                'practical_example': 'ESG-Scoring: Umwelt (CO2-Fußabdruck, Energieeffizienz, Wassermanagement), Sozial (Arbeitsrechte, Gemeindebeziehungen, Diversität), Unternehmensführung (Corporate Governance, Transparenz, Executive Compensation). MSCI ESG Rating: AAA (Führer) - CCC (Nachzügler). TCFD-Berichterstattung ist obligatorisch.',
                'mathematical_formula': 'ESG Score = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money" sagt Morgan Housel: "ESG-Investition ist nicht nur finanzielle Rendite, sondern auch soziale Wirkung. Langfristige Nachhaltigkeit ist kritisch."'
            },
            'it': {
                'title': 'Investimento ESG - Esperto',
                'concept_definition': 'L\'investimento ESG a livello esperto include criteri ambientali, sociali e di governance. Investimento sostenibile, impact investing, green bonds, social bonds e ESG scoring vengono analizzati. Vengono utilizzati punteggi ESG, standard di reporting (GRI, SASB, TCFD) e l\'integrazione ESG.',
                'practical_example': 'Punteggio ESG: Ambientale (impronta di carbonio, efficienza energetica, gestione dell\'acqua), Sociale (diritti dei lavoratori, relazioni comunitarie, diversità), Governance (governance aziendale, trasparenza, retribuzione degli esecutivi). Rating ESG MSCI: AAA (leader) - CCC (ritardatario). La reportistica TCFD è obbligatoria.',
                'mathematical_formula': 'Punteggio ESG = (E × wE + S × wS + G × wG) / (wE + wS + wG)\nCarbon Footprint = Σ(Emission × Activity)\nGreen Bond Yield = Coupon + Greenium',
                'python_function': 'calculate_sharpe_ratio(returns, risk_free_rate)',
                'literary_insights': 'In "The Psychology of Money", Morgan Housel dice: "L\'investimento ESG non riguarda solo i rendimenti finanziari, ma anche l\'impatto sociale. La sostenibilità a lungo termine è critica."'
            }
        }
    }
}


def get_guide_data(phase: str, topic: str, lang: str = 'tr') -> Dict[str, str]:
    """
    Finansal eğitim verisini döndür

    Args:
        phase: 'beginner', 'intermediate', 'advanced', veya 'expert'
        topic: Konu anahtarı (örn: 'income_expenses', 'compound_interest')
        lang: Dil kodu (varsayılan: 'tr')

    Returns:
        Konu verisi sözlüğü
    """
    try:
        return FINANCIAL_GUIDE_DATA[phase][topic][lang]
    except KeyError:
        # Eğer dil bulunamazsa Türkçe'ye dön
        try:
            return FINANCIAL_GUIDE_DATA[phase][topic]['tr']
        except KeyError:
            # Eğer konu bulunamazsa boş sözlük dön
            return {}


def get_all_phases() -> list:
    """Tüm fazları döndür"""
    return list(FINANCIAL_GUIDE_DATA.keys())


def get_all_topics(phase: str) -> list:
    """Belirli bir fazdaki tüm konuları döndür"""
    return list(FINANCIAL_GUIDE_DATA.get(phase, {}).keys())


def get_formula_function(function_name: str) -> Callable:
    """
    Formül fonksiyonunu döndür

    Args:
        function_name: Fonksiyon adı (örn: 'calculate_compound_interest')

    Returns:
        Python fonksiyonu
    """
    formula_functions = {
        'calculate_compound_interest': calculate_compound_interest,
        'calculate_simple_interest': calculate_simple_interest,
        'calculate_financial_independence_number': calculate_financial_independence_number,
        'calculate_dollar_cost_averaging': calculate_dollar_cost_averaging,
        'calculate_rule_of_72': calculate_rule_of_72,
        'calculate_50_30_20_budget': calculate_50_30_20_budget,
        'calculate_sharpe_ratio': calculate_sharpe_ratio,
        'calculate_inflation_adjusted_return': calculate_inflation_adjusted_return,
        'calculate_bes_return': calculate_bes_return,
        'calculate_mutual_fund_return': calculate_mutual_fund_return,
        'calculate_bond_yield': calculate_bond_yield,
        'calculate_commodity_future_price': calculate_commodity_future_price,
        'calculate_portfolio_beta': calculate_portfolio_beta,
        'calculate_capm_return': calculate_capm_return,
        'calculate_sortino_ratio': calculate_sortino_ratio,
        'calculate_information_ratio': calculate_information_ratio,
        'calculate_value_at_risk': calculate_value_at_risk,
        'calculate_max_drawdown': calculate_max_drawdown
    }

    return formula_functions.get(function_name, lambda *args, **kwargs: None)


# ============ FINANCIAL DICTIONARY ============

FINANCIAL_DICTIONARY = {
    'tr': {
        'bank': {
            'title': 'Banka',
            'definition': 'Para kabul eden, kredi veren, ödeme hizmetleri sunan ve finansal aracılık yapan kuruluştur. Merkez bankası, ticari banka, yatırım bankası gibi türleri vardır.',
            'working_mechanism': 'Bankalar mevduat toplar ve bu mevduatları kredi olarak verir. Aradaki faiz farkı (spread) ile kâr eder. Merkez bankası para politikasını yönetir, ticari bankalar bireysel ve kurumsal hizmetler sunar.',
            'examples': 'Ziraat Bankası, Garanti BBVA, İş Bankası (ticari bankalar); TCMB (merkez bankası)'
        },
        'investment_company': {
            'title': 'Yatırım Kuruluşu',
            'definition': 'Portföy yönetimi, yatırım danışmanlığı, varlık yönetimi ve sermaye piyasası işlemleri yapan finansal kuruluştur.',
            'working_mechanism': 'Yatırım kuruluşları müşterilerin paralarını profesyonel olarak yönetir, hisse senedi, tahvil, fon gibi varlıklara yatırım yapar. Yönetim ücreti ve performans komisyonu alır.',
            'examples': 'Ak Yatırım, İş Yatırım, Yapı Kredi Yatırım'
        },
        'savings_institution': {
            'title': 'Tasarruf Kuruluşu',
            'definition': 'Bireysel tasarrufu teşvik etmek, mevduat toplamak ve uzun vadeli finansman sağlamak amacıyla kurulan kuruluşlar.',
            'working_mechanism': 'Tasarruf kuruluşları genellikle devlet destekli olur, vergi avantajları sunar ve emeklilik, konut, eğitim gibi amaçlar için özel tasarruf ürünleri sunar.',
            'examples': 'BES şirketleri, emeklilik fonları, tasarruf sandıkları'
        },
        'bist': {
            'title': 'Borsa İstanbul (BIST)',
            'definition': 'Türkiye\'nin ulusal borsası. Hisse senetleri, borçlanma araçları, türev araçların alınıp satıldığı organize piyasadır.',
            'working_mechanism': 'BIST\'te şirketler halka arz olur, yatırımcılar hisse senedi alır-satar. BIST 100 endeksi piyasa performansını gösterir. İşlem saatleri 09:30-18:00 arasıdır.',
            'examples': 'BIST 100, BIST 30, BIST Banka endeksleri'
        },
        'mutual_fund': {
            'title': 'Yatırım Fonu',
            'definition': 'Birçok yatırımcının parasının toplanarak profesyonel yöneticiler tarafından çeşitli varlıklara (hisse, tahvil, emtia) yatırım yapılmasıdır.',
            'working_mechanism': 'Fon katılma belgesi (FKB) alınarak fonlara yatırım yapılır. Fon yöneticisi varlık dağılımını yapar. Gider kesintisi ve yönetim ücreti düşüldükten sonra getiri paylaşılır.',
            'examples': 'A tipi yatırım fonları (hisse ağırlıklı), B tipi (tahvil ağırlıklı), Altın fonları'
        },
        'bes': {
            'title': 'Bireysel Emeklilik Sistemi (BES)',
            'definition': 'Bireysel emeklilik için uzun vadeli tasarruf ve yatırım sistemi. Devlet katkısı ve vergi avantajı sunar.',
            'working_mechanism': 'Aylık katkı payı ödenir, işveren katkısı ve devlet katkısı eklenir. Emeklilik fonlarında birikim büyür. 10 yıl sonra veya 56 yaşında çekilebilir.',
            'examples': 'Allianz Hayat ve Emeklilik, Aegon Emeklilik, AvivaSA'
        },
        'commodity': {
            'title': 'Emtia',
            'definition': 'Altın, gümüş, petrol, tarım ürünleri gibi ticareti yapılan fiziksel mallar. Değer saklama aracı ve spekülasyon aracı olarak kullanılır.',
            'working_mechanism': 'Emtialar spot veya vadeli piyasalarda alınıp satılır. Fiyatları arz-talep dengesine, jeopolitik olaylara, enflasyona göre değişir.',
            'examples': 'Altın (XAU), Gümüş (XAG), Petrol (WTI, Brent), Bakır, Buğday'
        },
        'debt_securities': {
            'title': 'Borçlanma Araçları',
            'definition': 'Devlet veya şirketlerin borç almak için çıkardığı kıymetli evrak. Tahvil, bono, eurobond gibi türleri vardır.',
            'working_mechanism': 'Borçlanma aracı alan kişi, borç veren olur. Vade sonunda ana para ve kupon faizi alır. Getiri kupon oranı ve piyasa faizine göre hesaplanır.',
            'examples': 'Devlet tahvili, Hazine bonosu, Şirket tahvili, Eurobond'
        },
        'etf': {
            'title': 'Borsa Yatırım Fonu (ETF)',
            'definition': 'Bir endeksi takip eden, borsada hisse senedi gibi alınıp satılan fon. Düşük maliyet ve yüksek likidite sağlar.',
            'working_mechanism': 'ETF\'ler endeksleri (örn. S&P 500, BIST 30) takip eder. Fon yöneticisi değil, algoritmik yönetim vardır. Yönetim ücreti düşüktür.',
            'examples': 'iShares ETF\'leri, SPDR ETF\'leri, BIST 30 ETF'
        },
        'derivative': {
            'title': 'Türev Araç',
            'definition': 'Değeri başka bir varlığa (underlying) dayalı finansal araç. Risk yönetimi ve spekülasyon için kullanılır.',
            'working_mechanism': 'Türev araçlar vadeli işlem, opsiyon, swap şeklinde olabilir. İleriki bir tarihte belirli bir fiyattan alma/satma hakkı veya yükümlülüğü verir.',
            'examples': 'Vadeli işlem sözleşmeleri, Opsiyon sözleşmeleri, Swap işlemleri'
        },
        'repo': {
            'title': 'Repo',
            'definition': 'Gerçekleştirme tarihi itibarıyla belirli bir vadede geri alım taahhüdü ile menkul kıymet satımı işlemidir.',
            'working_mechanism': 'Repo yapan taraf menkul kıymet satar ve vade sonunda geri alır. Faiz farkı kâr/zarır olur. Kısa vadeli likidite yönetimi için kullanılır.',
            'examples': 'TL repo, USD repo, Euro repo işlemleri'
        },
        'leverage': {
            'title': 'Kaldıraç',
            'definition': 'Küçük bir sermaye ile büyük pozisyon açma imkanı. Risk ve getiriyi çarpan etkisiyle artırır.',
            'working_mechanism': 'Kaldıraç oranı 10 ise, 10.000 TL ile 100.000 TL pozisyon açılabilir. %1 artış %10 getiri, %1 düşüş %10 zarar sağlar.',
            'examples': 'Forex kaldıraç (1:10, 1:100), Vadeli işlem kaldıracı, CFD kaldıracı'
        },
        'margin': {
            'title': 'Marjin',
            'definition': 'Kaldıraçlı işlemlerde teminat olarak bloke edilen para. Pozisyonun devamı için gerekli minimum bakiyedir.',
            'working_mechanism': 'Marjin seviyesi düşerse teminat tamamlama çağrısı (margin call) gelir. Teminat yetersizse pozisyon otomatik kapatılır (stop out).',
            'examples': 'Başlangıç marjini, sürdürme marjini, teminat tamamlama'
        },
        'liquidity': {
            'title': 'Likidite',
            'definition': 'Bir varlığın nakde çevrilme hızı ve kolaylığı. Likid varlıklar hızlı nakde çevrilir, illik varlıklar zor çevrilir.',
            'working_mechanism': 'Likidite piyasa derinliği ile ölçülür. İşlem hacmi yüksekse likidite yüksektir. Likidite krizinde varlıklar hızla değer kaybeder.',
            'examples': 'Nakit (en likit), Hisse senedi (yüksek likid), Gayrimenkul (düşük likid)'
        },
        'volatility': {
            'title': 'Volatilite',
            'definition': 'Fiyatların değişkenliği. Yüksek volatilite fiyatların hızlı değiştiğini, düşük volatilite istikrarı gösterir.',
            'working_mechanism': 'Volatilite standart sapma ile ölçülür. VIX endeksi piyasa volatilitesini gösterir. Yüksek volatilite yüksek risk ve fırsat demektir.',
            'examples': 'VIX endeksi, Hisse volatilitesi, Kripto volatilitesi'
        }
    },
    'en': {
        'bank': {
            'title': 'Bank',
            'definition': 'Institution that accepts deposits, extends credit, provides payment services, and acts as financial intermediary. Types include central bank, commercial bank, investment bank.',
            'working_mechanism': 'Banks collect deposits and lend them as credit. They profit from the interest rate spread (difference). Central banks manage monetary policy, commercial banks provide individual and corporate services.',
            'examples': 'Ziraat Bank, Garanti BBVA, İş Bankası (commercial banks); TCMB (central bank)'
        },
        'investment_company': {
            'title': 'Investment Company',
            'definition': 'Financial institution that provides portfolio management, investment advisory, asset management, and capital market services.',
            'working_mechanism': 'Investment companies professionally manage clients\' money, investing in stocks, bonds, funds, and other assets. They charge management fees and performance commissions.',
            'examples': 'Ak Yatırım, İş Yatırım, Yapı Kredi Yatırım'
        },
        'savings_institution': {
            'title': 'Savings Institution',
            'definition': 'Institutions established to encourage individual savings, collect deposits, and provide long-term financing.',
            'working_mechanism': 'Savings institutions are often state-supported, offer tax advantages, and provide special savings products for retirement, housing, and education purposes.',
            'examples': 'BES companies, pension funds, savings banks'
        },
        'bist': {
            'title': 'Borsa İstanbul (BIST)',
            'definition': 'Turkey\'s national stock exchange. Organized market where stocks, debt securities, and derivatives are bought and sold.',
            'working_mechanism': 'Companies go public (IPO) on BIST, investors buy and sell stocks. BIST 100 index shows market performance. Trading hours are 09:30-18:00.',
            'examples': 'BIST 100, BIST 30, BIST Banking indices'
        },
        'mutual_fund': {
            'title': 'Mutual Fund',
            'definition': 'Pooling money from many investors to be invested in various assets (stocks, bonds, commodities) by professional managers.',
            'working_mechanism': 'Investors buy fund participation units (FKB). Fund managers determine asset allocation. Returns are shared after deducting expense ratios and management fees.',
            'examples': 'Type A funds (equity-weighted), Type B funds (bond-weighted), Gold funds'
        },
        'bes': {
            'title': 'Individual Pension System (BES)',
            'definition': 'Long-term savings and investment system for individual retirement. Offers government contribution and tax advantages.',
            'working_mechanism': 'Monthly contribution is paid, employer contribution and government contribution are added. Savings grow in pension funds. Can be withdrawn after 10 years or at age 56.',
            'examples': 'Allianz Hayat ve Emeklilik, Aegon Emeklilik, AvivaSA'
        },
        'commodity': {
            'title': 'Commodity',
            'definition': 'Physical goods traded such as gold, silver, oil, agricultural products. Used as store of value and speculation tool.',
            'working_mechanism': 'Commodities are bought and sold in spot or futures markets. Prices change based on supply-demand balance, geopolitical events, and inflation.',
            'examples': 'Gold (XAU), Silver (XAG), Oil (WTI, Brent), Copper, Wheat'
        },
        'debt_securities': {
            'title': 'Debt Securities',
            'definition': 'Valuable papers issued by governments or companies to borrow money. Types include bonds, bills, eurobonds.',
            'working_mechanism': 'Buyer of debt security becomes lender. At maturity, receives principal and coupon interest. Return is calculated based on coupon rate and market interest rate.',
            'examples': 'Government bond, Treasury bill, Corporate bond, Eurobond'
        },
        'etf': {
            'title': 'Exchange Traded Fund (ETF)',
            'definition': 'Fund that tracks an index, bought and sold like stocks on exchange. Provides low cost and high liquidity.',
            'working_mechanism': 'ETFs track indices (e.g., S&P 500, BIST 30). Uses algorithmic management instead of fund managers. Management fees are low.',
            'examples': 'iShares ETFs, SPDR ETFs, BIST 30 ETF'
        },
        'derivative': {
            'title': 'Derivative',
            'definition': 'Financial instrument whose value is derived from another asset (underlying). Used for risk management and speculation.',
            'working_mechanism': 'Derivatives can be futures, options, swaps. Give right or obligation to buy/sell at a specific price on a future date.',
            'examples': 'Futures contracts, Options contracts, Swap transactions'
        },
        'repo': {
            'title': 'Repo',
            'definition': 'Sale of securities with repurchase commitment at a specific maturity date from the transaction date.',
            'working_mechanism': 'Repo seller sells securities and buys back at maturity. Interest difference is profit/loss. Used for short-term liquidity management.',
            'examples': 'TL repo, USD repo, Euro repo transactions'
        },
        'leverage': {
            'title': 'Leverage',
            'definition': 'Ability to open large positions with small capital. Multiplies risk and return.',
            'working_mechanism': 'If leverage is 10, 10,000 TL can open 100,000 TL position. 1% increase gives 10% return, 1% decrease gives 10% loss.',
            'examples': 'Forex leverage (1:10, 1:100), Futures leverage, CFD leverage'
        },
        'margin': {
            'title': 'Margin',
            'definition': 'Money blocked as collateral in leveraged transactions. Minimum balance required to maintain position.',
            'working_mechanism': 'If margin level drops, margin call (collateral call) comes. If collateral insufficient, position automatically closes (stop out).',
            'examples': 'Initial margin, maintenance margin, margin call'
        },
        'liquidity': {
            'title': 'Liquidity',
            'definition': 'Speed and ease of converting an asset to cash. Liquid assets convert quickly, illiquid assets convert with difficulty.',
            'working_mechanism': 'Liquidity is measured by market depth. If trading volume is high, liquidity is high. In liquidity crisis, assets lose value rapidly.',
            'examples': 'Cash (most liquid), Stocks (high liquidity), Real estate (low liquidity)'
        },
        'volatility': {
            'title': 'Volatility',
            'definition': 'Variability of prices. High volatility means prices change rapidly, low volatility means stability.',
            'working_mechanism': 'Volatility is measured by standard deviation. VIX index shows market volatility. High volatility means high risk and opportunity.',
            'examples': 'VIX index, Stock volatility, Crypto volatility'
        }
    },
    'de': {
        'bank': {
            'title': 'Bank',
            'definition': 'Institution, die Einlagen annimmt, Kredit vergibt, Zahlungsdienste anbietet und als Finanzintermediär fungiert. Arten umfassen Zentralbank, Geschäftsbank, Investmentbank.',
            'working_mechanism': 'Banken sammeln Einlagen und verleihen sie als Kredit. Sie profitieren vom Zinsspread (Differenz). Zentralbanken verwalten die Geldpolitik, Geschäftsbanken bieten individuelle und unternehmensbezogene Dienstleistungen an.',
            'examples': 'Ziraat Bank, Garanti BBVA, İş Bankası (Geschäftsbanken); TCMB (Zentralbank)'
        },
        'investment_company': {
            'title': 'Investitionsunternehmen',
            'definition': 'Finanzinstitution, die Portfoliomanagement, Investmentberatung, Vermögensverwaltung und Kapitalmarktdienstleistungen anbietet.',
            'working_mechanism': 'Investitionsunternehmen verwalten professionell das Geld der Kunden und investieren in Aktien, Anleihen, Fonds und andere Vermögenswerte. Sie erheben Verwaltungsgebühren und Leistungskommissionen.',
            'examples': 'Ak Yatırım, İş Yatırım, Yapı Kredi Yatırım'
        },
        'savings_institution': {
            'title': 'Sparkasse',
            'definition': 'Institutionen, die zur Förderung individueller Ersparnisse, Sammlung von Einlagen und Bereitstellung langfristiger Finanzierung eingerichtet wurden.',
            'working_mechanism': 'Sparkassen sind oft staatlich unterstützt, bieten Steuervorteile und bieten spezielle Sparprodukte für Rente, Wohnen und Bildung.',
            'examples': 'BES-Unternehmen, Rentenfonds, Sparkassen'
        },
        'bist': {
            'title': 'Borsa İstanbul (BIST)',
            'definition': 'Türkeis nationale Börse. Organisierter Markt, an dem Aktien, Schuldverschreibungen und Derivate gekauft und verkauft werden.',
            'working_mechanism': 'Unternehmen gehen an die Börse (IPO), Investoren kaufen und verkaufen Aktien. Der BIST 100 Index zeigt die Marktperformance. Handelszeiten sind 09:30-18:00.',
            'examples': 'BIST 100, BIST 30, BIST Bankenindizes'
        },
        'mutual_fund': {
            'title': 'Investmentfonds',
            'definition': 'Zusammenlegung von Geld vieler Investoren, um von professionellen Managern in verschiedene Vermögenswerte (Aktien, Anleihen, Rohstoffe) investiert zu werden.',
            'working_mechanism': 'Investoren kaufen Fondsanteilsscheine (FKB). Fondsmanager bestimmen die Asset-Allokation. Renditen werden nach Abzug von Aufwandsquoten und Verwaltungsgebühren geteilt.',
            'examples': 'Typ A Fonds (aktienlastig), Typ B Fonds (anleihenlastig), Goldfonds'
        },
        'bes': {
            'title': 'Individuelles Rentensystem (BES)',
            'definition': 'Langfristiges Spar- und Investitionssystem für individuelle Rente. Bietet Staatsbeitrag und Steuervorteile.',
            'working_mechanism': 'Monatlicher Beitrag wird gezahlt, Arbeitgeberbeitrag und Staatsbeitrag werden hinzugefügt. Ersparnisse wachsen in Rentenfonds. Kann nach 10 Jahren oder im Alter von 56 abgehoben werden.',
            'examples': 'Allianz Hayat ve Emeklilik, Aegon Emeklilik, AvivaSA'
        },
        'commodity': {
            'title': 'Rohstoff',
            'definition': 'Physische Waren wie Gold, Silber, Öl, landwirtschaftliche Produkte. Wird als Wertspeicher und Spekulationsinstrument verwendet.',
            'working_mechanism': 'Rohstoffe werden auf Spot- oder Terminmärkten gekauft und verkauft. Preise ändern sich basierend auf Angebot-Nachfrage-Balance, geopolitische Ereignisse und Inflation.',
            'examples': 'Gold (XAU), Silber (XAG), Öl (WTI, Brent), Kupfer, Weizen'
        },
        'debt_securities': {
            'title': 'Schuldverschreibungen',
            'definition': 'Wertpapiere, die von Regierungen oder Unternehmen zur Kreditaufnahme ausgegeben werden. Arten umfassen Anleihen, Bills, Eurobonds.',
            'working_mechanism': 'Käufer von Schuldverschreibungen wird Gläubiger. Bei Fälligkeit erhält er Nennwert und Kuponzins. Rendite wird basierend auf Kuponrate und Marktzins berechnet.',
            'examples': 'Staatsanleihe, Schatzwechsel, Unternehmensanleihe, Eurobond'
        },
        'etf': {
            'title': 'Exchange Traded Fund (ETF)',
            'definition': 'Fonds, der einen Index nachverfolgt und an der Börse wie Aktien gekauft und verkauft wird. Bietet niedrige Kosten und hohe Liquidität.',
            'working_mechanism': 'ETFs verfolgen Indizes (z.B. S&P 500, BIST 30). Verwendet algorithmisches Management statt Fondsmanager. Verwaltungsgebühren sind niedrig.',
            'examples': 'iShares ETFs, SPDR ETFs, BIST 30 ETF'
        },
        'derivative': {
            'title': 'Derivat',
            'definition': 'Finanzinstrument, dessen Wert von einem anderen Vermögenswert (Underlying) abgeleitet ist. Wird für Risikomanagement und Spekulation verwendet.',
            'working_mechanism': 'Derivate können Futures, Optionen, Swaps sein. Geben Recht oder Verpflichtung, an einem zukünftigen Datum zu einem bestimmten Preis zu kaufen/verkaufen.',
            'examples': 'Terminkontrakte, Optionskontrakte, Swap-Transaktionen'
        },
        'repo': {
            'title': 'Repo',
            'definition': 'Verkauf von Wertpapieren mit Rückkaufverpflichtung an einem bestimmten Fälligkeitsdatum ab dem Transaktionsdatum.',
            'working_mechanism': 'Repo-Verkäufer verkauft Wertpapiere und kauft sie bei Fälligkeit zurück. Zinsdifferenz ist Gewinn/Verlust. Wird für kurzfristige Liquiditätsverwaltung verwendet.',
            'examples': 'TL Repo, USD Repo, Euro Repo Transaktionen'
        },
        'leverage': {
            'title': 'Hebel',
            'definition': 'Fähigkeit, große Positionen mit kleinem Kapital zu eröffnen. Multipliziert Risiko und Rendite.',
            'working_mechanism': 'Wenn Hebel 10 ist, können 10.000 TL eine 100.000 TL Position eröffnen. 1% Zunahme gibt 10% Rendite, 1% Abnahme gibt 10% Verlust.',
            'examples': 'Forex Hebel (1:10, 1:100), Futures Hebel, CFD Hebel'
        },
        'margin': {
            'title': 'Margin',
            'definition': 'Geld, das als Sicherheit in gehebelten Transaktionen blockiert wird. Mindestguthaben zur Aufrechterhaltung der Position.',
            'working_mechanism': 'Wenn Margenniveau sinkt, kommt Margin Call (Sicherheitsaufruf). Wenn Sicherheit unzureichend, schließt Position automatisch (Stop Out).',
            'examples': 'Anfangsmargin, Erhaltungsmargin, Margin Call'
        },
        'liquidity': {
            'title': 'Liquidität',
            'definition': 'Geschwindigkeit und Leichtigkeit der Umwandlung eines Vermögenswerts in Bargeld. Flüssige Vermögenswerte konvertieren schnell, illiquide Vermögenswerte konvertieren mit Schwierigkeit.',
            'working_mechanism': 'Liquidität wird durch Markttiefe gemessen. Wenn Handelsvolumen hoch ist, ist Liquidität hoch. In Liquiditätskrise verlieren Vermögenswerte schnell an Wert.',
            'examples': 'Bargeld (am flüssigsten), Aktien (hohe Liquidität), Immobilien (niedrige Liquidität)'
        },
        'volatility': {
            'title': 'Volatilität',
            'definition': 'Variabilität der Preise. Hohe Volatilität bedeutet, dass Preise schnell ändern, niedrige Volatilität bedeutet Stabilität.',
            'working_mechanism': 'Volatilität wird durch Standardabweichung gemessen. VIX Index zeigt Marktvolatilität. Hohe Volatilität bedeutet hohes Risiko und Chance.',
            'examples': 'VIX Index, Aktienvolatilität, Krypto-Volatilität'
        }
    },
    'it': {
        'bank': {
            'title': 'Banca',
            'definition': 'Istituzione che accetta depositi, estende credito, fornisce servizi di pagamento e agisce come intermediario finanziario. Tipi includono banca centrale, banca commerciale, banca di investimento.',
            'working_mechanism': 'Le banche raccolgono depositi e li prestano come credito. Profitto dallo spread dei tassi di interesse (differenza). Le banche centrali gestiscono la politica monetaria, le banche commerciali forniscono servizi individuali e aziendali.',
            'examples': 'Ziraat Bank, Garanti BBVA, İş Bankası (banche commerciali); TCMB (banca centrale)'
        },
        'investment_company': {
            'title': 'Società di Investimento',
            'definition': 'Istituzione finanziaria che fornisce gestione del portafoglio, consulenza agli investimenti, gestione degli asset e servizi del mercato dei capitali.',
            'working_mechanism': 'Le società di investimento gestiscono professionalmente i denaro dei clienti, investendo in azioni, obbligazioni, fondi e altri asset. Addebitano commissioni di gestione e commissioni di performance.',
            'examples': 'Ak Yatırım, İş Yatırım, Yapı Kredi Yatırım'
        },
        'savings_institution': {
            'title': 'Istituzione di Risparmio',
            'definition': 'Istituzioni stabilite per incoraggiare il risparmio individuale, raccogliere depositi e fornire finanziamenti a lungo termine.',
            'working_mechanism': 'Le istituzioni di risparmio sono spesso supportate dallo stato, offrono vantaggi fiscali e forniscono prodotti di risparmio speciali per pensionamento, alloggio e istruzione.',
            'examples': 'Società BES, fondi pensione, casse di risparmio'
        },
        'bist': {
            'title': 'Borsa İstanbul (BIST)',
            'definition': 'Borsa nazionale della Turchia. Mercato organizzato dove azioni, titoli di debito e derivati sono comprati e venduti.',
            'working_mechanism': 'Le aziende vanno in pubblico (IPO) su BIST, gli investitori comprano e vendono azioni. L\'indice BIST 100 mostra la performance del mercato. Gli orari di trading sono 09:30-18:00.',
            'examples': 'BIST 100, BIST 30, indici bancari BIST'
        },
        'mutual_fund': {
            'title': 'Fondo di Investimento',
            'definition': 'Raccolta di denaro da molti investitori per essere investito in vari asset (azioni, obbligazioni, materie prime) da manager professionisti.',
            'working_mechanism': 'Gli investitori acquistano quote di partecipazione al fondo (FKB). I gestori dei fondi determinano l\'allocazione degli asset. I rendimenti sono condivisi dopo aver dedotto i rapporti di spesa e le commissioni di gestione.',
            'examples': 'Fondi Tipo A (pesati azioni), Fondi Tipo B (pesati obbligazioni), Fondi oro'
        },
        'bes': {
            'title': 'Sistema Pensionistico Individuale (BES)',
            'definition': 'Sistema di risparmio e investimento a lungo termine per la pensione individuale. Offre contributo statale e vantaggi fiscali.',
            'working_mechanism': 'Viene pagato un contributo mensile, viene aggiunto il contributo del datore di lavoro e il contributo statale. I risparmi crescono nei fondi pensione. Può essere ritirato dopo 10 anni o all\'età di 56 anni.',
            'examples': 'Allianz Hayat ve Emeklilik, Aegon Emeklilik, AvivaSA'
        },
        'commodity': {
            'title': 'Materia Prima',
            'definition': 'Beni fisici scambiati come oro, argento, petrolio, prodotti agricoli. Usato come riserva di valore e strumento di speculazione.',
            'working_mechanism': 'Le materie prime sono comprate e vendute nei mercati spot o a termine. I prezzi cambiano in base all\'equilibrio domanda-offerta, eventi geopolitici e inflazione.',
            'examples': 'Oro (XAU), Argento (XAG), Petrolio (WTI, Brent), Rame, Grano'
        },
        'debt_securities': {
            'title': 'Titoli di Debito',
            'definition': 'Titoli preziosi emessi da governi o aziende per prendere in prestito denaro. Tipi includono obbligazioni, bills, eurobond.',
            'working_mechanism': 'L\'acquirente di titoli di debito diventa creditore. Alla scadenza, riceve capitale e interesse del coupon. Il rendimento è calcolato in base al tasso del coupon e al tasso di interesse di mercato.',
            'examples': 'Obbligazione governativa, Buono del tesoro, Obbligazione societaria, Eurobond'
        },
        'etf': {
            'title': 'Exchange Traded Fund (ETF)',
            'definition': 'Fondo che segue un indice, comprato e venduto come azioni in borsa. Fornisce basso costo e alta liquidità.',
            'working_mechanism': 'Gli ETF seguono indici (es. S&P 500, BIST 30). Usa gestione algoritmica invece di gestori di fondi. Le commissioni di gestione sono basse.',
            'examples': 'ETF iShares, ETF SPDR, ETF BIST 30'
        },
        'derivative': {
            'title': 'Derivato',
            'definition': 'Strumento finanziario il cui valore è derivato da un altro asset (underlying). Usato per la gestione del rischio e la speculazione.',
            'working_mechanism': 'I derivati possono essere futures, opzioni, swap. Danno diritto o obbligo di comprare/vendere a un prezzo specifico in una data futura.',
            'examples': 'Contratti futures, Contratti opzioni, Transazioni swap'
        },
        'repo': {
            'title': 'Repo',
            'definition': 'Vendita di titoli con impegno di riacquisto a una data di scadenza specifica dalla data della transazione.',
            'working_mechanism': 'Il venditore repo vende titoli e riacquista alla scadenza. La differenza di interesse è profitto/perdita. Usato per la gestione della liquidità a breve termine.',
            'examples': 'Transazioni repo TL, repo USD, repo Euro'
        },
        'leverage': {
            'title': 'Leva',
            'definition': 'Capacità di aprire grandi posizioni con piccolo capitale. Moltiplica rischio e rendimento.',
            'working_mechanism': 'Se la leva è 10, 10.000 TL possono aprire una posizione di 100.000 TL. 1% di aumento dà 10% di rendimento, 1% di diminuzione dà 10% di perdita.',
            'examples': 'Leva Forex (1:10, 1:100), Leva futures, Leva CFD'
        },
        'margin': {
            'title': 'Margine',
            'definition': 'Denaro bloccato come garanzia nelle transazioni con leva. Saldo minimo richiesto per mantenere la posizione.',
            'working_mechanism': 'Se il livello di margine scende, arriva la chiamata di margine (chiamata di garanzia). Se la garanzia è insufficiente, la posizione si chiude automaticamente (stop out).',
            'examples': 'Margine iniziale, margine di mantenimento, chiamata di margine'
        },
        'liquidity': {
            'title': 'Liquidità',
            'definition': 'Velocità e facilità di conversione di un asset in contanti. Gli asset liquidi convertono rapidamente, gli asset illiquidi convertono con difficoltà.',
            'working_mechanism': 'La liquidità è misurata dalla profondità del mercato. Se il volume di trading è alto, la liquidità è alta. In crisi di liquidità, gli asset perdono valore rapidamente.',
            'examples': 'Contanti (più liquido), Azioni (alta liquidità), Immobili (bassa liquidità)'
        },
        'volatility': {
            'title': 'Volatilità',
            'definition': 'Variabilità dei prezzi. Alta volatilità significa che i prezzi cambiano rapidamente, bassa volatilità significa stabilità.',
            'working_mechanism': 'La volatilità è misurata dalla deviazione standard. L\'indice VIX mostra la volatilità del mercato. Alta volatilità significa alto rischio e opportunità.',
            'examples': 'Indice VIX, Volatilità azionaria, Volatilità cripto'
        }
    }
}


def get_dictionary_term(term: str, lang: str = 'tr') -> Dict[str, str]:
    """
    Finansal sözlük terimini döndür

    Args:
        term: Terim anahtarı (örn: 'bank', 'bist', 'bes')
        lang: Dil kodu (varsayılan: 'tr')

    Returns:
        Terim verisi sözlüğü
    """
    try:
        return FINANCIAL_DICTIONARY[lang][term]
    except KeyError:
        # Eğer dil bulunamazsa Türkçe'ye dön
        try:
            return FINANCIAL_DICTIONARY['tr'][term]
        except KeyError:
            # Eğer terim bulunamazsa boş sözlük dön
            return {}


def get_all_dictionary_terms(lang: str = 'tr') -> list:
    """
    Belirli bir dildeki tüm sözlük terimlerini döndür

    Args:
        lang: Dil kodu (varsayılan: 'tr')

    Returns:
        Terim anahtarları listesi
    """
    return list(FINANCIAL_DICTIONARY.get(lang, FINANCIAL_DICTIONARY['tr']).keys())
