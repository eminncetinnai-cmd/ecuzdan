"""
Unit Tests - Repository Providers
Repository-level providers for Composition Root examples tests
"""

from unittest.mock import Mock, patch

import pytest

from repositories.providers import get_repository_provider


@pytest.mark.unit
def test_providers_module_imports():
    """Test providers module can be imported"""
    from repositories.providers import get_repository_provider
    assert get_repository_provider is not None


@pytest.mark.unit
def test_providers_module_structure():
    """Test providers module structure"""
    import repositories.providers as providers_module

    # Check for expected function
    assert hasattr(providers_module, 'get_repository_provider')


@pytest.mark.unit
def test_get_repository_provider_function():
    """Test get_repository_provider function exists"""
    assert callable(get_repository_provider)


@pytest.mark.unit
def test_get_repository_provider_calls_get_container():
    """Test get_repository_provider calls get_container"""
    mock_container = Mock()
    mock_container.repositories = Mock()

    with patch('repositories.providers.get_container', return_value=mock_container):
        result = get_repository_provider()

        assert result == mock_container.repositories


@pytest.mark.unit
def test_get_repository_provider_returns_repositories():
    """Test get_repository_provider returns repositories attribute"""
    mock_container = Mock()
    mock_repositories = Mock()
    mock_container.repositories = mock_repositories

    with patch('repositories.providers.get_container', return_value=mock_container):
        result = get_repository_provider()

        assert result is mock_repositories
