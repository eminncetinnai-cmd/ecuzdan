"""Unit tests for CatalogService category creation validation and robustness."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from domain.transactions.services.catalog_service import CatalogService, _parse_budget_limit
from repositories.catalog_repository import _generate_gl_code


@pytest.mark.unit
def test_parse_budget_limit_valid():
    """Test _parse_budget_limit with valid inputs."""
    assert _parse_budget_limit(None) is None
    assert _parse_budget_limit('') is None
    assert _parse_budget_limit('1500') == Decimal('1500')
    assert _parse_budget_limit('1500,50') == Decimal('1500.50')
    assert _parse_budget_limit(2500) == Decimal('2500')
    assert _parse_budget_limit('0') == Decimal('0')


@pytest.mark.unit
def test_parse_budget_limit_invalid():
    """Test _parse_budget_limit with invalid numbers."""
    with pytest.raises(ValueError, match="geçerli bir sayı"):
        _parse_budget_limit('invalid')

    with pytest.raises(ValueError, match="sıfır veya daha büyük"):
        _parse_budget_limit('-100')

    with pytest.raises(ValueError, match="sınırlarını aşıyor"):
        _parse_budget_limit('1' + '0' * 20)


@pytest.mark.unit
def test_generate_gl_code_transfer():
    """Test _generate_gl_code for transfer (TRF)."""
    assert _generate_gl_code('Transfer', 5) == 'TRF-5005'


@pytest.mark.unit
def test_add_from_form_validation_name_empty():
    """Test category creation fails if name is empty or whitespace."""
    mock_repo = Mock()
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="boş olamaz"):
        service.add_from_form({'action': 'add_cat', 'name': '   ', 'type': 'Gider'})


@pytest.mark.unit
def test_add_from_form_validation_name_too_short():
    """Test category creation fails if name has fewer than 2 characters."""
    mock_repo = Mock()
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="en az 2 karakter"):
        service.add_from_form({'action': 'add_cat', 'name': 'A', 'type': 'Gider'})


@pytest.mark.unit
def test_add_from_form_validation_name_too_long():
    """Test category creation fails if name exceeds 100 characters."""
    mock_repo = Mock()
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="en fazla 100 karakter"):
        service.add_from_form({'action': 'add_cat', 'name': 'A' * 101, 'type': 'Gider'})


@pytest.mark.unit
def test_add_from_form_validation_invalid_type():
    """Test category creation fails if category type is invalid."""
    mock_repo = Mock()
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="Geçersiz kategori türü"):
        service.add_from_form({'action': 'add_cat', 'name': 'Market', 'type': 'Bilinmeyen'})


@pytest.mark.unit
def test_add_from_form_validation_duplicate_category():
    """Test category creation fails if category already exists."""
    mock_repo = Mock()
    mock_repo.category_exists.return_value = True
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="zaten mevcut"):
        service.add_from_form({'action': 'add_cat', 'name': 'Market', 'type': 'Gider'})


@pytest.mark.unit
def test_add_from_form_validation_parent_type_mismatch():
    """Test category creation fails if parent category has a different type."""
    mock_repo = Mock()
    mock_repo.category_exists.return_value = False
    parent_mock = Mock(id=1, type='Gelir', name='Maaş Geliri')
    mock_repo.get_category.return_value = parent_mock
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="Üst kategori türü .* aynı olmalıdır"):
        service.add_from_form({
            'action': 'add_cat',
            'name': 'Gıda Harcaması',
            'type': 'Gider',
            'parent_id': '1'
        })


@pytest.mark.unit
def test_add_from_form_validation_duplicate_gl_code():
    """Test category creation fails if custom GL code is already in use."""
    mock_repo = Mock()
    mock_repo.category_exists.return_value = False
    existing_cat = Mock(id=2, name='Kira Gideri', code='GDR-7001')
    mock_repo.find_category_by_code.return_value = existing_cat
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="GL kodu zaten .* tanımlı"):
        service.add_from_form({
            'action': 'add_cat',
            'name': 'Ofis Kirası',
            'type': 'Gider',
            'code': 'GDR-7001'
        })


@pytest.mark.unit
def test_update_category_prevent_self_parenting():
    """Test updating a category prevents choosing itself as parent."""
    mock_repo = Mock()
    service = CatalogService(repository=mock_repo)

    with pytest.raises(ValueError, match="kendisinin üst kategorisi olamaz"):
        service.update_category(
            category_id=5,
            name='Ulaşım',
            category_type='Gider',
            parent_id=5
        )


@pytest.mark.unit
def test_add_from_form_success():
    """Test successful category creation calls add_category with normalized values."""
    mock_repo = Mock()
    mock_repo.category_exists.return_value = False
    mock_repo.find_category_by_code.return_value = None
    service = CatalogService(repository=mock_repo)

    service.add_from_form({
        'action': 'add_cat',
        'name': '  Market Alışverişi  ',
        'type': 'Gider',
        'budget_limit': '5000,50',
        'color': 'rose',
        'icon': 'shopping-bag',
        'code': 'gdr-7099'
    }, tenant_id='tenant_abc', user_id=42)

    mock_repo.add_category.assert_called_once_with(
        name='Market Alışverişi',
        category_type='Gider',
        tenant_id='tenant_abc',
        code='GDR-7099',
        parent_id=None,
        budget_limit=Decimal('5000.50'),
        user_id=42,
        color='rose',
        icon='shopping-bag'
    )
