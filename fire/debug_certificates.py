#!/usr/bin/env python3
"""
Debug script to check certificates and applications
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json

def debug_certificates():
    """Debug certificates and applications"""
    
    print("Debugging certificates and applications...")
    
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']
        
        print("\n=== APPLICATIONS COLLECTION ===")
        
        # Get all applications
        applications = list(db.applications.find().limit(10))
        print(f"Total applications: {db.applications.count_documents({})}")
        print(f"Approved applications: {db.applications.count_documents({'status': 'approved'})}")
        print(f"Applications with certificates: {db.applications.count_documents({'certificate_issued': True})}")
        
        # Show recent applications
        print("\nRecent applications:")
        for app in applications:
            print(f"  ID: {app['_id']}")
            print(f"  Business: {app.get('business_name', 'N/A')}")
            print(f"  Username: {app.get('username', 'N/A')}")
            print(f"  Status: {app.get('status', 'N/A')}")
            print(f"  Certificate Issued: {app.get('certificate_issued', False)}")
            print(f"  Certificate Number: {app.get('certificate_number', 'N/A')}")
            print("  ---")
        
        print("\n=== CERTIFICATES COLLECTION ===")
        
        # Get all certificates
        certificates = list(db.certificates.find().limit(10))
        print(f"Total certificates: {db.certificates.count_documents({})}")
        
        # Show certificates
        print("\nCertificates:")
        for cert in certificates:
            print(f"  ID: {cert['_id']}")
            print(f"  Certificate Number: {cert.get('certificate_number', 'N/A')}")
            print(f"  Application ID: {cert.get('application_id', 'N/A')}")
            print(f"  Username: {cert.get('username', 'N/A')}")
            print(f"  Business: {cert.get('business_name', 'N/A')}")
            print(f"  Status: {cert.get('status', 'N/A')}")
            print(f"  Issued Date: {cert.get('issued_date', 'N/A')}")
            print("  ---")
        
        print("\n=== INSPECTIONS COLLECTION ===")
        
        # Get all inspections
        inspections = list(db.inspections.find().limit(5))
        print(f"Total inspections: {db.inspections.count_documents({})}")
        print(f"Completed inspections: {db.inspections.count_documents({'status': 'completed'})}")
        
        # Show inspections
        print("\nInspections:")
        for insp in inspections:
            print(f"  ID: {insp['_id']}")
            print(f"  Application ID: {insp.get('application_id', 'N/A')}")
            print(f"  Inspector: {insp.get('inspector', 'N/A')}")
            print(f"  Status: {insp.get('status', 'N/A')}")
            print(f"  Compliance Score: {insp.get('compliance_score', 'N/A')}")
            print("  ---")
        
        print("\n=== USER SPECIFIC DATA ===")
        
        # Check for specific user
        username = "mkbhh"  # The user from the screenshots
        print(f"\nChecking data for user: {username}")
        
        user_apps = list(db.applications.find({'username': username}))
        print(f"Applications for {username}: {len(user_apps)}")
        
        for app in user_apps:
            print(f"  App ID: {app['_id']}")
            print(f"  Business: {app.get('business_name', 'N/A')}")
            print(f"  Status: {app.get('status', 'N/A')}")
            print(f"  Certificate Issued: {app.get('certificate_issued', False)}")
            print(f"  Certificate Number: {app.get('certificate_number', 'N/A')}")
            
            # Check if certificate exists in certificates collection
            if app.get('certificate_number'):
                cert = db.certificates.find_one({'certificate_number': app['certificate_number']})
                print(f"  Certificate in DB: {'Yes' if cert else 'No'}")
                if cert:
                    print(f"  Certificate Username: {cert.get('username', 'N/A')}")
            
            # Check if inspection exists
            inspection = db.inspections.find_one({'application_id': app['_id']})
            print(f"  Inspection exists: {'Yes' if inspection else 'No'}")
            if inspection:
                print(f"  Inspection Status: {inspection.get('status', 'N/A')}")
            print("  ---")
        
        # Check certificates for this user
        user_certs = list(db.certificates.find({'username': username}))
        print(f"\nCertificates for {username}: {len(user_certs)}")
        
        for cert in user_certs:
            print(f"  Cert Number: {cert.get('certificate_number', 'N/A')}")
            print(f"  Application ID: {cert.get('application_id', 'N/A')}")
            print(f"  Business: {cert.get('business_name', 'N/A')}")
            print("  ---")
        
        # Check inspection reports for this user
        user_app_ids = [app['_id'] for app in user_apps]
        user_inspections = list(db.inspections.find({'application_id': {'$in': user_app_ids}}))
        print(f"\nInspection reports for {username}: {len(user_inspections)}")
        
        for insp in user_inspections:
            print(f"  Inspection ID: {insp['_id']}")
            print(f"  Application ID: {insp.get('application_id', 'N/A')}")
            print(f"  Status: {insp.get('status', 'N/A')}")
            print(f"  Inspector: {insp.get('inspector', 'N/A')}")
            print("  ---")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_certificates()
