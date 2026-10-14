"""
Strateji Planı Motor - Dinamik hesaplamalar ve optimizasyonlar
"""

import logging
from datetime import datetime, timedelta

import numpy as np

from database import get_actual_cash
from models import StrategySettings, Transaction
from shared.decimal_precision import to_decimal

logger = logging.getLogger(__name__)


def _to_float(value, default=0.0):
    """
    Decimal → float sınır dönüşümü.

    Monte Carlo ve anomali istatistikleri numpy üzerinde çalışır; numpy
    Decimal ile aritmetik yapamaz (object dtype'a düşer ve `Decimal * float`
    TypeError verir). Bu fonksiyon dönüşümü TEK bir sınırda toplar.

    Buradaki değerler defter tutarı değil, olasılıksal projeksiyondur —
    float hassasiyeti kabul edilebilir. Defter aritmetiği Decimal kalır.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class StrategyEngine:
    """Strateji Planı hesaplamaları için merkezi motor"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.settings = self._get_or_create_settings()

    def _get_or_create_settings(self):
        """Kullanıcının strateji ayarlarını al veya oluştur"""
        from models import db
        settings = StrategySettings.query.filter_by(user_id=self.user_id).first()
        if not settings:
            settings = StrategySettings(user_id=self.user_id)
            db.session.add(settings)
            db.session.commit()
        return settings

    def get_mc_parameters(self):
        """Monte Carlo parametrelerini senaryo tipine göre döndür"""
        scenario_map = {
            'conservative': {'return': 0.08, 'volatility': 0.12},
            'balanced': {'return': 0.15, 'volatility': 0.20},
            'aggressive': {'return': 0.22, 'volatility': 0.30}
        }

        scenario = self.settings.mc_scenario or 'balanced'
        base_params = scenario_map.get(scenario, scenario_map['balanced'])

        # Kullanıcı ayarlarını override et — mu/sigma simülasyon girdisidir, float alanında tutulur.
        return {
            'mu': _to_float(self.settings.mc_expected_return or base_params['return']),
            'sigma': _to_float(self.settings.mc_volatility or base_params['volatility']),
            'years': self.settings.mc_years or 30,
            'simulations': min(self.settings.mc_simulations or 10000, 50000)  # Max 50k
        }

    def _run_single_scenario_sim(self, total_investable, mu, sigma, years, sims, annual_savings, inflation):
        """Tek senaryoyu NumPy vektörleriyle çalıştırıp yüzdelikleri hesaplar.

        Finansal formül değişmez; yalnızca simülasyon ekseni Python döngüsünden
        NumPy matris işlemlerine taşınır. Böylece strateji sayfası 10.000
        simülasyonluk varsayılan ayarda request timeout’a takılmaz.
        """
        mc_array = np.empty((sims, years + 1), dtype=float)
        mc_array[:, 0] = total_investable
        current = np.full(sims, total_investable, dtype=float)
        annual_savings_by_year = annual_savings * ((1 + inflation) ** np.arange(years))
        changes = np.random.normal(
            mu - 0.5 * sigma**2,
            sigma,
            size=(sims, years),
        )

        for year_index in range(years):
            current = current * np.exp(changes[:, year_index])
            current += annual_savings_by_year[year_index]
            mc_array[:, year_index + 1] = np.maximum(current, 0.0)

        percentiles = {'p10': [], 'p50': [], 'p90': []}
        for year_idx in range(years + 1):
            percentiles['p10'].append(float(np.percentile(mc_array[:, year_idx], 10)))
            percentiles['p50'].append(float(np.percentile(mc_array[:, year_idx], 50)))
            percentiles['p90'].append(float(np.percentile(mc_array[:, year_idx], 90)))

        return percentiles, mc_array

    def generate_monte_carlo_paths(self, total_investable):
        """Monte Carlo simülasyon yolları oluştur (3 senaryo için)"""
        # Tasarrufları son 12 ayın gelir/gider hareketlerine göre hesapla
        from datetime import datetime, timedelta

        from models import Transaction
        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        recent_tx = Transaction.query.filter(
            Transaction.date >= twelve_months_ago,
            Transaction.status == 'Ödendi'
        ).all()

        total_income = _to_float(sum(t.amount for t in recent_tx if t.type == 'Gelir'))
        total_expenses = _to_float(sum(t.amount for t in recent_tx if t.type == 'Gider'))
        monthly_savings = max(0.0, (total_income - total_expenses) / 12) if total_income > 0 else 0.0
        annual_savings = monthly_savings * 12

        # GBM simülasyonu float alanında çalışır; girdiler sınırda dönüştürülür.
        total_investable = _to_float(total_investable)
        inflation = _to_float(self.settings.annual_inflation or 0.40)
        years = self.settings.mc_years or 30
        sims = min(self.settings.mc_simulations or 10000, 10000)  # Aşırı yavaşlamayı önlemek için 10.000 ile sınırlı

        scenarios = {
            'conservative': {'mu': 0.08, 'sigma': 0.12},
            'balanced': {'mu': 0.15, 'sigma': 0.20},
            'aggressive': {'mu': 0.22, 'sigma': 0.30}
        }

        # Aktif senaryo ayarlarını al
        active_scenario = self.settings.mc_scenario or 'balanced'
        active_mu = _to_float(self.settings.mc_expected_return or scenarios[active_scenario]['mu'])
        active_sigma = _to_float(self.settings.mc_volatility or scenarios[active_scenario]['sigma'])

        results = {}
        success_rates = {}

        for name, params in scenarios.items():
            # Aktif senaryo ise kullanıcının ayarlarını ez, değilse varsayılanları kullan
            mu = active_mu if name == active_scenario else params['mu']
            sigma = active_sigma if name == active_scenario else params['sigma']

            p_dict, mc_arr = self._run_single_scenario_sim(
                total_investable, mu, sigma, years, sims, annual_savings, inflation
            )
            results[name] = p_dict
            success_rates[name] = self._calculate_success_rate(mc_arr)

        return {
            'scenarios': results,
            'success_rates': success_rates,
            'active_scenario': active_scenario,
            'params': {
                'mu': active_mu,
                'sigma': active_sigma,
                'years': years,
                'simulations': sims
            },
            'success_rate': success_rates[active_scenario]
        }

    def _calculate_success_rate(self, mc_array):
        """Başarı oranını hesapla (hedef değere ulaşan simülasyonların yüzdesi)"""
        if mc_array is None or len(mc_array) == 0:
            return 0.0
        final_values = mc_array[:, -1]
        initial_value = mc_array[0, 0]
        # Hedef: 30 yılda portföy değerini en az 3 katına çıkarmak (maliyet bazlı / reel büyüme)
        success_threshold = initial_value * 3 if initial_value > 0 else 100000.0
        success_rate = (final_values >= success_threshold).sum() / len(final_values) * 100
        return round(success_rate, 2)

    def detect_anomalies_advanced(self):
        """Gelişmiş anomali tespiti (miktar + sıklık)"""
        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        recent_tx = Transaction.query.filter(
            Transaction.date >= twelve_months_ago,
            Transaction.type == 'Gider'
        ).all()

        if not recent_tx:
            return []

        cat_stats = {}
        for t in recent_tx:
            if t.category not in cat_stats:
                cat_stats[t.category] = {'amounts': [], 'dates': []}
            # numpy istatistikleri için sınırda float'a çevrilir (bkz. _to_float).
            cat_stats[t.category]['amounts'].append(_to_float(t.amount))
            cat_stats[t.category]['dates'].append(t.date)

        anomalies = []
        current_month = datetime.now().strftime('%Y-%m')
        sigma_threshold = _to_float(self.settings.anomaly_sigma_threshold or 2.0)
        min_samples = self.settings.anomaly_min_samples or 3

        for cat, data in cat_stats.items():
            amounts = data['amounts']
            if len(amounts) >= min_samples:
                avg = np.mean(amounts)
                std = np.std(amounts)

                # Bu ayki harcama
                this_month_total = sum(t for t, d in zip(amounts, data['dates'])
                                      if d.startswith(current_month))

                # Sıklık anomalisi (bu ay kaç işlem var?)
                this_month_count = sum(1 for d in data['dates'] if d.startswith(current_month))
                avg_monthly_count = len(amounts) / 12

                # Miktar anomalisi
                if this_month_total > (avg + sigma_threshold * std) and std > 0:
                    deviation = (this_month_total - avg) / std
                    anomalies.append({
                        'category': cat,
                        'type': 'amount',
                        'avg': avg,
                        'current': this_month_total,
                        'deviation': deviation,
                        'severity': 'high' if deviation > 3 else 'medium'
                    })

                # Sıklık anomalisi
                if this_month_count > avg_monthly_count * 1.5:
                    anomalies.append({
                        'category': cat,
                        'type': 'frequency',
                        'avg_frequency': avg_monthly_count,
                        'current_frequency': this_month_count,
                        'severity': 'low'
                    })

        return sorted(anomalies, key=lambda x: x.get('deviation', 0), reverse=True)

    def calculate_real_yields(self, assets):
        """Reel getiri hesapla (dinamik enflasyon ile finans uzmanı mantığı)"""
        # Dinamik makroekonomik verileri çek
        # Varlık tutarları (a.value, a.roi) Decimal'dir; makro oranlar da Decimal'e
        # çevrilir ki Fisher denklemi boyunca 'Decimal / float' karışımı oluşmasın.
        try:
            from market_data_service import get_macro_economic_data
            macro_data = get_macro_economic_data()
            annual_inflation = to_decimal(macro_data.get('inflation_rate', 40.0)) / 100
            policy_rate = to_decimal(macro_data.get('interest_rate', 37.0)) / 100
        except Exception as e:
            logger.warning(f"Makro veri çekilemedi, varsayılan değerler kullanılıyor: {e}")
            annual_inflation = to_decimal(self.settings.annual_inflation or 0.40)
            policy_rate = to_decimal(0.37)

        real_yield_assets = []
        portfolio_metrics = {
            'total_nominal_value': 0,
            'total_real_value': 0,
            'weighted_nominal_roi': 0,
            'weighted_real_roi': 0,
            'inflation_burn': 0
        }

        for a in assets:
            if not a.purchase_date:
                continue

            try:
                # Tarih formatını otomatik algıla
                if '/' in a.purchase_date:
                    p_date = datetime.strptime(a.purchase_date, '%d/%m/%Y')
                else:
                    p_date = datetime.strptime(a.purchase_date, '%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Tarih ayrıştırma hatası {a.name}: {e}")
                p_date = datetime.now()

            days_held = (datetime.now() - p_date).days
            years_held = max(to_decimal(days_held) / to_decimal(365.25), to_decimal(0.01))  # En az 0.01 yıl

            # Kümülatif enflasyon (bileşik)
            cum_inflation = (1 + annual_inflation) ** years_held - 1

            # Nominal ROI
            nominal_roi = to_decimal(a.roi) / 100

            # Fisher Denklemi (Reel Getiri)
            real_roi = ((1 + nominal_roi) / (1 + cum_inflation)) - 1

            # Risk-adjusted real return (Basit Sharpe benzeri)
            # Risk seviyesine göre risk premium hesapla
            risk_premium = to_decimal(0)
            if a.risk_level == 'Düşük':
                risk_premium = to_decimal(0.02)  # %2 risk premium
            elif a.risk_level == 'Orta':
                risk_premium = to_decimal(0.05)  # %5 risk premium
            elif a.risk_level == 'Yüksek':
                risk_premium = to_decimal(0.10)  # %10 risk premium

            risk_adjusted_real_roi = real_roi - risk_premium

            # Politika faizine göre performans
            # Nominal getiri politika faizinden ne kadar yüksek/düşük?
            rate_spread = nominal_roi - policy_rate

            # Enflasyon koruması skoru (0-100)
            # Reel getiri pozitifse koruma sağlıyor
            inflation_protection_score = max(to_decimal(0), min(to_decimal(100), (real_roi * 100) * 10))

            # Portföy metriklerini güncelle
            asset_value = to_decimal(a.value)
            portfolio_metrics['total_nominal_value'] += asset_value
            portfolio_metrics['total_real_value'] += asset_value * (1 + real_roi)
            portfolio_metrics['inflation_burn'] += asset_value * cum_inflation

            real_yield_assets.append({
                'name': a.name,
                'type': a.type,
                'nominal_roi': to_decimal(a.roi),
                'real_roi': real_roi * 100,
                'risk_adjusted_real_roi': risk_adjusted_real_roi * 100,
                'inflation_impact': cum_inflation * 100,
                'years_held': round(to_decimal(years_held), 2),
                'rate_spread': rate_spread * 100,
                'inflation_protection_score': round(inflation_protection_score, 1),
                'risk_level': a.risk_level,
                'value': to_decimal(a.value)
            })

        # Portföy düzeyinde metrikleri hesapla
        if assets:
            total_value = sum(to_decimal(a.value) for a in assets)
            if total_value > 0:
                portfolio_metrics['weighted_nominal_roi'] = sum(
                    r['nominal_roi'] * r['value'] for r in real_yield_assets
                ) / total_value
                portfolio_metrics['weighted_real_roi'] = sum(
                    r['real_roi'] * r['value'] for r in real_yield_assets
                ) / total_value

        # Portföy metriklerini sonuçlara ekle
        return {
            'assets': real_yield_assets,
            'portfolio_metrics': portfolio_metrics,
            'macro_context': {
                'annual_inflation': annual_inflation * 100,
                'policy_rate': policy_rate * 100,
                'real_return_rate': (policy_rate - annual_inflation) * 100
            }
        }

    def optimize_bucket_strategy(self, assets):
        """Kova stratejisini dinamik olarak optimize et"""
        total_value = sum(a.value for a in assets) + get_actual_cash()

        # Ayarlardan hedef yüzdeleri al
        emergency_pct = self.settings.bucket_emergency_pct or 0.20
        short_term_pct = self.settings.bucket_short_term_pct or 0.30
        long_term_pct = self.settings.bucket_long_term_pct or 0.50

        buckets = {
            'Acil Durum': {
                'value': 0,
                'assets': [],
                'desc': 'Nakit ve likit varlıklar (0-6 ay)',
                'color': 'emerald',
                'target': total_value * emergency_pct
            },
            'Kısa/Orta Vadeli': {
                'value': 0,
                'assets': [],
                'desc': '1-3 yıl içindeki hedefler',
                'color': 'amber',
                'target': total_value * short_term_pct
            },
            'Uzun Vadeli / Emeklilik': {
                'value': 0,
                'assets': [],
                'desc': '10+ yıl, yüksek büyüme odaklı',
                'color': 'indigo',
                'target': total_value * long_term_pct
            }
        }

        # Varlıkları kovalara dağıt
        for a in assets:
            if a.liquidity == 'Likit' and a.risk_level == 'Düşük':
                buckets['Acil Durum']['value'] += a.value
                buckets['Acil Durum']['assets'].append(a.name)
            elif a.risk_level == 'Yüksek' or a.type in ['Hisse Senedi', 'Kripto Para', 'Yabancı Hisse']:
                buckets['Uzun Vadeli / Emeklilik']['value'] += a.value
                buckets['Uzun Vadeli / Emeklilik']['assets'].append(a.name)
            else:
                buckets['Kısa/Orta Vadeli']['value'] += a.value
                buckets['Kısa/Orta Vadeli']['assets'].append(a.name)

        # Hedef sapması hesapla
        for bucket in buckets.values():
            bucket['deviation'] = bucket['value'] - bucket['target']
            bucket['deviation_pct'] = (bucket['deviation'] / bucket['target'] * 100) if bucket['target'] > 0 else 0

        return buckets

    def validate_and_fix_dates(self, date_str):
        """Tarih stringini doğrula ve standardize et"""
        if not date_str:
            return None

        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        logger.warning(f"Tarih ayrıştırılamadı: {date_str}")
        return None
