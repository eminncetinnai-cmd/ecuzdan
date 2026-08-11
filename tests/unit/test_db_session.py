"""
Unit Tests - DB Session
Database session utilities for route error handling tests
"""

import pytest
from unittest.mock import Mock, patch
from utils.db_session import rollback_session, remove_session


@pytest.mark.unit
def test_db_session_module_imports():
    """Test db_session module can be imported"""
    from utils.db_session import rollback_session
    assert rollback_session is not None


@pytest.mark.unit
def test_db_session_module_structure():
    """Test db_session module structure"""
    import utils.db_session as session_module
    
    # Check for expected functions
    assert hasattr(session_module, 'rollback_session')
    assert hasattr(session_module, 'remove_session')


@pytest.mark.unit
def test_rollback_session():
    """Test rollback_session calls db.session.rollback"""
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session
    
    with patch('utils.db_session.db', mock_db):
        rollback_session()
        
        mock_session.rollback.assert_called_once()


@pytest.mark.unit
def test_remove_session():
    """Test remove_session calls db.session.remove"""
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session
    
    with patch('utils.db_session.db', mock_db):
        remove_session()
        
        mock_session.remove.assert_called_once()


@pytest.mark.unit
def test_rollback_session_callable():
    """Test rollback_session is callable"""
    assert callable(rollback_session)


@pytest.mark.unit
def test_remove_session_callable():
    """Test remove_session is callable"""
    assert callable(remove_session)
