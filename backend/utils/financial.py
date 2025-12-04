"""
Financial calculation utilities.
"""
import numpy as np

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.04

# Duration scaling for different investment horizons
DURATION_TRADING_DAYS = {
    '6m': 126,   # ~6 months
    '1y': 252,   # 1 year
    '2y': 504,   # 2 years
    '3y': 756,   # 3 years
    '4y': 1008,  # 4 years
    '5y': 1260,  # 5 years
    '10y': 2520  # 10 years
}


def annualize_volatility(daily_std: float) -> float:
    """Convert daily standard deviation to annual volatility."""
    return daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)


def calculate_sharpe_ratio(
    annual_return: float, 
    volatility: float, 
    risk_free_rate: float = RISK_FREE_RATE
) -> float:
    """Calculate Sharpe ratio (risk-adjusted return)."""
    return (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
