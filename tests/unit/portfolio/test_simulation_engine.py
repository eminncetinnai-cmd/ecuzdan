"""Unit tests for SimulationEngine (domain/portfolio/services/simulation_engine.py).

Tests Monte Carlo growth simulations, asset allocation scenario comparisons,
retirement withdrawal scenarios, and emergency fund simulations.
"""

import pytest
from domain.portfolio.services.simulation_engine import SimulationEngine


def test_simulate_investment_growth_full_statistics():
    res = SimulationEngine.simulate_investment_growth(
        initial_amount=10000.0,
        annual_return=15.0,
        years=3,
        monthly_contribution=500.0,
        volatility=12.0,
        simulations=50,
    )
    assert res["initial_amount"] == 10000.0
    assert res["years"] == 3
    assert res["monthly_contribution"] == 500.0
    results = res["results"]
    assert results["mean"] > 10000.0
    assert results["median"] > 0
    assert results["min"] <= results["median"] <= results["max"]
    assert results["deterministic"] > 10000.0
    assert "p10" in results["percentiles"]
    assert "p25" in results["percentiles"]
    assert "p75" in results["percentiles"]
    assert "p90" in results["percentiles"]
    assert "Moderate volatility" in res["interpretation"]


def test_simulate_investment_growth_volatility_interpretations():
    assert "Low volatility scenario" in SimulationEngine._interpretate_simulation(100, 100, 5.0)
    assert "Moderate volatility" in SimulationEngine._interpretate_simulation(100, 100, 15.0)
    assert "High volatility" in SimulationEngine._interpretate_simulation(100, 100, 25.0)
    assert "Very high volatility" in SimulationEngine._interpretate_simulation(100, 100, 35.0)


def test_simulate_asset_allocation_change():
    current_alloc = {"hisse": 40.0, "altin": 30.0, "nakit": 30.0}
    new_alloc = {"hisse": 60.0, "altin": 30.0, "nakit": 10.0}
    returns = {"hisse": 25.0, "altin": 18.0, "nakit": 10.0}
    vols = {"hisse": 22.0, "altin": 15.0, "nakit": 2.0}
    corrs = {
        "hisse": {"hisse": 1.0, "altin": 0.2, "nakit": 0.0},
        "altin": {"hisse": 0.2, "altin": 1.0, "nakit": 0.0},
        "nakit": {"hisse": 0.0, "altin": 0.0, "nakit": 1.0},
    }

    res = SimulationEngine.simulate_asset_allocation_change(
        current_allocation=current_alloc,
        new_allocation=new_alloc,
        expected_returns=returns,
        volatilities=vols,
        correlations=corrs,
        portfolio_value=100000.0,
        years=2,
    )

    assert "current_metrics" in res
    assert "new_metrics" in res
    assert res["current_metrics"]["expected_return"] > 0
    assert res["new_metrics"]["expected_return"] > res["current_metrics"]["expected_return"]
    assert "simulation_comparison" in res
    assert "recommendation" in res


def test_compare_allocations_matrix():
    # 1. Higher return, lower risk
    rec1 = SimulationEngine._compare_allocations(0.10, 0.15, 0.20, 0.15)
    assert "Recommended: Higher return" in rec1

    # 2. Higher return, higher risk
    rec2 = SimulationEngine._compare_allocations(0.10, 0.15, 0.15, 0.20)
    assert "Consider: Higher return" in rec2

    # 3. Lower return, lower risk
    rec3 = SimulationEngine._compare_allocations(0.15, 0.10, 0.20, 0.15)
    assert "Consider: Lower return" in rec3

    # 4. Lower return, higher risk
    rec4 = SimulationEngine._compare_allocations(0.15, 0.10, 0.15, 0.20)
    assert "Not recommended: Lower return" in rec4


def test_simulate_withdrawal_scenario():
    res = SimulationEngine.simulate_withdrawal_scenario(
        portfolio_value=500000.0,
        annual_withdrawal=20000.0,
        annual_return=8.0,
        years=5,
        inflation=2.5,
        simulations=50,
    )
    assert res["portfolio_value"] == 500000.0
    assert res["withdrawal_rate"] == 4.0
    assert "results" in res
    assert 0 <= res["results"]["success_rate"] <= 100
    assert "interpretation" in res


def test_interpretate_withdrawal_ratings():
    assert "Excellent:" in SimulationEngine._interpretate_withdrawal(95.0, 4.0)
    assert "Good:" in SimulationEngine._interpretate_withdrawal(80.0, 5.0)
    assert "Moderate:" in SimulationEngine._interpretate_withdrawal(60.0, 6.0)
    assert "Risky:" in SimulationEngine._interpretate_withdrawal(40.0, 8.0)


def test_simulate_emergency_fund():
    res = SimulationEngine.simulate_emergency_fund(
        monthly_expenses=5000.0,
        months_needed=6,
        current_savings=10000.0,
        monthly_savings=2500.0,
        months_to_build=12,
    )
    assert res["target_amount"] == 30000.0
    assert res["current_coverage"] == 2.0
    assert res["results"]["target_met"] is True
    assert res["results"]["months_to_target"] is not None
    assert len(res["results"]["projection"]) == 13


def test_simulate_withdrawal_scenario_depletion():
    # Force portfolio ruin so value <= 0 is hit (line 257)
    res = SimulationEngine.simulate_withdrawal_scenario(
        portfolio_value=50000.0,
        annual_withdrawal=40000.0,
        annual_return=2.0,
        years=5,
        inflation=5.0,
        simulations=20,
    )
    assert res["results"]["success_rate"] < 100


def test_recommend_emergency_fund_ratings():
    assert "Emergency fund target met" in SimulationEngine._recommend_emergency_fund(6.0, 6, True)
    assert "Progress:" in SimulationEngine._recommend_emergency_fund(4.0, 6, False)
    # When target_months=8, halfway is 4.0, so 3.5 is < 4.0 and >= 3 -> hits Building branch
    assert "Building:" in SimulationEngine._recommend_emergency_fund(3.5, 8, False)
    assert "Urgent:" in SimulationEngine._recommend_emergency_fund(1.5, 6, False)

