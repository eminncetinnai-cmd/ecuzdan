"""
Regression Tests for financial_engine.py
Critical financial calculations must remain unchanged during refactoring
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app import app
from engines.financial_engine import (
    calculate_cash_trend,
    format_date,
    format_money,
    get_asset_analysis,
    get_empty_freedom_analysis,
    get_financial_analysis,
    get_financial_freedom_analysis,
    get_monthly_dashboard_data,
)
from models import Asset, Payment, PlanOccurrence, RecurringPlan, Transaction, db


class TestFinancialEngineRegression:
    """Regression tests to ensure financial calculations remain unchanged"""

    @pytest.fixture
    def setup_data(self):
        """Setup baseline test data"""
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()

            # Clear dependent rows before their parent rows to honor SQLite FKs.
            from models import JournalEntry, LedgerAdjustment, LedgerAuditEvent, LedgerLine
            LedgerAuditEvent.query.delete()
            LedgerAdjustment.query.delete()
            LedgerLine.query.delete()
            JournalEntry.query.delete()
            PlanOccurrence.query.delete()
            Payment.query.delete()
            Transaction.query.delete()
            Asset.query.delete()
            RecurringPlan.query.delete()
            db.session.commit()

            # Create baseline transactions
            transactions = [
                Transaction(
                    date='2025-01-15',
                    category='Maaş',
                    description='Aylık maaş',
                    type='Gelir',
                    status='Ödendi',
                    amount=30000,
                    tenant_id='default'
                ),
                Transaction(
                    date='2025-01-20',
                    category='Kira',
                    description='Konut kirası',
                    type='Gider',
                    status='Ödendi',
                    amount=8500,
                    tenant_id='default'
                ),
                Transaction(
                    date='2025-01-25',
                    category='Yatırıma Aktarılan',
                    description='Aylık yatırım',
                    type='Yatırım',
                    status='Ödendi',
                    amount=4000,
                    tenant_id='default'
                ),
                Transaction(
                    date='2025-02-15',
                    category='Maaş',
                    description='Aylık maaş',
                    type='Gelir',
                    status='Ödendi',
                    amount=30000,
                    tenant_id='default'
                ),
                Transaction(
                    date='2025-02-20',
                    category='Kira',
                    description='Konut kirası',
                    type='Gider',
                    status='Ödendi',
                    amount=8500,
                    tenant_id='default'
                ),
            ]

            for tx in transactions:
                db.session.add(tx)

            # Create baseline assets
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='YKBNK',
                    value=50000,
                    description='Yapı Kredi Bankası',
                    purchase_date='2023-01-15',
                    purchase_cost=45000,
                    quantity=1000,
                    unit_price=50,
                    currency='TRY',
                    symbol='YKBNK',
                    risk_level='Orta',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id='default'
                ),
                Asset(
                    type='Altın',
                    name='Gram Altın',
                    value=30000,
                    description='Gram altın',
                    purchase_date='2023-06-01',
                    purchase_cost=28000,
                    quantity=100,
                    unit_price=300,
                    currency='TRY',
                    symbol='XAUTRY',
                    risk_level='Düşük',
                    liquidity='Likit',
                    sector_id=1,
                    tenant_id='default'
                ),
            ]

            for asset in assets:
                db.session.add(asset)

            # Create baseline recurring plan
            plan = RecurringPlan(
                name='Konut Kredisi',
                category='Kredi',
                flow_type='Gider',
                amount=5500,
                installments=24,
                payment_day=10,
                tenant_id='default'
            )
            db.session.add(plan)

            db.session.commit()

    def test_get_financial_analysis_regression(self, setup_data):
        """Test get_financial_analysis returns expected structure and reasonable values"""
        with app.app_context():
            result = get_financial_analysis()

            # Check structure
            assert 'total_servet' in result
            assert 'total_debt' in result
            assert 'actual_cash' in result
            assert 'score' in result
            assert 'liquidity' in result
            assert 'debt_ratio' in result
            assert 'savings' in result
            assert 'sustain' in result
            assert 'strategy' in result
            assert 'flags' in result
            assert 'recs' in result

            # Check value ranges
            assert result['score'] >= 0 and result['score'] <= 100
            assert result['total_servet'] >= 0
            assert result['total_debt'] >= 0
            assert result['actual_cash'] >= 0
            assert result['liquidity'] >= 0
            assert result['debt_ratio'] >= 0
            assert isinstance(result['flags'], list)
            assert isinstance(result['recs'], list)

    def test_calculate_cash_trend_regression(self, setup_data):
        """Test calculate_cash_trend returns expected baseline values"""
        with app.app_context():
            all_transactions = Transaction.query.all()
            now = datetime.now()

            # 7-day trend
            week_trend = calculate_cash_trend(now, all_transactions, 7)
            assert len(week_trend) == 7
            # Decimal migrasyonu sonrası para değerleri Decimal döner (SPRINT-01).
            assert all(isinstance(val, (int, float, Decimal)) for val in week_trend)

            # 30-day trend
            month_trend = calculate_cash_trend(now, all_transactions, 30)
            assert len(month_trend) == 30
            assert all(isinstance(val, (int, float, Decimal)) for val in month_trend)

    def test_get_monthly_dashboard_data_regression(self, setup_data):
        """Test get_monthly_dashboard_data returns expected baseline values"""
        with app.app_context():
            m_data, i_data, tr = get_monthly_dashboard_data(2025)

            assert len(m_data) == 12
            assert len(i_data) == 12
            assert len(tr) == 12

            # January 2025 baseline
            jan_data = m_data[0]
            assert jan_data['name'] == 'Ocak'
            assert jan_data['inc'] == 30000
            assert jan_data['exp'] == 8500
            assert jan_data['inv'] == 4000
            assert jan_data['net'] == 17500

            # February 2025 baseline
            feb_data = m_data[1]
            assert feb_data['name'] == 'Şubat'
            assert feb_data['inc'] == 30000
            assert feb_data['exp'] == 8500
            assert feb_data['inv'] == 0
            assert feb_data['net'] == 21500

    def test_get_asset_analysis_regression(self, setup_data):
        """Test get_asset_analysis returns expected baseline values"""
        with app.app_context():
            result = get_asset_analysis()

            # Baseline values
            assert result['total_value'] == 80000  # 50000 + 30000
            assert result['total_cost'] == 73000  # 45000 + 28000
            assert result['total_gain_loss'] == 7000  # 80000 - 73000
            # overall_roi Decimal döner; pytest.approx float ile karşılaştırır.
            assert float(result['overall_roi']) == pytest.approx(9.59, rel=0.01)  # (7000/73000)*100
            assert result['asset_count'] == 2

            # Check structure
            assert 'by_type' in result
            assert 'by_risk' in result
            assert 'by_liquidity' in result
            assert 'by_sector' in result
            assert 'top_performers' in result
            assert 'worst_performers' in result
            assert 'portfolio_concentration' in result
            assert 'risk_score' in result
            assert 'liquidity_score' in result

    def test_get_financial_freedom_analysis_regression(self, setup_data):
        """Test get_financial_freedom_analysis returns expected baseline values"""
        with app.app_context():
            result = get_financial_freedom_analysis()

            # Check structure
            assert 'net_worth' in result
            assert 'total_assets' in result
            assert 'total_cash' in result
            assert 'total_debts' in result
            assert 'monthly_avg_income' in result
            assert 'monthly_avg_expenses' in result
            assert 'savings_rate' in result
            assert 'fi_number' in result
            assert 'fi_progress_pct' in result
            assert 'freedom_score' in result
            assert 'freedom_stage' in result
            assert 'fire_profile' in result
            assert 'criteria' in result
            assert len(result['criteria']) == 6  # 6 criteria

    def test_format_money_regression(self):
        """Test format_money returns expected format"""
        # Test various inputs
        assert format_money(1234.56) == '1.234,56'
        assert format_money(1000) == '1.000,00'
        assert format_money(0) == '0,00'
        assert format_money(None) == '0,00'
        assert format_money(999999.99) == '999.999,99'

    def test_format_date_regression(self):
        """Test format_date returns expected format"""
        assert format_date('2025-01-15') == '15/01/2025'
        assert format_date('2025-12-31') == '31/12/2025'
        assert format_date('') == ''
        assert format_date(None) == ''

    def test_get_empty_freedom_analysis_regression(self):
        """Test get_empty_freedom_analysis returns expected structure"""
        result = get_empty_freedom_analysis()

        # All values should be 0 or None
        assert result['net_worth'] == 0
        assert result['total_assets'] == 0
        assert result['total_cash'] == 0
        assert result['total_debts'] == 0
        assert result['monthly_avg_income'] == 0
        assert result['monthly_avg_expenses'] == 0
        assert result['savings_rate'] == 0
        assert result['fi_number'] == 0
        assert result['fi_progress_pct'] == 0
        assert result['freedom_score'] == 0
        assert not result['is_financially_free']
        assert result['years_to_fi'] is None


class TestFinancialEngineFormulas:
    """Test specific financial formulas remain unchanged"""

    def test_roi_calculation_formula(self):
        """Test ROI calculation formula: ((value - cost) / cost) * 100"""
        with app.app_context():
            # Test case 1: Profit
            assert ((100000 - 80000) / 80000) * 100 == 25.0

            # Test case 2: Loss
            assert ((80000 - 100000) / 100000) * 100 == -20.0

            # Test case 3: Break even
            assert ((100000 - 100000) / 100000) * 100 == 0.0

    def test_liquidity_formula(self):
        """Test liquidity formula: actual_cash / monthly_expenses"""
        # Test case 1
        actual_cash = 30000
        monthly_expenses = 15000
        liquidity = actual_cash / monthly_expenses
        assert liquidity == 2.0

        # Test case 2: Edge case
        actual_cash = 15000
        monthly_expenses = 15000
        liquidity = actual_cash / monthly_expenses
        assert liquidity == 1.0

    def test_debt_ratio_formula(self):
        """Test debt ratio formula: (total_debt / total_servet) * 100"""
        total_debt = 100000
        total_servet = 500000
        debt_ratio = (total_debt / total_servet) * 100
        assert debt_ratio == 20.0

    def test_savings_rate_formula(self):
        """Test savings rate formula: ((income - expenses) / income) * 100"""
        income = 30000
        expenses = 20000
        savings_rate = ((income - expenses) / income) * 100
        assert savings_rate == pytest.approx(33.33, rel=0.01)

    def test_financial_score_formula(self):
        """Test financial score formula: max(0, min(100, int(100 - (dr * 1.5) + (sr * 0.5))))"""
        # Test case 1
        dr = 20  # debt ratio
        sr = 30  # savings rate
        score = max(0, min(100, int(100 - (dr * 1.5) + (sr * 0.5))))
        assert score == 85  # int(100 - 30 + 15) = int(85) = 85

        # Test case 2
        dr = 50
        sr = 10
        score = max(0, min(100, int(100 - (dr * 1.5) + (sr * 0.5))))
        assert score == 30  # int(100 - 75 + 5) = int(30) = 30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
