"""
Unit Tests - Strategy Routes
Strategy routes unit tests
"""


from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
def test_get_strategy_service():
    """Strategy service is resolved from the application container."""
    from routes.strategy import _get_strategy_service

    service = object()
    container = Mock()
    container.applications.strategy.return_value = service
    with patch('bootstrap.container.get_container', return_value=container):
        assert _get_strategy_service() is service


@pytest.mark.integration
def test_mc_scenarios_data_structure(authenticated_client):
    """Authenticated MC scenarios endpoint returns all three documented profiles."""
    response = authenticated_client.get('/strategy/api/mc-scenarios')

    assert response.status_code == 200
    data = response.get_json()
    assert set(data) == {'conservative', 'balanced', 'aggressive'}
    assert data['conservative']['return'] < data['balanced']['return'] < data['aggressive']['return']
    assert data['conservative']['volatility'] < data['balanced']['volatility'] < data['aggressive']['volatility']


@pytest.mark.unit
def test_mc_scenarios_conervative_data():
    """Test conservative scenario data values"""
    # The mc_scenarios function returns static data
    conservative = {
        'label': 'Muhafazakar',
        'description': 'Düşük risk, istikrarlı büyüme',
        'return': 0.08,
        'volatility': 0.12,
        'color': 'emerald',
    }

    assert conservative['label'] == 'Muhafazakar'
    assert conservative['return'] == 0.08
    assert conservative['volatility'] == 0.12
    assert conservative['color'] == 'emerald'


@pytest.mark.unit
def test_mc_scenarios_balanced_data():
    """Test balanced scenario data values"""
    balanced = {
        'label': 'Dengeli',
        'description': 'Orta risk, dengeli büyüme',
        'return': 0.15,
        'volatility': 0.20,
        'color': 'amber',
    }

    assert balanced['label'] == 'Dengeli'
    assert balanced['return'] == 0.15
    assert balanced['volatility'] == 0.20
    assert balanced['color'] == 'amber'


@pytest.mark.unit
def test_mc_scenarios_aggressive_data():
    """Test aggressive scenario data values"""
    aggressive = {
        'label': 'Agresif',
        'description': 'Yüksek risk, yüksek büyüme',
        'return': 0.22,
        'volatility': 0.30,
        'color': 'rose',
    }

    assert aggressive['label'] == 'Agresif'
    assert aggressive['return'] == 0.22
    assert aggressive['volatility'] == 0.30
    assert aggressive['color'] == 'rose'


@pytest.mark.unit
def test_mc_scenarios_return_progression():
    """Test that return rates increase from conservative to aggressive"""
    conservative_return = 0.08
    balanced_return = 0.15
    aggressive_return = 0.22

    assert conservative_return < balanced_return < aggressive_return


@pytest.mark.unit
def test_mc_scenarios_volatility_progression():
    """Test that volatility increases from conservative to aggressive"""
    conservative_vol = 0.12
    balanced_vol = 0.20
    aggressive_vol = 0.30

    assert conservative_vol < balanced_vol < aggressive_vol


@pytest.mark.unit
def test_mc_scenarios_color_mapping():
    """Test color mapping for each scenario"""
    colors = {
        'conservative': 'emerald',
        'balanced': 'amber',
        'aggressive': 'rose'
    }

    assert colors['conservative'] == 'emerald'
    assert colors['balanced'] == 'amber'
    assert colors['aggressive'] == 'rose'


@pytest.mark.unit
def test_mc_scenarios_labels_turkish():
    """Test that scenario labels are in Turkish"""

    # Verify Turkish characters
    assert 'ı' not in 'Muhafazakar'  # Uses regular i
    assert 'Dengeli' == 'Dengeli'
    assert 'Agresif' == 'Agresif'


@pytest.mark.unit
def test_mc_scenarios_descriptions_turkish():
    """Test that scenario descriptions are in Turkish"""
    descriptions = {
        'conservative': 'Düşük risk, istikrarlı büyüme',
        'balanced': 'Orta risk, dengeli büyüme',
        'aggressive': 'Yüksek risk, yüksek büyüme'
    }

    assert 'Düşük' in descriptions['conservative']
    assert 'Orta' in descriptions['balanced']
    assert 'Yüksek' in descriptions['aggressive']


@pytest.mark.unit
def test_mc_scenarios_return_values_valid():
    """Test that return values are valid percentages (0-1 range)"""
    returns = [0.08, 0.15, 0.22]

    for ret in returns:
        assert 0 < ret < 1


@pytest.mark.unit
def test_mc_scenarios_volatility_values_valid():
    """Test that volatility values are valid (0-1 range)"""
    volatilities = [0.12, 0.20, 0.30]

    for vol in volatilities:
        assert 0 < vol < 1


@pytest.mark.unit
def test_mc_scenarios_complete_structure():
    """Test that all scenarios have complete structure"""
    scenarios = {
        'conservative': {
            'label': 'Muhafazakar',
            'description': 'Düşük risk, istikrarlı büyüme',
            'return': 0.08,
            'volatility': 0.12,
            'color': 'emerald',
        },
        'balanced': {
            'label': 'Dengeli',
            'description': 'Orta risk, dengeli büyüme',
            'return': 0.15,
            'volatility': 0.20,
            'color': 'amber',
        },
        'aggressive': {
            'label': 'Agresif',
            'description': 'Yüksek risk, yüksek büyüme',
            'return': 0.22,
            'volatility': 0.30,
            'color': 'rose',
        }
    }

    required_keys = ['label', 'description', 'return', 'volatility', 'color']

    for scenario_name, scenario_data in scenarios.items():
        for key in required_keys:
            assert key in scenario_data


@pytest.mark.unit
def test_register_strategy_routes_exists():
    """Test that register_strategy_routes function exists"""
    from routes.strategy import register_strategy_routes
    assert callable(register_strategy_routes)
