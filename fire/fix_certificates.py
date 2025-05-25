#!/usr/bin/env python3
"""
Script to manually generate certificates for approved applications
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import json

def fix_certificates():
    """Generate certificates for approved applications that don't have them"""
    
    print("Fixing certificates for approved applications...")
    
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']
        
        # Find approved applications without certificates
        approved_apps = list(db.applications.find({
            'status': 'approved',
            'certificate_issued': {'$ne': True}
        }))
        
        print(f"Found {len(approved_apps)} approved applications without certificates")
        
        for app in approved_apps:
            print(f"\nProcessing application: {app['_id']}")
            print(f"Business: {app.get('business_name', 'N/A')}")
            print(f"Username: {app.get('username', 'N/A')}")
            
            # Check if inspection exists
            inspection = db.inspections.find_one({
                'application_id': app['_id'],
                'status': 'completed'
            })
            
            if not inspection:
                print("  No completed inspection found, skipping...")
                continue
            
            print(f"  Found inspection by: {inspection.get('inspector', 'Unknown')}")
            
            # Generate certificate
            certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(ObjectId())[-6:].upper()}"
            
            # Get inspector details
            inspector_name = inspection.get('inspector', 'Unknown')
            compliance_score = inspection.get('compliance_score', 85)
            
            certificate_data = {
                'certificate_number': certificate_number,
                'application_id': app['_id'],
                'user_id': app.get('user_id'),
                'username': app.get('username', ''),
                'business_name': app.get('business_name', ''),
                'business_address': app.get('business_address', ''),
                'business_type': app.get('business_type', ''),
                'owner_name': app.get('owner_name', ''),
                'contact_number': app.get('contact_number', ''),
                'email': app.get('email', ''),
                'issued_date': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=365),
                'issued_by': 'System',
                'inspector_name': inspector_name,
                'compliance_score': compliance_score,
                'status': 'active',
                'certificate_path': f"certificates/{certificate_number}.pdf"
            }
            
            # Insert certificate
            result = db.certificates.insert_one(certificate_data)
            print(f"  Certificate created: {certificate_number}")
            print(f"  Certificate ID: {result.inserted_id}")
            
            # Update application
            db.applications.update_one(
                {'_id': app['_id']},
                {
                    '$set': {
                        'certificate_number': certificate_number,
                        'certificate_issued': True,
                        'certificate_issued_date': datetime.now(),
                        'certificate_path': certificate_data['certificate_path']
                    }
                }
            )
            print(f"  Application updated with certificate details")
        
        print(f"\nFixed {len(approved_apps)} applications")
        
        # Verify the fix
        print("\n=== VERIFICATION ===")
        total_certs = db.certificates.count_documents({})
        print(f"Total certificates now: {total_certs}")
        
        # Check mkbhh user specifically
        mkbhh_apps = list(db.applications.find({'username': 'mkbhh', 'status': 'approved'}))
        print(f"mkbhh approved applications: {len(mkbhh_apps)}")
        
        mkbhh_certs = list(db.certificates.find({'username': 'mkbhh'}))
        print(f"mkbhh certificates: {len(mkbhh_certs)}")
        
        for cert in mkbhh_certs:
            print(f"  Certificate: {cert['certificate_number']}")
            print(f"  Business: {cert['business_name']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_certificates()
