"""Unit tests for PortfolioOptimizer (domain/portfolio/services/portfolio_optimization.py).

Tests MPT calculations, Markowitz mean-variance optimization, efficient frontier,
Capital Allocation Line (CAL), constrained optimization, and portfolio rebalancing.
"""

import pytest
from domain.portfolio.services.portfolio_optimization import PortfolioOptimizer


@pytest.fixture
def sample_assets():
    return [
        {
            "name": "BIST 100",
            "expected_return": 25.0,
            "volatility": 20.0,
            "correlations": {
                0: {0: 1.0, 1: 0.2, 2: 0.1},
                1: {0: 0.2, 1: 1.0, 2: 0.3},
                2: {0: 0.1, 1: 0.3, 2: 1.0},
            },
        },
        {
            "name": "Altın",
            "expected_return": 18.0,
            "volatility": 15.0,
        },
        {
            "name": "Eurobond",
            "expected_return": 12.0,
            "volatility": 8.0,
        },
    ]


def test_calculate_efficient_frontier_insufficient_assets():
    res = PortfolioOptimizer.calculate_efficient_frontier([{"name": "Tek Varlık"}])
    assert "error" in res
    assert res["error"] == "Need at least 2 assets for optimization"


def test_calculate_efficient_frontier_success(sample_assets):
    res = PortfolioOptimizer.calculate_efficient_frontier(sample_assets, num_portfolios=50)
    assert "error" not in res
    assert res["num_portfolios"] == 50
    assert len(res["all_portfolios"]) == 50
    assert "max_sharpe" in res["optimal_portfolios"]
    assert "min_volatility" in res["optimal_portfolios"]
    assert len(res["efficient_frontier"]) > 0

    max_sharpe = res["optimal_portfolios"]["max_sharpe"]
    assert "weights" in max_sharpe
    assert len(max_sharpe["weights"]) == 3
    assert abs(sum(max_sharpe["weights"]) - 1.0) < 1e-4
    assert max_sharpe["volatility"] > 0


def test_optimize_portfolio_insufficient_assets():
    res = PortfolioOptimizer.optimize_portfolio([{"name": "Tek Varlık"}])
    assert "error" in res


def test_optimize_portfolio_max_sharpe(sample_assets):
    res = PortfolioOptimizer.optimize_portfolio(sample_assets)
    assert "optimal_portfolio" in res
    assert "asset_allocation" in res
    assert "BIST 100" in res["asset_allocation"]
    assert "Altın" in res["asset_allocation"]
    assert "Eurobond" in res["asset_allocation"]
    alloc_sum = sum(res["asset_allocation"].values())
    assert abs(alloc_sum - 100.0) < 0.1


def test_optimize_portfolio_with_target_return(sample_assets):
    res = PortfolioOptimizer.optimize_portfolio(sample_assets, target_return=16.0)
    assert "optimal_portfolio" in res
    assert res["constraints"]["target_return"] == 16.0
    assert abs(res["metrics"]["expected_return"] - 16.0) < 4.0


def test_optimize_portfolio_with_target_volatility(sample_assets):
    res = PortfolioOptimizer.optimize_portfolio(sample_assets, target_volatility=12.0)
    assert "optimal_portfolio" in res
    assert res["constraints"]["target_volatility"] == 12.0
    assert abs(res["metrics"]["volatility"] - 12.0) < 4.0


def test_calculate_capital_allocation_line():
    optimal_risky = {
        "return": 20.0,
        "volatility": 15.0,
        "sharpe": 1.0,
    }
    res = PortfolioOptimizer.calculate_capital_allocation_line(5.0, optimal_risky)
    assert res["risk_free_rate"] == 5.0
    assert res["cal_slope"] == 1.0
    assert "E(Rp) = 5.0% + 1.00 × σp" in res["cal_equation"]
    assert "Each unit of risk adds 1.00% return" in res["interpretation"]


def test_optimize_with_constraints(sample_assets):
    constraints = {
        "min_weight": 0.1,
        "max_weight": 0.6,
    }
    res = PortfolioOptimizer.optimize_with_constraints(sample_assets, constraints)
    assert "optimal_portfolio" in res
    weights = res["optimal_portfolio"]["weights"]
    for w in weights:
        assert 0.09 <= w <= 0.61
    assert abs(sum(weights) - 1.0) < 1e-4


def test_optimize_with_default_constraints(sample_assets):
    res = PortfolioOptimizer.optimize_with_constraints(sample_assets)
    assert "optimal_portfolio" in res
    assert "asset_allocation" in res


def test_rebalance_portfolio_scenarios():
    current = {"BIST": 60.0, "Altın": 30.0, "Nakit": 10.0}
    target = {"BIST": 40.0, "Altın": 40.0, "Nakit": 20.0}
    portfolio_value = 100000.0

    res = PortfolioOptimizer.rebalance_portfolio(current, target, portfolio_value)
    assert res["portfolio_value"] == 100000.0
    assert len(res["trades"]) > 0

    trade_actions = {t["asset"]: t["action"] for t in res["trades"]}
    # BIST went from 60 to 40 -> SELL
    assert trade_actions["BIST"] == "SELL"
    # Altın went from 30 to 40 -> BUY
    assert trade_actions["Altın"] == "BUY"
    # Nakit went from 10 to 20 -> BUY
    assert trade_actions["Nakit"] == "BUY"


def test_rebalance_recommendations():
    assert PortfolioOptimizer._rebalance_recommendation(300, 10000) == "Minimal rebalancing needed"
    assert PortfolioOptimizer._rebalance_recommendation(1000, 10000) == "Moderate rebalancing recommended"
    assert PortfolioOptimizer._rebalance_recommendation(2000, 10000) == "Significant rebalancing needed"
    assert PortfolioOptimizer._rebalance_recommendation(4000, 10000) == "Major portfolio rebalancing required"
    # Zero value fallback
    assert PortfolioOptimizer._rebalance_recommendation(100, 0) == "Minimal rebalancing needed"


def test_optimize_portfolio_fallback_branches(sample_assets, monkeypatch):
    # Branch 146: frontier returns error
    monkeypatch.setattr(
        PortfolioOptimizer,
        "calculate_efficient_frontier",
        lambda *args, **kwargs: {"error": "Mocked frontier failure"},
    )
    res_err = PortfolioOptimizer.optimize_portfolio(sample_assets)
    assert res_err == {"error": "Mocked frontier failure"}

    # Restore monkeypatch
    monkeypatch.undo()

    # Branch 158: target return far outside range
    res_far_return = PortfolioOptimizer.optimize_portfolio(sample_assets, target_return=999.0)
    assert "optimal_portfolio" in res_far_return

    # Branch 166: target volatility far outside range
    res_far_vol = PortfolioOptimizer.optimize_portfolio(sample_assets, target_volatility=999.0)
    assert "optimal_portfolio" in res_far_vol

