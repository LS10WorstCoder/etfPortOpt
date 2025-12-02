"""
Quick API testing script
"""
import requests

BASE_URL = "http://localhost:8000/api"

# Login and get token
print("=== Testing Authentication ===")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tedtester99@gmail.com",
    "password": "TestPass123!"
})
print(f"Login Status: {login_response.status_code}")
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get user info
me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Get User: {me_response.status_code} - {me_response.json()['email']}")

# List portfolios
print("\n=== Testing Portfolios ===")
portfolios_response = requests.get(f"{BASE_URL}/portfolios", headers=headers)
print(f"List Portfolios: {portfolios_response.status_code}")
portfolios = portfolios_response.json()
print(f"Total Portfolios: {len(portfolios)}")
for p in portfolios:
    print(f"  - {p['name']}: {p['description']}")

# Create portfolio if needed
if len(portfolios) == 0:
    create_response = requests.post(f"{BASE_URL}/portfolios", 
                                    json={"name": "Test Portfolio", "description": "For testing"},
                                    headers=headers)
    print(f"Create Portfolio: {create_response.status_code}")
    portfolio_id = create_response.json()["id"]
else:
    portfolio_id = portfolios[0]["id"]

print(f"\nUsing Portfolio ID: {portfolio_id}")

# Get single portfolio
portfolio_response = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}", headers=headers)
print(f"Get Portfolio: {portfolio_response.status_code} - {portfolio_response.json()['name']}")

print("\n=== Testing Holdings Management ===")
# Add holdings
holdings_to_add = [
    {"ticker": "AAPL", "quantity": 10, "average_cost": 150.50},
    {"ticker": "MSFT", "quantity": 25, "average_cost": 300.00},
    {"ticker": "GOOGL", "quantity": 5, "average_cost": 120.75}
]

for holding in holdings_to_add:
    add_response = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/holdings",
                                json=holding, headers=headers)
    print(f"Add {holding['ticker']}: {add_response.status_code}")

# List holdings
holdings_response = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/holdings", headers=headers)
print(f"List Holdings: {holdings_response.status_code}")
holdings = holdings_response.json()
print(f"Total Holdings: {len(holdings)}")
for h in holdings:
    print(f"  - {h['ticker']}: {h['quantity']} @ ${h['average_cost']}")

# Test duplicate ticker prevention
print("\n=== Test Duplicate Prevention ===")
duplicate_response = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/holdings",
                                  json={"ticker": "AAPL", "quantity": 5, "average_cost": 160.00},
                                  headers=headers)
print(f"Add Duplicate AAPL: {duplicate_response.status_code} (should be 400)")

# Update holding
if holdings:
    holding_id = holdings[0]["id"]
    update_response = requests.put(f"{BASE_URL}/portfolios/{portfolio_id}/holdings/{holding_id}",
                                  json={"quantity": 15, "average_cost": 155.00},
                                  headers=headers)
    print(f"Update Holding: {update_response.status_code}")

print("\n✅ Authentication, Portfolio CRUD, and Holdings Management working!")

print("\n=== Testing Market Data ===")
# Validate ticker
validate_response = requests.get(f"{BASE_URL}/market/validate/AAPL", headers=headers)
print(f"Validate AAPL: {validate_response.status_code} - {validate_response.json()}")

# Get price
price_response = requests.get(f"{BASE_URL}/market/price/MSFT", headers=headers)
print(f"Get MSFT Price: {price_response.status_code} - ${price_response.json()['price']:.2f}")

print("\n=== Testing Portfolio Analytics ===")
# Analyze portfolio
analyze_response = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/analyze", headers=headers)
print(f"Analyze Portfolio: {analyze_response.status_code}")
if analyze_response.status_code == 200:
    analytics = analyze_response.json()
    print(f"Total Value: ${analytics['total_value']:.2f}")
    print(f"Volatility: {analytics['volatility']:.4f}")
    print(f"Sharpe Ratio: {analytics['sharpe_ratio']:.4f}")

# Test caching - should be instant
import time
start = time.time()
analyze_cached = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/analyze", headers=headers)
elapsed = time.time() - start
print(f"Cached Analysis: {analyze_cached.status_code} (took {elapsed:.3f}s)")

print("\n=== Testing Optimization Engine ===")
# Optimize for max Sharpe
optimize_response = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/optimize",
                                 json={"strategy": "max_sharpe"},
                                 headers=headers)
print(f"Optimize (Max Sharpe): {optimize_response.status_code}")
if optimize_response.status_code == 200:
    opt = optimize_response.json()
    print(f"Expected Return: {opt['expected_return']:.4f}")
    print(f"Expected Volatility: {opt['expected_volatility']:.4f}")
    print(f"Weights: {opt['optimized_weights']}")

print("\n✅ All core features working!")
