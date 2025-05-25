#!/usr/bin/env python3
"""
Quick script to update user role to manager
"""

import requests
import json

def update_user_role_to_manager():
    """Update the current user's role to manager"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🔧 Updating user role to manager...")
    
    try:
        # First check current session
        response = requests.get(f"{base_url}/api/debug/session")
        if response.status_code == 200:
            session_data = response.json()
            print(f"Current user: {session_data.get('username')}")
            print(f"Current role: {session_data.get('role')}")
        
        # Update role to manager
        response = requests.post(
            f"{base_url}/api/update-current-user-role",
            json={"role": "manager"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message')}")
            print(f"New role: {result.get('new_role')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Verify the change
        print("\n🔍 Verifying role change...")
        response = requests.get(f"{base_url}/api/debug/session")
        if response.status_code == 200:
            session_data = response.json()
            print(f"Updated user: {session_data.get('username')}")
            print(f"Updated role: {session_data.get('role')}")
            print(f"Is manager: {session_data.get('is_manager')}")
        
        # Test manager endpoints
        print("\n🧪 Testing manager endpoints...")
        
        # Test manager session check
        response = requests.get(f"{base_url}/api/manager/session-check")
        if response.status_code == 200:
            print("✅ Manager session check: PASSED")
        else:
            print(f"❌ Manager session check: FAILED ({response.status_code})")
            
        # Test analytics endpoint
        response = requests.get(f"{base_url}/api/manager/real-analytics")
        if response.status_code == 200:
            print("✅ Manager analytics: PASSED")
        else:
            print(f"❌ Manager analytics: FAILED ({response.status_code})")
            
        # Test inspection reports endpoint
        response = requests.get(f"{base_url}/api/manager/inspection-reports")
        if response.status_code == 200:
            print("✅ Manager inspection reports: PASSED")
        else:
            print(f"❌ Manager inspection reports: FAILED ({response.status_code})")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_user_role_to_manager()
