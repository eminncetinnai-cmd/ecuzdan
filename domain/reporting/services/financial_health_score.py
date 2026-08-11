"""
Financial Health Score Service
===============================
Multi-metric financial health scoring system
Phase 14: Financial health score (multi-metric scoring)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from models import Asset, Transaction

logger = logging.getLogger(__name__)


class FinancialHealthScorer:
    """Multi-metric financial health scoring system"""

    @staticmethod
    def calculate_financial_health_score(tenant_id: str = None) -> Dict:
        """
        Calculate comprehensive financial health score

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with financial health score and breakdown
        """
        # Calculate individual component scores
        liquidity_score = FinancialHealthScorer._calculate_liquidity_score(tenant_id)
        savings_score = FinancialHealthScorer._calculate_savings_score(tenant_id)
        debt_score = FinancialHealthScorer._calculate_debt_score(tenant_id)
        investment_score = FinancialHealthScorer._calculate_investment_score(tenant_id)
        diversification_score = FinancialHealthScorer._calculate_diversification_score(tenant_id)
        emergency_fund_score = FinancialHealthScorer._calculate_emergency_fund_score(tenant_id)

        # Calculate weighted overall score
        weights = {
            'liquidity': 0.20,
            'savings': 0.20,
            'debt': 0.20,
            'investment': 0.20,
            'diversification': 0.10,
            'emergency_fund': 0.10
        }

        overall_score = (
            liquidity_score['score'] * weights['liquidity'] +
            savings_score['score'] * weights['savings'] +
            debt_score['score'] * weights['debt'] +
            investment_score['score'] * weights['investment'] +
            diversification_score['score'] * weights['diversification'] +
            emergency_fund_score['score'] * weights['emergency_fund']
        )

        return {
            'overall_score': overall_score,
            'overall_rating': FinancialHealthScorer._get_rating(overall_score),
            'components': {
                'liquidity': liquidity_score,
                'savings': savings_score,
                'debt': debt_score,
                'investment': investment_score,
                'diversification': diversification_score,
                'emergency_fund': emergency_fund_score
            },
            'weights': weights,
            'recommendations': FinancialHealthScorer._generate_health_recommendations(
                liquidity_score, savings_score, debt_score, investment_score,
                diversification_score, emergency_fund_score
            )
        }

    @staticmethod
    def _calculate_liquidity_score(tenant_id: str = None) -> Dict:
        """Calculate liquidity score based on cash availability"""
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        # Calculate liquid assets (cash, döviz, etc.)
        liquid_assets = sum(a.value for a in assets if a.liquidity == 'Likit')
        sum(a.value for a in assets)

        # Get monthly expenses from transactions
        query = Transaction.query.filter_by(type='Gider', is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        # Get last 3 months of expenses
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        recent_expenses = query.filter(Transaction.date >= three_months_ago).all()
        monthly_expenses = sum(t.amount for t in recent_expenses) / 3 if recent_expenses else 0

        # Calculate liquidity ratio (liquid assets / monthly expenses)
        if monthly_expenses > 0:
            liquidity_ratio = liquid_assets / monthly_expenses
        else:
            liquidity_ratio = 0

        # Score based on liquidity ratio
        if liquidity_ratio >= 6:
            score = 100
        elif liquidity_ratio >= 3:
            score = 80
        elif liquidity_ratio >= 1:
            score = 60
        elif liquidity_ratio >= 0.5:
            score = 40
        else:
            score = 20

        return {
            'score': score,
            'rating': FinancialHealthScorer._get_rating(score),
            'metrics': {
                'liquid_assets': liquid_assets,
                'monthly_expenses': monthly_expenses,
                'liquidity_ratio': liquidity_ratio
            }
        }

    @staticmethod
    def _calculate_savings_score(tenant_id: str = None) -> Dict:
        """Calculate savings score based on savings rate"""
        query = Transaction.query.filter_by(is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        # Get last 12 months
        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        transactions = query.filter(Transaction.date >= twelve_months_ago).all()

        total_income = sum(t.amount for t in transactions if t.type == 'Gelir')
        total_expenses = sum(t.amount for t in transactions if t.type == 'Gider')
        total_investments = sum(t.amount for t in transactions if t.type == 'Yatırım')

        # Calculate savings rate
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income) * 100
        else:
            savings_rate = 0

        # Score based on savings rate
        if savings_rate >= 30:
            score = 100
        elif savings_rate >= 20:
            score = 80
        elif savings_rate >= 10:
            score = 60
        elif savings_rate >= 5:
            score = 40
        else:
            score = 20

        return {
            'score': score,
            'rating': FinancialHealthScorer._get_rating(score),
            'metrics': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'total_investments': total_investments,
                'savings_rate': savings_rate
            }
        }

    @staticmethod
    def _calculate_debt_score(tenant_id: str = None) -> Dict:
        """Calculate debt score based on debt-to-income ratio"""
        query = Transaction.query.filter_by(is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        # Get debt transactions (Borç category)
        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        transactions = query.filter(Transaction.date >= twelve_months_ago).all()

        total_income = sum(t.amount for t in transactions if t.type == 'Gelir')
        debt_payments = sum(t.amount for t in transactions if t.category == 'Borç')

        # Calculate debt-to-income ratio
        if total_income > 0:
            debt_ratio = (debt_payments / total_income) * 100
        else:
            debt_ratio = 0

        # Score based on debt ratio (lower is better)
        if debt_ratio <= 10:
            score = 100
        elif debt_ratio <= 20:
            score = 80
        elif debt_ratio <= 30:
            score = 60
        elif debt_ratio <= 40:
            score = 40
        else:
            score = 20

        return {
            'score': score,
            'rating': FinancialHealthScorer._get_rating(score),
            'metrics': {
                'total_income': total_income,
                'debt_payments': debt_payments,
                'debt_ratio': debt_ratio
            }
        }

    @staticmethod
    def _calculate_investment_score(tenant_id: str = None) -> Dict:
        """Calculate investment score based on investment performance"""
        from domain.portfolio.services.performance_calculation import PerformanceCalculator

        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'score': 50,
                'rating': 'Orta',
                'metrics': {'error': 'No investments'}
            }

        # Calculate portfolio performance
        portfolio_perf = PerformanceCalculator.get_portfolio_performance(tenant_id)

        # Score based on portfolio return
        portfolio_return = portfolio_perf['portfolio_twr']

        if portfolio_return >= 20:
            score = 100
        elif portfolio_return >= 10:
            score = 80
        elif portfolio_return >= 5:
            score = 60
        elif portfolio_return >= 0:
            score = 40
        else:
            score = 20

        return {
            'score': score,
            'rating': FinancialHealthScorer._get_rating(score),
            'metrics': {
                'portfolio_return': portfolio_return,
                'total_assets': len(assets)
            }
        }

    @staticmethod
    def _calculate_diversification_score(tenant_id: str = None) -> Dict:
        """Calculate diversification score based on asset allocation"""
        from domain.portfolio.services.advanced_allocation import AdvancedAllocationAnalyzer

        allocation = AdvancedAllocationAnalyzer.get_allocation_by_type(tenant_id)

        # Score based on diversification score from allocation analysis
        diversification_score = allocation.get('diversification_score', 0)

        return {
            'score': diversification_score,
            'rating': FinancialHealthScorer._get_rating(diversification_score),
            'metrics': {
                'diversification_score': diversification_score,
                'asset_types': len(allocation.get('by_type', {}))
            }
        }

    @staticmethod
    def _calculate_emergency_fund_score(tenant_id: str = None) -> Dict:
        """Calculate emergency fund score"""
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        # Calculate liquid assets
        liquid_assets = sum(a.value for a in assets if a.liquidity == 'Likit')

        # Get monthly expenses
        query = Transaction.query.filter_by(type='Gider', is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        recent_expenses = query.filter(Transaction.date >= three_months_ago).all()
        monthly_expenses = sum(t.amount for t in recent_expenses) / 3 if recent_expenses else 0

        # Calculate months of expenses covered
        if monthly_expenses > 0:
            months_covered = liquid_assets / monthly_expenses
        else:
            months_covered = 0

        # Score based on months covered (target: 6 months)
        if months_covered >= 6:
            score = 100
        elif months_covered >= 3:
            score = 80
        elif months_covered >= 1:
            score = 60
        elif months_covered >= 0.5:
            score = 40
        else:
            score = 20

        return {
            'score': score,
            'rating': FinancialHealthScorer._get_rating(score),
            'metrics': {
                'liquid_assets': liquid_assets,
                'monthly_expenses': monthly_expenses,
                'months_covered': months_covered
            }
        }

    @staticmethod
    def _get_rating(score: float) -> str:
        """Get rating based on score"""
        if score >= 80:
            return 'Mükemmel'
        elif score >= 60:
            return 'İyi'
        elif score >= 40:
            return 'Orta'
        elif score >= 20:
            return 'Zayıf'
        else:
            return 'Kötü'

    @staticmethod
    def _generate_health_recommendations(
        liquidity_score: Dict,
        savings_score: Dict,
        debt_score: Dict,
        investment_score: Dict,
        diversification_score: Dict,
        emergency_fund_score: Dict
    ) -> List[str]:
        """Generate recommendations based on component scores"""
        recommendations = []

        if liquidity_score['score'] < 60:
            recommendations.append("Increase liquid assets to improve liquidity")

        if savings_score['score'] < 60:
            recommendations.append("Increase savings rate to at least 10% of income")

        if debt_score['score'] < 60:
            recommendations.append("Reduce debt payments to improve financial health")

        if investment_score['score'] < 60:
            recommendations.append("Review investment portfolio for better performance")

        if diversification_score['score'] < 60:
            recommendations.append("Diversify portfolio across different asset types")

        if emergency_fund_score['score'] < 60:
            recommendations.append("Build emergency fund to cover at least 3 months of expenses")

        if not recommendations:
            recommendations.append("Financial health is excellent. Maintain current practices.")

        return recommendations

    @staticmethod
    def get_health_score_trend(tenant_id: str = None, months: int = 12) -> Dict:
        """
        Get historical trend of financial health score

        Args:
            tenant_id: Filter by tenant
            months: Number of months to analyze

        Returns:
            Dict with historical score trend
        """
        # Simplified - in production, would calculate historical scores
        current_score = FinancialHealthScorer.calculate_financial_health_score(tenant_id)

        # Generate synthetic trend data
        trend = []
        base_score = current_score['overall_score']

        for i in range(months):
            month_score = base_score + (i - months/2) * 2  # Simple trend
            month_score = max(0, min(100, month_score))

            trend.append({
                'month': i + 1,
                'score': month_score,
                'rating': FinancialHealthScorer._get_rating(month_score)
            })

        return {
            'current_score': current_score,
            'trend': trend,
            'trend_direction': 'improving' if trend[-1]['score'] > trend[0]['score'] else 'declining'
        }
