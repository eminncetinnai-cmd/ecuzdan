"""Unit tests for DemoDataOrchestrator."""

from unittest.mock import Mock, patch

import pytest

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader
from infrastructure.demo.demo_data_orchestrator import DemoDataOrchestrator, generate_advanced_demo_data


@pytest.mark.unit
def test_demo_data_orchestrator_init():
    """Test DemoDataOrchestrator initialization."""
    orchestrator = DemoDataOrchestrator(tenant_id='test-tenant', user_id='test-user')
    assert orchestrator.tenant_id == 'test-tenant'
    assert orchestrator.user_id == 'test-user'
    assert isinstance(orchestrator.category_service, CategoryService)
    assert isinstance(orchestrator.config_loader, DemoDataConfigLoader)


@pytest.mark.unit
def test_demo_data_orchestrator_init_without_params():
    """Test DemoDataOrchestrator initialization without parameters."""
    orchestrator = DemoDataOrchestrator()
    assert orchestrator.tenant_id is None
    assert orchestrator.user_id is None


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator._validate_categories')
@patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator._generate_transactions')
@patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator._generate_recurring_plans')
@patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator._generate_assets')
@patch('infrastructure.demo.demo_data_orchestrator.db')
def test_generate_comprehensive_demo_data(mock_db, mock_generate_assets, mock_generate_recurring_plans,
                                         mock_generate_transactions, mock_validate_categories):
    """Test comprehensive demo data generation."""
    # Setup mocks
    mock_generate_transactions.return_value = 100
    mock_generate_recurring_plans.return_value = 10
    mock_generate_assets.return_value = (5, 20)

    orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

    stats = orchestrator.generate_comprehensive_demo_data(
        start_year=2025,
        end_year=2027,
        is_admin_generated=True
    )

    # Verify all methods were called
    mock_validate_categories.assert_called_once()
    mock_generate_transactions.assert_called_once()
    mock_generate_recurring_plans.assert_called_once()
    mock_generate_assets.assert_called_once()
    mock_db.session.commit.assert_called_once()

    # Verify stats
    assert stats['transactions'] == 100
    assert stats['recurring_plans'] == 10
    assert stats['assets'] == 5
    assert stats['asset_valuations'] == 20


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator._validate_categories')
@patch('infrastructure.demo.demo_data_orchestrator.db')
def test_generate_comprehensive_demo_data_error_handling(mock_db, mock_validate_categories):
    """Test error handling in demo data generation."""
    # Setup mock to raise error
    mock_validate_categories.side_effect = ValueError("Invalid categories")

    orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

    with pytest.raises(ValueError, match="Invalid categories"):
        orchestrator.generate_comprehensive_demo_data(
            start_year=2025,
            end_year=2027,
            is_admin_generated=True
        )

    # Verify rollback was called
    mock_db.session.rollback.assert_called_once()


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.CategoryService')
def test_validate_categories_success(mock_category_service):
    """Test successful category validation."""
    # Setup mocks
    mock_service_instance = Mock()
    mock_service_instance.get_standard_categories.return_value = [
        Mock(name='Maaş / Ücret Geliri'),
        Mock(name='Market & Gıda')
    ]
    mock_service_instance.is_valid_category.return_value = True
    mock_category_service.return_value = mock_service_instance

    orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

    # Should not raise any exception
    orchestrator._validate_categories()


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.CategoryService')
def test_validate_categories_no_standard_categories(mock_category_service):
    """Test category validation when no standard categories exist."""
    # Setup mocks
    mock_service_instance = Mock()
    mock_service_instance.get_standard_categories.return_value = []
    mock_category_service.return_value = mock_service_instance

    orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

    with pytest.raises(ValueError, match="Standard categories must be seeded"):
        orchestrator._validate_categories()


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.CategoryService')
def test_validate_categories_invalid_category(mock_category_service):
    """Test category validation with invalid category."""
    # Setup mocks
    mock_service_instance = Mock()
    mock_service_instance.get_standard_categories.return_value = [
        Mock(name='Maaş / Ücret Geliri')
    ]
    mock_service_instance.is_valid_category.return_value = False
    mock_category_service.return_value = mock_service_instance

    orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

    with pytest.raises(ValueError, match="Invalid categories found"):
        orchestrator._validate_categories()


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.db')
@patch('infrastructure.demo.demo_data_orchestrator.User')
@patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator')
def test_generate_advanced_demo_data_function(mock_orchestrator_class, mock_user, mock_db):
    """Test the generate_advanced_demo_data convenience function."""
    # Setup mocks
    mock_user_instance = Mock()
    mock_user_instance.tenant_id = 'test-tenant'
    mock_db.session.get.return_value = mock_user_instance

    mock_orchestrator_instance = Mock()
    mock_orchestrator_instance.generate_comprehensive_demo_data.return_value = {
        'transactions': 100,
        'recurring_plans': 10,
        'assets': 5,
        'asset_valuations': 20
    }
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    # Call function
    stats = generate_advanced_demo_data(user_id='test-user', start_year=2025, end_year=2027)

    # Verify orchestrator was created with correct parameters
    mock_orchestrator_class.assert_called_once_with(tenant_id='test-tenant', user_id='test-user')

    # Verify generate_comprehensive_demo_data was called
    mock_orchestrator_instance.generate_comprehensive_demo_data.assert_called_once_with(
        start_year=2025,
        end_year=2027,
        is_admin_generated=True
    )

    # Verify stats
    assert stats['transactions'] == 100
    assert stats['recurring_plans'] == 10


@pytest.mark.unit
@patch('infrastructure.demo.demo_data_orchestrator.db')
@patch('infrastructure.demo.demo_data_orchestrator.User')
def test_generate_advanced_demo_data_no_user(mock_user, mock_db):
    """Test generate_advanced_demo_data when user is not found."""
    # Setup mock
    mock_db.session.get.return_value = None

    # Call function - should handle None user gracefully
    with patch('infrastructure.demo.demo_data_orchestrator.DemoDataOrchestrator') as mock_orchestrator_class:
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.generate_comprehensive_demo_data.return_value = {
            'transactions': 0,
            'recurring_plans': 0,
            'assets': 0,
            'asset_valuations': 0
        }
        mock_orchestrator_class.return_value = mock_orchestrator_instance

        stats = generate_advanced_demo_data(user_id='nonexistent-user')

        # Should still return stats (with tenant_id=None)
        assert stats is not None
        assert 'transactions' in stats


@pytest.mark.integration
def test_transaction_exists_check(app):
    """Duplicate transaction detection uses the transaction natural key."""
    from models import Transaction, db

    with app.app_context():
        transaction = Transaction(
            date='2026-01-15', category='Maaş', description='Demo maaş',
            type='Gelir', status='Ödendi', amount=1000, tenant_id='test-tenant'
        )
        db.session.add(transaction)
        db.session.commit()
        orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

        assert orchestrator._transaction_exists(transaction) is True
        different = Transaction(
            date='2026-01-15', category='Maaş', description='Farklı maaş',
            type='Gelir', status='Ödendi', amount=1000, tenant_id='test-tenant'
        )
        assert orchestrator._transaction_exists(different) is False


@pytest.mark.integration
def test_recurring_plan_exists_check(app):
    """Duplicate recurring-plan detection uses the plan name key."""
    from models import RecurringPlan, db

    with app.app_context():
        plan = RecurringPlan(
            name='Demo plan', category='Maaş / Ücret Geliri', flow_type='Gelir',
            amount=50000, installments=12, payment_day=15, tenant_id='test-tenant'
        )
        db.session.add(plan)
        db.session.commit()
        orchestrator = DemoDataOrchestrator(tenant_id='test-tenant')

        assert orchestrator._recurring_plan_exists(plan) is True
        different = RecurringPlan(
            name='Different plan', category='Maaş / Ücret Geliri', flow_type='Gelir',
            amount=50000, installments=12, payment_day=15, tenant_id='test-tenant'
        )
        assert orchestrator._recurring_plan_exists(different) is False
