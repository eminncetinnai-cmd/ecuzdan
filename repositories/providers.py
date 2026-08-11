"""Repository-level providers for Composition Root examples.

Expose helper that returns the shared RepositoryProvider from bootstrap.get_container().
"""
from bootstrap import get_container


def get_repository_provider():
    return get_container().repositories
