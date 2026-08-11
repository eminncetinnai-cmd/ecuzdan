"""
AI-Powered Insights and Recommendations Service
=============================================
Proactive financial insights and recommendations using rule-based AI.
Phase 15: AI-powered proactive insights and recommendations
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AIInsightProvider(ABC):
    """Abstract base class for AI insight providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        raise NotImplementedError


class PortfolioHealthInsightProvider(AIInsightProvider):
    """Insight provider for portfolio health analysis."""

    name = 'portfolio_health'

    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        from domain.reporting.services.financial_health_score import FinancialHealthScorer

        health_data = FinancialHealthScorer.calculate_financial_health_score(tenant_id)
        return AIInsightsEngine._generate_portfolio_insights(health_data)


class RiskAssessmentInsightProvider(AIInsightProvider):
    """Insight provider for risk assessment."""

    name = 'risk_assessment'

    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        from domain.analysis.services.risk_analysis import RiskAnalyzer

        risk_data = RiskAnalyzer.get_portfolio_risk_metrics(tenant_id)
        return AIInsightsEngine._generate_risk_insights(risk_data)


class PerformanceInsightProvider(AIInsightProvider):
    """Insight provider for portfolio performance analysis."""

    name = 'performance'

    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        from domain.analysis.services.benchmark_comparison import BenchmarkComparator
        from domain.portfolio.services.performance_calculation import PerformanceCalculator

        portfolio_perf = PerformanceCalculator.get_portfolio_performance(tenant_id)
        benchmark_comp = BenchmarkComparator.compare_to_multiple_benchmarks(tenant_id)

        return AIInsightsEngine._generate_performance_insights({
            'portfolio_performance': portfolio_perf,
            'benchmark_comparison': benchmark_comp
        })


class AllocationInsightProvider(AIInsightProvider):
    """Insight provider for asset allocation analysis."""

    name = 'allocation'

    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        from domain.portfolio.services.advanced_allocation import AdvancedAllocationAnalyzer

        allocation_data = AdvancedAllocationAnalyzer.get_comprehensive_allocation(tenant_id)
        return AIInsightsEngine._generate_allocation_insights(allocation_data)


class CashFlowInsightProvider(AIInsightProvider):
    """Insight provider for cash flow analysis."""

    name = 'cash_flow'

    def generate_insights(self, tenant_id: Optional[str] = None) -> List[Dict]:
        from domain.transactions.services.cash_flow_analysis import CashFlowAnalyzer

        cash_flow_data = CashFlowAnalyzer.get_cash_flow_summary(tenant_id)
        return AIInsightsEngine._generate_cash_flow_insights(cash_flow_data)


def get_default_insight_providers() -> List[AIInsightProvider]:
    """Return the default insight providers in the order they should execute."""
    return [
        PortfolioHealthInsightProvider(),
        RiskAssessmentInsightProvider(),
        PerformanceInsightProvider(),
        AllocationInsightProvider(),
        CashFlowInsightProvider(),
    ]


class AIInsightsEngine:
    """AI insights orchestration engine with provider-based modular architecture."""

    def __init__(self, providers: Optional[List[AIInsightProvider]] = None):
        self.providers = providers if providers is not None else get_default_insight_providers()

    def generate_proactive_insights(self, tenant_id: Optional[str] = None) -> Dict:
        """Generate proactive financial insights using registered providers."""
        insights = []

        for provider in self.providers:
            try:
                provider_insights = provider.generate_insights(tenant_id) or []
                insights.extend(provider_insights)
                logger.debug("%s returned %d insights", provider.name, len(provider_insights))
            except Exception as exc:
                logger.exception("Insight provider %s failed: %s", provider.name, exc)

        prioritized_insights = self._prioritize_insights(insights)

        return {
            'insights': prioritized_insights,
            'summary': self._generate_summary(prioritized_insights),
            'action_items': self._extract_action_items(prioritized_insights),
            'generated_at': datetime.now().isoformat()
        }

    def get_personalized_recommendations(self, tenant_id: Optional[str] = None) -> Dict:
        """Get personalized recommendations based on generated insights."""
        insights_payload = self.generate_proactive_insights(tenant_id)
        insights = insights_payload['insights']

        categories = {}
        for insight in insights:
            category = insight.get('category', 'general')
            categories.setdefault(category, []).append(insight)

        action_plan = []
        for category, cat_insights in categories.items():
            high_priority = [i for i in cat_insights if i.get('priority') == 'high']
            if high_priority:
                action_plan.append({
                    'category': category,
                    'priority': 'high',
                    'actions': [i.get('recommendation') for i in high_priority]
                })

        return {
            'categories': categories,
            'action_plan': action_plan,
            'total_actions': len(insights_payload['action_items'])
        }

    def register_provider(self, provider: AIInsightProvider) -> None:
        """Register an additional insight provider at runtime."""
        if not isinstance(provider, AIInsightProvider):
            raise TypeError('provider must be an AIInsightProvider')
        self.providers.append(provider)

    @staticmethod
    def _prioritize_insights(insights: List[Dict]) -> List[Dict]:
        """Sort insights by defined priority order."""
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(insights, key=lambda item: priority_order.get(item.get('priority'), 1))

    @staticmethod
    def _generate_summary(insights: List[Dict]) -> str:
        """Generate a concise summary from insight priorities."""
        high_priority = len([i for i in insights if i.get('priority') == 'high'])
        medium_priority = len([i for i in insights if i.get('priority') == 'medium'])
        if high_priority > 0:
            return f'Attention needed: {high_priority} high-priority, {medium_priority} medium-priority issues identified.'
        if medium_priority > 0:
            return f'Good standing with {medium_priority} optimization opportunities.'
        return 'Excellent financial health with minor optimization opportunities.'

    @staticmethod
    def _extract_action_items(insights: List[Dict]) -> List[str]:
        """Extract recommendation text for action items."""
        return [insight.get('recommendation') for insight in insights if insight.get('recommendation')]

    @staticmethod
    def _generate_portfolio_insights(health_data: Dict) -> List[Dict]:
        insights = []
        overall_score = health_data.get('overall_score', 0)

        if overall_score < 50:
            insights.append({
                'type': 'warning',
                'category': 'portfolio_health',
                'title': 'Financial Health Needs Attention',
                'description': f'Your financial health score is {overall_score:.1f}, which is below the recommended level of 60.',
                'priority': 'high',
                'recommendation': 'Focus on improving savings rate and reducing debt to increase financial health.'
            })
        elif overall_score < 70:
            insights.append({
                'type': 'info',
                'category': 'portfolio_health',
                'title': 'Financial Health is Good',
                'description': f'Your financial health score is {overall_score:.1f}, indicating good financial standing.',
                'priority': 'medium',
                'recommendation': 'Continue current practices while looking for optimization opportunities.'
            })
        else:
            insights.append({
                'type': 'success',
                'category': 'portfolio_health',
                'title': 'Excellent Financial Health',
                'description': f'Your financial health score is {overall_score:.1f}, indicating excellent financial standing.',
                'priority': 'low',
                'recommendation': 'Maintain current practices and consider advanced optimization strategies.'
            })

        components = health_data.get('components', {})
        if components.get('savings', {}).get('score', 0) < 60:
            insights.append({
                'type': 'warning',
                'category': 'savings',
                'title': 'Low Savings Rate',
                'description': 'Your savings rate is below the recommended 10% of income.',
                'priority': 'high',
                'recommendation': 'Increase automatic savings contributions to reach at least 10% of income.'
            })

        if components.get('debt', {}).get('score', 0) < 60:
            insights.append({
                'type': 'warning',
                'category': 'debt',
                'title': 'High Debt Burden',
                'description': 'Your debt-to-income ratio is above the recommended 30% threshold.',
                'priority': 'high',
                'recommendation': 'Prioritize debt repayment, starting with high-interest debt.'
            })

        if components.get('emergency_fund', {}).get('score', 0) < 60:
            insights.append({
                'type': 'warning',
                'category': 'emergency_fund',
                'title': 'Insufficient Emergency Fund',
                'description': 'Your emergency fund covers less than 3 months of expenses.',
                'priority': 'high',
                'recommendation': 'Build emergency fund to cover at least 3-6 months of expenses.'
            })

        return insights

    @staticmethod
    def _generate_risk_insights(risk_data: Dict) -> List[Dict]:
        insights = []
        portfolio_vol = risk_data.get('portfolio_volatility', 0)
        portfolio_sharpe = risk_data.get('portfolio_sharpe', 0)
        risk_score = risk_data.get('portfolio_risk_score', 0)

        if portfolio_vol > 25:
            insights.append({
                'type': 'warning',
                'category': 'risk',
                'title': 'High Portfolio Volatility',
                'description': f'Your portfolio volatility is {portfolio_vol:.1f}%, which is considered high.',
                'priority': 'medium',
                'recommendation': 'Consider adding lower-volatility assets like bonds or cash to reduce portfolio risk.'
            })

        if portfolio_sharpe < 0.5:
            insights.append({
                'type': 'warning',
                'category': 'risk',
                'title': 'Low Risk-Adjusted Return',
                'description': f'Your Sharpe ratio is {portfolio_sharpe:.2f}, indicating suboptimal risk-adjusted returns.',
                'priority': 'medium',
                'recommendation': 'Review portfolio allocation to improve risk-adjusted returns.'
            })

        if risk_score > 70:
            insights.append({
                'type': 'warning',
                'category': 'risk',
                'title': 'High Portfolio Risk Score',
                'description': f'Your portfolio risk score is {risk_score:.1f}, indicating high risk exposure.',
                'priority': 'medium',
                'recommendation': 'Consider diversifying across different asset classes to reduce risk.'
            })

        return insights

    @staticmethod
    def _generate_performance_insights(perf_data: Dict) -> List[Dict]:
        insights = []
        portfolio_perf = perf_data.get('portfolio_performance', {})
        benchmark_comp = perf_data.get('benchmark_comparison', {})
        portfolio_return = portfolio_perf.get('portfolio_twr', 0)

        if portfolio_return < 0:
            insights.append({
                'type': 'warning',
                'category': 'performance',
                'title': 'Negative Portfolio Return',
                'description': f'Your portfolio has a negative return of {portfolio_return:.1f}%.',
                'priority': 'high',
                'recommendation': 'Review underperforming assets and consider rebalancing or strategy adjustment.'
            })
        elif portfolio_return < 5:
            insights.append({
                'type': 'info',
                'category': 'performance',
                'title': 'Low Portfolio Return',
                'description': f'Your portfolio return is {portfolio_return:.1f}%, which is below market averages.',
                'priority': 'medium',
                'recommendation': 'Consider increasing exposure to growth assets while managing risk.'
            })

        summary = benchmark_comp.get('summary', {})
        win_rate = summary.get('win_rate', 0)

        if win_rate < 40:
            insights.append({
                'type': 'warning',
                'category': 'performance',
                'title': 'Underperforming Benchmarks',
                'description': f'Your portfolio is underperforming {100-win_rate:.0f}% of benchmark indices.',
                'priority': 'medium',
                'recommendation': 'Review asset allocation and consider aligning with better-performing benchmarks.'
            })
        elif win_rate > 60:
            insights.append({
                'type': 'success',
                'category': 'performance',
                'title': 'Outperforming Benchmarks',
                'description': f'Your portfolio is outperforming {win_rate:.0f}% of benchmark indices.',
                'priority': 'low',
                'recommendation': 'Continue current strategy while monitoring for sustainability.'
            })

        return insights

    @staticmethod
    def _generate_allocation_insights(allocation_data: Dict) -> List[Dict]:
        insights = []
        sector_alloc = allocation_data.get('sector', {})
        currency_alloc = allocation_data.get('currency', {})
        overall_score = allocation_data.get('overall_score', 0)
        max_sector = sector_alloc.get('max_sector_exposure', 0)
        if max_sector > 40:
            insights.append({
                'type': 'warning',
                'category': 'allocation',
                'title': 'High Sector Concentration',
                'description': f'Your portfolio has {max_sector:.1f}% exposure to a single sector.',
                'priority': 'medium',
                'recommendation': 'Diversify across different sectors to reduce concentration risk.'
            })

        max_currency = currency_alloc.get('max_currency_exposure', 0)
        if max_currency > 70:
            insights.append({
                'type': 'warning',
                'category': 'allocation',
                'title': 'High Currency Concentration',
                'description': f'Your portfolio has {max_currency:.1f}% exposure to a single currency.',
                'priority': 'medium',
                'recommendation': 'Consider adding foreign currency assets to reduce currency risk.'
            })

        if overall_score < 50:
            insights.append({
                'type': 'warning',
                'category': 'allocation',
                'title': 'Poor Portfolio Diversification',
                'description': f'Your allocation score is {overall_score:.1f}, indicating poor diversification.',
                'priority': 'medium',
                'recommendation': 'Increase diversification across different asset types, sectors, and currencies.'
            })

        return insights

    @staticmethod
    def _generate_cash_flow_insights(cash_flow_data: Dict) -> List[Dict]:
        insights = []
        net_cash_flow = cash_flow_data.get('cash_flow', {}).get('net_cash_flow', 0)

        if net_cash_flow < 0:
            insights.append({
                'type': 'warning',
                'category': 'cash_flow',
                'title': 'Negative Cash Flow',
                'description': f'Your net cash flow is negative ({net_cash_flow:.0f}).',
                'priority': 'high',
                'recommendation': 'Review expenses and identify areas to reduce spending or increase income.'
            })
        elif 0 <= net_cash_flow < 1000:
            insights.append({
                'type': 'info',
                'category': 'cash_flow',
                'title': 'Low Positive Cash Flow',
                'description': f'Your net cash flow is positive but low ({net_cash_flow:.0f}).',
                'priority': 'medium',
                'recommendation': 'Consider increasing savings rate to build financial buffer.'
            })
        else:
            insights.append({
                'type': 'success',
                'category': 'cash_flow',
                'title': 'Healthy Cash Flow',
                'description': f'Your net cash flow is positive ({net_cash_flow:.0f}).',
                'priority': 'low',
                'recommendation': 'Continue current cash flow management and consider investment opportunities.'
            })

        return insights


# Exposed default engine for simple integration.
ai_insights_engine = AIInsightsEngine()
