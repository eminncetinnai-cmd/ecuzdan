"""
Unit Tests - Reporting Repository
Repository for reporting and analytics queries
"""

from unittest.mock import Mock, patch

import pytest

from repositories.reporting_repository import ReportingRepository


@pytest.mark.unit
def test_reporting_repository_class_exists():
    """Test ReportingRepository class exists"""
    assert ReportingRepository is not None


@pytest.mark.unit
def test_reporting_repository_inheritance():
    """Test ReportingRepository inherits from base classes"""
    from repositories.base import BaseRepository

    assert issubclass(ReportingRepository, BaseRepository)
    # Skip protocol check as it requires @runtime_checkable
    # assert issubclass(ReportingRepository, ReportingRepositoryContract)


@pytest.mark.unit
def test_reporting_repository_init():
    """Test ReportingRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)
    assert repo.session == mock_session


@pytest.mark.unit
def test_reporting_repository_imports():
    """Test that ReportingRepository can be imported"""
    from repositories.reporting_repository import ReportingRepository
    assert ReportingRepository is not None


@pytest.mark.unit
def test_reporting_repository_module_structure():
    """Test reporting_repository module structure"""
    import repositories.reporting_repository as reporting_repo_module

    # Check for expected class
    assert hasattr(reporting_repo_module, 'ReportingRepository')

    # Check for expected imports
    assert hasattr(reporting_repo_module, 'Asset')
    assert hasattr(reporting_repo_module, 'RecurringPlan')
    assert hasattr(reporting_repo_module, 'Transaction')
    assert hasattr(reporting_repo_module, 'db')
    assert hasattr(reporting_repo_module, 'BaseRepository')
    assert hasattr(reporting_repo_module, 'ReportingRepositoryContract')


@pytest.mark.unit
def test_get_monthly_balance_method_exists():
    """Test get_monthly_balance method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_monthly_balance')
    assert callable(repo.get_monthly_balance)


@pytest.mark.unit
def test_get_actual_cash_method_exists():
    """Test get_actual_cash method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_actual_cash')
    assert callable(repo.get_actual_cash)


@pytest.mark.unit
def test_get_total_assets_method_exists():
    """Test get_total_assets method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_total_assets')
    assert callable(repo.get_total_assets)


@pytest.mark.unit
def test_get_total_debts_method_exists():
    """Test get_total_debts method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_total_debts')
    assert callable(repo.get_total_debts)


@pytest.mark.unit
def test_get_transactions_by_date_range_method_exists():
    """Test get_transactions_by_date_range method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_transactions_by_date_range')
    assert callable(repo.get_transactions_by_date_range)


@pytest.mark.unit
def test_get_calendar_month_data_method_exists():
    """Test get_calendar_month_data method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_calendar_month_data')
    assert callable(repo.get_calendar_month_data)


@pytest.mark.unit
def test_get_pending_payments_method_exists():
    """Test get_pending_payments method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, 'get_pending_payments')
    assert callable(repo.get_pending_payments)


@pytest.mark.unit
def test_serialize_calendar_tx_method_exists():
    """Test _serialize_calendar_tx private method exists"""
    repo = ReportingRepository()
    assert hasattr(repo, '_serialize_calendar_tx')
    assert callable(repo._serialize_calendar_tx)


@pytest.mark.unit
def test_reporting_repository_session_attribute():
    """Test ReportingRepository has session attribute"""
    repo = ReportingRepository()
    assert hasattr(repo, 'session')


@pytest.mark.unit
def test_reporting_repository_commit_method():
    """Test ReportingRepository has commit method from base"""
    repo = ReportingRepository()
    assert hasattr(repo, 'commit')
    assert callable(repo.commit)


@pytest.mark.unit
def test_reporting_repository_rollback_method():
    """Test ReportingRepository has rollback method from base"""
    repo = ReportingRepository()
    assert hasattr(repo, 'rollback')
    assert callable(repo.rollback)


@pytest.mark.unit
def test_serialize_calendar_tx():
    """Test _serialize_calendar_tx method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)
    mock_transaction = Mock()
    mock_transaction.id = 1
    mock_transaction.category = 'Test Category'
    mock_transaction.description = 'Test Description'
    mock_transaction.note = 'Test Note'
    mock_transaction.type = 'Gelir'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.0
    mock_transaction.origin = 'manual'

    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '₺100.00'
        result = repo._serialize_calendar_tx(mock_transaction)

        assert result['id'] == 1
        assert result['category'] == 'Test Category'
        assert result['description'] == 'Test Description'
        assert result['note'] == 'Test Note'
        assert result['type'] == 'Gelir'
        assert result['status'] == 'Ödendi'
        assert result['amount'] == 100.0
        assert result['amount_fmt'] == '₺100.00'
        assert result['origin'] == 'manual'


@pytest.mark.unit
def test_serialize_calendar_tx_empty_fields():
    """Test _serialize_calendar_tx with empty fields"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)
    mock_transaction = Mock()
    mock_transaction.id = 1
    mock_transaction.category = 'Test Category'
    mock_transaction.description = None
    mock_transaction.note = None
    mock_transaction.type = 'Gelir'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.0
    mock_transaction.origin = 'manual'

    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '₺100.00'
        result = repo._serialize_calendar_tx(mock_transaction)

        assert result['description'] == ''
        assert result['note'] == ''


@pytest.mark.unit
def test_get_monthly_balance():
    """Test get_monthly_balance method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)

    with patch('repositories.reporting_repository.db.session') as mock_db_session:
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        from decimal import Decimal
        result = repo.get_monthly_balance(2024, 1, 'test_tenant')
        assert result == (Decimal('0.0'), Decimal('0.0'))


@pytest.mark.unit
def test_get_actual_cash():
    """Test get_actual_cash method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)

    with patch('repositories.reporting_repository.db.session') as mock_db_session:
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.scalar.return_value = 1000.0

        result = repo.get_actual_cash('test_tenant')
        assert result == 1000.0


@pytest.mark.unit
def test_get_total_assets():
    """Test get_total_assets method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)

    with patch('repositories.reporting_repository.db.session') as mock_db_session:
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.scalar.return_value = 5000.0

        result = repo.get_total_assets('test_tenant')
        assert result == 5000.0


@pytest.mark.unit
def test_get_total_debts():
    """Test get_total_debts method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)

    with patch('repositories.reporting_repository.db.session') as mock_db_session:
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.scalar.return_value = 2000.0

        result = repo.get_total_debts('test_tenant')
        assert result == 2000.0


@pytest.mark.integration
def test_get_transactions_by_date_range(app):
    """Date-range reporting returns only tenant-scoped transactions."""
    from models import Transaction, db

    with app.app_context():
        transaction = Transaction(
            date='2026-01-15', category='Maaş', description='Ocak geliri',
            type='Gelir', status='Ödendi', amount=1000, tenant_id='default'
        )
        db.session.add(transaction)
        db.session.commit()

        result = ReportingRepository().get_transactions_by_date_range(
            '2026-01-01', '2026-01-31', tenant_id='default'
        )

    assert len(result) == 1
    assert result[0].description == 'Ocak geliri'


@pytest.mark.integration
def test_get_calendar_month_data(app):
    """Calendar reporting groups income and expenses by day."""
    from models import Transaction, db

    with app.app_context():
        db.session.add_all([
            Transaction(
                date='2026-01-15', category='Maaş', description='Gelir',
                type='Gelir', status='Ödendi', amount=1000, tenant_id='default'
            ),
            Transaction(
                date='2026-01-15', category='Vergi', description='Gider',
                type='Gider', status='Ödendi', amount=250, tenant_id='default'
            ),
        ])
        db.session.commit()

        result = ReportingRepository().get_calendar_month_data(
            2026, 1, tenant_id='default'
        )

    assert '2026-01-15' in result
    assert result['2026-01-15']['income_total'] == 1000.0
    assert result['2026-01-15']['expense_total'] == 250.0
    assert result['2026-01-15']['net'] == 750.0


@pytest.mark.integration
def test_get_pending_payments(app):
    """Pending expense and investment transactions are returned in date order."""
    from models import Transaction, db

    with app.app_context():
        db.session.add_all([
            Transaction(
                date='2026-01-15', category='Kredi', description='Bekleyen',
                type='Gider', status='Bekliyor', amount=300, tenant_id='default'
            ),
            Transaction(
                date='2026-01-16', category='Vergi', description='Ödenen',
                type='Gider', status='Ödendi', amount=400, tenant_id='default'
            ),
        ])
        db.session.commit()

        result = ReportingRepository().get_pending_payments(
            '2026-01-01', '2026-01-31', tenant_id='default'
        )

    assert len(result) == 1
    assert result[0].description == 'Bekleyen'



@pytest.mark.unit
def test_get_monthly_balance_with_tenant():
    """Test get_monthly_balance with tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)

    with patch('repositories.reporting_repository.db.session') as mock_db_session:
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        from decimal import Decimal
        result = repo.get_monthly_balance(2024, 1, 'test_tenant')
        assert result == (Decimal('0.0'), Decimal('0.0'))


@pytest.mark.integration
def test_get_transactions_by_date_range_no_tenant(app):
    """Date-range reporting can intentionally return all tenants when no scope is given."""
    from models import Transaction, db

    with app.app_context():
        db.session.add(Transaction(
            date='2026-02-01', category='Maaş', description='Global kayıt',
            type='Gelir', status='Ödendi', amount=500, tenant_id='default'
        ))
        db.session.commit()

        result = ReportingRepository().get_transactions_by_date_range(
            '2026-02-01', '2026-02-28'
        )

    assert len(result) == 1
    assert result[0].description == 'Global kayıt'


@pytest.mark.unit
def test_serialize_calendar_tx_with_recurring():
    """Test _serialize_calendar_tx with recurring transaction"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = ReportingRepository(database=mock_db)
    mock_transaction = Mock()
    mock_transaction.id = 1
    mock_transaction.category = 'Test Category'
    mock_transaction.description = 'Test Description'
    mock_transaction.note = 'Test Note'
    mock_transaction.type = 'Gelir'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.0
    mock_transaction.origin = 'recurring'

    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '₺100.00'
        result = repo._serialize_calendar_tx(mock_transaction)

        assert result['origin'] == 'recurring'
