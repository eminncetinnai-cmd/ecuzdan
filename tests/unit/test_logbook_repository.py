"""
Unit Tests - Logbook Repository
Repository for logbook entries and related dropdown data
"""

from unittest.mock import Mock, patch

import pytest

from repositories.logbook_repository import LogbookRepository


@pytest.mark.unit
def test_logbook_repository_class_exists():
    """Test LogbookRepository class exists"""
    assert LogbookRepository is not None


@pytest.mark.unit
def test_logbook_repository_inheritance():
    """Test LogbookRepository inherits from BaseRepository"""
    from repositories.base import BaseRepository

    assert issubclass(LogbookRepository, BaseRepository)


@pytest.mark.unit
def test_logbook_repository_init():
    """Test LogbookRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    assert repo.session == mock_session


@pytest.mark.unit
def test_logbook_repository_imports():
    """Test that LogbookRepository can be imported"""
    from repositories.logbook_repository import LogbookRepository
    assert LogbookRepository is not None


@pytest.mark.unit
def test_logbook_repository_module_structure():
    """Test logbook_repository module structure"""
    import repositories.logbook_repository as logbook_repo_module

    # Check for expected class
    assert hasattr(logbook_repo_module, 'LogbookRepository')

    # Check for expected imports
    assert hasattr(logbook_repo_module, 'Asset')
    assert hasattr(logbook_repo_module, 'LogbookEntry')
    assert hasattr(logbook_repo_module, 'Transaction')
    assert hasattr(logbook_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_query_entries_method_exists():
    """Test query_entries method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'query_entries')
    assert callable(repo.query_entries)


@pytest.mark.unit
def test_list_entries_method_exists():
    """Test list_entries method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'list_entries')
    assert callable(repo.list_entries)


@pytest.mark.unit
def test_paginate_entries_method_exists():
    """Test paginate_entries method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'paginate_entries')
    assert callable(repo.paginate_entries)


@pytest.mark.unit
def test_get_entry_method_exists():
    """Test get_entry method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'get_entry')
    assert callable(repo.get_entry)


@pytest.mark.unit
def test_add_entry_method_exists():
    """Test add_entry method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'add_entry')
    assert callable(repo.add_entry)


@pytest.mark.unit
def test_get_asset_method_exists():
    """Test get_asset method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'get_asset')
    assert callable(repo.get_asset)


@pytest.mark.unit
def test_get_transaction_method_exists():
    """Test get_transaction method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'get_transaction')
    assert callable(repo.get_transaction)


@pytest.mark.unit
def test_list_assets_method_exists():
    """Test list_assets method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'list_assets')
    assert callable(repo.list_assets)


@pytest.mark.unit
def test_list_transactions_method_exists():
    """Test list_transactions method exists"""
    repo = LogbookRepository()
    assert hasattr(repo, 'list_transactions')
    assert callable(repo.list_transactions)


@pytest.mark.unit
def test_logbook_repository_session_attribute():
    """Test LogbookRepository has session attribute"""
    repo = LogbookRepository()
    assert hasattr(repo, 'session')


@pytest.mark.unit
def test_logbook_repository_commit_method():
    """Test LogbookRepository has commit method from base"""
    repo = LogbookRepository()
    assert hasattr(repo, 'commit')
    assert callable(repo.commit)


@pytest.mark.unit
def test_logbook_repository_rollback_method():
    """Test LogbookRepository has rollback method from base"""
    repo = LogbookRepository()
    assert hasattr(repo, 'rollback')
    assert callable(repo.rollback)


@pytest.mark.unit
def test_query_entries_no_filters():
    """Test query_entries with no filters"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_query = Mock()

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.query.filter_by.return_value = mock_query
        result = repo.query_entries('test_tenant')

        assert result == mock_query


@pytest.mark.unit
def test_query_entries_with_category_filter():
    """Test query_entries with category filter"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_query = Mock()
    mock_filtered_query = Mock()

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.query.filter_by.return_value = mock_filtered_query
        mock_filtered_query.filter_by.return_value = mock_query

        result = repo.query_entries('test_tenant', {'category': 'Test Category'})

        assert result == mock_query


@pytest.mark.unit
def test_query_entries_with_sentiment_filter():
    """Test query_entries with sentiment filter"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_query = Mock()
    mock_filtered_query = Mock()

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.query.filter_by.return_value = mock_filtered_query
        mock_filtered_query.filter_by.return_value = mock_query

        result = repo.query_entries('test_tenant', {'sentiment': 'positive'})

        assert result == mock_query


@pytest.mark.integration
def test_query_entries_with_date_filters(app, test_user):
    """Date-from and date-to filters compose correctly."""
    from models import LogbookEntry, db

    with app.app_context():
        db.session.add_all([
            LogbookEntry(
                tenant_id='default', user_id=test_user.id, title='Ocak',
                content='Ocak notu', entry_date='2025-01-15', category='Finansal'
            ),
            LogbookEntry(
                tenant_id='default', user_id=test_user.id, title='Şubat',
                content='Şubat notu', entry_date='2025-02-15', category='Yatırım'
            ),
        ])
        db.session.commit()

        result = LogbookRepository(database=db).query_entries(
            'default', {'date_from': '2025-02-01', 'date_to': '2025-02-28'}
        ).all()

    assert [entry.title for entry in result] == ['Şubat']


@pytest.mark.unit
def test_list_entries_default_order():
    """Test list_entries with default descending order"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_query = Mock()
    mock_ordered_query = Mock()
    mock_entries = [Mock(), Mock()]

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.entry_date.desc.return_value = Mock()
        mock_query.order_by.return_value = mock_ordered_query
        mock_ordered_query.all.return_value = mock_entries
        repo.query_entries = Mock(return_value=mock_query)

        result = repo.list_entries('test_tenant')

        assert result == mock_entries


@pytest.mark.unit
def test_list_entries_ascending_order():
    """Test list_entries with ascending order"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_query = Mock()
    mock_ordered_query = Mock()
    mock_entries = [Mock(), Mock()]

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.entry_date.asc.return_value = Mock()
        mock_query.order_by.return_value = mock_ordered_query
        mock_ordered_query.all.return_value = mock_entries
        repo.query_entries = Mock(return_value=mock_query)

        result = repo.list_entries('test_tenant', ascending=True)

        assert result == mock_entries


@pytest.mark.unit
def test_paginate_entries():
    """Test paginate_entries method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_query = Mock()
    mock_ordered_query = Mock()
    mock_paginated = Mock()

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.entry_date.desc.return_value = Mock()
        mock_query.order_by.return_value = mock_ordered_query
        mock_ordered_query.paginate.return_value = mock_paginated
        repo.query_entries = Mock(return_value=mock_query)

        result = repo.paginate_entries('test_tenant', page=2, per_page=50)

        assert result == mock_paginated


@pytest.mark.integration
def test_query_entries_with_date_from_filter(app, test_user):
    """Date-from filter excludes earlier entries."""
    from models import LogbookEntry, db

    with app.app_context():
        db.session.add_all([
            LogbookEntry(
                tenant_id='default', user_id=test_user.id, title='Eski',
                content='Eski not', entry_date='2025-01-01'
            ),
            LogbookEntry(
                tenant_id='default', user_id=test_user.id, title='Yeni',
                content='Yeni not', entry_date='2025-02-01'
            ),
        ])
        db.session.commit()
        result = LogbookRepository(database=db).query_entries(
            'default', {'date_from': '2025-02-01'}
        ).all()

    assert [entry.title for entry in result] == ['Yeni']


@pytest.mark.integration
def test_query_entries_with_date_to_filter(app, test_user):
    """Date-to filter excludes later entries."""
    from models import LogbookEntry, db

    with app.app_context():
        db.session.add_all([
            LogbookEntry(
                tenant_id='default', user_id=test_user.id, title='Erken',
                content='Erken not', entry_date='2025-01-01'
            ),
            LogbookEntry(
                tenant_id='default', user_id=test_user.id, title='Geç',
                content='Geç not', entry_date='2025-02-01'
            ),
        ])
        db.session.commit()
        result = LogbookRepository(database=db).query_entries(
            'default', {'date_to': '2025-01-31'}
        ).all()

    assert [entry.title for entry in result] == ['Erken']


@pytest.mark.integration
def test_query_entries_with_both_date_filters(app, test_user):
    """Both date boundaries are inclusive."""
    from models import LogbookEntry, db

    with app.app_context():
        db.session.add(LogbookEntry(
            tenant_id='default', user_id=test_user.id, title='Sınır',
            content='Sınır not', entry_date='2025-01-31'
        ))
        db.session.commit()
        result = LogbookRepository(database=db).query_entries(
            'default', {'date_from': '2025-01-31', 'date_to': '2025-01-31'}
        ).all()

    assert [entry.title for entry in result] == ['Sınır']


@pytest.mark.unit
def test_get_entry():
    """Test get_entry method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_entry = Mock()

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.query.filter_by.return_value.first.return_value = mock_entry

        result = repo.get_entry(1, 'test_tenant')

        assert result == mock_entry


@pytest.mark.unit
def test_add_entry():
    """Test add_entry method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_entry = Mock()

    with patch('repositories.logbook_repository.LogbookEntry') as mock_entry_class:
        mock_entry_class.return_value = mock_entry
        repo.add = Mock(return_value=mock_entry)

        result = repo.add_entry(category='Test', content='Test content', tenant_id='test_tenant')

        assert result == mock_entry


@pytest.mark.unit
def test_get_asset():
    """Test get_asset method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_asset = Mock()

    with patch('repositories.logbook_repository.Asset') as mock_asset_class:
        mock_asset_class.query.filter_by.return_value.first.return_value = mock_asset

        result = repo.get_asset(1, 'test_tenant')

        assert result == mock_asset


@pytest.mark.unit
def test_get_transaction():
    """Test get_transaction method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_transaction = Mock()

    with patch('repositories.logbook_repository.Transaction') as mock_transaction_class:
        mock_transaction_class.query.filter_by.return_value.first.return_value = mock_transaction

        result = repo.get_transaction(1, 'test_tenant')

        assert result == mock_transaction


@pytest.mark.unit
def test_list_assets():
    """Test list_assets method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_assets = [Mock(), Mock()]
    mock_query = Mock()

    with patch('repositories.logbook_repository.Asset') as mock_asset_class:
        mock_asset_class.query.filter_by.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_assets

        result = repo.list_assets('test_tenant')

        assert result == mock_assets


@pytest.mark.unit
def test_list_transactions():
    """Test list_transactions method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_transactions = [Mock(), Mock()]
    mock_query = Mock()

    with patch('repositories.logbook_repository.Transaction') as mock_transaction_class:
        mock_transaction_class.query.filter_by.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_transactions

        result = repo.list_transactions('test_tenant', limit=50)

        assert result == mock_transactions


@pytest.mark.unit
def test_list_transactions_default_limit():
    """Test list_transactions with default limit"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session

    repo = LogbookRepository(database=mock_db)
    mock_transactions = [Mock()]
    mock_query = Mock()

    with patch('repositories.logbook_repository.Transaction') as mock_transaction_class:
        mock_transaction_class.query.filter_by.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_transactions

        result = repo.list_transactions('test_tenant')

        assert result == mock_transactions
        mock_query.order_by.return_value.limit.assert_called_once_with(100)
