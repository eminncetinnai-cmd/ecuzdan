"""Strategy page service layer."""

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from database import get_actual_cash
from market_data_service import get_macro_economic_data

from .strategy_engine import StrategyEngine

if TYPE_CHECKING:
    pass

class StrategyService:
    def __init__(self, financial_repository=None, repository=None):
        self.financial_repository = financial_repository
        self.repository = repository

    def page_context(self, user_id):
        engine = StrategyEngine(user_id)
        assets = self.financial_repository.list_assets()
        total_investable = sum(a.value for a in assets) + get_actual_cash()
        monte_carlo = engine.generate_monte_carlo_paths(total_investable)
        real_yields_data = engine.calculate_real_yields(assets)
        return {
            'mc_scenarios': json.dumps(monte_carlo['scenarios']),
            'mc_success_rates': json.dumps(monte_carlo['success_rates']),
            'active_scenario': monte_carlo['active_scenario'],
            'mc_success_rate': monte_carlo['success_rate'],
            'mc_params': monte_carlo['params'],
            'anomalies': engine.detect_anomalies_advanced(),
            'buckets': engine.optimize_bucket_strategy(assets),
            'real_yields': real_yields_data['assets'],
            'real_yields_data': real_yields_data,
            're_analysis': self._real_estate_analysis(assets),
            'total_investable': total_investable,
            'settings': engine.settings,
            'macro_data': get_macro_economic_data(),
        }

    def get_or_create_settings(self, user_id):
        return self.repository.get_settings_for_user(user_id) or self.repository.create_settings_for_user(user_id)

    def update_settings_from_form(self, user_id, form):
        from shared.decimal_precision import to_decimal
        settings = self.get_or_create_settings(user_id)
        settings.mc_expected_return = to_decimal(form.get('mc_expected_return', 0.15))
        settings.mc_volatility = to_decimal(form.get('mc_volatility', 0.20))
        settings.mc_years = int(form.get('mc_years', 30))
        settings.mc_simulations = int(form.get('mc_simulations', 10000))
        settings.mc_scenario = form.get('mc_scenario', 'balanced')
        settings.annual_inflation = to_decimal(form.get('annual_inflation', 0.40))
        settings.anomaly_sigma_threshold = to_decimal(form.get('anomaly_sigma_threshold', 2.0))
        settings.anomaly_min_samples = int(form.get('anomaly_min_samples', 3))
        settings.bucket_emergency_pct = to_decimal(form.get('bucket_emergency_pct', 0.20))
        settings.bucket_short_term_pct = to_decimal(form.get('bucket_short_term_pct', 0.30))
        settings.bucket_long_term_pct = to_decimal(form.get('bucket_long_term_pct', 0.50))
        settings.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.repository.commit()
        return settings

    def settings_payload(self, settings):
        return {
            'mc_expected_return': settings.mc_expected_return,
            'mc_volatility': settings.mc_volatility,
            'mc_years': settings.mc_years,
            'mc_simulations': settings.mc_simulations,
            'mc_scenario': settings.mc_scenario,
            'annual_inflation': settings.annual_inflation,
            'anomaly_sigma_threshold': settings.anomaly_sigma_threshold,
            'anomaly_min_samples': settings.anomaly_min_samples,
            'bucket_emergency_pct': settings.bucket_emergency_pct,
            'bucket_short_term_pct': settings.bucket_short_term_pct,
            'bucket_long_term_pct': settings.bucket_long_term_pct,
        }

    def _real_estate_analysis(self, assets):
        result = []
        for asset in [a for a in assets if a.type in ['Gayrimenkul', 'Konut', 'Arsa']]:
            monthly_rent = asset.monthly_rent if asset.monthly_rent and asset.monthly_rent > 0 else asset.value / 240
            inflation_rate = 0.40
            inflation_erosion = []
            cumulative_erosion = 0
            for year in range(1, 6):
                annual_erosion = monthly_rent * (inflation_rate / 100)
                cumulative_erosion += annual_erosion
                real_rent = monthly_rent - cumulative_erosion
                inflation_erosion.append({
                    'year': year,
                    'nominal_rent': monthly_rent,
                    'real_rent': max(0, real_rent),
                    'annual_erosion': annual_erosion,
                    'cumulative_erosion': cumulative_erosion,
                })
            result.append({
                'name': asset.name,
                'value': asset.value,
                'monthly_rent': monthly_rent,
                'is_manual': bool(asset.monthly_rent),
                'yield': (monthly_rent * 12 / asset.value) * 100 if asset.value > 0 else 0,
                'inflation_erosion': inflation_erosion,
                'total_5yr_erosion': cumulative_erosion,
            })
        return result
