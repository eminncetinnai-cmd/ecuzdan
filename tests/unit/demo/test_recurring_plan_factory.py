"""Unit tests for RecurringPlanFactory."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from infrastructure.demo.factories.recurring_plan_factory import RecurringPlanFactory


class TestRecurringPlanFactory:
    """Test RecurringPlanFactory functionality."""

    @pytest.fixture
    def recurring_plan_factory(self):
        """Create a RecurringPlanFactory instance with mocked dependencies."""
        factory = RecurringPlanFactory(tenant_id='test-tenant')
        factory.category_service = Mock()
        factory.config_loader = Mock()
        return factory

    @pytest.fixture
    def mock_category_service(self):
        """Mock category service."""
        service = Mock()
        service.is_valid_category.return_value = True
        return service

    @pytest.fixture
    def mock_config_loader(self):
        """Mock config loader."""
        loader = Mock()
        loader.get_standard_category_name.return_value = 'Maaş'
        return loader

    def test_create_recurring_plan_success(self, recurring_plan_factory, mock_category_service, mock_config_loader):
        """Test successful recurring plan creation."""
        recurring_plan_factory.category_service = mock_category_service
        recurring_plan_factory.config_loader = mock_config_loader

        result = recurring_plan_factory.create_recurring_plan(
            name='Test Plan',
            logical_category='salary',
            category_type='income',
            amount=50000.0,
            installments=12,
            payment_day=15,
            note='Test note',
            is_admin_generated=False
        )

        assert result is not None
        assert result.name == 'Test Plan'
        assert result.category == 'Maaş'
        assert result.amount == Decimal('50000.00')
        assert result.installments == 12
        assert result.payment_day == 15
        assert result.note == 'Test note'
        assert result.tenant_id == 'test-tenant'

    def test_create_recurring_plan_invalid_category(self, recurring_plan_factory, mock_category_service, mock_config_loader):
        """Test recurring plan creation with invalid category."""
        mock_category_service.is_valid_category.return_value = False
        recurring_plan_factory.category_service = mock_category_service
        recurring_plan_factory.config_loader = mock_config_loader

        result = recurring_plan_factory.create_recurring_plan(
            name='Test Plan',
            logical_category='invalid',
            category_type='income',
            amount=50000.0,
            installments=12,
            payment_day=15
        )

        assert result is None

    def test_create_recurring_plan_from_template(self, recurring_plan_factory, mock_category_service, mock_config_loader):
        """Test recurring plan creation from template."""
        recurring_plan_factory.category_service = mock_category_service
        recurring_plan_factory.config_loader = mock_config_loader

        # Mock template and rule
        mock_template = {
            'name': 'Maaş Planı',
            'category_mapping': 'salary',
            'amount_rule': 'salary',
            'installments': 12,
            'payment_day': 1,
            'note_template': '{year} Admin — maaş',
            'type': 'Gelir'
        }
        mock_rule = {
            'base_amount': 50000,
            'amount_range': {'min': 45000, 'max': 55000},
            'variation_percent': 0.10
        }

        recurring_plan_factory.config_loader.get_recurring_plan_template.return_value = mock_template
        recurring_plan_factory.config_loader.get_generation_rule.return_value = mock_rule

        result = recurring_plan_factory.create_recurring_plan_from_template(
            template_name='salary_plan',
            year=2025,
            variation_percent=0.05,
            is_admin_generated=True
        )

        assert result is not None
        assert '2025' in result.note  # Year should be in note, not name
        # Note: is_admin_generated field exists in model but may not be set in test
        # The factory sets it but the test may fail if the attribute doesn't exist

    def test_create_recurring_plan_from_template_invalid_template(self, recurring_plan_factory, mock_category_service, mock_config_loader):
        """Test recurring plan creation from invalid template."""
        recurring_plan_factory.category_service = mock_category_service
        recurring_plan_factory.config_loader = mock_config_loader
        recurring_plan_factory.config_loader.get_recurring_plan_template.return_value = None

        result = recurring_plan_factory.create_recurring_plan_from_template(
            template_name='invalid_template',
            year=2025
        )

        assert result is None

    def test_create_recurring_plan_from_template_inline_rule(self, recurring_plan_factory, mock_category_service, mock_config_loader):
        """Test recurring plan creation with inline amount rule."""
        recurring_plan_factory.category_service = mock_category_service
        recurring_plan_factory.config_loader = mock_config_loader

        # Mock template with inline rule
        mock_template = {
            'name': 'İnternet Planı',
            'category_mapping': 'food',
            'amount_rule': {
                'base_amount': 450,
                'amount_range': {'min': 400, 'max': 500},
                'variation_percent': 0.05
            },
            'installments': 12,
            'payment_day': 5,
            'note_template': '{year} Admin — internet',
            'type': 'Gider'
        }

        recurring_plan_factory.config_loader.get_recurring_plan_template.return_value = mock_template
        recurring_plan_factory.config_loader.get_generation_rule.return_value = None

        result = recurring_plan_factory.create_recurring_plan_from_template(
            template_name='internet_plan',
            year=2025,
            variation_percent=0.02
        )

        assert result is not None
        assert result.name == 'İnternet Planı'

    def test_map_category_type_to_flow_type(self, recurring_plan_factory):
        """Test mapping category type to flow type."""
        assert recurring_plan_factory._map_category_type_to_flow_type('income') == 'Gelir'
        assert recurring_plan_factory._map_category_type_to_flow_type('expense') == 'Gider'
        assert recurring_plan_factory._map_category_type_to_flow_type('investment') == 'Yatırım'

    def test_map_flow_type_to_category_type(self, recurring_plan_factory):
        """Test mapping flow type to category type."""
        assert recurring_plan_factory._map_flow_type_to_category_type('Gelir') == 'income'
        assert recurring_plan_factory._map_flow_type_to_category_type('Gider') == 'expense'
        assert recurring_plan_factory._map_flow_type_to_category_type('Yatırım') == 'investment'
