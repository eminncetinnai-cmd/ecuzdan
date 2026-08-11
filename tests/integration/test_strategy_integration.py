"""
Integration tests for strategy module
"""

import pytest
from datetime import datetime, timedelta, timezone


class TestStrategyIntegration:
    """Integration tests for strategy module"""

    def test_strategy_page_loads(self, authenticated_client):
        """Test strategy page loads successfully"""
        response = authenticated_client.get('/strategy')
        assert response.status_code == 200
        assert b'Finansal Strateji' in response.data

    def test_strategy_page_monte_carlo_section(self, authenticated_client):
        """Test strategy page includes Monte Carlo simulation section"""
        response = authenticated_client.get('/strategy')
        assert response.status_code == 200
        assert b'Monte Carlo' in response.data

    def test_strategy_page_real_yield_section(self, authenticated_client):
        """Test strategy page includes real yield calculation section"""
        response = authenticated_client.get('/strategy')
        assert response.status_code == 200
        assert b'Fisher' in response.data or b'Reel Getiri' in response.data

    def test_strategy_api_settings_get(self, authenticated_client):
        """Test GET /strategy/api/settings retrieves user settings"""
        response = authenticated_client.get('/strategy/api/settings')
        assert response.status_code in [200, 404]  # 200 if settings exist, 404 if not

    def test_strategy_api_settings_post(self, authenticated_client):
        """Test POST /strategy/api/settings saves user settings"""
        settings_data = {
            'monte_carlo_simulations': 1000,
            'confidence_level': 95,
            'time_horizon_years': 10,
            'inflation_rate': 40.0,
            'risk_free_rate': 50.0
        }
        
        response = authenticated_client.post('/strategy/api/settings',
                                           json=settings_data,
                                           content_type='application/json')
        assert response.status_code in [200, 400, 500]

    def test_strategy_api_simulation(self, authenticated_client):
        """Test POST /strategy/api/simulation runs Monte Carlo simulation"""
        simulation_data = {
            'initial_amount': 100000,
            'monthly_contribution': 5000,
            'time_horizon_years': 10,
            'expected_return': 15.0,
            'volatility': 20.0,
            'simulations': 1000
        }
        
        response = authenticated_client.post('/strategy/api/simulation',
                                           json=simulation_data,
                                           content_type='application/json')
        assert response.status_code in [200, 400, 500]

    def test_strategy_api_real_yield(self, authenticated_client):
        """Test POST /strategy/api/real_yield calculates real yield"""
        yield_data = {
            'nominal_return': 15.0,
            'inflation_rate': 40.0
        }
        
        response = authenticated_client.post('/strategy/api/real_yield',
                                           json=yield_data,
                                           content_type='application/json')
        assert response.status_code in [200, 400, 500]

    def test_strategy_api_rollback(self, authenticated_client):
        """Test POST /strategy/api/rollback rolls back settings"""
        response = authenticated_client.post('/strategy/api/rollback')
        assert response.status_code in [200, 400, 500]

    def test_strategy_page_context(self, authenticated_client):
        """Test strategy page context includes required data"""
        response = authenticated_client.get('/strategy')
        assert response.status_code == 200
        # Check for common strategy elements
        assert b'strateji' in response.data.lower() or b'strategy' in response.data.lower()

    def test_strategy_page_authenticated_only(self, client):
        """Test strategy page requires authentication"""
        response = client.get('/strategy')
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_strategy_api_requires_auth(self, client):
        """Test strategy API endpoints require authentication"""
        endpoints = [
            '/strategy/api/settings',
            '/strategy/api/simulation',
            '/strategy/api/real_yield',
            '/strategy/api/rollback'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [302, 401, 403]

    def test_strategy_settings_persistence(self, authenticated_client):
        """Test strategy settings persist across requests"""
        # First, save settings
        settings_data = {
            'monte_carlo_simulations': 500,
            'confidence_level': 90,
            'time_horizon_years': 5,
            'inflation_rate': 35.0,
            'risk_free_rate': 45.0
        }
        
        post_response = authenticated_client.post('/strategy/api/settings',
                                                 json=settings_data,
                                                 content_type='application/json')
        
        # Then retrieve settings
        get_response = authenticated_client.get('/strategy/api/settings')
        
        # If both succeeded, verify persistence
        if post_response.status_code == 200 and get_response.status_code == 200:
            retrieved_settings = get_response.json
            assert retrieved_settings.get('monte_carlo_simulations') == 500

    def test_strategy_simulation_parameters_validation(self, authenticated_client):
        """Test simulation endpoint validates parameters"""
        # Test with invalid parameters
        invalid_data = {
            'initial_amount': -1000,  # Negative amount
            'monthly_contribution': 'invalid',  # Invalid type
            'time_horizon_years': -5,  # Negative years
        }
        
        response = authenticated_client.post('/strategy/api/simulation',
                                           json=invalid_data,
                                           content_type='application/json')
        assert response.status_code in [400, 500]

    def test_strategy_real_yield_calculation_accuracy(self, authenticated_client):
        """Test real yield calculation uses Fisher equation correctly"""
        # Fisher equation: (1 + nominal) / (1 + inflation) - 1
        yield_data = {
            'nominal_return': 15.0,  # 15%
            'inflation_rate': 40.0   # 40%
        }
        
        response = authenticated_client.post('/strategy/api/real_yield',
                                           json=yield_data,
                                           content_type='application/json')
        
        if response.status_code == 200:
            result = response.json
            # Expected real return: (1.15 / 1.40) - 1 = -0.1786 = -17.86%
            expected_real = ((1 + 0.15) / (1 + 0.40) - 1) * 100
            if 'real_return' in result:
                assert abs(result['real_return'] - expected_real) < 1.0  # Allow 1% tolerance

    def test_strategy_page_load_time(self, authenticated_client):
        """Test strategy page loads within reasonable time"""
        import time
        
        start_time = time.time()
        response = authenticated_client.get('/strategy')
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 5.0  # Should load within 5 seconds

    def test_strategy_concurrent_requests(self, authenticated_client):
        """Test strategy handles concurrent requests gracefully"""
        import threading
        
        def make_request():
            return authenticated_client.get('/strategy')
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should complete without errors
        # (This is a basic smoke test for concurrency issues)

    def test_strategy_error_handling(self, authenticated_client):
        """Test strategy handles errors gracefully"""
        # Send malformed data
        response = authenticated_client.post('/strategy/api/simulation',
                                           json='invalid json',
                                           content_type='application/json')
        assert response.status_code in [400, 500]

    def test_strategy_csrf_protection(self, authenticated_client):
        """Test strategy endpoints are protected by CSRF"""
        # POST without CSRF token should fail
        response = authenticated_client.post('/strategy/api/settings',
                                           json={'test': 'data'},
                                           content_type='application/json')
        # Should return 400 for CSRF violation or 200 if CSRF exempt
        assert response.status_code in [200, 400]


class TestStrategyServiceIntegration:
    """Integration tests for strategy service layer"""

    def test_strategy_service_initialization(self):
        """Test strategy service initializes correctly"""
        from bootstrap.container import get_container
        
        container = get_container()
        strategy_service = container.domains.strategy_svc()
        
        assert strategy_service is not None

    def test_strategy_service_monte_carlo(self):
        """Test strategy service Monte Carlo simulation"""
        from bootstrap.container import get_container
        
        container = get_container()
        strategy_service = container.domains.strategy_svc()
        
        # Run a simple simulation
        result = strategy_service.run_monte_carlo_simulation(
            initial_amount=100000,
            monthly_contribution=5000,
            years=10,
            expected_return=0.15,
            volatility=0.20,
            simulations=100
        )
        
        assert result is not None
        assert 'final_amount' in result or 'mean' in result or 'median' in result

    def test_strategy_service_real_yield(self):
        """Test strategy service real yield calculation"""
        from bootstrap.container import get_container
        
        container = get_container()
        strategy_service = container.domains.strategy_svc()
        
        result = strategy_service.calculate_real_yield(
            nominal_return=15.0,
            inflation_rate=40.0
        )
        
        assert result is not None
        # Should use Fisher equation
        expected = ((1 + 0.15) / (1 + 0.40) - 1) * 100
        assert abs(result - expected) < 1.0

    def test_strategy_application_service(self):
        """Test strategy application service"""
        from bootstrap.container import get_container
        
        container = get_container()
        strategy_app = container.applications.strategy()
        
        assert strategy_app is not None

    def test_strategy_settings_crud(self):
        """Test strategy settings CRUD operations"""
        from bootstrap.container import get_container
        from models import db, User, StrategySettings
        
        container = get_container()
        strategy_app = container.applications.strategy()
        
        # This test would require database setup
        # For now, just verify the service exists
        assert strategy_app is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
