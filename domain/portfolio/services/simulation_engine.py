"""
Simulation Engine Service
==========================
What-if scenario analysis for investment decisions
Phase 11: Simulation engine (what-if scenarios)
"""

import logging
import math
import random
from typing import Dict

logger = logging.getLogger(__name__)


class SimulationEngine:
    """What-if scenario simulation engine"""

    @staticmethod
    def simulate_investment_growth(
        initial_amount: float,
        annual_return: float,
        years: int,
        monthly_contribution: float = 0,
        volatility: float = 15.0,
        simulations: int = 1000
    ) -> Dict:
        """
        Simulate investment growth with Monte Carlo method

        Args:
            initial_amount: Initial investment amount
            annual_return: Expected annual return (as percentage)
            years: Investment horizon in years
            monthly_contribution: Monthly contribution amount
            volatility: Annual volatility (as percentage)
            simulations: Number of Monte Carlo simulations

        Returns:
            Dict with simulation results
        """
        random.seed(42)  # For reproducibility

        final_values = []
        monthly_return = annual_return / 12 / 100
        monthly_volatility = volatility / 12 / 100

        for _ in range(simulations):
            amount = initial_amount

            for month in range(years * 12):
                # Random return based on normal distribution
                random_return = random.gauss(monthly_return, monthly_volatility)
                amount = amount * (1 + random_return) + monthly_contribution

            final_values.append(amount)

        # Calculate statistics
        mean_value = sum(final_values) / len(final_values)
        median_value = sorted(final_values)[len(final_values) // 2]
        min_value = min(final_values)
        max_value = max(final_values)

        # Percentiles
        percentiles = {
            'p10': sorted(final_values)[int(len(final_values) * 0.1)],
            'p25': sorted(final_values)[int(len(final_values) * 0.25)],
            'p75': sorted(final_values)[int(len(final_values) * 0.75)],
            'p90': sorted(final_values)[int(len(final_values) * 0.9)],
        }

        # Calculate without volatility (deterministic)
        deterministic_value = initial_amount
        for month in range(years * 12):
            deterministic_value = deterministic_value * (1 + monthly_return) + monthly_contribution

        return {
            'initial_amount': initial_amount,
            'annual_return': annual_return,
            'years': years,
            'monthly_contribution': monthly_contribution,
            'volatility': volatility,
            'simulations': simulations,
            'results': {
                'mean': mean_value,
                'median': median_value,
                'min': min_value,
                'max': max_value,
                'deterministic': deterministic_value,
                'percentiles': percentiles
            },
            'interpretation': SimulationEngine._interpretate_simulation(mean_value, deterministic_value, volatility)
        }

    @staticmethod
    def _interpretate_simulation(mean_value: float, deterministic_value: float, volatility: float) -> str:
        """Generate interpretation of simulation results"""
        if volatility < 10:
            return "Low volatility scenario: Results are relatively predictable"
        elif volatility < 20:
            return "Moderate volatility: Some variation in outcomes expected"
        elif volatility < 30:
            return "High volatility: Significant variation in outcomes"
        else:
            return "Very high volatility: Outcomes vary widely"

    @staticmethod
    def simulate_asset_allocation_change(
        current_allocation: Dict[str, float],
        new_allocation: Dict[str, float],
        expected_returns: Dict[str, float],
        volatilities: Dict[str, float],
        correlations: Dict[str, Dict[str, float]],
        portfolio_value: float,
        years: int = 5
    ) -> Dict:
        """
        Simulate portfolio performance with different asset allocation

        Args:
            current_allocation: Current allocation {asset_type: percentage}
            new_allocation: Proposed new allocation
            expected_returns: Expected annual returns {asset_type: percentage}
            volatilities: Annual volatilities {asset_type: percentage}
            correlations: Correlation matrix {asset_type: {asset_type: correlation}}
            portfolio_value: Current portfolio value
            years: Simulation horizon

        Returns:
            Dict with allocation comparison
        """
        # Calculate current portfolio expected return and volatility
        current_return = sum(current_allocation[asset] * expected_returns[asset] for asset in current_allocation) / 100
        current_vol = SimulationEngine._calculate_portfolio_volatility(
            current_allocation, volatilities, correlations
        )

        # Calculate new portfolio expected return and volatility
        new_return = sum(new_allocation[asset] * expected_returns[asset] for asset in new_allocation) / 100
        new_vol = SimulationEngine._calculate_portfolio_volatility(
            new_allocation, volatilities, correlations
        )

        # Simulate both portfolios
        current_sim = SimulationEngine.simulate_investment_growth(
            portfolio_value,
            current_return * 100,
            years,
            volatility=current_vol,
            simulations=500
        )

        new_sim = SimulationEngine.simulate_investment_growth(
            portfolio_value,
            new_return * 100,
            years,
            volatility=new_vol,
            simulations=500
        )

        return {
            'current_allocation': current_allocation,
            'new_allocation': new_allocation,
            'current_metrics': {
                'expected_return': current_return * 100,
                'volatility': current_vol,
                'sharpe': (current_return - 0.05) / (current_vol / 100) if current_vol > 0 else 0
            },
            'new_metrics': {
                'expected_return': new_return * 100,
                'volatility': new_vol,
                'sharpe': (new_return - 0.05) / (new_vol / 100) if new_vol > 0 else 0
            },
            'simulation_comparison': {
                'current': current_sim['results'],
                'new': new_sim['results']
            },
            'recommendation': SimulationEngine._compare_allocations(
                current_return, new_return, current_vol, new_vol
            )
        }

    @staticmethod
    def _calculate_portfolio_volatility(allocation: Dict[str, float], volatilities: Dict[str, float], correlations: Dict[str, Dict[str, float]]) -> float:
        """Calculate portfolio volatility using correlation matrix"""
        assets = list(allocation.keys())
        portfolio_variance = 0

        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                weight1 = allocation[asset1] / 100
                weight2 = allocation[asset2] / 100
                vol1 = volatilities[asset1] / 100
                vol2 = volatilities[asset2] / 100
                corr = correlations.get(asset1, {}).get(asset2, 0)

                portfolio_variance += weight1 * weight2 * vol1 * vol2 * corr

        return math.sqrt(portfolio_variance) * 100

    @staticmethod
    def _compare_allocations(current_return: float, new_return: float, current_vol: float, new_vol: float) -> str:
        """Compare two allocations and provide recommendation"""
        return_diff = new_return - current_return
        vol_diff = new_vol - current_vol

        if return_diff > 0 and vol_diff < 0:
            return f"Recommended: Higher return ({return_diff*100:.1f}%) with lower risk ({abs(vol_diff):.1f}%)"
        elif return_diff > 0 and vol_diff > 0:
            return f"Consider: Higher return ({return_diff*100:.1f}%) but higher risk ({vol_diff:.1f}%)"
        elif return_diff < 0 and vol_diff < 0:
            return f"Consider: Lower return ({return_diff*100:.1f}%) but lower risk ({abs(vol_diff):.1f}%)"
        else:
            return f"Not recommended: Lower return ({return_diff*100:.1f}%) with higher risk ({vol_diff:.1f}%)"

    @staticmethod
    def simulate_withdrawal_scenario(
        portfolio_value: float,
        annual_withdrawal: float,
        annual_return: float,
        years: int,
        inflation: float = 3.0,
        simulations: int = 1000
    ) -> Dict:
        """
        Simulate withdrawal scenario (retirement planning)

        Args:
            portfolio_value: Initial portfolio value
            annual_withdrawal: Annual withdrawal amount
            annual_return: Expected annual return
            years: Simulation horizon
            inflation: Annual inflation rate
            simulations: Number of simulations

        Returns:
            Dict with withdrawal simulation results
        """
        random.seed(42)

        success_count = 0
        final_values = []

        for _ in range(simulations):
            value = portfolio_value
            withdrawal = annual_withdrawal

            for year in range(years):
                # Adjust withdrawal for inflation
                withdrawal = withdrawal * (1 + inflation / 100)

                # Random return
                random_return = random.gauss(annual_return / 100, 0.15)
                value = value * (1 + random_return) - withdrawal

                if value <= 0:
                    break

            if value > 0:
                success_count += 1
                final_values.append(value)

        success_rate = (success_count / simulations) * 100

        return {
            'portfolio_value': portfolio_value,
            'annual_withdrawal': annual_withdrawal,
            'withdrawal_rate': (annual_withdrawal / portfolio_value * 100),
            'annual_return': annual_return,
            'years': years,
            'inflation': inflation,
            'simulations': simulations,
            'results': {
                'success_rate': success_rate,
                'success_count': success_count,
                'final_values': final_values
            },
            'interpretation': SimulationEngine._interpretate_withdrawal(success_rate, annual_withdrawal / portfolio_value * 100)
        }

    @staticmethod
    def _interpretate_withdrawal(success_rate: float, withdrawal_rate: float) -> str:
        """Interpret withdrawal simulation results"""
        if success_rate > 90:
            return f"Excellent: {success_rate:.1f}% success rate at {withdrawal_rate:.1f}% withdrawal rate"
        elif success_rate > 70:
            return f"Good: {success_rate:.1f}% success rate at {withdrawal_rate:.1f}% withdrawal rate"
        elif success_rate > 50:
            return f"Moderate: {success_rate:.1f}% success rate at {withdrawal_rate:.1f}% withdrawal rate"
        else:
            return f"Risky: Only {success_rate:.1f}% success rate at {withdrawal_rate:.1f}% withdrawal rate"

    @staticmethod
    def simulate_emergency_fund(
        monthly_expenses: float,
        months_needed: int = 6,
        current_savings: float = 0,
        monthly_savings: float = 0,
        months_to_build: int = 12
    ) -> Dict:
        """
        Simulate emergency fund building

        Args:
            monthly_expenses: Monthly expenses
            months_needed: Months of expenses to cover
            current_savings: Current emergency fund
            monthly_savings: Monthly contribution to emergency fund
            months_to_build: Months to build the fund

        Returns:
            Dict with emergency fund simulation
        """
        target_amount = monthly_expenses * months_needed
        current_coverage = current_savings / monthly_expenses

        # Simulate building the fund
        savings_projection = []
        accumulated = current_savings

        for month in range(months_to_build + 1):
            coverage = accumulated / monthly_expenses
            savings_projection.append({
                'month': month,
                'amount': accumulated,
                'coverage_months': coverage,
                'target_met': accumulated >= target_amount
            })
            accumulated += monthly_savings

        final_coverage = savings_projection[-1]['coverage_months']
        target_met = savings_projection[-1]['target_met']

        # Calculate months to reach target
        months_to_target = None
        for projection in savings_projection:
            if projection['target_met']:
                months_to_target = projection['month']
                break

        return {
            'monthly_expenses': monthly_expenses,
            'months_needed': months_needed,
            'target_amount': target_amount,
            'current_savings': current_savings,
            'current_coverage': current_coverage,
            'monthly_savings': monthly_savings,
            'months_to_build': months_to_build,
            'results': {
                'final_coverage': final_coverage,
                'target_met': target_met,
                'months_to_target': months_to_target,
                'projection': savings_projection
            },
            'recommendation': SimulationEngine._recommend_emergency_fund(current_coverage, months_needed, target_met)
        }

    @staticmethod
    def _recommend_emergency_fund(current_coverage: float, target_months: int, target_met: bool) -> str:
        """Generate emergency fund recommendation"""
        if target_met:
            return f"Emergency fund target met: {current_coverage:.1f} months coverage"
        elif current_coverage >= target_months * 0.5:
            return f"Progress: {current_coverage:.1f} months coverage, halfway to target"
        elif current_coverage >= 3:
            return f"Building: {current_coverage:.1f} months coverage, continue saving"
        else:
            return f"Urgent: Only {current_coverage:.1f} months coverage, prioritize emergency fund"
