"""
Unit Tests - Export Service
Export service layer for data export/import operations
"""

from unittest.mock import Mock, patch

import pytest

from infrastructure.export.export_service import ExportService


@pytest.mark.unit
def test_export_service_init():
    """Test ExportService initialization"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    assert service.financial_repository == mock_financial_repo
    assert service.user_repository == mock_user_repo


@pytest.mark.unit
def test_export_service_init_default_repos():
    """Test ExportService initialization with default repositories"""
    with patch('infrastructure.export.export_service.FinancialRepository') as mock_financial_repo_class:
        with patch('infrastructure.export.export_service.UserRepository') as mock_user_repo_class:
            mock_financial_repo = Mock()
            mock_user_repo = Mock()
            mock_financial_repo_class.return_value = mock_financial_repo
            mock_user_repo_class.return_value = mock_user_repo

            service = ExportService()

            assert service.financial_repository == mock_financial_repo
            assert service.user_repository == mock_user_repo


@pytest.mark.unit
def test_export_service_imports():
    """Test that ExportService can be imported"""
    from infrastructure.export.export_service import ExportService

    assert ExportService is not None


@pytest.mark.unit
def test_export_service_module_structure():
    """Test export_service module structure"""
    import infrastructure.export.export_service as export_service_module

    # Check for expected class
    assert hasattr(export_service_module, 'ExportService')

    # Check for expected imports
    assert hasattr(export_service_module, 'calendar')
    assert hasattr(export_service_module, 'datetime')
    assert hasattr(export_service_module, 'timedelta')


@pytest.mark.unit
def test_require_admin_success():
    """Test require_admin with admin user"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.has_admin_access = True
    mock_user_repo.get_user.return_value = mock_user

    service = ExportService(user_repository=mock_user_repo)
    result = service.require_admin(1)

    assert result == mock_user


@pytest.mark.unit
def test_require_admin_no_user():
    """Test require_admin with non-existent user"""
    mock_user_repo = Mock()
    mock_user_repo.get_user.return_value = None

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.require_admin(1)


@pytest.mark.unit
def test_require_admin_not_admin():
    """Test require_admin with non-admin user"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.has_admin_access = False
    mock_user_repo.get_user.return_value = mock_user

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.require_admin(1)


@pytest.mark.unit
def test_require_platform_owner_success():
    """Test require_platform_owner with super admin"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.is_super_admin = True
    mock_user_repo.get_user.return_value = mock_user

    service = ExportService(user_repository=mock_user_repo)
    result = service.require_platform_owner(1)

    assert result == mock_user


@pytest.mark.unit
def test_require_platform_owner_no_user():
    """Test require_platform_owner with non-existent user"""
    mock_user_repo = Mock()
    mock_user_repo.get_user.return_value = None

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.require_platform_owner(1)


@pytest.mark.unit
def test_require_platform_owner_not_super_admin():
    """Test require_platform_owner with non-super admin"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.is_super_admin = False
    mock_user_repo.get_user.return_value = mock_user

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.require_platform_owner(1)


@pytest.mark.unit
def test_pdf_report_context_week_period():
    """Test pdf_report_context with week period"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.tenant_id = 'test_tenant'
    mock_user_repo.get_user.return_value = mock_user
    mock_financial_repo.pending_transactions_between.return_value = []

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    title, transactions, today = service.pdf_report_context(
        period='week',
        user_id=1
    )

    assert title == "Haftalık Bekleyen Ödemeler Raporu"
    assert transactions == []
    assert today is not None


@pytest.mark.unit
def test_pdf_report_context_month_period():
    """Test pdf_report_context with month period"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.tenant_id = 'test_tenant'
    mock_user_repo.get_user.return_value = mock_user
    mock_financial_repo.pending_transactions_between.return_value = []

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    title, transactions, today = service.pdf_report_context(
        period='month',
        user_id=1
    )

    assert title == "Aylık Bekleyen Ödemeler Raporu"
    assert transactions == []


@pytest.mark.unit
def test_pdf_report_context_all_period():
    """Test pdf_report_context with all period"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.tenant_id = 'test_tenant'
    mock_user_repo.get_user.return_value = mock_user
    mock_financial_repo.list_transactions.return_value = []

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    title, transactions, today = service.pdf_report_context(
        period='all',
        user_id=1
    )

    assert title == "Nakit Akış Hareketleri Raporu"
    assert transactions == []


@pytest.mark.unit
def test_pdf_report_context_no_tenant_id():
    """Test pdf_report_context raises error when no tenant_id"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()
    mock_user_repo.get_user.return_value = None

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    with pytest.raises(RuntimeError):
        service.pdf_report_context(period='week', user_id=1)


@pytest.mark.unit
def test_pdf_report_context_with_tenant_id():
    """Test pdf_report_context with explicit tenant_id"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()
    mock_financial_repo.pending_transactions_between.return_value = []

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    title, transactions, today = service.pdf_report_context(
        period='week',
        tenant_id='test_tenant'
    )

    assert title == "Haftalık Bekleyen Ödemeler Raporu"


@pytest.mark.unit
def test_export_tenant_json():
    """Test export_tenant_json"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.tenant_id = 'test_tenant'
    mock_user_repo.get_user.return_value = mock_user

    with patch('models.Transaction') as mock_transaction:
        with patch('models.RecurringPlan') as mock_recurring:
            with patch('domain.portfolio.models.portfolio_models.Asset') as mock_asset:
                mock_transaction.query.filter_by.return_value.all.return_value = []
                mock_recurring.query.filter_by.return_value.all.return_value = []
                mock_asset.query.filter_by.return_value.all.return_value = []

                service = ExportService(user_repository=mock_user_repo)
                result = service.export_tenant_json(user_id=1)

                assert result is not None
                assert isinstance(result, str)


@pytest.mark.unit
def test_export_tenant_json_no_user():
    """Test export_tenant_json with non-existent user"""
    mock_user_repo = Mock()
    mock_user_repo.get_user.return_value = None

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.export_tenant_json(user_id=1)


@pytest.mark.unit
def test_export_database_json():
    """Test export_database_json"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.is_super_admin = True
    mock_user_repo.get_user.return_value = mock_user

    with patch('infrastructure.export.export_service.export_database_to_json') as mock_export:
        mock_export.return_value = '{"data": "test"}'

        service = ExportService(user_repository=mock_user_repo)
        result = service.export_database_json(user_id=1)

        assert result == '{"data": "test"}'


@pytest.mark.unit
def test_export_database_json_not_super_admin():
    """Test export_database_json with non-super admin"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.is_super_admin = False
    mock_user_repo.get_user.return_value = mock_user

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.export_database_json(user_id=1)


@pytest.mark.unit
def test_import_database_json():
    """Test import_database_json"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.is_super_admin = True
    mock_user_repo.get_user.return_value = mock_user

    with patch('infrastructure.export.export_service.import_database_from_json') as mock_import:
        mock_import.return_value = {'success': True}

        service = ExportService(user_repository=mock_user_repo)
        result = service.import_database_json(user_id=1, content='{"data": "test"}')

        assert result == {'success': True}


@pytest.mark.unit
def test_import_database_json_not_super_admin():
    """Test import_database_json with non-super admin"""
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.is_super_admin = False
    mock_user_repo.get_user.return_value = mock_user

    service = ExportService(user_repository=mock_user_repo)

    with pytest.raises(PermissionError):
        service.import_database_json(user_id=1, content='{"data": "test"}')




@pytest.mark.unit
def test_export_service_module_has_required_imports():
    """Test export_service module has required imports"""
    import infrastructure.export.export_service as export_service_module

    # Standard library imports
    assert hasattr(export_service_module, 'calendar')
    assert hasattr(export_service_module, 'datetime')
    assert hasattr(export_service_module, 'timedelta')

    # Custom imports
    assert hasattr(export_service_module, 'FinancialRepository')
    assert hasattr(export_service_module, 'UserRepository')


@pytest.mark.unit
def test_pdf_report_context_custom_datetime():
    """Test pdf_report_context with custom datetime"""
    mock_financial_repo = Mock()
    mock_user_repo = Mock()
    mock_user = Mock()
    mock_user.tenant_id = 'test_tenant'
    mock_user_repo.get_user.return_value = mock_user
    mock_financial_repo.pending_transactions_between.return_value = []

    service = ExportService(
        financial_repository=mock_financial_repo,
        user_repository=mock_user_repo
    )

    from datetime import datetime
    custom_dt = datetime(2024, 1, 15)

    title, transactions, today = service.pdf_report_context(
        period='week',
        now_dt=custom_dt,
        tenant_id='test_tenant'
    )

    assert today == '2024-01-15'
