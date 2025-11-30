"""
Portfolio optimization service using scipy.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from scipy.optimize import minimize
from services.portfolio_analyzer import PortfolioAnalyzer
from utils.financial import TRADING_DAYS_PER_YEAR, RISK_FREE_RATE, calculate_sharpe_ratio as calc_sharpe


class PortfolioOptimizer:
    """Optimizes portfolio allocations using Modern Portfolio Theory."""
    
    TRADING_DAYS_PER_YEAR = TRADING_DAYS_PER_YEAR
    RISK_FREE_RATE = RISK_FREE_RATE
    
    def __init__(self, tickers: List[str], period: str = "1y"):
        """
        Initialize portfolio optimizer.
        
        Args:
            tickers: List of ticker symbols
            period: Historical period for analysis ('1y', '2y', '5y', etc.)
        """
        self.tickers = tickers
        self.period = period
        self.analyzer = None  # Will be created lazily
        self.returns_df = None
        self.mean_returns = None
        self.cov_matrix = None
    
    def _get_analyzer(self) -> PortfolioAnalyzer:
        """Get or create analyzer instance (lazy initialization)."""
        if self.analyzer is None:
            # Create dummy holdings (only tickers matter for returns)
            dummy_holdings = [
                {'ticker': ticker, 'quantity': 1, 'average_cost': 0}
                for ticker in self.tickers
            ]
            self.analyzer = PortfolioAnalyzer(dummy_holdings, period=self.period)
        return self.analyzer
    
    def fetch_historical_data(self) -> pd.DataFrame:
        """
        Fetch historical price data and calculate returns.
        
        Reuses PortfolioAnalyzer.calculate_returns() to avoid code duplication.
        
        Returns:
            DataFrame with daily returns for each ticker
        """
        analyzer = self._get_analyzer()
        self.returns_df = analyzer.calculate_returns()
        return self.returns_df
    
    def calculate_statistics(self):
        """
        Calculate mean returns and covariance matrix.
        
        Reuses data fetched by PortfolioAnalyzer.
        """
        if self.returns_df is None:
            self.fetch_historical_data()
        
        # Annualized mean returns
        self.mean_returns = self.returns_df.mean() * self.TRADING_DAYS_PER_YEAR
        
        # Annualized covariance matrix
        self.cov_matrix = self.returns_df.cov() * self.TRADING_DAYS_PER_YEAR
    
    def portfolio_performance(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate portfolio performance metrics for given weights.
        
        This is different from PortfolioAnalyzer metrics because it calculates
        expected future performance based on historical statistics, not actual
        historical performance.
        
        Args:
            weights: Array of portfolio weights
            
        Returns:
            Tuple of (annual_return, volatility, sharpe_ratio)
        """
        # Portfolio expected return (already annualized from mean_returns)
        portfolio_return = np.dot(weights, self.mean_returns)
        
        # Portfolio variance and volatility (already annualized from cov_matrix)
        portfolio_variance = np.dot(weights.T, np.dot(self.cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Sharpe ratio using shared utility function
        sharpe_ratio = calc_sharpe(portfolio_return, portfolio_volatility)
        
        return float(portfolio_return), float(portfolio_volatility), float(sharpe_ratio)
    
    def _negative_sharpe(self, weights: np.ndarray) -> float:
        """Objective function for max Sharpe optimization (negative for minimization)."""
        _, volatility, sharpe = self.portfolio_performance(weights)
        return -sharpe
    
    def _portfolio_volatility(self, weights: np.ndarray) -> float:
        """Objective function for min volatility optimization."""
        _, volatility, _ = self.portfolio_performance(weights)
        return volatility
    
    def optimize(
        self,
        strategy: str,
        constraints: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict:
        """
        Optimize portfolio allocation.
        
        Args:
            strategy: 'max_sharpe', 'min_volatility', or 'equal_weight'
            constraints: Optional per-ticker weight constraints
                Example: {'AAPL': {'min': 0.2, 'max': 0.4}}
                
        Returns:
            Dictionary with optimized weights and metrics
        """
        # Handle single ticker case
        if len(self.tickers) == 1:
            return self._single_ticker_optimization()
        
        # Calculate statistics for optimization
        if self.mean_returns is None:
            self.calculate_statistics()
        
        # Equal weight strategy (no optimization needed)
        if strategy == 'equal_weight':
            return self._equal_weight_optimization()
        
        # Setup optimization
        n_assets = len(self.tickers)
        initial_guess = np.array([1.0 / n_assets] * n_assets)
        
        # Build bounds (min/max for each weight)
        bounds = self._build_bounds(constraints)
        
        # Constraint: weights sum to 1
        weight_constraint = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        
        # Select objective function
        if strategy == 'max_sharpe':
            objective = self._negative_sharpe
        elif strategy == 'min_volatility':
            objective = self._portfolio_volatility
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Run optimization
        try:
            result = minimize(
                fun=objective,
                x0=initial_guess,
                method='SLSQP',
                bounds=bounds,
                constraints=weight_constraint,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if not result.success:
                raise ValueError(f"Optimization failed: {result.message}")
            
            optimal_weights = result.x
            
        except Exception as e:
            # Fallback to equal weight if optimization fails
            return self._equal_weight_optimization(error=str(e))
        
        # Format results
        return self._format_results(optimal_weights, strategy, constrained=bool(constraints))
    
    def _build_bounds(self, constraints: Optional[Dict]) -> List[Tuple[float, float]]:
        """
        Build bounds for scipy optimizer.
        
        Args:
            constraints: Per-ticker min/max constraints
            
        Returns:
            List of (min, max) tuples for each ticker
        """
        bounds = []
        
        for ticker in self.tickers:
            if constraints and ticker in constraints:
                min_weight = constraints[ticker].get('min', 0.0)
                max_weight = constraints[ticker].get('max', 1.0)
                
                # Validate constraints
                min_weight = max(0.0, min(min_weight, 1.0))
                max_weight = max(min_weight, min(max_weight, 1.0))
                
                bounds.append((min_weight, max_weight))
            else:
                bounds.append((0.0, 1.0))  # Default: 0-100%
        
        return bounds
    
    def _equal_weight_optimization(self, error: Optional[str] = None) -> Dict:
        """Equal weight allocation strategy."""
        n = len(self.tickers)
        weights = np.array([1.0 / n] * n)
        
        return self._format_results(weights, 'equal_weight', error=error)
    
    def _single_ticker_optimization(self) -> Dict:
        """Handle single ticker case."""
        weights = np.array([1.0])
        
        # Recalculate statistics if needed
        if self.mean_returns is None:
            self.calculate_statistics()
        
        return self._format_results(weights, 'single_ticker')
    
    def _format_results(
        self,
        weights: np.ndarray,
        strategy: str,
        constrained: bool = False,
        error: Optional[str] = None
    ) -> Dict:
        """
        Format optimization results.
        
        Args:
            weights: Optimal weight array
            strategy: Strategy used
            constrained: Whether constraints were applied
            error: Error message if optimization failed
            
        Returns:
            Dictionary with formatted results
        """
        # Create weights dictionary
        weights_dict = {
            ticker: float(weight)
            for ticker, weight in zip(self.tickers, weights)
        }
        
        # Calculate performance metrics
        annual_return, volatility, sharpe_ratio = self.portfolio_performance(weights)
        
        result = {
            'strategy': strategy,
            'weights': weights_dict,
            'expected_return': annual_return,
            'expected_volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'period': self.period,
            'constrained': constrained,
            'optimized_at': datetime.now().isoformat()
        }
        
        if error:
            result['warning'] = f"Optimization failed, using fallback: {error}"
        
        return result
