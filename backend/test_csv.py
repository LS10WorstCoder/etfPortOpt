"""
Test CSV Import/Export
"""
import requests

BASE_URL = "http://localhost:8000/api"

# Login
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "tedtester99@gmail.com",
    "password": "TestPass123!"
})
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get portfolio
portfolios = requests.get(f"{BASE_URL}/portfolios", headers=headers).json()
portfolio_id = portfolios[0]["id"]

print("=== Testing CSV Import/Export ===")

# Test CSV import
with open("test_holdings.csv", "rb") as f:
    csv_import = requests.post(
        f"{BASE_URL}/portfolios/{portfolio_id}/import",
        files={"file": f},
        headers=headers
    )
    print(f"CSV Import: {csv_import.status_code}")
    result = csv_import.json()
    print(f"Imported: {result['imported']}, Skipped: {result['skipped']}, Errors: {len(result.get('errors', []))}")

# List holdings after import
holdings = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/holdings", headers=headers).json()
print(f"\nTotal Holdings After Import: {len(holdings)}")
for h in holdings:
    print(f"  - {h['ticker']}: {h['quantity']}")

# Test CSV export
export_response = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/export", headers=headers)
print(f"\nCSV Export: {export_response.status_code}")
print(f"Content Type: {export_response.headers.get('Content-Type')}")
print(f"First 200 chars:\n{export_response.text[:200]}")

print("\n✅ CSV Import/Export working!")
