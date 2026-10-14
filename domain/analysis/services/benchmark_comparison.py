"""
Benchmark Comparison Service
=============================
Compare portfolio performance against major indices and assets
Phase 10: Benchmark comparison (BIST100, S&P500, Gold, USD, etc.)
"""

import logging
import math
from datetime import datetime
from typing import Dict, List

from domain.portfolio.services.performance_calculation import PerformanceCalculator

logger = logging.getLogger(__name__)


class BenchmarkComparator:
    """Portfolio benchmark comparison against indices and assets"""

    # Benchmark definitions
    BENCHMARKS = {
        'BIST100': {
            'name': 'BIST 100',
            'type': 'index',
            'country': 'TR',
            'currency': 'TRY',
            'description': 'Turkey\'s main stock index'
        },
        'BIST30': {
            'name': 'BIST 30',
            'type': 'index',
            'country': 'TR',
            'currency': 'TRY',
            'description': 'Turkey\'s blue-chip index'
        },
        'S&P500': {
            'name': 'S&P 500',
            'type': 'index',
            'country': 'US',
            'currency': 'USD',
            'description': 'US large-cap stock index'
        },
        'NASDAQ': {
            'name': 'NASDAQ',
            'type': 'index',
            'country': 'US',
            'currency': 'USD',
            'description': 'US tech stock index'
        },
        'GOLD': {
            'name': 'Gold',
            'type': 'commodity',
            'country': 'Global',
            'currency': 'USD',
            'description': 'Gold price per ounce'
        },
        'SILVER': {
            'name': 'Silver',
            'type': 'commodity',
            'country': 'Global',
            'currency': 'USD',
            'description': 'Silver price per ounce'
        },
        'USD_TRY': {
            'name': 'USD/TRY',
            'type': 'currency',
            'country': 'FX',
            'currency': 'TRY',
            'description': 'US Dollar to Turkish Lira'
        },
        'EUR_TRY': {
            'name': 'EUR/TRY',
            'type': 'currency',
            'country': 'FX',
            'currency': 'TRY',
            'description': 'Euro to Turkish Lira'
        },
        'BTC_USD': {
            'name': 'Bitcoin',
            'type': 'crypto',
            'country': 'Global',
            'currency': 'USD',
            'description': 'Bitcoin price in USD'
        },
        'MEVDUAT': {
            'name': 'Mevduat',
            'type': 'fixed_income',
            'country': 'TR',
            'currency': 'TRY',
            'description': 'Turkish deposit interest rate'
        },
    }

    # Historical benchmark returns (simplified - in production, fetch from API)
    HISTORICAL_RETURNS = {
        'BIST100': {
            2020: 25.0,
            2021: 15.0,
            2022: -15.0,
            2023: 45.0,
            2024: 30.0,
        },
        'BIST30': {
            2020: 20.0,
            2021: 10.0,
            2022: -20.0,
            2023: 40.0,
            2024: 25.0,
        },
        'S&P500': {
            2020: 16.0,
            2021: 27.0,
            2022: -18.0,
            2023: 24.0,
            2024: 15.0,
        },
        'NASDAQ': {
            2020: 43.0,
            2021: 21.0,
            2022: -33.0,
            2023: 43.0,
            2024: 20.0,
        },
        'GOLD': {
            2020: 25.0,
            2021: -3.0,
            2022: -0.3,
            2023: 13.0,
            2024: 15.0,
        },
        'SILVER': {
            2020: 48.0,
            2021: -11.0,
            2022: 3.0,
            2023: -1.0,
            2024: 10.0,
        },
        'USD_TRY': {
            2020: 20.0,
            2021: 50.0,
            2022: 30.0,
            2023: 40.0,
            2024: 35.0,
        },
        'EUR_TRY': {
            2020: 15.0,
            2021: 40.0,
            2022: 25.0,
            2023: 35.0,
            2024: 30.0,
        },
        'BTC_USD': {
            2020: 300.0,
            2021: 60.0,
            2022: -65.0,
            2023: 155.0,
            2024: 50.0,
        },
        'MEVDUAT': {
            2020: 15.0,
            2021: 18.0,
            2022: 25.0,
            2023: 35.0,
            2024: 40.0,
        },
    }

    @staticmethod
    def get_benchmark_return(benchmark_code: str, year: int = None) -> float:
        """
        Get benchmark return for a specific year

        Args:
            benchmark_code: Benchmark code (e.g., 'BIST100')
            year: Year (default: current year)

        Returns:
            Return as percentage
        """
        if not year:
            year = datetime.now().year

        if benchmark_code not in BenchmarkComparator.BENCHMARKS:
            logger.warning(f"Unknown benchmark: {benchmark_code}")
            return 0.0

        if benchmark_code not in BenchmarkComparator.HISTORICAL_RETURNS:
            logger.warning(f"No historical data for benchmark: {benchmark_code}")
            return 0.0

        return BenchmarkComparator.HISTORICAL_RETURNS[benchmark_code].get(year, 0.0)

    @staticmethod
    def compare_portfolio_to_benchmark(tenant_id: str = None, benchmark_code: str = 'BIST100', start_date: str = None, end_date: str = None) -> Dict:
        """
        Compare portfolio performance against a benchmark

        Args:
            tenant_id: Filter by tenant
            benchmark_code: Benchmark to compare against
            start_date: Start date
            end_date: End date

        Returns:
            Dict with comparison results
        """
        from models import Asset

        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'error': 'No assets found',
                'benchmark': BenchmarkComparator.BENCHMARKS.get(benchmark_code, {})
            }

        # Calculate portfolio TWR
        portfolio_perf = PerformanceCalculator.get_portfolio_performance(tenant_id, start_date, end_date)
        portfolio_return = portfolio_perf['portfolio_twr']

        # Get benchmark return
        year = datetime.now().year
        benchmark_return = BenchmarkComparator.get_benchmark_return(benchmark_code, year)

        # Calculate alpha (excess return)
        alpha = portfolio_return - benchmark_return

        # Calculate information ratio (alpha / tracking error)
        # Simplified: assume tracking error = 10% for now
        tracking_error = 10.0
        information_ratio = alpha / tracking_error if tracking_error > 0 else 0

        return {
            'benchmark': BenchmarkComparator.BENCHMARKS.get(benchmark_code, {}),
            'benchmark_return': benchmark_return,
            'portfolio_return': portfolio_return,
            'alpha': alpha,
            'information_ratio': information_ratio,
            'outperformed': alpha > 0,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'year': year
            },
            'interpretation': BenchmarkComparator._interpretate_comparison(alpha, benchmark_code)
        }

    @staticmethod
    def _interpretate_comparison(alpha: float, benchmark_code: str) -> str:
        """Generate interpretation of comparison result"""
        if alpha > 10:
            return f"Exceptional performance: Outperformed {benchmark_code} by {alpha:.1f}%"
        elif alpha > 5:
            return f"Strong performance: Outperformed {benchmark_code} by {alpha:.1f}%"
        elif alpha > 0:
            return f"Positive performance: Outperformed {benchmark_code} by {alpha:.1f}%"
        elif alpha > -5:
            return f"Slight underperformance: Underperformed {benchmark_code} by {abs(alpha):.1f}%"
        elif alpha > -10:
            return f"Moderate underperformance: Underperformed {benchmark_code} by {abs(alpha):.1f}%"
        else:
            return f"Significant underperformance: Underperformed {benchmark_code} by {abs(alpha):.1f}%"

    @staticmethod
    def compare_to_multiple_benchmarks(tenant_id: str = None, benchmark_codes: List[str] = None, start_date: str = None, end_date: str = None) -> Dict:
        """
        Compare portfolio against multiple benchmarks

        Args:
            tenant_id: Filter by tenant
            benchmark_codes: List of benchmark codes (default: all major benchmarks)
            start_date: Start date
            end_date: End date

        Returns:
            Dict with multi-benchmark comparison
        """
        if benchmark_codes is None:
            benchmark_codes = ['BIST100', 'S&P500', 'GOLD', 'USD_TRY', 'MEVDUAT']

        comparisons = []

        for benchmark_code in benchmark_codes:
            comparison = BenchmarkComparator.compare_portfolio_to_benchmark(
                tenant_id, benchmark_code, start_date, end_date
            )
            if 'error' not in comparison:
                comparisons.append(comparison)

        # Calculate summary statistics
        alphas = [c['alpha'] for c in comparisons]
        avg_alpha = sum(alphas) / len(alphas) if alphas else 0
        outperformed_count = sum(1 for c in comparisons if c['outperformed'])

        return {
            'comparisons': comparisons,
            'summary': {
                'avg_alpha': avg_alpha,
                'outperformed_count': outperformed_count,
                'total_benchmarks': len(comparisons),
                'win_rate': outperformed_count / len(comparisons) * 100 if comparisons else 0
            },
            'best_benchmark': max(comparisons, key=lambda x: x['alpha']) if comparisons else None,
            'worst_benchmark': min(comparisons, key=lambda x: x['alpha']) if comparisons else None
        }

    @staticmethod
    def get_benchmark_correlation(benchmark_code1: str, benchmark_code2: str, years: int = 5) -> Dict:
        """
        Calculate correlation between two benchmarks

        Args:
            benchmark_code1: First benchmark
            benchmark_code2: Second benchmark
            years: Number of years to analyze

        Returns:
            Dict with correlation analysis
        """
        current_year = datetime.now().year
        start_year = current_year - years

        returns1 = []
        returns2 = []

        for year in range(start_year, current_year + 1):
            r1 = BenchmarkComparator.get_benchmark_return(benchmark_code1, year)
            r2 = BenchmarkComparator.get_benchmark_return(benchmark_code2, year)
            returns1.append(r1)
            returns2.append(r2)

        # Calculate correlation
        correlation = BenchmarkComparator._calculate_correlation(returns1, returns2)

        return {
            'benchmark1': BenchmarkComparator.BENCHMARKS.get(benchmark_code1, {}),
            'benchmark2': BenchmarkComparator.BENCHMARKS.get(benchmark_code2, {}),
            'correlation': correlation,
            'returns1': returns1,
            'returns2': returns2,
            'interpretation': BenchmarkComparator._interpretate_correlation(correlation)
        }

    @staticmethod
    def _calculate_correlation(returns1: List[float], returns2: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return 0.0

        n = len(returns1)
        mean1 = sum(returns1) / n
        mean2 = sum(returns2) / n

        numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2))

        variance1 = sum((r1 - mean1) ** 2 for r1 in returns1)
        variance2 = sum((r2 - mean2) ** 2 for r2 in returns2)

        denominator = math.sqrt(variance1 * variance2)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def _interpretate_correlation(correlation: float) -> str:
        """Interpret correlation coefficient"""
        if correlation > 0.8:
            return 'Strong positive correlation'
        elif correlation > 0.5:
            return 'Moderate positive correlation'
        elif correlation > 0.2:
            return 'Weak positive correlation'
        elif correlation > -0.2:
            return 'No significant correlation'
        elif correlation > -0.5:
            return 'Weak negative correlation'
        elif correlation > -0.8:
            return 'Moderate negative correlation'
        else:
            return 'Strong negative correlation'

    @staticmethod
    def get_available_benchmarks() -> List[Dict]:
        """Get list of available benchmarks"""
        return [
            {
                'code': code,
                **BenchmarkComparator.BENCHMARKS[code]
            }
            for code in BenchmarkComparator.BENCHMARKS
        ]
