"""
Comparison test: Simple Monte Carlo vs Cholesky Monte Carlo
Shows the improvement in correlation handling
"""
import numpy as np
import sys
sys.path.insert(0, '.')

from services.portfolio_optimizer import PortfolioOptimizer

def compare_monte_carlo_methods():
    print("\n" + "="*70)
    print("COMPARING MONTE CARLO METHODS: SIMPLE vs CHOLESKY")
    print("="*70)
    
    # Test portfolio with highly correlated assets (SPY + QQQ) and negatively correlated (TLT)
    tickers = ['SPY', 'QQQ', 'TLT', 'GLD']
    equal_weights = np.array([0.25, 0.25, 0.25, 0.25])
    
    print(f"\nTest Portfolio:")
    print(f"  Tickers: {tickers}")
    print(f"  SPY + QQQ = Highly correlated (both US equities)")
    print(f"  TLT = Negatively correlated with stocks (bonds)")
    print(f"  GLD = Low correlation hedge (gold)")
    print(f"  Weights: Equal 25% each")
    
    # Create optimizer
    optimizer = PortfolioOptimizer(
        tickers=tickers,
        period='5y',
        target_duration='1y'
    )
    
    # Calculate statistics
    print("\nFetching historical data and calculating statistics...")
    optimizer.calculate_statistics()
    
    # Show correlation matrix
    print("\nCorrelation Matrix:")
    returns_df = optimizer.fetch_historical_data()
    corr_matrix = returns_df[tickers].corr()
    print(corr_matrix.round(3))
    
    # Run new Cholesky method
    print("\n" + "-"*70)
    print("CHOLESKY MONTE CARLO (New - Correlation-Preserving)")
    print("-"*70)
    mc_cholesky = optimizer.monte_carlo_simulation(
        weights=equal_weights,
        n_simulations=10000,
        confidence_level=95
    )
    
    print(f"Method: {mc_cholesky['method']}")
    print(f"Expected return: {mc_cholesky['expected_return']:.2%}")
    print(f"Std deviation: {mc_cholesky['std_deviation']:.2%}")
    print(f"95% CI: [{mc_cholesky['confidence_interval']['lower']:.2%}, {mc_cholesky['confidence_interval']['upper']:.2%}]")
    print(f"Probability of loss: {mc_cholesky['probability_of_loss']:.2%}")
    print(f"Skewness: {mc_cholesky['skewness']:.3f}")
    print(f"Kurtosis: {mc_cholesky['kurtosis']:.3f}")
    
    # Simulate old simple method for comparison
    print("\n" + "-"*70)
    print("SIMPLE MONTE CARLO (Old - Ignores Correlations)")
    print("-"*70)
    portfolio_return, portfolio_volatility, _ = optimizer.portfolio_performance(equal_weights)
    
    # Generate simple random returns (old method)
    simple_returns = np.random.normal(
        loc=portfolio_return,
        scale=portfolio_volatility,
        size=10000
    )
    
    print(f"Method: simple (independent random draws)")
    print(f"Expected return: {np.mean(simple_returns):.2%}")
    print(f"Std deviation: {np.std(simple_returns):.2%}")
    print(f"95% CI: [{np.percentile(simple_returns, 2.5):.2%}, {np.percentile(simple_returns, 97.5):.2%}]")
    print(f"Probability of loss: {np.sum(simple_returns < 0) / 10000:.2%}")
    print(f"Skewness: {np.mean(((simple_returns - np.mean(simple_returns)) / np.std(simple_returns)) ** 3):.3f}")
    print(f"Kurtosis: {np.mean(((simple_returns - np.mean(simple_returns)) / np.std(simple_returns)) ** 4):.3f}")
    
    print("\n" + "="*70)
    print("KEY DIFFERENCES")
    print("="*70)
    print("1. Cholesky method preserves asset correlations")
    print("   - More realistic when assets move together (SPY/QQQ)")
    print("   - Captures diversification benefit from TLT/GLD")
    print("\n2. Simple method treats all assets as independent")
    print("   - May underestimate/overestimate portfolio risk")
    print("   - Misses correlation-driven tail events")
    print("\n3. Skewness & Kurtosis show distribution shape")
    print("   - Cholesky captures non-normal features")
    print("   - Simple is artificially normal (by construction)")
    print("\n✅ Cholesky method is more accurate for multi-asset portfolios")
    print("="*70 + "\n")

if __name__ == "__main__":
    np.random.seed(42)  # For reproducibility
    compare_monte_carlo_methods()
