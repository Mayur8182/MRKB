from flask import Flask, render_template_string, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>Fire NOC Certificate System</h1>
    <p><a href="/certificate">View Sample Certificate</a></p>
    <p><a href="/api/test">Test API</a></p>
    '''

@app.route('/certificate')
def certificate():
    try:
        # Read the certificate HTML file
        with open('certificate_demo.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading certificate: {str(e)}"

@app.route('/api/test')
def api_test():
    return jsonify({
        'status': 'success',
        'message': 'API is working',
        'certificate_url': '/certificate'
    })

@app.route('/api/application/<application_id>')
def get_application_data(application_id):
    """Mock API for application data"""
    return jsonify({
        'business_name': 'Tech Solutions Pvt Ltd',
        'contact_person': 'Rajesh Kumar',
        'contact_number': '+91-9876543210',
        'pan_number': 'ABCDE1234F',
        'business_type': 'IT Office',
        'business_address': 'Sector 10, Gandhinagar, Gujarat',
        'building_area': '5000',
        'floors': '3',
        'max_occupancy': '150',
        'fire_extinguishers': 'Available (15 units)',
        'fire_alarm': 'Installed & Functional',
        'emergency_exits': 'Adequate (6 exits)',
        'last_fire_drill': 'Last month',
        'status': 'approved',
        'certificate_number': 'NOC-2024-001234'
    })

@app.route('/api/certificate/<application_id>')
def get_certificate_data(application_id):
    """Mock API for certificate data"""
    return jsonify({
        'certificate_number': 'NOC-2024-001234',
        'business_name': 'Tech Solutions Pvt Ltd',
        'issue_date': '15/12/2024',
        'valid_until': '15/12/2025',
        'issued_by': 'MAYUR BHARVAD',
        'inspector_name': 'Inspector Priya Sharma',
        'inspection_date': '10/12/2024',
        'compliance_score': 92,
        'status': 'approved'
    })

@app.route('/api/inspection-report/<application_id>')
def get_inspection_report(application_id):
    """Mock API for inspection report data"""
    return jsonify({
        'inspector': 'Inspector Priya Sharma',
        'inspection_date': '10/12/2024',
        'compliance_score': 92,
        'fire_extinguishers': 'Available (15 units)',
        'fire_alarm': 'Installed & Functional',
        'emergency_exits': 'Adequate (6 exits)',
        'overall_result': 'Passed',
        'status': 'completed'
    })

if __name__ == '__main__':
    print("Starting simple Flask server...")
    print("Certificate demo available at: http://localhost:5001/certificate")
    print("API test available at: http://localhost:5001/api/test")
    app.run(debug=True, port=5001, host='0.0.0.0')
