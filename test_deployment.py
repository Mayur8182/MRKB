#!/usr/bin/env python3
"""
Fire Shakti PWA - Deployment Test Script
Tests all critical components before deployment
"""

import sys
import os
import importlib.util

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        # Test Flask app import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fire'))
        from app import app
        print("✅ Flask app import successful")
        
        # Test critical modules
        import flask
        import pymongo
        import bcrypt
        import reportlab
        print("✅ All critical modules available")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_wsgi():
    """Test WSGI application"""
    print("🧪 Testing WSGI application...")
    
    try:
        from simple_wsgi import application
        print("✅ WSGI application loaded successfully")
        return True
    except Exception as e:
        print(f"❌ WSGI error: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("🧪 Testing environment...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major == 3 and python_version.minor >= 10:
        print("✅ Python version compatible")
        return True
    else:
        print("❌ Python version incompatible")
        return False

def test_static_files():
    """Test static files"""
    print("🧪 Testing static files...")
    
    required_files = [
        'fire/static/manifest.json',
        'fire/static/service-worker.js',
        'fire/static/icons/icon-192x192.svg',
        'fire/static/icons/icon-512x512.svg'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 Fire Shakti PWA - Deployment Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("WSGI", test_wsgi),
        ("Static Files", test_static_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} Test:")
        result = test_func()
        results.append(result)
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All tests passed! Ready for deployment!")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    exit(main())
