from flask import Flask, render_template
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['aek_noc']
    applications = db['applications']
    certificates = db['certificates']
    inspections = db['inspections']
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def test_certificate():
    try:
        # Get a real application from database
        real_app = applications.find_one({'status': {'$in': ['approved', 'certificate_issued']}})

        if not real_app:
            # Create a real application if none exists
            real_app_data = {
                'username': 'real_user',
                'business_name': 'Shree Krishna Restaurant & Banquet Hall',
                'business_type': 'Hospitality',
                'business_address': 'Plot No. 15, Sector 21, Near ISCON Temple, Gandhinagar, Gujarat - 382021',
                'contact_person': 'Ramesh Patel',
                'contact_number': '+91-9876543210',
                'email': 'ramesh.patel@krishnarestaurant.com',
                'pan_number': 'BKPPP1234K',
                'building_area': '8500',
                'floors': '2',
                'max_occupancy': '250',
                'fire_extinguishers': '12',
                'fire_alarm': 'Yes - Installed',
                'emergency_exits': '6',
                'last_fire_drill': '2024-11-15',
                'sprinkler_system': 'Yes',
                'fire_safety_officer': 'Yes',
                'status': 'approved',
                'timestamp': datetime.now(),
                'documents_verified': True,
                'assigned_manager': 'manager1',
                'verification_score': 92,
                'approved_by': 'Fire Safety Manager',
                'approval_date': datetime.now()
            }

            app_result = applications.insert_one(real_app_data)
            real_app = applications.find_one({'_id': app_result.inserted_id})

        # Get or create certificate for this application
        certificate = certificates.find_one({'application_id': real_app['_id']})

        if not certificate:
            # Create certificate
            certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(real_app['_id'])[-6:]}"
            certificate_data = {
                'certificate_number': certificate_number,
                'application_id': real_app['_id'],
                'business_name': real_app.get('business_name'),
                'business_type': real_app.get('business_type'),
                'business_address': real_app.get('business_address'),
                'issued_date': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=365),
                'status': 'active',
                'issued_by': 'Fire Safety Department',
                'created_at': datetime.now()
            }
            certificates.insert_one(certificate_data)
            certificate = certificate_data

        # Get inspection data
        inspection = inspections.find_one({'application_id': real_app['_id']})
        if not inspection:
            # Create inspection record
            inspection_data = {
                'application_id': real_app['_id'],
                'inspector': 'Suresh Kumar',
                'status': 'completed',
                'compliance_score': 88,
                'date': datetime.now(),
                'findings': ['All fire safety equipment properly installed', 'Emergency exits clearly marked'],
                'recommendations': ['Monthly fire drill schedule to be maintained'],
                'completed_at': datetime.now()
            }
            inspections.insert_one(inspection_data)
            inspection = inspection_data
        # Render the certificate template with real data
        return render_template('certificate_template.html',
            certificate_number=certificate.get('certificate_number', f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(real_app['_id'])[-6:]}"),
            business_name=real_app.get('business_name', ''),
            business_type=real_app.get('business_type', ''),
            business_address=real_app.get('business_address', ''),
            pan_number=real_app.get('pan_number', 'Not Provided'),
            contact_person=real_app.get('contact_person', 'Business Owner'),
            contact_number=real_app.get('contact_number', 'Not Provided'),
            building_area=real_app.get('building_area', 'As per application'),
            floors=real_app.get('floors', 'As per plan'),
            max_occupancy=real_app.get('max_occupancy', 'As per norms'),
            fire_extinguishers=real_app.get('fire_extinguishers', 'As per norms'),
            fire_alarm=real_app.get('fire_alarm', 'Installed'),
            emergency_exits=real_app.get('emergency_exits', 'Adequate'),
            last_fire_drill=real_app.get('last_fire_drill', 'As required'),
            sprinkler_system=real_app.get('sprinkler_system', 'Not specified'),
            issue_date=certificate.get('issued_date', datetime.now()).strftime('%d/%m/%Y') if isinstance(certificate.get('issued_date'), datetime) else datetime.now().strftime('%d/%m/%Y'),
            valid_until=certificate.get('valid_until', datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y') if isinstance(certificate.get('valid_until'), datetime) else (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
            compliance_score=inspection.get('compliance_score', 88),
            inspector_name=inspection.get('inspector', 'System Inspector'),
            inspector_signature=f"Digitally Signed by {inspection.get('inspector', 'System Inspector')}",
            manager_signature=f"Digitally Signed by {certificate.get('issued_by', 'Manager')}",
            approved_by=certificate.get('issued_by', 'Fire Safety Manager')
        )

    except Exception as e:
        return f"Error loading certificate: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
