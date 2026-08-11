"""
Goal-Based Investment Planning Service
=====================================
Financial goal planning and tracking
Phase 12: Goal-based investment planning
"""

import logging
from datetime import datetime
from typing import Dict, List

from models import Asset

logger = logging.getLogger(__name__)


class GoalBasedPlanner:
    """Goal-based investment planning and tracking"""

    @staticmethod
    def calculate_goal_progress(
        goal_amount: float,
        current_amount: float,
        target_date: str,
        start_date: str = None
    ) -> Dict:
        """
        Calculate progress toward a financial goal

        Args:
            goal_amount: Target goal amount
            current_amount: Current saved amount
            target_date: Target completion date (YYYY-MM-DD)
            start_date: Goal start date (YYYY-MM-DD)

        Returns:
            Dict with goal progress analysis
        """
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')

        # Calculate percentage complete
        progress_pct = (current_amount / goal_amount * 100) if goal_amount > 0 else 0
        remaining_amount = goal_amount - current_amount

        # Calculate time remaining
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        current_dt = datetime.now()

        total_days = (target_dt - start_dt).days
        elapsed_days = (current_dt - start_dt).days
        remaining_days = (target_dt - current_dt).days

        # Calculate required savings rate
        if remaining_days > 0:
            daily_savings_needed = remaining_amount / remaining_days
            monthly_savings_needed = daily_savings_needed * 30
        else:
            daily_savings_needed = 0
            monthly_savings_needed = 0

        # Calculate if on track
        expected_progress = (elapsed_days / total_days * 100) if total_days > 0 else 100
        on_track = progress_pct >= expected_progress

        return {
            'goal_amount': goal_amount,
            'current_amount': current_amount,
            'progress_pct': progress_pct,
            'remaining_amount': remaining_amount,
            'timeline': {
                'start_date': start_date,
                'target_date': target_date,
                'total_days': total_days,
                'elapsed_days': elapsed_days,
                'remaining_days': remaining_days
            },
            'savings_rate': {
                'daily_needed': daily_savings_needed,
                'monthly_needed': monthly_savings_needed
            },
            'status': {
                'on_track': on_track,
                'expected_progress': expected_progress,
                'progress_diff': progress_pct - expected_progress
            },
            'interpretation': GoalBasedPlanner._interpretate_goal_progress(progress_pct, on_track, remaining_days)
        }

    @staticmethod
    def _interpretate_goal_progress(progress_pct: float, on_track: bool, remaining_days: int) -> str:
        """Generate interpretation of goal progress"""
        if progress_pct >= 100:
            return "Goal achieved!"
        elif progress_pct >= 75:
            return "Near completion: Goal almost achieved"
        elif progress_pct >= 50:
            return "Good progress: Halfway to goal"
        elif progress_pct >= 25:
            return "Building progress: Quarter of goal reached"
        elif on_track:
            return "On track: Progress aligned with timeline"
        elif remaining_days < 365:
            return "Behind schedule: Less than 1 year remaining"
        else:
            return "Early stage: Continue consistent saving"

    @staticmethod
    def calculate_required_savings(
        goal_amount: float,
        current_amount: float,
        years: int,
        expected_return: float = 7.0,
        inflation: float = 3.0
    ) -> Dict:
        """
        Calculate required monthly savings to reach goal

        Args:
            goal_amount: Target goal amount (future value)
            current_amount: Current saved amount
            years: Time horizon in years
            expected_return: Expected annual return
            inflation: Annual inflation rate

        Returns:
            Dict with savings requirements
        """
        # Calculate real return
        real_return = ((1 + expected_return / 100) / (1 + inflation / 100) - 1) * 100

        # Calculate future value of current savings
        future_value_current = current_amount * ((1 + expected_return / 100) ** years)

        # Calculate additional amount needed
        additional_needed = goal_amount - future_value_current

        if additional_needed <= 0:
            return {
                'goal_amount': goal_amount,
                'current_amount': current_amount,
                'years': years,
                'expected_return': expected_return,
                'inflation': inflation,
                'real_return': real_return,
                'future_value_current': future_value_current,
                'additional_needed': 0,
                'monthly_savings': 0,
                'interpretation': 'Current savings will reach goal without additional contributions'
            }

        # Calculate required monthly savings (future value of annuity)
        monthly_rate = expected_return / 12 / 100
        months = years * 12

        # Future value of annuity formula: PMT = FV × r / ((1 + r)^n - 1)
        monthly_savings = additional_needed * monthly_rate / ((1 + monthly_rate) ** months - 1)

        # Adjust for inflation (real monthly savings)
        real_monthly_savings = monthly_savings / ((1 + inflation / 100) ** years)

        return {
            'goal_amount': goal_amount,
            'current_amount': current_amount,
            'years': years,
            'expected_return': expected_return,
            'inflation': inflation,
            'real_return': real_return,
            'future_value_current': future_value_current,
            'additional_needed': additional_needed,
            'monthly_savings': monthly_savings,
            'real_monthly_savings': real_monthly_savings,
            'interpretation': f'Save ₺{monthly_savings:,.0f}/month (₺{real_monthly_savings:,.0f} in today\'s money) to reach goal'
        }

    @staticmethod
    def optimize_goal_achievement(
        goal_amount: float,
        current_amount: float,
        max_monthly_savings: float,
        expected_return: float = 7.0,
        inflation: float = 3.0
    ) -> Dict:
        """
        Optimize goal achievement by finding best combination of time and savings

        Args:
            goal_amount: Target goal amount
            current_amount: Current saved amount
            max_monthly_savings: Maximum affordable monthly savings
            expected_return: Expected annual return
            inflation: Annual inflation rate

        Returns:
            Dict with optimization results
        """
        scenarios = []

        # Test different time horizons (1 to 30 years)
        for years in range(1, 31):
            savings_req = GoalBasedPlanner.calculate_required_savings(
                goal_amount, current_amount, years, expected_return, inflation
            )

            if savings_req['monthly_savings'] <= max_monthly_savings:
                scenarios.append({
                    'years': years,
                    'monthly_savings': savings_req['monthly_savings'],
                    'total_contributions': savings_req['monthly_savings'] * years * 12,
                    'feasible': True
                })

        if scenarios:
            # Find optimal (shortest time with reasonable savings)
            optimal = min(scenarios, key=lambda x: x['years'])

            return {
                'goal_amount': goal_amount,
                'current_amount': current_amount,
                'max_monthly_savings': max_monthly_savings,
                'optimal_scenario': optimal,
                'all_scenarios': scenarios,
                'interpretation': f'Goal achievable in {optimal["years"]} years with ₺{optimal["monthly_savings"]:,.0f}/month'
            }
        else:
            # Not feasible with max savings
            return {
                'goal_amount': goal_amount,
                'current_amount': current_amount,
                'max_monthly_savings': max_monthly_savings,
                'optimal_scenario': None,
                'interpretation': 'Goal not feasible with current savings capacity. Increase savings or extend timeline.'
            }

    @staticmethod
    def create_goal_template(goal_type: str) -> Dict:
        """
        Create a goal template with default parameters

        Args:
            goal_type: Type of goal (retirement, house, education, emergency, etc.)

        Returns:
            Dict with goal template
        """
        templates = {
            'retirement': {
                'name': 'Retirement',
                'default_years': 25,
                'expected_return': 7.0,
                'inflation': 3.0,
                'description': 'Retirement savings goal'
            },
            'house': {
                'name': 'House Purchase',
                'default_years': 10,
                'expected_return': 5.0,
                'inflation': 3.0,
                'description': 'House down payment goal'
            },
            'education': {
                'name': 'Education',
                'default_years': 5,
                'expected_return': 6.0,
                'inflation': 4.0,
                'description': 'Education fund goal'
            },
            'emergency': {
                'name': 'Emergency Fund',
                'default_years': 1,
                'expected_return': 3.0,
                'inflation': 3.0,
                'description': 'Emergency fund (6 months expenses)'
            },
            'vacation': {
                'name': 'Vacation',
                'default_years': 2,
                'expected_return': 4.0,
                'inflation': 3.0,
                'description': 'Vacation fund goal'
            },
            'car': {
                'name': 'Car Purchase',
                'default_years': 5,
                'expected_return': 5.0,
                'inflation': 3.0,
                'description': 'Car purchase goal'
            }
        }

        return templates.get(goal_type, {
            'name': 'Custom Goal',
            'default_years': 5,
            'expected_return': 7.0,
            'inflation': 3.0,
            'description': 'Custom financial goal'
        })

    @staticmethod
    def get_portfolio_goal_alignment(tenant_id: str = None) -> Dict:
        """
        Analyze how well current portfolio aligns with goals

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with goal alignment analysis
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        total_value = sum(a.value for a in assets)

        # Analyze asset types and their suitability for different goals
        goal_suitability = {
            'short_term': {'cash': 0, 'bonds': 0, 'stocks': 0},
            'medium_term': {'cash': 0, 'bonds': 0, 'stocks': 0},
            'long_term': {'cash': 0, 'bonds': 0, 'stocks': 0}
        }

        for asset in assets:
            asset_type = asset.type.lower()
            value = asset.value

            if 'nakit' in asset_type or 'döviz' in asset_type:
                goal_suitability['short_term']['cash'] += value
                goal_suitability['medium_term']['cash'] += value * 0.5
                goal_suitability['long_term']['cash'] += value * 0.2
            elif 'tahvil' in asset_type or 'bono' in asset_type:
                goal_suitability['short_term']['bonds'] += value * 0.8
                goal_suitability['medium_term']['bonds'] += value
                goal_suitability['long_term']['bonds'] += value * 0.6
            else:  # stocks, gold, etc.
                goal_suitability['short_term']['stocks'] += value * 0.2
                goal_suitability['medium_term']['stocks'] += value * 0.6
                goal_suitability['long_term']['stocks'] += value

        # Calculate alignment scores
        alignment_scores = {}
        for horizon, allocation in goal_suitability.items():
            total = sum(allocation.values())
            if total > 0:
                # Ideal allocation depends on horizon
                if horizon == 'short_term':
                    ideal = {'cash': 0.7, 'bonds': 0.3, 'stocks': 0.0}
                elif horizon == 'medium_term':
                    ideal = {'cash': 0.3, 'bonds': 0.5, 'stocks': 0.2}
                else:  # long_term
                    ideal = {'cash': 0.1, 'bonds': 0.3, 'stocks': 0.6}

                # Calculate alignment score
                score = 0
                for asset_class in allocation:
                    actual_pct = allocation[asset_class] / total
                    ideal_pct = ideal.get(asset_class, 0)
                    score += 100 - abs(actual_pct - ideal_pct) * 100

                alignment_scores[horizon] = score / 3

        return {
            'total_portfolio_value': total_value,
            'goal_suitability': goal_suitability,
            'alignment_scores': alignment_scores,
            'recommendations': GoalBasedPlanner._generate_allocation_recommendations(alignment_scores)
        }

    @staticmethod
    def _generate_allocation_recommendations(alignment_scores: Dict[str, float]) -> List[str]:
        """Generate allocation recommendations based on goal alignment"""
        recommendations = []

        if alignment_scores.get('short_term', 0) < 70:
            recommendations.append("Increase cash and short-term bonds for short-term goals")

        if alignment_scores.get('medium_term', 0) < 70:
            recommendations.append("Balance allocation with more bonds for medium-term goals")

        if alignment_scores.get('long_term', 0) < 70:
            recommendations.append("Increase stock allocation for long-term growth goals")

        if not recommendations:
            recommendations.append("Portfolio well-aligned with typical goal horizons")

        return recommendations
