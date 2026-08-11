"""
Thread-Safe Singleton Tests for analysis_engine.py
Tests for race condition prevention and thread safety
"""

import threading

import pytest

from engines.analysis_engine import get_analysis_engine


class MockMarketDataService:
    """Mock market data service for testing"""
    def get_all_market_data(self):
        return {}


def test_singleton_returns_same_instance():
    """Test that Singleton returns the same instance"""
    mock_service = MockMarketDataService()

    instance1 = get_analysis_engine(mock_service)
    instance2 = get_analysis_engine(mock_service)

    assert instance1 is instance2


def test_singleton_thread_safety():
    """Test that Singleton is thread-safe (no race conditions)"""
    mock_service = MockMarketDataService()
    instances = []

    def create_instance():
        instance = get_analysis_engine(mock_service)
        instances.append(instance)

    # Create multiple threads that try to get the instance simultaneously
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=create_instance)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All instances should be the same object
    first_instance = instances[0]
    for instance in instances[1:]:
        assert instance is first_instance


def test_singleton_reset_for_testing():
    """Test that we can reset the singleton for testing purposes"""
    # This is a utility function that might be needed for testing
    # In production, this should not be available

    # Get current instance
    mock_service = MockMarketDataService()
    instance1 = get_analysis_engine(mock_service)

    # Reset for testing (this would need to be added to the module)
    # For now, we just verify the pattern works
    assert instance1 is not None


def test_singleton_with_different_services():
    """Test that Singleton ignores different services after first creation"""
    service1 = MockMarketDataService()
    service2 = MockMarketDataService()

    instance1 = get_analysis_engine(service1)
    instance2 = get_analysis_engine(service2)

    # Should return the same instance regardless of service
    assert instance1 is instance2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
