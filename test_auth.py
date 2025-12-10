#!/usr/bin/env python
"""
Test script for authentication endpoints.

Usage:
    python test_auth.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"
session = requests.Session()  # This will handle cookies automatically

def print_response(response, title):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.cookies:
        print(f"Cookies: {dict(response.cookies)}")

def test_register():
    """Test user registration."""
    url = f"{BASE_URL}/api/auth/register/"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = session.post(url, json=data)
    print_response(response, "TEST: User Registration")
    return response.status_code == 201

def test_login():
    """Test user login."""
    url = f"{BASE_URL}/api/auth/login/"
    data = {
        "username": "testuser",
        "password": "TestPassword123!"
    }
    
    response = session.post(url, json=data)
    print_response(response, "TEST: User Login")
    return response.status_code == 200

def test_get_me():
    """Test getting current user."""
    url = f"{BASE_URL}/api/auth/me/"
    
    response = session.get(url)
    print_response(response, "TEST: Get Current User")
    return response.status_code == 200

def test_refresh():
    """Test token refresh."""
    url = f"{BASE_URL}/api/auth/refresh/"
    
    response = session.post(url)
    print_response(response, "TEST: Refresh Token")
    return response.status_code == 200

def test_logout():
    """Test user logout."""
    url = f"{BASE_URL}/api/auth/logout/"
    
    response = session.post(url)
    print_response(response, "TEST: User Logout")
    return response.status_code == 200

def test_google_login_url():
    """Test getting Google OAuth URL."""
    url = f"{BASE_URL}/api/auth/google/login/"
    
    response = session.get(url)
    print_response(response, "TEST: Get Google OAuth URL")
    return response.status_code == 200

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Starting Authentication API Tests")
    print("="*60)
    
    tests = [
        ("User Registration", test_register),
        ("User Login", test_login),
        ("Get Current User", test_get_me),
        ("Refresh Token", test_refresh),
        ("Get Google OAuth URL", test_google_login_url),
        ("User Logout", test_logout),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASSED" if result else "❌ FAILED"))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {str(e)}")
            results.append((name, f"❌ ERROR: {str(e)}"))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for name, result in results:
        print(f"{name}: {result}")
    
    passed = sum(1 for _, result in results if "✅" in result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
