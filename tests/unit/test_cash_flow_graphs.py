"""
Cash Flow Graph Tests
Test nakit akışı grafiklerinin doğruluğunu
"""

import pytest
from datetime import datetime
from decimal import Decimal
from models import Transaction, db
from engines.financial_engine import calculate_cash_trend
from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer
from domain.reporting.services.dashboard_service import DashboardService


@pytest.fixture
def app(app):
    """Use the existing app fixture from conftest.py"""
    return app


@pytest.mark.unit
def test_calculate_cash_trend_excludes_transfers():
    """
    calculate_cash_trend fonksiyonunun transfer'leri hariç tutup tutmadığını test et
    Transfer'ler nakit akışını etkilememeli
    """
    tenant_id = 'test_cashflow_tenant'
    
    # Test transaction'ları oluştur
    transactions = [
        # Gelir: 1000
        Transaction(
            date='2025-01-01',
            type='Gelir',
            amount=Decimal('1000'),
            status='Ödendi',
            category='Maaş / Ücret Geliri',
            description='Maaş',
            tenant_id=tenant_id
        ),
        # Gider: 500
        Transaction(
            date='2025-01-02',
            type='Gider',
            amount=Decimal('500'),
            status='Ödendi',
            category='Konut & Kira',
            description='Kira',
            tenant_id=tenant_id
        ),
        # Transfer: 200 (nakit akışını etkilememeli)
        Transaction(
            date='2025-01-03',
            type='Transfer',
            amount=Decimal('200'),
            status='Ödendi',
            category='Hesap Arası Transfer',
            description='Nakit -> Yatırım',
            transfer_from='Nakit',
            transfer_to='Yatırım',
            tenant_id=tenant_id
        ),
    ]
    
    now = datetime(2025, 1, 1)
    trend_data = calculate_cash_trend(now, transactions, 7)
    
    # İlk gün: 1000 (maaş)
    assert trend_data[0] == 1000, f"Expected 1000, got {trend_data[0]}"
    
    # İkinci gün: 1000 - 500 = 500 (transfer hariç)
    assert trend_data[1] == 500, f"Expected 500, got {trend_data[1]}"
    
    # Üçüncü gün: 500 (transfer nakit akışını etkilememeli)
    assert trend_data[2] == 500, f"Expected 500, got {trend_data[2]}"


@pytest.mark.unit
def test_cash_flow_analyzer_excludes_transfers(app):
    """
    CashFlowAnalyzer'ın transfer'leri doğru şekilde hariç tuttuğunu test et
    """
    tenant_id = 'test_analyzer_tenant'
    
    with app.app_context():
        # Test transaction'ları oluştur
        transactions = [
            Transaction(
                date='2025-01-01',
                type='Gelir',
                amount=Decimal('1000'),
                status='Ödendi',
                category='Maaş / Ücret Geliri',
                description='Maaş',
                tenant_id=tenant_id
            ),
            Transaction(
                date='2025-01-02',
                type='Gider',
                amount=Decimal('500'),
                status='Ödendi',
                category='Konut & Kira',
                description='Kira',
                tenant_id=tenant_id
            ),
            Transaction(
                date='2025-01-03',
                type='Transfer',
                amount=Decimal('200'),
                status='Ödendi',
                category='Hesap Arası Transfer',
                description='Transfer',
                transfer_from='Nakit',
                transfer_to='Yatırım',
                tenant_id=tenant_id
            ),
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        summary = CashFlowAnalyzer.get_cash_flow_summary(tenant_id, '2025-01-01', '2025-01-31')
        
        # Gelir: 1000
        assert summary['cash_flow']['total_income'] == 1000
        
        # Gider: 500 (transfer hariç)
        assert summary['cash_flow']['total_expenses'] == 500
        
        # Net cash flow: 1000 - 500 = 500
        assert summary['cash_flow']['net_cash_flow'] == 500
        
        # Transfer'ler ayrı raporlanmalı
        assert summary['transfers']['total_transfers'] == 200
        assert summary['transfers']['transfer_count'] == 1


@pytest.mark.unit
def test_dashboard_service_actual_cash_calculation():
    """
    DashboardService'in actual_cash hesaplamasının doğruluğunu test et
    Transfer'ler nakit akışını etkilememeli
    """
    tenant_id = 'test_dashboard_tenant'
    
    transactions = [
        Transaction(
            date='2025-01-01',
            type='Gelir',
            amount=Decimal('1000'),
            status='Ödendi',
            category='Maaş / Ücret Geliri',
            description='Maaş',
            tenant_id=tenant_id
        ),
        Transaction(
            date='2025-01-02',
            type='Gider',
            amount=Decimal('500'),
            status='Ödendi',
            category='Konut & Kira',
            description='Kira',
            tenant_id=tenant_id
        ),
        Transaction(
            date='2025-01-03',
            type='Transfer',
            amount=Decimal('200'),
            status='Ödendi',
            category='Hesap Arası Transfer',
            description='Transfer',
            transfer_from='Nakit',
            transfer_to='Yatırım',
            tenant_id=tenant_id
        ),
    ]
    
    # Mock repository
    class MockFinancialRepository:
        def list_transactions(self, tenant_id=None):
            return transactions
        
        def list_assets(self, tenant_id=None):
            return []
    
    class MockCatalogRepository:
        def list_visible_categories(self, tenant_id=None):
            return []
    
    service = DashboardService(
        financial_repository=MockFinancialRepository(),
        catalog_repository=MockCatalogRepository()
    )
    
    context = service.index_context(tenant_id=tenant_id, now=datetime(2025, 1, 5))
    
    # actual_cash: 1000 - 500 = 500 (transfer hariç)
    # Ancak mevcut implementasyon transfer'leri filtrelemiyor olabilir
    # Bu test mevcut davranışı doğrular
    expected_cash = 500  # Transfer hariç doğru değer
    actual_cash = context['today_cash']
    
    # Eğer transfer dahil edilmişse, bu bir bug'dır
    if actual_cash == 300:  # 1000 - 500 - 200 (transfer dahil)
        pytest.fail("BUG: DashboardService actual_cash hesaplaması transfer'leri dahil ediyor")
    
    assert actual_cash == expected_cash, f"Expected {expected_cash}, got {actual_cash}"


@pytest.mark.unit
def test_cash_flow_vs_net_worth_separation(app):
    """
    Nakit akışı ve net worth ayrımının doğru olduğunu test et
    Transfer'ler net worth'u değiştirmemeli ama nakit akışını etkilememeli
    """
    tenant_id = 'test_separation_tenant'
    
    with app.app_context():
        transactions = [
            Transaction(
                date='2025-01-01',
                type='Gelir',
                amount=Decimal('10000'),
                status='Ödendi',
                category='Maaş / Ücret Geliri',
                description='Maaş',
                tenant_id=tenant_id
            ),
            Transaction(
                date='2025-01-02',
                type='Transfer',
                amount=Decimal('5000'),
                status='Ödendi',
                category='Hesap Arası Transfer',
                description='Nakit -> Yatırım',
                transfer_from='Nakit',
                transfer_to='Yatırım',
                tenant_id=tenant_id
            ),
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        comparison = CashFlowAnalyzer.compare_with_vs_without_transfers(
            tenant_id, '2025-01-01', '2025-01-31'
        )
        
        # Doğru nakit akışı (transfer hariç)
        assert comparison['correct_cash_flow']['income'] == 10000
        assert comparison['correct_cash_flow']['expenses'] == 0
        assert comparison['correct_cash_flow']['net'] == 10000
        
        # Yanlış hesaplama (transfer dahil)
        # Transfer gider olarak sayılırsa
        assert comparison['incorrect_including_transfers']['expenses'] == 5000
        assert comparison['incorrect_including_transfers']['net'] == 5000
        
        # Fark
        assert comparison['difference']['expense_difference'] == 5000
        assert comparison['difference']['net_difference'] == -5000


@pytest.mark.unit
def test_transfer_detection():
    """
    Transfer detection logic'inin doğru çalıştığını test et
    """
    # Transfer transaction
    transfer_tx = Transaction(
        date='2025-01-01',
        type='Transfer',
        amount=Decimal('100'),
        status='Ödendi',
        category='Transfer',
        description='Transfer',
        transfer_from='A',
        transfer_to='B',
        tenant_id='test'
    )
    
    # Normal expense
    expense_tx = Transaction(
        date='2025-01-01',
        type='Gider',
        amount=Decimal('100'),
        status='Ödendi',
        category='Diğer Giderler',
        description='Yemek',
        tenant_id='test'
    )
    
    assert CashFlowAnalyzer.is_transfer(transfer_tx) == True
    assert CashFlowAnalyzer.is_transfer(expense_tx) == False
