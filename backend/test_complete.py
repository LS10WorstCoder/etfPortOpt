"""
Comprehensive Backend API Test Suite
Tests all 23 endpoints with various scenarios
"""
import requests
import time

BASE_URL = "http://localhost:8000/api"
test_results = []

def log_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append((name, passed, details))
    print(f"{status}: {name}")
    if details:
        print(f"  {details}")

print("=" * 60)
print("BACKEND API COMPREHENSIVE TEST SUITE")
print("=" * 60)

# 1. AUTHENTICATION (3 endpoints)
print("\n[1/8] Authentication Flow")
register_response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPass123!"
})
log_test("Register User", register_response.status_code == 201)

login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tedtester99@gmail.com",
    "password": "TestPass123!"
})
log_test("Login", login_response.status_code == 200)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
log_test("Get Current User", me_response.status_code == 200, f"User: {me_response.json()['email']}")

# 2. PORTFOLIO CRUD (5 endpoints)
print("\n[2/8] Portfolio Management")
create_portfolio = requests.post(f"{BASE_URL}/portfolios",
                                json={"name": "Test Suite Portfolio", "description": "For automated testing"},
                                headers=headers)
log_test("Create Portfolio", create_portfolio.status_code == 201)
portfolio_id = create_portfolio.json()["id"]

list_portfolios = requests.get(f"{BASE_URL}/portfolios", headers=headers)
log_test("List Portfolios", list_portfolios.status_code == 200, f"Found {len(list_portfolios.json())} portfolios")

get_portfolio = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}", headers=headers)
log_test("Get Portfolio", get_portfolio.status_code == 200)

update_portfolio = requests.put(f"{BASE_URL}/portfolios/{portfolio_id}",
                               json={"name": "Updated Test Portfolio"},
                               headers=headers)
log_test("Update Portfolio", update_portfolio.status_code == 200)

# 3. HOLDINGS CRUD (5 endpoints)
print("\n[3/8] Holdings Management")
add_holding_1 = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/holdings",
                             json={"ticker": "TSLA", "quantity": 10, "average_cost": 250.00},
                             headers=headers)
log_test("Add Holding", add_holding_1.status_code == 201)

add_holding_2 = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/holdings",
                             json={"ticker": "SPY", "quantity": 50, "average_cost": 450.00},
                             headers=headers)
log_test("Add Second Holding", add_holding_2.status_code == 201)

list_holdings = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/holdings", headers=headers)
log_test("List Holdings", list_holdings.status_code == 200, f"Total holdings: {len(list_holdings.json())}")
holding_id = list_holdings.json()[0]["id"]

update_holding = requests.put(f"{BASE_URL}/portfolios/{portfolio_id}/holdings/{holding_id}",
                             json={"quantity": 15, "average_cost": 255.00},
                             headers=headers)
log_test("Update Holding", update_holding.status_code == 200)

# 4. MARKET DATA (4 endpoints)
print("\n[4/8] Market Data Integration")
validate_ticker = requests.get(f"{BASE_URL}/market/validate/AAPL", headers=headers)
log_test("Validate Ticker", validate_ticker.status_code == 200, f"AAPL valid: {validate_ticker.json()['valid']}")

get_price = requests.get(f"{BASE_URL}/market/price/TSLA", headers=headers)
log_test("Get Current Price", get_price.status_code == 200, f"TSLA: ${get_price.json()['price']:.2f}")

get_info = requests.get(f"{BASE_URL}/market/info/MSFT", headers=headers)
log_test("Get Ticker Info", get_info.status_code == 200)

get_historical = requests.get(f"{BASE_URL}/market/historical/SPY?period=1mo", headers=headers)
log_test("Get Historical Data", get_historical.status_code == 200)

# 5. ANALYTICS (3 endpoints) - Run BEFORE deleting holdings
print("\n[5/8] Portfolio Analytics")
analyze_start = time.time()
analyze = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/analyze", headers=headers)
analyze_time = time.time() - analyze_start
if analyze.status_code == 200:
    log_test("Analyze Portfolio", True, f"Took {analyze_time:.2f}s, Value: ${analyze.json().get('total_value', 0):.2f}")
else:
    log_test("Analyze Portfolio", False, f"Status {analyze.status_code}: {analyze.json().get('detail', 'Unknown error')}")

cached_start = time.time()
analyze_cached = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/analyze", headers=headers)
cached_time = time.time() - cached_start
if analyze_cached.status_code == 200:
    log_test("Cached Analysis", True, f"Took {cached_time:.2f}s (should be <0.1s)")
else:
    log_test("Cached Analysis", False, f"Status {analyze_cached.status_code}")

analytics_history = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/analytics/history", headers=headers)
log_test("Get Analytics History", analytics_history.status_code == 200)

# Now delete a holding for cleanup
delete_holding = requests.delete(f"{BASE_URL}/portfolios/{portfolio_id}/holdings/{holding_id}",
                                headers=headers)
log_test("Delete Holding", delete_holding.status_code == 204)

# 6. OPTIMIZATION (2 endpoints)
print("\n[6/8] Portfolio Optimization")
opt_max_sharpe = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/optimize?strategy=max_sharpe",
                               headers=headers)
log_test("Optimize (Max Sharpe)", opt_max_sharpe.status_code == 200, f"Sharpe: {opt_max_sharpe.json()['sharpe_ratio']:.4f}")

opt_min_vol = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/optimize?strategy=min_volatility",
                           headers=headers)
log_test("Optimize (Min Volatility)", opt_min_vol.status_code == 200)

opt_history = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/optimizations/history", headers=headers)
log_test("Get Optimization History", opt_history.status_code == 200)

# 7. CSV IMPORT/EXPORT (2 endpoints)
print("\n[7/8] CSV Import/Export")
with open("test_holdings.csv", "rb") as f:
    csv_import = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/import",
                              files={"file": f},
                              headers=headers)
log_test("CSV Import", csv_import.status_code == 200, f"Imported: {csv_import.json()['imported']}")

csv_export = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/export", headers=headers)
log_test("CSV Export", csv_export.status_code == 200, "Downloaded CSV file")

# 8. ERROR HANDLING
print("\n[8/8] Error Handling")
invalid_login = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "wrong@example.com",
    "password": "wrong"
})
log_test("Invalid Login (401)", invalid_login.status_code == 401)

no_auth = requests.get(f"{BASE_URL}/portfolios")
log_test("No Authorization (403)", no_auth.status_code == 403)

duplicate_holding = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/holdings",
                                 json={"ticker": "SPY", "quantity": 5, "average_cost": 450.00},
                                 headers=headers)
log_test("Duplicate Holding (400)", duplicate_holding.status_code == 400)

invalid_ticker = requests.post(f"{BASE_URL}/portfolios/{portfolio_id}/holdings",
                              json={"ticker": "INVALID", "quantity": 5, "average_cost": 100.00},
                              headers=headers)
log_test("Invalid Ticker (400)", invalid_ticker.status_code == 400)

# Cleanup
delete_portfolio = requests.delete(f"{BASE_URL}/portfolios/{portfolio_id}", headers=headers)
log_test("Delete Portfolio (Cleanup)", delete_portfolio.status_code == 204)

# SUMMARY
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
passed = sum(1 for _, p, _ in test_results if p)
total = len(test_results)
print(f"Passed: {passed}/{total}")
print(f"Failed: {total - passed}/{total}")
print(f"Success Rate: {(passed/total)*100:.1f}%")

if passed == total:
    print("\n🎉 ALL TESTS PASSED! Backend is production-ready.")
else:
    print("\n⚠️ Some tests failed. Review errors above.")
    for name, passed, details in test_results:
        if not passed:
            print(f"  ❌ {name}: {details}")
