"""
Portfolio analysis service for calculating risk and performance metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from services.market_data import MarketDataService
from utils.financial import TRADING_DAYS_PER_YEAR, RISK_FREE_RATE, annualize_volatility, calculate_sharpe_ratio as calc_sharpe


class PortfolioAnalyzer:
    """Analyzes portfolio risk and performance metrics."""
    
    TRADING_DAYS_PER_YEAR = TRADING_DAYS_PER_YEAR
    RISK_FREE_RATE = RISK_FREE_RATE
    
    def __init__(self, holdings: List[Dict], period: str = "1y"):
        """
        Initialize portfolio analyzer.
        
        Args:
            holdings: List of holdings with 'ticker', 'quantity', 'average_cost'
            period: Historical period for analysis ('1y', '2y', '5y', etc.)
        """
        self.holdings = holdings
        self.period = period
        self.tickers = [h['ticker'] for h in holdings]
        self.quantities = {h['ticker']: float(h['quantity']) for h in holdings}
        
    def get_portfolio_value(self) -> Dict:
        """
        Calculate current portfolio value.
        
        Returns:
            Dictionary with total value and individual holding values
        """
        current_prices = MarketDataService.get_multiple_prices(self.tickers)
        
        holding_values = {}
        total_value = 0.0
        
        for ticker in self.tickers:
            price = current_prices.get(ticker, 0)
            quantity = self.quantities[ticker]
            value = price * quantity
            
            holding_values[ticker] = {
                'quantity': quantity,
                'current_price': price,
                'value': value
            }
            total_value += value
        
        return {
            'total_value': total_value,
            'holdings': holding_values,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def calculate_weights_from_holdings(holdings: list) -> Dict[str, float]:
        """
        Calculate portfolio weights from holdings (static utility method).
        
        Reusable by other services (e.g., optimization API).
        
        Args:
            holdings: List of Holding objects with ticker and quantity
            
        Returns:
            Dictionary mapping ticker to weight (0-1)
        """
        try:
            tickers = [h.ticker for h in holdings]
            prices = MarketDataService.get_multiple_prices(tickers)
            
            # Calculate total value
            total_value = sum(
                float(h.quantity) * prices.get(h.ticker, 0)
                for h in holdings
            )
            
            if total_value == 0:
                return {}
            
            # Calculate weights
            return {
                h.ticker: (float(h.quantity) * prices.get(h.ticker, 0)) / total_value
                for h in holdings
            }
        except Exception:
            return {}
    
    def calculate_returns(self) -> pd.DataFrame:
        """
        Calculate historical returns for portfolio holdings.
        
        Returns:
            DataFrame with daily returns for each holding
        """
        returns_data = {}
        
        for ticker in self.tickers:
            try:
                hist = MarketDataService.get_historical_prices(ticker, period=self.period)
                if not hist.empty:
                    # Calculate daily returns
                    returns = hist['Close'].pct_change().dropna()
                    returns_data[ticker] = returns
            except Exception:
                continue
        
        if not returns_data:
            raise ValueError("Unable to fetch historical data for any tickers")
        
        # Combine into single DataFrame
        returns_df = pd.DataFrame(returns_data)
        return returns_df.dropna()
    
    def calculate_portfolio_returns(self, returns_df: pd.DataFrame) -> pd.Series:
        """
        Calculate weighted portfolio returns.
        
        Args:
            returns_df: DataFrame of individual asset returns
            
        Returns:
            Series of portfolio returns
        """
        # Get current portfolio value and weights
        portfolio_value = self.get_portfolio_value()
        total_val = portfolio_value['total_value']
        
        if total_val == 0:
            raise ValueError("Portfolio has zero value")
        
        # Calculate weights
        weights = {}
        for ticker in self.tickers:
            if ticker in returns_df.columns:
                value = portfolio_value['holdings'][ticker]['value']
                weights[ticker] = value / total_val
        
        # Calculate weighted returns
        portfolio_returns = pd.Series(0, index=returns_df.index)
        for ticker, weight in weights.items():
            if ticker in returns_df.columns:
                portfolio_returns += returns_df[ticker] * weight
        
        return portfolio_returns
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        """
        Calculate annualized volatility (standard deviation).
        
        Args:
            returns: Series of returns
            
        Returns:
            Annualized volatility
        """
        daily_vol = returns.std()
        return annualize_volatility(daily_vol)
    
    def calculate_sharpe_ratio(self, returns: pd.Series, volatility: float) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted return).
        
        Args:
            returns: Series of daily returns
            volatility: Annualized volatility
            
        Returns:
            Sharpe ratio
        """
        annual_return = returns.mean() * self.TRADING_DAYS_PER_YEAR
        return calc_sharpe(annual_return, volatility)
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        Calculate maximum drawdown (largest peak-to-trough decline).
        
        Args:
            returns: Series of returns
            
        Returns:
            Maximum drawdown as decimal (e.g., 0.25 = 25% loss)
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        return float(max_dd)
    
    def calculate_var_95(self, returns: pd.Series) -> float:
        """
        Calculate Value at Risk at 95% confidence level.
        
        VaR is NOT annualized - it represents the daily loss threshold.
        Annualizing VaR would introduce compounding assumptions that don't
        apply to percentile-based risk metrics.
        
        Args:
            returns: Series of daily returns
            
        Returns:
            Daily VaR 95% (daily loss not exceeded 95% of the time, as decimal)
        """
        var_95 = returns.quantile(0.05)  # 5th percentile of daily returns
        return float(var_95)
    
    def calculate_correlation_matrix(self, returns_df: pd.DataFrame) -> Dict:
        """
        Calculate correlation matrix between holdings.
        
        Args:
            returns_df: DataFrame of individual asset returns
            
        Returns:
            Correlation matrix as nested dictionary
        """
        corr_matrix = returns_df.corr()
        return corr_matrix.to_dict()
    
    def analyze(self) -> Dict:
        """
        Perform complete portfolio analysis.
        
        Returns:
            Dictionary with all risk metrics
        """
        # Get portfolio value
        portfolio_value = self.get_portfolio_value()
        
        # Check minimum holdings requirement
        if len(self.tickers) < 2:
            raise ValueError("Portfolio must have at least 2 different holdings for analysis")
        
        # Calculate returns
        returns_df = self.calculate_returns()
        portfolio_returns = self.calculate_portfolio_returns(returns_df)
        
        # Calculate metrics
        annual_return = portfolio_returns.mean() * self.TRADING_DAYS_PER_YEAR
        volatility = self.calculate_volatility(portfolio_returns)
        sharpe_ratio = self.calculate_sharpe_ratio(portfolio_returns, volatility)
        max_drawdown = self.calculate_max_drawdown(portfolio_returns)
        var_95 = self.calculate_var_95(portfolio_returns)
        correlation_matrix = self.calculate_correlation_matrix(returns_df)
        
        return {
            'total_value': float(portfolio_value['total_value']),
            'annual_return': float(annual_return),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'var_95': float(var_95),
            'correlation_matrix': correlation_matrix,
            'holdings': portfolio_value['holdings'],
            'period': self.period,
            'calculated_at': datetime.now().isoformat()
        }
