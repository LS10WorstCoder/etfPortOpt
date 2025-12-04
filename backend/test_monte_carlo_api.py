"""Quick API test for Monte Carlo simulation."""
import requests
import json

BASE_URL = "http://localhost:8000"

def quick_test():
    # Login
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "tedtester99@gmail.com",
        "password": "TestPass123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test portfolio
    portfolio_response = requests.post(
        f"{BASE_URL}/api/portfolios",
        headers=headers,
        json={"name": "MC Test", "description": "Monte Carlo API test"}
    )
    portfolio_id = portfolio_response.json()['id']
    
    # Add holdings
    tickers = ['SPY', 'QQQ', 'TLT', 'GLD']
    for ticker in tickers:
        requests.post(
            f"{BASE_URL}/api/portfolios/{portfolio_id}/holdings",
            headers=headers,
            json={"ticker": ticker, "quantity": 10, "average_cost": 100.0}
        )
    
    # Test Monte Carlo with equal weight strategy
    print("\n" + "="*60)
    print("TESTING MONTE CARLO VIA API")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/api/optimize/portfolio/{portfolio_id}",
        headers=headers,
        params={
            "strategy": "equal_weight",
            "target_duration": "1y",
            "run_monte_carlo": True,
            "confidence_level": 95
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        if 'monte_carlo' in result:
            mc = result['monte_carlo']
            print("\n✅ Monte Carlo Results:")
            print(f"  Method: {mc['method']}")
            print(f"  Simulations: {mc['n_simulations']:,}")
            print(f"  Expected return: {mc['expected_return']:.2%}")
            print(f"  Std deviation: {mc['std_deviation']:.2%}")
            print(f"  95% CI: [{mc['confidence_interval']['lower']:.2%}, {mc['confidence_interval']['upper']:.2%}]")
            print(f"  Probability of loss: {mc['probability_of_loss']:.2%}")
            print(f"  Skewness: {mc['skewness']:.3f}")
            print(f"  Kurtosis: {mc['kurtosis']:.3f}")
            
            if mc['method'] == 'cholesky':
                print("\n✅ SUCCESS: API using Cholesky decomposition!")
            else:
                print("\n⚠️  WARNING: Fell back to simple method")
        else:
            print("❌ No monte_carlo in response")
    else:
        print(f"❌ API request failed: {response.status_code}")
        print(response.text)
    
    # Cleanup
    requests.delete(f"{BASE_URL}/api/portfolios/{portfolio_id}", headers=headers)
    print("\n" + "="*60)

if __name__ == "__main__":
    quick_test()
