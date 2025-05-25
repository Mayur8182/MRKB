#!/usr/bin/env python3
"""
Test script to verify application submission functionality
"""

import requests
import json

def test_application_submission():
    """Test the application submission endpoint"""
    
    # Base URL
    base_url = "http://127.0.0.1:5000"
    
    # Test data
    test_data = {
        'businessName': 'Test Business',
        'businessType': 'Restaurant',
        'businessAddress': '123 Test Street, Test City',
        'contactPerson': 'John Doe',
        'contactNumber': '9876543210',
        'emailAddress': 'test@example.com',
        'buildingArea': '1000',
        'floors': '2',
        'occupancyType': 'Commercial',
        'maxOccupancy': '50',
        'fireExtinguishers': 'Yes - 5 units',
        'fireAlarm': 'Yes - Installed',
        'emergencyExits': 'Yes - 2 exits',
        'sprinklerSystem': 'No',
        'fireSafetyOfficer': 'No',
        'lastFireDrill': '2024-01-15'
    }
    
    print("🔥 Testing Fire NOC Application Submission")
    print("=" * 50)
    
    # First, test the test endpoint
    print("\n1. Testing debug endpoint...")
    try:
        response = requests.post(f"{base_url}/api/test-submission", data=test_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result}")
            print("   ✅ Debug endpoint working!")
        else:
            print(f"   ❌ Debug endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error testing debug endpoint: {e}")
    
    # Test the actual submission endpoint
    print("\n2. Testing actual submission endpoint...")
    try:
        response = requests.post(f"{base_url}/submit_noc", data=test_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Application submission working!")
                print(f"   Application ID: {result.get('application_id')}")
            else:
                print(f"   ❌ Submission failed: {result.get('error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing submission: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_application_submission()
