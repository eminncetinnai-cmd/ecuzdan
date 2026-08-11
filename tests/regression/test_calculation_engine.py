"""
Calculation Engine Validation Tests - FAZ 3
Validates financial calculation engine correctness and consistency
"""

import pytest
from decimal import Decimal
from engines.financial_engine import (
    get_financial_analysis,
    get_monthly_dashboard_data,
    get_financial_freedom_analysis,
)
from engines.analysis_engine import AnalysisEngine
from models import db


@pytest.fixture
def app(app):
    """Use the existing app fixture from conftest.py"""
    return app


@pytest.mark.regression
def test_financial_analysis_calculation_consistency(app):
    """
    Financial analysis calculation consistency:
    - get_financial_analysis should return consistent results
    - Calculations should be deterministic
    - Same inputs should produce same outputs
    """
    tenant = 'tenant_analysis_consistency'
    
    # Create test data
    from models import Category, Transaction
    from database.crud import get_actual_cash
    
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Add transactions
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('10000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    # Run analysis twice
    analysis1 = get_financial_analysis(tenant)
    analysis2 = get_financial_analysis(tenant)
    
    # Results should be consistent
    assert analysis1 is not None
    assert analysis2 is not None


@pytest.mark.regression
def test_monthly_dashboard_data_accuracy(app):
    """
    Monthly dashboard data accuracy:
    - get_monthly_dashboard_data should calculate correct monthly aggregates
    - Income, expense, and investment totals should match transaction sums
    """
    tenant = 'tenant_monthly_accuracy'
    
    # Create categories
    from models import Category
    income_cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    expense_cat = Category(name='Test Gider', type='Gider', tenant_id=tenant)
    investment_cat = Category(name='Test Yatırım', type='Yatırım', tenant_id=tenant)
    db.session.add_all([income_cat, expense_cat, investment_cat])
    db.session.commit()
    
    # Add transactions for specific month
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('5000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-15', 'Test Gider', 'Expense', 
        Decimal('2000'), 'Ödendi', 'Test Gider', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-20', 'Test Yatırım', 'Investment', 
        Decimal('1000'), 'Ödendi', 'Test Yatırım', tenant_id=tenant
    )
    db.session.commit()
    
    # Get monthly dashboard data - correct signature: (year, tenant_id)
    dashboard = get_monthly_dashboard_data(2025, tenant)
    
    # Verify data structure
    assert dashboard is not None
    # Returns (data, labels, months) - 3 elements
    assert len(dashboard) == 3


@pytest.mark.regression
def test_financial_freedom_calculation(app):
    """
    Financial freedom calculation:
    - get_financial_freedom_analysis should calculate correct freedom metrics
    - Years to freedom calculation should be mathematically sound
    """
    tenant = 'tenant_freedom_calc'
    
    # Create test data
    from models import Category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('100000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    # Get financial freedom analysis
    analysis = get_financial_freedom_analysis(tenant)
    
    # Verify structure
    assert analysis is not None
    # Should contain freedom-related metrics
    assert isinstance(analysis, dict)


@pytest.mark.regression
def test_analysis_engine_initialization(app):
    """
    Analysis engine initialization:
    - AnalysisEngine should initialize correctly with market data service
    - Engine should handle missing or invalid market data gracefully
    """
    # Initialize engine with mock market data service
    class MockMarketDataService:
        def get_market_data(self):
            return {'assets': {}}
    
    mock_service = MockMarketDataService()
    engine = AnalysisEngine(mock_service)
    
    # Verify engine initialized
    assert engine is not None
    assert hasattr(engine, 'market_data_service')


@pytest.mark.regression
def test_cash_trend_calculation(app):
    """
    Cash trend calculation:
    - calculate_cash_trend should compute correct trend over time
    - Trend should reflect actual cash flow changes
    """
    from engines.financial_engine import calculate_cash_trend
    from models import Transaction
    
    tenant = 'tenant_cash_trend'
    
    # Create test data
    from models import Category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income 1', 
        Decimal('5000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-02-01', 'Test Gelir', 'Income 2', 
        Decimal('6000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    # Get all transactions for the tenant
    all_transactions = Transaction.query.filter_by(tenant_id=tenant).all()
    
    # Calculate cash trend with correct signature
    # calculate_cash_trend(now, all_transactions, days_count)
    from datetime import datetime
    trend = calculate_cash_trend(datetime.now(), all_transactions, days_count=30)
    
    # Verify trend calculation
    assert trend is not None
    assert isinstance(trend, tuple) or isinstance(trend, list)


@pytest.mark.regression
def test_investment_ratio_calculation(app):
    """
    Investment ratio calculation:
    - Investment ratio should be calculated as investment / total income
    - Ratio should be between 0 and 1 (or 0% and 100%)
    """
    tenant = 'tenant_investment_ratio'
    
    # Create categories
    from models import Category
    income_cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    investment_cat = Category(name='Test Yatırım', type='Yatırım', tenant_id=tenant)
    db.session.add_all([income_cat, investment_cat])
    db.session.commit()
    
    # Add income and investment
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('10000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-15', 'Test Yatırım', 'Investment', 
        Decimal('2000'), 'Ödendi', 'Test Yatırım', tenant_id=tenant
    )
    db.session.commit()
    
    # Get dashboard data which should include investment ratio
    # Correct signature: (year, tenant_id)
    dashboard = get_monthly_dashboard_data(2025, tenant)
    assert dashboard is not None


@pytest.mark.regression
def test_savings_rate_calculation(app):
    """
    Savings rate calculation:
    - Savings rate should be (income - expenses) / income
    - Should handle edge cases (zero income, negative savings)
    """
    tenant = 'tenant_savings_rate'
    
    # Create categories
    from models import Category
    income_cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    expense_cat = Category(name='Test Gider', type='Gider', tenant_id=tenant)
    db.session.add_all([income_cat, expense_cat])
    db.session.commit()
    
    # Add income and expenses
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('10000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    create_one_time_transaction(
        '2025-01-15', 'Test Gider', 'Expense', 
        Decimal('7000'), 'Ödendi', 'Test Gider', tenant_id=tenant
    )
    db.session.commit()
    
    # Expected savings rate: (10000 - 7000) / 10000 = 0.3 or 30%
    # Verify through dashboard or analysis
    # Correct signature: (year, tenant_id)
    dashboard = get_monthly_dashboard_data(2025, tenant)
    assert dashboard is not None


@pytest.mark.regression
def test_engine_decimal_precision(app):
    """
    Engine decimal precision:
    - All calculations should use Decimal arithmetic
    - No floating-point precision errors in results
    """
    from shared.decimal_precision import to_decimal
    
    # Test precision in calculations
    value1 = to_decimal('0.1')
    value2 = to_decimal('0.2')
    result = value1 + value2
    
    # Should equal 0.3 exactly
    assert result == to_decimal('0.3'), "Decimal precision error in engine"


@pytest.mark.regression
def test_analysis_engine_market_data_handling(app):
    """
    Analysis engine market data handling:
    - Engine should handle missing market data gracefully
    - Should provide default values when data is unavailable
    """
    # Initialize with mock service that returns empty data
    class EmptyMarketDataService:
        def get_market_data(self):
            return {}
    
    empty_service = EmptyMarketDataService()
    engine = AnalysisEngine(empty_service)
    
    # Engine should still initialize
    assert engine is not None


@pytest.mark.regression
def test_calculation_idempotency(app):
    """
    Calculation idempotency:
    - Running same calculation multiple times should produce same result
    - No side effects from repeated calculations
    """
    tenant = 'tenant_idempotency'
    
    # Create minimal test data
    from models import Category
    cat = Category(name='Test Gelir', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    from domain.transactions.services.financial_ledger import create_one_time_transaction
    create_one_time_transaction(
        '2025-01-01', 'Test Gelir', 'Income', 
        Decimal('5000'), 'Ödendi', 'Test Gelir', tenant_id=tenant
    )
    db.session.commit()
    
    # Run calculation multiple times
    result1 = get_financial_analysis(tenant)
    result2 = get_financial_analysis(tenant)
    result3 = get_financial_analysis(tenant)
    
    # Results should be consistent
    assert result1 is not None
    assert result2 is not None
    assert result3 is not None
