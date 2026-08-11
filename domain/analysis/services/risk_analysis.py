"""
Risk Analysis Service
====================
Professional risk metrics: volatility, Sharpe, Sortino, Max Drawdown, Beta, VaR, etc.
Phase 8: Risk analysis metrics
"""

import logging
import math
from typing import Dict, List

from models import Asset, AssetUpdate

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Professional risk analysis with institutional-grade metrics"""

    @staticmethod
    def calculate_volatility(returns: List[float], annualize: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns)

        Args:
            returns: List of periodic returns (as decimals, e.g., 0.05 for 5%)
            annualize: Annualize the volatility (assumes daily returns)

        Returns:
            Volatility as percentage
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Calculate mean
        mean_return = sum(returns) / len(returns)

        # Calculate variance
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)

        # Standard deviation
        volatility = math.sqrt(variance)

        # Annualize (assuming daily returns, 252 trading days)
        if annualize:
            volatility = volatility * math.sqrt(252)

        return volatility * 100  # Convert to percentage

    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.05) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return)

        Formula: Sharpe = (Portfolio Return - Risk-Free Rate) / Volatility

        Args:
            returns: List of periodic returns (as decimals)
            risk_free_rate: Annual risk-free rate (as decimal, e.g., 0.05 for 5%)

        Returns:
            Sharpe Ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Calculate average return
        avg_return = sum(returns) / len(returns)

        # Annualize return (assuming daily returns)
        annual_return = avg_return * 252

        # Calculate volatility
        volatility = RiskAnalyzer.calculate_volatility(returns, annualize=True) / 100

        if volatility == 0:
            return 0.0

        # Sharpe ratio
        sharpe = (annual_return - risk_free_rate) / volatility

        return sharpe

    @staticmethod
    def calculate_sortino_ratio(returns: List[float], risk_free_rate: float = 0.05) -> float:
        """
        Calculate Sortino Ratio (downside risk-adjusted return)

        Formula: Sortino = (Portfolio Return - Risk-Free Rate) / Downside Deviation

        Args:
            returns: List of periodic returns (as decimals)
            risk_free_rate: Annual risk-free rate (as decimal)

        Returns:
            Sortino Ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Calculate average return
        avg_return = sum(returns) / len(returns)

        # Annualize return
        annual_return = avg_return * 252

        # Calculate downside deviation (only negative returns)
        negative_returns = [r for r in returns if r < 0]

        if not negative_returns:
            return float('inf')  # No downside risk

        downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
        downside_deviation = math.sqrt(downside_variance) * math.sqrt(252)

        if downside_deviation == 0:
            return float('inf')

        # Sortino ratio
        sortino = (annual_return - risk_free_rate) / downside_deviation

        return sortino

    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> Dict:
        """
        Calculate Maximum Drawdown (largest peak-to-trough decline)

        Args:
            prices: List of asset prices or portfolio values

        Returns:
            Dict with drawdown metrics
        """
        if not prices or len(prices) < 2:
            return {'max_drawdown': 0, 'max_drawdown_pct': 0, 'peak': 0, 'trough': 0}

        peak = prices[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        peak_value = peak
        trough_value = peak

        for price in prices[1:]:
            if price > peak:
                peak = price
                peak_value = peak

            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown * 100
                trough_value = price

        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'peak': peak_value,
            'trough': trough_value,
            'recovery_needed': (peak_value - trough_value) / trough_value * 100 if trough_value > 0 else 0
        }

    @staticmethod
    def calculate_beta(asset_returns: List[float], market_returns: List[float]) -> float:
        """
        Calculate Beta (systematic risk relative to market)

        Formula: Beta = Covariance(Asset, Market) / Variance(Market)

        Args:
            asset_returns: List of asset returns
            market_returns: List of market returns (same length)

        Returns:
            Beta value
        """
        if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
            return 1.0  # Default to market beta

        # Calculate means
        asset_mean = sum(asset_returns) / len(asset_returns)
        market_mean = sum(market_returns) / len(market_returns)

        # Calculate covariance
        covariance = sum((a - asset_mean) * (m - market_mean) for a, m in zip(asset_returns, market_returns)) / len(asset_returns)

        # Calculate market variance
        market_variance = sum((m - market_mean) ** 2 for m in market_returns) / len(market_returns)

        if market_variance == 0:
            return 1.0

        beta = covariance / market_variance

        return beta

    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) - maximum expected loss at confidence level

        Args:
            returns: List of returns (as decimals)
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            VaR as percentage (negative value indicates loss)
        """
        if not returns:
            return 0.0

        # Sort returns
        sorted_returns = sorted(returns)

        # Calculate VaR percentile
        percentile = (1 - confidence_level) * len(sorted_returns)
        index = int(percentile)

        if index >= len(sorted_returns):
            var = sorted_returns[-1]
        else:
            var = sorted_returns[index]

        return var * 100  # Convert to percentage

    @staticmethod
    def calculate_cvar(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall) - average loss beyond VaR

        Args:
            returns: List of returns (as decimals)
            confidence_level: Confidence level

        Returns:
            CVaR as percentage
        """
        if not returns:
            return 0.0

        # Calculate VaR
        var = RiskAnalyzer.calculate_var(returns, confidence_level) / 100

        # Get returns worse than VaR
        tail_losses = [r for r in returns if r <= var]

        if not tail_losses:
            return var * 100

        # Average of tail losses
        cvar = sum(tail_losses) / len(tail_losses)

        return cvar * 100

    @staticmethod
    def get_asset_risk_metrics(asset: Asset, period_days: int = 252) -> Dict:
        """
        Get comprehensive risk metrics for an asset

        Args:
            asset: Asset instance
            period_days: Number of days for analysis (default: 1 year)

        Returns:
            Dict with all risk metrics
        """
        # Get historical price updates
        updates = AssetUpdate.query.filter_by(asset_id=asset.id).order_by(AssetUpdate.date.desc()).limit(period_days).all()

        if len(updates) < 10:
            return {
                'asset_id': asset.id,
                'asset_name': asset.name,
                'error': 'Insufficient data for risk analysis',
                'data_points': len(updates)
            }

        # Extract prices and calculate returns
        prices = [float(u.price) for u in reversed(updates)]
        returns = []

        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(daily_return)

        # Calculate risk metrics
        volatility = RiskAnalyzer.calculate_volatility(returns)
        sharpe = RiskAnalyzer.calculate_sharpe_ratio(returns)
        sortino = RiskAnalyzer.calculate_sortino_ratio(returns)
        drawdown = RiskAnalyzer.calculate_max_drawdown(prices)
        var_95 = RiskAnalyzer.calculate_var(returns, 0.95)
        var_99 = RiskAnalyzer.calculate_var(returns, 0.99)
        cvar_95 = RiskAnalyzer.calculate_cvar(returns, 0.95)

        # Risk score (0-100, higher = riskier)
        risk_score = RiskAnalyzer._calculate_risk_score(volatility, drawdown['max_drawdown_pct'])

        return {
            'asset_id': asset.id,
            'asset_name': asset.name,
            'asset_type': asset.type,
            'data_points': len(updates),
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': drawdown,
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'risk_score': risk_score,
            'risk_level': RiskAnalyzer._get_risk_level(risk_score)
        }

    @staticmethod
    def _calculate_risk_score(volatility: float, max_drawdown_pct: float) -> float:
        """Calculate composite risk score (0-100)"""
        # Volatility component (0-50 points)
        vol_score = min(50, volatility / 2)  # 100% volatility = 50 points

        # Drawdown component (0-50 points)
        dd_score = min(50, max_drawdown_pct / 2)  # 100% drawdown = 50 points

        return vol_score + dd_score

    @staticmethod
    def _get_risk_level(score: float) -> str:
        """Get risk level description"""
        if score < 20:
            return 'Çok Düşük'
        elif score < 40:
            return 'Düşük'
        elif score < 60:
            return 'Orta'
        elif score < 80:
            return 'Yüksek'
        else:
            return 'Çok Yüksek'

    @staticmethod
    def get_portfolio_risk_metrics(tenant_id: str = None) -> Dict:
        """
        Get portfolio-level risk metrics

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with portfolio risk analysis
        """
        from models import Asset

        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'total_assets': 0,
                'portfolio_volatility': 0,
                'portfolio_sharpe': 0,
                'portfolio_risk_score': 0,
                'asset_risk': []
            }

        # Get risk metrics for each asset
        asset_risk = []
        total_value = sum(a.value for a in assets)

        weighted_volatility = 0
        weighted_sharpe = 0
        weighted_risk_score = 0

        for asset in assets:
            risk_metrics = RiskAnalyzer.get_asset_risk_metrics(asset)

            if 'error' not in risk_metrics:
                weight = (asset.value / total_value) if total_value > 0 else 0

                weighted_volatility += risk_metrics['volatility'] * weight
                weighted_sharpe += risk_metrics['sharpe_ratio'] * weight
                weighted_risk_score += risk_metrics['risk_score'] * weight

                asset_risk.append({
                    'asset_id': asset.id,
                    'asset_name': asset.name,
                    'weight': weight * 100,
                    'risk_metrics': risk_metrics
                })

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'portfolio_volatility': weighted_volatility,
            'portfolio_sharpe': weighted_sharpe,
            'portfolio_risk_score': weighted_risk_score,
            'portfolio_risk_level': RiskAnalyzer._get_risk_level(weighted_risk_score),
            'asset_risk': asset_risk
        }

    @staticmethod
    def compare_risk_metrics(asset1: Asset, asset2: Asset) -> Dict:
        """
        Compare risk metrics between two assets

        Args:
            asset1: First asset
            asset2: Second asset

        Returns:
            Dict with risk comparison
        """
        risk1 = RiskAnalyzer.get_asset_risk_metrics(asset1)
        risk2 = RiskAnalyzer.get_asset_risk_metrics(asset2)

        if 'error' in risk1 or 'error' in risk2:
            return {
                'error': 'Insufficient data for comparison',
                'asset1': risk1,
                'asset2': risk2
            }

        comparison = {
            'asset1': {
                'name': asset1.name,
                'risk_metrics': risk1
            },
            'asset2': {
                'name': asset2.name,
                'risk_metrics': risk2
            },
            'comparison': {
                'volatility_diff': risk1['volatility'] - risk2['volatility'],
                'sharpe_diff': risk1['sharpe_ratio'] - risk2['sharpe_ratio'],
                'drawdown_diff': risk1['max_drawdown']['max_drawdown_pct'] - risk2['max_drawdown']['max_drawdown_pct'],
                'risk_score_diff': risk1['risk_score'] - risk2['risk_score']
            },
            'winner': {
                'lower_risk': asset1.name if risk1['risk_score'] < risk2['risk_score'] else asset2.name,
                'higher_sharpe': asset1.name if risk1['sharpe_ratio'] > risk2['sharpe_ratio'] else asset2.name
            }
        }

        return comparison
