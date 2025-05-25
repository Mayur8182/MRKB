#!/usr/bin/env python3
"""
Quick check for specific application
"""

from pymongo import MongoClient
from bson import ObjectId

def check_application():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']
        
        app_id = "68315cfa516df556eff65c0a"
        print(f"Checking application: {app_id}")
        
        app = db.applications.find_one({'_id': ObjectId(app_id)})
        if app:
            print(f"Application found:")
            print(f"  Business: {app.get('business_name', 'N/A')}")
            print(f"  Username: {app.get('username', 'N/A')}")
            print(f"  Status: {app.get('status', 'N/A')}")
            print(f"  Certificate Issued: {app.get('certificate_issued', False)}")
            print(f"  Certificate Number: {app.get('certificate_number', 'N/A')}")
        else:
            print("Application not found")
        
        # Check certificate
        cert = db.certificates.find_one({'application_id': ObjectId(app_id)})
        if cert:
            print(f"\nCertificate found:")
            print(f"  Certificate Number: {cert.get('certificate_number', 'N/A')}")
            print(f"  Business: {cert.get('business_name', 'N/A')}")
            print(f"  Status: {cert.get('status', 'N/A')}")
        else:
            print("\nCertificate not found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_application()
