"""Performance test for Monte Carlo simulation."""
import time
import numpy as np
import sys
sys.path.insert(0, '.')

from services.portfolio_optimizer import PortfolioOptimizer

def test_performance():
    print("\n" + "="*70)
    print("MONTE CARLO PERFORMANCE TEST")
    print("="*70)
    
    tickers = ['SPY', 'QQQ', 'TLT', 'GLD']
    weights = np.array([0.25, 0.25, 0.25, 0.25])
    
    optimizer = PortfolioOptimizer(
        tickers=tickers,
        period='5y',
        target_duration='1y'
    )
    
    # Initial statistics calculation (this is cached)
    print("\n1. Initial statistics calculation (fetches historical data):")
    start = time.time()
    optimizer.calculate_statistics()
    stats_time = time.time() - start
    print(f"   Time: {stats_time:.3f} seconds")
    
    # First Monte Carlo run
    print("\n2. First Monte Carlo simulation (10,000 runs):")
    start = time.time()
    mc1 = optimizer.monte_carlo_simulation(weights, n_simulations=10000)
    first_time = time.time() - start
    print(f"   Time: {first_time:.3f} seconds")
    print(f"   Method: {mc1['method']}")
    
    # Second Monte Carlo run (should be faster - no data fetch)
    print("\n3. Second Monte Carlo simulation (reuses cached data):")
    start = time.time()
    mc2 = optimizer.monte_carlo_simulation(weights, n_simulations=10000)
    second_time = time.time() - start
    print(f"   Time: {second_time:.3f} seconds")
    
    # Different simulation sizes
    print("\n4. Performance by simulation count:")
    for n_sims in [1000, 5000, 10000, 50000, 100000]:
        start = time.time()
        optimizer.monte_carlo_simulation(weights, n_simulations=n_sims)
        elapsed = time.time() - start
        print(f"   {n_sims:>6,} simulations: {elapsed:.3f}s ({n_sims/elapsed:,.0f} sims/sec)")
    
    print("\n" + "="*70)
    print("CACHING ANALYSIS")
    print("="*70)
    print(f"Initial data fetch: {stats_time:.3f}s (historical prices from yfinance)")
    print(f"Monte Carlo run:    {first_time:.3f}s (10,000 simulations)")
    print(f"Subsequent runs:    {second_time:.3f}s (reuses cached mean/cov)")
    print(f"\nSpeedup from caching: {first_time/second_time:.1f}x")
    
    # API scenario analysis
    print("\n" + "="*70)
    print("API REQUEST SCENARIOS")
    print("="*70)
    print("\nScenario 1: User requests optimization WITHOUT Monte Carlo")
    print(f"  - Data fetch + optimization: ~{stats_time + 0.1:.2f}s")
    print(f"  - No Monte Carlo overhead")
    
    print("\nScenario 2: User requests optimization WITH Monte Carlo")
    print(f"  - Data fetch + optimization: ~{stats_time + 0.1:.2f}s")
    print(f"  - Monte Carlo (10k sims):    +{first_time:.2f}s")
    print(f"  - Total:                     ~{stats_time + 0.1 + first_time:.2f}s")
    
    print("\nScenario 3: User runs MULTIPLE optimizations (same portfolio)")
    print(f"  - First request (with MC):   ~{stats_time + 0.1 + first_time:.2f}s")
    print(f"  - Second request (with MC):  ~{second_time:.2f}s (cached data)")
    print(f"  - Cache saves:               ~{stats_time:.2f}s per subsequent request")
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    if first_time < 1.0:
        print("✅ Monte Carlo is FAST (<1 second)")
        print("   - No need for separate caching layer")
        print("   - Can run on-demand with each optimization request")
        print("   - Results are fresh and reflect current parameters")
    else:
        print("⚠️  Monte Carlo is SLOW (>1 second)")
        print("   - Consider caching results by portfolio_id + parameters")
        print("   - Cache key: portfolio_id + strategy + duration + confidence_level")
        print("   - TTL: 1 hour or until portfolio holdings change")
    
    print(f"\nCurrent performance: {first_time:.3f}s is ", end="")
    if first_time < 0.5:
        print("EXCELLENT (no caching needed)")
    elif first_time < 1.0:
        print("GOOD (acceptable for on-demand)")
    elif first_time < 2.0:
        print("ACCEPTABLE (caching optional)")
    else:
        print("SLOW (caching recommended)")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    test_performance()
