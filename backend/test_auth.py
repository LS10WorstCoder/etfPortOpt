"""
Test script for authentication endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/auth"

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 201

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123"
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Token: {data.get('access_token', '')[:50]}...")
    
    return response.status_code == 200, data.get('access_token')

def test_get_current_user(token):
    """Test getting current user info"""
    print("\nTesting get current user...")
    
    response = requests.get(
        f"{BASE_URL}/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_invalid_login():
    """Test login with wrong password"""
    print("\nTesting invalid login...")
    
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 401

if __name__ == "__main__":
    print("=" * 60)
    print("Authentication API Tests")
    print("=" * 60)
    
    # Test registration
    if test_registration():
        print("✓ Registration successful")
    else:
        print("✗ Registration failed")
    
    # Test login
    login_success, token = test_login()
    if login_success:
        print("✓ Login successful")
        
        # Test getting current user
        if test_get_current_user(token):
            print("✓ Get current user successful")
        else:
            print("✗ Get current user failed")
    else:
        print("✗ Login failed")
    
    # Test invalid login
    if test_invalid_login():
        print("✓ Invalid login properly rejected")
    else:
        print("✗ Invalid login test failed")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
