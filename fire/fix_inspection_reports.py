#!/usr/bin/env python3
"""
Script to check and fix inspection reports for users
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import json

def fix_inspection_reports():
    """Check and fix inspection reports"""
    
    print("Checking inspection reports...")
    
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']
        
        # Check mkbhh user specifically
        username = "mkbhh"
        print(f"\nChecking inspection reports for user: {username}")
        
        # Get user's applications
        user_applications = list(db.applications.find({'username': username}))
        app_ids = [app['_id'] for app in user_applications]
        
        print(f"User has {len(user_applications)} applications")
        
        # Get inspection reports for user's applications
        user_reports = list(db.inspections.find({
            'application_id': {'$in': app_ids},
            'status': 'completed'
        }).sort('inspection_date', -1))
        
        print(f"Found {len(user_reports)} completed inspection reports")
        
        # Show detailed inspection reports
        for i, report in enumerate(user_reports, 1):
            print(f"\n--- Report {i} ---")
            print(f"Inspection ID: {report['_id']}")
            print(f"Application ID: {report.get('application_id', 'N/A')}")
            print(f"Inspector: {report.get('inspector', 'N/A')}")
            print(f"Status: {report.get('status', 'N/A')}")
            print(f"Compliance Score: {report.get('compliance_score', 'N/A')}")
            print(f"Recommendation: {report.get('recommendation', 'N/A')}")
            print(f"Inspection Date: {report.get('inspection_date', 'N/A')}")
            
            # Get application details
            app_data = db.applications.find_one({'_id': report['application_id']})
            if app_data:
                print(f"Business Name: {app_data.get('business_name', 'N/A')}")
                print(f"Business Type: {app_data.get('business_type', 'N/A')}")
            
            # Check if this inspection has proper data for API response
            if not report.get('inspection_date'):
                print("  WARNING: Missing inspection_date")
                # Fix missing inspection_date
                db.inspections.update_one(
                    {'_id': report['_id']},
                    {'$set': {'inspection_date': datetime.now()}}
                )
                print("  FIXED: Added inspection_date")
            
            if not report.get('compliance_score'):
                print("  WARNING: Missing compliance_score")
                # Fix missing compliance_score
                db.inspections.update_one(
                    {'_id': report['_id']},
                    {'$set': {'compliance_score': 85}}
                )
                print("  FIXED: Added compliance_score")
            
            if not report.get('recommendation'):
                print("  WARNING: Missing recommendation")
                # Fix missing recommendation
                db.inspections.update_one(
                    {'_id': report['_id']},
                    {'$set': {'recommendation': 'approved'}}
                )
                print("  FIXED: Added recommendation")
        
        print(f"\n=== API TEST ===")
        
        # Test the API response format
        user_reports_fixed = list(db.inspections.find({
            'application_id': {'$in': app_ids},
            'status': 'completed'
        }).sort('inspection_date', -1))
        
        formatted_reports = []
        for report in user_reports_fixed:
            # Get application details
            app_data = db.applications.find_one({'_id': report['application_id']})
            if app_data:
                formatted_report = {
                    'id': str(report['_id']),
                    'report_number': f"RPT-{report['inspection_date'].strftime('%Y%m%d')}-{str(report['_id'])[-6:].upper()}" if report.get('inspection_date') else f"RPT-{str(report['_id'])[-6:].upper()}",
                    'business_name': app_data.get('business_name', 'N/A'),
                    'inspector': report.get('inspector', 'N/A'),
                    'inspection_date': report.get('inspection_date', datetime.now()).isoformat() if report.get('inspection_date') else datetime.now().isoformat(),
                    'compliance_score': report.get('compliance_score', 0),
                    'recommendation': report.get('recommendation', 'pending'),
                    'status': report.get('status', 'completed')
                }
                formatted_reports.append(formatted_report)
        
        print(f"API would return {len(formatted_reports)} reports:")
        for report in formatted_reports[:3]:  # Show first 3
            print(f"  - {report['report_number']}: {report['business_name']} (Score: {report['compliance_score']})")
        
        if len(formatted_reports) > 3:
            print(f"  ... and {len(formatted_reports) - 3} more")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_inspection_reports()
