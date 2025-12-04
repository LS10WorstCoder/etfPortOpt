"""Simple test of the improved Monte Carlo with Cholesky decomposition."""
import numpy as np
import sys
sys.path.insert(0, '.')

from services.portfolio_optimizer import PortfolioOptimizer

def test_monte_carlo():
    print("\n" + "="*60)
    print("TESTING IMPROVED MONTE CARLO (CHOLESKY DECOMPOSITION)")
    print("="*60)
    
    # Test portfolio: SPY, QQQ, TLT, GLD
    tickers = ['SPY', 'QQQ', 'TLT', 'GLD']
    equal_weights = np.array([0.25, 0.25, 0.25, 0.25])
    
    print(f"\nTickers: {tickers}")
    print(f"Weights: {equal_weights}")
    
    # Create optimizer
    optimizer = PortfolioOptimizer(
        tickers=tickers,
        period='5y',
        target_duration='1y'
    )
    
    # Calculate statistics (this will cache mean_returns and cov_matrix)
    print("\nCalculating statistics...")
    stats = optimizer.calculate_statistics()
    print(f"Mean returns calculated: {optimizer.mean_returns is not None}")
    print(f"Covariance matrix calculated: {optimizer.cov_matrix is not None}")
    
    # Run Monte Carlo simulation
    print("\nRunning Monte Carlo simulation (10,000 simulations)...")
    mc_results = optimizer.monte_carlo_simulation(
        weights=equal_weights,
        n_simulations=10000,
        confidence_level=95
    )
    
    # Display results
    print("\n" + "="*60)
    print("MONTE CARLO RESULTS")
    print("="*60)
    print(f"Method: {mc_results['method']}")
    print(f"Number of simulations: {mc_results['n_simulations']:,}")
    print(f"Confidence level: {mc_results['confidence_level']}%")
    print(f"\nExpected return: {mc_results['expected_return']:.2%}")
    print(f"Median return: {mc_results['median_return']:.2%}")
    print(f"Std deviation: {mc_results['std_deviation']:.2%}")
    print(f"\n{mc_results['confidence_level']}% Confidence interval:")
    print(f"  Lower bound: {mc_results['confidence_interval']['lower']:.2%}")
    print(f"  Upper bound: {mc_results['confidence_interval']['upper']:.2%}")
    print(f"\nProbability of loss: {mc_results['probability_of_loss']:.2%}")
    print(f"Skewness: {mc_results['skewness']:.3f}")
    print(f"Kurtosis: {mc_results['kurtosis']:.3f}")
    print(f"\nTarget duration: {mc_results['target_duration']}")
    
    # Verify Cholesky method was used
    if mc_results['method'] == 'cholesky':
        print("\n✅ SUCCESS: Using Cholesky decomposition (correlation-preserving)")
    else:
        print("\n⚠️  WARNING: Fell back to simple method")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_monte_carlo()
