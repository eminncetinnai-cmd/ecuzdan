"""Strategy page service layer."""

import json
import threading
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from database import get_actual_cash
from market_data_service import get_macro_economic_data
from models import User, db

from .strategy_engine import StrategyEngine

if TYPE_CHECKING:
    pass

_STRATEGY_CACHE = {}
_STRATEGY_CACHE_LOCK = threading.Lock()
STRATEGY_CACHE_TTL = 300  # 5 minutes


def invalidate_strategy_cache(user_id=None):
    """Purge cached strategy context for a specific user or all users."""
    with _STRATEGY_CACHE_LOCK:
        if user_id is None:
            _STRATEGY_CACHE.clear()
        else:
            _STRATEGY_CACHE.pop(user_id, None)


class StrategyService:
    def __init__(self, financial_repository=None, repository=None):
        self.financial_repository = financial_repository
        self.repository = repository

    def invalidate_cache(self, user_id=None):
        invalidate_strategy_cache(user_id)

    def page_context(self, user_id, force_refresh=False):
        now = time.time()
        if not force_refresh:
            with _STRATEGY_CACHE_LOCK:
                cached = _STRATEGY_CACHE.get(user_id)
                if cached and (now - cached['time'] < STRATEGY_CACHE_TTL):
                    return cached['data'].copy()

        engine = StrategyEngine(user_id)
        assets = self.financial_repository.list_assets()
        total_investable = sum(a.value for a in assets) + get_actual_cash()
        monte_carlo = engine.generate_monte_carlo_paths(total_investable)
        real_yields_data = engine.calculate_real_yields(assets)
        try:
            macro_data = get_macro_economic_data(allow_network=False)
        except TypeError:
            macro_data = get_macro_economic_data()
        context = {
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
            'macro_data': macro_data,
        }

        with _STRATEGY_CACHE_LOCK:
            _STRATEGY_CACHE[user_id] = {
                'time': now,
                'data': context,
            }

        return context


    def _tenant_id_for_user(self, user_id):
        user = db.session.get(User, user_id)
        if not user or not user.tenant_id:
            raise ValueError('Authenticated user has no tenant context')
        return user.tenant_id

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
        invalidate_strategy_cache(user_id)
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
        from shared.decimal_precision import to_decimal
        result = []
        for asset in [a for a in assets if a.type in ['Gayrimenkul', 'Konut', 'Arsa']]:
            val = to_decimal(asset.value or 0)
            monthly_rent = to_decimal(asset.monthly_rent) if asset.monthly_rent and asset.monthly_rent > 0 else (val / 240 if val > 0 else to_decimal(0))
            inflation_rate = to_decimal("0.40")
            inflation_erosion = []
            cumulative_erosion = to_decimal(0)
            for year in range(1, 6):
                annual_erosion = monthly_rent * (inflation_rate / 100)
                cumulative_erosion += annual_erosion
                real_rent = monthly_rent - cumulative_erosion
                inflation_erosion.append({
                    'year': year,
                    'nominal_rent': monthly_rent,
                    'real_rent': max(to_decimal(0), real_rent),
                    'annual_erosion': annual_erosion,
                    'cumulative_erosion': cumulative_erosion,
                })
            asset_yield = (monthly_rent * 12 / val) * 100 if val > 0 else to_decimal(0)
            result.append({
                'name': asset.name,
                'value': val,
                'monthly_rent': monthly_rent,
                'is_manual': bool(asset.monthly_rent),
                'yield': asset_yield,
                'inflation_erosion': inflation_erosion,
                'total_5yr_erosion': cumulative_erosion,
            })
        return result
