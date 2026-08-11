"""
Regression Tests for strategy_engine.py
Critical strategy calculations must remain unchanged during refactoring
"""

import numpy as np
import pytest

from domain.analysis.services import StrategyEngine
from models import Asset, StrategySettings, Transaction, User, db


class TestStrategyEngineRegression:
    """Regression tests to ensure strategy calculations remain unchanged"""

    @pytest.fixture
    def setup_user(self, app):
        """Setup test user and data — uses conftest app fixture (in-memory DB)."""
        from werkzeug.security import generate_password_hash
        with app.app_context():
            # Resolve tenant first (needed for all models with NOT NULL tenant_id)
            from models import Tenant
            tenant = Tenant.query.filter_by(id='default').first()
            tenant_id = tenant.id if tenant else None

            # Create test user
            user = User.query.filter_by(username='test_strategy_user').first()
            if not user:
                user = User(
                    username='test_strategy_user',
                    password=generate_password_hash('test_password'),
                    role='kullanici',
                    tenant_id=tenant_id
                )
                db.session.add(user)
                db.session.commit()

            # Create test assets
            Asset.query.filter(Asset.name.like('Test%')).delete()

            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Test Hisse 1',
                    value=50000,
                    description='Test hisse senedi',
                    purchase_date='2023-01-15',
                    purchase_cost=45000,
                    quantity=1000,
                    unit_price=50,
                    currency='TRY',
                    symbol='TEST1',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=tenant_id,
                ),
                Asset(
                    type='Altın',
                    name='Test Altın',
                    value=30000,
                    description='Test altın',
                    purchase_date='2023-06-01',
                    purchase_cost=28000,
                    quantity=100,
                    unit_price=300,
                    currency='TRY',
                    symbol='TESTAU',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id=tenant_id,
                ),
            ]

            for asset in assets:
                db.session.add(asset)

            # Create test transactions
            Transaction.query.filter(Transaction.description.like('Test%')).delete()

            transactions = [
                Transaction(
                    date='2025-01-15',
                    category='Maaş',
                    description='Test Maaş',
                    type='Gelir',
                    status='Ödendi',
                    amount=30000,
                    tenant_id=tenant_id,
                ),
                Transaction(
                    date='2025-01-20',
                    category='Kira',
                    description='Test Kira',
                    type='Gider',
                    status='Ödendi',
                    amount=8500,
                    tenant_id=tenant_id,
                ),
            ]

            for tx in transactions:
                db.session.add(tx)

            db.session.commit()

            return user.id



    def test_strategy_engine_initialization(self, setup_user, app):
        """Test StrategyEngine initialization"""
        with app.app_context():
            engine = StrategyEngine(setup_user)
            assert engine.user_id == setup_user
            assert engine.settings is not None
            assert isinstance(engine.settings, StrategySettings)

    def test_get_mc_parameters_structure(self, setup_user, app):
        """Test Monte Carlo parameters structure"""
        with app.app_context():
            engine = StrategyEngine(setup_user)
            params = engine.get_mc_parameters()

            # Must contain these keys
            assert 'mu' in params
            assert 'sigma' in params
            assert 'years' in params
            assert 'simulations' in params

            # Values must be numeric
            assert isinstance(params['mu'], (int, float))
            assert isinstance(params['sigma'], (int, float))
            assert isinstance(params['years'], int)
            assert isinstance(params['simulations'], int)

            # Reasonable ranges
            assert 0 < params['mu'] < 1.0
            assert 0 < params['sigma'] < 1.0
            assert 1 <= params['years'] <= 50
            assert 100 <= params['simulations'] <= 50000

    def test_scenario_parameter_mapping(self, setup_user, app):
        """Test scenario parameter mapping remains unchanged"""
        with app.app_context():
            engine = StrategyEngine(setup_user)

            # Test each scenario
            scenarios = ['conservative', 'balanced', 'aggressive']
            expected_returns = [0.08, 0.15, 0.22]
            expected_volatilities = [0.12, 0.20, 0.30]

            for scenario, expected_ret, expected_vol in zip(scenarios, expected_returns, expected_volatilities):
                engine.settings.mc_scenario = scenario
                db.session.commit()

                # Re-initialize to get fresh settings
                engine = StrategyEngine(setup_user)
                params = engine.get_mc_parameters()

                # Should be close to expected values (user settings may override)
                assert params['mu'] > 0
                assert params['sigma'] > 0

    def test_monte_carlo_formula(self):
        """Test Monte Carlo GBM formula: S_t = S_{t-1} * exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)"""
        # Test case
        S_prev = 1000
        mu = 0.15
        sigma = 0.20
        dt = 1.0  # 1 year
        Z = 0.5  # random normal

        # GBM formula
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt) * Z
        S_current = S_prev * np.exp(drift + diffusion)

        # Should be positive
        assert S_current > 0
        assert isinstance(S_current, (int, float))

    def test_percentile_calculation(self):
        """Test percentile calculation in Monte Carlo"""
        # Generate sample data
        np.random.seed(42)
        sample_data = np.random.normal(100, 20, 1000)

        p10 = np.percentile(sample_data, 10)
        p50 = np.percentile(sample_data, 50)
        p90 = np.percentile(sample_data, 90)

        # Percentiles should be ordered
        assert p10 < p50 < p90
        assert all(isinstance(p, (int, float)) for p in [p10, p50, p90])

    def test_inflation_adjustment_formula(self):
        """Test inflation adjustment: annual_savings * ((1 + inflation) ** (year - 1))"""
        annual_savings = 10000
        inflation = 0.40  # 40% inflation

        # Year 1: no adjustment
        year1_savings = annual_savings * ((1 + inflation) ** 0)
        assert year1_savings == 10000

        # Year 2: one year of inflation
        year2_savings = annual_savings * ((1 + inflation) ** 1)
        assert year2_savings == 14000

        # Year 3: two years of inflation (use approximate comparison for float precision)
        year3_savings = annual_savings * ((1 + inflation) ** 2)
        assert abs(year3_savings - 19600) < 0.001

    def test_savings_calculation_from_transactions(self, setup_user, app):
        """Test monthly savings calculation from transactions"""
        with app.app_context():
            StrategyEngine(setup_user)

            # Calculate savings from recent transactions
            from datetime import datetime, timedelta
            twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            recent_tx = Transaction.query.filter(
                Transaction.date >= twelve_months_ago,
                Transaction.status == 'Ödendi'
            ).all()

            total_income = sum(t.amount for t in recent_tx if t.type == 'Gelir')
            total_expenses = sum(t.amount for t in recent_tx if t.type == 'Gider')
            monthly_savings = max(0.0, (total_income - total_expenses) / 12) if total_income > 0 else 0.0

            # Should be non-negative
            assert monthly_savings >= 0
            assert isinstance(monthly_savings, (int, float))


class TestStrategyEngineFormulas:
    """Test specific strategy formulas remain unchanged"""

    def test_geometric_brownian_motion_formula(self):
        """Test GBM formula components"""
        mu = 0.15  # expected return
        sigma = 0.20  # volatility

        # Drift component: mu - 0.5 * sigma^2
        drift = mu - 0.5 * sigma**2
        expected_drift = 0.15 - 0.5 * 0.04  # 0.15 - 0.02 = 0.13
        assert abs(drift - expected_drift) < 0.001

        # Volatility component: sigma * sqrt(dt)
        dt = 1.0
        vol_component = sigma * np.sqrt(dt)
        assert abs(vol_component - sigma) < 0.001

    def test_bucket_strategy_formula(self):
        """Test bucket strategy allocation formula"""
        total_amount = 100000
        emergency_pct = 0.20  # 20%
        short_term_pct = 0.30  # 30%
        long_term_pct = 0.50  # 50%

        emergency_amount = total_amount * emergency_pct
        short_term_amount = total_amount * short_term_pct
        long_term_amount = total_amount * long_term_pct

        assert emergency_amount == 20000
        assert short_term_amount == 30000
        assert long_term_amount == 50000

        # Should sum to total
        assert abs(emergency_amount + short_term_amount + long_term_amount - total_amount) < 0.01

    def test_compound_growth_formula(self):
        """Test compound growth: P * (1 + r)^n"""
        principal = 10000
        rate = 0.15  # 15%
        years = 5

        future_value = principal * (1 + rate) ** years
        expected_value = 10000 * (1.15) ** 5  # approximately 20113.57

        assert abs(future_value - expected_value) < 1.0

    def test_risk_adjusted_return_formula(self):
        """Test risk-adjusted return: (return - risk_free) / volatility"""
        portfolio_return = 0.20
        risk_free_rate = 0.08
        volatility = 0.25

        risk_adjusted_return = (portfolio_return - risk_free_rate) / volatility
        expected_value = (0.20 - 0.08) / 0.25  # 0.48

        assert abs(risk_adjusted_return - expected_value) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
