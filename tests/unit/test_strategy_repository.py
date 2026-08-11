"""
Unit Tests - Strategy Repository
Strategy settings repository tests
"""

import pytest
from unittest.mock import Mock, patch
from repositories.strategy_repository import StrategyRepository


@pytest.mark.unit
def test_strategy_repository_module_imports():
    """Test strategy_repository module can be imported"""
    from repositories.strategy_repository import StrategyRepository
    assert StrategyRepository is not None


@pytest.mark.unit
def test_strategy_repository_module_structure():
    """Test strategy_repository module structure"""
    import repositories.strategy_repository as strategy_module
    
    # Check for expected class
    assert hasattr(strategy_module, 'StrategyRepository')


@pytest.mark.unit
def test_strategy_repository_init():
    """Test StrategyRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = StrategyRepository(database=mock_db)
    
    assert repo.db == mock_db
    assert repo.session == mock_session


@pytest.mark.unit
def test_strategy_repository_inheritance():
    """Test StrategyRepository inherits from BaseRepository"""
    from repositories.strategy_repository import StrategyRepository
    from repositories.base import BaseRepository
    
    assert issubclass(StrategyRepository, BaseRepository)


@pytest.mark.unit
def test_get_settings_for_user():
    """Test get_settings_for_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = StrategyRepository(database=mock_db)
    
    mock_settings = Mock()
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_settings
    
    with patch('repositories.strategy_repository.StrategySettings') as mock_settings_class:
        mock_settings_class.query = mock_query
        
        result = repo.get_settings_for_user(user_id=1)
        
        assert result == mock_settings
        mock_query.filter_by.assert_called_once_with(user_id=1)


@pytest.mark.unit
def test_get_settings_for_user_not_found():
    """Test get_settings_for_user when settings not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = StrategyRepository(database=mock_db)
    
    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = None
    
    with patch('repositories.strategy_repository.StrategySettings') as mock_settings_class:
        mock_settings_class.query = mock_query
        
        result = repo.get_settings_for_user(user_id=1)
        
        assert result is None


@pytest.mark.unit
def test_create_settings_for_user():
    """Test create_settings_for_user method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = StrategyRepository(database=mock_db)
    repo.add = Mock()
    repo.commit = Mock()
    
    mock_settings = Mock()
    mock_settings.id = 1
    
    with patch('repositories.strategy_repository.StrategySettings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        
        result = repo.create_settings_for_user(user_id=1)
        
        assert result == mock_settings
        mock_settings_class.assert_called_once_with(user_id=1)
        repo.add.assert_called_once_with(mock_settings)
        repo.commit.assert_called_once()


@pytest.mark.unit
def test_strategy_repository_has_required_methods():
    """Test StrategyRepository has required methods"""
    from repositories.strategy_repository import StrategyRepository
    
    repo = StrategyRepository(database=Mock())
    
    assert hasattr(repo, 'get_settings_for_user')
    assert hasattr(repo, 'create_settings_for_user')
    assert callable(repo.get_settings_for_user)
    assert callable(repo.create_settings_for_user)
