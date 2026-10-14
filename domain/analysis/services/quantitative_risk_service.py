"""Quantitative Risk, Simulation, and Parity Service.

Provides Historical VaR, Geometric Brownian Motion Monte Carlo simulation, and Risk Parity weighting.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_historical_var(returns, confidence_level=0.95):
    """Calculate Value at Risk (VaR) using the historical simulation method.

    VaR estimates the maximum potential loss with a given confidence level
    over a specified time horizon based on historical return distribution.

    Args:
        returns: pandas Series or numpy array of historical returns (decimal, not percentage)
        confidence_level: Confidence level for VaR (default: 0.95 for 95% VaR)

    Returns:
        float: VaR as a negative percentage (e.g., -0.05 for -5% VaR)
               None if insufficient data
    """
    try:
        # Convert to numpy array if needed
        if hasattr(returns, 'values'):
            returns = returns.values

        returns = np.array(returns)

        # Validate input
        if len(returns) < 10:
            logger.warning("Insufficient data for VaR calculation (need at least 10 data points)")
            return None

        # Remove NaN values
        returns = returns[~np.isnan(returns)]

        if len(returns) < 10:
            logger.warning("Insufficient valid data for VaR calculation after NaN removal")
            return None

        # Calculate VaR using historical simulation method
        # VaR is the quantile of the return distribution at (1 - confidence_level)
        var = np.percentile(returns, (1 - confidence_level) * 100)

        logger.info(f"Historical VaR ({confidence_level*100}%): {var:.4f}")
        return float(var)

    except Exception as e:
        logger.error(f"Historical VaR calculation error: {e}")
        return None


def simulate_monte_carlo_path(current_price, expected_return, volatility, days=252, simulations=100):
    """Generate Monte Carlo simulation for an asset's future price paths based on Geometric Brownian Motion.

    Uses the standard GBM model: dS = μSdt + σSdW
    Where: μ = expected return, σ = volatility, dW = Wiener process

    Args:
        current_price: Current asset price (float)
        expected_return: Expected annual return (decimal, e.g., 0.10 for 10%)
        volatility: Annual volatility (decimal, e.g., 0.20 for 20%)
        days: Number of days to simulate (default: 252 trading days)
        simulations: Number of simulation paths (default: 100)

    Returns:
        dict: {
            'paths': numpy array of shape (simulations, days) with price paths,
            'final_prices': numpy array of final prices for each simulation,
            'mean_final_price': mean of final prices,
            'median_final_price': median of final prices,
            'percentiles': dict with 5th, 25th, 50th, 75th, 95th percentiles
        }
        None if invalid input
    """
    try:
        # Validate input
        if current_price <= 0:
            logger.warning("Current price must be positive")
            return None

        if volatility < 0:
            logger.warning("Volatility cannot be negative")
            return None

        if days <= 0 or simulations <= 0:
            logger.warning("Days and simulations must be positive")
            return None

        # Convert annual parameters to daily
        dt = 1 / 252  # Daily time step (assuming 252 trading days per year)
        daily_return = expected_return * dt
        daily_volatility = volatility * np.sqrt(dt)

        # Initialize price paths array
        paths = np.zeros((simulations, days))
        paths[:, 0] = current_price

        # Generate random shocks (Wiener process)
        random_shocks = np.random.standard_normal((simulations, days - 1))

        # Simulate price paths using GBM
        for t in range(1, days):
            # GBM formula: S(t) = S(t-1) * exp((μ - 0.5σ²)dt + σ√dt * Z)
            paths[:, t] = paths[:, t - 1] * np.exp(
                (daily_return - 0.5 * daily_volatility**2) * dt
                + daily_volatility * random_shocks[:, t - 1]
            )

        # Calculate statistics
        final_prices = paths[:, -1]
        mean_final_price = np.mean(final_prices)
        median_final_price = np.median(final_prices)

        percentiles = {
            'p5': np.percentile(final_prices, 5),
            'p25': np.percentile(final_prices, 25),
            'p50': np.percentile(final_prices, 50),
            'p75': np.percentile(final_prices, 75),
            'p95': np.percentile(final_prices, 95),
        }

        logger.info(f"Monte Carlo simulation completed: {simulations} paths over {days} days")
        logger.info(f"Mean final price: {mean_final_price:.2f}, Median: {median_final_price:.2f}")

        return {
            'paths': paths,
            'final_prices': final_prices,
            'mean_final_price': mean_final_price,
            'median_final_price': median_final_price,
            'percentiles': percentiles,
        }

    except Exception as e:
        logger.error(f"Monte Carlo simulation error: {e}")
        return None


def calculate_risk_parity_weights(covariance_matrix):
    """Calculate inverse-volatility weights as a simplified step towards full Risk Parity / Markowitz optimization.

    Risk Parity aims to allocate capital such that each asset contributes equally to portfolio risk.
    This simplified version uses inverse volatility weighting, which is a common approximation.

    Args:
        covariance_matrix: pandas DataFrame or numpy array of asset returns covariance matrix

    Returns:
        dict: {
            'weights': dict of {asset: weight} for each asset,
            'volatilities': dict of {asset: volatility} for each asset,
            'inverse_volatilities': dict of {asset: inverse_volatility} for each asset
        }
        None if invalid input
    """
    try:
        # Convert to DataFrame if needed
        if not isinstance(covariance_matrix, pd.DataFrame):
            if isinstance(covariance_matrix, np.ndarray):
                covariance_matrix = pd.DataFrame(covariance_matrix)
            else:
                logger.warning("Covariance matrix must be numpy array or pandas DataFrame")
                return None

        # Validate input
        if covariance_matrix.empty:
            logger.warning("Covariance matrix is empty")
            return None

        # Extract volatilities (standard deviations) from diagonal
        volatilities = np.sqrt(np.diag(covariance_matrix))

        # Handle zero or negative volatilities
        volatilities[volatilities <= 0] = 1e-10  # Avoid division by zero

        # Calculate inverse volatilities
        inverse_volatilities = 1.0 / volatilities

        # Normalize to get weights (sum to 1)
        weights = inverse_volatilities / np.sum(inverse_volatilities)

        # Get asset names
        asset_names = covariance_matrix.index.tolist()

        # Create result dictionaries
        weights_dict = {asset_names[i]: float(weights[i]) for i in range(len(asset_names))}
        volatilities_dict = {asset_names[i]: float(volatilities[i]) for i in range(len(asset_names))}
        inverse_volatilities_dict = {asset_names[i]: float(inverse_volatilities[i]) for i in range(len(asset_names))}

        logger.info(f"Risk parity weights calculated for {len(asset_names)} assets")
        logger.info(f"Weights: {weights_dict}")

        return {
            'weights': weights_dict,
            'volatilities': volatilities_dict,
            'inverse_volatilities': inverse_volatilities_dict,
        }

    except Exception as e:
        logger.error(f"Risk parity weights calculation error: {e}")
        return None
