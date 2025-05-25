#!/usr/bin/env python3
"""
Test script to verify manager inspection reports functionality
"""

import requests
import json
from datetime import datetime

# Base URL for the application
BASE_URL = "http://127.0.0.1:5000"

def test_manager_reports():
    """Test the manager inspection reports endpoint"""

    print("Testing Manager Inspection Reports...")

    # Create a session
    session = requests.Session()

    # First, let's try to access the manager reports API directly
    try:
        response = session.get(f"{BASE_URL}/api/manager/inspection-reports")
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print(f"Raw response text: {response.text[:500]}...")  # Show first 500 chars
            try:
                data = response.json()
                print(f"Success: {data.get('success')}")
                reports = data.get('reports', [])
                print(f"Number of reports found: {len(reports)}")

                if reports:
                    print("\nReports found:")
                    for i, report in enumerate(reports[:3]):  # Show first 3 reports
                        print(f"  {i+1}. Business: {report.get('business_name')}")
                        print(f"     Inspector: {report.get('inspector')}")
                        print(f"     Date: {report.get('inspection_date')}")
                        print(f"     Score: {report.get('compliance_score')}")
                        print(f"     Recommendation: {report.get('recommendation')}")
                        print()
                else:
                    print("No reports found in the response")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Response content type: {response.headers.get('content-type')}")

        elif response.status_code == 401:
            print("Unauthorized - Need to login as manager first")

        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error testing manager reports: {str(e)}")

def test_inspector_reports():
    """Test the inspector reports endpoint for comparison"""

    print("\nTesting Inspector Reports for comparison...")

    session = requests.Session()

    try:
        response = session.get(f"{BASE_URL}/api/inspector/reports")
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            reports = data.get('reports', [])
            print(f"Number of inspector reports found: {len(reports)}")

            if reports:
                print("\nInspector reports found:")
                for i, report in enumerate(reports[:3]):  # Show first 3 reports
                    print(f"  {i+1}. Business: {report.get('business_name')}")
                    print(f"     Inspector: {report.get('inspector')}")
                    print(f"     Date: {report.get('inspection_date')}")
                    print(f"     Score: {report.get('compliance_score')}")
                    print()

        elif response.status_code == 401:
            print("Unauthorized - Need to login as inspector first")

        else:
            print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Error testing inspector reports: {str(e)}")

def check_database_directly():
    """Check the database directly to see what data exists"""

    print("\nChecking database directly...")

    try:
        from pymongo import MongoClient

        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']

        # Check inspections collection
        inspections_count = db.inspections.count_documents({'status': 'completed'})
        print(f"Total completed inspections in database: {inspections_count}")

        # Get sample inspection
        sample_inspection = db.inspections.find_one({'status': 'completed'})
        if sample_inspection:
            print(f"Sample inspection ID: {sample_inspection.get('_id')}")
            print(f"Application ID: {sample_inspection.get('application_id')}")
            print(f"Inspector: {sample_inspection.get('inspector')}")
            print(f"Status: {sample_inspection.get('status')}")

            # Check corresponding application
            app_id = sample_inspection.get('application_id')
            if app_id:
                application = db.applications.find_one({'_id': app_id})
                if application:
                    print(f"Application found: {application.get('business_name')}")
                    print(f"Assigned manager: {application.get('assigned_manager')}")
                else:
                    print("No corresponding application found")

        # Check applications with assigned_manager
        apps_with_manager = db.applications.count_documents({'assigned_manager': {'$exists': True}})
        print(f"Applications with assigned_manager: {apps_with_manager}")

        client.close()

    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("MANAGER INSPECTION REPORTS TEST")
    print("=" * 50)

    test_manager_reports()
    test_inspector_reports()
    check_database_directly()

    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)
