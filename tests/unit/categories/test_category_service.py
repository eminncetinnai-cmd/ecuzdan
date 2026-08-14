"""Unit tests for CategoryService."""

import pytest
from unittest.mock import Mock, MagicMock

from domain.categories.services.category_service import CategoryService
from models import Category


class TestCategoryService:
    """Test CategoryService functionality."""

    @pytest.fixture
    def category_service(self):
        """Create a CategoryService instance with mocked repository."""
        service = CategoryService()
        service.repository = Mock()
        service.tenant_repository = Mock()
        return service

    @pytest.fixture
    def mock_standard_categories(self):
        """Create mock standard categories."""
        return [
            Category(id=1, name='Maaş / Ücret Geliri', type='Gelir', code='GLR-6001', tenant_id=None),
            Category(id=2, name='Kira Geliri', type='Gelir', code='GLR-6003', tenant_id=None),
            Category(id=3, name='Konut & Kira', type='Gider', code='GDR-7001', tenant_id=None),
            Category(id=4, name='Kredi Kartı Ödemesi', type='Gider', code='GDR-7011', tenant_id=None),
            Category(id=5, name='Yatırıma Aktarılan', type='Yatırım', code='YTR-1001', tenant_id=None),
        ]

    def test_get_standard_categories(self, category_service, mock_standard_categories):
        """Test getting standard categories."""
        category_service.repository.get_standard_categories.return_value = mock_standard_categories
        
        result = category_service.get_standard_categories()
        
        assert len(result) == 5
        category_service.repository.get_standard_categories.assert_called_once()

    def test_get_category_by_name_standard(self, category_service, mock_standard_categories):
        """Test getting category by name from standard categories."""
        category_service.repository.find_category_by_name.return_value = mock_standard_categories[0]
        
        result = category_service.get_category_by_name('Maaş / Ücret Geliri')
        
        assert result.name == 'Maaş / Ücret Geliri'
        category_service.repository.find_category_by_name.assert_called_once_with('Maaş / Ücret Geliri', None)

    def test_get_category_by_name_tenant(self, category_service):
        """Test getting category by name for tenant."""
        mock_category = Category(id=10, name='Custom Category', type='Gider', code='CUSTOM-001', tenant_id='tenant-123')
        category_service.repository.find_category_by_name.return_value = mock_category
        
        result = category_service.get_category_by_name('Custom Category', tenant_id='tenant-123')
        
        assert result.name == 'Custom Category'
        category_service.repository.find_category_by_name.assert_called_once_with('Custom Category', 'tenant-123')

    def test_get_category_by_code(self, category_service, mock_standard_categories):
        """Test getting category by code."""
        category_service.repository.find_category_by_code.return_value = mock_standard_categories[0]
        
        result = category_service.get_category_by_code('GLR-6001')
        
        assert result.code == 'GLR-6001'
        category_service.repository.find_category_by_code.assert_called_once_with('GLR-6001', None)

    def test_get_categories_by_type(self, category_service, mock_standard_categories):
        """Test getting categories by type."""
        income_categories = [cat for cat in mock_standard_categories if cat.type == 'Gelir']
        category_service.repository.get_categories_by_type.return_value = income_categories
        
        result = category_service.get_categories_by_type('Gelir')
        
        assert len(result) == 2
        assert all(cat.type == 'Gelir' for cat in result)
        category_service.repository.get_categories_by_type.assert_called_once_with('Gelir', None)

    def test_is_valid_category_true(self, category_service, mock_standard_categories):
        """Test valid category check."""
        category_service.repository.find_category_by_name.return_value = mock_standard_categories[0]
        
        result = category_service.is_valid_category('Maaş')
        
        assert result is True

    def test_is_valid_category_false(self, category_service):
        """Test invalid category check."""
        category_service.repository.find_category_by_name.return_value = None
        
        result = category_service.is_valid_category('NonExistent')
        
        assert result is False

    def test_validate_category_names_all_valid(self, category_service, mock_standard_categories):
        """Test validating multiple category names - all valid."""
        category_service.repository.find_category_by_name.side_effect = [
            mock_standard_categories[0],  # Maaş
            mock_standard_categories[1],  # Kira
            mock_standard_categories[2],  # Vergi
        ]
        
        result = category_service.validate_category_names(['Maaş', 'Kira', 'Vergi'])
        
        assert result['is_valid'] is True
        assert len(result['valid']) == 3
        assert len(result['invalid']) == 0

    def test_validate_category_names_mixed(self, category_service, mock_standard_categories):
        """Test validating multiple category names - mixed valid/invalid."""
        category_service.repository.find_category_by_name.side_effect = [
            mock_standard_categories[0],  # Maaş - valid
            None,  # Invalid - NonExistent
            mock_standard_categories[1],  # Kira - valid
        ]
        
        result = category_service.validate_category_names(['Maaş', 'NonExistent', 'Kira'])
        
        assert result['is_valid'] is False
        assert len(result['valid']) == 2
        assert len(result['invalid']) == 1
        assert 'NonExistent' in result['invalid']

    def test_get_income_categories(self, category_service):
        """Test getting income categories."""
        category_service.repository.get_categories_by_type.return_value = []
        
        result = category_service.get_income_categories()
        
        category_service.repository.get_categories_by_type.assert_called_once_with('Gelir', None)

    def test_get_expense_categories(self, category_service):
        """Test getting expense categories."""
        category_service.repository.get_categories_by_type.return_value = []
        
        result = category_service.get_expense_categories()
        
        category_service.repository.get_categories_by_type.assert_called_once_with('Gider', None)

    def test_get_investment_categories(self, category_service):
        """Test getting investment categories."""
        category_service.repository.get_categories_by_type.return_value = []
        
        result = category_service.get_investment_categories()
        
        category_service.repository.get_categories_by_type.assert_called_once_with('Yatırım', None)

    def test_get_category_mapping(self, category_service, mock_standard_categories):
        """Test getting category name to type mapping."""
        category_service.repository.get_standard_categories.return_value = mock_standard_categories
        
        result = category_service.get_category_mapping()
        
        assert result['Maaş / Ücret Geliri'] == 'Gelir'
        assert result['Kira Geliri'] == 'Gelir'
        assert result['Konut & Kira'] == 'Gider'
        assert result['Kredi Kartı Ödemesi'] == 'Gider'
        assert result['Yatırıma Aktarılan'] == 'Yatırım'

    def test_get_standard_category_codes(self, category_service, mock_standard_categories):
        """Test getting standard category codes."""
        category_service.repository.get_standard_categories.return_value = mock_standard_categories
        
        result = category_service.get_standard_category_codes()
        
        assert 'Gelir' in result
        assert 'Gider' in result
        assert 'Yatırım' in result
        assert 'GLR-6001' in result['Gelir']
        assert 'GLR-6003' in result['Gelir']
        assert 'GDR-7001' in result['Gider']
        assert 'YTR-1001' in result['Yatırım']
