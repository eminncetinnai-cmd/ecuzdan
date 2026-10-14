"""
Unit Tests - Reporting Repository
Repository for reporting and analytics queries
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from repositories.reporting_repository import ReportingRepository


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
    assert hasattr(reporting_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_reporting_repository_extends_base():
    """Test ReportingRepository extends BaseRepository"""
    from repositories.base import BaseRepository
    from repositories.reporting_repository import ReportingRepository

    assert issubclass(ReportingRepository, BaseRepository)


@pytest.mark.unit
def test_get_monthly_balance():
    """Test get_monthly_balance method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_rows = [('Gelir', Decimal('1000.00')), ('Gider', Decimal('500.00'))]
        mock_query.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = mock_rows

        repo = ReportingRepository(database=mock_db)

        income, expense = repo.get_monthly_balance(2025, 1, tenant_id='test_tenant')

        assert income == Decimal('1000.00')
        assert expense == Decimal('500.00')


@pytest.mark.unit
def test_get_monthly_balance_no_tenant():
    """Test get_monthly_balance without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_rows = [('Gelir', Decimal('1000.00'))]
        mock_query.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = mock_rows

        repo = ReportingRepository(database=mock_db)

        income, expense = repo.get_monthly_balance(2025, 1)

        assert income == Decimal('1000.00')
        assert expense == Decimal('0.00')


@pytest.mark.unit
def test_get_monthly_balance_empty():
    """Test get_monthly_balance with no data"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = []

        repo = ReportingRepository(database=mock_db)

        income, expense = repo.get_monthly_balance(2025, 1, tenant_id='test_tenant')

        assert income == Decimal('0.00')
        assert expense == Decimal('0.00')


@pytest.mark.unit
def test_get_actual_cash():
    """Test get_actual_cash method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal('5000.00')

        repo = ReportingRepository(database=mock_db)

        result = repo.get_actual_cash(tenant_id='test_tenant')

        assert result == Decimal('5000.00')


@pytest.mark.unit
def test_get_actual_cash_no_tenant():
    """Test get_actual_cash without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = Decimal('3000.00')

        repo = ReportingRepository(database=mock_db)

        result = repo.get_actual_cash()

        assert result == Decimal('3000.00')


@pytest.mark.unit
def test_get_actual_cash_null():
    """Test get_actual_cash when result is None"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = None

        repo = ReportingRepository(database=mock_db)

        result = repo.get_actual_cash(tenant_id='test_tenant')

        assert result == Decimal('0.00')


@pytest.mark.unit
def test_get_total_assets():
    """Test get_total_assets method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = Decimal('100000.00')

        repo = ReportingRepository(database=mock_db)

        result = repo.get_total_assets(tenant_id='test_tenant')

        assert result == Decimal('100000.00')


@pytest.mark.unit
def test_get_total_assets_no_tenant():
    """Test get_total_assets without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.scalar.return_value = Decimal('75000.00')

        repo = ReportingRepository(database=mock_db)

        result = repo.get_total_assets()

        assert result == Decimal('75000.00')


@pytest.mark.unit
def test_get_total_assets_null():
    """Test get_total_assets when result is None"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = None

        repo = ReportingRepository(database=mock_db)

        result = repo.get_total_assets(tenant_id='test_tenant')

        assert result == Decimal('0.00')


@pytest.mark.unit
def test_get_total_debts():
    """Test get_total_debts method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = Decimal('25000.00')

        repo = ReportingRepository(database=mock_db)

        result = repo.get_total_debts(tenant_id='test_tenant')

        assert result == Decimal('25000.00')


@pytest.mark.unit
def test_get_total_debts_no_tenant():
    """Test get_total_debts without tenant_id"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.scalar.return_value = Decimal('15000.00')

        repo = ReportingRepository(database=mock_db)

        result = repo.get_total_debts()

        assert result == Decimal('15000.00')


@pytest.mark.unit
def test_get_total_debts_null():
    """Test get_total_debts when result is None"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    with patch('repositories.reporting_repository.db.session.query') as mock_query:
        mock_query.return_value.filter.return_value.filter.return_value.scalar.return_value = None

        repo = ReportingRepository(database=mock_db)

        result = repo.get_total_debts(tenant_id='test_tenant')

        assert result == Decimal('0.00')


@pytest.mark.integration
def test_get_transactions_by_date_range(app):
    """Date-range query returns only tenant-scoped records in the inclusive range."""
    from models import Transaction, db

    with app.app_context():
        db.session.add_all([
            Transaction(
                date='2025-01-15', category='Range', description='Included',
                type='Gider', status='Ödendi', amount=100, tenant_id='default'
            ),
            Transaction(
                date='2026-01-15', category='Range', description='Excluded',
                type='Gider', status='Ödendi', amount=100, tenant_id='default'
            ),
        ])
        db.session.commit()
        result = ReportingRepository(database=db).get_transactions_by_date_range(
            '2025-01-01', '2025-12-31', tenant_id='default'
        )

    assert [transaction.description for transaction in result] == ['Included']


@pytest.mark.integration
def test_get_transactions_by_date_range_no_tenant(app):
    """Date-range query without tenant filter returns the isolated in-range record."""
    from models import Transaction, db

    with app.app_context():
        db.session.add(Transaction(
            date='2025-01-15', category='Range', description='Global included',
            type='Gelir', status='Ödendi', amount=200, tenant_id='default'
        ))
        db.session.commit()
        result = ReportingRepository(database=db).get_transactions_by_date_range(
            '2025-01-01', '2025-12-31'
        )

    assert [transaction.description for transaction in result] == ['Global included']


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
    mock_transaction.type = 'Gider'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.50
    mock_transaction.origin = 'manual'

    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '100,50'

        result = repo._serialize_calendar_tx(mock_transaction)

        assert result['id'] == 1
        assert result['category'] == 'Test Category'
        assert result['description'] == 'Test Description'
        assert result['note'] == 'Test Note'
        assert result['type'] == 'Gider'
        assert result['status'] == 'Ödendi'
        assert result['amount'] == 100.50
        assert result['amount_fmt'] == '100,50'
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
    mock_transaction.type = 'Gider'
    mock_transaction.status = 'Ödendi'
    mock_transaction.amount = 100.50
    mock_transaction.origin = None

    with patch('utils.format_utils.format_money') as mock_format_money:
        mock_format_money.return_value = '100,50'

        result = repo._serialize_calendar_tx(mock_transaction)

        assert result['description'] == ''
        assert result['note'] == ''


@pytest.mark.integration
def test_get_calendar_month_data(app):
    """Calendar data groups real income and expense transactions by day."""
    from models import Transaction, db

    with app.app_context():
        db.session.add_all([
            Transaction(
                date='2025-01-15', category='Salary', description='Monthly Salary',
                type='Gelir', status='Ödendi', amount=1000, tenant_id='default'
            ),
            Transaction(
                date='2025-01-15', category='Rent', description='Monthly Rent',
                type='Gider', status='Ödendi', amount=500, tenant_id='default'
            ),
        ])
        db.session.commit()
        result = ReportingRepository(database=db).get_calendar_month_data(
            2025, 1, tenant_id='default'
        )

    assert '2025-01-15' in result
    assert len(result['2025-01-15']['income']) == 1
    assert len(result['2025-01-15']['expense']) == 1
    assert result['2025-01-15']['income_total'] == 1000.00
    assert result['2025-01-15']['expense_total'] == 500.00
    assert result['2025-01-15']['net'] == 500.00


@pytest.mark.integration
def test_get_calendar_month_data_no_tenant(app):
    """Calendar data without a tenant filter returns an empty isolated month."""
    from models import db

    with app.app_context():
        result = ReportingRepository(database=db).get_calendar_month_data(2025, 1)

    assert result == {}


@pytest.mark.integration
def test_get_calendar_month_data_investment(app):
    """Calendar data keeps investment transactions separate from expenses."""
    from models import Transaction, db

    with app.app_context():
        db.session.add(Transaction(
            date='2025-01-15', category='Stocks', description='Stock Purchase',
            type='Yatırım', status='Ödendi', amount=2000, tenant_id='default'
        ))
        db.session.commit()
        result = ReportingRepository(database=db).get_calendar_month_data(
            2025, 1, tenant_id='default'
        )

    assert len(result['2025-01-15']['investment']) == 1
    assert result['2025-01-15']['investment_total'] == 2000.00
    assert result['2025-01-15']['net'] == -2000.00


@pytest.mark.integration
def test_get_pending_payments(app):
    """Pending payments return only unpaid expense transactions."""
    from models import Transaction, db

    with app.app_context():
        db.session.add_all([
            Transaction(
                date='2025-02-01', category='Credit', description='Bekleyen',
                type='Gider', status='Bekliyor', amount=300, tenant_id='default'
            ),
            Transaction(
                date='2025-02-02', category='Credit', description='Ödenen',
                type='Gider', status='Ödendi', amount=400, tenant_id='default'
            ),
        ])
        db.session.commit()
        result = ReportingRepository(database=db).get_pending_payments(
            '2025-01-01', '2025-12-31', tenant_id='default'
        )

    assert len(result) == 1
    assert result[0].description == 'Bekleyen'


@pytest.mark.integration
def test_get_pending_payments_no_tenant(app):
    """Pending payments without tenant filter can return the isolated record."""
    from models import Transaction, db

    with app.app_context():
        db.session.add(Transaction(
            date='2025-02-01', category='Credit', description='Global pending',
            type='Gider', status='Bekliyor', amount=300, tenant_id='default'
        ))
        db.session.commit()
        result = ReportingRepository(database=db).get_pending_payments(
            '2025-01-01', '2025-12-31'
        )

    assert len(result) == 1
    assert result[0].description == 'Global pending'

@pytest.mark.integration
def test_reporting_repository_ignores_soft_deleted_transactions(app):
    """Soft-deleted transactions (is_deleted=True) must not appear in calendar or pending queries."""
    from models import Transaction, db

    with app.app_context():
        db.session.add_all([
            Transaction(
                date='2026-10-15', category='Kredi', description='Aktif Bekleyen',
                type='Gider', status='Bekliyor', amount=1000, tenant_id='default', is_deleted=False
            ),
            Transaction(
                date='2026-10-15', category='Kredi', description='Silinmiş Bekleyen',
                type='Gider', status='Bekliyor', amount=2000, tenant_id='default', is_deleted=True
            ),
        ])
        db.session.commit()
        repo = ReportingRepository(database=db)

        # Test pending payments
        pending = repo.get_pending_payments('2026-10-01', '2026-10-31', tenant_id='default')
        assert any(t.description == 'Aktif Bekleyen' for t in pending)
        assert not any(t.description == 'Silinmiş Bekleyen' for t in pending)

        # Test calendar month data
        month_data = repo.get_calendar_month_data(2026, 10, tenant_id='default')
        oct_15_expenses = [t['description'] for t in month_data.get('2026-10-15', {}).get('expense', [])]
        assert 'Aktif Bekleyen' in oct_15_expenses
        assert 'Silinmiş Bekleyen' not in oct_15_expenses


@pytest.mark.unit
def test_reporting_repository_module_has_required_imports():
    """Test reporting_repository module has required imports"""
    import repositories.reporting_repository as reporting_repo_module

    # Custom imports
    assert hasattr(reporting_repo_module, 'Asset')
    assert hasattr(reporting_repo_module, 'RecurringPlan')
    assert hasattr(reporting_repo_module, 'Transaction')
    assert hasattr(reporting_repo_module, 'BaseRepository')
    assert hasattr(reporting_repo_module, 'ReportingRepositoryContract')
