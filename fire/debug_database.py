#!/usr/bin/env python3
"""
Debug script to check database structure and fix data issues
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json

def debug_database():
    """Debug the database structure"""
    
    print("Debugging database structure...")
    
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']
        
        print("\n=== INSPECTIONS COLLECTION ===")
        
        # Get all inspections
        inspections = list(db.inspections.find().limit(5))
        print(f"Total inspections: {db.inspections.count_documents({})}")
        print(f"Completed inspections: {db.inspections.count_documents({'status': 'completed'})}")
        
        if inspections:
            print("\nSample inspection records:")
            for i, inspection in enumerate(inspections):
                print(f"\nInspection {i+1}:")
                print(f"  _id: {inspection.get('_id')}")
                print(f"  application_id: {inspection.get('application_id')}")
                print(f"  inspector: {inspection.get('inspector')}")
                print(f"  inspector_id: {inspection.get('inspector_id')}")
                print(f"  status: {inspection.get('status')}")
                print(f"  date: {inspection.get('date')}")
                print(f"  inspection_date: {inspection.get('inspection_date')}")
                print(f"  Keys: {list(inspection.keys())}")
        
        print("\n=== APPLICATIONS COLLECTION ===")
        
        # Get applications with inspection data
        apps_with_inspection = list(db.applications.find({
            'inspection_report_id': {'$exists': True}
        }).limit(3))
        
        print(f"Applications with inspection_report_id: {len(apps_with_inspection)}")
        
        if apps_with_inspection:
            print("\nSample applications with inspection data:")
            for i, app in enumerate(apps_with_inspection):
                print(f"\nApplication {i+1}:")
                print(f"  _id: {app.get('_id')}")
                print(f"  business_name: {app.get('business_name')}")
                print(f"  status: {app.get('status')}")
                print(f"  assigned_manager: {app.get('assigned_manager')}")
                print(f"  assigned_inspector: {app.get('assigned_inspector')}")
                print(f"  inspection_report_id: {app.get('inspection_report_id')}")
        
        # Check for mismatched data
        print("\n=== DATA CONSISTENCY CHECK ===")
        
        # Find inspections with missing application_id
        missing_app_id = db.inspections.count_documents({
            'application_id': {'$in': [None, '']}
        })
        print(f"Inspections with missing application_id: {missing_app_id}")
        
        # Find inspections with missing inspector
        missing_inspector = db.inspections.count_documents({
            'inspector': {'$in': [None, '']}
        })
        print(f"Inspections with missing inspector: {missing_inspector}")
        
        client.close()
        
    except Exception as e:
        print(f"Error debugging database: {str(e)}")

def fix_inspection_data():
    """Fix inspection data by creating proper test data"""
    
    print("\n=== FIXING INSPECTION DATA ===")
    
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']
        
        # Clear existing problematic inspections
        result = db.inspections.delete_many({
            '$or': [
                {'application_id': None},
                {'inspector': None},
                {'application_id': ''},
                {'inspector': ''}
            ]
        })
        print(f"Deleted {result.deleted_count} problematic inspection records")
        
        # Get some applications to create proper inspection data
        applications = list(db.applications.find().limit(5))
        
        if applications:
            print(f"Creating proper inspection data for {len(applications)} applications...")
            
            for i, app in enumerate(applications):
                # Create a proper inspection record
                inspection_data = {
                    'application_id': app['_id'],
                    'inspector': 'inspector1',
                    'inspector_id': 'inspector1',
                    'inspection_date': datetime.now(),
                    'date': datetime.now(),
                    'status': 'completed',
                    'compliance_score': 85 + (i * 3),
                    'recommendation': 'approved',
                    'report_details': {
                        'fire_safety': 'Good',
                        'emergency_exits': 'Adequate',
                        'fire_extinguishers': 'Properly placed'
                    },
                    'findings': ['Fire safety equipment in good condition', 'Emergency exits clearly marked'],
                    'recommendations': ['Regular maintenance required', 'Monthly fire drills recommended'],
                    'overall_result': 'Passed',
                    'photos': [],
                    'created_at': datetime.now()
                }
                
                # Insert inspection
                result = db.inspections.insert_one(inspection_data)
                print(f"Created inspection {result.inserted_id} for {app.get('business_name')}")
                
                # Update application with inspection data
                db.applications.update_one(
                    {'_id': app['_id']},
                    {
                        '$set': {
                            'status': 'inspection_completed',
                            'inspection_report_id': result.inserted_id,
                            'assigned_manager': 'manager',
                            'assigned_inspector': 'inspector1',
                            'inspection_completed_at': datetime.now(),
                            'compliance_score': inspection_data['compliance_score'],
                            'inspector_recommendation': inspection_data['recommendation']
                        }
                    }
                )
        
        print("Inspection data fixed successfully!")
        
        client.close()
        
    except Exception as e:
        print(f"Error fixing inspection data: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE DEBUG AND FIX SCRIPT")
    print("=" * 60)
    
    debug_database()
    
    # Ask user if they want to fix the data
    print("\n" + "=" * 60)
    fix_data = input("Do you want to fix the inspection data? (y/n): ").lower().strip()
    
    if fix_data == 'y':
        fix_inspection_data()
        print("\nRunning debug again to verify fixes...")
        debug_database()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETED")
    print("=" * 60)
