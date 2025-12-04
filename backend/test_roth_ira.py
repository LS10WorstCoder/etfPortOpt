"""
Test script for Roth IRA portfolio optimization with whole-share constraints.
"""
import requests

BASE_URL = "http://localhost:8000"

def test_roth_ira_workflow():
    """Test complete Roth IRA workflow: create, import CSV, optimize."""
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test@example.com",
        "password": "Test123!@#"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Create Roth IRA portfolio
    print("\n2. Creating Roth IRA portfolio...")
    portfolio_response = requests.post(f"{BASE_URL}/portfolios", 
        headers=headers,
        json={
            "name": "My Roth IRA",
            "description": "Retirement account - whole shares only",
            "account_type": "roth_ira"
        }
    )
    
    if portfolio_response.status_code != 201:
        print(f"❌ Portfolio creation failed: {portfolio_response.status_code}")
        print(portfolio_response.json())
        return
    
    portfolio = portfolio_response.json()
    portfolio_id = portfolio['id']
    print(f"✅ Created Roth IRA portfolio: {portfolio_id}")
    print(f"   Account Type: {portfolio['account_type']}")
    
    # Step 3: Add holdings manually (simulating CSV import)
    print("\n3. Adding holdings...")
    holdings = [
        {"ticker": "VTI", "quantity": 25, "average_cost": 225.00},   # Vanguard Total Market
        {"ticker": "VXUS", "quantity": 15, "average_cost": 60.00},   # Vanguard International
        {"ticker": "BND", "quantity": 30, "average_cost": 78.00},    # Vanguard Total Bond
    ]
    
    for holding in holdings:
        holding_response = requests.post(f"{BASE_URL}/holdings",
            headers=headers,
            json={**holding, "portfolio_id": portfolio_id}
        )
        if holding_response.status_code == 201:
            print(f"   ✅ Added {holding['ticker']}: {holding['quantity']} shares @ ${holding['average_cost']}")
        else:
            print(f"   ❌ Failed to add {holding['ticker']}: {holding_response.status_code}")
    
    # Step 4: Optimize portfolio (max Sharpe ratio)
    print("\n4. Running optimization (max Sharpe ratio)...")
    opt_response = requests.post(
        f"{BASE_URL}/portfolios/{portfolio_id}/optimize",
        headers=headers,
        params={"strategy": "max_sharpe", "period": "1y"}
    )
    
    if opt_response.status_code != 200:
        print(f"❌ Optimization failed: {opt_response.status_code}")
        print(opt_response.json())
        return
    
    results = opt_response.json()
    print("✅ Optimization complete!")
    print(f"\n📊 Results for {results.get('account_type', 'unknown')} account:")
    print(f"   Strategy: {results['strategy']}")
    print(f"   Whole Shares: {results.get('whole_shares', False)}")
    print(f"   Expected Return: {results['expected_return']:.2%}")
    print(f"   Expected Volatility: {results['expected_volatility']:.2%}")
    print(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    print(f"\n🎯 Optimized Allocation:")
    for ticker, weight in results['weights'].items():
        print(f"   {ticker}: {weight:.2%}")
    
    if 'current_allocation' in results:
        print(f"\n📈 Current Allocation:")
        for ticker, weight in results['current_allocation'].items():
            print(f"   {ticker}: {weight:.2%}")
    
    if 'rebalancing_needed' in results:
        print(f"\n🔄 Rebalancing Needed:")
        for ticker, change in results['rebalancing_needed'].items():
            direction = "🟢 increase" if change > 0 else "🔴 decrease"
            print(f"   {ticker}: {direction} by {abs(change):.2%}")
    
    if 'note' in results:
        print(f"\n💡 Note: {results['note']}")
    
    # Step 5: Compare with taxable account optimization
    print("\n5. Creating taxable account for comparison...")
    taxable_response = requests.post(f"{BASE_URL}/portfolios", 
        headers=headers,
        json={
            "name": "My Brokerage Account",
            "description": "Taxable account - fractional shares allowed",
            "account_type": "taxable"
        }
    )
    
    if taxable_response.status_code == 201:
        taxable_portfolio = taxable_response.json()
        taxable_id = taxable_portfolio['id']
        
        # Add same holdings
        for holding in holdings:
            requests.post(f"{BASE_URL}/holdings",
                headers=headers,
                json={**holding, "portfolio_id": taxable_id}
            )
        
        # Optimize taxable account
        taxable_opt_response = requests.post(
            f"{BASE_URL}/portfolios/{taxable_id}/optimize",
            headers=headers,
            params={"strategy": "max_sharpe", "period": "1y"}
        )
        
        if taxable_opt_response.status_code == 200:
            taxable_results = taxable_opt_response.json()
            print(f"\n📊 Taxable Account Results:")
            print(f"   Whole Shares: {taxable_results.get('whole_shares', False)}")
            print(f"   Sharpe Ratio: {taxable_results['sharpe_ratio']:.2f}")
            print(f"\n🎯 Taxable Optimized Allocation:")
            for ticker, weight in taxable_results['weights'].items():
                print(f"   {ticker}: {weight:.2%}")
        
        # Cleanup taxable portfolio
        requests.delete(f"{BASE_URL}/portfolios/{taxable_id}", headers=headers)
    
    # Step 6: Cleanup
    print("\n6. Cleaning up...")
    delete_response = requests.delete(f"{BASE_URL}/portfolios/{portfolio_id}", headers=headers)
    
    if delete_response.status_code == 204:
        print("✅ Portfolio deleted successfully")
    
    print("\n🎉 Roth IRA test complete!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Roth IRA Portfolio Optimization")
    print("=" * 60)
    
    try:
        test_roth_ira_workflow()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
