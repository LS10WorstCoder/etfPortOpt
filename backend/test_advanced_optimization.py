"""
Test script for advanced optimization features:
1. Risk Budgeting (equal_risk strategy)
2. Maximum Drawdown constraint
3. Monte Carlo simulation
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_advanced_features():
    """Test all three new optimization features."""
    
    # Step 1: Login
    print("\n" + "="*60)
    print("TESTING ADVANCED OPTIMIZATION FEATURES")
    print("="*60)
    
    print("\n1. Logging in...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "tedtester99@gmail.com",
        "password": "TestPass123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Create test portfolio
    print("\n2. Creating test portfolio...")
    portfolio_response = requests.post(f"{BASE_URL}/api/portfolios", 
        headers=headers,
        json={
            "name": "Advanced Optimization Test",
            "description": "Testing risk parity, max drawdown, and Monte Carlo",
            "account_type": "taxable"
        }
    )
    
    if portfolio_response.status_code != 201:
        print(f"❌ Portfolio creation failed: {portfolio_response.status_code}")
        return
    
    portfolio_id = portfolio_response.json()['id']
    print(f"✅ Created portfolio: {portfolio_id}")
    
    # Step 3: Add diverse holdings
    print("\n3. Adding holdings...")
    holdings = [
        {"ticker": "SPY", "quantity": 50, "average_cost": 450.00},   # S&P 500
        {"ticker": "QQQ", "quantity": 30, "average_cost": 380.00},   # Nasdaq 100
        {"ticker": "TLT", "quantity": 40, "average_cost": 95.00},    # Long-term bonds
        {"ticker": "GLD", "quantity": 20, "average_cost": 180.00},   # Gold
    ]
    
    for holding in holdings:
        holding_response = requests.post(f"{BASE_URL}/api/portfolios/{portfolio_id}/holdings",
            headers=headers,
            json={**holding}
        )
        if holding_response.status_code == 201:
            print(f"   ✅ Added {holding['ticker']}")
        else:
            print(f"   ❌ Failed to add {holding['ticker']}: {holding_response.status_code} - {holding_response.text[:100]}")
    
    # Test 1: Equal Risk (Risk Parity) Strategy
    print("\n" + "="*60)
    print("TEST 1: EQUAL RISK CONTRIBUTION (RISK PARITY)")
    print("="*60)
    
    print("\nRunning equal_risk optimization...")
    risk_parity_response = requests.post(
        f"{BASE_URL}/api/portfolios/{portfolio_id}/optimize",
        headers=headers,
        params={
            "strategy": "equal_risk",
            "period": "1y",
            "target_duration": "1y"
        }
    )
    
    if risk_parity_response.status_code == 200:
        results = risk_parity_response.json()
        print("✅ Risk Parity optimization complete!")
        print(f"\n📊 Results:")
        print(f"   Strategy: {results['strategy']}")
        print(f"   Expected Return: {results['expected_return']:.2%}")
        print(f"   Volatility: {results['expected_volatility']:.2%}")
        print(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"\n🎯 Risk-Balanced Allocation:")
        for ticker, weight in results['weights'].items():
            print(f"   {ticker}: {weight:.2%}")
    else:
        print(f"❌ Risk parity failed: {risk_parity_response.status_code}")
        print(f"Response: {risk_parity_response.text}")
    
    # Test 2: Maximum Drawdown Constraint
    print("\n" + "="*60)
    print("TEST 2: MAXIMUM DRAWDOWN CONSTRAINT")
    print("="*60)
    
    print("\nRunning max_sharpe with 15% drawdown limit...")
    drawdown_response = requests.post(
        f"{BASE_URL}/api/portfolios/{portfolio_id}/optimize",
        headers=headers,
        params={
            "strategy": "max_sharpe",
            "period": "1y",
            "target_duration": "1y",
            "max_drawdown": 0.15  # 15% max loss
        }
    )
    
    if drawdown_response.status_code == 200:
        results = drawdown_response.json()
        print("✅ Drawdown-constrained optimization complete!")
        print(f"\n📊 Results (Max 15% Drawdown):")
        print(f"   Expected Return: {results['expected_return']:.2%}")
        print(f"   Volatility: {results['expected_volatility']:.2%}")
        print(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"\n🎯 Conservative Allocation:")
        for ticker, weight in results['weights'].items():
            print(f"   {ticker}: {weight:.2%}")
    else:
        print(f"❌ Drawdown constraint failed: {drawdown_response.status_code}")
        print(drawdown_response.json())
    
    # Test 3: Monte Carlo Simulation
    print("\n" + "="*60)
    print("TEST 3: MONTE CARLO SIMULATION")
    print("="*60)
    
    print("\nRunning optimization with Monte Carlo (95% confidence)...")
    mc_response = requests.post(
        f"{BASE_URL}/api/portfolios/{portfolio_id}/optimize",
        headers=headers,
        params={
            "strategy": "max_sharpe",
            "period": "1y",
            "target_duration": "6m",  # 6-month horizon
            "run_monte_carlo": True,
            "confidence_level": 95
        }
    )
    
    if mc_response.status_code == 200:
        results = mc_response.json()
        print("✅ Monte Carlo simulation complete!")
        print(f"\n📊 6-Month Optimization:")
        print(f"   Expected Return: {results['expected_return']:.2%}")
        print(f"   Volatility: {results['expected_volatility']:.2%}")
        
        if 'monte_carlo' in results:
            mc = results['monte_carlo']
            print(f"\n🎲 Monte Carlo Results ({mc['n_simulations']:,} simulations):")
            print(f"   Confidence Level: {mc['confidence_level']}%")
            print(f"   Expected Return: {mc['expected_return']:.2%}")
            print(f"   Median Return: {mc['median_return']:.2%}")
            print(f"   95% Confidence Interval:")
            print(f"      Lower: {mc['confidence_interval']['lower']:.2%}")
            print(f"      Upper: {mc['confidence_interval']['upper']:.2%}")
            print(f"   Probability of Loss: {mc['probability_of_loss']:.1%}")
    else:
        print(f"❌ Monte Carlo failed: {mc_response.status_code}")
        print(mc_response.json())
    
    # Test 4: Combine all features
    print("\n" + "="*60)
    print("TEST 4: COMBINED FEATURES")
    print("="*60)
    
    print("\nRunning equal_risk + max drawdown + Monte Carlo...")
    combined_response = requests.post(
        f"{BASE_URL}/api/portfolios/{portfolio_id}/optimize",
        headers=headers,
        params={
            "strategy": "equal_risk",
            "period": "2y",
            "target_duration": "2y",
            "max_drawdown": 0.20,  # 20% max loss
            "run_monte_carlo": True,
            "confidence_level": 90
        }
    )
    
    if combined_response.status_code == 200:
        results = combined_response.json()
        print("✅ Combined optimization complete!")
        print(f"\n📊 2-Year Risk Parity with 20% Max Drawdown:")
        print(f"   Expected Return: {results['expected_return']:.2%}")
        print(f"   Volatility: {results['expected_volatility']:.2%}")
        print(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        
        print(f"\n🎯 Allocation:")
        for ticker, weight in results['weights'].items():
            print(f"   {ticker}: {weight:.2%}")
        
        if 'monte_carlo' in results:
            mc = results['monte_carlo']
            print(f"\n🎲 90% Confidence Interval:")
            print(f"   {mc['confidence_interval']['lower']:.2%} to {mc['confidence_interval']['upper']:.2%}")
            print(f"   Probability of Loss: {mc['probability_of_loss']:.1%}")
    else:
        print(f"❌ Combined optimization failed: {combined_response.status_code}")
        print(combined_response.json())
    
    # Cleanup
    print("\n" + "="*60)
    print("5. Cleaning up...")
    delete_response = requests.delete(f"{BASE_URL}/api/portfolios/{portfolio_id}", headers=headers)
    
    if delete_response.status_code == 204:
        print("✅ Portfolio deleted successfully")
    
    print("\n🎉 All advanced optimization tests complete!")
    print("="*60)


if __name__ == "__main__":
    try:
        test_advanced_features()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
