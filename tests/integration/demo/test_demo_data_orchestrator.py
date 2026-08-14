"""Integration tests for DemoDataOrchestrator."""

import pytest
from datetime import datetime

from infrastructure.demo.demo_data_orchestrator import DemoDataOrchestrator
from domain.categories.services.category_service import CategoryService
from models import Transaction, RecurringPlan, Asset, AssetUpdate, Category, db


class TestDemoDataOrchestrator:
    """Integration tests for DemoDataOrchestrator."""

    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Setup database for tests."""
        with app.app_context():
            # Create standard categories if they don't exist
            self._ensure_standard_categories()
            yield
            # Cleanup after tests
            self._cleanup_demo_data()

    def _ensure_standard_categories(self):
        """Ensure standard categories exist for testing."""
        from scripts.seed_standard_categories import STANDARD_CATEGORIES
        
        for code, name, type_, sort_order, budget_limit in STANDARD_CATEGORIES:
            existing = Category.query.filter_by(code=code, tenant_id=None).first()
            if not existing:
                category = Category(name=name, type=type_, code=code, tenant_id=None, budget_limit=budget_limit)
                db.session.add(category)
        
        db.session.commit()

    def _cleanup_demo_data(self):
        """Clean up demo data after tests."""
        # Delete demo transactions
        Transaction.query.filter(Transaction.is_admin_generated.is_(True)).delete()
        
        # Delete demo recurring plans
        RecurringPlan.query.filter(RecurringPlan.note.ilike('%Admin%')).delete()
        
        # Delete demo assets
        demo_assets = Asset.query.filter(Asset.is_admin_generated.is_(True)).all()
        for asset in demo_assets:
            AssetUpdate.query.filter_by(asset_id=asset.id).delete()
        
        Asset.query.filter(Asset.is_admin_generated.is_(True)).delete()
        
        db.session.commit()

    def test_generate_comprehensive_demo_data(self, app):
        """Test comprehensive demo data generation."""
        with app.app_context():
            orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')
            
            stats = orchestrator.generate_comprehensive_demo_data(
                start_year=2025,
                end_year=2025,  # Single year for faster testing
                is_admin_generated=True
            )
            
            # Verify statistics (may be 0 if categories don't match, but should not error)
            assert stats is not None
            assert 'transactions' in stats
            assert 'recurring_plans' in stats
            assert 'assets' in stats
            assert 'asset_valuations' in stats

    def test_validate_categories(self, app):
        """Test category validation during generation."""
        with app.app_context():
            orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')
            
            # This should not raise any errors
            orchestrator._validate_categories()

    def test_transaction_exists_check(self, app):
        """Test transaction existence check."""
        with app.app_context():
            orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')
            
            # Create a test transaction
            test_transaction = Transaction(
                date='2025-01-15',
                category='Maaş / Ücret Geliri',
                description='Test transaction',
                type='Gelir',
                status='Ödendi',
                amount=50000.00,
                tenant_id='test-tenant'
            )
            db.session.add(test_transaction)
            db.session.commit()
            
            # Check if it exists
            assert orchestrator._transaction_exists(test_transaction) is True
            
            # Create a different transaction
            different_transaction = Transaction(
                date='2025-01-16',
                category='Maaş / Ücret Geliri',
                description='Different transaction',
                type='Gelir',
                status='Ödendi',
                amount=50000.00,
                tenant_id='test-tenant'
            )
            
            assert orchestrator._transaction_exists(different_transaction) is False

    def test_recurring_plan_exists_check(self, app):
        """Test recurring plan existence check."""
        with app.app_context():
            orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')
            
            # Create a test plan
            test_plan = RecurringPlan(
                name='Test Plan',
                category='Maaş / Ücret Geliri',
                flow_type='Gelir',
                amount=50000.00,
                installments=12,
                payment_day=15,
                tenant_id='test-tenant'
            )
            db.session.add(test_plan)
            db.session.commit()
            
            # Check if it exists
            assert orchestrator._recurring_plan_exists(test_plan) is True
            
            # Create a different plan
            different_plan = RecurringPlan(
                name='Different Plan',
                category='Maaş / Ücret Geliri',
                flow_type='Gelir',
                amount=50000.00,
                installments=12,
                payment_day=15,
                tenant_id='test-tenant'
            )
            
            assert orchestrator._recurring_plan_exists(different_plan) is False

    def test_category_validation_integration(self, app):
        """Test that only valid categories are used."""
        with app.app_context():
            category_service = CategoryService()
            
            # Verify standard categories exist
            standard_categories = category_service.get_standard_categories()
            assert len(standard_categories) > 0
            
            # Verify specific categories exist (using new database names)
            assert category_service.is_valid_category('Maaş / Ücret Geliri', None)
            assert category_service.is_valid_category('Aylık Sabit Gider', None)
            assert category_service.is_valid_category('Hisse Senedi', None)
            
            # Verify invalid category is rejected
            assert not category_service.is_valid_category('Invalid Category', None)
            
            # Verify that standard categories are valid for tenants as well
            # (tenants can use standard categories)
            assert category_service.is_valid_category('Maaş / Ücret Geliri', 'some-tenant')

    def test_no_duplicate_transactions(self, app):
        """Test that duplicate transactions are not created."""
        with app.app_context():
            orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')
            
            # Generate data twice
            stats1 = orchestrator.generate_comprehensive_demo_data(
                start_year=2025,
                end_year=2025,
                is_admin_generated=True
            )
            
            stats2 = orchestrator.generate_comprehensive_demo_data(
                start_year=2025,
                end_year=2025,
                is_admin_generated=True
            )
            
            # Second generation should create fewer transactions (duplicates skipped)
            assert stats2['transactions'] <= stats1['transactions']
            
            # Total transactions should not be double
            total_transactions = Transaction.query.filter_by(tenant_id='test-tenant').count()
            assert total_transactions <= stats1['transactions'] + 10  # Allow small margin for randomness

    def test_tenant_scoped_data(self, app):
        """Test that data is properly scoped to tenant."""
        with app.app_context():
            # Generate data for tenant1
            orchestrator1 = DemoDataOrchestrator(tenant_id='tenant-1')
            stats1 = orchestrator1.generate_comprehensive_demo_data(
                start_year=2025,
                end_year=2025,
                is_admin_generated=True
            )
            
            # Generate data for tenant2
            orchestrator2 = DemoDataOrchestrator(tenant_id='tenant-2')
            stats2 = orchestrator2.generate_comprehensive_demo_data(
                start_year=2025,
                end_year=2025,
                is_admin_generated=True
            )
            
            # Verify data is scoped correctly
            tenant1_transactions = Transaction.query.filter_by(tenant_id='tenant-1').count()
            tenant2_transactions = Transaction.query.filter_by(tenant_id='tenant-2').count()
            
            assert tenant1_transactions > 0
            assert tenant2_transactions > 0
            assert tenant1_transactions == stats1['transactions']
            assert tenant2_transactions == stats2['transactions']

    def test_generate_advanced_demo_data_function(self, app):
        """Test the generate_advanced_demo_data convenience function."""
        with app.app_context():
            from infrastructure.demo import generate_advanced_demo_data
            from models import User
            
            # Get or create a test user
            user = User.query.first()
            if not user:
                user = User(username='test_user', password='test', role='kullanici')
                db.session.add(user)
                db.session.commit()
            
            # Generate data using the convenience function
            stats = generate_advanced_demo_data(
                user_id=user.id,
                start_year=2025,
                end_year=2025
            )
            
            # Verify statistics
            assert stats is not None
            assert 'transactions' in stats
            assert 'recurring_plans' in stats
            assert 'assets' in stats
            assert 'asset_valuations' in stats

    def test_standard_categories_only(self, app):
        """Test that demo data only uses standard categories."""
        with app.app_context():
            orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')
            
            # Generate data
            stats = orchestrator.generate_comprehensive_demo_data(
                start_year=2025,
                end_year=2025,
                is_admin_generated=True
            )
            
            # Get all generated transactions
            transactions = Transaction.query.filter_by(tenant_id='test-tenant').all()
            
            # Get all standard categories
            standard_category_names = {cat.name for cat in Category.query.filter_by(tenant_id=None).all()}
            
            # Verify all transactions use standard categories
            for tx in transactions:
                assert tx.category in standard_category_names, f"Transaction uses non-standard category: {tx.category}"
            
            # Get all generated recurring plans
            plans = RecurringPlan.query.filter_by(tenant_id='test-tenant').all()
            
            # Verify all plans use standard categories
            for plan in plans:
                assert plan.category in standard_category_names, f"Plan uses non-standard category: {plan.category}"
