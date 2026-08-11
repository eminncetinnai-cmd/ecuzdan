"""
Advanced Performance Calculation Service
========================================
Time-Weighted Return (TWR) and Money-Weighted Return (IRR) calculations
Phase 3: Professional performance metrics instead of simple difference
"""

import logging
from datetime import datetime
from typing import Dict, List

from models import Asset, AssetTransaction

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """Professional portfolio performance calculation using TWR and IRR"""

    @staticmethod
    def calculate_time_weighted_return(asset: Asset, start_date: str = None, end_date: str = None) -> Dict:
        """
        Calculate Time-Weighted Return (TWR)

        TWR eliminates the effect of cash flows and measures the portfolio's
        intrinsic performance. It's the industry standard for comparing
        portfolio managers.

        Formula: TWR = (1 + R1) × (1 + R2) × ... × (1 + Rn) - 1
        Where R is the return for each sub-period between cash flows

        Args:
            asset: Asset instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with TWR metrics
        """
        if not start_date:
            # Use purchase date if not specified
            start_date = asset.purchase_date
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Get all transactions (buys and sells) within the period
        transactions = AssetTransaction.query.filter_by(asset_id=asset.id).filter(
            AssetTransaction.transaction_date >= start_date,
            AssetTransaction.transaction_date <= end_date
        ).order_by(AssetTransaction.transaction_date).all()

        if not transactions:
            # No transactions, use simple return
            start_value = asset.purchase_cost
            end_value = asset.value
            twr = (end_value - start_value) / start_value if start_value > 0 else 0
            return {
                'twr': twr * 100,  # Percentage
                'periods': 1,
                'method': 'simple_return',
                'start_date': start_date,
                'end_date': end_date,
                'start_value': start_value,
                'end_value': end_value
            }

        # Calculate sub-period returns
        sub_period_returns = []

        # Initial value
        current_value = asset.purchase_cost

        for tx in transactions:
            # Calculate return for this sub-period
            if tx.transaction_type == 'buy':
                # Cash inflow - end of sub-period
                # Get value just before this transaction
                # For simplicity, assume value at transaction date

                if current_value > 0:
                    period_return = 0  # No change if just before cash flow
                else:
                    period_return = 0

                sub_period_returns.append(period_return)

                # Add cash flow
                current_value += tx.total_cost

            elif tx.transaction_type == 'sell':
                # Cash outflow - end of sub-period

                if current_value > 0:
                    period_return = (tx.unit_price - (current_value / asset.quantity if asset.quantity > 0 else tx.unit_price)) / tx.unit_price
                else:
                    period_return = 0

                sub_period_returns.append(period_return)

                # Subtract cash flow
                current_value -= tx.total_cost


        # Final period return
        if current_value > 0:
            final_return = (asset.value - current_value) / current_value
        else:
            final_return = 0
        sub_period_returns.append(final_return)

        # Calculate TWR
        twr = 1.0
        for r in sub_period_returns:
            twr *= (1 + r)
        twr -= 1

        return {
            'twr': twr * 100,  # Percentage
            'periods': len(sub_period_returns),
            'method': 'time_weighted_return',
            'start_date': start_date,
            'end_date': end_date,
            'sub_period_returns': sub_period_returns,
            'transaction_count': len(transactions)
        }

    @staticmethod
    def calculate_money_weighted_return(asset: Asset, start_date: str = None, end_date: str = None) -> Dict:
        """
        Calculate Money-Weighted Return (IRR)

        IRR takes into account the timing and amount of cash flows.
        It represents the investor's actual return considering when
        they added/withdrawed money.

        Formula: Solve for r in: NPV = Σ(CFt / (1 + r)^t) = 0
        Where CFt are cash flows at time t

        Args:
            asset: Asset instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with IRR metrics
        """
        if not start_date:
            start_date = asset.purchase_date
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Get all transactions
        transactions = AssetTransaction.query.filter_by(asset_id=asset.id).filter(
            AssetTransaction.transaction_date >= start_date,
            AssetTransaction.transaction_date <= end_date
        ).order_by(AssetTransaction.transaction_date).all()

        # Build cash flow timeline
        cash_flows = []

        # Initial investment (negative cash flow)
        initial_investment = -asset.purchase_cost
        cash_flows.append({
            'date': start_date,
            'amount': initial_investment,
            'days_from_start': 0
        })

        # Additional buys (negative cash flows)
        for tx in transactions:
            if tx.transaction_type == 'buy':
                days_from_start = PerformanceCalculator._days_between(start_date, tx.transaction_date)
                cash_flows.append({
                    'date': tx.transaction_date,
                    'amount': -tx.total_cost,
                    'days_from_start': days_from_start
                })

        # Sells (positive cash flows)
        for tx in transactions:
            if tx.transaction_type == 'sell':
                days_from_start = PerformanceCalculator._days_between(start_date, tx.transaction_date)
                cash_flows.append({
                    'date': tx.transaction_date,
                    'amount': tx.total_cost,
                    'days_from_start': days_from_start
                })

        # Final value (positive cash flow at end)
        final_days = PerformanceCalculator._days_between(start_date, end_date)
        cash_flows.append({
            'date': end_date,
            'amount': asset.value,
            'days_from_start': final_days
        })

        # Calculate IRR using numerical method (Newton-Raphson)
        irr = PerformanceCalculator._calculate_irr(cash_flows)

        # Annualize IRR
        total_days = final_days if final_days > 0 else 365
        annualized_irr = ((1 + irr) ** (365 / total_days) - 1) if irr > -1 else irr

        return {
            'irr': irr * 100,  # Percentage
            'annualized_irr': annualized_irr * 100,
            'method': 'money_weighted_return',
            'start_date': start_date,
            'end_date': end_date,
            'cash_flows': cash_flows,
            'total_days': total_days
        }

    @staticmethod
    def _days_between(date1: str, date2: str) -> int:
        """Calculate days between two dates"""
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        return (d2 - d1).days

    @staticmethod
    def _calculate_irr(cash_flows: List[Dict], guess: float = 0.1, max_iter: int = 100, tolerance: float = 1e-6) -> float:
        """
        Calculate IRR using Newton-Raphson method

        Args:
            cash_flows: List of cash flow dicts with 'amount' and 'days_from_start'
            guess: Initial guess for IRR
            max_iter: Maximum iterations
            tolerance: Convergence tolerance

        Returns:
            IRR as decimal (e.g., 0.15 for 15%)
        """
        def npv(rate):
            """Calculate Net Present Value at given rate"""
            total = 0.0
            for cf in cash_flows:
                days = cf['days_from_start']
                if days == 0:
                    total += cf['amount']
                else:
                    # Convert annual rate to daily rate
                    daily_rate = (1 + rate) ** (days / 365) - 1
                    total += cf['amount'] / (1 + daily_rate)
            return total

        def npv_derivative(rate):
            """Calculate derivative of NPV"""
            total = 0.0
            for cf in cash_flows:
                days = cf['days_from_start']
                if days > 0:
                    (1 + rate) ** (days / 365) - 1
                    # Derivative of 1/(1+r)^t
                    total += -cf['amount'] * days / 365 * (1 + rate) ** ((days / 365) - 1)
            return total

        # Newton-Raphson iteration
        rate = guess
        for i in range(max_iter):
            npv_value = npv(rate)
            if abs(npv_value) < tolerance:
                return rate

            derivative = npv_derivative(rate)
            if abs(derivative) < tolerance:
                break

            rate = rate - npv_value / derivative

            # Prevent divergence
            if rate < -0.99:
                rate = -0.99
            elif rate > 10:
                rate = 10

        return rate

    @staticmethod
    def compare_performance_methods(asset: Asset, start_date: str = None, end_date: str = None) -> Dict:
        """
        Compare TWR, IRR, and simple return methods

        This demonstrates why professional methods matter
        """
        # Simple return (current method)
        simple_return = ((asset.value - asset.purchase_cost) / asset.purchase_cost * 100) if asset.purchase_cost > 0 else 0

        # TWR
        twr_result = PerformanceCalculator.calculate_time_weighted_return(asset, start_date, end_date)

        # IRR
        irr_result = PerformanceCalculator.calculate_money_weighted_return(asset, start_date, end_date)

        return {
            'simple_return': simple_return,
            'time_weighted_return': twr_result['twr'],
            'money_weighted_return': irr_result['irr'],
            'annualized_irr': irr_result['annualized_irr'],
            'method_comparison': {
                'simple': 'Basic calculation, ignores cash flow timing',
                'twr': 'Eliminates cash flow effects, best for manager comparison',
                'irr': 'Includes cash flow timing, best for investor experience'
            },
            'recommendation': PerformanceCalculator._get_recommendation(simple_return, twr_result['twr'], irr_result['irr'])
        }

    @staticmethod
    def _get_recommendation(simple: float, twr: float, irr: float) -> str:
        """Get recommendation on which method to use"""
        if abs(twr - irr) < 1:  # Less than 1% difference
            return "All methods show similar results. Portfolio has minimal cash flows."
        elif irr > twr:
            return "IRR > TWR: You added money before good periods. Good timing!"
        elif twr > irr:
            return "TWR > IRR: Portfolio performed well, but you added money at suboptimal times."
        else:
            return "Use TWR for manager comparison, IRR for personal return evaluation."

    @staticmethod
    def get_portfolio_performance(tenant_id: str = None, start_date: str = None, end_date: str = None) -> Dict:
        """
        Calculate portfolio-level performance using TWR and IRR

        Args:
            tenant_id: Filter by tenant
            start_date: Start date
            end_date: End date

        Returns:
            Portfolio performance metrics
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'total_assets': 0,
                'portfolio_twr': 0,
                'portfolio_irr': 0,
                'asset_performance': []
            }

        # Calculate performance for each asset
        asset_performance = []
        total_value = sum(a.value for a in assets)

        for asset in assets:
            twr_result = PerformanceCalculator.calculate_time_weighted_return(asset, start_date, end_date)
            irr_result = PerformanceCalculator.calculate_money_weighted_return(asset, start_date, end_date)

            weight = (asset.value / total_value * 100) if total_value > 0 else 0

            asset_performance.append({
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_type': asset.type,
                'value': asset.value,
                'weight': weight,
                'twr': twr_result['twr'],
                'irr': irr_result['irr'],
                'annualized_irr': irr_result['annualized_irr']
            })

        # Calculate portfolio-level TWR (weighted average)
        portfolio_twr = sum(ap['twr'] * ap['weight'] / 100 for ap in asset_performance) if asset_performance else 0

        # Calculate portfolio-level IRR (aggregate cash flows)
        # This is complex - simplified version uses weighted average
        portfolio_irr = sum(ap['irr'] * ap['weight'] / 100 for ap in asset_performance) if asset_performance else 0

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'portfolio_twr': portfolio_twr,
            'portfolio_irr': portfolio_irr,
            'asset_performance': asset_performance,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
