from flask import Flask, render_template
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['aek_noc']

@app.route('/test-certificate/<application_id>')
def test_certificate(application_id):
    """Test the new certificate design"""
    try:
        # Get application data
        app_data = db.applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return f"Application not found: {application_id}", 404

        # Get certificate data
        certificate = db.certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return f"Certificate not found for application: {application_id}", 404

        # Prepare certificate data
        certificate_data = {
            'certificate_number': certificate.get('certificate_number', 'NOC-TEST-001'),
            'business_name': app_data.get('business_name', 'Test Business'),
            'business_type': app_data.get('business_type', 'Commercial'),
            'business_address': app_data.get('business_address', 'Test Address'),
            'pan_number': app_data.get('pan_number', 'ABCDE1234F'),
            'building_area': app_data.get('building_area', '1000'),
            'floors': app_data.get('floors', '2'),
            'fire_extinguishers': app_data.get('fire_extinguishers', '5'),
            'emergency_exits': app_data.get('emergency_exits', '2'),
            'fire_alarm': app_data.get('fire_alarm', 'Yes'),
            'last_fire_drill': app_data.get('last_fire_drill', '2024-01-15'),
            'compliance_score': app_data.get('compliance_score', '95'),
            'issue_date': certificate.get('issue_date', datetime.now().strftime('%Y-%m-%d')),
            'valid_until': certificate.get('valid_until', '2025-12-31'),
            'contact_person': app_data.get('contact_person', app_data.get('business_name', 'Business Owner')),
            'inspector_name': certificate.get('inspector_name', 'Fire Safety Inspector')
        }

        return render_template('certificate_template.html', **certificate_data)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    print("🔥 Starting Certificate Test Server...")
    print("📋 Available test URLs:")
    print("   http://localhost:5001/test-certificate/679a4b22cd7c04c2175b98ea")
    print("   http://localhost:5001/test-certificate/679a161315c8395aa6753352")
    app.run(debug=True, port=5001)
