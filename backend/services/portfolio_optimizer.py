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
    
    def __init__(self, tickers: List[str], period: str = "1y", whole_shares: bool = False, target_duration: str = "1y", max_drawdown: Optional[float] = None):
        """
        Initialize portfolio optimizer.
        
        Args:
            tickers: List of ticker symbols
            period: Historical period for analysis ('1y', '2y', '5y', etc.)
            whole_shares: Whether to round allocations to whole shares (for retirement accounts)
            target_duration: Investment horizon ('6m', '1y', '2y', '3y', '4y', '5y', '10y') - affects risk/return scaling
            max_drawdown: Maximum allowed drawdown constraint (0.10 = 10% max loss)
        """
        self.tickers = tickers
        self.period = period
        self.whole_shares = whole_shares
        self.target_duration = target_duration
        self.max_drawdown = max_drawdown
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
        Calculate mean returns and covariance matrix scaled to target duration.
        
        For shorter durations (6m), we scale returns and volatility appropriately:
        - Returns scale linearly with time
        - Volatility scales with sqrt(time)
        """
        if self.returns_df is None:
            self.fetch_historical_data()
        
        # Get trading days for target duration
        from utils.financial import DURATION_TRADING_DAYS
        target_days = DURATION_TRADING_DAYS.get(self.target_duration, self.TRADING_DAYS_PER_YEAR)
        
        # Scale mean returns to target duration
        self.mean_returns = self.returns_df.mean() * target_days
        
        # Scale covariance matrix to target duration
        self.cov_matrix = self.returns_df.cov() * target_days
    
    def portfolio_performance(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate portfolio performance metrics for given weights.
        
        This is different from PortfolioAnalyzer metrics because it calculates
        expected future performance based on historical statistics, not actual
        historical performance. Metrics are scaled to target_duration.
        
        Args:
            weights: Array of portfolio weights
            
        Returns:
            Tuple of (period_return, volatility, sharpe_ratio) scaled to target duration
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
    
    def _risk_contribution(self, weights: np.ndarray) -> np.ndarray:
        """
        Calculate marginal risk contribution for each asset.
        
        Reuses cached covariance matrix from calculate_statistics().
        
        Args:
            weights: Portfolio weights
            
        Returns:
            Array of risk contributions (sums to portfolio volatility)
        """
        portfolio_variance = np.dot(weights.T, np.dot(self.cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Marginal contribution to risk (MCR)
        mcr = np.dot(self.cov_matrix, weights) / portfolio_volatility if portfolio_volatility > 0 else np.zeros(len(weights))
        
        # Risk contribution = weight * MCR
        risk_contrib = weights * mcr
        
        return risk_contrib
    
    def _risk_parity_objective(self, weights: np.ndarray) -> float:
        """
        Objective function for equal risk contribution strategy.
        
        Minimizes variance of risk contributions (forces equal risk).
        """
        risk_contrib = self._risk_contribution(weights)
        target_risk = np.mean(risk_contrib)
        return np.sum((risk_contrib - target_risk) ** 2)
    
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
        
        # Equal risk strategy
        if strategy == 'equal_risk':
            return self._equal_risk_optimization(constraints)
        
        # Setup optimization
        n_assets = len(self.tickers)
        initial_guess = np.array([1.0 / n_assets] * n_assets)
        
        # Build bounds (min/max for each weight)
        bounds = self._build_bounds(constraints)
        
        # Constraints list
        optimization_constraints = []
        
        # Constraint: weights sum to 1
        optimization_constraints.append({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        
        # Constraint: maximum drawdown (if specified)
        if self.max_drawdown is not None:
            optimization_constraints.append({
                'type': 'ineq',
                'fun': lambda w: self.max_drawdown - self._calculate_historical_drawdown(w)
            })
        
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
                constraints=optimization_constraints,
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
    
    def _equal_risk_optimization(self, constraints: Optional[Dict] = None) -> Dict:
        """
        Equal risk contribution (risk parity) strategy.
        
        Each asset contributes equally to portfolio risk.
        """
        n_assets = len(self.tickers)
        initial_guess = np.array([1.0 / n_assets] * n_assets)
        
        # Build bounds
        bounds = self._build_bounds(constraints)
        
        # Constraints list
        optimization_constraints = []
        optimization_constraints.append({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        
        if self.max_drawdown is not None:
            optimization_constraints.append({
                'type': 'ineq',
                'fun': lambda w: self.max_drawdown - self._calculate_historical_drawdown(w)
            })
        
        try:
            result = minimize(
                fun=self._risk_parity_objective,
                x0=initial_guess,
                method='SLSQP',
                bounds=bounds,
                constraints=optimization_constraints,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if not result.success:
                raise ValueError(f"Risk parity optimization failed: {result.message}")
            
            optimal_weights = result.x
            
        except Exception as e:
            # Fallback to equal weight
            return self._equal_weight_optimization(error=str(e))
        
        return self._format_results(optimal_weights, 'equal_risk', constrained=bool(constraints))
    
    def _single_ticker_optimization(self) -> Dict:
        """Handle single ticker case."""
        weights = np.array([1.0])
        
        # Recalculate statistics if needed
        if self.mean_returns is None:
            self.calculate_statistics()
        
        return self._format_results(weights, 'single_ticker')
    
    def _convert_to_whole_shares(
        self,
        weights: np.ndarray,
        total_value: float,
        current_prices: Dict[str, float]
    ) -> np.ndarray:
        """
        Convert fractional weights to whole-share allocations.
        
        Used for retirement accounts (Roth IRA, Traditional IRA, 401k) where
        fractional shares typically aren't allowed.
        
        Args:
            weights: Fractional weight array
            total_value: Total portfolio value
            current_prices: Current price for each ticker
            
        Returns:
            Adjusted weights based on whole shares
        """
        # Calculate dollar allocation per ticker
        dollar_amounts = weights * total_value
        
        # Calculate whole shares per ticker
        whole_shares_array = np.floor(dollar_amounts / np.array([current_prices[t] for t in self.tickers]))
        
        # Calculate actual dollar value with whole shares
        actual_values = whole_shares_array * np.array([current_prices[t] for t in self.tickers])
        
        # Recalculate weights (may not sum to exactly 1 due to cash remainder)
        new_weights = actual_values / actual_values.sum() if actual_values.sum() > 0 else weights
        
        return new_weights
    
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
        
        # Calculate performance metrics (reuses cached statistics)
        annual_return, volatility, sharpe_ratio = self.portfolio_performance(weights)
        
        result = {
            'strategy': strategy,
            'weights': weights_dict,
            'expected_return': annual_return,
            'expected_volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'period': self.period,
            'target_duration': self.target_duration,
            'constrained': constrained,
            'whole_shares': self.whole_shares,
            'optimized_at': datetime.now().isoformat()
        }
        
        
        if error:
            result['warning'] = f"Optimization failed, using fallback: {error}"
        
        return result
    
    def monte_carlo_simulation(
        self,
        weights: np.ndarray,
        n_simulations: int = 10000,
        confidence_level: int = 95
    ) -> Dict:
        """
        Run Monte Carlo simulation for portfolio outcomes using Cholesky decomposition.
        
        This method preserves the correlation structure between assets, providing
        more realistic simulations than independent random draws.
        
        Reuses cached mean_returns and cov_matrix to avoid re-calculation.
        
        Args:
            weights: Portfolio weights
            n_simulations: Number of simulations to run
            confidence_level: Confidence level (80, 90, or 95)
            
        Returns:
            Dictionary with simulation results including skewness and kurtosis
        """
        # Ensure statistics are calculated
        if self.mean_returns is None:
            self.calculate_statistics()
        
        # Cholesky decomposition of covariance matrix
        # This preserves correlation structure between assets
        try:
            L = np.linalg.cholesky(self.cov_matrix)
        except np.linalg.LinAlgError:
            # If covariance matrix is not positive definite, fall back to simple method
            portfolio_return, portfolio_volatility, _ = self.portfolio_performance(weights)
            simulated_returns = np.random.normal(
                loc=portfolio_return,
                scale=portfolio_volatility,
                size=n_simulations
            )
            method = 'simple'
        else:
            # Generate correlated random returns for each asset
            simulated_portfolio_returns = np.zeros(n_simulations)
            
            for i in range(n_simulations):
                # Independent standard normal draws
                z = np.random.normal(0, 1, len(self.tickers))
                
                # Transform to correlated returns using Cholesky decomposition
                # This maintains the correlation structure from the covariance matrix
                asset_returns = self.mean_returns + L @ z
                
                # Calculate portfolio return for this simulation
                simulated_portfolio_returns[i] = np.dot(weights, asset_returns)
            
            simulated_returns = simulated_portfolio_returns
            method = 'cholesky'
        
        # Calculate percentiles for confidence interval
        lower_percentile = (100 - confidence_level) / 2
        upper_percentile = 100 - lower_percentile
        
        confidence_interval = (
            float(np.percentile(simulated_returns, lower_percentile)),
            float(np.percentile(simulated_returns, upper_percentile))
        )
        
        median_return = float(np.median(simulated_returns))
        mean_return = float(np.mean(simulated_returns))
        probability_of_loss = float(np.sum(simulated_returns < 0) / n_simulations)
        
        # Calculate additional risk metrics
        std_dev = float(np.std(simulated_returns))
        skewness = float(np.mean(((simulated_returns - mean_return) / std_dev) ** 3))
        kurtosis = float(np.mean(((simulated_returns - mean_return) / std_dev) ** 4))
        
        return {
            'n_simulations': n_simulations,
            'confidence_level': confidence_level,
            'confidence_interval': {
                'lower': confidence_interval[0],
                'upper': confidence_interval[1]
            },
            'median_return': median_return,
            'expected_return': mean_return,
            'std_deviation': std_dev,
            'probability_of_loss': probability_of_loss,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'target_duration': self.target_duration,
            'method': method
        }
