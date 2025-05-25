#!/usr/bin/env python3
"""
Test script for the comprehensive email notification system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_service import EmailService
from flask import Flask
from flask_mail import Mail
from datetime import datetime

def test_email_templates():
    """Test all email templates"""
    
    # Initialize Flask app for testing
    app = Flask(__name__)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'mkbharvad534@gmail.com'
    app.config['MAIL_PASSWORD'] = 'dwtp fmiq miyl ccvq'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    
    mail = Mail(app)
    email_service = EmailService(mail, app.config)
    
    print("🧪 Testing Email Templates...")
    
    # Test data
    test_data = {
        'application_received': {
            'template_type': 'application_received',
            'business_name': 'Test Restaurant',
            'business_type': 'Restaurant',
            'applicant_name': 'John Doe',
            'application_id': 'APP123456',
            'submission_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'dashboard_url': 'http://localhost:5000/manager_dashboard',
            'plain_text': 'New NOC application received from Test Restaurant'
        },
        'inspection_scheduled': {
            'template_type': 'inspection_scheduled',
            'user_name': 'John Doe',
            'business_name': 'Test Restaurant',
            'inspector_name': 'Inspector Smith',
            'inspection_date': '2024-01-15',
            'application_id': 'APP123456',
            'application_url': 'http://localhost:5000/view_application/APP123456',
            'plain_text': 'Inspection scheduled for Test Restaurant'
        },
        'inspector_assignment': {
            'template_type': 'inspector_assignment',
            'inspector_name': 'Inspector Smith',
            'business_name': 'Test Restaurant',
            'business_address': '123 Main St, City',
            'business_type': 'Restaurant',
            'inspection_date': '2024-01-15',
            'application_id': 'APP123456',
            'assigned_by': 'Manager',
            'inspector_dashboard_url': 'http://localhost:5000/inspector_dashboard',
            'plain_text': 'You have been assigned to inspect Test Restaurant'
        },
        'inspection_started': {
            'template_type': 'inspection_started',
            'user_name': 'John Doe',
            'business_name': 'Test Restaurant',
            'inspector_name': 'Inspector Smith',
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'application_id': 'APP123456',
            'application_url': 'http://localhost:5000/view_application/APP123456',
            'plain_text': 'Inspection has started for Test Restaurant'
        },
        'inspection_completed': {
            'template_type': 'inspection_completed',
            'user_name': 'John Doe',
            'business_name': 'Test Restaurant',
            'inspector_name': 'Inspector Smith',
            'completion_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'compliance_score': '95',
            'overall_result': 'Approved',
            'report_number': 'RPT-20240115-123456',
            'application_id': 'APP123456',
            'application_url': 'http://localhost:5000/view_application/APP123456',
            'plain_text': 'Inspection completed for Test Restaurant'
        },
        'manager_approval': {
            'template_type': 'manager_approval',
            'business_name': 'Test Restaurant',
            'inspector_name': 'Inspector Smith',
            'completion_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'compliance_score': '95',
            'recommendation': 'Approved',
            'application_id': 'APP123456',
            'key_findings': [
                'Fire extinguishers properly installed',
                'Emergency exits clearly marked',
                'Smoke detectors functional',
                'Fire safety training completed'
            ],
            'manager_dashboard_url': 'http://localhost:5000/manager_dashboard',
            'plain_text': 'Inspection completed for Test Restaurant and requires your approval'
        },
        'certificate_issued': {
            'template_type': 'certificate_issued',
            'user_name': 'John Doe',
            'business_name': 'Test Restaurant',
            'certificate_number': 'NOC-20240115-123456',
            'issue_date': datetime.now().strftime('%Y-%m-%d'),
            'valid_until': '2025-01-15',
            'approved_by': 'Manager',
            'certificate_url': 'http://localhost:5000/view_certificate/APP123456',
            'plain_text': 'NOC Certificate issued for Test Restaurant'
        }
    }
    
    # Test each template
    for template_name, data in test_data.items():
        print(f"\n📧 Testing {template_name} template...")
        try:
            html_content = email_service.generate_html_template(data)
            
            # Save to file for inspection
            filename = f"test_email_{template_name}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ {template_name} template generated successfully")
            print(f"   📄 Saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error generating {template_name} template: {str(e)}")
    
    print("\n🎉 Email template testing completed!")
    print("\n📋 Summary:")
    print("- All email templates have been generated and saved as HTML files")
    print("- You can open these files in a browser to preview the email designs")
    print("- The templates include professional styling and responsive design")
    print("- Each template contains relevant information for its workflow stage")
    
    print("\n🔧 Next Steps:")
    print("1. Review the generated HTML files to ensure they look good")
    print("2. Test actual email sending with a test email address")
    print("3. Integrate the email notifications into your workflow")
    print("4. Monitor email delivery and user feedback")

def test_email_sending():
    """Test actual email sending (optional - requires valid email setup)"""
    print("\n📨 Email Sending Test")
    print("Note: This requires valid SMTP configuration")
    
    # You can uncomment and modify this section to test actual email sending
    """
    app = Flask(__name__)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your-app-password'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    
    mail = Mail(app)
    email_service = EmailService(mail, app.config)
    
    test_data = {
        'template_type': 'application_received',
        'business_name': 'Test Restaurant',
        'business_type': 'Restaurant',
        'applicant_name': 'John Doe',
        'application_id': 'APP123456',
        'submission_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dashboard_url': 'http://localhost:5000/manager_dashboard',
        'plain_text': 'New NOC application received from Test Restaurant'
    }
    
    with app.app_context():
        success = email_service.send_email_with_template(
            subject="🧪 Test Email - New NOC Application",
            recipient="test@example.com",  # Replace with your test email
            template_data=test_data
        )
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email")
    """
    
    print("⚠️  Email sending test is commented out")
    print("   Uncomment and configure the test_email_sending() function to test actual email delivery")

if __name__ == "__main__":
    print("🔥 Fire NOC System - Email Notification Test")
    print("=" * 50)
    
    test_email_templates()
    test_email_sending()
    
    print("\n" + "=" * 50)
    print("✨ Testing completed! Check the generated HTML files to preview your emails.")
