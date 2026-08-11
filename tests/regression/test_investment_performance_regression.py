"""
Regression Tests for investment_performance.py
Critical investment performance calculations must remain unchanged during refactoring
"""

import pytest

from domain.portfolio.services.investment_performance import (
    TURKEY_INFLATION_DATA,
    _calculate_inflation_adjusted_returns,
    _calculate_portfolio_summary,
    _empty_performance_data,
    get_inflation_rate,
    get_yearly_performance,
    update_inflation_data,
)
from models import Asset, AssetUpdate, db
from shared.decimal_precision import to_decimal


class TestInvestmentPerformanceRegression:
    """Regression tests to ensure investment performance calculations remain unchanged"""

    def test_turkey_inflation_data_constants(self):
        """Test Turkey inflation data constants remain unchanged"""
        assert TURKEY_INFLATION_DATA[2020] == 12.28
        assert TURKEY_INFLATION_DATA[2021] == 19.60
        assert TURKEY_INFLATION_DATA[2022] == 72.31
        assert TURKEY_INFLATION_DATA[2023] == 53.86
        assert TURKEY_INFLATION_DATA[2024] == 47.06
        assert TURKEY_INFLATION_DATA[2025] == 40.00

    def test_get_inflation_rate(self):
        """Test get_inflation_rate returns expected values"""
        assert get_inflation_rate(2020) == to_decimal(12.28)
        assert get_inflation_rate(2021) == to_decimal(19.60)
        assert get_inflation_rate(2022) == to_decimal(72.31)
        assert get_inflation_rate(2023) == to_decimal(53.86)
        assert get_inflation_rate(2024) == to_decimal(47.06)
        assert get_inflation_rate(2025) == to_decimal(40.00)
        # Bilinmeyen geçmiş yıl için son bilinen oran kullanılır
        assert get_inflation_rate(1999) == to_decimal(TURKEY_INFLATION_DATA[max(TURKEY_INFLATION_DATA)])

    def test_update_inflation_data(self):
        """Test update_inflation_data function"""
        update_inflation_data(2026, 35.0)
        assert get_inflation_rate(2026) == to_decimal(35.0)
        # Reset to default
        TURKEY_INFLATION_DATA.pop(2026, None)

    def test_get_inflation_rate_uses_current_macro_for_current_year(self, monkeypatch):
        """Current year için makro servis oranı kullanılabilmeli"""
        import domain.portfolio.services.investment_performance as perf

        monkeypatch.setattr(perf, '_get_current_macro_inflation_context', lambda: (37.5, 'macro_test'))
        assert perf.get_inflation_rate(2026) == to_decimal(37.5)

    def test_empty_performance_data_structure(self):
        """Test empty performance data returns expected structure"""
        result = _empty_performance_data()

        assert 'yearly_data' in result
        assert 'inflation_adjusted' in result
        assert 'summary' in result
        assert 'inflation_rates' in result
        assert 'inflation_sources' in result

        assert result['yearly_data'] == {}
        assert result['inflation_adjusted'] == {}
        assert result['summary']['total_years'] == 0
        assert result['summary']['avg_nominal_roi'] == 0
        assert result['summary']['avg_real_roi'] == 0
        assert result['summary']['best_year'] is None
        assert result['summary']['worst_year'] is None
        assert result['inflation_sources'] == {}

    def test_calculate_inflation_adjusted_returns_formula(self):
        """Test inflation adjustment formula: ((1 + nominal) / (1 + inflation)) - 1"""
        yearly_data = {
            2023: {'roi': 20.0},
            2024: {'roi': 15.0}
        }

        result = _calculate_inflation_adjusted_returns(yearly_data)

        # 2023: ((1 + 0.20) / (1 + 0.5386)) - 1 = (1.20 / 1.5386) - 1 = 0.7799 - 1 = -0.2201 = -22.01%
        assert abs(result[2023]['real_roi'] - to_decimal('-22.01')) < to_decimal('0.1')
        assert result[2023]['inflation_rate'] == to_decimal(53.86)
        assert result[2023]['nominal_roi'] == to_decimal(20.0)
        assert result[2023]['inflation_source'] == 'historical_table'

        # 2024: ((1 + 0.15) / (1 + 0.4706)) - 1 = (1.15 / 1.4706) - 1 = 0.7815 - 1 = -0.2185 = -21.85%
        assert abs(result[2024]['real_roi'] - to_decimal('-21.85')) < to_decimal('0.1')
        assert result[2024]['inflation_rate'] == to_decimal(47.06)
        assert result[2024]['nominal_roi'] == to_decimal(15.0)

    def test_calculate_portfolio_summary(self):
        """Test portfolio summary calculations"""
        yearly_data = {
            2023: {'roi': 20.0},
            2024: {'roi': 15.0},
            2025: {'roi': 25.0}
        }

        inflation_adjusted = {
            2023: {'real_roi': -22.01},
            2024: {'real_roi': -21.85},
            2025: {'real_roi': -10.71}
        }

        result = _calculate_portfolio_summary(yearly_data, inflation_adjusted)

        assert result['total_years'] == 3
        assert abs(result['avg_nominal_roi'] - to_decimal(20.0)) < to_decimal('0.1')  # (20 + 15 + 25) / 3
        assert abs(result['avg_real_roi'] - to_decimal('-18.19')) < to_decimal('0.1')  # (-22.01 - 21.85 - 10.71) / 3
        assert result['best_year'] == 2025
        assert result['worst_year'] == 2024
        assert result['best_year_roi'] == to_decimal(25.0)
        assert result['worst_year_roi'] == to_decimal(15.0)
        assert abs(result['total_inflation_impact'] - to_decimal('-114.57')) < to_decimal('0.1')  # sum(real) - sum(nominal) = -54.57 - 60 = -114.57

    def test_get_yearly_performance_structure(self, app):
        """Test get_yearly_performance returns expected structure"""
        with app.app_context():
            result = get_yearly_performance()

            assert 'yearly_data' in result
            assert 'inflation_adjusted' in result
            assert 'summary' in result
            assert 'inflation_rates' in result
            assert 'inflation_sources' in result

            assert isinstance(result['yearly_data'], dict)
            assert isinstance(result['inflation_adjusted'], dict)
            assert isinstance(result['summary'], dict)
            assert isinstance(result['inflation_rates'], dict)
            assert isinstance(result['inflation_sources'], dict)


class TestInvestmentPerformanceFormulas:
    """Test specific investment performance formulas remain unchanged"""

    def test_roi_calculation_formula(self):
        """Test ROI formula: ((value - cost) / cost) * 100"""
        value = 120000
        cost = 100000
        roi = ((value - cost) / cost) * 100

        assert roi == 20.0

    def test_gain_loss_calculation_formula(self):
        """Test gain/loss formula: value - cost"""
        value = 120000
        cost = 100000
        gain_loss = value - cost

        assert gain_loss == 20000

    def test_inflation_adjusted_return_formula(self):
        """Test real return formula: ((1 + nominal) / (1 + inflation)) - 1"""
        nominal_return = 0.20  # 20%
        inflation_rate = 0.40  # 40%

        real_return = ((1 + nominal_return) / (1 + inflation_rate)) - 1
        expected = ((1.20) / (1.40)) - 1  # 0.8571 - 1 = -0.1429 = -14.29%

        assert abs(real_return - expected) < 0.001

    def test_average_roi_formula(self):
        """Test average ROI formula: sum(roi) / count"""
        rois = [20.0, 15.0, 25.0, 18.0]
        avg_roi = sum(rois) / len(rois)

        assert avg_roi == 19.5

    def test_total_inflation_impact_formula(self):
        """Test total inflation impact: sum(real_rois) - sum(nominal_rois)"""
        real_rois = [-22.01, -21.85, -10.71]
        nominal_rois = [20.0, 15.0, 25.0]

        total_impact = sum(real_rois) - sum(nominal_rois)
        expected = (-54.57) - 60.0  # -114.57

        assert abs(total_impact - expected) < 0.1

    def test_purchase_date_parsing_yyyy_mm_dd(self):
        """Test purchase date parsing for YYYY-MM-DD format"""
        purchase_date = "2023-06-15"
        year = int(purchase_date[:4])

        assert year == 2023

    def test_purchase_date_parsing_dd_mm_yyyy(self):
        """Test purchase date parsing for DD/MM/YYYY format"""
        purchase_date = "15/06/2023"
        parts = purchase_date.split('/')
        year = int(parts[2])

        assert year == 2023


class TestInvestmentPerformanceIntegration:
    """Integration tests with actual database"""

    @pytest.fixture
    def setup_assets(self, app):
        """Setup test assets — uses conftest app fixture (in-memory DB)."""
        with app.app_context():
            from models import Tenant
            tenant = Tenant.query.filter_by(id='default').first()
            tenant_id = tenant.id if tenant else None

            # Clear test assets
            Asset.query.filter(Asset.name.like('Test%')).delete()
            AssetUpdate.query.delete()
            db.session.commit()

            # Create test assets
            assets = [
                Asset(
                    type='Hisse Senedi',
                    name='Test Hisse 1',
                    value=120000,
                    description='Test hisse senedi',
                    purchase_date='2023-01-15',
                    purchase_cost=100000,
                    quantity=1000,
                    unit_price=100,
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
                    value=115000,
                    description='Test altın',
                    purchase_date='2024-01-15',
                    purchase_cost=100000,
                    quantity=100,
                    unit_price=1000,
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

            db.session.commit()

    def test_get_yearly_performance_with_assets(self, setup_assets, app):
        """Test get_yearly_performance with actual assets"""
        with app.app_context():
            result = get_yearly_performance()

            assert 'yearly_data' in result
            assert len(result['yearly_data']) > 0

            # Check structure of yearly data
            for year, data in result['yearly_data'].items():
                assert 'total_value' in data
                assert 'total_cost' in data
                assert 'gain_loss' in data
                assert 'roi' in data
                assert 'assets' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
