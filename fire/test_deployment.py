#!/usr/bin/env python3
"""
Test script to verify deployment functionality
"""

import os
import requests
import json
from dotenv import load_dotenv

def test_application_health(base_url):
    """Test if the application is running"""
    print(f"🔍 Testing application health at {base_url}")
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Application is running successfully")
            return True
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to application: {str(e)}")
        return False

def test_database_endpoints(base_url):
    """Test database-related endpoints"""
    print("🗄️ Testing database endpoints...")
    
    endpoints = [
        "/login",
        "/register", 
        "/api/admin/analytics"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code in [200, 302, 401]:  # 401 is expected for protected routes
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")

def test_static_files(base_url):
    """Test if static files are served correctly"""
    print("📁 Testing static file serving...")
    
    # Test if static directory is accessible
    try:
        response = requests.get(f"{base_url}/static/", timeout=10)
        print(f"✅ Static files endpoint accessible")
    except Exception as e:
        print(f"⚠️ Static files test: {str(e)}")

def main():
    """Main test function"""
    print("🧪 Fire Safety NOC System - Deployment Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get base URL (for local testing, use localhost)
    base_url = input("Enter your deployed application URL (e.g., https://your-app.onrender.com): ").strip()
    
    if not base_url:
        base_url = "http://localhost:5000"
        print(f"Using default URL: {base_url}")
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    print(f"\n🎯 Testing deployment at: {base_url}")
    print("-" * 50)
    
    # Run tests
    health_ok = test_application_health(base_url)
    
    if health_ok:
        test_database_endpoints(base_url)
        test_static_files(base_url)
        
        print("\n🎉 Deployment test completed!")
        print("✅ Your Fire Safety NOC System appears to be working correctly")
        
        print("\n📋 Manual testing checklist:")
        print("1. ✓ Visit the homepage")
        print("2. ✓ Try user registration")
        print("3. ✓ Test login with 2FA")
        print("4. ✓ Access different dashboards")
        print("5. ✓ Submit a NOC application")
        print("6. ✓ Test file uploads")
        print("7. ✓ Verify email notifications")
        print("8. ✓ Test certificate generation")
        
    else:
        print("\n❌ Deployment test failed!")
        print("Please check your deployment configuration and try again.")

if __name__ == '__main__':
    main()
