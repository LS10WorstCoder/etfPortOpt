"""
Test Supabase authentication endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("=" * 60)
    print("Testing User Registration")
    print("=" * 60)
    
    payload = {
        "email": "testuser@example.com",
        "password": "TestPass123"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        return response.json()
    else:
        print("❌ Registration failed!")
        return None


def test_login():
    """Test user login"""
    print("\n" + "=" * 60)
    print("Testing User Login")
    print("=" * 60)
    
    payload = {
        "email": "testuser@example.com",
        "password": "TestPass123"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
        return response.json().get("access_token")
    else:
        print("❌ Login failed!")
        return None


def test_get_user(token):
    """Test getting current user info"""
    print("\n" + "=" * 60)
    print("Testing Get Current User")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Get user successful!")
        return True
    else:
        print("❌ Get user failed!")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Supabase Auth Tests\n")
    
    # Test 1: Register
    test_registration()
    
    # Test 2: Login
    token = test_login()
    
    # Test 3: Get current user
    if token:
        test_get_user(token)
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)
