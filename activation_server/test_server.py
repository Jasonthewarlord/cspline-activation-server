"""
Test the activation server locally.
"""

import requests
import json
import time
import subprocess
import threading
import os

SERVER_URL = "http://localhost:5000"

def test_health_check():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Health check passed")
            return True
        else:
            print(f"[FAIL] Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False

def test_activation_api():
    """Test the activation API."""
    print("\n=== Testing Activation API ===")
    
    # Test activation request
    activation_data = {
        "key": "CSPLINE-TEST-KEY1-2024",
        "email": "test@example.com",
        "name": "Test User",
        "machine_id": "FA0F9E318E74A0BA"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/activate",
            json=activation_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("[OK] Activation API working")
                print("Token received:", bool(result.get('token')))
                return True
            else:
                print(f"[FAIL] Activation failed: {result.get('error')}")
                return False
        else:
            print(f"[FAIL] Activation API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Activation API error: {e}")
        return False

def test_invalid_key():
    """Test activation with invalid key."""
    print("\n=== Testing Invalid Key ===")
    
    activation_data = {
        "key": "INVALID-KEY-123",
        "email": "test@example.com", 
        "name": "Test User",
        "machine_id": "FA0F9E318E74A0BA"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/activate",
            json=activation_data,
            timeout=10
        )
        
        if response.status_code == 400:
            result = response.json()
            if not result.get('success'):
                print("[OK] Invalid key properly rejected")
                return True
        
        print("[FAIL] Invalid key should be rejected")
        return False
        
    except Exception as e:
        print(f"[FAIL] Invalid key test error: {e}")
        return False

def run_server():
    """Start the Flask server in background."""
    print("Starting Flask server...")
    os.environ['FLASK_ENV'] = 'development'
    import app
    app.app.run(host='localhost', port=5000, debug=False, use_reloader=False)

def main():
    """Run server tests."""
    print("CSpline Activation Server Test")
    print("=" * 40)
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Run tests
    tests = [
        test_health_check,
        test_activation_api,
        test_invalid_key
    ]
    
    passed = 0
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[ERROR] Test {test_func.__name__} failed: {e}")
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("[SUCCESS] Server is working correctly!")
        print(f"\nAdmin interface: {SERVER_URL}/")
        print("Default password: admin123")
        return True
    else:
        print("[FAILURE] Some tests failed")
        return False

if __name__ == "__main__":
    main()
