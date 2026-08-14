"""
Enhanced Inflation Analysis Service
===================================
Comprehensive inflation analysis with nominal vs real return calculations
Phase 7: Inflation analysis (nominal vs real return - enhanced)
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class InflationAnalyzer:
    """Comprehensive inflation analysis for real return calculations"""

    # Historical inflation data for multiple countries (can be expanded)
    INFLATION_DATA = {
        'TR': {  # Turkey
            2020: 12.28,
            2021: 19.60,
            2022: 72.31,
            2023: 53.86,
            2024: 47.06,
            2025: 40.00,
        },
        'US': {  # United States
            2020: 1.23,
            2021: 4.70,
            2022: 8.00,
            2023: 4.12,
            2024: 3.24,
            2025: 2.50,
        },
        'EU': {  # Eurozone
            2020: 0.25,
            2021: 2.55,
            2022: 8.40,
            2023: 5.43,
            2024: 2.71,
            2025: 2.00,
        },
    }

    @staticmethod
    def calculate_real_return(nominal_return: float, inflation_rate: float) -> float:
        """
        Calculate real return using Fisher equation

        Formula: Real Return = (1 + Nominal Return) / (1 + Inflation) - 1

        Args:
            nominal_return: Nominal return as percentage (e.g., 15 for 15%)
            inflation_rate: Inflation rate as percentage (e.g., 40 for 40%)

        Returns:
            Real return as percentage
        """
        nominal_decimal = nominal_return / 100
        inflation_decimal = inflation_rate / 100

        real_decimal = ((1 + nominal_decimal) / (1 + inflation_decimal)) - 1
        real_return = real_decimal * 100

        return real_return

    @staticmethod
    def calculate_purchasing_power(initial_amount: float, inflation_rate: float, years: int = 1) -> Dict:
        """
        Calculate purchasing power after inflation

        Formula: Purchasing Power = Initial Amount / (1 + Inflation)^Years

        Args:
            initial_amount: Initial amount
            inflation_rate: Annual inflation rate as percentage
            years: Number of years

        Returns:
            Dict with purchasing power analysis
        """
        inflation_decimal = inflation_rate / 100

        final_amount = initial_amount / ((1 + inflation_decimal) ** years)
        purchasing_power_loss = initial_amount - final_amount
        purchasing_power_loss_pct = (purchasing_power_loss / initial_amount * 100)

        return {
            'initial_amount': initial_amount,
            'final_amount': final_amount,
            'purchasing_power_loss': purchasing_power_loss,
            'purchasing_power_loss_pct': purchasing_power_loss_pct,
            'years': years,
            'inflation_rate': inflation_rate
        }

    @staticmethod
    def get_inflation_adjusted_return(asset_value: float, cost_basis: float, purchase_year: int, current_year: int = None, country: str = 'TR') -> Dict:
        """
        Get inflation-adjusted return for an asset

        Args:
            asset_value: Current asset value
            cost_basis: Original cost basis
            purchase_year: Year of purchase
            current_year: Current year (default: current year)
            country: Country code for inflation data

        Returns:
            Dict with inflation-adjusted return analysis
        """
        if not current_year:
            current_year = datetime.now().year

        # Calculate nominal return
        nominal_return = ((asset_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

        # Get cumulative inflation over holding period
        cumulative_inflation = InflationAnalyzer._get_cumulative_inflation(purchase_year, current_year, country)

        # Calculate real return
        real_return = InflationAnalyzer.calculate_real_return(nominal_return, cumulative_inflation)

        # Calculate inflation-adjusted value
        inflation_adjusted_cost = cost_basis * ((1 + cumulative_inflation / 100) ** (current_year - purchase_year))
        real_gain = asset_value - inflation_adjusted_cost
        real_return_pct = (real_gain / inflation_adjusted_cost * 100) if inflation_adjusted_cost > 0 else 0

        return {
            'nominal_return': nominal_return,
            'cumulative_inflation': cumulative_inflation,
            'real_return': real_return,
            'inflation_adjusted_cost': inflation_adjusted_cost,
            'real_gain': real_gain,
            'real_return_pct': real_return_pct,
            'holding_period': current_year - purchase_year,
            'country': country,
            'interpretation': InflationAnalyzer._interpretate_real_return(real_return, nominal_return)
        }

    @staticmethod
    def _get_cumulative_inflation(start_year: int, end_year: int, country: str = 'TR') -> float:
        """
        Calculate cumulative inflation over a period

        Args:
            start_year: Start year
            end_year: End year
            country: Country code

        Returns:
            Cumulative inflation rate as percentage
        """
        if country not in InflationAnalyzer.INFLATION_DATA:
            logger.warning(f"No inflation data for country {country}, using TR")
            country = 'TR'

        inflation_data = InflationAnalyzer.INFLATION_DATA[country]

        if start_year == end_year:
            return inflation_data.get(start_year, 0)

        # Calculate cumulative inflation
        cumulative = 0.0
        for year in range(start_year, end_year + 1):
            year_inflation = inflation_data.get(year, 0)
            # Compound inflation
            cumulative = ((1 + cumulative / 100) * (1 + year_inflation / 100) - 1) * 100

        return cumulative

    @staticmethod
    def _interpretate_real_return(real_return: float, nominal_return: float) -> str:
        """Generate interpretation of real vs nominal return"""
        if real_return > nominal_return:
            return "Exceptional: Real return exceeds nominal return (deflationary period or exceptional performance)"
        elif real_return > 0:
            return "Positive: Investment outpaced inflation"
        elif real_return > -5:
            return "Near Break-even: Investment roughly kept pace with inflation"
        elif real_return > -15:
            return "Negative: Investment lost value in real terms"
        else:
            return "Significant Loss: Investment significantly underperformed inflation"

    @staticmethod
    def get_portfolio_real_return_analysis(tenant_id: str = None, country: str = 'TR') -> Dict:
        """
        Get portfolio-level real return analysis

        Args:
            tenant_id: Filter by tenant
            country: Country for inflation data

        Returns:
            Dict with portfolio real return analysis
        """

        from models import Asset

        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'total_assets': 0,
                'nominal_return': 0,
                'real_return': 0,
                'asset_analysis': []
            }

        total_value = sum(a.value for a in assets)
        total_cost = sum(a.purchase_cost for a in assets)

        # Calculate weighted average real return
        asset_analysis = []
        weighted_real_return = 0
        current_year = datetime.now().year

        for asset in assets:
            purchase_year = int(asset.purchase_date[:4]) if asset.purchase_date else current_year

            real_analysis = InflationAnalyzer.get_inflation_adjusted_return(
                asset.value,
                asset.purchase_cost,
                purchase_year,
                current_year,
                country
            )

            weight = (asset.value / total_value) if total_value > 0 else 0
            weighted_real_return += real_analysis['real_return'] * weight

            asset_analysis.append({
                'asset_id': asset.id,
                'asset_name': asset.name,
                'weight': weight * 100,
                'real_analysis': real_analysis
            })

        # Portfolio-level nominal return
        portfolio_nominal_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

        # Get average inflation for portfolio
        avg_holding_period = sum(a['real_analysis']['holding_period'] for a in asset_analysis) / len(asset_analysis) if asset_analysis else 1
        base_year = current_year - int(avg_holding_period)
        portfolio_inflation = InflationAnalyzer._get_cumulative_inflation(base_year, current_year, country)

        # Portfolio real return
        portfolio_real_return = InflationAnalyzer.calculate_real_return(portfolio_nominal_return, portfolio_inflation)

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'total_cost': total_cost,
            'nominal_return': portfolio_nominal_return,
            'cumulative_inflation': portfolio_inflation,
            'real_return': portfolio_real_return,
            'weighted_real_return': weighted_real_return,
            'avg_holding_period': avg_holding_period,
            'country': country,
            'asset_analysis': asset_analysis,
            'interpretation': InflationAnalyzer._interpretate_real_return(portfolio_real_return, portfolio_nominal_return)
        }

    @staticmethod
    def compare_with_inflation_benchmarks(nominal_return: float, country: str = 'TR') -> Dict:
        """
        Compare investment return with inflation benchmarks

        Args:
            nominal_return: Investment nominal return
            country: Country code

        Returns:
            Dict with benchmark comparison
        """
        current_year = datetime.now().year
        inflation_rate = InflationAnalyzer.INFLATION_DATA.get(country, {}).get(current_year, 40)

        real_return = InflationAnalyzer.calculate_real_return(nominal_return, inflation_rate)

        # Common benchmarks
        benchmarks = {
            'inflation': inflation_rate,
            'mevduat_avg': 35.0,  # Average deposit rate in Turkey
            'gov_bond_avg': 38.0,  # Average government bond yield
            'bist100_avg': 25.0,  # Average BIST100 return
        }

        comparison = {}
        for benchmark_name, benchmark_rate in benchmarks.items():
            comparison[benchmark_name] = {
                'rate': benchmark_rate,
                'difference': nominal_return - benchmark_rate,
                'outperformed': nominal_return > benchmark_rate
            }

        return {
            'nominal_return': nominal_return,
            'inflation_rate': inflation_rate,
            'real_return': real_return,
            'benchmarks': comparison,
            'summary': f"Your return ({nominal_return}%) {'beat' if nominal_return > inflation_rate else 'did not beat'} inflation ({inflation_rate}%)"
        }
