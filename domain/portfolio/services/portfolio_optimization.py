"""
Portfolio Optimization Service
===============================
Modern Portfolio Theory (MPT) and Markowitz mean-variance optimization
Phase 13: Portfolio optimization algorithms (MPT, Markowitz, etc.)
"""

import logging
import math
import random
from typing import Dict, List

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Portfolio optimization using MPT and Markowitz mean-variance optimization"""

    @staticmethod
    def calculate_efficient_frontier(
        assets: List[Dict],
        num_portfolios: int = 100
    ) -> Dict:
        """
        Calculate efficient frontier using Monte Carlo simulation

        Args:
            assets: List of assets with expected_return and volatility
            num_portfolios: Number of portfolios to simulate

        Returns:
            Dict with efficient frontier data
        """
        if len(assets) < 2:
            return {'error': 'Need at least 2 assets for optimization'}

        # Extract asset data
        returns = [a['expected_return'] for a in assets]
        volatilities = [a['volatility'] for a in assets]
        correlations = assets[0].get('correlations', {})

        portfolios = []

        for _ in range(num_portfolios):
            # Generate random weights
            weights = PortfolioOptimizer._generate_random_weights(len(assets))

            # Calculate portfolio metrics
            portfolio_return = sum(w * r for w, r in zip(weights, returns))
            portfolio_vol = PortfolioOptimizer._calculate_portfolio_volatility(
                weights, volatilities, correlations
            )

            # Calculate Sharpe ratio (assuming 5% risk-free rate)
            sharpe = (portfolio_return - 5) / portfolio_vol if portfolio_vol > 0 else 0

            portfolios.append({
                'weights': weights,
                'return': portfolio_return,
                'volatility': portfolio_vol,
                'sharpe': sharpe
            })

        # Find efficient frontier (max return for each volatility level)
        portfolios.sort(key=lambda x: x['volatility'])
        efficient_frontier = []

        for portfolio in portfolios:
            # Check if this portfolio has max return for its volatility
            same_vol = [p for p in portfolios if abs(p['volatility'] - portfolio['volatility']) < 0.5]
            max_return = max(p['return'] for p in same_vol)

            if portfolio['return'] >= max_return - 0.1:
                efficient_frontier.append(portfolio)

        # Find optimal portfolios
        max_sharpe = max(portfolios, key=lambda x: x['sharpe'])
        min_vol = min(portfolios, key=lambda x: x['volatility'])

        return {
            'assets': assets,
            'num_portfolios': num_portfolios,
            'efficient_frontier': efficient_frontier,
            'optimal_portfolios': {
                'max_sharpe': max_sharpe,
                'min_volatility': min_vol
            },
            'all_portfolios': portfolios
        }

    @staticmethod
    def _generate_random_weights(n: int) -> List[float]:
        """Generate random weights that sum to 1"""
        weights = [random.random() for _ in range(n)]
        total = sum(weights)
        return [w / total for w in weights]

    @staticmethod
    def _calculate_portfolio_volatility(
        weights: List[float],
        volatilities: List[float],
        correlations: Dict
    ) -> float:
        """Calculate portfolio volatility using correlation matrix"""
        n = len(weights)
        portfolio_variance = 0

        for i in range(n):
            for j in range(n):
                w1 = weights[i]
                w2 = weights[j]
                v1 = volatilities[i] / 100
                v2 = volatilities[j] / 100
                corr = correlations.get(i, {}).get(j, 0.5)  # Default 0.5 correlation

                portfolio_variance += w1 * w2 * v1 * v2 * corr

        return math.sqrt(portfolio_variance) * 100

    @staticmethod
    def optimize_portfolio(
        assets: List[Dict],
        target_return: float = None,
        target_volatility: float = None,
        risk_free_rate: float = 5.0
    ) -> Dict:
        """
        Optimize portfolio for given constraints

        Args:
            assets: List of assets with expected_return and volatility
            target_return: Target return (optional)
            target_volatility: Target volatility (optional)
            risk_free_rate: Risk-free rate for Sharpe calculation

        Returns:
            Dict with optimal portfolio
        """
        if len(assets) < 2:
            return {'error': 'Need at least 2 assets for optimization'}

        # Calculate efficient frontier
        frontier = PortfolioOptimizer.calculate_efficient_frontier(assets, num_portfolios=500)

        if 'error' in frontier:
            return frontier

        portfolios = frontier['all_portfolios']

        # Select optimal portfolio based on constraints
        if target_return:
            # Find portfolio closest to target return with minimum volatility
            target_portfolios = [p for p in portfolios if abs(p['return'] - target_return) < 2]
            if target_portfolios:
                optimal = min(target_portfolios, key=lambda x: x['volatility'])
            else:
                # Find closest return
                optimal = min(portfolios, key=lambda x: abs(x['return'] - target_return))
        elif target_volatility:
            # Find portfolio closest to target volatility with maximum return
            target_portfolios = [p for p in portfolios if abs(p['volatility'] - target_volatility) < 2]
            if target_portfolios:
                optimal = max(target_portfolios, key=lambda x: x['return'])
            else:
                # Find closest volatility
                optimal = min(portfolios, key=lambda x: abs(x['volatility'] - target_volatility))
        else:
            # Maximize Sharpe ratio
            optimal = frontier['optimal_portfolios']['max_sharpe']

        # Calculate portfolio metrics
        weights = optimal['weights']
        asset_allocation = {
            assets[i]['name']: weights[i] * 100
            for i in range(len(assets))
        }

        return {
            'optimal_portfolio': optimal,
            'asset_allocation': asset_allocation,
            'metrics': {
                'expected_return': optimal['return'],
                'volatility': optimal['volatility'],
                'sharpe_ratio': optimal['sharpe']
            },
            'constraints': {
                'target_return': target_return,
                'target_volatility': target_volatility
            }
        }

    @staticmethod
    def calculate_capital_allocation_line(
        risk_free_rate: float,
        optimal_risky_portfolio: Dict
    ) -> Dict:
        """
        Calculate Capital Allocation Line (CAL)

        Args:
            risk_free_rate: Risk-free rate
            optimal_risky_portfolio: Optimal risky portfolio from MPT

        Returns:
            Dict with CAL data
        """
        optimal_risky_portfolio['return']
        optimal_risky_portfolio['volatility']
        risky_sharpe = optimal_risky_portfolio['sharpe']

        # CAL equation: E(Rp) = Rf + (E(Rm) - Rf) / σm × σp
        # Slope = Sharpe ratio of risky portfolio

        cal_slope = risky_sharpe

        return {
            'risk_free_rate': risk_free_rate,
            'risky_portfolio': optimal_risky_portfolio,
            'cal_slope': cal_slope,
            'cal_equation': f'E(Rp) = {risk_free_rate}% + {cal_slope:.2f} × σp',
            'interpretation': f'Each unit of risk adds {cal_slope:.2f}% return'
        }

    @staticmethod
    def optimize_with_constraints(
        assets: List[Dict],
        constraints: Dict = None
    ) -> Dict:
        """
        Optimize portfolio with custom constraints

        Args:
            assets: List of assets with expected_return and volatility
            constraints: Dict with constraints (min_weight, max_weight, sector limits, etc.)

        Returns:
            Dict with constrained optimal portfolio
        """
        if constraints is None:
            constraints = {
                'min_weight': 0,
                'max_weight': 1,
                'sector_limits': {}
            }

        # Generate portfolios with constraints
        num_portfolios = 1000
        portfolios = []

        returns = [a['expected_return'] for a in assets]
        volatilities = [a['volatility'] for a in assets]
        correlations = assets[0].get('correlations', {})

        for _ in range(num_portfolios):
            # Generate constrained weights
            weights = PortfolioOptimizer._generate_constrained_weights(
                len(assets),
                constraints.get('min_weight', 0),
                constraints.get('max_weight', 1)
            )

            # Calculate portfolio metrics
            portfolio_return = sum(w * r for w, r in zip(weights, returns))
            portfolio_vol = PortfolioOptimizer._calculate_portfolio_volatility(
                weights, volatilities, correlations
            )

            sharpe = (portfolio_return - 5) / portfolio_vol if portfolio_vol > 0 else 0

            portfolios.append({
                'weights': weights,
                'return': portfolio_return,
                'volatility': portfolio_vol,
                'sharpe': sharpe
            })

        # Find optimal (max Sharpe)
        optimal = max(portfolios, key=lambda x: x['sharpe'])

        asset_allocation = {
            assets[i]['name']: optimal['weights'][i] * 100
            for i in range(len(assets))
        }

        return {
            'optimal_portfolio': optimal,
            'asset_allocation': asset_allocation,
            'constraints': constraints,
            'metrics': {
                'expected_return': optimal['return'],
                'volatility': optimal['volatility'],
                'sharpe_ratio': optimal['sharpe']
            }
        }

    @staticmethod
    def _generate_constrained_weights(n: int, min_weight: float, max_weight: float) -> List[float]:
        """Generate random weights with constraints"""
        while True:
            weights = [random.uniform(min_weight, max_weight) for _ in range(n)]
            total = sum(weights)
            normalized = [w / total for w in weights]

            # Check constraints
            if all(min_weight <= w <= max_weight for w in normalized):
                return normalized

    @staticmethod
    def rebalance_portfolio(
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float],
        portfolio_value: float
    ) -> Dict:
        """
        Calculate rebalancing trades

        Args:
            current_allocation: Current allocation {asset: percentage}
            target_allocation: Target allocation {asset: percentage}
            portfolio_value: Total portfolio value

        Returns:
            Dict with rebalancing instructions
        """
        trades = []

        for asset in target_allocation:
            current_pct = current_allocation.get(asset, 0)
            target_pct = target_allocation[asset]

            diff_pct = target_pct - current_pct
            diff_value = portfolio_value * diff_pct / 100

            if abs(diff_value) > 100:  # Only trade if difference > 100
                action = 'BUY' if diff_value > 0 else 'SELL'
                trades.append({
                    'asset': asset,
                    'action': action,
                    'amount': abs(diff_value),
                    'percentage': abs(diff_pct)
                })

        total_trade_value = sum(t['amount'] for t in trades)

        return {
            'current_allocation': current_allocation,
            'target_allocation': target_allocation,
            'portfolio_value': portfolio_value,
            'trades': trades,
            'total_trade_value': total_trade_value,
            'trade_percentage': (total_trade_value / portfolio_value * 100) if portfolio_value > 0 else 0,
            'recommendation': PortfolioOptimizer._rebalance_recommendation(total_trade_value, portfolio_value)
        }

    @staticmethod
    def _rebalance_recommendation(total_trade_value: float, portfolio_value: float) -> str:
        """Generate rebalancing recommendation"""
        trade_pct = (total_trade_value / portfolio_value * 100) if portfolio_value > 0 else 0

        if trade_pct < 5:
            return "Minimal rebalancing needed"
        elif trade_pct < 15:
            return "Moderate rebalancing recommended"
        elif trade_pct < 30:
            return "Significant rebalancing needed"
        else:
            return "Major portfolio rebalancing required"
