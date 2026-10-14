"""Unit tests for TransactionFactory."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from infrastructure.demo.factories.transaction_factory import TransactionFactory


class TestTransactionFactory:
    """Test TransactionFactory functionality."""

    @pytest.fixture
    def transaction_factory(self):
        """Create a TransactionFactory instance with mocked dependencies."""
        factory = TransactionFactory(tenant_id='test-tenant')
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

    def test_create_transaction_success(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test successful transaction creation."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader

        result = transaction_factory.create_transaction(
            date='2025-01-15',
            logical_category='salary',
            category_type='income',
            description='Test transaction',
            amount=50000.0,
            status='Ödendi',
            is_admin_generated=False
        )

        assert result is not None
        assert result.date == '2025-01-15'
        assert result.category == 'Maaş'
        assert result.description == 'Test transaction'
        assert result.amount == Decimal('50000.00')
        assert result.status == 'Ödendi'
        assert result.is_admin_generated is False
        assert result.tenant_id == 'test-tenant'

    def test_create_transaction_invalid_category(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test transaction creation with invalid category."""
        mock_category_service.is_valid_category.return_value = False
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader

        result = transaction_factory.create_transaction(
            date='2025-01-15',
            logical_category='invalid',
            category_type='income',
            description='Test transaction',
            amount=50000.0
        )

        assert result is None

    def test_create_transaction_auto_status(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test transaction creation with automatic status determination."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader

        # Mock the generation rule to return a status distribution
        mock_rule = {
            'status_distribution': {'Ödendi': 0.7, 'Bekliyor': 0.3}
        }
        transaction_factory.config_loader.get_generation_rule.return_value = mock_rule

        result = transaction_factory.create_transaction(
            date='2025-01-15',
            logical_category='salary',
            category_type='income',
            description='Test transaction',
            amount=50000.0
        )

        assert result is not None
        assert result.status in ['Ödendi', 'Bekliyor']  # Valid income statuses

    def test_create_transaction_from_template(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test transaction creation from template."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader

        # Mock template and rule
        mock_template = {
            'category_mapping': 'salary',
            'description_template': '{year}-{month} maaş',
            'amount_rule': 'salary',
            'type': 'Gelir',
            'day': 15
        }
        mock_rule = {
            'base_amount': 50000,
            'amount_range': {'min': 45000, 'max': 55000},
            'variation_percent': 0.10
        }

        transaction_factory.config_loader.get_transaction_template.return_value = mock_template
        transaction_factory.config_loader.get_generation_rule.return_value = mock_rule

        result = transaction_factory.create_transaction_from_template(
            template_name='monthly_salary',
            year=2025,
            month=1,
            variation_percent=0.05,
            is_admin_generated=True
        )

        assert result is not None
        assert result.date == '2025-01-15'
        assert result.description == '2025-1 maaş'
        assert result.is_admin_generated is True

    def test_create_transaction_from_template_invalid_template(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test transaction creation from invalid template."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader
        transaction_factory.config_loader.get_transaction_template.return_value = None

        result = transaction_factory.create_transaction_from_template(
            template_name='invalid_template',
            year=2025,
            month=1
        )

        assert result is None

    def test_determine_status_with_distribution(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test status determination with distribution rules."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader

        mock_rule = {
            'status_distribution': {'Ödendi': 0.90, 'Gecikti': 0.10}
        }
        transaction_factory.config_loader.get_generation_rule.return_value = mock_rule

        status = transaction_factory._determine_status('income', 'Maaş')

        assert status in ['Ödendi', 'Gecikti']

    def test_determine_status_default_income(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test default status determination for income."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader
        transaction_factory.config_loader.get_generation_rule.return_value = None

        status = transaction_factory._determine_status('income', 'Maaş')

        assert status in ['Ödendi', 'Bekliyor']

    def test_determine_status_default_expense(self, transaction_factory, mock_category_service, mock_config_loader):
        """Test default status determination for expense."""
        transaction_factory.category_service = mock_category_service
        transaction_factory.config_loader = mock_config_loader
        transaction_factory.config_loader.get_generation_rule.return_value = None

        status = transaction_factory._determine_status('expense', 'Gıda')

        assert status in ['Ödendi', 'Bekliyor', 'Gecikti', 'İptal']

    def test_map_category_type_to_transaction_type(self, transaction_factory):
        """Test mapping category type to transaction type."""
        assert transaction_factory._map_category_type_to_transaction_type('income') == 'Gelir'
        assert transaction_factory._map_category_type_to_transaction_type('expense') == 'Gider'
        assert transaction_factory._map_category_type_to_transaction_type('investment') == 'Yatırım'
        assert transaction_factory._map_category_type_to_transaction_type('transfer') == 'Transfer'

    def test_map_transaction_type_to_category_type(self, transaction_factory):
        """Test mapping transaction type to category type."""
        assert transaction_factory._map_transaction_type_to_category_type('Gelir') == 'income'
        assert transaction_factory._map_transaction_type_to_category_type('Gider') == 'expense'
        assert transaction_factory._map_transaction_type_to_category_type('Yatırım') == 'investment'
        assert transaction_factory._map_transaction_type_to_category_type('Transfer') == 'transfer'

    def test_map_category_name_to_rule_name(self, transaction_factory):
        """Test mapping category name to rule name."""
        assert transaction_factory._map_category_name_to_rule_name('Maaş / Ücret Geliri') == 'salary'
        assert transaction_factory._map_category_name_to_rule_name('Ek Gelir / Yan İş') == 'extra_income'
        assert transaction_factory._map_category_name_to_rule_name('Kira Geliri') == 'rent_income'
        assert transaction_factory._map_category_name_to_rule_name('Market & Gıda') == 'food'
