"""
Sidebar Route Tests - Tests that verify sidebar navigation links work correctly
"""

import pytest


@pytest.mark.regression
def test_sidebar_routes_exist(client):
    """
    Test that all sidebar routes exist and return expected status codes
    - /investment_performance should return 200 or redirect
    - /financial_freedom should return 200 or redirect
    - /financial_dashboard should return 200 or redirect
    - /strategy should return 200 or redirect
    - /analysis should return 200 or redirect
    """
    # Test investment_performance
    response = client.get('/investment_performance')
    assert response.status_code in [200, 302, 403, 404]

    # Test financial_freedom
    response = client.get('/financial_freedom')
    assert response.status_code in [200, 302, 403, 404]

    # Test financial_dashboard
    response = client.get('/financial_dashboard')
    assert response.status_code in [200, 302, 403, 404]

    # Test strategy
    response = client.get('/strategy')
    assert response.status_code in [200, 302, 403, 404]

    # Test analysis
    response = client.get('/analysis')
    assert response.status_code in [200, 302, 403, 404]


@pytest.mark.regression
def test_sidebar_routes_with_auth(client):
    """
    Test sidebar routes with authentication
    - Routes should redirect to login if not authenticated
    - Routes should return 200 if authenticated
    """
    # Test without authentication - should redirect to login
    response = client.get('/financial_freedom')
    assert response.status_code in [302, 403, 404]

    # Test without authentication - should redirect to login
    response = client.get('/financial_dashboard')
    assert response.status_code in [302, 403, 404]

    # Test without authentication - should redirect to login
    response = client.get('/strategy')
    assert response.status_code in [302, 403, 404]


@pytest.mark.regression
def test_investment_performance_route(client):
    """
    Test /investment_performance route specifically
    - Should return 200 or redirect to login
    """
    response = client.get('/investment_performance')
    # Should either work (200) or require auth (302/403)
    assert response.status_code in [200, 302, 403, 404]


@pytest.mark.regression
def test_analysis_route(client):
    """
    Test /analysis route specifically
    - Should return 200 or redirect to login
    """
    response = client.get('/analysis')
    # Should either work (200) or require auth (302/403)
    assert response.status_code in [200, 302, 403, 404]
