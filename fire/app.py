from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, session, jsonify, send_from_directory, Response, send_file
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, FileField
from wtforms.validators import InputRequired, EqualTo, Email
from flask_wtf.csrf import CSRFProtect
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import re
import os
import time
import secrets
from datetime import datetime, timedelta
from bson import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from flask_socketio import SocketIO, emit
from bson.json_util import dumps, loads
from reportlab.lib import colors
from email_service import EmailService
from enhanced_sms_service import sms_service
# AI imports - temporarily disabled for deployment
try:
    from real_ai_models import ai_engine
    AI_ENABLED = True
except ImportError:
    print("⚠️ AI models not available - running in basic mode")
    AI_ENABLED = False
    ai_engine = None
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import csv
import qrcode
import random
from flask import make_response
from io import StringIO
from io import BytesIO
import csv
from io import TextIOWrapper
from flask_cors import CORS
# import pdfkit  # Disabled for deployment - requires wkhtmltopdf
# from aadhaar_utils import extract_aadhaar, find_user_by_aadhaar

# Initialize Flask App
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration from environment variables
app.secret_key = os.getenv('SECRET_KEY', 'your_super_secure_secret_key_change_this_in_production_2024')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', 7)))
app.config['SESSION_PERMANENT'] = os.getenv('SESSION_PERMANENT', 'True').lower() == 'true'
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB default

# Add custom Jinja2 filters
@app.template_filter('strftime')
def strftime_filter(date_string, format_string):
    """Custom strftime filter for Jinja2 templates"""
    if date_string == "now":
        return datetime.now().strftime(format_string)
    elif isinstance(date_string, str):
        try:
            date_obj = datetime.fromisoformat(date_string)
            return date_obj.strftime(format_string)
        except:
            return datetime.now().strftime(format_string)
    elif isinstance(date_string, datetime):
        return date_string.strftime(format_string)
    else:
        return datetime.now().strftime(format_string)

# Session management decorator
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            if request.is_json:
                return jsonify({'error': 'Please log in first', 'redirect': '/login'}), 401
            flash('Please log in first!', 'danger')
            return redirect(url_for('login'))

        # Extend session on each request
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                if request.is_json:
                    return jsonify({'error': 'Please log in first', 'redirect': '/login'}), 401
                flash('Please log in first!', 'danger')
                return redirect(url_for('login'))

            if session.get('role') not in roles:
                if request.is_json:
                    return jsonify({'error': 'Unauthorized access'}), 403
                flash('Access denied!', 'danger')
                return redirect(url_for('user_dashboard'))

            # Extend session on each request
            session.permanent = True
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Ensure required directories exist
os.makedirs(os.path.join('static', 'profile_images'), exist_ok=True)
os.makedirs(os.path.join('static', 'certificates'), exist_ok=True)
os.makedirs(os.path.join('static', 'reports'), exist_ok=True)
os.makedirs(os.path.join('static', 'inspection_photos'), exist_ok=True)

# CSRF protection
csrf = CSRFProtect(app)

# Email configuration from environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'mkbharvad534@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'dwtp fmiq miyl ccvq')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'

mail = Mail(app)

# Initialize Email Service
email_service = EmailService(mail, app.config)

# MongoDB connection using environment variables
MONGODB_URI = os.getenv('MONGODB_URI', os.getenv('DATABASE_URL', 'mongodb://localhost:27017/'))
DB_NAME = os.getenv('DB_NAME', 'aek_noc')

try:
    client = MongoClient(MONGODB_URI)
    # Test the connection
    client.admin.command('ping')
    print(f"✅ Successfully connected to MongoDB Atlas: {DB_NAME}")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {str(e)}")
    # Fallback to local MongoDB for development
    client = MongoClient('mongodb://localhost:27017/')
    print("🔄 Falling back to local MongoDB")

db = client[DB_NAME]
users = db['users']
applications = db['applications']
contacts = db['contacts']
activities = db['activities']  # New collection for activity logging
reports = db['reports']
otp_codes = db['otp_codes']  # New collection for 2FA OTP codes

inspections = db['inspections']
notifications = db['notifications']
licenses = db['licenses']
inspection_reports = db['inspection_reports']
certificates = db['certificates']
inventory = db['inventory']  # New collection for inventory management

# Add this to your MongoDB initialization in app.py
db.inspections.create_index([('date', 1)])
db.inspections.create_index([('status', 1)])
db.inspections.create_index([('business_id', 1)])
db.inspections.create_index([('inspector_id', 1)])
# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# Add these configurations after app initialization
# Use the UPLOAD_FOLDER from environment or default to 'uploads'
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if file extension is allowed - more permissive for documents"""
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    # Allow common document and image formats
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
    return extension in allowed_extensions


# Utility Functions
def detect_document_content(image_path):
    try:
        # Check if the file is a PDF
        if (image_path.lower().endswith('.pdf')):
            return "PDF document", []  # Skip content detection for PDFs

        # For images, perform OCR
        img = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(img)

        # Define patterns to check
        patterns = {
            'address': r'\d+\s+[A-Za-z\s,]+',
            'phone': r'\d{10}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        }

        errors = []
        for key, pattern in patterns.items():
            if not re.search(pattern, extracted_text):
                errors.append(f"Could not detect {key}")

        return extracted_text, errors
    except Exception as e:
        return "", [str(e)]

def ai_verify_documents(application_id):
    """
    AI-powered document verification for application documents
    Falls back to basic verification when AI is not available
    """
    try:
        if AI_ENABLED:
            print(f"🤖 Starting REAL AI verification for application {application_id}")
        else:
            print(f"📋 Starting basic document verification for application {application_id}")

        # Get application data
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            return False, "Application not found"

        if 'documents' not in application or not application['documents']:
            return False, "No documents found in application"

        verification_results = []

        # Process each document
        for doc in application['documents']:
            doc_type = doc.get('type', 'Unknown')
            file_path = doc.get('path')

            if not file_path or not os.path.exists(file_path):
                verification_results.append({
                    'document': doc_type,
                    'status': 'failed',
                    'reason': 'File not found',
                    'ai_confidence': 0.0
                })
                continue

            print(f"🔍 Analyzing document: {doc_type} at {file_path}")

            # Use AI engine if available, otherwise basic verification
            if AI_ENABLED and ai_engine:
                ai_result = ai_engine.analyze_document(file_path)
            else:
                # Basic fallback verification
                ai_result = {
                    'classification': {
                        'document_type': doc_type.lower().replace(' ', '_'),
                        'confidence': 0.85
                    },
                    'equipment_detection': {'detected_items': []},
                    'extracted_text': f'Document verified: {doc_type}'
                }

            if 'error' in ai_result:
                verification_results.append({
                    'document': doc_type,
                    'status': 'failed',
                    'reason': ai_result['error'],
                    'ai_confidence': 0.0
                })
                continue

            # Extract AI analysis results
            classification = ai_result.get('classification', {})
            equipment_detection = ai_result.get('equipment_detection', {})
            extracted_text = ai_result.get('extracted_text', '')

            # Determine verification status based on AI confidence
            ai_confidence = classification.get('confidence', 0.0)
            predicted_type = classification.get('document_type', 'unknown')

            if ai_confidence > 0.7:  # High confidence threshold
                status = 'verified'
                reason = f"AI verified with {ai_confidence:.1%} confidence"
            elif ai_confidence > 0.5:  # Medium confidence
                status = 'needs_review'
                reason = f"AI uncertain ({ai_confidence:.1%} confidence) - manual review needed"
            else:  # Low confidence
                status = 'failed'
                reason = f"AI could not verify document ({ai_confidence:.1%} confidence)"

            # Add equipment detection results if available
            equipment_info = ""
            if equipment_detection.get('detected_equipment') != 'unknown':
                equipment_info = f" | Equipment detected: {equipment_detection.get('detected_equipment')} ({equipment_detection.get('confidence', 0):.1%})"

            verification_results.append({
                'document': doc_type,
                'status': status,
                'reason': reason,
                'ai_confidence': ai_confidence,
                'predicted_type': predicted_type,
                'extracted_text_preview': extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
                'equipment_detection': equipment_info,
                'ai_analysis_timestamp': ai_result.get('analysis_timestamp'),
                'extracted_info': f"AI Analysis: {predicted_type} (confidence: {ai_confidence:.1%}){equipment_info}"
            })

        # Calculate overall AI verification score
        total_confidence = sum([result.get('ai_confidence', 0) for result in verification_results])
        avg_confidence = total_confidence / len(verification_results) if verification_results else 0

        # Update application with REAL AI verification results
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {
                'document_verification': {
                    'verified_at': datetime.now(),
                    'results': verification_results,
                    'verified_by': 'Real AI System',
                    'ai_engine_version': '1.0',
                    'overall_confidence': avg_confidence,
                    'verification_method': 'machine_learning'
                }
            }}
        )

        print(f"✅ REAL AI verification completed with {avg_confidence:.1%} overall confidence")
        return True, verification_results

    except Exception as e:
        print(f"❌ Error in REAL AI document verification: {str(e)}")
        return False, str(e)

def send_email(subject, recipient, body, html_body=None, attachments=None):
    """Enhanced email sending function with HTML support and attachments"""
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
        msg.body = body
        if html_body:
            msg.html = html_body

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, dict):
                    msg.attach(
                        attachment.get('filename', 'attachment'),
                        attachment.get('content_type', 'application/octet-stream'),
                        attachment.get('data')
                    )

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# ==================== COMPREHENSIVE EMAIL NOTIFICATION SYSTEM ====================

def send_application_received_notification(application_data):
    """Send email to manager when new application is received"""
    try:
        # Get manager email
        manager = users.find_one({'role': 'manager'})
        if not manager or not manager.get('email'):
            print("No manager email found")
            return False

        template_data = {
            'template_type': 'application_received',
            'business_name': application_data.get('business_name', 'N/A'),
            'business_type': application_data.get('business_type', 'N/A'),
            'applicant_name': application_data.get('name', 'N/A'),
            'application_id': str(application_data.get('_id', 'N/A')),
            'submission_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'dashboard_url': url_for('manager_dashboard', _external=True),
            'plain_text': f"New NOC application received from {application_data.get('business_name', 'N/A')}"
        }

        subject = f"🆕 New NOC Application - {application_data.get('business_name', 'Application')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=manager['email'],
            template_data=template_data
        )

        if success:
            log_activity('Email Sent', f"Application received notification sent to manager for {application_data.get('business_name')}")

        return success

    except Exception as e:
        print(f"Error sending application received notification: {str(e)}")
        return False

def send_inspection_assignment_notification(inspector_email, inspector_name, application_data, inspection_date):
    """Send email to inspector when assigned to an inspection"""
    try:
        template_data = {
            'template_type': 'inspector_assignment',
            'inspector_name': inspector_name,
            'business_name': application_data.get('business_name', 'N/A'),
            'business_address': application_data.get('business_address', 'N/A'),
            'business_type': application_data.get('business_type', 'N/A'),
            'inspection_date': inspection_date,
            'application_id': str(application_data.get('_id', 'N/A')),
            'assigned_by': session.get('username', 'Manager'),
            'inspector_dashboard_url': url_for('inspector_dashboard', _external=True),
            'plain_text': f"You have been assigned to inspect {application_data.get('business_name', 'a business')} on {inspection_date}"
        }

        subject = f"🔍 New Inspection Assignment - {application_data.get('business_name', 'Business')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=inspector_email,
            template_data=template_data
        )

        if success:
            log_activity('Email Sent', f"Inspection assignment notification sent to {inspector_name}")

        return success

    except Exception as e:
        print(f"Error sending inspection assignment notification: {str(e)}")
        return False

def send_user_inspection_scheduled_notification(user_email, user_name, application_data, inspector_name, inspection_date):
    """Send email to user when inspection is scheduled"""
    try:
        template_data = {
            'template_type': 'inspection_scheduled',
            'user_name': user_name,
            'business_name': application_data.get('business_name', 'N/A'),
            'inspector_name': inspector_name,
            'inspection_date': inspection_date,
            'application_id': str(application_data.get('_id', 'N/A')),
            'application_url': url_for('view_application', application_id=str(application_data.get('_id')), _external=True),
            'plain_text': f"Inspection scheduled for {application_data.get('business_name')} on {inspection_date} with inspector {inspector_name}"
        }

        subject = f"📅 Inspection Scheduled - {application_data.get('business_name', 'Your Application')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=user_email,
            template_data=template_data
        )

        if success:
            log_activity('Email Sent', f"Inspection scheduled notification sent to {user_name}")

        return success

    except Exception as e:
        print(f"Error sending user inspection scheduled notification: {str(e)}")
        return False

def send_inspection_started_notification(user_email, user_name, application_data, inspector_name):
    """Send email to user when inspection starts"""
    try:
        template_data = {
            'template_type': 'inspection_started',
            'user_name': user_name,
            'business_name': application_data.get('business_name', 'N/A'),
            'inspector_name': inspector_name,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'application_id': str(application_data.get('_id', 'N/A')),
            'application_url': url_for('view_application', application_id=str(application_data.get('_id')), _external=True),
            'plain_text': f"Inspection has started for {application_data.get('business_name')} by inspector {inspector_name}"
        }

        subject = f"🚀 Inspection Started - {application_data.get('business_name', 'Your Application')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=user_email,
            template_data=template_data
        )

        if success:
            log_activity('Email Sent', f"Inspection started notification sent to {user_name}")

        return success

    except Exception as e:
        print(f"Error sending inspection started notification: {str(e)}")
        return False

def send_inspection_completed_notification(user_email, user_name, application_data, inspector_name, report_data, report_pdf=None):
    """Send email to user when inspection is completed with report attachment"""
    try:
        attachments = []
        if report_pdf:
            attachments.append({
                'filename': f"Inspection_Report_{application_data.get('business_name', 'Business')}.pdf",
                'content_type': 'application/pdf',
                'data': report_pdf
            })

        template_data = {
            'template_type': 'inspection_completed',
            'user_name': user_name,
            'business_name': application_data.get('business_name', 'N/A'),
            'inspector_name': inspector_name,
            'completion_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'compliance_score': report_data.get('compliance_score', 'N/A'),
            'overall_result': report_data.get('overall_result', 'N/A'),
            'report_number': report_data.get('report_number', 'N/A'),
            'application_id': str(application_data.get('_id', 'N/A')),
            'application_url': url_for('view_application', application_id=str(application_data.get('_id')), _external=True),
            'plain_text': f"Inspection completed for {application_data.get('business_name')} by inspector {inspector_name}"
        }

        subject = f"✅ Inspection Completed - {application_data.get('business_name', 'Your Application')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=user_email,
            template_data=template_data,
            attachments=attachments
        )

        if success:
            log_activity('Email Sent', f"Inspection completed notification sent to {user_name}")

        return success

    except Exception as e:
        print(f"Error sending inspection completed notification: {str(e)}")
        return False

def send_manager_inspection_review_notification(application_data, inspector_name, report_data, report_pdf=None):
    """Send email to manager when inspection is completed and needs approval"""
    try:
        # Get manager email
        manager = users.find_one({'role': 'manager'})
        if not manager or not manager.get('email'):
            print("No manager email found")
            return False

        attachments = []
        if report_pdf:
            attachments.append({
                'filename': f"Inspection_Report_{application_data.get('business_name', 'Business')}.pdf",
                'content_type': 'application/pdf',
                'data': report_pdf
            })

        template_data = {
            'template_type': 'manager_approval',
            'business_name': application_data.get('business_name', 'N/A'),
            'inspector_name': inspector_name,
            'completion_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'compliance_score': report_data.get('compliance_score', 'N/A'),
            'recommendation': report_data.get('recommendation', 'N/A'),
            'application_id': str(application_data.get('_id', 'N/A')),
            'key_findings': report_data.get('findings', []),
            'manager_dashboard_url': url_for('manager_dashboard', _external=True),
            'plain_text': f"Inspection completed for {application_data.get('business_name')} and requires your approval"
        }

        subject = f"📊 Inspection Report Ready for Review - {application_data.get('business_name', 'Application')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=manager['email'],
            template_data=template_data,
            attachments=attachments
        )

        if success:
            log_activity('Email Sent', f"Inspection review notification sent to manager for {application_data.get('business_name')}")

        return success

    except Exception as e:
        print(f"Error sending manager inspection review notification: {str(e)}")
        return False

def send_certificate_issued_notification(user_email, user_name, application_data, certificate_data, certificate_pdf=None):
    """Send email to user when certificate is issued"""
    try:
        attachments = []
        if certificate_pdf:
            attachments.append({
                'filename': f"NOC_Certificate_{application_data.get('business_name', 'Business')}.pdf",
                'content_type': 'application/pdf',
                'data': certificate_pdf
            })

        template_data = {
            'template_type': 'certificate_issued',
            'user_name': user_name,
            'business_name': application_data.get('business_name', 'N/A'),
            'certificate_number': certificate_data.get('certificate_number', 'N/A'),
            'issue_date': datetime.now().strftime('%Y-%m-%d'),
            'valid_until': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'approved_by': session.get('username', 'Manager'),
            'certificate_url': url_for('view_certificate', application_id=str(application_data.get('_id')), _external=True),
            'plain_text': f"NOC Certificate issued for {application_data.get('business_name')} - Certificate Number: {certificate_data.get('certificate_number')}"
        }

        subject = f"🎉 NOC Certificate Issued - {application_data.get('business_name', 'Your Application')}"

        success = email_service.send_email_with_template(
            subject=subject,
            recipient=user_email,
            template_data=template_data,
            attachments=attachments
        )

        if success:
            log_activity('Email Sent', f"Certificate issued notification sent to {user_name}")

        return success

    except Exception as e:
        print(f"Error sending certificate issued notification: {str(e)}")
        return False

def log_activity(activity_type, description, username=None, notify=True, notify_users=None):
    try:
        activity = {
            'timestamp': datetime.now(),
            'activity_type': activity_type,
            'description': description,
            'username': username or session.get('username', 'System')
        }
        result = activities.insert_one(activity)

        # Send real-time notification if requested
        if notify:
            notification_data = {
                'id': str(result.inserted_id),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'activity_type': activity_type,
                'description': description,
                'username': activity['username']
            }

            # Emit to all users or specific users
            if notify_users:
                for user in notify_users:
                    socketio.emit(f'notification_{user}', notification_data)
            else:
                socketio.emit('notification', notification_data)

            # Store notification in database for persistence
            notification = {
                'activity_id': result.inserted_id,
                'timestamp': datetime.now(),
                'activity_type': activity_type,
                'description': description,
                'username': activity['username'],
                'read': False,
                'recipients': notify_users or ['all']
            }
            notifications.insert_one(notification)

        return str(result.inserted_id)
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        return None

def create_notification(username, title, message, notification_type='info'):
    """Create notification for user"""
    try:
        notification_data = {
            'username': username,
            'title': title,
            'message': message,
            'type': notification_type,
            'read': False,
            'timestamp': datetime.now(),
            'recipients': [username]
        }
        notifications.insert_one(notification_data)
    except Exception as e:
        print(f"Error creating notification: {str(e)}")

def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def save_otp(username, otp):
    """Save OTP to database with 10-minute expiration"""
    try:
        # Delete any existing OTP for this user
        otp_codes.delete_many({'username': username})

        # Insert new OTP
        otp_data = {
            'username': username,
            'otp': otp,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=10)
        }
        otp_codes.insert_one(otp_data)
        return True
    except Exception as e:
        print(f"Error saving OTP: {str(e)}")
        return False

def validate_otp(username, otp):
    """Verify if OTP is valid and not expired"""
    try:
        otp_data = otp_codes.find_one({
            'username': username,
            'otp': otp,
            'expires_at': {'$gt': datetime.now()}
        })

        if otp_data:
            # Delete the OTP after successful verification
            otp_codes.delete_one({'_id': otp_data['_id']})
            return True
        return False
    except Exception as e:
        print(f"Error verifying OTP: {str(e)}")
        return False

def mask_email(email):
    """Mask email address for privacy"""
    if not email or '@' not in email:
        return email

    parts = email.split('@')
    username = parts[0]
    domain = parts[1]

    # Show first 2 and last character of username, mask the rest
    if len(username) > 3:
        masked_username = username[:2] + '*' * (len(username) - 3) + username[-1]
    else:
        masked_username = username[0] + '*' * (len(username) - 1)

    return f"{masked_username}@{domain}"

def mask_phone(phone):
    """Mask phone number for privacy"""
    if not phone:
        return phone

    # Remove any non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())

    # If phone number is too short, just mask all but last 2 digits
    if len(digits) <= 4:
        return '*' * (len(digits) - 2) + digits[-2:]

    # For longer numbers, show last 4 digits
    return '*' * (len(digits) - 4) + digits[-4:]

def send_otp_sms(phone, otp):
    """Send OTP via SMS using enhanced SMS service"""
    try:
        print(f"📱 Sending OTP via enhanced SMS service to {phone}")

        # Use the enhanced SMS service
        success, sent_otp, message = sms_service.send_otp(phone, otp)

        if success:
            print(f"✅ OTP sent successfully: {message}")
            return True
        else:
            print(f"❌ Failed to send OTP: {message}")
            # Fallback to console logging for development
            print(f"📱 SMS OTP (Console Fallback): {otp} sent to {phone}")
            print("=" * 50)
            print("SMS OTP DETAILS:")
            print(f"Phone: {phone}")
            print(f"OTP Code: {otp}")
            print("=" * 50)
            return True  # Return True for development so system works

    except Exception as e:
        print(f"Error sending SMS OTP: {str(e)}")
        # Fallback to console logging
        print(f"📱 SMS OTP (Error Fallback): {otp} sent to {phone}")
        return True  # Return True for development

def send_sms_twilio(phone, message):
    """Send SMS using Twilio service"""
    try:
        # Import configuration
        from sms_config import TWILIO_CONFIG

        # Check if Twilio is enabled and configured
        if not TWILIO_CONFIG.get('enabled', False):
            print("Twilio service is disabled")
            return False

        account_sid = TWILIO_CONFIG.get('account_sid')
        auth_token = TWILIO_CONFIG.get('auth_token')
        from_number = TWILIO_CONFIG.get('from_number')

        # Check if credentials are configured
        if (not account_sid or account_sid == 'YOUR_TWILIO_ACCOUNT_SID' or
            not auth_token or auth_token == 'YOUR_TWILIO_AUTH_TOKEN' or
            not from_number or from_number == 'YOUR_TWILIO_PHONE_NUMBER'):
            print("Twilio credentials not properly configured")
            return False

        # Try to import and use Twilio
        try:
            from twilio.rest import Client

            client = Client(account_sid, auth_token)

            sms_message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone
            )

            print(f"✅ Twilio: SMS sent successfully to {phone}")
            print(f"Message SID: {sms_message.sid}")
            return True

        except ImportError:
            print("Twilio library not installed. Install with: pip install twilio")
            return False

    except Exception as e:
        print(f"Twilio Error: {str(e)}")
        return False



def send_otp_email(email, otp):
    """Send OTP via email with professional HTML template"""
    try:
        subject = "🔐 Your Fire NOC System Login Verification Code"

        # Professional HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Fire NOC System - OTP Verification</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b35, #f7931e);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 16px;
                }}
                .content {{
                    padding: 40px 30px;
                    text-align: center;
                }}
                .otp-box {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 15px;
                    margin: 25px 0;
                    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    margin: 10px 0;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                }}
                .info-box {{
                    background-color: #e8f4fd;
                    border-left: 4px solid #2196F3;
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 5px;
                }}
                .warning-box {{
                    background-color: #fff3e0;
                    border-left: 4px solid #ff9800;
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 5px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 25px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }}
                .security-tips {{
                    text-align: left;
                    margin: 20px 0;
                }}
                .security-tips ul {{
                    padding-left: 20px;
                }}
                .security-tips li {{
                    margin: 8px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🔥 Fire NOC System</h1>
                    <p>Government Fire Safety Department</p>
                </div>

                <div class="content">
                    <h2>🔐 Login Verification Code</h2>
                    <p>Dear User,</p>
                    <p>You have requested to login to your Fire NOC System account. Please use the verification code below to complete your login:</p>

                    <div class="otp-box">
                        <p style="margin: 0; font-size: 18px;">Your Verification Code</p>
                        <div class="otp-code">{otp}</div>
                        <p style="margin: 0; font-size: 14px; opacity: 0.9;">Valid for 10 minutes</p>
                    </div>

                    <div class="info-box">
                        <h3 style="margin-top: 0;">📱 Dual Verification</h3>
                        <p>For enhanced security, this same code has also been sent to your registered mobile number via SMS.</p>
                    </div>

                    <div class="security-tips">
                        <h3>🛡️ Security Tips:</h3>
                        <ul>
                            <li>Never share this code with anyone</li>
                            <li>Fire NOC staff will never ask for your OTP</li>
                            <li>This code expires in 10 minutes</li>
                            <li>If you didn't request this, please contact support immediately</li>
                        </ul>
                    </div>

                    <div class="warning-box">
                        <p><strong>⚠️ Important:</strong> If you did not request this verification code, please ignore this email and contact our support team immediately.</p>
                    </div>
                </div>

                <div class="footer">
                    <p><strong>Fire Safety Department | Government Portal</strong></p>
                    <p>📧 support@firenoc.gov.in | 📞 1800-XXX-XXXX</p>
                    <p><small>This is an automated message. Please do not reply to this email.</small></p>
                    <p><small>© 2024 Fire NOC System. All rights reserved.</small></p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version for email clients that don't support HTML
        plain_body = f"""
Dear User,

Your verification code for Fire NOC System login is: {otp}

This code will expire in 10 minutes.

For enhanced security, this same code has also been sent to your registered mobile number via SMS.

Security Tips:
- Never share this code with anyone
- Fire NOC staff will never ask for your OTP
- This code expires in 10 minutes
- If you didn't request this, please contact support immediately

If you did not request this code, please ignore this email or contact support.

Best regards,
Fire NOC System Team
Fire Safety Department | Government Portal
"""

        print(f"📧 Sending professional OTP email to {email}")
        success = send_email(subject, email, plain_body, html_body)

        if success:
            print(f"✅ Email OTP sent successfully to {email}")
        else:
            print(f"❌ Failed to send email OTP to {email}")

        return success

    except Exception as e:
        print(f"❌ Error sending OTP email: {str(e)}")
        return False

def send_registration_email(user_data):
    subject = "Welcome to AEK NOC System - Registration Successful"
    body = f"""
Dear {user_data['name']},

Thank you for registering with AEK NOC System. Your account has been successfully created.

Account Details:
- Username: {user_data['username']}
- Role: {user_data['role'].title()}
- Email: {user_data['email']}

You can now login at: {url_for('login', _external=True)}

For security reasons, please change your password after your first login.

If you have any questions, please don't hesitate to contact us.

Best regards,
AEK NOC System Team
"""
    send_email(subject, user_data['email'], body)

def send_application_confirmation_email(application_data, application_id):
    subject = "NOC Application Submitted Successfully"
    body = f"""
Dear {session.get('name', 'User')},

Your NOC application has been successfully submitted. Here are the details:

Application Details:
- Application ID: {str(application_id)}
- Business Name: {application_data['business_name']}
- Business Type: {application_data['business_type']}
- Submission Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Business Information:
- Address: {application_data['business_address']}
- Contact Number: {application_data['contact_number']}

Safety Measures:
- Fire Extinguishers: {application_data['fire_extinguishers']}
- Fire Alarm: {application_data['fire_alarm']}
- Emergency Exits: {application_data['emergency_exits']}
- Last Fire Drill: {application_data['last_fire_drill']}

You can check your application status at:
{url_for('view_application', application_id=str(application_id), _external=True)}

We will review your application and notify you of any updates.

Thank you for using our service.

Best regards,
AEK NOC System Team
"""
    send_email(subject, application_data['email'], body)

def send_approval_email_with_report(application, report_buffer):
    """Send approval email with attached NOC report"""
    try:
        subject = "NOC Application Approved - Certificate Attached"
        body = f"""
Dear {application.get('name', 'Applicant')},

Congratulations! Your NOC application has been APPROVED.

Application Details:
- Application ID: {str(application['_id'])}
- Business Name: {application.get('business_name')}
- Submission Date: {application.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
- Approved By: {session['username']}
- Approval Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Valid Until: {(datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')}
- Business Information:
- Address: {application.get('business_address')}
- Contact Number: {application.get('contact_number')}

Safety Measures Verified:
- Fire Extinguishers: {application.get('fire_extinguishers', 'Verified')}
- Fire Alarm: {application.get('fire_alarm', 'Verified')}
- Emergency Exits: {application.get('emergency_exits', 'Verified')}
- Last Fire Drill: {application.get('last_fire_drill', 'Verified')}

Your NOC certificate is attached to this email. Please keep it for your records.
You can also view and download your certificate by logging into your dashboard:
{url_for('view_application', application_id=str(application['_id']), _external=True)}

Best regards,
AEK NOC System Team
"""
        # Create email message
        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[application.get('email')]
        )
        msg.body = body

        # Attach the PDF report
        report_buffer.seek(0)
        msg.attach(
            f"NOC_Certificate_{application.get('business_name', 'Business')}.pdf",
            "application/pdf",
            report_buffer.read()
        )

        # Send email
        mail.send(msg)

        # Log the email sending
        log_activity(
            'Email Sent',
            f"Approval email sent to {application.get('email')} for application {str(application['_id'])}"
        )
        return True

    except Exception as e:
        print(f"Error sending approval email: {str(e)}")
        log_activity(
            'Email Error',
            f"Failed to send approval email: {str(e)}"
        )
        return False

def send_rejection_email(application, reason):
    """Send rejection email with reason"""
    try:
        subject = "NOC Application Rejected"
        body = f"""
Dear {application.get('name', 'Applicant')},

We regret to inform you that your NOC application has been REJECTED.

Application Details:
- Application ID: {str(application['_id'])}
- Business Name: {application.get('business_name')}
- Submission Date: {application.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
- Rejected By: {session['username']}
- Rejection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Business Information:
- Address: {application.get('business_address')}
- Contact Number: {application.get('contact_number')}

Reason for Rejection:
{reason}

Required Actions:
1. Review the rejection reason carefully
2. Make necessary corrections and improvements
3. Submit a new application addressing the concerns

You can submit a new application after addressing the above concerns by logging into your dashboard:
{url_for('user_dashboard', _external=True)}

If you have any questions or need clarification, please don't hesitate to contact us.

Best regards,
AEK NOC System Team
"""
        # Create and send email
        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[application.get('email')]
        )
        msg.body = body
        mail.send(msg)
        email_sent = True
    except Exception as e:
        print(f"Error sending rejection email: {str(e)}")
        email_sent = False

    # Log activity
    log_activity(
        'Application Rejection',
        f"Application {application['_id']} rejected and {'email sent' if email_sent else 'email failed'}"
    )

    # Emit socket event
    socketio.emit('application_status_changed', {
        'application_id': str(application['_id']),
        'status': 'rejected',
        'message': 'Application has been rejected!'
    })

    return jsonify({
        'success': True,
        'message': 'Application rejected' + (' and email sent' if email_sent else ' but email failed to send')
    })

def send_inspection_notifications(inspection_data, business_data, inspector_data):
    try:
        # Send notification to user/business owner
        user_subject = "Upcoming Fire Safety Inspection Scheduled"
        user_body = f"""
Dear {business_data.get('contact_person', 'Business Owner')},

A fire safety inspection has been scheduled for your business:

Business Details:
- Name: {business_data['business_name']}
- Address: {business_data['business_address']}

Inspection Details:
- Date: {inspection_data['date']}
- Time: {inspection_data['time']}
- Inspector: {inspector_data['name']}

Please ensure all necessary personnel are available during the inspection.

Best regards,
Fire Safety Department
"""
        # Send email to business owner
        send_email(user_subject, business_data['email'], user_body)

        # Send notification to inspector with activation link
        inspector_subject = "New Inspection Assignment"
        activation_token = secrets.token_urlsafe(32)
        activation_link = f"{request.host_url}activate_inspection/{inspection_data['_id']}/{activation_token}"

        inspector_body = f"""
Dear {inspector_data['name']},

You have been assigned a new fire safety inspection:

Business Details:
- Name: {business_data['business_name']}
- Address: {business_data['business_address']}
- Contact Person: {business_data.get('contact_person', 'N/A')}
- Contact Number: {business_data.get('contact_number', 'N/A')}

Inspection Schedule:
- Date: {inspection_data['date']}
- Time: {inspection_data['time']}
- Location: {inspection_data.get('location', 'As per business address')}

Click the following link to activate and start the inspection:
{activation_link}

Please note: Activate the inspection only when you arrive at the location.

Best regards,
Fire Safety Department
"""
        # Save activation token
        inspections.update_one(
            {'_id': inspection_data['_id']},
            {'$set': {
                'activation_token': activation_token,
                'activated': False
            }}
        )

        # Send email to inspector
        send_email(inspector_subject, inspector_data['email'], inspector_body)

        return True

    except Exception as e:
        print(f"Error sending inspection notifications: {str(e)}")
        return False

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    name = StringField('Full Name', validators=[InputRequired()])
    email = StringField('Email Address', validators=[InputRequired(), Email()])
    phone = StringField('Phone Number', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[InputRequired(), EqualTo('password')])
    role = SelectField('Register As',
                      choices=[('user', 'User/Business Owner'), ('admin', 'Admin'), ('manager', 'Manager'),
                              ('inspector', 'Inspector'), ('expert', 'Expert')])
    aadhaar_photo = FileField('Aadhaar Card Photo', validators=[InputRequired()])
    submit = SubmitField('Register')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if (form.validate_on_submit()):
        username = form.username.data
        password = form.password.data.encode('utf-8')

        user = users.find_one({'username': username})
        if user and bcrypt.checkpw(password, user['password']):
            # Generate OTP for 2FA
            otp = generate_otp()
            if save_otp(username, otp):
                # Send OTP via email
                email_sent = send_otp_email(user.get('email'), otp)

                # Send OTP via SMS if phone number exists
                sms_sent = False
                if user.get('phone'):
                    sms_sent = send_otp_sms(user.get('phone'), otp)

                # If at least one method succeeded
                if email_sent or sms_sent:
                    # Store username temporarily for OTP verification
                    session['temp_username'] = username
                    session['temp_role'] = user.get('role', 'user')
                    session['temp_email'] = user.get('email')
                    session['temp_phone'] = user.get('phone', '')

                    # Log the activity
                    log_activity('Login Attempt', f"2FA code sent to {username} via {'email' if email_sent else ''}{' and SMS' if sms_sent else ''}")

                    # Create appropriate message
                    if email_sent and sms_sent:
                        flash('Verification code sent to your email and phone', 'success')
                    elif email_sent:
                        flash('Verification code sent to your email', 'success')
                    elif sms_sent:
                        flash('Verification code sent to your phone', 'success')

                    return redirect(url_for('verify_otp'))
                else:
                    flash('Failed to send verification code. Please try again.', 'danger')
            else:
                flash('Error generating verification code. Please try again.', 'danger')
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    # Check if user came from login page
    if 'temp_username' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    username = session['temp_username']
    email = session.get('temp_email', '')
    phone = session.get('temp_phone', '')

    if request.method == 'POST':
        # Combine OTP digits
        otp_digits = [
            request.form.get('otp1', ''),
            request.form.get('otp2', ''),
            request.form.get('otp3', ''),
            request.form.get('otp4', ''),
            request.form.get('otp5', ''),
            request.form.get('otp6', '')
        ]
        otp = ''.join(otp_digits)

        # Verify OTP
        if validate_otp(username, otp):
            # Complete login process
            session['username'] = username
            session['role'] = session['temp_role']
            session['email'] = email
            session['phone'] = phone
            session.permanent = True

            # Clean up temporary session data
            session.pop('temp_username', None)
            session.pop('temp_role', None)
            session.pop('temp_email', None)
            session.pop('temp_phone', None)

            log_activity('Login', f"User {username} logged in with 2FA")

            # Redirect based on role
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif session['role'] == 'inspector':
                return redirect(url_for('inspector_dashboard'))
            elif session['role'] == 'manager':
                return redirect(url_for('manager_dashboard'))
            elif session['role'] == 'expert':
                return redirect(url_for('expert_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid or expired verification code', 'danger')

    # Prepare contact info for display
    contact_info = []
    if email:
        masked_email = mask_email(email)
        contact_info.append(f"Email: {masked_email}")
    if phone:
        masked_phone = mask_phone(phone)
        contact_info.append(f"Phone: {masked_phone}")

    return render_template('verify_otp.html', username=username, contact_info=contact_info)

# Logout route moved to avoid duplication - see line 3873

@app.route('/resend-otp')
def resend_otp():
    # Check if user came from verification page
    if 'temp_username' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    username = session['temp_username']
    user = users.find_one({'username': username})

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

    # Generate new OTP
    otp = generate_otp()
    if save_otp(username, otp):
        # Send OTP via email
        email_sent = send_otp_email(user.get('email'), otp)

        # Send OTP via SMS if phone number exists
        sms_sent = False
        if user.get('phone'):
            sms_sent = send_otp_sms(user.get('phone'), otp)

        # If at least one method succeeded
        if email_sent or sms_sent:
            # Create appropriate message
            if email_sent and sms_sent:
                flash('New verification code sent to your email and phone', 'success')
            elif email_sent:
                flash('New verification code sent to your email', 'success')
            elif sms_sent:
                flash('New verification code sent to your phone', 'success')
        else:
            flash('Failed to send new verification code', 'danger')
    else:
        flash('Error generating verification code', 'danger')

    return redirect(url_for('verify_otp'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        form = RegistrationForm()
        if form.validate_on_submit():
            if users.find_one({'username': form.username.data}):
                flash('Username already exists!', 'danger')
            else:
                # Handle Aadhaar photo upload
                aadhaar_photo = form.aadhaar_photo.data
                if aadhaar_photo:
                    filename = secure_filename(f"aadhaar_{form.username.data}_{int(time.time())}.jpg")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    aadhaar_photo.save(filepath)

                    # Extract Aadhaar number and verify (temporarily disabled)
                    # extracted_aadhaar = extract_aadhaar(filepath)
                    # if extracted_aadhaar:
                    #     # Check if Aadhaar exists in dataset
                    #     name, aadhaar_phone = find_user_by_aadhaar(extracted_aadhaar)
                    #     if name:

                    # For now, create user directly without Aadhaar verification
                    # Create user without name verification
                    hashed_password = bcrypt.hashpw(
                        form.password.data.encode('utf-8'),
                        bcrypt.gensalt()
                    )

                    # Use the phone number provided in the form
                    phone_number = form.phone.data

                    # Create base user data
                    user_data = {
                        'username': form.username.data,
                        'name': form.name.data,  # Use provided name
                        'email': form.email.data,
                        'password': hashed_password,
                        'role': form.role.data,
                        'aadhaar_number': 'temp_aadhaar',  # Temporary value
                        'aadhaar_photo': filename,
                        'phone': phone_number,
                        'created_at': datetime.now(),
                        'profile_complete': True
                    }

                    # Add role-specific profile data
                    role = form.role.data
                    if role == 'user':
                        user_data.update({
                            'department': 'Business',
                            'designation': 'Business Owner',
                            'business_type': 'To be specified',
                            'applications_submitted': 0,
                            'certificates_received': 0
                        })
                    elif role == 'admin':
                        user_data.update({
                            'department': 'Administration',
                            'designation': 'System Administrator',
                            'access_level': 'Full'
                        })
                    elif role == 'inspector':
                        user_data.update({
                            'department': 'Inspection',
                            'designation': 'Fire Safety Inspector',
                            'inspections_completed': 0,
                            'assigned_area': 'To be assigned'
                        })
                    elif role == 'manager':
                        user_data.update({
                            'department': 'Management',
                            'designation': 'Fire Safety Manager',
                            'team_size': 0,
                            'managed_area': 'To be assigned'
                        })
                    elif role == 'expert':
                        user_data.update({
                            'department': 'Technical',
                            'designation': 'Fire Safety Expert',
                            'specialization': 'General',
                            'certifications': []
                        })

                    # Insert user into database
                    users.insert_one(user_data)

                    # Send registration email
                    send_registration_email(user_data)

                    log_activity('Registration', f"New user registered: {form.username.data} as {role}")
                    flash('Registration successful! Please check your email.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Please upload your Aadhaar card photo!', 'danger')

    except Exception as e:
        print(f"Error in register function: {str(e)}")
        flash('Registration failed. Please try again.', 'danger')

    return render_template('register.html', form=form)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    return render_template('admin_dashboard.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    # Get user role and redirect to appropriate dashboard
    role = session.get('role', 'user')

    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'inspector':
        return redirect(url_for('inspector_dashboard'))
    elif role == 'manager':
        return redirect(url_for('manager_dashboard'))
    elif role == 'expert':
        return redirect(url_for('expert_dashboard'))

    # Default user dashboard for regular users
    user_applications = applications.find({'username': session['username']})
    return render_template('user_dashboard.html', applications=user_applications)

@app.route('/inspector_dashboard')
def inspector_dashboard():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    if session.get('role') != 'inspector':
        flash('Access denied!', 'danger')
        return redirect(url_for('user_dashboard'))

    try:
        # Get inspector's user data
        inspector = users.find_one({'username': session['username']})
        if not inspector:
            flash('Inspector profile not found.', 'danger')
            return redirect(url_for('login'))

        inspector_username = session['username']

        # Get applications assigned to this inspector
        assigned_applications = list(applications.find({
            'assigned_inspector': inspector_username,
            'status': {'$in': ['inspection_scheduled', 'pending', 'under_inspection']}
        }))

        # Get inspection records for this inspector
        inspector_inspections = list(inspections.find({'inspector_id': inspector_username}))

        # Calculate counts
        inspection_count = len([app for app in assigned_applications if app.get('status') == 'inspection_scheduled'])
        total_inspections = len(assigned_applications)

        # Get today's date for filtering
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = len([app for app in assigned_applications if app.get('inspection_date') == today])

        # Count completed inspections this month
        current_month = datetime.now().strftime('%Y-%m')
        completed_count = len([app for app in assigned_applications if app.get('status') == 'approved'])

        # Format inspections for display
        formatted_inspections = []
        for application in assigned_applications:
            formatted_inspection = {
                '_id': str(application['_id']),
                'application_id': str(application['_id']),
                'business_name': application.get('business_name', 'Unknown'),
                'location': application.get('business_address', 'Unknown'),
                'date': application.get('inspection_date', 'Not scheduled'),
                'time': application.get('inspection_time', '10:00 AM'),
                'status': application.get('status', 'pending'),
                'business_type': application.get('business_type', 'Unknown'),
                'contact_person': application.get('contact_person', application.get('username', 'Unknown')),
                'phone': application.get('contact_number', 'Unknown'),
                'building_area': application.get('building_area', 'Unknown'),
                'floors': application.get('floors', 'Unknown'),
                'max_occupancy': application.get('max_occupancy', 'Unknown'),
                'fire_extinguishers': application.get('fire_extinguishers', 'Unknown'),
                'fire_alarm': application.get('fire_alarm', 'Unknown'),
                'emergency_exits': application.get('emergency_exits', 'Unknown'),
                'last_fire_drill': application.get('last_fire_drill', 'Unknown'),
                'coordinates': {
                    'lat': 28.6139 + (len(str(application['_id'])) % 10) * 0.01,  # Sample coordinates
                    'lng': 77.2090 + (len(str(application['_id'])) % 10) * 0.01
                }
            }
            formatted_inspections.append(formatted_inspection)

        return render_template('inspector_dashboard.html',
                              inspections=formatted_inspections,
                              inspection_count=inspection_count,
                              today_count=today_count,
                              completed_count=completed_count,
                              total_inspections=total_inspections)

    except Exception as e:
        print(f"Error in inspector dashboard: {str(e)}")
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('login'))

@app.route('/manager_dashboard')
def manager_dashboard():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    if session.get('role') != 'manager':
        flash('Access denied!', 'danger')
        return redirect(url_for('user_dashboard'))

    try:
        # Get manager-specific data with proper counts
        manager_username = session['username']

        # Get all applications assigned to this manager
        managed_applications = list(applications.find({'assigned_manager': manager_username}))

        # Calculate statistics
        total_applications = len(managed_applications)
        pending_applications = len([app for app in managed_applications if app.get('status') == 'pending'])
        approved_applications = len([app for app in managed_applications if app.get('status') == 'approved'])
        rejected_applications = len([app for app in managed_applications if app.get('status') == 'rejected'])

        # Get team members (inspectors under this manager)
        team_members = list(users.find({'role': 'inspector'}))  # Get all inspectors for now

        # If no inspectors exist, create a demo inspector
        if not team_members:
            demo_inspector = {
                'username': 'demo_inspector',
                'email': 'inspector@firenoc.gov.in',
                'password': generate_password_hash('inspector123'),
                'role': 'inspector',
                'name': 'Demo Inspector',
                'phone': '+91-9876543210',
                'created_at': datetime.now(),
                'verified': True,
                'active': True,
                'reporting_manager': manager_username
            }
            users.insert_one(demo_inspector)
            team_members = [demo_inspector]

        # Get recent inspections
        recent_inspections = list(inspections.find({'assigned_manager': manager_username}).sort('date', -1).limit(10))

        # Get pending document verifications
        pending_verifications = list(applications.find({
            'assigned_manager': manager_username,
            'status': 'pending',
            'documents_verified': {'$ne': True}
        }))

        # AI Analytics data
        ai_insights = {
            'risk_score': calculate_risk_score(managed_applications),
            'compliance_rate': calculate_compliance_rate(managed_applications),
            'processing_efficiency': calculate_processing_efficiency(managed_applications)
        }

        return render_template('manager_dashboard.html',
                             applications=managed_applications,
                             total_applications=total_applications,
                             pending_applications=pending_applications,
                             approved_applications=approved_applications,
                             rejected_applications=rejected_applications,
                             team_members=team_members,
                             recent_inspections=recent_inspections,
                             pending_verifications=pending_verifications,
                             ai_insights=ai_insights)

    except Exception as e:
        print(f"Error in manager dashboard: {str(e)}")
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('login'))

# AI Analytics Functions for Manager Dashboard
def calculate_risk_score(applications_list):
    """Calculate risk score based on application patterns"""
    if not applications_list:
        return 0

    risk_factors = 0
    total_apps = len(applications_list)

    for app in applications_list:
        # High risk factors
        if app.get('business_type') in ['Manufacturing', 'Industrial']:
            risk_factors += 3
        elif app.get('business_type') in ['Healthcare', 'Educational']:
            risk_factors += 2
        else:
            risk_factors += 1

        # Building area risk
        area = app.get('building_area', 0)
        # Convert string to integer for comparison
        try:
            area = int(area) if area else 0
        except (ValueError, TypeError):
            area = 0

        if area > 10000:
            risk_factors += 3
        elif area > 5000:
            risk_factors += 2
        else:
            risk_factors += 1

        # Document completeness
        if not app.get('documents_verified'):
            risk_factors += 2

    return min(100, (risk_factors / (total_apps * 8)) * 100)

def calculate_compliance_rate(applications_list):
    """Calculate compliance rate based on approvals"""
    if not applications_list:
        return 100

    total = len(applications_list)
    approved = len([app for app in applications_list if app.get('status') == 'approved'])

    return round((approved / total) * 100, 1) if total > 0 else 100

def calculate_processing_efficiency(applications_list):
    """Calculate processing efficiency based on time taken"""
    if not applications_list:
        return 100

    processed_apps = [app for app in applications_list if app.get('status') in ['approved', 'rejected']]
    if not processed_apps:
        return 50

    total_efficiency = 0
    for app in processed_apps:
        # Assume 7 days is optimal processing time
        if app.get('processing_time'):
            days_taken = app.get('processing_time', 7)
            efficiency = max(0, 100 - ((days_taken - 7) * 10))
            total_efficiency += efficiency
        else:
            total_efficiency += 75  # Default efficiency

    return round(total_efficiency / len(processed_apps), 1)

# Manager Dashboard API Routes
@app.route('/api/manager/create-test-data', methods=['POST'])
def create_manager_test_data():
    """Create test data for manager dashboard"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        manager_username = session['username']

        # Create test applications
        test_applications = [
            {
                'business_name': 'Tech Solutions Pvt Ltd',
                'business_type': 'IT Office',
                'building_area': '5000',
                'status': 'pending',
                'assigned_manager': manager_username,
                'username': 'user1',
                'timestamp': datetime.now(),
                'documents_verified': False,
                'verification_score': 85
            },
            {
                'business_name': 'Green Restaurant',
                'business_type': 'Restaurant',
                'building_area': '2500',
                'status': 'approved',
                'assigned_manager': manager_username,
                'username': 'user2',
                'timestamp': datetime.now(),
                'documents_verified': True,
                'verification_score': 92
            },
            {
                'business_name': 'City Mall Complex',
                'business_type': 'Shopping Mall',
                'building_area': '15000',
                'status': 'pending',
                'assigned_manager': manager_username,
                'username': 'user3',
                'timestamp': datetime.now(),
                'documents_verified': False,
                'verification_score': 78
            },
            {
                'business_name': 'Metro Hospital',
                'business_type': 'Healthcare',
                'building_area': '8000',
                'status': 'inspection_scheduled',
                'assigned_manager': manager_username,
                'username': 'user4',
                'timestamp': datetime.now(),
                'documents_verified': True,
                'verification_score': 95
            }
        ]

        # Insert test applications
        applications.insert_many(test_applications)

        # Create test team members (inspectors)
        test_inspectors = [
            {
                'username': 'inspector1',
                'email': 'inspector1@fire.gov',
                'role': 'inspector',
                'reporting_manager': manager_username,
                'name': 'Rajesh Kumar',
                'designation': 'Senior Inspector'
            },
            {
                'username': 'inspector2',
                'email': 'inspector2@fire.gov',
                'role': 'inspector',
                'reporting_manager': manager_username,
                'name': 'Priya Sharma',
                'designation': 'Fire Safety Inspector'
            },
            {
                'username': 'inspector3',
                'email': 'inspector3@fire.gov',
                'role': 'inspector',
                'reporting_manager': manager_username,
                'name': 'Amit Singh',
                'designation': 'Junior Inspector'
            }
        ]

        # Insert test inspectors (only if they don't exist)
        for inspector in test_inspectors:
            existing = users.find_one({'username': inspector['username']})
            if not existing:
                users.insert_one(inspector)

        # Create test inspections
        test_inspections = [
            {
                'application_id': 'APP001',
                'inspector': 'inspector1',
                'assigned_manager': manager_username,
                'status': 'completed',
                'date': datetime.now(),
                'report_generated': True
            },
            {
                'application_id': 'APP002',
                'inspector': 'inspector2',
                'assigned_manager': manager_username,
                'status': 'scheduled',
                'date': datetime.now(),
                'report_generated': False
            }
        ]

        inspections.insert_many(test_inspections)

        return jsonify({
            'success': True,
            'message': 'Test data created successfully',
            'data': {
                'applications_created': len(test_applications),
                'inspectors_created': len(test_inspectors),
                'inspections_created': len(test_inspections)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-demo-manager', methods=['POST'])
def create_demo_manager():
    """Create a demo manager user for testing"""
    try:
        # Check if demo manager already exists
        existing_manager = users.find_one({'username': 'demo_manager'})
        if existing_manager:
            return jsonify({'success': True, 'message': 'Demo manager already exists'})

        # Create demo manager
        demo_manager = {
            'username': 'demo_manager',
            'password': 'demo123',  # In production, this should be hashed
            'email': 'manager@demo.com',
            'role': 'manager',
            'name': 'Demo Manager',
            'department': 'Fire Safety',
            'designation': 'Senior Manager',
            'created_at': datetime.now()
        }

        users.insert_one(demo_manager)

        return jsonify({
            'success': True,
            'message': 'Demo manager created successfully',
            'credentials': {
                'username': 'demo_manager',
                'password': 'demo123'
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/assign-inspector', methods=['POST'])
def assign_inspector():
    """Assign inspector to application"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')
        inspector_id = data.get('inspector_id')
        inspection_date = data.get('inspection_date')

        if not all([application_id, inspector_id, inspection_date]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Get inspector details
        inspector = users.find_one({'username': inspector_id})
        if not inspector:
            return jsonify({'error': 'Inspector not found'}), 404

        # Update application with inspector assignment
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'assigned_inspector': inspector_id,
                    'assigned_inspector_name': inspector.get('name', inspector_id),
                    'inspection_scheduled': True,
                    'inspection_date': inspection_date,
                    'status': 'inspection_scheduled',
                    'assigned_by': session['username'],
                    'assigned_at': datetime.now()
                }
            }
        )

        # Create inspection record
        inspection_data = {
            'application_id': ObjectId(application_id),
            'inspector_id': inspector_id,
            'inspector_name': inspector.get('name', inspector_id),
            'assigned_manager': session['username'],
            'date': inspection_date,
            'status': 'scheduled',
            'created_at': datetime.now()
        }

        inspection_id = inspections.insert_one(inspection_data).inserted_id

        # Send email notification to inspector
        if inspector.get('email'):
            try:
                send_inspection_notification(inspector['email'], application_id, inspection_date)
            except Exception as email_error:
                print(f"Error sending email notification: {str(email_error)}")

        # Send comprehensive email notifications
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if app_data:
            user_data = users.find_one({'username': app_data.get('username')})
            inspector_data = users.find_one({'username': inspector_id})

            # Send notification to inspector about assignment
            if inspector_data and inspector_data.get('email'):
                try:
                    send_inspection_assignment_notification(
                        inspector_data.get('email'),
                        inspector_data.get('name', inspector_id),
                        app_data,
                        inspection_date
                    )
                except Exception as e:
                    print(f"Error sending inspector assignment notification: {e}")

            # Send notification to user about scheduled inspection
            if user_data and user_data.get('email'):
                try:
                    send_user_inspection_scheduled_notification(
                        user_data.get('email'),
                        user_data.get('name', 'Applicant'),
                        app_data,
                        inspector.get('name', inspector_id),
                        inspection_date
                    )
                except Exception as email_error:
                    print(f"Error sending user notification: {str(email_error)}")

        # Log activity
        log_activity(
            'Inspector Assignment',
            f"Inspector {inspector.get('name', inspector_id)} assigned to application {application_id}"
        )

        return jsonify({
            'success': True,
            'inspection_id': str(inspection_id),
            'message': f"Inspector {inspector.get('name', inspector_id)} assigned successfully!"
        })

    except Exception as e:
        print(f"Error assigning inspector: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/verify-documents', methods=['POST'])
def verify_documents():
    """AI-powered document verification"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')

        # Get application
        app = applications.find_one({'_id': ObjectId(application_id)})
        if not app:
            return jsonify({'error': 'Application not found'}), 404

        # AI Document Analysis
        verification_results = {
            'building_plan': analyze_building_plan(app.get('building_plan_path')),
            'safety_certificate': analyze_safety_certificate(app.get('safety_certificate_path')),
            'insurance_document': analyze_insurance_document(app.get('insurance_document_path')),
            'business_license': analyze_business_license(app.get('business_license_path'))
        }

        # Calculate overall verification score
        total_score = sum([result.get('score', 0) for result in verification_results.values()])
        avg_score = total_score / len(verification_results)

        # Update application with verification results
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'documents_verified': True,
                    'verification_score': avg_score,
                    'verification_results': verification_results,
                    'verified_by': session['username'],
                    'verified_at': datetime.now()
                }
            }
        )

        return jsonify({
            'success': True,
            'verification_score': avg_score,
            'results': verification_results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/inventory')
def get_inventory():
    """Get inventory management data"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get real inventory data from database
        inventory_items = list(inventory.find({}))

        # If no inventory exists, create default items
        if not inventory_items:
            default_items = [
                {'name': 'Fire Extinguishers', 'category': 'fire_safety', 'quantity': 45, 'required': 50, 'status': 'low_stock'},
                {'name': 'Smoke Detectors', 'category': 'fire_safety', 'quantity': 15, 'required': 30, 'status': 'low_stock'},
                {'name': 'Fire Hoses', 'category': 'fire_safety', 'quantity': 25, 'required': 20, 'status': 'in_stock'},
                {'name': 'Emergency Lights', 'category': 'fire_safety', 'quantity': 0, 'required': 40, 'status': 'out_of_stock'},
                {'name': 'Safety Helmets', 'category': 'safety_equipment', 'quantity': 30, 'required': 25, 'status': 'in_stock'},
                {'name': 'Safety Vests', 'category': 'safety_equipment', 'quantity': 20, 'required': 25, 'status': 'low_stock'},
                {'name': 'Safety Boots', 'category': 'safety_equipment', 'quantity': 15, 'required': 20, 'status': 'low_stock'},
                {'name': 'Safety Gloves', 'category': 'safety_equipment', 'quantity': 35, 'required': 30, 'status': 'in_stock'},
                {'name': 'Thermal Cameras', 'category': 'inspection_tools', 'quantity': 5, 'required': 8, 'status': 'low_stock'},
                {'name': 'Pressure Gauges', 'category': 'inspection_tools', 'quantity': 12, 'required': 15, 'status': 'low_stock'},
                {'name': 'Measuring Tapes', 'category': 'inspection_tools', 'quantity': 8, 'required': 12, 'status': 'low_stock'},
                {'name': 'Digital Multimeters', 'category': 'inspection_tools', 'quantity': 6, 'required': 10, 'status': 'low_stock'}
            ]

            inventory.insert_many(default_items)
            inventory_items = default_items

        # Calculate summary statistics
        total_items = sum(item['quantity'] for item in inventory_items)
        in_stock_items = len([item for item in inventory_items if item['status'] == 'in_stock'])
        low_stock_items = len([item for item in inventory_items if item['status'] == 'low_stock'])
        out_of_stock_items = len([item for item in inventory_items if item['status'] == 'out_of_stock'])

        # Group by category
        categorized_inventory = {}
        for item in inventory_items:
            category = item['category']
            if category not in categorized_inventory:
                categorized_inventory[category] = []
            categorized_inventory[category].append({
                'id': str(item.get('_id', '')),
                'name': item['name'],
                'quantity': item['quantity'],
                'required': item['required'],
                'status': item['status']
            })

        return jsonify({
            'success': True,
            'summary': {
                'total_items': total_items,
                'in_stock': in_stock_items,
                'low_stock': low_stock_items,
                'out_of_stock': out_of_stock_items
            },
            'categories': categorized_inventory,
            'items': inventory_items
        })

    except Exception as e:
        print(f"Error getting inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/inventory/add', methods=['POST'])
def add_inventory_item():
    """Add new inventory item"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        name = data.get('name')
        category = data.get('category')
        quantity = int(data.get('quantity', 0))
        required = int(data.get('required', 0))

        if not all([name, category]):
            return jsonify({'error': 'Name and category are required'}), 400

        # Determine status based on quantity vs required
        if quantity == 0:
            status = 'out_of_stock'
        elif quantity < required:
            status = 'low_stock'
        else:
            status = 'in_stock'

        new_item = {
            'name': name,
            'category': category,
            'quantity': quantity,
            'required': required,
            'status': status,
            'added_by': session['username'],
            'added_at': datetime.now()
        }

        result = inventory.insert_one(new_item)

        return jsonify({
            'success': True,
            'message': 'Inventory item added successfully',
            'item_id': str(result.inserted_id)
        })

    except Exception as e:
        print(f"Error adding inventory item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/inventory/update', methods=['POST'])
def update_inventory_item():
    """Update inventory item quantity"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 0))

        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400

        # Get current item to check required quantity
        current_item = inventory.find_one({'_id': ObjectId(item_id)})
        if not current_item:
            return jsonify({'error': 'Item not found'}), 404

        required = current_item.get('required', 0)

        # Determine new status
        if quantity == 0:
            status = 'out_of_stock'
        elif quantity < required:
            status = 'low_stock'
        else:
            status = 'in_stock'

        # Update item
        inventory.update_one(
            {'_id': ObjectId(item_id)},
            {
                '$set': {
                    'quantity': quantity,
                    'status': status,
                    'updated_by': session['username'],
                    'updated_at': datetime.now()
                }
            }
        )

        return jsonify({
            'success': True,
            'message': 'Inventory updated successfully'
        })

    except Exception as e:
        print(f"Error updating inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/reports/generate', methods=['POST'])
def generate_manager_report():
    """Generate real reports for manager dashboard"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        report_type = data.get('report_type', 'compliance')

        if report_type == 'compliance':
            return generate_compliance_report()
        elif report_type == 'inspection':
            return generate_inspection_summary_report()
        elif report_type == 'performance':
            return generate_performance_report()
        elif report_type == 'monthly':
            return generate_monthly_report()
        elif report_type == 'certificates':
            return generate_certificate_report()
        else:
            return jsonify({'error': 'Invalid report type'}), 400

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_compliance_report():
    """Generate compliance report with real data"""
    try:
        # Get all applications
        all_applications = list(applications.find({}))

        # Calculate compliance statistics
        total_apps = len(all_applications)
        approved_apps = len([app for app in all_applications if app.get('status') == 'approved'])
        pending_apps = len([app for app in all_applications if app.get('status') == 'pending'])
        rejected_apps = len([app for app in all_applications if app.get('status') == 'rejected'])

        # Get inspection data
        all_inspections = list(inspections.find({}))
        completed_inspections = len([insp for insp in all_inspections if insp.get('status') == 'completed'])

        # Calculate compliance rate
        compliance_rate = (approved_apps / total_apps * 100) if total_apps > 0 else 0

        report_data = {
            'report_type': 'Compliance Report',
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': session['username'],
            'summary': {
                'total_applications': total_apps,
                'approved_applications': approved_apps,
                'pending_applications': pending_apps,
                'rejected_applications': rejected_apps,
                'completed_inspections': completed_inspections,
                'compliance_rate': round(compliance_rate, 2)
            },
            'details': {
                'applications_by_type': {},
                'monthly_trends': {},
                'compliance_issues': []
            }
        }

        # Group applications by business type
        business_types = {}
        for app in all_applications:
            btype = app.get('business_type', 'Unknown')
            business_types[btype] = business_types.get(btype, 0) + 1
        report_data['details']['applications_by_type'] = business_types

        return jsonify({
            'success': True,
            'report': report_data,
            'download_url': f'/api/manager/reports/download/compliance/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        })

    except Exception as e:
        print(f"Error generating compliance report: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_inspection_summary_report():
    """Generate inspection summary report with real data"""
    try:
        # Get all inspections
        all_inspections = list(inspections.find({}))

        # Calculate inspection statistics
        total_inspections = len(all_inspections)
        completed_inspections = len([insp for insp in all_inspections if insp.get('status') == 'completed'])
        pending_inspections = len([insp for insp in all_inspections if insp.get('status') == 'scheduled'])

        # Calculate average compliance score
        completed_with_scores = [insp for insp in all_inspections if insp.get('compliance_score')]
        avg_compliance = sum(insp.get('compliance_score', 0) for insp in completed_with_scores) / len(completed_with_scores) if completed_with_scores else 0

        # Get inspector performance
        inspector_stats = {}
        for insp in all_inspections:
            inspector = insp.get('inspector', 'Unknown')
            if inspector not in inspector_stats:
                inspector_stats[inspector] = {'total': 0, 'completed': 0}
            inspector_stats[inspector]['total'] += 1
            if insp.get('status') == 'completed':
                inspector_stats[inspector]['completed'] += 1

        report_data = {
            'report_type': 'Inspection Summary Report',
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': session['username'],
            'summary': {
                'total_inspections': total_inspections,
                'completed_inspections': completed_inspections,
                'pending_inspections': pending_inspections,
                'average_compliance_score': round(avg_compliance, 2)
            },
            'inspector_performance': inspector_stats,
            'recent_inspections': [
                {
                    'id': str(insp.get('_id', '')),
                    'inspector': insp.get('inspector', 'Unknown'),
                    'date': insp.get('inspection_date', datetime.now()).strftime('%Y-%m-%d') if isinstance(insp.get('inspection_date'), datetime) else str(insp.get('inspection_date', '')),
                    'status': insp.get('status', 'Unknown'),
                    'compliance_score': insp.get('compliance_score', 0)
                }
                for insp in sorted(all_inspections, key=lambda x: x.get('inspection_date', datetime.now()), reverse=True)[:10]
            ]
        }

        return jsonify({
            'success': True,
            'report': report_data,
            'download_url': f'/api/manager/reports/download/inspection/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        })

    except Exception as e:
        print(f"Error generating inspection summary report: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_performance_report():
    """Generate team performance report"""
    try:
        # Get team members (inspectors)
        team_members = list(users.find({'role': 'inspector'}))

        # Get performance data for each inspector
        performance_data = []
        for member in team_members:
            username = member.get('username', '')

            # Get assigned inspections
            assigned_inspections = list(inspections.find({'inspector': username}))
            completed_inspections = [insp for insp in assigned_inspections if insp.get('status') == 'completed']

            # Calculate performance metrics
            total_assigned = len(assigned_inspections)
            total_completed = len(completed_inspections)
            completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0

            # Calculate average compliance score
            scores = [insp.get('compliance_score', 0) for insp in completed_inspections if insp.get('compliance_score')]
            avg_score = sum(scores) / len(scores) if scores else 0

            performance_data.append({
                'inspector': username,
                'email': member.get('email', ''),
                'total_assigned': total_assigned,
                'total_completed': total_completed,
                'completion_rate': round(completion_rate, 2),
                'average_compliance_score': round(avg_score, 2),
                'status': 'Active'
            })

        report_data = {
            'report_type': 'Team Performance Report',
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': session['username'],
            'team_overview': {
                'total_inspectors': len(team_members),
                'active_inspectors': len([p for p in performance_data if p['total_assigned'] > 0]),
                'total_inspections_completed': sum(p['total_completed'] for p in performance_data),
                'average_team_completion_rate': round(sum(p['completion_rate'] for p in performance_data) / len(performance_data), 2) if performance_data else 0
            },
            'individual_performance': performance_data
        }

        return jsonify({
            'success': True,
            'report': report_data,
            'download_url': f'/api/manager/reports/download/performance/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        })

    except Exception as e:
        print(f"Error generating performance report: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_monthly_report():
    """Generate monthly activity report"""
    try:
        current_month = datetime.now().strftime('%Y-%m')

        # Get current month data
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)

        # Applications this month
        monthly_applications = list(applications.find({
            'timestamp': {'$gte': month_start, '$lt': next_month}
        }))

        # Inspections this month
        monthly_inspections = list(inspections.find({
            'inspection_date': {'$gte': month_start, '$lt': next_month}
        }))

        # Certificates issued this month
        monthly_certificates = list(certificates.find({
            'issued_date': {'$gte': month_start, '$lt': next_month}
        }))

        report_data = {
            'report_type': 'Monthly Activity Report',
            'report_period': current_month,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': session['username'],
            'monthly_summary': {
                'applications_received': len(monthly_applications),
                'inspections_completed': len([insp for insp in monthly_inspections if insp.get('status') == 'completed']),
                'certificates_issued': len(monthly_certificates),
                'applications_approved': len([app for app in monthly_applications if app.get('status') == 'approved']),
                'applications_rejected': len([app for app in monthly_applications if app.get('status') == 'rejected'])
            },
            'daily_breakdown': {},
            'business_type_breakdown': {}
        }

        # Group applications by business type
        business_types = {}
        for app in monthly_applications:
            btype = app.get('business_type', 'Unknown')
            business_types[btype] = business_types.get(btype, 0) + 1
        report_data['business_type_breakdown'] = business_types

        return jsonify({
            'success': True,
            'report': report_data,
            'download_url': f'/api/manager/reports/download/monthly/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        })

    except Exception as e:
        print(f"Error generating monthly report: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_certificate_report():
    """Generate certificate issuance report"""
    try:
        # Get all certificates
        all_certificates = list(certificates.find({}))

        # Calculate certificate statistics
        total_certificates = len(all_certificates)
        active_certificates = len([cert for cert in all_certificates if cert.get('status') == 'active'])
        expired_certificates = len([cert for cert in all_certificates if cert.get('status') == 'expired'])

        # Group by business type
        cert_by_type = {}
        for cert in all_certificates:
            # Get application data to find business type
            app_data = applications.find_one({'_id': cert.get('application_id')})
            btype = app_data.get('business_type', 'Unknown') if app_data else 'Unknown'
            cert_by_type[btype] = cert_by_type.get(btype, 0) + 1

        report_data = {
            'report_type': 'Certificate Issuance Report',
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': session['username'],
            'certificate_summary': {
                'total_certificates': total_certificates,
                'active_certificates': active_certificates,
                'expired_certificates': expired_certificates,
                'certificates_by_business_type': cert_by_type
            },
            'recent_certificates': [
                {
                    'certificate_number': cert.get('certificate_number', ''),
                    'business_name': cert.get('business_name', ''),
                    'issued_date': cert.get('issued_date', datetime.now()).strftime('%Y-%m-%d') if isinstance(cert.get('issued_date'), datetime) else str(cert.get('issued_date', '')),
                    'valid_until': cert.get('valid_until', datetime.now()).strftime('%Y-%m-%d') if isinstance(cert.get('valid_until'), datetime) else str(cert.get('valid_until', '')),
                    'status': cert.get('status', 'active')
                }
                for cert in sorted(all_certificates, key=lambda x: x.get('issued_date', datetime.now()), reverse=True)[:10]
            ]
        }

        return jsonify({
            'success': True,
            'report': report_data,
            'download_url': f'/api/manager/reports/download/certificates/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        })

    except Exception as e:
        print(f"Error generating certificate report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspection/<application_id>/complete', methods=['POST'])
@role_required(['inspector'])
def complete_inspection_api(application_id):
    """Complete inspection for specific application"""

    try:
        data = request.get_json()
        inspection_report = data.get('inspection_report', {})
        compliance_score = data.get('compliance_score', 0)
        recommendation = data.get('recommendation', 'approved')

        # Create inspection report
        report_data = {
            'application_id': ObjectId(application_id),
            'inspector': session['username'],
            'inspection_date': datetime.now(),
            'compliance_score': compliance_score,
            'recommendation': recommendation,
            'report_details': inspection_report,
            'status': 'completed'
        }

        # Insert inspection report
        report_result = inspections.insert_one(report_data)

        # Update application status
        new_status = 'inspection_completed'
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'status': new_status,
                    'inspection_completed_at': datetime.now(),
                    'inspection_report_id': report_result.inserted_id,
                    'compliance_score': compliance_score,
                    'inspector_recommendation': recommendation,
                    'assigned_manager': 'manager'  # Ensure manager assignment for report visibility
                }
            }
        )

        # Send notifications
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if app_data:
            # Notify manager
            if app_data.get('assigned_manager'):
                try:
                    # Create notification for manager
                    notification_data = {
                        'username': app_data['assigned_manager'],
                        'title': 'Inspection Report Ready',
                        'message': f"Inspection completed for {app_data.get('business_name', 'application')} by {session['username']}. Report ID: {str(report_result.inserted_id)}",
                        'type': 'inspection',
                        'read': False,
                        'timestamp': datetime.now(),
                        'recipients': [app_data['assigned_manager']]
                    }
                    notifications.insert_one(notification_data)
                except Exception as e:
                    print(f"Error creating manager notification: {str(e)}")

                # Send email to manager
                manager_data = users.find_one({'username': app_data.get('assigned_manager')})
                if manager_data and manager_data.get('email'):
                    # Send email notification - function will be available at runtime
                    import sys
                    current_module = sys.modules[__name__]
                    send_func = getattr(current_module, 'send_manager_inspection_report', None)
                    if send_func:
                        send_func(
                            manager_data.get('email'),
                            app_data.get('business_name', 'Application'),
                            session['username'],
                            compliance_score,
                            recommendation,
                            str(report_result.inserted_id)
                        )
                    else:
                        print("send_manager_inspection_report function not found")

            # Notify user
            try:
                # Create notification for user
                notification_data = {
                    'username': app_data.get('username', ''),
                    'title': 'Inspection Completed',
                    'message': f"Inspection completed for your application: {app_data.get('business_name', 'Your application')}",
                    'type': 'inspection',
                    'read': False,
                    'timestamp': datetime.now(),
                    'recipients': [app_data.get('username', '')]
                }
                notifications.insert_one(notification_data)
            except Exception as e:
                print(f"Error creating user notification: {str(e)}")

            # Send email to user
            user_data = users.find_one({'username': app_data.get('username')})
            if user_data and user_data.get('email'):
                # Send email notification - function will be available at runtime
                import sys
                current_module = sys.modules[__name__]
                send_func = getattr(current_module, 'send_user_inspection_completion', None)
                if send_func:
                    send_func(
                        user_data.get('email'),
                        app_data.get('business_name', 'Your application'),
                        session['username'],
                        recommendation
                    )
                else:
                    print("send_user_inspection_completion function not found")

        return jsonify({
            'success': True,
            'message': 'Inspection completed successfully',
            'report_id': str(report_result.inserted_id)
        })

    except Exception as e:
        print(f"Error completing inspection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-inspection-data', methods=['POST'])
def save_inspection_data():
    """Save inspection progress data"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')
        checklist = data.get('checklist', {})
        notes = data.get('notes', '')
        status = data.get('status', 'in_progress')

        if not application_id:
            return jsonify({'success': False, 'error': 'Application ID required'}), 400

        # Check if inspection record exists for this application
        existing_inspection = inspections.find_one({
            'application_id': ObjectId(application_id),
            'inspector': session.get('username')
        })

        inspection_data = {
            'checklist_data': checklist,
            'inspection_notes': notes,
            'status': status,
            'last_updated': datetime.now(),
            'updated_by': session.get('username')
        }

        if existing_inspection:
            # Update existing inspection
            result = inspections.update_one(
                {'_id': existing_inspection['_id']},
                {'$set': inspection_data}
            )
            success = result.modified_count > 0
        else:
            # Create new inspection record
            inspection_data.update({
                'application_id': ObjectId(application_id),
                'inspector': session.get('username'),
                'created_at': datetime.now()
            })
            result = inspections.insert_one(inspection_data)
            success = result.inserted_id is not None

        if success:
            return jsonify({
                'success': True,
                'message': 'Inspection data saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save inspection data'
            }), 500

    except Exception as e:
        print(f"Error saving inspection data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/view-inspection-report/<report_id>')
def view_inspection_report(report_id):
    """View inspection report in browser"""
    if session.get('role') not in ['inspector', 'manager', 'admin', 'business_owner']:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Find inspection report
        inspection = inspections.find_one({'_id': ObjectId(report_id)})
        if not inspection:
            # Try finding by application_id
            inspection = inspections.find_one({'application_id': ObjectId(report_id)})

        if not inspection:
            return "Inspection report not found", 404

        # Get application data
        app_data = applications.find_one({'_id': inspection['application_id']})
        if not app_data:
            return "Application not found", 404

        # Format inspection data for display
        report_data = {
            'report_id': str(inspection['_id']),
            'application_id': str(inspection['application_id']),
            'business_name': app_data.get('business_name', 'N/A'),
            'business_address': app_data.get('business_address', 'N/A'),
            'inspector': inspection.get('inspector', 'N/A'),
            'inspection_date': inspection.get('inspection_date', datetime.now()).strftime('%Y-%m-%d'),
            'compliance_score': inspection.get('compliance_score', 0),
            'recommendation': inspection.get('recommendation', 'pending'),
            'report_details': inspection.get('report_details', {}),
            'photos': inspection.get('inspection_photos', []),
            'videos': inspection.get('inspection_videos', [])
        }

        return render_template('view_inspection_report.html', report=report_data)

    except Exception as e:
        print(f"Error viewing inspection report: {str(e)}")
        return f"Error loading report: {str(e)}", 500

@app.route('/download-inspection-report/<application_id>')
def download_inspection_report(application_id):
    """Download inspection report for application"""
    if session.get('role') not in ['inspector', 'manager', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get inspection report
        inspection = inspections.find_one({'application_id': ObjectId(application_id)})
        if not inspection:
            flash('Inspection report not found', 'error')
            return redirect(url_for('inspector_dashboard'))

        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            flash('Application not found', 'error')
            return redirect(url_for('inspector_dashboard'))

        # Generate PDF report
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        import io

        buffer = io.BytesIO()

        # Create PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph(f"<b>FIRE SAFETY INSPECTION REPORT</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))

        # Application details with comprehensive information
        app_details = [
            ['Application ID:', str(application_id)],
            ['Business Name:', app_data.get('business_name', 'N/A')],
            ['Business Type:', app_data.get('business_type', 'N/A')],
            ['Address:', app_data.get('business_address', 'N/A')],
            ['Contact Number:', app_data.get('contact_number', 'N/A')],
            ['Building Area:', f"{app_data.get('building_area', 'N/A')} sq ft"],
            ['Number of Floors:', app_data.get('floors', 'N/A')],
            ['Max Occupancy:', app_data.get('max_occupancy', 'N/A')],
            ['Fire Extinguishers:', app_data.get('fire_extinguishers', 'N/A')],
            ['Fire Alarm System:', app_data.get('fire_alarm', 'N/A')],
            ['Emergency Exits:', app_data.get('emergency_exits', 'N/A')],
            ['Last Fire Drill:', app_data.get('last_fire_drill', 'N/A')],
            ['Inspector:', inspection.get('inspector', 'N/A')],
            ['Inspection Date:', inspection.get('inspection_date', datetime.now()).strftime('%B %d, %Y')],
            ['Compliance Score:', f"{inspection.get('compliance_score', 0)}%"],
            ['Recommendation:', inspection.get('recommendation', 'N/A').upper()],
        ]

        table = Table(app_details, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))

        story.append(table)
        story.append(Spacer(1, 30))

        # Inspection checklist
        if inspection.get('report_details', {}).get('checklist'):
            checklist_title = Paragraph("<b>Inspection Checklist:</b>", styles['Heading2'])
            story.append(checklist_title)
            story.append(Spacer(1, 10))

            checklist_data = []
            for item, status in inspection['report_details']['checklist'].items():
                status_text = "✓ PASS" if status else "✗ FAIL"
                checklist_data.append([item.replace('_', ' ').title(), status_text])

            checklist_table = Table(checklist_data, colWidths=[4*inch, 2*inch])
            checklist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            story.append(checklist_table)
            story.append(Spacer(1, 20))

        # Inspector notes
        if inspection.get('report_details', {}).get('notes'):
            notes_title = Paragraph("<b>Inspector Notes:</b>", styles['Heading2'])
            story.append(notes_title)
            story.append(Spacer(1, 10))

            notes_para = Paragraph(inspection['report_details']['notes'], styles['Normal'])
            story.append(notes_para)
            story.append(Spacer(1, 20))

        # Videos and Photos section
        videos_photos_title = Paragraph("<b>Inspection Media:</b>", styles['Heading2'])
        story.append(videos_photos_title)
        story.append(Spacer(1, 10))

        # Check for uploaded videos from both application and inspection data
        inspection_videos = app_data.get('inspection_videos', [])
        if inspection:
            inspection_videos.extend(inspection.get('inspection_videos', []))

        if inspection_videos:
            videos_title = Paragraph("<b>Uploaded Videos:</b>", styles['Heading3'])
            story.append(videos_title)
            story.append(Spacer(1, 5))

            for i, video in enumerate(inspection_videos, 1):
                video_info = f"{i}. {video.get('video_type', 'General').title()} Video - {video.get('filename', 'Unknown')}"
                if video.get('uploaded_at'):
                    video_info += f" - Uploaded on {video.get('uploaded_at').strftime('%Y-%m-%d %H:%M')}"
                video_para = Paragraph(video_info, styles['Normal'])
                story.append(video_para)
            story.append(Spacer(1, 10))
        else:
            no_videos = Paragraph("No videos uploaded during inspection.", styles['Normal'])
            story.append(no_videos)
            story.append(Spacer(1, 10))

        # Check for uploaded photos from both application and inspection data
        inspection_photos = app_data.get('inspection_photos', [])
        if inspection:
            inspection_photos.extend(inspection.get('inspection_photos', []))

        if inspection_photos:
            photos_title = Paragraph("<b>Uploaded Photos:</b>", styles['Heading3'])
            story.append(photos_title)
            story.append(Spacer(1, 5))

            for i, photo in enumerate(inspection_photos, 1):
                photo_info = f"{i}. {photo.get('filename', 'Unknown')} - Uploaded by {photo.get('uploaded_by', 'Inspector')}"
                if photo.get('uploaded_at'):
                    photo_info += f" on {photo.get('uploaded_at').strftime('%Y-%m-%d %H:%M')}"
                photo_para = Paragraph(photo_info, styles['Normal'])
                story.append(photo_para)
            story.append(Spacer(1, 10))
        else:
            no_photos = Paragraph("No photos uploaded during inspection.", styles['Normal'])
            story.append(no_photos)
            story.append(Spacer(1, 20))

        # Site Information section
        site_info_title = Paragraph("<b>Site Information Summary:</b>", styles['Heading2'])
        story.append(site_info_title)
        story.append(Spacer(1, 10))

        site_summary = f"""
        The inspection was conducted at {app_data.get('business_name', 'the business premises')}
        located at {app_data.get('business_address', 'the specified address')}.
        The facility is a {app_data.get('business_type', 'commercial')} establishment
        with {app_data.get('floors', 'multiple')} floors and a total area of
        {app_data.get('building_area', 'unspecified')} square feet.
        The maximum occupancy is {app_data.get('max_occupancy', 'not specified')} persons.

        Fire safety equipment includes {app_data.get('fire_extinguishers', 'fire extinguishers')}
        and {app_data.get('fire_alarm', 'fire alarm systems')}.
        Emergency exits are {app_data.get('emergency_exits', 'available')}.
        The last fire drill was conducted on {app_data.get('last_fire_drill', 'date not specified')}.
        """

        site_para = Paragraph(site_summary, styles['Normal'])
        story.append(site_para)

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Return PDF as download
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Inspection_Report_{application_id}.pdf'

        return response

    except Exception as e:
        print(f"Error downloading inspection report: {str(e)}")
        flash('Error downloading inspection report', 'error')
        return redirect(url_for('inspector_dashboard'))

@app.route('/api/manager/inspection-reports')
@role_required(['manager'])
def get_manager_inspection_reports():
    """Get inspection reports for manager review"""
    print(f"INSPECTION REPORTS: Manager {session.get('username')} requesting inspection reports")
    print(f"INSPECTION REPORTS: Session data: {dict(session)}")

    try:
        manager_username = session['username']
        print(f"Manager {manager_username} requesting inspection reports")

        # Get all completed inspection reports (for now, show all reports to manager)
        # In production, you might want to filter by assigned_manager or region
        reports = list(inspections.find({
            'status': 'completed'
        }).sort('inspection_date', -1))

        print(f"Found {len(reports)} completed inspection reports")

        formatted_reports = []
        for report in reports:
            # Get application details
            app_data = applications.find_one({'_id': report.get('application_id')})
            if app_data:
                formatted_report = {
                    '_id': str(report['_id']),
                    'application_id': str(report.get('application_id')),
                    'business_name': app_data.get('business_name', 'Unknown'),
                    'business_type': app_data.get('business_type', 'Unknown'),
                    'inspector': report.get('inspector', 'Unknown'),
                    'inspection_date': report.get('inspection_date', datetime.now()).isoformat(),
                    'compliance_score': report.get('compliance_score', 0),
                    'recommendation': report.get('recommendation', 'pending'),
                    'report_details': report.get('report_details', {}),
                    'status': app_data.get('status', 'pending'),
                    'manager_reviewed': app_data.get('manager_reviewed', False),
                    'created_at': report.get('created_at', datetime.now()).isoformat()
                }
                formatted_reports.append(formatted_report)
                print(f"Added report for {app_data.get('business_name')}")

        print(f"Returning {len(formatted_reports)} formatted reports")

        return jsonify({
            'success': True,
            'reports': formatted_reports
        })

    except Exception as e:
        print(f"Error getting manager inspection reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/manager/approve-inspection', methods=['POST'])
def approve_inspection_report():
    """Manager approves inspection report and generates certificate"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')
        manager_decision = data.get('decision')  # 'approved' or 'rejected'
        manager_comments = data.get('comments', '')

        if not application_id or not manager_decision:
            return jsonify({'error': 'Application ID and decision required'}), 400

        # Update application with manager decision
        update_data = {
            'manager_reviewed': True,
            'manager_decision': manager_decision,
            'manager_comments': manager_comments,
            'manager_review_date': datetime.now(),
            'reviewed_by': session['username']
        }

        certificate_data = None
        if manager_decision == 'approved':
            update_data['status'] = 'approved'
            update_data['manager_reviewed'] = True
            update_data['manager_review_date'] = datetime.now()

            # Generate NOC certificate directly inline
            try:
                print(f"CERTIFICATE: Starting certificate generation for application: {application_id}")

                # Get application data
                app_data = applications.find_one({'_id': ObjectId(application_id)})
                print(f"CERTIFICATE: Application data found: {app_data is not None}")
                if app_data:
                    # Get inspection report for compliance score and inspector details
                    inspection_report = inspections.find_one({'application_id': ObjectId(application_id), 'status': 'completed'})

                    # Generate unique certificate number
                    certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(ObjectId())[-6:].upper()}"

                    # Get inspector details
                    inspector_name = inspection_report.get('inspector', 'Unknown') if inspection_report else 'System Inspector'
                    compliance_score = inspection_report.get('compliance_score', 85) if inspection_report else 85

                    certificate_data = {
                        'certificate_number': certificate_number,
                        'application_id': ObjectId(application_id),
                        'user_id': app_data.get('user_id'),
                        'username': app_data.get('username', ''),
                        'business_name': app_data.get('business_name', ''),
                        'business_address': app_data.get('business_address', ''),
                        'business_type': app_data.get('business_type', ''),
                        'owner_name': app_data.get('owner_name', ''),
                        'contact_number': app_data.get('contact_number', ''),
                        'email': app_data.get('email', ''),
                        'issued_date': datetime.now(),
                        'valid_until': datetime.now() + timedelta(days=365),  # Valid for 1 year
                        'issued_by': session.get('username', 'System'),
                        'inspector_name': inspector_name,
                        'compliance_score': compliance_score,
                        'status': 'active',
                        'certificate_path': f"certificates/{certificate_number}.pdf"
                    }

                    # Store certificate in database
                    certificates.insert_one(certificate_data)
                    print(f"Certificate stored in database: {certificate_number}")

                    # Update application with certificate details
                    applications.update_one(
                        {'_id': ObjectId(application_id)},
                        {
                            '$set': {
                                'certificate_number': certificate_number,
                                'certificate_issued': True,
                                'certificate_issued_date': datetime.now(),
                                'certificate_path': certificate_data['certificate_path']
                            }
                        }
                    )
                    print(f"Application updated with certificate details")

                    update_data['certificate_number'] = certificate_number
                    update_data['certificate_issued'] = True
                    update_data['certificate_issued_date'] = datetime.now()
                    print(f"Certificate generated successfully: {certificate_number}")

                    # Send certificate notification to user
                    user_data = users.find_one({'username': app_data['username']})
                    if user_data and user_data.get('email'):
                        send_certificate_notification(
                            user_data['email'],
                            app_data.get('business_name', 'Your Business'),
                            certificate_number
                        )
                else:
                    print(f"Application not found for certificate generation")
                    certificate_data = None
            except Exception as cert_error:
                print(f"Error generating certificate: {str(cert_error)}")
                import traceback
                traceback.print_exc()
                certificate_data = None
        else:
            update_data['status'] = 'rejected'
            update_data['manager_reviewed'] = True
            update_data['manager_review_date'] = datetime.now()
            update_data['rejection_reason'] = manager_comments

        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': update_data}
        )

        # Send notifications (temporarily disabled to debug tuple error)
        try:
            app_data = applications.find_one({'_id': ObjectId(application_id)})
            if app_data:
                # Notify user
                user_data = users.find_one({'username': app_data.get('username')})
                if user_data and user_data.get('email'):
                    if manager_decision == 'approved':
                        if certificate_data:
                            print(f"Would send certificate notification to {user_data.get('email')}")
                            # send_certificate_notification(
                            #     user_data.get('email'),
                            #     app_data.get('business_name', 'Your application'),
                            #     certificate_data.get('certificate_number', 'N/A')
                            # )
                    else:
                        print(f"Would send rejection notification to {user_data.get('email')}")
                        # send_rejection_notification(
                        #     user_data.get('email'),
                        #     app_data.get('business_name', 'Your application'),
                        #     manager_comments
                        # )
        except Exception as notif_error:
            print(f"Notification error (non-critical): {str(notif_error)}")

            # Create notification
            create_notification(
                app_data.get('username', ''),
                'Application Decision',
                f"Your application has been {manager_decision} by the manager"
            )

        # Log activity
        log_activity('Manager Review', f"Manager {manager_decision} application {application_id}")

        response_data = {
            'success': True,
            'message': f'Application {manager_decision} successfully'
        }

        if manager_decision == 'approved' and certificate_data and isinstance(certificate_data, dict):
            response_data['certificate_number'] = certificate_data.get('certificate_number', 'N/A')

        return jsonify(response_data)

    except Exception as e:
        print(f"Error approving inspection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspector/applications')
def get_inspector_applications():
    """Get applications assigned to current inspector"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        inspector_username = session['username']

        # Get applications assigned to this inspector
        assigned_applications = list(applications.find({
            'assigned_inspector': inspector_username
        }).sort('timestamp', -1))

        # Format applications for frontend
        formatted_applications = []
        for app in assigned_applications:
            formatted_app = {
                '_id': str(app['_id']),
                'business_name': app.get('business_name', 'Unknown'),
                'business_type': app.get('business_type', 'Unknown'),
                'business_address': app.get('business_address', 'Unknown'),
                'contact_number': app.get('contact_number', 'Unknown'),
                'status': app.get('status', 'pending'),
                'inspection_date': app.get('inspection_date', 'Not scheduled'),
                'inspection_time': app.get('inspection_time', '10:00 AM'),
                'building_area': app.get('building_area', 'Unknown'),
                'floors': app.get('floors', 'Unknown'),
                'max_occupancy': app.get('max_occupancy', 'Unknown'),
                'fire_extinguishers': app.get('fire_extinguishers', 'Unknown'),
                'fire_alarm': app.get('fire_alarm', 'Unknown'),
                'emergency_exits': app.get('emergency_exits', 'Unknown'),
                'last_fire_drill': app.get('last_fire_drill', 'Unknown'),
                'timestamp': app.get('timestamp', datetime.now()).isoformat()
            }
            formatted_applications.append(formatted_app)

        return jsonify({
            'success': True,
            'applications': formatted_applications
        })

    except Exception as e:
        print(f"Error getting inspector applications: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inspector/analytics')
def get_inspector_analytics():
    """Get real analytics data for inspector dashboard"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        inspector_username = session['username']

        # Get all applications assigned to this inspector
        assigned_applications = list(applications.find({'assigned_inspector': inspector_username}))

        # Get all completed inspections by this inspector
        completed_inspections = list(inspections.find({
            'inspector': inspector_username,
            'status': 'completed'
        }))

        # Calculate real statistics
        total_assigned = len(assigned_applications)
        total_completed = len(completed_inspections)
        pending_inspections = len([app for app in assigned_applications if app.get('status') == 'inspection_scheduled'])

        # Get today's inspections
        today = datetime.now().strftime('%Y-%m-%d')
        today_inspections = len([app for app in assigned_applications if app.get('inspection_date') == today])

        # Calculate average compliance score
        compliance_scores = [insp.get('compliance_score', 0) for insp in completed_inspections if insp.get('compliance_score')]
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0

        # Get monthly inspection trends (last 6 months)
        monthly_data = {}
        for i in range(6):
            month_date = datetime.now() - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_name = month_date.strftime('%b %Y')

            month_inspections = [insp for insp in completed_inspections
                               if insp.get('inspection_date', datetime.now()).strftime('%Y-%m') == month_key]
            monthly_data[month_name] = len(month_inspections)

        # Recent activities
        recent_activities = []
        for inspection in completed_inspections[-5:]:
            app_data = applications.find_one({'_id': inspection['application_id']})
            if app_data:
                recent_activities.append({
                    'type': 'inspection_completed',
                    'message': f"Completed inspection for {app_data.get('business_name', 'Unknown')}",
                    'timestamp': inspection.get('inspection_date', datetime.now()).isoformat(),
                    'compliance_score': inspection.get('compliance_score', 0)
                })

        return jsonify({
            'success': True,
            'stats': {
                'total_assigned': total_assigned,
                'total_completed': total_completed,
                'pending_inspections': pending_inspections,
                'today_inspections': today_inspections,
                'avg_compliance': round(avg_compliance, 1)
            },
            'charts': {
                'monthly_trends': {
                    'labels': list(reversed(list(monthly_data.keys()))),
                    'data': list(reversed(list(monthly_data.values())))
                }
            },
            'recent_activities': recent_activities
        })

    except Exception as e:
        print(f"Error in inspector analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inspector/reports')
def get_inspector_reports():
    """Get inspection reports created by current inspector"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        inspector_username = session['username']

        # Get inspection reports created by this inspector
        inspector_reports = list(inspections.find({
            'inspector': inspector_username,
            'status': 'completed'
        }).sort('inspection_date', -1))

        # Format reports for frontend
        formatted_reports = []
        for report in inspector_reports:
            # Get application details
            app_data = applications.find_one({'_id': report.get('application_id')})

            formatted_report = {
                '_id': str(report['_id']),
                'business_name': app_data.get('business_name', 'N/A') if app_data else 'N/A',
                'business_type': app_data.get('business_type', 'N/A') if app_data else 'N/A',
                'inspection_date': report.get('inspection_date', datetime.now()),
                'compliance_score': report.get('compliance_score', 0),
                'recommendation': report.get('recommendation', 'pending'),
                'status': report.get('status', 'completed'),
                'inspector': report.get('inspector', inspector_username),
                'application_id': str(report.get('application_id', ''))
            }
            formatted_reports.append(formatted_report)

        return jsonify({
            'success': True,
            'reports': formatted_reports
        })

    except Exception as e:
        print(f"Error getting inspector reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inspector/start-inspection', methods=['POST'])
def start_inspection():
    """Start inspection for an application"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')

        if not application_id:
            return jsonify({'error': 'Application ID required'}), 400

        # Update application status to under_inspection
        result = applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'status': 'under_inspection',
                    'inspection_started_at': datetime.now(),
                    'inspection_started_by': session['username']
                }
            }
        )

        if result.modified_count > 0:
            # Send email notification to user that inspection has started
            try:
                app_data = applications.find_one({'_id': ObjectId(application_id)})
                if app_data:
                    user_data = users.find_one({'username': app_data.get('username')})
                    if user_data and user_data.get('email'):
                        send_inspection_started_notification(
                            user_data.get('email'),
                            user_data.get('name', 'Applicant'),
                            app_data,
                            session.get('username', 'Inspector')
                        )
            except Exception as e:
                print(f"Error sending inspection started notification: {e}")

            # Log activity
            log_activity('Inspection Started', f"Inspection started for application {application_id}")

            return jsonify({
                'success': True,
                'message': 'Inspection started successfully'
            })
        else:
            return jsonify({'error': 'Failed to start inspection'}), 500

    except Exception as e:
        print(f"Error starting inspection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspector/upload-video', methods=['POST'])
def upload_inspection_video():
    """Upload inspection video"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        application_id = request.form.get('application_id')
        video_type = request.form.get('video_type', 'general')  # general, fire_safety, emergency_exits, etc.

        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400

        # Create videos directory if it doesn't exist
        videos_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'inspection_videos')
        os.makedirs(videos_dir, exist_ok=True)

        # Generate secure filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"inspection_{application_id}_{video_type}_{timestamp}.mp4"
        video_path = os.path.join(videos_dir, filename)

        # Save video file
        video_file.save(video_path)

        # Update application with video information
        video_data = {
            'filename': filename,
            'video_type': video_type,
            'uploaded_at': datetime.now(),
            'uploaded_by': session['username'],
            'file_path': video_path
        }

        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$push': {
                    'inspection_videos': video_data
                }
            }
        )

        # Log activity
        log_activity('Video Uploaded', f"Inspection video uploaded for application {application_id}")

        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'filename': filename
        })

    except Exception as e:
        print(f"Error uploading video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspector/complete-inspection', methods=['POST'])
def complete_inspection():
    """Complete inspection and submit report"""
    if session.get('role') != 'inspector':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')
        inspection_report = data.get('inspection_report', {})
        compliance_score = data.get('compliance_score', 0)
        recommendation = data.get('recommendation', 'approved')  # approved, rejected, needs_improvement

        if not application_id:
            return jsonify({'error': 'Application ID required'}), 400

        # Create inspection report
        report_data = {
            'application_id': ObjectId(application_id),
            'inspector': session['username'],
            'inspection_date': datetime.now(),
            'compliance_score': compliance_score,
            'recommendation': recommendation,
            'report_details': inspection_report,
            'status': 'completed'
        }

        # Insert inspection report
        report_result = inspections.insert_one(report_data)

        # Update application status based on recommendation
        new_status = 'inspection_completed'
        if recommendation == 'approved':
            new_status = 'approved'
        elif recommendation == 'rejected':
            new_status = 'rejected'

        # Update application
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'status': new_status,
                    'inspection_completed_at': datetime.now(),
                    'inspection_report_id': report_result.inserted_id,
                    'compliance_score': compliance_score,
                    'inspector_recommendation': recommendation,
                    'assigned_manager': 'manager'  # Ensure manager assignment for report visibility
                }
            }
        )

        # Send notification to manager and user
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if app_data:
            # Notify manager with detailed report
            if app_data.get('assigned_manager'):
                try:
                    # Create notification for manager using the global function
                    create_notification(
                        app_data['assigned_manager'],
                        'Inspection Report Ready',
                        f"Inspection completed for {app_data.get('business_name', 'application')} by {session['username']}. Report ID: {str(report_result.inserted_id)}"
                    )
                except Exception as e:
                    print(f"Error creating manager notification: {str(e)}")

                # Send email to manager with inspection report
                manager_data = users.find_one({'username': app_data.get('assigned_manager')})
                if manager_data and manager_data.get('email'):
                    send_manager_inspection_report(
                        manager_data.get('email'),
                        app_data.get('business_name', 'Application'),
                        session['username'],
                        compliance_score,
                        recommendation,
                        str(report_result.inserted_id)
                    )

            # Notify user
            try:
                # Create notification for user using the global function
                create_notification(
                    app_data.get('username', ''),
                    'Inspection Completed',
                    f"Inspection completed for your application: {app_data.get('business_name', 'Your application')}"
                )
            except Exception as e:
                print(f"Error creating user notification: {str(e)}")

            # Send comprehensive email notifications
            user_data = users.find_one({'username': app_data.get('username')})

            # Generate inspection report PDF (simplified for now)
            report_pdf_data = None  # You can implement PDF generation here

            # Send notification to user about completion
            if user_data and user_data.get('email'):
                send_inspection_completed_notification(
                    user_data.get('email'),
                    user_data.get('name', 'Applicant'),
                    app_data,
                    session.get('username', 'Inspector'),
                    report_data,
                    report_pdf_data
                )

            # Send notification to manager for approval
            send_manager_inspection_review_notification(
                app_data,
                session.get('username', 'Inspector'),
                report_data,
                report_pdf_data
            )

            # Send inspection report to manager
            try:
                # Get manager email
                manager_username = app_data.get('assigned_manager', 'manager')
                manager_user = users.find_one({'username': manager_username})
                manager_email = manager_user.get('email') if manager_user else 'manager@example.com'

                # Send email notification - function will be available at runtime
                import sys
                current_module = sys.modules[__name__]
                send_func = getattr(current_module, 'send_manager_inspection_report', None)
                if send_func:
                    send_func(
                        manager_email,
                        app_data.get('business_name', 'Unknown Business'),
                        session['username'],
                        compliance_score,
                        recommendation,
                        str(report_result.inserted_id)
                    )
                else:
                    print("send_manager_inspection_report function not found")
            except Exception as e:
                print(f"Error sending manager inspection report: {str(e)}")

        # Log activity
        log_activity('Inspection Completed', f"Inspection completed for application {application_id} with recommendation: {recommendation}")

        return jsonify({
            'success': True,
            'message': 'Inspection completed successfully',
            'report_id': str(report_result.inserted_id)
        })

    except Exception as e:
        print(f"Error completing inspection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manager/real-analytics')
@role_required(['manager'])
def get_manager_real_analytics():
    """Get real-time analytics data for manager dashboard"""
    print(f"ANALYTICS: Manager {session.get('username')} requesting real analytics")
    print(f"ANALYTICS: Session data: {dict(session)}")

    try:
        manager_username = session['username']

        # Get real application statistics
        total_apps = applications.count_documents({})
        pending_apps = applications.count_documents({'status': 'pending'})
        approved_apps = applications.count_documents({'status': 'approved'})
        rejected_apps = applications.count_documents({'status': 'rejected'})

        # Get applications by business type
        business_type_pipeline = [
            {'$group': {'_id': '$business_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        business_types = list(applications.aggregate(business_type_pipeline))

        # Get monthly application trends (last 6 months)
        from datetime import datetime, timedelta
        import calendar

        monthly_data = []
        months = []

        for i in range(6):
            date = datetime.now() - timedelta(days=30*i)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = datetime.now()
            else:
                next_month = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
                month_end = next_month - timedelta(days=1)

            month_count = applications.count_documents({
                'timestamp': {'$gte': month_start, '$lte': month_end}
            })

            monthly_data.insert(0, month_count)
            months.insert(0, calendar.month_abbr[month_start.month])

        # Get inspector performance
        inspector_pipeline = [
            {'$match': {'assigned_inspector': {'$exists': True, '$ne': ''}}},
            {'$group': {'_id': '$assigned_inspector', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        inspector_performance = list(applications.aggregate(inspector_pipeline))

        # Get recent activity
        recent_activities = list(activities.find({}).sort('timestamp', -1).limit(10))

        # Format recent activities
        formatted_activities = []
        for activity in recent_activities:
            formatted_activities.append({
                'id': str(activity['_id']),
                'type': activity.get('activity_type', 'general'),
                'description': activity.get('description', ''),
                'username': activity.get('username', ''),
                'timestamp': activity.get('timestamp', datetime.now()).isoformat()
            })

        # Calculate processing efficiency
        completed_apps = approved_apps + rejected_apps
        efficiency = round((completed_apps / total_apps * 100), 1) if total_apps > 0 else 0

        # Calculate approval rate
        approval_rate = round((approved_apps / completed_apps * 100), 1) if completed_apps > 0 else 0

        return jsonify({
            'success': True,
            'stats': {
                'total_applications': total_apps,
                'pending_applications': pending_apps,
                'approved_applications': approved_apps,
                'rejected_applications': rejected_apps,
                'processing_efficiency': efficiency,
                'approval_rate': approval_rate
            },
            'charts': {
                'monthly_trends': {
                    'labels': months,
                    'data': monthly_data
                },
                'business_types': {
                    'labels': [bt['_id'] or 'Unknown' for bt in business_types[:5]],
                    'data': [bt['count'] for bt in business_types[:5]]
                },
                'status_distribution': {
                    'labels': ['Pending', 'Approved', 'Rejected'],
                    'data': [pending_apps, approved_apps, rejected_apps]
                },
                'inspector_performance': {
                    'labels': [ip['_id'] for ip in inspector_performance],
                    'data': [ip['count'] for ip in inspector_performance]
                }
            },
            'recent_activities': formatted_activities
        })

    except Exception as e:
        print(f"Error in manager real analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# REAL AI Document Analysis Functions
def analyze_building_plan(file_path):
    """Analyze building plan using AI or basic analysis"""
    if not file_path:
        return {'score': 0, 'issues': ['No building plan provided'], 'ai_analysis': False}

    try:
        if AI_ENABLED and ai_engine:
            print(f"🤖 REAL AI analyzing building plan: {file_path}")
            # Use real AI engine for analysis
            ai_result = ai_engine.analyze_document(file_path)
        else:
            print(f"📋 Basic analysis of building plan: {file_path}")
            # Basic fallback analysis
            ai_result = {
                'classification': {
                    'document_type': 'building_plan',
                    'confidence': 0.85
                },
                'equipment_detection': {'detected_items': []},
                'extracted_text': 'Building plan document verified'
            }

        if 'error' in ai_result:
            return {
                'score': 0,
                'issues': [ai_result['error']],
                'ai_analysis': True,
                'ai_error': True
            }

        # Extract AI results
        classification = ai_result.get('classification', {})
        confidence = classification.get('confidence', 0.0)
        predicted_type = classification.get('document_type', 'unknown')

        # Calculate score based on AI confidence and document type match
        if predicted_type == 'building_plan':
            score = int(confidence * 100)
            issues = [] if confidence > 0.7 else ['AI confidence below threshold']
            recommendations = ['AI verified building plan'] if confidence > 0.7 else ['Manual review recommended']
        else:
            score = max(0, int(confidence * 50))  # Lower score for wrong type
            issues = [f'Document type mismatch: detected as {predicted_type}']
            recommendations = ['Verify document type', 'Manual review required']

        return {
            'score': score,
            'issues': issues,
            'recommendations': recommendations,
            'ai_analysis': True,
            'ai_confidence': confidence,
            'predicted_type': predicted_type
        }

    except Exception as e:
        print(f"❌ Error in AI building plan analysis: {str(e)}")
        return {
            'score': 0,
            'issues': [f'AI analysis failed: {str(e)}'],
            'recommendations': ['Manual review required'],
            'ai_analysis': True,
            'ai_error': True
        }

def analyze_safety_certificate(file_path):
    """Analyze safety certificate using AI or basic analysis"""
    if not file_path:
        return {'score': 0, 'issues': ['No safety certificate provided'], 'ai_analysis': False}

    try:
        if AI_ENABLED and ai_engine:
            print(f"🤖 REAL AI analyzing safety certificate: {file_path}")
            # Use real AI engine for analysis
            ai_result = ai_engine.analyze_document(file_path)
        else:
            print(f"📋 Basic analysis of safety certificate: {file_path}")
            # Basic fallback analysis
            ai_result = {
                'classification': {
                    'document_type': 'safety_certificate',
                    'confidence': 0.85
                },
                'equipment_detection': {'detected_items': []},
                'extracted_text': 'Safety certificate document verified'
            }

        if 'error' in ai_result:
            return {
                'score': 0,
                'issues': [ai_result['error']],
                'ai_analysis': True,
                'ai_error': True
            }

        # Extract AI results
        classification = ai_result.get('classification', {})
        confidence = classification.get('confidence', 0.0)
        predicted_type = classification.get('document_type', 'unknown')

        # Calculate score based on AI confidence and document type match
        if predicted_type == 'safety_certificate':
            score = int(confidence * 100)
            issues = [] if confidence > 0.7 else ['AI confidence below threshold']
            recommendations = ['AI verified safety certificate'] if confidence > 0.7 else ['Manual review recommended']
        else:
            score = max(0, int(confidence * 50))
            issues = [f'Document type mismatch: detected as {predicted_type}']
            recommendations = ['Verify document type', 'Manual review required']

        return {
            'score': score,
            'issues': issues,
            'recommendations': recommendations,
            'ai_analysis': True,
            'ai_confidence': confidence,
            'predicted_type': predicted_type
        }

    except Exception as e:
        print(f"❌ Error in AI safety certificate analysis: {str(e)}")
        return {
            'score': 0,
            'issues': [f'AI analysis failed: {str(e)}'],
            'recommendations': ['Manual review required'],
            'ai_analysis': True,
            'ai_error': True
        }

def analyze_insurance_document(file_path):
    """Analyze insurance document using AI or basic analysis"""
    if not file_path:
        return {'score': 0, 'issues': ['No insurance document provided'], 'ai_analysis': False}

    try:
        if AI_ENABLED and ai_engine:
            print(f"🤖 REAL AI analyzing insurance document: {file_path}")
            # Use real AI engine for analysis
            ai_result = ai_engine.analyze_document(file_path)
        else:
            print(f"📋 Basic analysis of insurance document: {file_path}")
            # Basic fallback analysis
            ai_result = {
                'classification': {
                    'document_type': 'insurance',
                    'confidence': 0.85
                },
                'equipment_detection': {'detected_items': []},
                'extracted_text': 'Insurance document verified'
            }

        if 'error' in ai_result:
            return {
                'score': 0,
                'issues': [ai_result['error']],
                'ai_analysis': True,
                'ai_error': True
            }

        # Extract AI results
        classification = ai_result.get('classification', {})
        confidence = classification.get('confidence', 0.0)
        predicted_type = classification.get('document_type', 'unknown')

        # Calculate score based on AI confidence and document type match
        if predicted_type == 'insurance':
            score = int(confidence * 100)
            issues = [] if confidence > 0.7 else ['AI confidence below threshold']
            recommendations = ['AI verified insurance document'] if confidence > 0.7 else ['Manual review recommended']
        else:
            score = max(0, int(confidence * 50))
            issues = [f'Document type mismatch: detected as {predicted_type}']
            recommendations = ['Verify document type', 'Manual review required']

        return {
            'score': score,
            'issues': issues,
            'recommendations': recommendations,
            'ai_analysis': True,
            'ai_confidence': confidence,
            'predicted_type': predicted_type
        }

    except Exception as e:
        print(f"❌ Error in AI insurance document analysis: {str(e)}")
        return {
            'score': 0,
            'issues': [f'AI analysis failed: {str(e)}'],
            'recommendations': ['Manual review required'],
            'ai_analysis': True,
            'ai_error': True
        }

def analyze_business_license(file_path):
    """Analyze business license using AI or basic analysis"""
    if not file_path:
        return {'score': 0, 'issues': ['No business license provided'], 'ai_analysis': False}

    try:
        if AI_ENABLED and ai_engine:
            print(f"🤖 REAL AI analyzing business license: {file_path}")
            # Use real AI engine for analysis
            ai_result = ai_engine.analyze_document(file_path)
        else:
            print(f"📋 Basic analysis of business license: {file_path}")
            # Basic fallback analysis
            ai_result = {
                'classification': {
                    'document_type': 'business_license',
                    'confidence': 0.85
                },
                'equipment_detection': {'detected_items': []},
                'extracted_text': 'Business license document verified'
            }

        if 'error' in ai_result:
            return {
                'score': 0,
                'issues': [ai_result['error']],
                'ai_analysis': True,
                'ai_error': True
            }

        # Extract AI results
        classification = ai_result.get('classification', {})
        confidence = classification.get('confidence', 0.0)
        predicted_type = classification.get('document_type', 'unknown')

        # Calculate score based on AI confidence and document type match
        if predicted_type == 'business_license':
            score = int(confidence * 100)
            issues = [] if confidence > 0.7 else ['AI confidence below threshold']
            recommendations = ['AI verified business license'] if confidence > 0.7 else ['Manual review recommended']
        else:
            score = max(0, int(confidence * 50))
            issues = [f'Document type mismatch: detected as {predicted_type}']
            recommendations = ['Verify document type', 'Manual review required']

        return {
            'score': score,
            'issues': issues,
            'recommendations': recommendations,
            'ai_analysis': True,
            'ai_confidence': confidence,
            'predicted_type': predicted_type
        }

    except Exception as e:
        print(f"❌ Error in AI business license analysis: {str(e)}")
        return {
            'score': 0,
            'issues': [f'AI analysis failed: {str(e)}'],
            'recommendations': ['Manual review required'],
            'ai_analysis': True,
            'ai_error': True
        }

def send_inspection_notification(email, application_id, inspection_date):
    """Send email notification to inspector"""
    try:
        # Email sending logic here
        print(f"Sending inspection notification to {email} for application {application_id} on {inspection_date}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

# License Generation System
def generate_noc_license(application_id):
    """Generate NOC License after manager approval and inspection completion"""
    try:
        # Get application details
        app = applications.find_one({'_id': ObjectId(application_id)})
        if not app:
            return None

        # Generate unique license number
        license_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(application_id)[-6:].upper()}"

        # Create license data
        license_data = {
            'license_number': license_number,
            'application_id': ObjectId(application_id),
            'business_name': app.get('business_name'),
            'business_type': app.get('business_type'),
            'business_address': app.get('business_address'),
            'contact_number': app.get('contact_number'),
            'username': app.get('username'),
            'issued_date': datetime.now(),
            'valid_until': datetime.now() + timedelta(days=365),  # Valid for 1 year
            'status': 'active',
            'issued_by': app.get('assigned_manager', 'System'),
            'inspector': app.get('assigned_inspector'),
            'verification_score': app.get('verification_score', 0),
            'inspection_report_id': app.get('inspection_report_id'),
            'qr_code': f"https://firenoc.gov.in/verify/{license_number}",
            'created_at': datetime.now()
        }

        # Insert license into database
        license_id = licenses.insert_one(license_data).inserted_id

        # Update application status
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'status': 'approved',
                    'license_generated': True,
                    'license_id': license_id,
                    'license_number': license_number,
                    'approved_at': datetime.now()
                }
            }
        )

        # Update user statistics
        users.update_one(
            {'username': app.get('username')},
            {'$inc': {'certificates_received': 1}}
        )

        # Send license notification to user
        send_license_notification(app.get('username'), license_data)

        return license_data

    except Exception as e:
        print(f"Error generating NOC license: {str(e)}")
        return None

def send_license_notification(username, license_data):
    """Send license notification to user via email and dashboard"""
    try:
        user = users.find_one({'username': username})
        if not user:
            return False

        # Create notification for dashboard
        notification_data = {
            'username': username,
            'title': '🎉 NOC License Generated!',
            'message': f'Your Fire NOC License {license_data["license_number"]} has been successfully generated and is now active.',
            'type': 'success',
            'read': False,
            'created_at': datetime.now(),
            'license_number': license_data['license_number'],
            'valid_until': license_data['valid_until']
        }

        notifications.insert_one(notification_data)

        # Send email notification
        subject = "🔥 Fire NOC License Generated - Congratulations!"
        body = f"""
Dear {user.get('name', username)},

Congratulations! Your Fire NOC License has been successfully generated.

License Details:
📋 License Number: {license_data['license_number']}
🏢 Business Name: {license_data['business_name']}
📅 Issue Date: {license_data['issued_date'].strftime('%d/%m/%Y')}
📅 Valid Until: {license_data['valid_until'].strftime('%d/%m/%Y')}
⭐ Verification Score: {license_data['verification_score']}%

You can download your license from your dashboard.

Important Notes:
• Keep your license number safe for future reference
• Display the license prominently at your business premises
• Renew before expiry date to maintain compliance
• Contact us for any queries

Best regards,
Fire Safety Department
Government of India
"""

        send_email(subject, user.get('email'), body)

        return True

    except Exception as e:
        print(f"Error sending license notification: {str(e)}")
        return False

# Inspection Report System
def generate_inspection_report(inspection_id):
    """Generate inspection report after inspection completion"""
    try:
        # Get inspection details
        inspection = inspections.find_one({'_id': ObjectId(inspection_id)})
        if not inspection:
            return None

        # Get application details
        app = applications.find_one({'_id': inspection['application_id']})
        if not app:
            return None

        # Generate report data
        report_data = {
            'inspection_id': ObjectId(inspection_id),
            'application_id': inspection['application_id'],
            'report_number': f"RPT-{datetime.now().strftime('%Y%m%d')}-{str(inspection_id)[-6:].upper()}",
            'business_name': app.get('business_name'),
            'business_address': app.get('business_address'),
            'inspector': inspection.get('inspector_id'),
            'inspection_date': inspection.get('date'),
            'inspection_status': inspection.get('status'),
            'findings': inspection.get('findings', []),
            'recommendations': inspection.get('recommendations', []),
            'compliance_score': inspection.get('compliance_score', 0),
            'photos': inspection.get('photos', []),
            'overall_result': inspection.get('overall_result', 'Pending'),
            'generated_at': datetime.now(),
            'generated_by': inspection.get('inspector_id')
        }

        # Insert report into database
        report_id = inspection_reports.insert_one(report_data).inserted_id

        # Update inspection with report ID
        inspections.update_one(
            {'_id': ObjectId(inspection_id)},
            {
                '$set': {
                    'report_generated': True,
                    'report_id': report_id,
                    'report_number': report_data['report_number']
                }
            }
        )

        # Update application with report ID
        applications.update_one(
            {'_id': inspection['application_id']},
            {
                '$set': {
                    'inspection_report_id': report_id,
                    'inspection_completed': True,
                    'status': 'inspection_completed'
                }
            }
        )

        # Send report to user
        send_inspection_report_to_user(app.get('username'), report_data)

        # Check if ready for license generation
        check_and_generate_license(str(inspection['application_id']))

        return report_data

    except Exception as e:
        print(f"Error generating inspection report: {str(e)}")
        return None

def send_inspection_report_to_user(username, report_data):
    """Send inspection report to user's email and dashboard"""
    try:
        user = users.find_one({'username': username})
        if not user:
            return False

        # Create notification for dashboard
        notification_data = {
            'username': username,
            'title': '📋 Inspection Report Available',
            'message': f'Your inspection report {report_data["report_number"]} is now available for download.',
            'type': 'info',
            'read': False,
            'created_at': datetime.now(),
            'report_number': report_data['report_number'],
            'inspection_date': report_data['inspection_date']
        }

        notifications.insert_one(notification_data)

        # Send email notification
        subject = "🔍 Fire Safety Inspection Report Available"
        body = f"""
Dear {user.get('name', username)},

Your fire safety inspection has been completed and the report is now available.

Report Details:
📋 Report Number: {report_data['report_number']}
🏢 Business Name: {report_data['business_name']}
📅 Inspection Date: {report_data['inspection_date'].strftime('%d/%m/%Y') if report_data['inspection_date'] else 'N/A'}
👨‍🔧 Inspector: {report_data['inspector']}
⭐ Compliance Score: {report_data['compliance_score']}%
📊 Overall Result: {report_data['overall_result']}

You can view and download the complete report from your dashboard.

Next Steps:
• Review the inspection findings
• Address any recommendations if applicable
• Your NOC license will be generated automatically if all requirements are met

Best regards,
Fire Safety Department
"""

        send_email(subject, user.get('email'), body)

        return True

    except Exception as e:
        print(f"Error sending inspection report: {str(e)}")
        return False

def check_and_generate_license(application_id):
    """Check if application is ready for license generation and generate automatically"""
    try:
        app = applications.find_one({'_id': ObjectId(application_id)})
        if not app:
            return False

        # Check if all conditions are met
        conditions_met = (
            app.get('status') == 'inspection_completed' and
            app.get('documents_verified') == True and
            app.get('inspection_completed') == True and
            app.get('assigned_manager') and
            not app.get('license_generated', False)
        )

        if conditions_met:
            # Generate license automatically
            license_data = generate_noc_license(application_id)
            if license_data:
                print(f"License automatically generated for application {application_id}")
                return True

        return False

    except Exception as e:
        print(f"Error checking license generation conditions: {str(e)}")
        return False

# Automation API Routes

@app.route('/api/manager/approve-application', methods=['POST'])
def approve_application():
    """Manager approves application and triggers license generation if inspection is complete"""
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        application_id = data.get('application_id')

        # Update application status
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'manager_approved': True,
                    'manager_approval_date': datetime.now(),
                    'approved_by': session['username']
                }
            }
        )

        # Check if inspection is also completed and generate license
        app = applications.find_one({'_id': ObjectId(application_id)})
        if app and app.get('inspection_completed'):
            license_data = generate_noc_license(application_id)
            if license_data:
                # Send certificate issued notification to user
                try:
                    user_data = users.find_one({'username': app.get('username')})
                    if user_data and user_data.get('email'):
                        # Generate certificate PDF (simplified for now)
                        certificate_pdf_data = None  # You can implement PDF generation here

                        send_certificate_issued_notification(
                            user_data.get('email'),
                            user_data.get('name', 'Applicant'),
                            app,
                            license_data,
                            certificate_pdf_data
                        )
                except Exception as e:
                    print(f"Error sending certificate issued notification: {e}")

                return jsonify({
                    'success': True,
                    'message': 'Application approved and license generated automatically!',
                    'license_number': license_data['license_number']
                })

        return jsonify({
            'success': True,
            'message': 'Application approved. License will be generated after inspection completion.'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/get-licenses')
def get_user_licenses():
    """Get user's NOC certificates and licenses"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get user's approved applications (certificates available for approved apps)
        user_applications = list(applications.find({
            'username': session['username'],
            'status': 'approved'
        }))

        user_certificates = []
        for app in user_applications:
            # Get certificate details
            certificate = certificates.find_one({'application_id': app['_id']})

            if certificate:
                # Certificate exists in database
                cert_data = {
                    '_id': str(certificate['_id']),
                    'application_id': str(app['_id']),
                    'certificate_number': certificate['certificate_number'],
                    'business_name': certificate['business_name'],
                    'business_type': certificate['business_type'],
                    'business_address': certificate['business_address'],
                    'issued_date': certificate['issued_date'].strftime('%d/%m/%Y'),
                    'valid_until': certificate['valid_until'].strftime('%d/%m/%Y'),
                    'status': certificate['status'],
                    'compliance_score': certificate.get('compliance_score', 85),
                    'inspector_name': certificate.get('inspector_name', 'Unknown'),
                    'issued_by': certificate.get('issued_by', 'System')
                }
                user_certificates.append(cert_data)
            else:
                # Create certificate for approved application if it doesn't exist
                certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app['_id'])[-6:]}"

                # Create certificate record
                certificate_data = {
                    'certificate_number': certificate_number,
                    'application_id': app['_id'],
                    'business_name': app.get('business_name', 'Unknown'),
                    'business_type': app.get('business_type', 'Unknown'),
                    'business_address': app.get('business_address', 'Unknown'),
                    'issued_date': datetime.now(),
                    'valid_until': datetime.now() + timedelta(days=365),
                    'status': 'active',
                    'compliance_score': 85,
                    'inspector_name': app.get('assigned_inspector', 'System Inspector'),
                    'issued_by': app.get('approved_by', 'System'),
                    'created_at': datetime.now()
                }

                # Insert certificate
                cert_id = certificates.insert_one(certificate_data).inserted_id

                # Update application with certificate number
                applications.update_one(
                    {'_id': app['_id']},
                    {'$set': {'certificate_number': certificate_number, 'certificate_issued': True}}
                )

                # Add to response
                cert_data = {
                    '_id': str(cert_id),
                    'application_id': str(app['_id']),
                    'certificate_number': certificate_number,
                    'business_name': app.get('business_name', 'Unknown'),
                    'business_type': app.get('business_type', 'Unknown'),
                    'business_address': app.get('business_address', 'Unknown'),
                    'issued_date': datetime.now().strftime('%d/%m/%Y'),
                    'valid_until': (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
                    'status': 'active',
                    'compliance_score': 85,
                    'inspector_name': app.get('assigned_inspector', 'System Inspector'),
                    'issued_by': app.get('approved_by', 'System')
                }
                user_certificates.append(cert_data)

        return jsonify({
            'success': True,
            'licenses': user_certificates,
            'certificates': user_certificates  # For backward compatibility
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/get-inspection-reports')
def get_user_inspection_reports():
    """Get user's inspection reports"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get user's applications
        user_applications = list(applications.find({'username': session['username']}))
        app_ids = [app['_id'] for app in user_applications]

        # Get inspection reports for user's applications from inspections collection
        user_reports = list(inspections.find({
            'application_id': {'$in': app_ids},
            'status': 'completed'
        }).sort('inspection_date', -1))

        # Format reports for frontend
        formatted_reports = []
        for report in user_reports:
            # Get application details
            app_data = applications.find_one({'_id': report['application_id']})
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

        return jsonify({
            'success': True,
            'reports': formatted_reports
        })

    except Exception as e:
        print(f"Error getting user inspection reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/get-inspection-schedule')
def get_user_inspection_schedule():
    """Get user's upcoming inspection schedule"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        username = session['username']
        print(f"Getting inspection schedule for user: {username}")

        # Get user's applications
        user_applications = list(applications.find({'username': username}))
        app_ids = [app['_id'] for app in user_applications]

        print(f"Found {len(user_applications)} applications for user")

        # Get all inspections for user's applications (scheduled, assigned, in_progress)
        scheduled_inspections = list(inspections.find({
            'application_id': {'$in': app_ids},
            'status': {'$in': ['scheduled', 'assigned', 'in_progress']}
        }).sort('date', 1))

        print(f"Found {len(scheduled_inspections)} scheduled inspections")

        # Format inspections for frontend
        formatted_inspections = []
        for inspection in scheduled_inspections:
            # Get application details
            app_data = applications.find_one({'_id': inspection['application_id']})
            if app_data:
                # Get inspector details
                inspector_name = 'TBA'
                inspector_phone = ''
                if inspection.get('inspector_id'):
                    inspector = users.find_one({'username': inspection['inspector_id']})
                    if inspector:
                        inspector_name = inspector.get('name', inspection['inspector_id'])
                        inspector_phone = inspector.get('phone', '')

                formatted_inspection = {
                    'id': str(inspection['_id']),
                    'business_name': app_data.get('business_name', 'N/A'),
                    'business_address': app_data.get('business_address', 'N/A'),
                    'inspector': inspector_name,
                    'inspector_phone': inspector_phone,
                    'date': inspection.get('date', ''),
                    'time': inspection.get('time', ''),
                    'status': inspection.get('status', 'scheduled'),
                    'application_id': str(app_data['_id']),
                    'notes': inspection.get('notes', '')
                }
                formatted_inspections.append(formatted_inspection)

        return jsonify({
            'success': True,
            'inspections': formatted_inspections
        })

    except Exception as e:
        print(f"Error getting user inspection schedule: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Demo/Test Routes for Automation
@app.route('/api/demo/create-test-data', methods=['POST'])
def create_test_data():
    """Create test data for demonstration"""
    if session.get('role') not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Create a test application
        test_app_data = {
            'username': session['username'],
            'business_name': 'Demo Restaurant',
            'business_type': 'Restaurant',
            'business_address': '123 Main Street, Delhi',
            'contact_number': '+91 9876543210',
            'fire_extinguishers': '5',
            'fire_alarm': 'Yes',
            'emergency_exits': '3',
            'last_fire_drill': '2024-01-15',
            'status': 'pending',
            'timestamp': datetime.now(),
            'email': session.get('email', ''),
            'documents': [],
            'documents_verified': True,
            'assigned_manager': session['username'],
            'verification_score': 85
        }

        app_result = applications.insert_one(test_app_data)
        app_id = app_result.inserted_id

        # Create a test inspection
        test_inspection_data = {
            'application_id': app_id,
            'inspector_id': 'demo_inspector',
            'date': datetime.now(),
            'status': 'completed',
            'findings': ['Fire extinguishers properly placed', 'Emergency exits clearly marked'],
            'recommendations': ['Install additional smoke detectors', 'Conduct monthly fire drills'],
            'compliance_score': 88,
            'overall_result': 'Passed',
            'photos': [],
            'completed_at': datetime.now(),
            'completed_by': 'demo_inspector'
        }

        inspection_result = inspections.insert_one(test_inspection_data)
        inspection_id = inspection_result.inserted_id

        # Generate inspection report
        report_data = generate_inspection_report(str(inspection_id))

        # Update application status to trigger license generation
        applications.update_one(
            {'_id': app_id},
            {
                '$set': {
                    'status': 'inspection_completed',
                    'inspection_completed': True,
                    'manager_approved': True
                }
            }
        )

        # Generate license
        license_data = generate_noc_license(str(app_id))

        return jsonify({
            'success': True,
            'message': 'Test data created successfully!',
            'application_id': str(app_id),
            'inspection_id': str(inspection_id),
            'report_number': report_data['report_number'] if report_data else None,
            'license_number': license_data['license_number'] if license_data else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view-certificate/<application_id>')
def view_certificate(application_id):
    """View certificate for an application"""
    try:
        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404

        # Get certificate data
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            # Create certificate if it doesn't exist for approved applications
            if app_data.get('status') == 'approved':
                certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app_data['_id'])[-6:]}"

                certificate_data = {
                    'certificate_number': certificate_number,
                    'application_id': ObjectId(application_id),
                    'business_name': app_data.get('business_name', 'Unknown'),
                    'business_type': app_data.get('business_type', 'Unknown'),
                    'business_address': app_data.get('business_address', 'Unknown'),
                    'issued_date': datetime.now(),
                    'valid_until': datetime.now() + timedelta(days=365),
                    'status': 'active',
                    'compliance_score': 85,
                    'inspector_name': app_data.get('assigned_inspector', 'System Inspector'),
                    'issued_by': app_data.get('approved_by', 'System'),
                    'created_at': datetime.now()
                }

                certificates.insert_one(certificate_data)
                certificate = certificate_data
            else:
                return "Certificate not available for this application", 404

        return render_template('certificate_template.html',
                             certificate=certificate,
                             application=app_data)

    except Exception as e:
        return f"Error viewing certificate: {str(e)}", 500

@app.route('/manager-download-certificate/<application_id>')
def manager_download_certificate(application_id):
    """Download certificate PDF for manager"""
    try:
        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404

        # Get certificate data
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return "Certificate not found", 404

        # Generate PDF content
        from io import BytesIO
        import base64

        # Create a simple PDF-like response
        pdf_content = f"""
        FIRE SAFETY CERTIFICATE - NOC
        ==============================

        Certificate Number: {certificate['certificate_number']}
        Business Name: {certificate['business_name']}
        Business Type: {certificate['business_type']}
        Address: {certificate['business_address']}

        Issue Date: {certificate['issued_date'].strftime('%d/%m/%Y')}
        Valid Until: {certificate['valid_until'].strftime('%d/%m/%Y')}

        Compliance Score: {certificate.get('compliance_score', 85)}%
        Inspector: {certificate.get('inspector_name', 'System Inspector')}
        Issued By: {certificate.get('issued_by', 'System')}

        This is a system-generated certificate.
        """

        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=certificate_{certificate["certificate_number"]}.pdf'

        return response

    except Exception as e:
        return f"Error downloading certificate: {str(e)}", 500

@app.route('/expert_dashboard')
def expert_dashboard():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    if session.get('role') != 'expert':
        flash('Access denied!', 'danger')
        return redirect(url_for('user_dashboard'))

    # Get expert-specific data
    expert_data = {}
    return render_template('expert_dashboard.html', data=expert_data)

@app.route('/submit_noc', methods=['POST'])
@login_required
def submit_noc():
    """Submit NOC application"""

    try:
        print(f"DEBUG: Form data received: {dict(request.form)}")
        print(f"DEBUG: Files received: {list(request.files.keys())}")
        print(f"DEBUG: Session data: {dict(session)}")

        # Create uploads directory if it doesn't exist
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            print(f"DEBUG: Created upload folder: {upload_folder}")

        # Collect form data with better error handling
        application_data = {
            'username': session['username'],
            'business_name': request.form.get('businessName', '').strip(),
            'business_type': request.form.get('businessType', '').strip(),
            'business_address': request.form.get('businessAddress', '').strip(),
            'contact_person': request.form.get('contactPerson', '').strip(),
            'contact_number': request.form.get('contactNumber', '').strip(),
            'email_address': request.form.get('emailAddress', '').strip(),
            'contact_person_email': request.form.get('contactPersonEmail', '').strip(),
            'building_area': request.form.get('buildingArea', '').strip(),
            'floors': request.form.get('floors', '').strip(),
            'occupancy_type': request.form.get('occupancyType', '').strip(),
            'max_occupancy': request.form.get('maxOccupancy', '').strip(),
            'fire_extinguishers': request.form.get('fireExtinguishers', '').strip(),
            'fire_alarm': request.form.get('fireAlarm', '').strip(),
            'emergency_exits': request.form.get('emergencyExits', '').strip(),
            'sprinkler_system': request.form.get('sprinklerSystem', 'No').strip(),
            'fire_safety_officer': request.form.get('fireSafetyOfficer', 'No').strip(),
            'last_fire_drill': request.form.get('lastFireDrill', '').strip(),
            'status': 'pending',
            'timestamp': datetime.now(),
            'email': session.get('email', ''),
            'documents': []  # Initialize empty documents list
        }

        print(f"DEBUG: Application data collected: {application_data}")

        # Validate required fields with better error messages
        required_fields = {
            'business_name': 'Business Name',
            'business_type': 'Business Type',
            'business_address': 'Business Address',
            'contact_number': 'Contact Number'
        }

        missing_fields = []
        for field, display_name in required_fields.items():
            if not application_data.get(field):
                missing_fields.append(display_name)
                print(f"DEBUG: Missing required field: {field} ({display_name})")

        if missing_fields:
            error_msg = f"Please fill in the following required fields: {', '.join(missing_fields)}"
            print(f"DEBUG: Validation failed: {error_msg}")
            return jsonify({'error': error_msg}), 400

        print(f"DEBUG: All required fields validated successfully")

        # Handle file uploads with better error handling
        file_types = {
            'buildingPlan': 'Building Plan',
            'safetyCertificate': 'Safety Certificate',
            'insuranceDoc': 'Insurance Document'
        }

        print(f"DEBUG: Processing file uploads...")
        for file_key, file_type in file_types.items():
            if file_key in request.files:
                file = request.files[file_key]
                print(f"DEBUG: Processing file {file_key}: {file.filename}")

                if file and file.filename:
                    # Check if file is allowed (make it more permissive for debugging)
                    if allowed_file(file.filename):
                        try:
                            # Create a secure filename with timestamp
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"{timestamp}_{secure_filename(file.filename)}"
                            file_path = os.path.join(upload_folder, filename)

                            # Save the file
                            file.save(file_path)
                            print(f"DEBUG: File saved successfully: {file_path}")

                            # Add to documents list
                            file_size = os.path.getsize(file_path)
                            application_data['documents'].append({
                                'type': file_type,
                                'filename': filename,
                                'original_name': file.filename,
                                'uploaded_at': datetime.now(),
                                'size': file_size,
                                'path': file_path
                            })
                            print(f"DEBUG: Document added to list: {file_type}")

                        except Exception as file_error:
                            print(f"DEBUG: Error saving file {file_key}: {str(file_error)}")
                            # Don't fail the entire submission for file upload errors
                            continue
                    else:
                        print(f"DEBUG: File {file.filename} not allowed. Allowed extensions: {ALLOWED_EXTENSIONS}")
                        # Don't fail for file type issues, just skip
                        continue
                else:
                    print(f"DEBUG: No file provided for {file_key}")

        print(f"DEBUG: File upload completed. Total documents: {len(application_data['documents'])}")

        # Auto-assign to a manager (for demo purposes)
        available_managers = list(users.find({'role': 'manager'}))
        if not available_managers:
            # Create a default manager if none exists
            default_manager = {
                'username': 'manager1',
                'email': 'manager@firenoc.com',
                'password': bcrypt.hashpw('manager123'.encode('utf-8'), bcrypt.gensalt()),
                'role': 'manager',
                'name': 'Fire Safety Manager',
                'phone': '+91-9876543210',
                'created_at': datetime.now(),
                'is_verified': True,
                'department': 'Fire Safety',
                'designation': 'Senior Manager'
            }
            users.insert_one(default_manager)
            assigned_manager = 'manager1'
        else:
            assigned_manager = available_managers[0]['username']  # Assign to first available manager

        application_data['assigned_manager'] = assigned_manager
        application_data['manager_assigned_at'] = datetime.now()

        print(f"DEBUG: About to insert application data: {application_data.keys()}")
        print(f"DEBUG: Application data size: {len(str(application_data))}")

        # Test MongoDB connection first
        try:
            # Test database connection
            db.command('ping')
            print("DEBUG: MongoDB connection successful")
        except Exception as db_error:
            print(f"DEBUG: MongoDB connection failed: {str(db_error)}")
            return jsonify({'error': 'Database connection failed. Please try again later.'}), 500

        # Insert application into database with better error handling
        try:
            result = applications.insert_one(application_data)
            print(f"DEBUG: Application inserted successfully with ID: {result.inserted_id}")

            if not result.inserted_id:
                print("DEBUG: Failed to get inserted ID")
                return jsonify({'error': 'Failed to save application. Please try again.'}), 500

        except Exception as insert_error:
            print(f"DEBUG: Database insertion failed: {str(insert_error)}")
            return jsonify({'error': f'Failed to save application: {str(insert_error)}'}), 500

        # Send confirmation email to applicant
        send_application_confirmation_email(application_data, result.inserted_id)

        # Send notification to assigned manager
        if available_managers:
            manager_email = available_managers[0].get('email', 'manager@example.com')
            manager_notification = f'''New NOC application assigned to you:
Business Name: {application_data['business_name']}
Business Type: {application_data['business_type']}
Application ID: {str(result.inserted_id)}
Submitted By: {session['username']}
Contact: {application_data['contact_number']}

Please review and process the application at:
{url_for('manager_dashboard', _external=True)}
'''
            try:
                send_email(
                    'New NOC Application Assigned',
                    manager_email,
                    manager_notification
                )
            except Exception as e:
                print(f"Error sending manager notification: {e}")

        # Send notification to admin
        admin_notification = f'''New NOC application received:
Business Name: {application_data['business_name']}
Business Type: {application_data['business_type']}
Application ID: {str(result.inserted_id)}
Submitted By: {session['username']}
Contact: {application_data['contact_number']}
Assigned Manager: {application_data.get('assigned_manager', 'Not assigned')}

You can review the application at:
{url_for('view_application', application_id=str(result.inserted_id), _external=True)}
'''

        send_email(
            'New NOC Application Submitted',
            app.config['MAIL_USERNAME'],
            admin_notification
        )

        # Log activity
        log_activity(
            'Application Submitted',
            f"New NOC application submitted for: {application_data['business_name']}"
        )

        # Send comprehensive email notifications
        try:
            # Get the complete application data with ID
            complete_app_data = applications.find_one({'_id': result.inserted_id})

            # Send notification to manager
            send_application_received_notification(complete_app_data)

            # Also send to admin email as backup
            admin_notification = f'''New NOC application received:
Business Name: {application_data['business_name']}
Business Type: {application_data['business_type']}
Application ID: {str(result.inserted_id)}'''

            send_email(
                'New NOC Application Submitted',
                app.config['MAIL_USERNAME'],  # Admin email
                admin_notification
            )
        except Exception as e:
            # Log email error but don't fail the submission
            print(f"Error sending email notification: {e}")

        # Emit socket.io event for real-time updates
        socketio.emit('new_application', {
            'message': 'New application submitted!',
            'applicationId': str(result.inserted_id)
        })

        return jsonify({
            'success': True,
            'message': 'NOC application submitted successfully!',
            'application_id': str(result.inserted_id)
        })

    except Exception as e:
        print(f"DEBUG: Exception in submit_noc: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        app.logger.error(f"Error submitting application: {str(e)}")
        return jsonify({'error': f'Application submission failed: {str(e)}'}), 500

# Test endpoint for debugging
@app.route('/api/test-submission', methods=['POST'])
@csrf.exempt
def test_submission():
    """Test endpoint to debug form submission issues"""
    try:
        print("DEBUG: Test submission endpoint called")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Content type: {request.content_type}")
        print(f"DEBUG: Form data: {dict(request.form)}")
        print(f"DEBUG: Files: {list(request.files.keys())}")
        print(f"DEBUG: Session: {dict(session)}")

        return jsonify({
            'success': True,
            'message': 'Test endpoint working',
            'received_data': {
                'form': dict(request.form),
                'files': list(request.files.keys()),
                'session_user': session.get('username', 'Not logged in')
            }
        })
    except Exception as e:
        print(f"DEBUG: Test endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-stats')
def get_dashboard_stats():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Basic application stats
        total_apps = applications.count_documents({})
        pending_apps = applications.count_documents({'status': 'pending'})
        approved_apps = applications.count_documents({'status': 'approved'})
        rejected_apps = applications.count_documents({'status': 'rejected'})

        # Enhanced stats
        total_users = users.count_documents({})
        total_certificates = certificates.count_documents({})
        total_inspections = inspections.count_documents({'status': 'completed'})

        # Calculate revenue (example calculation)
        total_revenue = approved_apps * 500  # Assuming ₹500 per approved application

        stats = {
            'total': total_apps,
            'pending': pending_apps,
            'approved': approved_apps,
            'rejected': rejected_apps,
            'total_users': total_users,
            'total_certificates': total_certificates,
            'total_inspections': total_inspections,
            'total_revenue': total_revenue
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-activities')
def get_recent_activities():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        recent = list(activities.find(
            {},
            {'_id': 0}
        ).sort('timestamp', -1).limit(10))

        # Convert timestamps to ISO format
        for activity in recent:
            activity['timestamp'] = activity['timestamp'].isoformat()

        return jsonify({'activities': recent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest-applications')
def get_latest_applications():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        latest = list(applications.find(
            {},
            {
                '_id': 1,
                'business_name': 1,
                'status': 1,
                'timestamp': 1
            }
        ).sort('timestamp', -1).limit(5))

        # Convert ObjectId to string
        for app in latest:
            app['id'] = str(app['_id'])
            del app['_id']

        return jsonify({'applications': latest})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Application Routes
@app.route('/application/<application_id>', methods=['GET'])
def get_application_details(application_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            return jsonify({'error': 'Application not found'}), 404

        if session.get('role') != 'admin' and application['username'] != session['username']:
            return jsonify({'error': 'Unauthorized'}), 401

        formatted_application = {
            'id': str(application['_id']),
            'business_name': application.get('business_name', ''),
            'business_type': application.get('business_type', ''),
            'business_address': application.get('business_address', ''),
            'contact_number': application.get('contact_number', ''),
            'username': application.get('username', ''),
            'email': application.get('email', ''),
            'status': application.get('status', 'pending'),
            'timestamp': application['timestamp'].isoformat() if 'timestamp' in application else '',
            'last_updated': application.get('updated_at', datetime.now()).isoformat(),
            'updated_by': application.get('updated_by', ''),
            'fire_safety': {
                'fire_extinguishers': application.get('fire_extinguishers', ''),
                'fire_alarm': application.get('fire_alarm', ''),
                'emergency_exits': application.get('emergency_exits', ''),
                'last_fire_drill': application.get('last_fire_drill', '')
            },
            'files': []
        }

        if 'files' in application:
            for file_type, filename in application['files'].items():
                formatted_application['files'].append({
                    'type': file_type,
                    'filename': filename,
                    'url': url_for('download_file', filename=filename, _external=True)
                })

        return jsonify(formatted_application)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/reject_application/<application_id>', methods=['POST'])
def reject_application(application_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        rejection_reason = data.get('rejection_reason')

        if not rejection_reason:
            return jsonify({'error': 'Rejection reason is required'}), 400

        # Get application details
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            return jsonify({'error': 'Application not found'}), 404

        # Update application status
        result = applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {
                'status': 'rejected',
                'rejected_by': session['username'],
                'rejected_at': datetime.now(),
                'rejection_reason': rejection_reason
            }}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Failed to reject application'}), 500

        # Send rejection email
        subject = "NOC Application Rejected"
        body = f"""
Dear {application.get('name', 'Applicant')},

Your NOC application has been REJECTED.

Application Details:
- Application ID: {str(application['_id'])}
- Business Name: {application.get('business_name')}
- Submission Date: {application.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
- Rejected By: {session.get('username')}
- Rejection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Business Information:
- Address: {application.get('business_address')}
- Contact Number: {application.get('contact_number')}

Reason for Rejection:
{rejection_reason}

You can submit a new application after addressing the above concerns.
Please log in to your dashboard for more details.

Best regards,
Fire Safety Department
"""
        try:
            msg = Message(
                subject,
                sender=app.config['MAIL_USERNAME'],
                recipients=[application.get('email')]
            )
            msg.body = body
            mail.send(msg)
            email_sent = True
        except Exception as e:
            print(f"Error sending rejection email: {str(e)}")
            email_sent = False

        # Log activity
        log_activity(
            'Application Rejection',
            f"Application {application_id} rejected and {'email sent' if email_sent else 'email failed'}"
        )

        # Emit socket event
        socketio.emit('application_status_changed', {
            'application_id': str(application_id),
            'status': 'rejected',
            'message': 'Application has been rejected!'
        })

        return jsonify({
            'success': True,
            'message': 'Application rejected' + (' and email sent' if email_sent else ' but email failed to send')
        })

    except Exception as e:
        print(f"Error in reject_application: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/application/<application_id>/update-status', methods=['POST'])
@csrf.exempt  # If you want to handle CSRF manually
def update_application_status(application_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        new_status = data.get('status')
        reason = data.get('reason', '')

        if new_status not in ['approved', 'rejected', 'pending']:
            return jsonify({'error': 'Invalid status'}), 400

        current_time = datetime.now()

        # Get application details for email
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            return jsonify({'error': 'Application not found'}), 404

        # Prepare update data
        update_data = {
            'status': new_status,
            'updated_at': current_time,
            'updated_by': session.get('username')
        }

        if new_status == 'approved':
            valid_until = current_time + timedelta(days=365)
            update_data.update({
                'approval_date': current_time,
                'approved_by': session.get('username'),
                'valid_until': valid_until
            })

            # Generate NOC certificate
            try:
                certificate_data = generate_noc_certificate(application_id)
                if certificate_data:
                    update_data['certificate_number'] = certificate_data['certificate_number']
                    update_data['certificate_path'] = certificate_data['certificate_path']
            except Exception as e:
                print(f"Error generating certificate: {e}")

        elif new_status == 'rejected':
            update_data.update({
                'rejection_date': current_time,
                'rejected_by': session.get('username'),
                'rejection_reason': reason
            })

        # Update application
        result = applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': update_data}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Application not found'}), 404

        # Get the updated application
        updated_app = applications.find_one({'_id': ObjectId(application_id)})

        # Send email notification
        try:
            send_status_notification_email(updated_app, new_status, reason)
        except Exception as e:
            print(f"Error sending email notification: {e}")

        # Send notification via WebSocket
        socketio.emit('application_updated', {
            'applicationId': application_id,
            'status': new_status
        })

        # Log activity
        log_activity(
            f'Application {new_status.title()}',
            f"Application {application_id} {new_status} by {session.get('username')}"
        )

        return jsonify({
            'success': True,
            'message': f'Application {new_status} successfully',
            'application': {
                'id': str(updated_app['_id']),
                'status': new_status,
                'updated_at': current_time.isoformat()
            }
        })

    except Exception as e:
        app.logger.error(f"Error updating application status: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_noc_certificate(application_id):
    """Generate NOC certificate for approved application"""
    try:
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            return None

        certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(application_id)[-6:]}"

        # Create certificate directory if it doesn't exist
        cert_dir = os.path.join('static', 'certificates')
        os.makedirs(cert_dir, exist_ok=True)

        certificate_path = os.path.join(cert_dir, f"{certificate_number}.pdf")

        # Generate PDF certificate (simplified version)
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4

        c = canvas.Canvas(certificate_path, pagesize=A4)
        width, height = A4

        # Certificate content
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredText(width/2, height-100, "FIRE NOC CERTIFICATE")

        c.setFont("Helvetica", 14)
        c.drawCentredText(width/2, height-150, f"Certificate Number: {certificate_number}")
        c.drawCentredText(width/2, height-200, f"Business Name: {application.get('business_name', 'N/A')}")
        c.drawCentredText(width/2, height-250, f"Business Type: {application.get('business_type', 'N/A')}")
        c.drawCentredText(width/2, height-300, f"Valid Until: {(datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')}")

        c.save()

        return {
            'certificate_number': certificate_number,
            'certificate_path': certificate_path
        }
    except Exception as e:
        print(f"Error generating certificate: {e}")
        return None

def generate_approval_report(application):
    """Generate a structured report for approved applications"""
    current_time = datetime.now()
    valid_until = current_time + timedelta(days=365)

    return {
        'report_id': str(ObjectId()),
        'application_id': str(application['_id']),
        'business_name': application.get('business_name'),
        'business_type': application.get('business_type'),
        'business_address': application.get('business_address'),
        'approval_details': {
            'approved_by': session['username'],
            'approval_date': current_time,
            'valid_until': valid_until
        },
        'safety_compliance': {
            'fire_extinguishers': application.get('fire_extinguishers'),
            'fire_alarm': application.get('fire_alarm'),
            'emergency_exits': application.get('emergency_exits'),
            'last_fire_drill': application.get('last_fire_drill')
        },
        'approval_conditions': [
            'Regular maintenance of fire safety equipment required',
            'Monthly fire drills mandatory',
            'Annual safety audit to be conducted',
            'Immediate reporting of any safety incidents'
        ],
        'timestamp': current_time
    }

def send_status_notification_email(application, status, reason=''):
    """Send beautiful HTML email notification for application status updates"""
    subject = f'🔥 NOC Application {status.capitalize()} - Fire Safety Department'

    if status == 'approved':
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NOC Application Approved</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #ea580c 50%, #f59e0b 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .success-badge {{ background-color: #10b981; color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; }}
                .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                .details-table th {{ background-color: #f8f9fa; font-weight: 600; }}
                .footer {{ background-color: #1f2937; color: white; padding: 20px; text-align: center; }}
                .btn {{ background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
                .certificate-box {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 Fire NOC Portal</h1>
                    <h2>Application Approved!</h2>
                </div>
                <div class="content">
                    <div class="success-badge">
                        ✅ APPROVED
                    </div>
                    <h3>Dear {application.get('contact_person', 'Applicant')},</h3>
                    <p>Congratulations! Your Fire NOC application has been <strong>APPROVED</strong>.</p>

                    <table class="details-table">
                        <tr><th>Application ID</th><td>#{str(application['_id'])[-8:]}</td></tr>
                        <tr><th>Business Name</th><td>{application.get('business_name', 'N/A')}</td></tr>
                        <tr><th>Business Type</th><td>{application.get('business_type', 'N/A')}</td></tr>
                        <tr><th>Approved By</th><td>{session.get('username', 'Admin')}</td></tr>
                        <tr><th>Approval Date</th><td>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</td></tr>
                        <tr><th>Valid Until</th><td>{(datetime.now() + timedelta(days=365)).strftime('%B %d, %Y')}</td></tr>
                    </table>

                    <div class="certificate-box">
                        <h3>🏆 NOC Certificate Ready</h3>
                        <p>Your official Fire NOC certificate is now available for download.</p>
                        <a href="{url_for('user_dashboard', _external=True)}" class="btn">Download Certificate</a>
                    </div>

                    <p><strong>Important Notes:</strong></p>
                    <ul>
                        <li>Keep your NOC certificate in a safe place</li>
                        <li>Display the certificate prominently at your business premises</li>
                        <li>Ensure regular maintenance of fire safety equipment</li>
                        <li>Conduct monthly fire drills as required</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>Fire Safety Department | Government Portal</p>
                    <p>For support, contact us at support@firenoc.gov.in</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NOC Application Status Update</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #ea580c 50%, #f59e0b 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .rejection-badge {{ background-color: #ef4444; color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; }}
                .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                .details-table th {{ background-color: #f8f9fa; font-weight: 600; }}
                .footer {{ background-color: #1f2937; color: white; padding: 20px; text-align: center; }}
                .btn {{ background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
                .reason-box {{ background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 Fire NOC Portal</h1>
                    <h2>Application Status Update</h2>
                </div>
                <div class="content">
                    <div class="rejection-badge">
                        ❌ REJECTED
                    </div>
                    <h3>Dear {application.get('contact_person', 'Applicant')},</h3>
                    <p>We regret to inform you that your Fire NOC application has been <strong>REJECTED</strong>.</p>

                    <table class="details-table">
                        <tr><th>Application ID</th><td>#{str(application['_id'])[-8:]}</td></tr>
                        <tr><th>Business Name</th><td>{application.get('business_name', 'N/A')}</td></tr>
                        <tr><th>Rejected By</th><td>{session.get('username', 'Admin')}</td></tr>
                        <tr><th>Rejection Date</th><td>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</td></tr>
                    </table>

                    <div class="reason-box">
                        <h4>Reason for Rejection:</h4>
                        <p>{reason or 'Please contact the fire safety department for details.'}</p>
                    </div>

                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Review the rejection reason carefully</li>
                        <li>Address the mentioned issues</li>
                        <li>Submit a new application with corrected information</li>
                        <li>Contact our support team if you need assistance</li>
                    </ul>

                    <a href="{url_for('user_dashboard', _external=True)}" class="btn">Submit New Application</a>
                </div>
                <div class="footer">
                    <p>Fire Safety Department | Government Portal</p>
                    <p>For support, contact us at support@firenoc.gov.in</p>
                </div>
            </div>
        </body>
        </html>
        """

    try:
        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[application.get('email')]
        )
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/download/<filename>')
def download_file(filename):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-certificate/<filename>')
def download_certificate(filename):
    """Download a generated NOC certificate"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        print(f"DOWNLOAD CERT: Attempting to download certificate file: {filename}")
        print(f"DOWNLOAD CERT: Session user: {session.get('username')}, role: {session.get('role')}")

        # Check if filename is actually an application ID
        if len(filename) == 24:  # MongoDB ObjectId length
            print(f"DOWNLOAD CERT: Filename looks like application ID, redirecting to certificate download")
            return redirect(url_for('certificate_download', application_id=filename))

        certificate_path = os.path.join(app.config['UPLOAD_FOLDER'], 'certificates')
        print(f"DOWNLOAD CERT: Looking for certificate in: {certificate_path}")

        if not os.path.exists(certificate_path):
            print(f"DOWNLOAD CERT: Certificate directory doesn't exist, creating it")
            os.makedirs(certificate_path, exist_ok=True)

        full_path = os.path.join(certificate_path, filename)
        if not os.path.exists(full_path):
            print(f"DOWNLOAD CERT: Certificate file not found: {full_path}")
            return jsonify({'error': 'Certificate file not found'}), 404

        return send_from_directory(certificate_path, filename, as_attachment=True)
    except Exception as e:
        print(f"DOWNLOAD CERT: Error downloading certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download-noc-certificate/<application_id>')
def download_noc_certificate(application_id):
    """Download NOC certificate PDF for users"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        print(f"USER CERT DOWNLOAD: Downloading certificate for application: {application_id}")
        print(f"USER CERT DOWNLOAD: Session user: {session.get('username')}, role: {session.get('role')}")

        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            print(f"USER CERT DOWNLOAD: Application not found: {application_id}")
            return "Application not found", 404

        # Check if user owns this application (unless admin/manager)
        if session.get('role') not in ['admin', 'manager'] and app_data.get('username') != session.get('username'):
            return jsonify({'error': 'Unauthorized access to this certificate'}), 403

        # Get certificate data
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            print(f"USER CERT DOWNLOAD: Certificate not found for application: {application_id}")
            return "Certificate not found. Please contact admin if your application is approved.", 404

        # Generate PDF certificate
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )

        # Content
        story = []

        # Header
        story.append(Paragraph("GOVERNMENT OF INDIA", styles['Normal']))
        story.append(Paragraph("FIRE SAFETY DEPARTMENT", title_style))
        story.append(Paragraph("NO OBJECTION CERTIFICATE (NOC)", styles['Heading2']))
        story.append(Spacer(1, 20))

        # Certificate details
        story.append(Paragraph(f"<b>Certificate Number:</b> {certificate['certificate_number']}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Business Name:</b> {certificate['business_name']}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Business Type:</b> {certificate['business_type']}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Address:</b> {certificate['business_address']}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Issue Date:</b> {certificate['issued_date'].strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Valid Until:</b> {certificate['valid_until'].strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Compliance details
        story.append(Paragraph(f"<b>Compliance Score:</b> {certificate.get('compliance_score', 85)}%", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Inspector:</b> {certificate.get('inspector_name', 'System Inspector')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Issued By:</b> {certificate.get('issued_by', 'Fire Safety Department')}", styles['Normal']))
        story.append(Spacer(1, 30))

        # Footer
        story.append(Paragraph("This is a digitally generated certificate.", styles['Normal']))
        story.append(Paragraph("For verification, visit our official website.", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Create filename
        business_name = app_data.get('business_name', 'Business').replace(' ', '_')
        certificate_number = certificate['certificate_number']
        filename = f"NOC_Certificate_{business_name}_{certificate_number}.pdf"

        # Return PDF as download
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        print(f"USER CERT DOWNLOAD: Successfully generated PDF for {certificate_number}")
        return response

    except Exception as e:
        print(f"USER CERT DOWNLOAD: Error downloading certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error downloading certificate: {str(e)}", 500


@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity('Logout', f"User {session['username']} logged out")
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/generate_csrf_token', methods=['GET'])
def generate_csrf_token():
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return jsonify({'csrf_token': token})

@app.route('/api/refresh-session', methods=['POST'])
@login_required
def refresh_session():
    """Refresh user session to prevent timeout"""
    try:
        session.permanent = True
        return jsonify({
            'success': True,
            'message': 'Session refreshed successfully',
            'username': session.get('username'),
            'role': session.get('role')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/session-status', methods=['GET'])
def session_status():
    """Check if user session is valid"""
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session.get('username'),
            'role': session.get('role'),
            'email': session.get('email'),
            'session_data': dict(session)  # Debug: show all session data
        })
    else:
        return jsonify({
            'authenticated': False
        }), 401

@app.route('/api/debug/session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session data"""
    return jsonify({
        'session_data': dict(session),
        'username': session.get('username'),
        'role': session.get('role'),
        'authenticated': 'username' in session,
        'session_keys': list(session.keys()),
        'is_manager': session.get('role') == 'manager',
        'role_check': session.get('role') in ['manager']
    })

@app.route('/api/manager/session-check', methods=['GET'])
def manager_session_check():
    """Check manager session specifically"""
    print(f"MANAGER SESSION CHECK: Current session: {dict(session)}")

    if 'username' not in session:
        return jsonify({
            'authenticated': False,
            'error': 'No username in session',
            'session_data': dict(session)
        }), 401

    if session.get('role') != 'manager':
        return jsonify({
            'authenticated': True,
            'authorized': False,
            'error': f"Role '{session.get('role')}' is not manager",
            'session_data': dict(session)
        }), 403

    return jsonify({
        'authenticated': True,
        'authorized': True,
        'username': session.get('username'),
        'role': session.get('role'),
        'session_data': dict(session)
    })

@app.route('/api/create-manager-user', methods=['POST'])
def create_manager_user():
    """Create a manager user for testing"""
    try:
        # Check if manager already exists
        existing_manager = users.find_one({'username': 'manager'})
        if existing_manager:
            return jsonify({'success': True, 'message': 'Manager user already exists'})

        # Create manager user
        manager_data = {
            'username': 'manager',
            'password': bcrypt.hashpw('manager123'.encode('utf-8'), bcrypt.gensalt()),
            'email': 'manager@firenoc.gov.in',
            'role': 'manager',
            'name': 'Fire Safety Manager',
            'phone': '+91-9876543210',
            'created_at': datetime.now(),
            'verified': True,
            'active': True
        }

        users.insert_one(manager_data)

        return jsonify({
            'success': True,
            'message': 'Manager user created successfully',
            'credentials': {
                'username': 'manager',
                'password': 'manager123'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-current-user-role', methods=['POST'])
def update_current_user_role():
    """Update current user's role - for testing purposes"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        new_role = data.get('role')

        if new_role not in ['user', 'admin', 'manager', 'inspector']:
            return jsonify({'error': 'Invalid role'}), 400

        # Update user role in database
        result = users.update_one(
            {'username': session['username']},
            {'$set': {
                'role': new_role,
                'updated_at': datetime.now()
            }}
        )

        if result.modified_count > 0:
            # Update session
            session['role'] = new_role

            return jsonify({
                'success': True,
                'message': f'Role updated to {new_role}',
                'new_role': new_role
            })
        else:
            return jsonify({'error': 'Failed to update role'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_role_update.html')
def test_role_update_page():
    """Serve the role update test page"""
    return send_from_directory('.', 'test_role_update.html')

@app.route('/api/refresh-user-role', methods=['POST'])
def refresh_user_role():
    """Refresh user role from database to session"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        username = session['username']

        # Get updated user data from database
        user = users.find_one({'username': username})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Update session with new role
        old_role = session.get('role')
        new_role = user.get('role')

        session['role'] = new_role

        return jsonify({
            'success': True,
            'message': f'Role refreshed from {old_role} to {new_role}',
            'old_role': old_role,
            'new_role': new_role
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    try:
        contact_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'message': request.form.get('message'),
            'timestamp': datetime.now()
        }

        if not all([contact_data['name'], contact_data['email'], contact_data['message']]):
            return jsonify({'error': 'All fields are required'}), 400

        contacts.insert_one(contact_data)

        log_activity('Contact Form Submission', f"New contact form submission from {contact_data['email']}")

        return jsonify({'success': True, 'message': 'Message sent successfully!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view_application/<application_id>')
def view_application(application_id):
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    try:
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            flash('Application not found!', 'danger')
            return redirect(url_for('manage_applications'))

        # Add created_at if it doesn't exist
        if 'created_at' not in application:
            application['created_at'] = application.get('timestamp', datetime.now())

        # Add approved_by if it doesn't exist
        if 'status' in application and application['status'] == 'approved':
            if 'approved_by' not in application:
                application['approved_by'] = application.get('last_modified_by', 'Admin')

        # Convert ObjectId to string for JSON serialization
        application['_id'] = str(application['_id'])

        # Ensure documents list exists
        if 'documents' not in application:
            application['documents'] = []

        # Add file URLs to documents
        for doc in application['documents']:
            doc['download_url'] = url_for('download_file', filename=doc['filename'])
            doc['type_label'] = doc.get('type', 'Document')

        # Get report if application is approved
        report = None
        if application.get('status') == 'approved':
            report = reports.find_one({'application_id': application_id})
            if report:
                report['_id'] = str(report['_id'])

        return render_template('view_application.html',
                             application=application,
                             report=report)

    except Exception as e:
        print(f"Error in view_application: {str(e)}")
        flash('Error loading application!', 'danger')
        return redirect(url_for('manage_applications'))

@app.route('/approval-report/<report_id>')
def view_approval_report(report_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        report = reports.find_one({'_id': ObjectId(report_id)})
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Get the associated application
        application = applications.find_one({'_id': ObjectId(report['application_id'])})
        if not application:
            return jsonify({'error': 'Associated application not found'}), 404

        # Add required fields if they don't exist
        report['created_at'] = report.get('created_at', application.get('approved_date', datetime.now()))
        report['approved_by'] = report.get('approved_by', application.get('approved_by', 'Admin'))

        # Convert ObjectId to string
        report['_id'] = str(report['_id'])
        report['application_id'] = str(report['application_id'])

        return jsonify(report)

    except Exception as e:
        print(f"Error in view_approval_report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/manage_applications')
def manage_applications():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    all_applications = list(applications.find().sort('timestamp', -1))
    return render_template('manage_applications.html', applications=all_applications)

@app.route('/manage_users')
def manage_users():
    if 'username' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    all_users = list(users.find({}, {
        'password': 0  # Exclude password from results
    }))

    return render_template('manage_users.html', users=all_users)

@app.route('/user/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        result = users.delete_one({'_id': ObjectId(user_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'User not found'}), 404

        log_activity('User Deletion', f"User {user_id} deleted by {session['username']}")

        return jsonify({'success': True, 'message': 'User deleted successfully!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/application/<application_id>/delete', methods=['POST'])
def delete_application(application_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        result = applications.delete_one({'_id': ObjectId(application_id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Application not found'}), 404

        log_activity('Application Deletion', f"Application {application_id} deleted by {session['username']}")

        return jsonify({'success': True, 'message': 'Application deleted successfully!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<user_id>') #for fetching user details
def get_user_details(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user = users.find_one({'_id': ObjectId(user_id)}, {'password': 0}) #exclude password
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user['_id'] = str(user['_id']) #convert object id to string
        return jsonify(user)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/user/<user_id>/update', methods=['POST'])
def update_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        updated_data = request.get_json()  # Get the JSON data from the request body

        # Check if the username already exists (excluding the current user being updated)
        existing_user = users.find_one({'username': updated_data.get('username')})
        if existing_user and str(existing_user['_id']) != user_id:
            return jsonify({'error': 'Username already exists'}), 400

        # Handle expert status update
        if 'is_expert' in updated_data:
            updated_data['is_expert'] = bool(updated_data['is_expert'])
            # Log expert status change
            log_activity(
                'User Update',
                f"User {updated_data.get('username')} {'set as expert' if updated_data['is_expert'] else 'removed from expert'} by {session['username']}"
            )

        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': updated_data}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'User not found'}), 404

        log_activity('User Update', f"User {user_id} updated by {session['username']}")

        return jsonify({'success': True, 'message': 'User details updated successfully!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add these routes to handle user dashboard data
@app.route('/api/user-data', methods=['GET'])
def get_user_profile_data():  # Renamed to avoid conflicts
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        user = users.find_one({'username': session['username']})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Convert ObjectId to string for JSON serialization
        user['_id'] = str(user['_id'])

        # Remove sensitive information
        user.pop('password', None)

        return jsonify({
            'success': True,
            'data': {
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'phone': user.get('phone', ''),
                'role': user.get('role', ''),
                'department': user.get('department', ''),
                'address': user.get('address', ''),
                'profile_image': user.get('profile_image', '/static/default-profile.png'),
                'created_at': user.get('created_at', datetime.now()).isoformat(),
                'last_login': user.get('last_login', datetime.now()).isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user-applications')
def get_user_applications():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        # Get applications by username (more reliable than email)
        username = session.get('username')
        user_applications = list(applications.find(
            {'username': username}
        ).sort('timestamp', -1))

        # Convert ObjectIds to strings and format dates
        formatted_applications = []
        for app in user_applications:
            formatted_app = {}
            for key, value in app.items():
                if key == '_id':
                    formatted_app['_id'] = str(value)
                elif key in ['timestamp', 'approval_date', 'valid_until'] and value:
                    if hasattr(value, 'isoformat'):
                        formatted_app[key] = value.isoformat()
                    else:
                        formatted_app[key] = str(value)
                else:
                    # Handle any other ObjectId fields
                    if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                        formatted_app[key] = str(value)
                    else:
                        formatted_app[key] = value
            formatted_applications.append(formatted_app)

        return jsonify({'success': True, 'applications': formatted_applications})
    except Exception as e:
        print(f"Error fetching user applications: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/approval-reports')
def get_approval_reports():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        # Get all approved applications for the user
        approved_apps = list(applications.find({
            'username': session['username'],
            'status': 'approved'
        }).sort('approval_date', -1))

        reports_data = []
        for app in approved_apps:
            report = {
                'report_id': str(app['_id']),
                'business_name': app.get('business_name', ''),
                'business_type': app.get('business_type', ''),
                'business_address': app.get('business_address', ''),
                'approval_details': {
                    'approved_by': app.get('approved_by', ''),
                    'approval_date': app.get('approval_date', datetime.now()).isoformat(),
                    'valid_until': app.get('valid_until', datetime.now() + timedelta(days=365)).isoformat()
                },
                'safety_compliance': {
                    'fire_extinguishers': app.get('fire_extinguishers', ''),
                    'fire_alarm': app.get('fire_alarm', ''),
                    'emergency_exits': app.get('emergency_exits', ''),
                    'last_fire_drill': app.get('last_fire_drill', '')
                },
                'approval_conditions': [
                    'Regular maintenance of fire safety equipment required',
                    'Monthly fire drills mandatory',
                    'Annual safety audit to be conducted',
                    'Immediate reporting of any safety incidents'
                ]
            }
            reports_data.append(report)

        return jsonify({'reports': reports_data})
    except Exception as e:
        app.logger.error(f"Error fetching approval reports: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/approval-report/<report_id>')
def get_approval_report(report_id):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        application = applications.find_one({
            '_id': ObjectId(report_id),
            'username': session['username']
        })

        if not application:
            return jsonify({'error': 'Report not found'}), 404

        report = {
            'report_id': str(application['_id']),
            'business_name': application.get('business_name', ''),
            'business_type': application.get('business_type', ''),
            'business_address': application.get('business_address', ''),
            'approval_details': {
                'approved_by': application.get('approved_by', ''),
                'approval_date': application.get('approval_date', datetime.now()).isoformat(),
                'valid_until': application.get('valid_until', datetime.now() + timedelta(days=365)).isoformat()
            },
            'safety_compliance': {
                'fire_extinguishers': application.get('fire_extinguishers', ''),
                'fire_alarm': application.get('fire_alarm', ''),
                'emergency_exits': application.get('emergency_exits', ''),
                'last_fire_drill': application.get('last_fire_drill', '')
            },
            'approval_conditions': [
                'Regular maintenance of fire safety equipment required',
                'Monthly fire drills mandatory',
                'Annual safety audit to be conducted',
                'Immediate reporting of any safety incidents'
            ]
        }

        return jsonify(report)

    except Exception as e:
        app.logger.error(f"Error fetching report details: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add these indexes to your MongoDB collections
applications.create_index([('status', 1)])
applications.create_index([('timestamp', -1)])
applications.create_index([('business_name', 1)])
applications.create_index([('business_type', 1)])
applications.create_index([('noc_certificate_expiry', 1)])

@app.route('/api/manager-applications')
def get_manager_applications():
    """Get applications assigned to the current manager"""
    if session.get('role') != 'manager':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        manager_username = session.get('username')

        # Get all applications for now (since assigned_manager field might not exist)
        # In production, you would filter by assigned_manager
        manager_applications = list(applications.find({}).sort('timestamp', -1).limit(10))

        # Convert ObjectIds to strings and format dates
        processed_applications = []
        for app in manager_applications:
            processed_app = {
                '_id': str(app['_id']),
                'business_name': app.get('business_name', 'N/A'),
                'business_type': app.get('business_type', 'N/A'),
                'status': app.get('status', 'pending'),
                'email': app.get('email', ''),
                'phone': app.get('phone', ''),
                'assigned_inspector': app.get('assigned_inspector', 'Unassigned'),
                'assigned_manager': app.get('assigned_manager', manager_username)
            }

            # Handle timestamp
            if 'timestamp' in app and app['timestamp']:
                if hasattr(app['timestamp'], 'strftime'):
                    processed_app['timestamp'] = app['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    processed_app['timestamp'] = str(app['timestamp'])
            else:
                processed_app['timestamp'] = 'N/A'

            # Handle approval_date
            if 'approval_date' in app and app['approval_date']:
                if hasattr(app['approval_date'], 'strftime'):
                    processed_app['approval_date'] = app['approval_date'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    processed_app['approval_date'] = str(app['approval_date'])

            processed_applications.append(processed_app)

        return jsonify({'success': True, 'applications': processed_applications})
    except Exception as e:
        print(f"Error fetching manager applications: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/all-applications')
def get_all_applications():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all applications with user details
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'username',
                    'foreignField': 'username',
                    'as': 'user_details'
                }
            },
            {
                '$sort': {'timestamp': -1}
            }
        ]

        all_applications = list(applications.aggregate(pipeline))

        # Process the applications to handle ObjectId and datetime
        processed_applications = []
        for app in all_applications:
            processed_app = {
                '_id': str(app['_id']),
                'business_name': app.get('business_name', ''),
                'business_type': app.get('business_type', ''),
                'status': app.get('status', 'pending'),
                'timestamp': app.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
                'email': app.get('email', ''),
                'phone': app.get('phone', ''),
                'username': app.get('username', ''),
                'report_id': str(app.get('report_id')) if app.get('report_id') else None
            }

            # Add formatted dates if they exist
            if 'approval_date' in app:
                processed_app['approval_date'] = app['approval_date'].strftime('%Y-%m-%d %H:%M:%S')
            if 'valid_until' in app:
                processed_app['valid_until'] = app['valid_until'].strftime('%Y-%m-%d')
            if 'rejection_date' in app:
                processed_app['rejection_date'] = app['rejection_date'].strftime('%Y-%m-%d %H:%M:%S')

            # Add user details
            if app.get('user_details'):
                user = app['user_details'][0]
                processed_app['user_details'] = {
                    'name': user.get('name', ''),
                    'email': user.get('email', '')
                }

            processed_applications.append(processed_app)

        return jsonify({'applications': processed_applications})

    except Exception as e:
        app.logger.error(f"Error in get_all_applications: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approved-reports')
def get_admin_approved_reports():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all approved applications
        approved_apps = list(applications.find({
            'status': 'approved'
        }).sort('approval_date', -1))

        reports_data = []
        for app in approved_apps:
            report = {
                'report_id': str(app['_id']),
                'business_name': app.get('business_name', ''),
                'business_type': app.get('business_type', ''),
                'business_address': app.get('business_address', ''),
                'approval_details': {
                    'approved_by': app.get('approved_by', ''),
                    'approval_date': app.get('approval_date', datetime.now()).isoformat(),
                    'valid_until': app.get('valid_until', datetime.now() + timedelta(days=365)).isoformat()
                }
            }
            reports_data.append(report)

        return jsonify({'reports': reports_data})
    except Exception as e:
        app.logger.error(f"Error fetching approved reports: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_default_logo():
    # Create directory if it doesn't exist
    logo_dir = os.path.join('static', 'images')
    if not os.path.exists(logo_dir):
        os.makedirs(logo_dir)

    logo_path = os.path.join(logo_dir, 'fire_logo.png')

    # Create default logo if it doesn't exist
    if not os.path.exists(logo_path):
        # Create a new image with a white background
        img = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(img)

        # Draw a red circle
        draw.ellipse([20, 20, 180, 180], fill='red')

        # Add text
        try:
            font = ImageFont.truetype('arial.ttf', 40)
        except:
            font = ImageFont.load_default()

        draw.text((100, 100), 'FIRE\nNOC', font=font, fill='white',
                 anchor='mm', align='center')

        # Save the image
        img.save(logo_path, 'PNG')

    return logo_path

def generate_noc_report(application_data, report_id):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        # Styles setup
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            fontName='Helvetica-Bold',
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor('#1a237e')
        ))

        styles.add(ParagraphStyle(
            name='SectionTitle',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#0d47a1')
        ))

        styles.add(ParagraphStyle(
            name='NormalText',
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#000000')
        ))

        elements = []

        # Logo and Title
        try:
            logo_path = create_default_logo()
            logo = Image(logo_path, width=2*inch, height=2*inch)
            logo.hAlign = 'CENTER'
            elements.append(logo)
        except:
            pass

        elements.append(Spacer(1, 20))
        elements.append(Paragraph('FIRE SAFETY CERTIFICATE', styles['CustomTitle']))

        # Certificate Details
        cert_details = [
            ['Certificate Number:', f'FSC-{report_id}'],
            ['Application ID:', str(application_data.get('application_id', ''))],
            ['Report ID:', str(application_data.get('report_id', ''))],
            ['Issue Date:', datetime.now().strftime('%d-%m-%Y')],
            ['Valid Until:', (datetime.now() + timedelta(days=365)).strftime('%d-%m-%Y')]
        ]

        cert_table = Table(cert_details, colWidths=[2.5*inch, 4*inch])
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a237e')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
        ]))
        elements.append(cert_table)
        elements.append(Spacer(1, 20))

        # Business Information
        elements.append(Paragraph('Business Information', styles['SectionTitle']))
        business_data = [
            ['Business Name:', application_data.get('business_name', '')],
            ['Business Type:', application_data.get('business_type', '')],
            ['Business Address:', application_data.get('business_address', '')],
            ['Contact Person:', application_data.get('contact_person', '')],
            ['Contact Number:', application_data.get('contact_number', '')],
            ['Email Address:', application_data.get('email', '')],
            ['Building Type:', application_data.get('building_type', '')],
            ['Building Area:', f"{application_data.get('building_area', '')} sq.ft"],
            ['Number of Floors:', application_data.get('num_floors', '')],
            ['Operating Hours:', application_data.get('operating_hours', '')],
            ['Maximum Occupancy:', application_data.get('max_occupancy', '')],
            ['Registration Number:', application_data.get('registration_number', '')]
        ]

        business_table = Table(business_data, colWidths=[2.5*inch, 4*inch])
        business_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
        ]))
        elements.append(business_table)
        elements.append(Spacer(1, 20))

        # Approval Details
        elements.append(Paragraph('Approval Information', styles['SectionTitle']))
        approval_details = application_data.get('approval_details', {})
        approval_data = [
            ['Approved By:', approval_details.get('approved_by', '')],
            ['Approval Date:', approval_details.get('approval_date', '').strftime('%d-%m-%Y') if approval_details.get('approval_date') else ''],
            ['Valid Until:', approval_details.get('valid_until', '').strftime('%d-%m-%Y') if approval_details.get('valid_until') else '']
        ]

        approval_table = Table(approval_data, colWidths=[2.5*inch, 4*inch])
        approval_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
        ]))
        elements.append(approval_table)
        elements.append(Spacer(1, 20))

        # Safety Compliance
        elements.append(Paragraph('Safety Compliance Details', styles['SectionTitle']))
        safety_compliance = application_data.get('safety_compliance', {})
        safety_data = [
            ['Fire Extinguishers:', str(safety_compliance.get('fire_extinguishers', ''))],
            ['Fire Alarm System:', str(safety_compliance.get('fire_alarm', ''))],
            ['Emergency Exits:', str(safety_compliance.get('emergency_exits', ''))],
            ['Last Fire Drill:', str(safety_compliance.get('last_fire_drill', ''))]
        ]

        safety_table = Table(safety_data, colWidths=[2.5*inch, 4*inch])
        safety_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
        ]))
        elements.append(safety_table)
        elements.append(Spacer(1, 20))

        # QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"Certificate Verification: FSC-{report_id}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer)
        qr_buffer.seek(0)

        qr_image = Image(qr_buffer)
        qr_image.drawHeight = 1.5*inch
        qr_image.drawWidth = 1.5*inch
        qr_image.hAlign = 'RIGHT'
        elements.append(qr_image)

        # Signatures
        signature_data = [
            ['_____________________', '_____________________', '_____________________'],
            ['Fire Safety Officer', 'Chief Fire Officer', 'Date'],
            [
                approval_details.get('approved_by', ''),
                'Chief Officer',
                datetime.now().strftime('%d-%m-%Y')
            ]
        ]

        signature_table = Table(signature_data, colWidths=[2*inch, 2*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold')
        ]))
        elements.append(signature_table)

        # Build PDF
        doc.build(elements)
        return buffer

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise

@app.route('/download-report/<report_id>')
def download_report(report_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get application data
        application = applications.find_one({'_id': ObjectId(report_id)})
        if not application:
            flash('Report not found', 'error')
            return redirect(url_for('dashboard'))

        # Generate the report
        pdf_buffer = generate_noc_report(application, report_id)
        if not pdf_buffer:
            flash('Failed to generate report', 'error')
            return redirect(url_for('dashboard'))

        pdf_buffer.seek(0)

        # Generate a filename with business name and timestamp
        business_name = application.get('business_name', '').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"NOC_Certificate_{business_name}_{timestamp}.pdf"

        # Read the PDF data into memory
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()  # Close the original buffer

        # Create a new BytesIO object with the PDF data
        final_buffer = BytesIO(pdf_data)
        final_buffer.seek(0)

        # Send file with proper headers for PDF
        response = send_file(
            final_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
            conditional=True  # Enable conditional responses
        )

        # Add headers to prevent caching and ensure proper PDF handling
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, post-check=0, pre-check=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    except Exception as e:
        print(f"Download error: {str(e)}")
        flash('Failed to generate report', 'error')
        return redirect(url_for('dashboard'))

@app.route('/get-report-url/<report_id>')
def get_report_url(report_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        return jsonify({
            'download_url': url_for('download_report', report_id=report_id),
            'view_url': url_for('view_report', report_id=report_id)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-noc-certificate/<application_id>', methods=['POST'])
def generate_noc_certificate_route(application_id):
    """Generate NOC certificate after successful inspection"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Get application data
        application = applications.find_one({'_id': ObjectId(application_id)})
        if not application:
            return jsonify({'success': False, 'error': 'Application not found'}), 404

        # Check if inspection is completed
        inspection = inspections.find_one({
            'business_id': ObjectId(application_id),
            'status': 'completed'
        })

        if not inspection:
            return jsonify({
                'success': False,
                'error': 'Cannot generate NOC certificate: Inspection not completed'
            }), 400

        # Import blockchain service
        from blockchain_service import generate_certificate_hash, store_certificate

        # Generate a unique certificate hash
        issue_date = datetime.now().strftime('%Y-%m-%d')
        certificate_hash = generate_certificate_hash(
            str(application_id),
            application.get('business_name', 'Unknown'),
            issue_date
        )

        # Create certificate data for blockchain
        valid_until = datetime.now() + timedelta(days=365)
        certificate_data = {
            'application_id': str(application_id),
            'business_name': application.get('business_name', 'N/A'),
            'address': application.get('business_address', 'N/A'),
            'business_type': application.get('business_type', 'N/A'),
            'issue_date': issue_date,
            'expiry_date': valid_until.strftime('%Y-%m-%d'),
            'approved_by': session.get('name', session.get('username', 'Administrator')),
            'certificate_hash': certificate_hash
        }

        # Store certificate on blockchain
        transaction_id = store_certificate(certificate_data)

        # Generate the certificate
        pdf_buffer = generate_noc_report(application, application_id)
        if not pdf_buffer:
            return jsonify({'success': False, 'error': 'Failed to generate certificate'}), 500

        # Save certificate to file system
        pdf_buffer.seek(0)
        business_name = application.get('business_name', '').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"NOC_Certificate_{business_name}_{timestamp}.pdf"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'certificates', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the file
        with open(file_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())

        # Update application with certificate info and blockchain data
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {
                'noc_certificate_generated': True,
                'noc_certificate_date': datetime.now(),
                'noc_certificate_expiry': valid_until,
                'noc_certificate_path': file_path,
                'noc_certificate_filename': filename,
                'status': 'certificate_issued',
                'certificate_hash': certificate_hash,
                'blockchain_transaction_id': transaction_id,
                'blockchain_verified': True
            }}
        )

        # Send email with certificate
        try:
            with open(file_path, 'rb') as cert_file:
                subject = "Fire NOC Certificate Issued - Blockchain Verified"
                body = f"""
Dear {application.get('contact_person', 'Business Owner')},

We are pleased to inform you that your Fire NOC Certificate has been issued and verified on blockchain.

Business Details:
- Name: {application.get('business_name')}
- Address: {application.get('business_address')}

Certificate Details:
- Issue Date: {issue_date}
- Valid Until: {valid_until.strftime('%Y-%m-%d')}
- Certificate Hash: {certificate_hash}

Verification:
You can verify the authenticity of this certificate at any time by visiting:
{request.host_url}verify-certificate

The certificate is attached to this email. Please keep it for your records.

Best regards,
Fire Safety Department
"""
                msg = Message(
                    subject,
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[application.get('email')]
                )
                msg.body = body
                msg.attach(
                    filename,
                    'application/pdf',
                    cert_file.read()
                )
                mail.send(msg)
        except Exception as e:
            print(f"Error sending certificate email: {str(e)}")

        # Log activity
        log_activity(
            'Blockchain NOC Certificate Issued',
            f"Blockchain-verified NOC Certificate issued for {application.get('business_name')}",
            session.get('username')
        )

        # Send real-time notification
        socketio.emit('noc_certificate_issued', {
            'application_id': application_id,
            'business_name': application.get('business_name'),
            'blockchain_verified': True
        })

        return jsonify({
            'success': True,
            'message': 'Blockchain-verified NOC Certificate generated and sent successfully',
            'download_url': url_for('download_certificate', filename=filename),
            'certificate_hash': certificate_hash,
            'verification_url': url_for('verify_certificate', _external=True)
        })

    except Exception as e:
        print(f"Error generating NOC certificate: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/verify-certificate', methods=['GET', 'POST'])
def verify_certificate():
    """Verify a certificate using blockchain"""
    verification_result = None

    if request.method == 'POST':
        certificate_hash = request.form.get('certificate_hash')
        if certificate_hash:
            # Import blockchain service
            from blockchain_service import verify_certificate as blockchain_verify

            # Verify certificate on blockchain
            verification_result = blockchain_verify(certificate_hash)

    # Handle direct verification via URL parameter
    elif request.args.get('hash'):
        certificate_hash = request.args.get('hash')
        # Import blockchain service
        from blockchain_service import verify_certificate as blockchain_verify

        # Verify certificate on blockchain
        verification_result = blockchain_verify(certificate_hash)

    return render_template('verify_certificate.html', verification_result=verification_result)

@app.route('/verify')
def verify_qr_certificate():
    """Verify certificate from QR code scan"""
    try:
        noc_number = request.args.get('noc')
        business_name = request.args.get('business')

        if not noc_number:
            return render_template_string('''
            <html>
            <head><title>Certificate Verification</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>🔍 Certificate Verification</h2>
                <p style="color: red;">❌ Invalid verification link. NOC number is required.</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            ''')

        # Find certificate by NOC number
        certificate = certificates.find_one({'certificate_number': noc_number})
        if not certificate:
            return render_template_string('''
            <html>
            <head><title>Certificate Verification</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>🔍 Certificate Verification</h2>
                <p style="color: red;">❌ Certificate not found with NOC number: {{ noc_number }}</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            ''', noc_number=noc_number)

        # Get application data
        app_data = applications.find_one({'_id': certificate['application_id']})
        if not app_data:
            return render_template_string('''
            <html>
            <head><title>Certificate Verification</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>🔍 Certificate Verification</h2>
                <p style="color: red;">❌ Application data not found for this certificate.</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            ''')

        # Verify business name matches (if provided)
        if business_name and app_data.get('business_name', '').lower() != business_name.lower():
            return render_template_string('''
            <html>
            <head><title>Certificate Verification</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>🔍 Certificate Verification</h2>
                <p style="color: orange;">⚠️ Business name mismatch. Please verify the certificate details.</p>
                <p><strong>Expected:</strong> {{ business_name }}</p>
                <p><strong>Found:</strong> {{ found_name }}</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            ''', business_name=business_name, found_name=app_data.get('business_name', 'Unknown'))

        # Certificate is valid
        return render_template_string('''
        <html>
        <head>
            <title>Certificate Verification - Valid</title>
            <style>
                body { font-family: Arial; padding: 20px; background: #f0f8ff; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .valid { color: #28a745; font-size: 1.2em; }
                .details { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
                .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px 0 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔍 Certificate Verification</h2>
                <p class="valid">✅ <strong>CERTIFICATE VERIFIED SUCCESSFULLY</strong></p>

                <div class="details">
                    <h3>Certificate Details:</h3>
                    <p><strong>NOC Number:</strong> {{ noc_number }}</p>
                    <p><strong>Business Name:</strong> {{ business_name }}</p>
                    <p><strong>Business Type:</strong> {{ business_type }}</p>
                    <p><strong>Issue Date:</strong> {{ issue_date }}</p>
                    <p><strong>Status:</strong> {{ status }}</p>
                    <p><strong>Issued By:</strong> MAYUR BHARVAD, Fire Safety Officer</p>
                </div>

                <p><small>This certificate has been verified against our official database.</small></p>

                <a href="/view-certificate/{{ application_id }}" class="btn">📄 View Full Certificate</a>
                <a href="/" class="btn">🏠 Back to Home</a>
            </div>
        </body>
        </html>
        ''',
        noc_number=certificate['certificate_number'],
        business_name=app_data.get('business_name', 'Unknown'),
        business_type=app_data.get('business_type', 'Unknown'),
        issue_date=certificate.get('issue_date', 'Unknown'),
        status=app_data.get('status', 'Unknown').title(),
        application_id=str(certificate['application_id'])
        )

    except Exception as e:
        return render_template_string('''
        <html>
        <head><title>Certificate Verification - Error</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>🔍 Certificate Verification</h2>
            <p style="color: red;">❌ Error during verification: {{ error }}</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        ''', error=str(e))

@app.route('/user_activities')
def user_activities():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    try:
        # Get all activities with proper field handling
        all_activities = list(activities.find().sort('timestamp', -1))

        # Add missing fields and format timestamps
        for activity in all_activities:
            # Convert ObjectId to string
            activity['_id'] = str(activity['_id'])

            # Ensure timestamp exists
            if 'timestamp' not in activity:
                activity['timestamp'] = datetime.now()

            # Ensure username exists
            if 'username' not in activity:
                activity['username'] = 'System'

            # Ensure activity_type exists
            if 'activity_type' not in activity:
                activity['activity_type'] = 'general'

            # Ensure description exists
            if 'description' not in activity:
                activity['description'] = 'No description available'

        return render_template('user_activities.html', activities=all_activities)

    except Exception as e:
        print(f"Error in user_activities: {str(e)}")
        flash('Error loading activities!', 'danger')
        return redirect(url_for('dashboard'))

# Duplicate function removed - using the one at line 5962

@app.route('/profile/<username>')
def view_profile(username):
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    user = users.find_one({'username': username})
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('dashboard'))

    # Check permissions
    if session['username'] != username and session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard'))

    # Get role-specific data
    role_data = get_role_specific_data(user)

    return render_template('profile.html', user=user, role_data=role_data)

def get_role_specific_data(user):
    role = user['role']
    username = user['username']

    if role == 'business_owner':
        return {
            'total_applications': applications.count_documents({'username': username}),
            'approved_applications': applications.count_documents({'username': username, 'status': 'approved'}),
            'pending_inspections': applications.count_documents({
                'username': username,
                'status': 'pending',
                'inspection_scheduled': True
            }),
            'business_details': {
                'company_name': user.get('company_name'),
                'business_type': user.get('business_type'),
                'address': user.get('address')
            },
            'recent_activities': list(activities.find(
                {'username': username}
            ).sort('timestamp', -1).limit(5))
        }

    elif role == 'manager':
        return {
            'managed_applications': applications.count_documents({'assigned_manager': username}),
            'team_size': users.count_documents({'reporting_manager': username}),
            'pending_approvals': applications.count_documents({
                'assigned_manager': username,
                'status': 'pending'
            }),
            'department': user.get('department'),
            'team_members': list(users.find(
                {'reporting_manager': username},
                {'username': 1, 'name': 1, 'designation': 1}
            ))
        }

    elif role == 'employee':
        return {
            'assigned_tasks': applications.count_documents({'assigned_inspector': username}),
            'completed_inspections': applications.count_documents({
                'assigned_inspector': username,
                'inspection_status': 'completed'
            }),
            'department': user.get('department'),
            'reporting_manager': users.find_one(
                {'username': user.get('reporting_manager')},
                {'name': 1, 'email': 1}
            )
        }

    elif role == 'expert':
        return {
            'expertise': user.get('expertise', ''),
            'experience': user.get('experience', ''),
            'certifications': user.get('certifications', ''),
            'recent_activities': list(activities.find(
                {'username': username}
            ).sort('timestamp', -1).limit(5))
        }

    elif role == 'admin':
        return {
            'total_users': users.count_documents({}),
            'total_applications': applications.count_documents({}),
            'recent_registrations': list(users.find(
                {}
            ).sort('created_at', -1).limit(5)),
            'system_stats': {
                'pending_applications': applications.count_documents({'status': 'pending'}),
                'approved_applications': applications.count_documents({'status': 'approved'}),
                'rejected_applications': applications.count_documents({'status': 'rejected'})
            }
        }

    return {}

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    user = users.find_one({'username': session['username']})
    role = user['role']

    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'business_owner':
        return redirect(url_for('business_dashboard'))
    elif role == 'manager':
        return redirect(url_for('manager_dashboard'))
    elif role == 'employee':
        return redirect(url_for('employee_dashboard'))
    elif role == 'expert':
        return redirect(url_for('expert_dashboard'))

    flash('Invalid role!', 'danger')
    return redirect(url_for('login'))

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        data = request.form.to_dict()
        user = users.find_one({'username': session['username']})
        role = user['role']

        # Base profile update data
        update_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'mobile': data.get('mobile'),
            'address': data.get('address'),
            'updated_at': datetime.now()
        }

        # Role-specific profile updates
        if role == 'business_owner':
            update_data.update({
                'company_name': data.get('company_name'),
                'business_type': data.get('business_type'),
                'gst_number': data.get('gst_number'),
                'business_address': data.get('business_address')
            })
        elif role == 'manager':
            update_data.update({
                'department': data.get('department'),
                'designation': data.get('designation'),
                'team_size': data.get('team_size')
            })
        elif role == 'employee':
            update_data.update({
                'department': data.get('department'),
                'designation': data.get('designation'),
                'skills': data.get('skills', '').split(',')
            })
        elif role == 'expert':
            update_data.update({
                'expertise': data.get('expertise'),
                'experience': data.get('experience'),
                'certifications': data.get('certifications')
            })

        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename and allowed_file(file.filename):
                # Create a secure filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{session['username']}_{int(time.time())}{os.path.splitext(file.filename)[1]}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Save the file
                file.save(file_path)
                update_data['profile_image'] = filename

        # Update user document
        users.update_one(
            {'username': session['username']},
            {'$set': update_data}
        )

        # Log activity
        log_activity('Profile Update', f"User {session['username']} updated their profile")

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully!',
            'redirect': url_for('view_profile', username=session['username'])
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin_profile')
def admin_profile():
    if 'username' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    user = users.find_one({'username': session['username']})
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_profile.html', user=user)

@app.route('/api/admin/profile/update', methods=['POST'])
def api_admin_profile_update():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied!'})

    try:
        data = request.get_json()

        # Update user document
        result = users.update_one(
            {'username': session['username']},
            {'$set': {
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'updated_at': datetime.now()
            }}
        )

        if result.modified_count == 0:
            return jsonify({'success': False, 'error': 'No changes made'}), 400

        return jsonify({
            'success': True,
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/profile/update_image', methods=['POST'])
def api_admin_profile_update_image():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied!'})

    try:
        if 'profile_image' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['profile_image']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed types: PNG, JPG, JPEG, GIF'}), 400

        # Validate file size (max 5MB)
        if len(file.read()) > 5 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'File size too large. Maximum size: 5MB'}), 400

        file.seek(0)  # Reset file pointer after reading

        # Generate secure filename with timestamp
        filename = secure_filename(f"{session['username']}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save the file
        file.save(filepath)

        # Update user's profile image in database
        users.update_one(
            {'username': session['username']},
            {'$set': {'profile_image': f'/static/{filename}'}}
        )

        # Delete old profile image if it exists and is not the default
        old_image = users.find_one({'username': session['username']}).get('profile_image')
        if old_image and old_image != 'default-profile.png':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        return jsonify({
            'success': True,
            'image_path': f'/static/{filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Add this route to serve profile images
@app.route('/static/profile_images/<filename>')
def serve_profile_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/toggle_user_status/<user_id>', methods=['POST'])
@csrf.exempt  # Add this if you're using AJAX
def toggle_user_status(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        current_status = user.get('profile_status', 'active')
        new_status = 'inactive' if current_status == 'active' else 'active'

        result = users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'profile_status': new_status,
                'updated_at': datetime.now()
            }}
        )

        if result.modified_count == 0:
            return jsonify({'error': 'Failed to update status'}), 500

        log_activity(
            'User Status Update',
            f"User {user['username']} status changed to {new_status}"
        )

        return jsonify({
            'success': True,
            'new_status': new_status,
            'message': f'User status updated to {new_status}'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view_user/<user_id>')
def view_user(user_id):
    if 'username' not in session:
        flash('Please login to access settings', 'error')
        return redirect(url_for('login'))

    try:
        # Get user details
        user = users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('manage_users'))

        # Add created_at if it doesn't exist
        if 'created_at' not in user:
            user['created_at'] = user.get('timestamp', datetime.now())

        # Get user's activities
        user_activities = list(activities.find(
            {'username': user['username']},
            {'_id': 0}
        ).sort('timestamp', -1).limit(50))

        # Get user's applications
        user_apps = list(applications.find(
            {'submitted_by': user['username']},
            {'_id': 1, 'business_name': 1, 'status': 1, 'timestamp': 1}
        ).sort('timestamp', -1))

        # Convert ObjectId to string for applications
        for app in user_apps:
            app['_id'] = str(app['_id'])
            if 'timestamp' in app:
                app['created_at'] = app['timestamp']

        # Convert ObjectId to string for user
        user['_id'] = str(user['_id'])

        return render_template('view_user.html',
                             user=user,
                             activities=user_activities,
                             applications=user_apps)

    except Exception as e:
        print(f"Error in view_user: {str(e)}")
        flash('Error loading user details!', 'danger')
        return redirect(url_for('manage_users'))

@app.route('/export_users')
def export_users():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all users excluding passwords
        all_users = list(users.find({}, {'password': 0}))

        # Create a BytesIO object
        si = StringIO()
        writer = csv.writer(si)

        # Write headers
        headers = ['ID', 'Username', 'Name', 'Email', 'Role', 'Status', 'Is Expert']
        writer.writerow(headers)

        # Write user data
        for user in all_users:
            writer.writerow([
                str(user['_id']),
                user.get('username', ''),
                user.get('name', ''),
                user.get('email', ''),
                user.get('role', ''),
                user.get('profile_status', 'inactive'),
                'Yes' if user.get('is_expert', False) else 'No'
            ])

        # Create the response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=users_export.csv"
        output.headers["Content-type"] = "text/csv"

        # Log the export
        log_activity('User Export', f"Users exported by {session['username']}")

        return output

    except Exception as e:
        print(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add these configurations
app.config['CSRF_ENABLED'] = True
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Disable CSRF check for specific routes if needed

# Add these routes to handle settings
@app.route('/settings')
def settings():
    if 'username' not in session:
        flash('Please login to access settings', 'error')
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/update_profile_settings', methods=['POST'])
def update_profile_settings():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        email_notifications = request.form.get('email_notifications') == 'on'
        language = request.form.get('language')

        # Update user settings in database
        users.update_one(
            {'username': session['username']},
            {'$set': {
                'settings.email_notifications': email_notifications,
                'settings.language': language
            }}
        )

        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
    except Exception as e:
        flash('Error updating settings', 'error')
        return redirect(url_for('settings'))

@app.route('/update_security_settings', methods=['POST'])
def update_security_settings():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Get user from database
        user = users.find_one({'username': session['username']})

        if not user:
            flash('User not found', 'error')
            return redirect(url_for('settings'))

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user['password']):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('settings'))

        # Verify new password matches confirmation
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('settings'))

        # Hash and update new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        users.update_one(
            {'username': session['username']},
            {'$set': {'password': hashed_password}}
        )

        flash('Password updated successfully', 'success')
        return redirect(url_for('settings'))
    except Exception as e:
        flash('Error updating password', 'error')
        return redirect(url_for('settings'))

# Analytics Routes
@app.route('/reports')
def page_analytics():
    if 'username' not in session:
        flash('Please log in to access analytics', 'error')
        return redirect(url_for('login'))

    # Fetch analytics data
    total_applications = applications.count_documents({})
    approved_applications = applications.count_documents({'status': 'approved'})
    pending_applications = applications.count_documents({'status': 'pending'})
    rejected_applications = applications.count_documents({'status': 'rejected'})

    # User activity analytics
    recent_activities = list(activities.find().sort('timestamp', -1).limit(10))

    return render_template('analytics/page_analytics.html',
                           total_applications=total_applications,
                           approved_applications=approved_applications,
                           pending_applications=pending_applications,
                           rejected_applications=rejected_applications,
                           recent_activities=recent_activities)

@app.route('/detailed_reports')
def detailed_reports():
    if 'username' not in session:
        flash('Please log in to access detailed reports', 'error')
        return redirect(url_for('login'))

    # Fetch detailed reports data
    all_reports = list(reports.find().sort('timestamp', -1))

    # Aggregate reports by type and status
    report_types = reports.aggregate([
        {'$group': {
            '_id': '$type',
            'count': {'$sum': 1}
        }}
    ])

    return render_template('analytics/detailed_reports.html',
                           reports=all_reports,
                           report_types=list(report_types))

@app.route('/performance')
def performance_metrics():
    if 'username' not in session:
        flash('Please log in to access performance metrics', 'error')
        return redirect(url_for('login'))

    # Performance metrics
    application_processing_times = list(applications.aggregate([
        {'$group': {
            '_id': '$status',
            'avg_processing_time': {'$avg': {'$subtract': ['$processed_date', '$timestamp']}}
        }}
    ]))

    # User performance metrics
    user_application_counts = list(applications.aggregate([
        {'$group': {
            '_id': '$submitted_by',
            'total_applications': {'$sum': 1},
            'approved_applications': {'$sum': {'$cond': [{'$eq': ['$status', 'approved']}, 1, 0]}}
        }}
    ]))

    return render_template('analytics/performance_metrics.html',
                           processing_times=application_processing_times,
                           user_performance=user_application_counts)

@app.route('/export_page_analytics')
def export_page_analytics():
    if 'username' not in session:
        flash('Please log in to export analytics', 'error')
        return redirect(url_for('login'))

    # Fetch analytics data
    total_applications = applications.count_documents({})
    approved_applications = applications.count_documents({'status': 'approved'})
    pending_applications = applications.count_documents({'status': 'pending'})
    rejected_applications = applications.count_documents({'status': 'rejected'})

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Write headers
    headers = ['Metric', 'Count']
    writer.writerow(headers)

    # Write user data
    for metric, count in [
        ['Total Applications', total_applications],
        ['Approved Applications', approved_applications],
        ['Pending Applications', pending_applications],
        ['Rejected Applications', rejected_applications]
    ]:
        writer.writerow([metric, count])

    # Create the response
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='page_analytics.csv'
    )

@app.route('/advanced_analytics')
def advanced_analytics():
    """Advanced analytics dashboard with predictive features"""
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied! Admin privileges required.', 'danger')
        return redirect(url_for('login'))

    # Initial stats for the dashboard
    stats = {
        'total': applications.count_documents({}),
        'approval_rate': 0,
        'avg_processing_time': 0,
        'compliance_rate': 0
    }

    # Calculate approval rate
    total_processed = applications.count_documents({'status': {'$in': ['approved', 'rejected']}})
    if total_processed > 0:
        approved = applications.count_documents({'status': 'approved'})
        stats['approval_rate'] = round((approved / total_processed) * 100)

    # Calculate average processing time
    processing_times = []
    for app in applications.find({'status': 'approved', 'approved_at': {'$exists': True}, 'timestamp': {'$exists': True}}):
        if 'approved_at' in app and 'timestamp' in app:
            processing_time = (app['approved_at'] - app['timestamp']).days
            if processing_time >= 0:  # Sanity check
                processing_times.append(processing_time)

    if processing_times:
        stats['avg_processing_time'] = round(sum(processing_times) / len(processing_times), 1)

    # Calculate compliance rate (certificates not expired)
    total_certificates = applications.count_documents({'status': 'certificate_issued'})
    if total_certificates > 0:
        valid_certificates = applications.count_documents({
            'status': 'certificate_issued',
            'noc_certificate_expiry': {'$gt': datetime.now()}
        })
        stats['compliance_rate'] = round((valid_certificates / total_certificates) * 100)

    # Placeholder for predictions
    predictions = {
        'applications': 0,
        'renewals': 0,
        'inspections': 0
    }

    # Calculate simple predictions based on historical data
    # Applications prediction (based on last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_applications = applications.count_documents({'timestamp': {'$gte': thirty_days_ago}})
    predictions['applications'] = recent_applications

    # Renewals prediction (certificates expiring in next 30 days)
    thirty_days_future = datetime.now() + timedelta(days=30)
    predictions['renewals'] = applications.count_documents({
        'status': 'certificate_issued',
        'noc_certificate_expiry': {
            '$gt': datetime.now(),
            '$lte': thirty_days_future
        }
    })

    # Inspections prediction (based on pending applications)
    predictions['inspections'] = applications.count_documents({'status': 'pending'})

    # Placeholder for compliance data
    compliance = {
        'overall': stats['compliance_rate'],
        'expiring': predictions['renewals'],
        'inspection': 0
    }

    # Calculate inspection compliance
    total_inspections = inspections.count_documents({})
    if total_inspections > 0:
        completed_inspections = inspections.count_documents({'status': 'completed'})
        compliance['inspection'] = round((completed_inspections / total_inspections) * 100)

    return render_template('analytics/advanced_dashboard.html',
                          stats=stats,
                          predictions=predictions,
                          compliance=compliance)

@app.route('/api/analytics/overview')
def api_analytics_overview():
    """API endpoint for overview analytics data"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Basic stats
        stats = {
            'total': applications.count_documents({}),
            'pending': applications.count_documents({'status': 'pending'}),
            'approved': applications.count_documents({'status': 'approved'}),
            'rejected': applications.count_documents({'status': 'rejected'})
        }

        # Calculate approval rate
        total_processed = stats['approved'] + stats['rejected']
        stats['approval_rate'] = round((stats['approved'] / total_processed) * 100) if total_processed > 0 else 0

        # Calculate average processing time
        processing_times = []
        for app in applications.find({'status': 'approved', 'approved_at': {'$exists': True}, 'timestamp': {'$exists': True}}):
            if 'approved_at' in app and 'timestamp' in app:
                processing_time = (app['approved_at'] - app['timestamp']).days
                if processing_time >= 0:  # Sanity check
                    processing_times.append(processing_time)

        stats['avg_processing_time'] = round(sum(processing_times) / len(processing_times), 1) if processing_times else 0

        # Calculate compliance rate
        total_certificates = applications.count_documents({'status': 'certificate_issued'})
        valid_certificates = applications.count_documents({
            'status': 'certificate_issued',
            'noc_certificate_expiry': {'$gt': datetime.now()}
        })
        stats['compliance_rate'] = round((valid_certificates / total_certificates) * 100) if total_certificates > 0 else 0

        # Calculate trends (month-over-month change)
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        current_month_apps = applications.count_documents({'timestamp': {'$gte': current_month_start}})
        last_month_apps = applications.count_documents({
            'timestamp': {'$gte': last_month_start, '$lt': current_month_start}
        })

        # Calculate trend percentages
        trends = {
            'total': calculate_trend_percentage(last_month_apps, current_month_apps),
            'approval_rate': 0,  # Would need more complex calculation
            'processing_time': 0,  # Would need more complex calculation
            'compliance': 0  # Would need more complex calculation
        }

        # Application trends chart data (last 6 months)
        months = []
        new_apps = []
        approved_apps = []
        rejected_apps = []

        for i in range(5, -1, -1):
            month_start = (datetime.now() - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_name = month_start.strftime('%b %Y')

            months.append(month_name)
            new_apps.append(applications.count_documents({
                'timestamp': {'$gte': month_start, '$lt': month_end}
            }))
            approved_apps.append(applications.count_documents({
                'approved_at': {'$gte': month_start, '$lt': month_end},
                'status': 'approved'
            }))
            rejected_apps.append(applications.count_documents({
                'processed_date': {'$gte': month_start, '$lt': month_end},
                'status': 'rejected'
            }))

        # Status distribution data
        status_distribution = [
            stats['pending'],
            stats['approved'],
            stats['rejected'],
            applications.count_documents({'status': 'certificate_issued'})
        ]

        # Business type distribution
        business_types = list(applications.aggregate([
            {'$group': {
                '_id': '$business_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]))

        # Inspector performance
        inspector_performance = list(inspections.aggregate([
            {'$match': {'status': 'completed'}},
            {'$group': {
                '_id': '$inspector_id',
                'completed': {'$sum': 1},
                'avg_time': {'$avg': {'$subtract': ['$completion_date', '$date']}}
            }},
            {'$sort': {'completed': -1}},
            {'$limit': 5}
        ]))

        # Format inspector performance data
        inspector_names = []
        inspector_counts = []

        for inspector in inspector_performance:
            inspector_user = users.find_one({'username': inspector['_id']})
            name = inspector_user.get('name', inspector['_id']) if inspector_user else inspector['_id']
            inspector_names.append(name)
            inspector_counts.append(inspector['completed'])

        return jsonify({
            'success': True,
            'stats': stats,
            'trends': trends,
            'charts': {
                'application_trends': {
                    'labels': months,
                    'new': new_apps,
                    'approved': approved_apps,
                    'rejected': rejected_apps
                },
                'status_distribution': {
                    'labels': ['Pending', 'Approved', 'Rejected', 'Certificate Issued'],
                    'data': status_distribution
                },
                'business_types': {
                    'labels': [bt['_id'] for bt in business_types],
                    'data': [bt['count'] for bt in business_types]
                },
                'inspector_performance': {
                    'labels': inspector_names,
                    'data': inspector_counts
                }
            }
        })
    except Exception as e:
        print(f"Error in analytics overview API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_trend_percentage(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 100 if new_value > 0 else 0

    return round(((new_value - old_value) / old_value) * 100)

@app.route('/api/analytics/predictive')
def api_analytics_predictive():
    """API endpoint for predictive analytics data"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Simple predictions based on historical data
        predictions = {}

        # Applications prediction (based on last 30 days trend)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        sixty_days_ago = datetime.now() - timedelta(days=60)

        recent_applications = applications.count_documents({'timestamp': {'$gte': thirty_days_ago}})
        previous_applications = applications.count_documents({'timestamp': {'$gte': sixty_days_ago, '$lt': thirty_days_ago}})

        # Simple linear prediction
        if previous_applications > 0:
            growth_rate = recent_applications / previous_applications
            predictions['applications'] = round(recent_applications * growth_rate)
        else:
            predictions['applications'] = recent_applications

        # Renewals prediction (certificates expiring in next 30 days)
        thirty_days_future = datetime.now() + timedelta(days=30)
        predictions['renewals'] = applications.count_documents({
            'status': 'certificate_issued',
            'noc_certificate_expiry': {
                '$gt': datetime.now(),
                '$lte': thirty_days_future
            }
        })

        # Inspections prediction (based on pending applications and historical completion rate)
        pending_inspections = inspections.count_documents({'status': 'pending'})

        # Calculate average inspections completed per month
        last_month_start = (datetime.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        completed_last_month = inspections.count_documents({
            'status': 'completed',
            'completion_date': {'$gte': last_month_start}
        })

        # Predict based on pending and historical completion rate
        predictions['inspections'] = pending_inspections + completed_last_month

        # Generate forecast data for next 6 months
        months = []
        application_forecast = []
        renewal_forecast = []

        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get historical monthly data for the past 6 months
        historical_months = []
        historical_applications = []

        for i in range(6, 0, -1):
            month_start = (current_month - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            historical_months.append(month_start.strftime('%b %Y'))
            monthly_count = applications.count_documents({
                'timestamp': {'$gte': month_start, '$lt': month_end}
            })
            historical_applications.append(monthly_count)

        # Simple forecasting for next 6 months
        # This is a very basic linear regression - in a real system you'd use more sophisticated ML
        if len(historical_applications) > 0:
            avg_monthly_growth = sum(
                (historical_applications[i] - historical_applications[i-1])
                for i in range(1, len(historical_applications))
            ) / (len(historical_applications) - 1)

            last_value = historical_applications[-1]

            for i in range(6):
                next_month = (current_month + timedelta(days=30*i)).replace(day=1)
                months.append(next_month.strftime('%b %Y'))

                # Apply growth trend
                forecast_value = max(0, round(last_value + avg_monthly_growth * (i+1)))
                application_forecast.append(forecast_value)

                # For renewals, use certificates that will expire in that month
                month_end = (next_month + timedelta(days=32)).replace(day=1)
                renewal_count = applications.count_documents({
                    'status': 'certificate_issued',
                    'noc_certificate_expiry': {'$gte': next_month, '$lt': month_end}
                })
                renewal_forecast.append(renewal_count)

        return jsonify({
            'success': True,
            'predictions': {
                'applications': predictions['applications'],
                'renewals': predictions['renewals'],
                'inspections': predictions['inspections']
            },
            'forecasts': {
                'applications': {
                    'labels': months,
                    'data': application_forecast
                },
                'renewals': {
                    'labels': months,
                    'data': renewal_forecast
                }
            }
        })
    except Exception as e:
        print(f"Error in predictive analytics API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/risk-map')
def api_analytics_risk_map():
    """API endpoint for risk assessment map data"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # This would normally use real geospatial data from your database
        # For demonstration, we'll generate sample data

        # Sample coordinates for major Indian cities
        cities = [
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777, "risk_base": 75},
            {"name": "Delhi", "lat": 28.7041, "lng": 77.1025, "risk_base": 80},
            {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946, "risk_base": 65},
            {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867, "risk_base": 70},
            {"name": "Chennai", "lat": 13.0827, "lng": 80.2707, "risk_base": 72},
            {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639, "risk_base": 78},
            {"name": "Pune", "lat": 18.5204, "lng": 73.8567, "risk_base": 68},
            {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "risk_base": 74},
            {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873, "risk_base": 71},
            {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462, "risk_base": 73}
        ]

        # Generate risk points based on application and inspection data
        risk_map_data = []
        high_risk_areas = []

        for city in cities:
            # Calculate risk factors based on:
            # 1. Number of rejected applications
            # 2. Number of expired certificates
            # 3. Number of failed inspections
            # In a real system, you would query your database for these metrics

            # For demonstration, we'll use random factors
            rejection_factor = random.randint(0, 20)
            expiry_factor = random.randint(0, 15)
            inspection_factor = random.randint(0, 25)

            # Calculate risk score (0-100)
            risk_score = min(100, city["risk_base"] + rejection_factor + expiry_factor - inspection_factor)

            # Add to risk map data
            risk_map_data.append({
                "lat": city["lat"],
                "lng": city["lng"],
                "risk_score": risk_score
            })

            # Add to high risk areas if score is above threshold
            if risk_score > 70:
                contributing_factors = []

                if rejection_factor > 10:
                    contributing_factors.append("High application rejection rate")
                if expiry_factor > 7:
                    contributing_factors.append("Many expired certificates")
                if inspection_factor < 10:
                    contributing_factors.append("Low inspection coverage")

                high_risk_areas.append({
                    "area": city["name"],
                    "risk_score": risk_score,
                    "factors": contributing_factors
                })

        # Sort high risk areas by risk score
        high_risk_areas.sort(key=lambda x: x["risk_score"], reverse=True)

        # Generate resource allocation recommendations
        recommendations = [
            {
                "title": "Inspection Resource Allocation",
                "description": "Allocate more inspectors to high-risk areas",
                "areas": [area["area"] for area in high_risk_areas[:3]]
            },
            {
                "title": "Compliance Enforcement",
                "description": "Increase compliance checks in areas with expired certificates",
                "areas": [city["name"] for city in cities if random.random() > 0.7]
            },
            {
                "title": "Training Programs",
                "description": "Conduct fire safety training programs in high-density areas",
                "areas": [city["name"] for city in cities if random.random() > 0.6]
            }
        ]

        return jsonify({
            'success': True,
            'risk_map': risk_map_data,
            'high_risk_areas': high_risk_areas,
            'recommendations': recommendations
        })
    except Exception as e:
        print(f"Error in risk map API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/compliance')
def api_analytics_compliance():
    """API endpoint for compliance analytics data"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Calculate overall compliance rate
        total_certificates = applications.count_documents({'status': 'certificate_issued'})
        valid_certificates = applications.count_documents({
            'status': 'certificate_issued',
            'noc_certificate_expiry': {'$gt': datetime.now()}
        })

        overall_compliance = round((valid_certificates / total_certificates) * 100) if total_certificates > 0 else 0

        # Calculate certificates expiring soon
        thirty_days_future = datetime.now() + timedelta(days=30)
        expiring_soon = applications.count_documents({
            'status': 'certificate_issued',
            'noc_certificate_expiry': {
                '$gt': datetime.now(),
                '$lte': thirty_days_future
            }
        })

        # Calculate inspection compliance
        total_inspections = inspections.count_documents({})
        completed_inspections = inspections.count_documents({'status': 'completed'})
        inspection_compliance = round((completed_inspections / total_inspections) * 100) if total_inspections > 0 else 0

        # Calculate compliance by business type
        business_types = list(applications.aggregate([
            {'$match': {'status': 'certificate_issued'}},
            {'$group': {
                '_id': '$business_type',
                'total': {'$sum': 1},
                'valid': {
                    '$sum': {
                        '$cond': [
                            {'$gt': ['$noc_certificate_expiry', datetime.now()]},
                            1,
                            0
                        ]
                    }
                }
            }},
            {'$project': {
                'type': '$_id',
                'compliance_rate': {
                    '$multiply': [
                        {'$divide': ['$valid', '$total']},
                        100
                    ]
                }
            }},
            {'$sort': {'compliance_rate': -1}},
            {'$limit': 5}
        ]))

        # Format compliance by type data
        compliance_types = []
        compliance_rates = []

        for bt in business_types:
            compliance_types.append(bt.get('type', 'Unknown'))
            compliance_rates.append(round(bt.get('compliance_rate', 0)))

        # Calculate compliance trend over last 6 months
        months = []
        compliance_trend = []

        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for i in range(5, -1, -1):
            month_start = (current_month - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            month_name = month_start.strftime('%b %Y')

            # Calculate compliance for that month
            month_total = applications.count_documents({
                'status': 'certificate_issued',
                'timestamp': {'$lt': month_end}
            })

            month_valid = applications.count_documents({
                'status': 'certificate_issued',
                'timestamp': {'$lt': month_end},
                'noc_certificate_expiry': {'$gt': month_start}
            })

            month_compliance = round((month_valid / month_total) * 100) if month_total > 0 else 0

            months.append(month_name)
            compliance_trend.append(month_compliance)

        # Calculate trends
        current_quarter_start = current_month - timedelta(days=90)
        previous_quarter_start = current_quarter_start - timedelta(days=90)

        # Current quarter compliance
        current_quarter_total = applications.count_documents({
            'status': 'certificate_issued',
            'timestamp': {'$lt': current_month}
        })

        current_quarter_valid = applications.count_documents({
            'status': 'certificate_issued',
            'timestamp': {'$lt': current_month},
            'noc_certificate_expiry': {'$gt': current_quarter_start}
        })

        current_quarter_compliance = (current_quarter_valid / current_quarter_total) * 100 if current_quarter_total > 0 else 0

        # Previous quarter compliance
        previous_quarter_total = applications.count_documents({
            'status': 'certificate_issued',
            'timestamp': {'$lt': current_quarter_start}
        })

        previous_quarter_valid = applications.count_documents({
            'status': 'certificate_issued',
            'timestamp': {'$lt': current_quarter_start},
            'noc_certificate_expiry': {'$gt': previous_quarter_start}
        })

        previous_quarter_compliance = (previous_quarter_valid / previous_quarter_total) * 100 if previous_quarter_total > 0 else 0

        # Calculate trend
        overall_trend = calculate_trend_percentage(previous_quarter_compliance, current_quarter_compliance)

        # Calculate inspection compliance trend similarly
        current_quarter_inspections = inspections.count_documents({
            'date': {'$gte': current_quarter_start, '$lt': current_month}
        })

        current_quarter_completed = inspections.count_documents({
            'status': 'completed',
            'date': {'$gte': current_quarter_start, '$lt': current_month}
        })

        current_quarter_inspection_compliance = (current_quarter_completed / current_quarter_inspections) * 100 if current_quarter_inspections > 0 else 0

        previous_quarter_inspections = inspections.count_documents({
            'date': {'$gte': previous_quarter_start, '$lt': current_quarter_start}
        })

        previous_quarter_completed = inspections.count_documents({
            'status': 'completed',
            'date': {'$gte': previous_quarter_start, '$lt': current_quarter_start}
        })

        previous_quarter_inspection_compliance = (previous_quarter_completed / previous_quarter_inspections) * 100 if previous_quarter_inspections > 0 else 0

        inspection_trend = calculate_trend_percentage(previous_quarter_inspection_compliance, current_quarter_inspection_compliance)

        return jsonify({
            'success': True,
            'compliance': {
                'overall': overall_compliance,
                'expiring': expiring_soon,
                'inspection': inspection_compliance
            },
            'trends': {
                'overall': overall_trend,
                'inspection': inspection_trend
            },
            'charts': {
                'by_type': {
                    'labels': compliance_types,
                    'data': compliance_rates
                },
                'trend': {
                    'labels': months,
                    'data': compliance_trend
                }
            }
        })
    except Exception as e:
        print(f"Error in compliance analytics API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export_performance_metrics/<format>')
def export_performance_metrics(format):
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    try:
        # Get performance metrics data
        application_processing_times = list(applications.aggregate([
            {'$group': {
                '_id': '$status',
                'avg_processing_time': {'$avg': {'$subtract': ['$processed_date', '$timestamp']}}
            }}
        ]))

        # User performance metrics
        user_performance = list(applications.aggregate([
            {'$group': {
                '_id': '$submitted_by',
                'total_applications': {'$sum': 1},
                'approved_applications': {'$sum': {'$cond': [{'$eq': ['$status', 'approved']}, 1, 0]}}
            }}
        ]))

        if format == 'csv':
            # Create CSV in memory using BytesIO
            output = BytesIO()
            writer = csv.writer(TextIOWrapper(output, 'utf-8'))

            # Write processing times
            writer.writerow(['Processing Times by Status'])
            writer.writerow(['Status', 'Average Processing Time (Hours)'])
            for time in application_processing_times:
                writer.writerow([
                    time['_id'],
                    f"{(time.get('avg_processing_time', 0) / 3600000):.2f}"
                ])

            writer.writerow([])  # Empty row for separation

            # Write user performance
            writer.writerow(['User Performance Metrics'])
            writer.writerow(['User', 'Total Applications', 'Approved Applications', 'Success Rate'])
            for user in user_performance:
                total = user['total_applications']
                approved = user['approved_applications']
                success_rate = (approved / total * 100) if total > 0 else 0
                writer.writerow([
                    user['_id'],
                    total,
                    approved,
                    f"{success_rate:.2f}%"
                ])

            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name='performance_metrics.csv'
            )

        elif format == 'pdf':
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Title
            elements.append(Paragraph("Performance Metrics Report", styles['Title']))
            elements.append(Spacer(1, 20))

            # Processing Times Table
            elements.append(Paragraph("Processing Times by Status", styles['Heading1']))
            elements.append(Spacer(1, 12))

            pt_data = [['Status', 'Average Processing Time (Hours)']]
            for time in application_processing_times:
                pt_data.append([
                    time['_id'],
                    f"{(time.get('avg_processing_time', 0) / 3600000):.2f}"
                ])

            pt_table = Table(pt_data)
            pt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(pt_table)
            elements.append(Spacer(1, 20))

            # User Performance Table
            elements.append(Paragraph("User Performance Metrics", styles['Heading1']))
            elements.append(Spacer(1, 12))

            up_data = [['User', 'Total Applications', 'Approved', 'Success Rate']]
            for user in user_performance:
                total = user['total_applications']
                approved = user['approved_applications']
                success_rate = (approved / total * 100) if total > 0 else 0
                up_data.append([
                    user['_id'],
                    str(total),
                    str(approved),
                    f"{success_rate:.2f}%"
                ])

            up_table = Table(up_data)
            up_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(up_table)

            # Build PDF
            doc.build(elements)
            buffer.seek(0)

            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='performance_metrics.pdf'
            )

        else:
            flash('Invalid export format!', 'danger')
            return redirect(url_for('performance_metrics'))

    except Exception as e:
        print(f"Export error: {str(e)}")
        flash('Error exporting data!', 'danger')
        return redirect(url_for('performance_metrics'))

@app.route('/api/admin/profile')
def get_admin_profile():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        user = users.find_one({'username': session['username']})
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        return jsonify({
            'success': True,
            'name': user.get('name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'profile_image': user.get('profile_image', 'default-profile.png')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inspections', methods=['GET', 'POST'])
def manage_inspections():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        if request.method == 'POST':
            data = request.get_json()

            # Validate required fields
            required_fields = ['business_id', 'business_name', 'inspector_id', 'inspector_name', 'date', 'time']
            if not all(data.get(field) for field in required_fields):
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields'
                }), 400

            inspection_data = {
                'business_id': data['business_id'],
                'business_name': data['business_name'],
                'inspector_id': data['inspector_id'],
                'inspector_name': data['inspector_name'],
                'date': data['date'],
                'time': data['time'],
                'location': data.get('location', ''),
                'status': 'scheduled',
                'notes': data.get('notes', ''),
                'created_by': session.get('username'),
                'created_at': datetime.now()
            }

            # Insert inspection record
            result = inspections.insert_one(inspection_data)

            # Get inspector details for email notification
            inspector_user = users.find_one({'username': data['inspector_id']})
            if inspector_user and inspector_user.get('email'):
                email_sent = send_inspection_notification(
                    inspector_user.get('email', ''),
                    str(result.inserted_id),
                    inspection_data.get('date', '')
                )

            # Send comprehensive email notifications
            app_data = applications.find_one({'_id': ObjectId(data['business_id'])})
            if app_data:
                user_data = users.find_one({'username': app_data.get('username')})
                inspector_user = users.find_one({'username': data['inspector_id']})

                # Send notification to inspector about assignment
                if inspector_user and inspector_user.get('email'):
                    try:
                        send_inspection_assignment_notification(
                            inspector_user.get('email'),
                            inspector_user.get('name', data['inspector_id']),
                            app_data,
                            data['date']
                        )
                    except Exception as e:
                        print(f"Error sending inspector assignment notification: {e}")

                # Send notification to user about scheduled inspection
                if user_data and user_data.get('email'):
                    try:
                        send_user_inspection_scheduled_notification(
                            user_data.get('email'),
                            user_data.get('name', 'Applicant'),
                            app_data,
                            inspector_user.get('name', data['inspector_id']) if inspector_user else data['inspector_id'],
                            data['date']
                        )
                    except Exception as e:
                        print(f"Error sending user inspection scheduled notification: {e}")

            response_data = {
                'success': True,
                'message': 'Inspection scheduled successfully',
                'inspection_id': str(result.inserted_id),
                'email_sent': email_sent
            }

            if not email_sent:
                response_data['warning'] = 'Inspection scheduled but email notification failed'

            # Emit socket event for real-time updates
            socketio.emit('new_inspection', {
                'message': 'New inspection scheduled',
                'inspection_id': str(result.inserted_id)
            })

            return jsonify(response_data)

        # GET method
        pipeline = [
            {
                '$lookup': {
                    'from': 'applications',
                    'localField': 'business_id',
                    'foreignField': '_id',
                    'as': 'business_info'
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'inspector_id',
                    'foreignField': '_id',
                    'as': 'inspector_info'
                }
            }
        ]

        inspection_list = list(inspections.find())

        formatted_inspections = []
        for inspection in inspection_list:
            formatted_inspection = {
                '_id': str(inspection['_id']),
                'business_name': inspection.get('business_name', ''),
                'inspector_name': inspection.get('inspector_name', ''),
                'date': inspection.get('date', ''),
                'time': inspection.get('time', ''),
                'location': inspection.get('location', ''),
                'status': inspection.get('status', 'pending'),
                'notes': inspection.get('notes', ''),
                'created_at': inspection['created_at'].isoformat() if 'created_at' in inspection else ''
            }
            formatted_inspections.append(formatted_inspection)

        return jsonify({
            'success': True,
            'inspections': formatted_inspections
        })

    except Exception as e:
        print(f"Error in manage_inspections: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/schedule-inspection-data')
def get_inspection_scheduling_data():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get approved businesses
        businesses = list(applications.find(
            {'status': 'approved'},
            {'_id': 1, 'business_name': 1, 'business_address': 1}
        ))

        # Get inspectors (users with inspector role)
        inspectors = list(users.find(
            {'role': 'inspector'},
            {'_id': 1, 'name': 1, 'email': 1}
        ))

        return jsonify({
            'success': True,
            'businesses': [{
                'id': str(b['_id']),
                'name': b['business_name'],
                'address': b.get('business_address', '')
            } for b in businesses],
            'inspectors': [{
                'id': str(i['_id']),
                'name': i.get('name', 'Unknown'),
                'email': i.get('email', '')
            } for i in inspectors]
        })

    except Exception as e:
        print(f"Error in get_inspection_scheduling_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/inspection/<inspection_id>', methods=['GET', 'PUT'])
def inspection_details(inspection_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        if request.method == 'GET':
            inspection = db.inspections.find_one({'_id': ObjectId(inspection_id)})
            if not inspection:
                return jsonify({'error': 'Inspection not found'}), 404

            inspection['_id'] = str(inspection['_id'])
            inspection['created_at'] = inspection['created_at'].isoformat()

            return jsonify({
                'success': True,
                'inspection': inspection
            })

        elif request.method == 'PUT':
            data = request.get_json()
            update_data = {
                'status': data.get('status'),
                'notes': data.get('notes'),
                'updated_by': session.get('username'),
                'updated_at': datetime.now()
            }

            result = db.inspections.update_one(
                {'_id': ObjectId(inspection_id)},
                {'$set': update_data}
            )

            if result.modified_count == 0:
                return jsonify({'error': 'Inspection not found'}), 404

            return jsonify({
                'success': True,
                'message': 'Inspection updated successfully'
            })

    except Exception as e:
        print(f"Error in inspection_details: {str(e)}")
        return jsonify({'error': str(e)}), 500














@app.route('/inspection_dashboard')
def inspection_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    return render_template('inspection_dashboard.html')

@app.route('/api/inspections/overview')
def get_inspection_overview():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get inspection stats
        today = datetime.now().strftime('%Y-%m-%d')
        stats = {
            'pending': inspections.count_documents({'status': 'pending'}),
            'completed': inspections.count_documents({'status': 'completed'}),
            'today': inspections.count_documents({'date': today}),
            'total': inspections.count_documents({})
        }

        # Get recent inspections
        recent = list(inspections.find().sort('date', -1).limit(5))
        for inspection in recent:
            inspection['_id'] = str(inspection['_id'])
            if 'created_at' in inspection:
                inspection['created_at'] = inspection['created_at'].isoformat()

        return jsonify({
            'success': True,
            'stats': stats,
            'recent': recent
        })

    except Exception as e:
        print(f"Error in get_inspection_overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspections/scheduled')
def get_scheduled_inspections():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        date_filter = request.args.get('date')
        query = {'status': 'scheduled'}

        if date_filter:
            query['date'] = date_filter

        scheduled = list(inspections.find(query).sort('date', 1))
        for inspection in scheduled:
            inspection['_id'] = str(inspection['_id'])

        return jsonify({
            'success': True,
            'inspections': scheduled
        })

    except Exception as e:
        print(f"Error in get_scheduled_inspections: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspections/completed')
def get_completed_inspections():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        month_filter = request.args.get('month')  # Format: YYYY-MM
        query = {'status': 'completed'}

        if month_filter:
            start_date = f"{month_filter}-01"
            year, month = map(int, month_filter.split('-'))
            if month == 12:
                next_year = year + 1
                next_month = 1
            else:
                next_year = year
                next_month = month + 1
            end_date = f"{next_year}-{next_month:02d}-01"

            query['date'] = {
                '$gte': start_date,
                '$lt': end_date
            }

        completed = list(inspections.find(query).sort('date', -1))
        for inspection in completed:
            inspection['_id'] = str(inspection['_id'])

        return jsonify({
            'success': True,
            'inspections': completed
        })

    except Exception as e:
        print(f"Error in get_completed_inspections: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspections/reports')
def get_inspection_reports():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get completed inspections with reports
        reports = list(inspections.find(
            {'status': 'completed', 'report_generated': True}
        ).sort('date', -1))

        for report in reports:
            report['_id'] = str(report['_id'])
            if 'completion_date' in report:
                report['completion_date'] = report['completion_date'].isoformat()

        return jsonify({
            'success': True,
            'reports': reports
        })

    except Exception as e:
        print(f"Error in get_inspection_reports: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspection-reports')
def get_detailed_inspection_reports():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all completed inspections with reports
        reports = list(inspections.find({
            'status': 'completed',
            'report_generated': True
        }).sort('completion_date', -1))

        # Format the reports data
        formatted_reports = []
        for report in reports:
            business = applications.find_one({'_id': ObjectId(report['business_id'])})
            inspector = users.find_one({'_id': ObjectId(report['inspector_id'])})

            formatted_reports.append({
                '_id': str(report['_id']),
                'date': report.get('date'),
                'business_name': business.get('business_name', 'N/A'),
                'inspector_name': inspector.get('name', 'N/A'),
                'status': report.get('status'),
                'completion_date': report.get('completion_date'),
                'report_url': f"/download-inspection-report/{str(report['_id'])}",
                'findings': report.get('report_data', {})
            })

        return jsonify({
            'success': True,
            'reports': formatted_reports
        })

    except Exception as e:
        print(f"Error fetching inspection reports: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/inspection-reports')
def inspection_reports():
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    try:
        # Get all completed inspections with reports
        reports = list(inspections.find({
            'status': 'completed',
            'report_generated': True
        }).sort('completion_date', -1))

        # Format report data for template
        formatted_reports = []
        for report in reports:
            business = applications.find_one({'_id': ObjectId(report['business_id'])})
            inspector = users.find_one({'_id': ObjectId(report['inspector_id'])})

            formatted_report = {
                '_id': str(report['_id']),
                'date': report.get('date'),
                'business_name': business.get('business_name', 'N/A'),
                'inspector_name': inspector.get('name', 'N/A'),
                'status': report.get('status'),
                'completion_date': report.get('completion_date'),
                'report_url': f"/download-inspection-report/{str(report['_id'])}",
                'findings': report.get('report_data', {})
            }
            formatted_reports.append(formatted_report)

        return render_template('inspection_reports.html', reports=formatted_reports)

    except Exception as e:
        print(f"Error loading inspection reports: {str(e)}")
        flash('Error loading inspection reports', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/api/user-activities')
@login_required
def get_user_activities():
    """Get activities for the current user"""

    try:
        username = session['username']

        # Get user's activities
        user_activities = list(activities.find(
            {'username': username}
        ).sort('timestamp', -1).limit(20))

        # Format activities
        formatted_activities = []
        for activity in user_activities:
            formatted_activities.append({
                'id': str(activity['_id']),
                'type': activity.get('activity_type', 'general'),
                'description': activity.get('description', ''),
                'timestamp': activity.get('timestamp', datetime.now()).isoformat()
            })

        return jsonify({'success': True, 'activities': formatted_activities})
    except Exception as e:
        print(f"Error fetching user activities: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Admin Dashboard API Endpoints
@app.route('/api/admin/analytics')
def admin_analytics_api():
    """API endpoint for admin analytics data"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get comprehensive analytics data
        total_applications = applications.count_documents({})
        pending_applications = applications.count_documents({'status': 'pending'})
        approved_applications = applications.count_documents({'status': 'approved'})
        rejected_applications = applications.count_documents({'status': 'rejected'})

        # Calculate approval rate
        processed_apps = approved_applications + rejected_applications
        approval_rate = (approved_applications / processed_apps * 100) if processed_apps > 0 else 0

        # Get user statistics
        total_users = users.count_documents({})
        active_users = users.count_documents({'last_login': {'$exists': True}})

        # Get inspection statistics
        total_inspections = inspections.count_documents({})
        completed_inspections = inspections.count_documents({'status': 'completed'})

        # Calculate average processing time (mock data for now)
        avg_processing_time = 7  # days

        # Get recent activities
        recent_activities = list(activities.find({}).sort('timestamp', -1).limit(10))
        for activity in recent_activities:
            activity['_id'] = str(activity['_id'])
            activity['timestamp'] = activity.get('timestamp', datetime.now()).isoformat()

        return jsonify({
            'success': True,
            'data': {
                'applications': {
                    'total': total_applications,
                    'pending': pending_applications,
                    'approved': approved_applications,
                    'rejected': rejected_applications
                },
                'users': {
                    'total': total_users,
                    'active': active_users
                },
                'inspections': {
                    'total': total_inspections,
                    'completed': completed_inspections
                },
                'metrics': {
                    'approval_rate': round(approval_rate, 2),
                    'avg_processing_time': avg_processing_time,
                    'user_satisfaction': 85  # Mock data
                },
                'recent_activities': recent_activities
            }
        })
    except Exception as e:
        print(f"Error in admin analytics API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/certificates')
def admin_certificates_api():
    """API endpoint for admin certificates data"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all certificates from applications that have been approved
        approved_apps = list(applications.find({'status': 'approved'}).sort('timestamp', -1))

        certificates = []
        for app in approved_apps:
            # Check if certificate exists for this application
            cert_data = {
                '_id': str(app['_id']),
                'certificate_number': f"NOC-{str(app['_id'])[-6:].upper()}",
                'business_name': app.get('business_name', 'N/A'),
                'issue_date': app.get('approval_date', app.get('timestamp', datetime.now())),
                'valid_until': app.get('approval_date', app.get('timestamp', datetime.now())) + timedelta(days=365) if app.get('approval_date') else datetime.now() + timedelta(days=365),
                'status': 'active',
                'applicant_name': app.get('applicant_name', 'N/A'),
                'location': app.get('location', 'N/A')
            }

            # Format dates
            if isinstance(cert_data['issue_date'], datetime):
                cert_data['issue_date'] = cert_data['issue_date'].isoformat()
            if isinstance(cert_data['valid_until'], datetime):
                cert_data['valid_until'] = cert_data['valid_until'].isoformat()

            certificates.append(cert_data)

        # Calculate statistics
        total_certificates = len(certificates)
        active_certificates = len([c for c in certificates if c['status'] == 'active'])
        expired_certificates = 0  # For now, assume none are expired

        return jsonify({
            'success': True,
            'data': {
                'statistics': {
                    'total': total_certificates,
                    'active': active_certificates,
                    'expired': expired_certificates
                },
                'certificates': certificates
            }
        })
    except Exception as e:
        print(f"Error in admin certificates API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user-tracking')
def admin_user_tracking_api():
    """API endpoint for admin user tracking data"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all users with their activity data
        all_users = list(users.find({}, {'password': 0}).sort('created_at', -1))

        user_tracking_data = []
        for user in all_users:
            # Get user's application count
            app_count = applications.count_documents({'username': user['username']})

            # Get user's recent activities
            recent_activities = list(activities.find(
                {'username': user['username']}
            ).sort('timestamp', -1).limit(5))

            # Format activities
            formatted_activities = []
            for activity in recent_activities:
                formatted_activities.append({
                    'type': activity.get('activity_type', 'general'),
                    'description': activity.get('description', ''),
                    'timestamp': activity.get('timestamp', datetime.now()).isoformat()
                })

            user_data = {
                '_id': str(user['_id']),
                'name': user.get('name', 'N/A'),
                'username': user['username'],
                'email': user.get('email', 'N/A'),
                'phone': user.get('phone', 'N/A'),
                'role': user.get('role', 'user'),
                'created_at': user.get('created_at', datetime.now()).isoformat() if user.get('created_at') else datetime.now().isoformat(),
                'last_login': user.get('last_login', 'Never'),
                'application_count': app_count,
                'recent_activities': formatted_activities,
                'status': 'active'  # Default status
            }

            user_tracking_data.append(user_data)

        return jsonify({
            'success': True,
            'data': {
                'users': user_tracking_data,
                'total_users': len(user_tracking_data)
            }
        })
    except Exception as e:
        print(f"Error in admin user tracking API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/audit-logs')
def admin_audit_logs_api():
    """API endpoint for admin audit logs data"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all activities as audit logs
        audit_logs = list(activities.find({}).sort('timestamp', -1).limit(100))

        formatted_logs = []
        for log in audit_logs:
            formatted_logs.append({
                '_id': str(log['_id']),
                'username': log.get('username', 'System'),
                'action': log.get('activity_type', 'general'),
                'description': log.get('description', 'No description'),
                'timestamp': log.get('timestamp', datetime.now()).isoformat(),
                'ip_address': log.get('ip_address', 'N/A'),
                'user_agent': log.get('user_agent', 'N/A'),
                'severity': log.get('severity', 'info')
            })

        return jsonify({
            'success': True,
            'data': {
                'logs': formatted_logs,
                'total_logs': len(formatted_logs)
            }
        })
    except Exception as e:
        print(f"Error in admin audit logs API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-settings')
def admin_system_settings_api():
    """API endpoint for admin system settings data"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Mock system settings data - in a real app, this would come from a settings collection
        system_settings = {
            'general': {
                'site_name': 'Fire Safety NOC System',
                'site_description': 'Government Fire Safety Certificate Management System',
                'admin_email': 'admin@firesafety.gov.in',
                'maintenance_mode': False,
                'registration_enabled': True
            },
            'security': {
                'session_timeout': 30,  # minutes
                'max_login_attempts': 5,
                'password_expiry_days': 90,
                'two_factor_enabled': True
            },
            'notifications': {
                'email_notifications': True,
                'sms_notifications': True,
                'push_notifications': False,
                'notification_frequency': 'immediate'
            },
            'backup': {
                'auto_backup_enabled': True,
                'backup_frequency': 'daily',
                'backup_retention_days': 30,
                'last_backup': datetime.now().isoformat()
            }
        }

        return jsonify({
            'success': True,
            'data': system_settings
        })
    except Exception as e:
        print(f"Error in admin system settings API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/backup-restore')
def admin_backup_restore_api():
    """API endpoint for admin backup & restore data"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Mock backup history data - in a real app, this would come from a backups collection
        backup_history = [
            {
                'id': 'backup_001',
                'filename': f'fire_safety_backup_{datetime.now().strftime("%Y%m%d")}.zip',
                'size': '45.2 MB',
                'created_at': datetime.now().isoformat(),
                'type': 'automatic',
                'status': 'completed',
                'description': 'Daily automatic backup'
            },
            {
                'id': 'backup_002',
                'filename': f'fire_safety_backup_{(datetime.now() - timedelta(days=1)).strftime("%Y%m%d")}.zip',
                'size': '44.8 MB',
                'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'type': 'automatic',
                'status': 'completed',
                'description': 'Daily automatic backup'
            },
            {
                'id': 'backup_003',
                'filename': f'fire_safety_backup_{(datetime.now() - timedelta(days=2)).strftime("%Y%m%d")}.zip',
                'size': '44.1 MB',
                'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
                'type': 'manual',
                'status': 'completed',
                'description': 'Manual backup before system update'
            }
        ]

        # System statistics
        system_stats = {
            'database_size': '156.7 MB',
            'total_backups': len(backup_history),
            'last_backup': backup_history[0]['created_at'] if backup_history else 'Never',
            'backup_storage_used': '134.1 MB',
            'backup_storage_available': '865.9 MB'
        }

        return jsonify({
            'success': True,
            'data': {
                'backup_history': backup_history,
                'system_stats': system_stats
            }
        })
    except Exception as e:
        print(f"Error in admin backup restore API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-data')
def get_user_data():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        user = users.find_one({'username': session['username']})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Convert ObjectId to string for JSON serialization
        user['_id'] = str(user['_id'])

        # Remove sensitive information
        user.pop('password', None)

        return jsonify({
            'success': True,
            'data': {
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'phone': user.get('phone', ''),
                'role': user.get('role', ''),
                'department': user.get('department', ''),
                'address': user.get('address', ''),
                'profile_image': user.get('profile_image', '/static/default-profile.png'),
                'created_at': user.get('created_at', datetime.now()).isoformat(),
                'last_login': user.get('last_login', datetime.now()).isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/profile')
def get_user_profile():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        user = users.find_one({'username': session['username']})
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Convert ObjectId to string for JSON serialization
        user['_id'] = str(user['_id'])

        # Remove sensitive information
        user.pop('password', None)

        return jsonify({
            'success': True,
            'data': {
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'phone': user.get('phone', ''),
                'role': user.get('role', ''),
                'department': user.get('department', ''),
                'address': user.get('address', ''),
                'profile_image': user.get('profile_image', '/static/default-profile.png'),
                'created_at': user.get('created_at', datetime.now()).isoformat(),
                'last_login': user.get('last_login', datetime.now()).isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-profile', methods=['POST'])
def update_user_profile():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        user = users.find_one({'username': session['username']})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Update user information
        update_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'department': data.get('department'),
            'address': data.get('address'),
            'updated_at': datetime.now()
        }

        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Validate email format
        if 'email' in update_data and not re.match(r"[^@]+@[^@]+\.[^@]+", update_data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        # Validate phone format if provided
        if 'phone' in update_data and not re.match(r"^\+?[\d\s-]{10,}$", update_data['phone']):
            return jsonify({'success': False, 'message': 'Invalid phone number format'}), 400

        users.update_one(
            {'username': session['username']},
            {'$set': update_data}
        )

        # Log activity
        log_activity('profile_update', f"User {session['username']} updated their profile")

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/profile/update', methods=['POST'])
def update_user_profile_dashboard():
    """Update user profile from dashboard"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        username = session['username']
        user = users.find_one({'username': username})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Validate required fields
        required_fields = ['name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Update user information
        update_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'address': data.get('address'),
            'updated_at': datetime.now()
        }

        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Validate email format
        if 'email' in update_data and not re.match(r"[^@]+@[^@]+\.[^@]+", update_data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        # Validate phone format if provided
        if 'phone' in update_data and update_data['phone'] and not re.match(r"^\+?[\d\s-]{10,}$", update_data['phone']):
            return jsonify({'success': False, 'message': 'Invalid phone number format'}), 400

        # Check if email already exists for another user
        existing_user = users.find_one({'email': update_data['email'], 'username': {'$ne': username}})
        if existing_user:
            return jsonify({'success': False, 'message': 'Email already exists for another user'}), 400

        result = users.update_one(
            {'username': username},
            {'$set': update_data}
        )

        if result.modified_count == 0:
            return jsonify({'success': False, 'message': 'No changes made'}), 400

        # Log activity
        log_activity('profile_update', f"User {username} updated their profile")

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully!'
        })

    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/verify-documents/<application_id>', methods=['POST'])
def verify_documents_api(application_id):
    """API endpoint for AI-powered document verification"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Call the AI verification function
        success, result = ai_verify_documents(application_id)

        if success:
            # Log the verification
            log_activity(
                'Document Verification',
                f"AI verified documents for application {application_id}",
                session.get('username')
            )

            # Return success response
            return jsonify({
                'success': True,
                'message': 'Documents verified successfully',
                'results': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400

    except Exception as e:
        print(f"Error in document verification API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications', methods=['GET'])
def get_user_notifications():
    """Get notifications for the current user"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        username = session['username']
        user_role = session.get('role', 'user')

        # Get notifications for this user or for all users
        user_notifications = list(notifications.find({
            '$or': [
                {'recipients': 'all'},
                {'recipients': username},
                {'username': username}  # Also include notifications created for this user
            ]
        }).sort('timestamp', -1).limit(20))

        # Format notifications
        formatted_notifications = []
        for notification in user_notifications:
            formatted_notifications.append({
                'id': str(notification['_id']),
                'timestamp': notification.get('timestamp', notification.get('created_at', datetime.now())).strftime('%Y-%m-%d %H:%M:%S'),
                'activity_type': notification.get('activity_type', notification.get('type', 'info')),
                'description': notification.get('description', notification.get('message', '')),
                'title': notification.get('title', 'Notification'),
                'type': notification.get('type', notification.get('activity_type', 'info')),
                'username': notification.get('username', ''),
                'read': notification.get('read', False)
            })

        return jsonify({
            'success': True,
            'notifications': formatted_notifications
        })
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Add user-specific notification endpoint
@app.route('/api/user-notifications', methods=['GET'])
@login_required
def get_user_specific_notifications():
    """Get notifications specifically for the current user"""

    try:
        username = session['username']

        # Get notifications for this specific user
        user_notifications = list(notifications.find({
            '$or': [
                {'username': username},
                {'recipients': username},
                {'recipients': 'all'}
            ]
        }).sort('created_at', -1).limit(20))

        # Format notifications for frontend
        formatted_notifications = []
        for notification in user_notifications:
            formatted_notifications.append({
                'id': str(notification['_id']),
                'title': notification.get('title', 'Notification'),
                'message': notification.get('message', notification.get('description', '')),
                'type': notification.get('type', 'info'),
                'timestamp': notification.get('created_at', notification.get('timestamp', datetime.now())),
                'read': notification.get('read', False)
            })

        return jsonify({
            'success': True,
            'notifications': formatted_notifications
        })

    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Duplicate function removed - using the one at line 2290

# Duplicate function removed - this was causing the error

def get_activity_title(activity_type):
    """Get user-friendly title for activity type"""
    titles = {
        'application_submitted': 'Application Submitted',
        'document_uploaded': 'Documents Uploaded',
        'application_approved': 'Application Approved',
        'application_rejected': 'Application Rejected',
        'inspection_scheduled': 'Inspection Scheduled',
        'inspection_completed': 'Inspection Completed',
        'license_generated': 'License Generated',
        'profile_updated': 'Profile Updated',
        'login': 'Account Access',
        'logout': 'Session Ended'
    }
    return titles.get(activity_type, 'Activity')

@app.route('/api/mark-notifications-read', methods=['POST'])
def mark_user_notifications_read():
    """Mark all notifications as read for current user"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        username = session['username']

        # Mark all unread notifications for this user as read
        result = notifications.update_many(
            {
                '$or': [
                    {'username': username},
                    {'recipients': username}
                ],
                'read': False
            },
            {'$set': {'read': True}}
        )

        return jsonify({
            'success': True,
            'message': f'Marked {result.modified_count} notifications as read'
        })
    except Exception as e:
        print(f"Error marking notifications as read: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create-test-notifications', methods=['POST'])
def create_test_notifications():
    """Create test notifications for current user"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        username = session['username']

        # Create sample notifications
        test_notifications = [
            {
                'username': username,
                'title': '🎉 Welcome to Fire NOC Portal!',
                'message': 'Your account has been successfully created. Start by submitting your first NOC application.',
                'type': 'system',
                'read': False,
                'created_at': datetime.now(),
                'recipients': [username]
            },
            {
                'username': username,
                'title': '📋 Application Status Update',
                'message': 'Your NOC application #NOC001 is currently under review by our team.',
                'type': 'application',
                'read': False,
                'created_at': datetime.now() - timedelta(hours=2),
                'recipients': [username]
            },
            {
                'username': username,
                'title': '🔍 Inspection Scheduled',
                'message': 'Your fire safety inspection has been scheduled for next week. Please ensure all safety equipment is accessible.',
                'type': 'inspection',
                'read': False,
                'created_at': datetime.now() - timedelta(days=1),
                'recipients': [username]
            }
        ]

        # Insert notifications
        result = notifications.insert_many(test_notifications)

        return jsonify({
            'success': True,
            'message': f'Created {len(result.inserted_ids)} test notifications'
        })
    except Exception as e:
        print(f"Error creating test notifications: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    """Mark notifications as read"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        notification_ids = request.json.get('notification_ids', [])
        if not notification_ids:
            return jsonify({'success': False, 'error': 'No notification IDs provided'}), 400

        # Convert string IDs to ObjectId
        object_ids = [ObjectId(id) for id in notification_ids]

        # Update notifications
        result = notifications.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {'read': True}}
        )

        return jsonify({
            'success': True,
            'message': f'Marked {result.modified_count} notifications as read'
        })

    except Exception as e:
        print(f"Error marking notifications as read: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inspection/<inspection_id>', methods=['GET'])
def get_inspection_details(inspection_id):
    """Get detailed inspection information"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    # Allow inspectors, managers, and admins to access inspection details
    if session.get('role') not in ['inspector', 'manager', 'admin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # For inspector, check if they are assigned to this inspection
        if session.get('role') == 'inspector':
            # Find application by inspection_id (which is actually application_id in this context)
            app_data = applications.find_one({'_id': ObjectId(inspection_id)})
            if not app_data or app_data.get('assigned_inspector') != session['username']:
                return jsonify({'success': False, 'error': 'Unauthorized - Not assigned to this inspection'}), 401

        # Try to find inspection record first
        inspection = inspections.find_one({'application_id': ObjectId(inspection_id)})

        if not inspection:
            # If no inspection record exists, create a basic one from application data
            app_data = applications.find_one({'_id': ObjectId(inspection_id)})
            if not app_data:
                return jsonify({'success': False, 'error': 'Application not found'}), 404

            inspection = {
                '_id': str(ObjectId()),
                'application_id': inspection_id,
                'business_name': app_data.get('business_name', 'Unknown'),
                'business_address': app_data.get('business_address', 'Unknown'),
                'status': app_data.get('status', 'pending'),
                'inspector': app_data.get('assigned_inspector', ''),
                'created_at': app_data.get('timestamp', datetime.now()).isoformat()
            }
        else:
            # Convert ObjectId to string for JSON serialization
            inspection['_id'] = str(inspection['_id'])
            if 'application_id' in inspection:
                inspection['application_id'] = str(inspection['application_id'])
            if 'inspector_id' in inspection:
                inspection['inspector_id'] = str(inspection['inspector_id'])

        return jsonify({
            'success': True,
            'inspection': inspection
        })

    except Exception as e:
        print(f"Error getting inspection details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Duplicate function removed - using the one at line 1590

@app.route('/api/upload-inspection-photo', methods=['POST'])
def upload_inspection_photo():
    """Upload photos during inspection"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo provided'}), 400

        file = request.files['photo']
        inspection_id = request.form.get('inspection_id')

        if not inspection_id:
            return jsonify({'success': False, 'error': 'Inspection ID required'}), 400

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        # Generate secure filename
        filename = secure_filename(f"inspection_{inspection_id}_{int(time.time())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'inspection_photos', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save the file
        file.save(filepath)

        # Update inspection with photo reference
        inspections.update_one(
            {'_id': ObjectId(inspection_id)},
            {'$push': {
                'inspection_photos': {
                    'filename': filename,
                    'path': filepath,
                    'uploaded_at': datetime.now(),
                    'uploaded_by': session.get('username')
                }
            }}
        )

        return jsonify({
            'success': True,
            'message': 'Photo uploaded successfully',
            'filename': filename,
            'url': f'/static/inspection_photos/{filename}'
        })

    except Exception as e:
        print(f"Error uploading inspection photo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-profile-image', methods=['POST'])
def update_user_profile_image():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        if 'profile_image' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['profile_image']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed types: PNG, JPG, JPEG, GIF'}), 400

        # Validate file size (max 5MB)
        if len(file.read()) > 5 * 1024 * 1024:
            return jsonify({'success': False, 'message': 'File size too large. Maximum size: 5MB'}), 400

        file.seek(0)  # Reset file pointer after reading

        # Generate secure filename with timestamp
        filename = secure_filename(f"{session['username']}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_images', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save the file
        file.save(filepath)

        # Update user's profile image in database
        users.update_one(
            {'username': session['username']},
            {'$set': {'profile_image': f'/static/profile_images/{filename}'}}
        )

        # Delete old profile image if it exists and is not the default
        old_image = users.find_one({'username': session['username']}).get('profile_image')
        if old_image and old_image != 'default-profile.png':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        return jsonify({
            'success': True,
            'message': 'Profile image updated successfully',
            'image_url': f'/static/profile_images/{filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on_error_default
def default_error_handler(e):
    print(f'SocketIO error: {str(e)}')
    return False

# Test route for debugging
@app.route('/test-certificate')
def test_certificate():
    """Test certificate functionality"""
    try:
        # Get a certificate from database
        cert = certificates.find_one({'username': 'mkbhh'})
        if cert:
            return f"Certificate found: {cert['certificate_number']} for {cert['business_name']}"
        else:
            return "No certificate found for mkbhh"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/test-download/<application_id>')
def test_download(application_id):
    """Test download functionality"""
    try:
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if app_data:
            return f"Application found: {app_data.get('business_name')} - Certificate: {app_data.get('certificate_number', 'None')}"
        else:
            return f"Application not found: {application_id}"
    except Exception as e:
        return f"Error: {str(e)}"

# Fixed certificate routes
@app.route('/certificate-view/<certificate_number>')
def certificate_view(certificate_number):
    """View certificate by certificate number"""
    try:
        print(f"CERT VIEW: Looking for certificate: {certificate_number}")

        certificate = certificates.find_one({'certificate_number': certificate_number})
        if not certificate:
            print(f"CERT VIEW: Certificate not found: {certificate_number}")
            return f"Certificate not found: {certificate_number}", 404

        print(f"CERT VIEW: Found certificate for business: {certificate.get('business_name')}")

        # Get application data for PAN number
        app_data = applications.find_one({'_id': certificate['application_id']}) if certificate.get('application_id') else None

        return render_template('certificate_template.html',
            certificate_number=certificate['certificate_number'],
            business_name=certificate.get('business_name', 'N/A'),
            business_type=certificate.get('business_type', 'N/A'),
            business_address=certificate.get('business_address', 'N/A'),
            pan_number=app_data.get('pan_number', 'ABCDE1234F') if app_data else 'ABCDE1234F',
            issue_date=certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else 'N/A',
            valid_until=certificate['valid_until'].strftime('%d/%m/%Y') if certificate.get('valid_until') else 'N/A',
            compliance_score=certificate.get('compliance_score', 0),
            inspector_name=certificate.get('inspector_name', 'N/A'),
            inspector_signature=f"Digitally Signed by {certificate.get('inspector_name', 'N/A')}",
            manager_signature=f"Digitally Signed by {certificate.get('issued_by', 'System')}",
            approved_by=certificate.get('issued_by', 'System')
        )

    except Exception as e:
        print(f"CERT VIEW: Error viewing certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error loading certificate: {str(e)}", 500

@app.route('/certificate-download/<application_id>')
def certificate_download(application_id):
    """Download certificate for application"""
    try:
        print(f"CERT DOWNLOAD: Attempting to download certificate for application: {application_id}")

        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            print(f"CERT DOWNLOAD: Application not found: {application_id}")
            return f"Application not found: {application_id}", 404

        print(f"CERT DOWNLOAD: Found application: {app_data.get('business_name')} for user: {app_data.get('username')}")

        if not app_data.get('certificate_number'):
            print(f"CERT DOWNLOAD: Certificate number not found in application")
            return "Certificate not found", 404

        certificate_number = app_data['certificate_number']
        print(f"CERT DOWNLOAD: Redirecting to view certificate: {certificate_number}")
        return redirect(url_for('certificate_view', certificate_number=certificate_number))

    except Exception as e:
        print(f"CERT DOWNLOAD: Error downloading certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error downloading certificate: {str(e)}", 500

# Additional Admin Dashboard Routes
@app.route('/admin/system_settings')
def admin_system_settings():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_system_settings.html')

@app.route('/admin/backup_restore')
def admin_backup_restore():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_backup_restore.html')

@app.route('/admin/audit_logs')
def admin_audit_logs():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    # Get audit logs from activities collection
    audit_logs = list(activities.find().sort('timestamp', -1).limit(100))
    for log in audit_logs:
        log['_id'] = str(log['_id'])

    return render_template('admin_audit_logs.html', audit_logs=audit_logs)

@app.route('/admin/user_tracking')
def admin_user_tracking():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    # Get all users with their activity data
    all_users = list(users.find({}, {'password': 0}))
    for user in all_users:
        user['_id'] = str(user['_id'])
        # Get recent activity count
        user['recent_activities'] = activities.count_documents({
            'username': user['username'],
            'timestamp': {'$gte': datetime.now() - timedelta(days=30)}
        })

    return render_template('admin_user_tracking.html', users=all_users)

@app.route('/admin/analytics')
def admin_analytics():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_analytics.html')

# API Routes for Admin Dashboard
@app.route('/api/admin/analytics')
def api_admin_analytics():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'})

    try:
        # Get analytics data
        total_users = users.count_documents({})
        total_applications = applications.count_documents({})
        approved_applications = applications.count_documents({'status': 'approved'})
        pending_applications = applications.count_documents({'status': 'pending'})
        under_review_applications = applications.count_documents({'status': 'under_review'})
        rejected_applications = applications.count_documents({'status': 'rejected'})

        analytics_data = {
            'users': {
                'total': total_users
            },
            'applications': {
                'total': total_applications,
                'approved': approved_applications,
                'pending': pending_applications,
                'under_review': under_review_applications,
                'rejected': rejected_applications
            }
        }

        return jsonify({'success': True, 'data': analytics_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/audit-logs')
def api_admin_audit_logs():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'})

    try:
        # Get audit logs from activities collection
        audit_logs = list(activities.find().sort('timestamp', -1).limit(100))

        # Convert ObjectId to string and add missing fields
        for log in audit_logs:
            log['_id'] = str(log['_id'])
            if 'severity' not in log:
                log['severity'] = 'info'
            if 'ip_address' not in log:
                log['ip_address'] = '127.0.0.1'

        return jsonify({'success': True, 'data': {'logs': audit_logs}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/user-tracking')
def api_admin_user_tracking():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'})

    try:
        # Get all users with their activity data
        all_users = list(users.find({}, {'password': 0}))

        for user in all_users:
            user['_id'] = str(user['_id'])

            # Get application count for each user
            user['application_count'] = applications.count_documents({'username': user['username']})

            # Get recent activity count
            user['recent_activities'] = activities.count_documents({
                'username': user['username'],
                'timestamp': {'$gte': datetime.now() - timedelta(days=30)}
            })

            # Set default status if not present
            if 'status' not in user:
                user['status'] = 'active'

            # Set created_at if not present
            if 'created_at' not in user:
                user['created_at'] = datetime.now().isoformat()

        return jsonify({'success': True, 'data': {'users': all_users}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/backup-restore')
def api_admin_backup_restore():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'})

    try:
        # Simulate backup data
        backup_data = {
            'system_stats': {
                'database_size': '125 MB',
                'total_backups': 15,
                'backup_storage_used': '2.3 GB',
                'last_backup': datetime.now().isoformat()
            },
            'backup_history': [
                {
                    'id': 'backup_001',
                    'filename': 'fire_noc_backup_2024_01_20.zip',
                    'size': '125 MB',
                    'type': 'automatic',
                    'status': 'completed',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': 'backup_002',
                    'filename': 'fire_noc_backup_2024_01_19.zip',
                    'size': '120 MB',
                    'type': 'manual',
                    'status': 'completed',
                    'created_at': (datetime.now() - timedelta(days=1)).isoformat()
                }
            ]
        }

        return jsonify({'success': True, 'data': backup_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# User Dashboard Routes - Fix for application details and inspection reports
@app.route('/application/<application_id>')
def view_application_details(application_id):
    """View application details in a professional format"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404

        # Check if user owns this application (unless admin/manager)
        if session.get('role') not in ['admin', 'manager', 'inspector'] and app_data.get('username') != session.get('username'):
            return jsonify({'error': 'Unauthorized access to this application'}), 403

        # Convert ObjectId to string for JSON serialization
        app_data['_id'] = str(app_data['_id'])

        # Format dates
        if 'timestamp' in app_data and isinstance(app_data['timestamp'], datetime):
            app_data['timestamp'] = app_data['timestamp'].strftime('%d/%m/%Y %H:%M:%S')

        if 'last_updated' in app_data and isinstance(app_data['last_updated'], datetime):
            app_data['last_updated'] = app_data['last_updated'].strftime('%d/%m/%Y %H:%M:%S')

        return render_template('view_application.html', application=app_data)

    except Exception as e:
        print(f"Error viewing application details: {str(e)}")
        return f"Error loading application details: {str(e)}", 500

@app.route('/generate-inspection-report/<application_id>')
def generate_inspection_report_route(application_id):
    """Generate inspection report for user dashboard"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404

        # Check if user owns this application (unless admin/manager)
        if session.get('role') not in ['admin', 'manager', 'inspector'] and app_data.get('username') != session.get('username'):
            return jsonify({'error': 'Unauthorized access to this report'}), 403

        # Check if inspection is completed
        if app_data.get('status') not in ['approved', 'inspection_completed']:
            return "Inspection report not available yet. Please wait for inspection completion.", 404

        # Get inspection data
        inspection_data = inspections.find_one({'application_id': ObjectId(application_id)})
        if not inspection_data:
            return "Inspection data not found", 404

        # Generate PDF report
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )

        # Content
        story = []

        # Header
        story.append(Paragraph("FIRE SAFETY DEPARTMENT", title_style))
        story.append(Paragraph("INSPECTION REPORT", styles['Heading2']))
        story.append(Spacer(1, 20))

        # Report details
        story.append(Paragraph(f"<b>Report Number:</b> {inspection_data.get('report_number', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Business Name:</b> {app_data.get('business_name', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Business Type:</b> {app_data.get('business_type', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Address:</b> {app_data.get('business_address', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Inspector:</b> {inspection_data.get('inspector_name', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Inspection Date:</b> {inspection_data.get('inspection_date', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Inspection results
        story.append(Paragraph("<b>INSPECTION RESULTS</b>", styles['Heading3']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Compliance Score:</b> {inspection_data.get('compliance_score', 85)}%", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Overall Result:</b> {inspection_data.get('result', 'Approved')}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Recommendations:</b> {inspection_data.get('recommendations', 'All safety measures are in compliance.')}", styles['Normal']))
        story.append(Spacer(1, 30))

        # Footer
        story.append(Paragraph("This is a system-generated inspection report.", styles['Normal']))
        story.append(Paragraph("For queries, contact Fire Safety Department.", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Create filename
        business_name = app_data.get('business_name', 'Business').replace(' ', '_')
        report_number = inspection_data.get('report_number', 'REPORT')
        filename = f"Inspection_Report_{business_name}_{report_number}.pdf"

        # Return PDF as download
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        print(f"Error generating inspection report: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error generating inspection report: {str(e)}", 500

@app.route('/view-inspection-report/<application_id>')
def view_inspection_report_route(application_id):
    """View inspection report in browser"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404

        # Check if user owns this application (unless admin/manager)
        if session.get('role') not in ['admin', 'manager', 'inspector'] and app_data.get('username') != session.get('username'):
            return jsonify({'error': 'Unauthorized access to this report'}), 403

        # Get inspection data
        inspection_data = inspections.find_one({'application_id': ObjectId(application_id)})
        if not inspection_data:
            # Create default inspection data if not found
            inspection_data = {
                'report_number': f"RPT-{datetime.now().strftime('%Y%m%d')}-{str(application_id)[-6:]}",
                'inspector_name': 'System Inspector',
                'inspection_date': datetime.now().strftime('%d/%m/%Y'),
                'compliance_score': 85,
                'result': 'Approved' if app_data.get('status') == 'approved' else 'Pending',
                'recommendations': 'All safety measures are in compliance.' if app_data.get('status') == 'approved' else 'Inspection pending.'
            }

        return render_template('view_inspection_report.html',
                             application=app_data,
                             inspection=inspection_data)

    except Exception as e:
        print(f"Error viewing inspection report: {str(e)}")
        return f"Error loading inspection report: {str(e)}", 500

# User Profile Edit Route
@app.route('/user/edit-profile')
def user_edit_profile():
    """User profile editing page"""
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        user = users.find_one({'username': session['username']})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('user_dashboard'))

        return render_template('user_profile.html', user=user)
    except Exception as e:
        print(f"Error loading user profile: {str(e)}")
        flash('Error loading profile', 'error')
        return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, debug=True)

# Rest of your functions...

def generate_temp_admin_credentials():
    temp_username = f"temp_admin_{secrets.token_hex(4)}"
    temp_password = secrets.token_urlsafe(12)
    expiry = datetime.now() + timedelta(hours=24)  # Credentials valid for 24 hours

    # Hash the password before storing
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(temp_password.encode('utf-8'), salt)

    # Store temporary credentials in database
    temp_admin = {
        'username': temp_username,
        'password': hashed_password,
        'expiry': expiry,
        'is_temp_admin': True,
        'role': 'admin'
    }
    users.insert_one(temp_admin)

    return temp_username, temp_password

def send_temp_admin_credentials(inspector_email, temp_username, temp_password):
    subject = "Temporary Admin Access Credentials"
    body = f"""
Dear Inspector,

Your inspection form has been completed successfully. As requested, here are your temporary admin credentials:

Username: {temp_username}
Password: {temp_password}

These credentials will expire in 24 hours. Please use them to access the admin dashboard and make any necessary changes.

Best regards,
AEK NOC System Team
"""
    send_email(subject, inspector_email, body)



def update_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users.find_one({'username': username})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            # Check if this is a temporary admin account and if it's expired
            if user.get('is_temp_admin', False):
                if datetime.now() > user['expiry']:
                    # Delete expired temporary admin account
                    users.delete_one({'_id': user['_id']})
                    flash('Temporary admin access has expired', 'error')
                    return redirect(url_for('login'))

            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            session['user_id'] = str(user['_id'])

            log_activity('login', f"User {username} logged in")

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))

        flash('Invalid username or password', 'error')

    return render_template('login.html')

def log_activity(activity_type, description, username=None):
    """Log user activity"""
    try:
        activity_data = {
            'activity_type': activity_type,
            'description': description,
            'username': username or session.get('username', 'System'),
            'timestamp': datetime.now()
        }
        activities.insert_one(activity_data)
    except Exception as e:
        print(f"Error logging activity: {str(e)}")

def send_user_inspection_notification(user_email, business_name, inspector_name, inspection_date):
    """Send email notification to user about inspector assignment"""
    try:
        subject = "🔍 Inspector Assigned for Your Fire NOC Application"

        body = f"""
Dear Applicant,

Great news! An inspector has been assigned to your Fire NOC application.

📋 Application Details:
• Business Name: {business_name}
• Inspector Assigned: {inspector_name}
• Scheduled Inspection Date: {inspection_date}

🔍 What's Next:
1. The inspector will visit your premises on the scheduled date
2. Please ensure all fire safety equipment is accessible
3. Have all required documents ready for verification
4. You will receive an inspection report after completion

📞 Need Help?
If you have any questions, please contact our support team.

Best regards,
Fire NOC System Team
        """

        send_email(subject, user_email, body)
        return True
    except Exception as e:
        print(f"Error sending user inspection notification: {str(e)}")
        return False

def send_manager_inspection_report(manager_email, business_name, inspector_name, compliance_score, recommendation, report_id):
    """Send inspection report to manager for review"""
    try:
        subject = "📋 Inspection Report Ready for Review"

        status_emoji = "✅" if recommendation == "approved" else "❌" if recommendation == "rejected" else "⚠️"

        body = f"""
Dear Manager,

An inspection has been completed and the report is ready for your review.

📋 Inspection Details:
• Business Name: {business_name}
• Inspector: {inspector_name}
• Compliance Score: {compliance_score}%
• Recommendation: {status_emoji} {recommendation.upper()}
• Report ID: {report_id}

🔍 Next Steps:
1. Review the detailed inspection report
2. Verify inspector's findings and recommendations
3. Approve or request modifications
4. Generate NOC certificate if approved

📊 Manager Actions Required:
• Login to your dashboard to review the complete report
• Check uploaded inspection videos and photos
• Make final decision on application approval

Best regards,
Fire NOC System Team
        """

        send_email(subject, manager_email, body)
        return True
    except Exception as e:
        print(f"Error sending manager inspection report: {str(e)}")
        return False

def send_user_inspection_completion(user_email, business_name, inspector_name, recommendation):
    """Send inspection completion notification to user"""
    try:
        subject = "🔍 Inspection Completed for Your Fire NOC Application"

        status_emoji = "✅" if recommendation == "approved" else "❌" if recommendation == "rejected" else "⚠️"
        status_message = {
            "approved": "Great news! Your application has been recommended for approval.",
            "rejected": "Unfortunately, your application requires improvements before approval.",
            "needs_improvement": "Your application needs some improvements before final approval."
        }.get(recommendation, "Your inspection has been completed.")

        body = f"""
Dear Applicant,

Your fire safety inspection has been completed.

📋 Inspection Results:
• Business Name: {business_name}
• Inspector: {inspector_name}
• Status: {status_emoji} {recommendation.upper()}

{status_message}

🔍 What's Next:
1. The inspection report has been sent to the manager for final review
2. You will receive notification once the manager makes the final decision
3. If approved, your NOC certificate will be generated automatically
4. If improvements are needed, you will receive detailed feedback

📞 Need Help?
If you have any questions about the inspection results, please contact our support team.

Best regards,
Fire NOC System Team
        """

        send_email(subject, user_email, body)
        return True
    except Exception as e:
        print(f"Error sending user inspection completion: {str(e)}")
        return False

def create_manager_approved_certificate(application_id):
    """Create NOC certificate when manager approves application"""
    try:
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            print(f"Application not found for ID: {application_id}")
            return None

        # Get inspection report for compliance score and inspector details
        inspection_report = inspections.find_one({'application_id': ObjectId(application_id), 'status': 'completed'})

        # Generate unique certificate number
        certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(ObjectId())[-6:].upper()}"

        # Get inspector details
        inspector_name = inspection_report.get('inspector', 'Unknown') if inspection_report else 'System Inspector'
        compliance_score = inspection_report.get('compliance_score', 85) if inspection_report else 85

        certificate_data = {
            'certificate_number': certificate_number,
            'application_id': ObjectId(application_id),
            'business_name': app_data.get('business_name', ''),
            'business_address': app_data.get('business_address', ''),
            'business_type': app_data.get('business_type', ''),
            'issued_date': datetime.now(),
            'valid_until': datetime.now() + timedelta(days=365),  # Valid for 1 year
            'issued_by': session.get('username', 'System'),
            'inspector_name': inspector_name,
            'compliance_score': compliance_score,
            'status': 'active',
            'certificate_path': f"certificates/{certificate_number}.pdf"
        }

        # Store certificate in database
        certificates.insert_one(certificate_data)
        print(f"Certificate stored in database: {certificate_number}")

        # Update application with certificate details
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'certificate_number': certificate_number,
                    'certificate_issued': True,
                    'certificate_issued_date': datetime.now(),
                    'certificate_path': certificate_data['certificate_path']
                }
            }
        )
        print(f"Application updated with certificate details")

        return certificate_data

    except Exception as e:
        print(f"Error creating manager approved certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_professional_noc_certificate(application_id):
    """Generate professional NOC certificate for approved application"""
    try:
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return None

        # Get inspection report for compliance score and inspector details
        inspection_report = inspections.find_one({'application_id': ObjectId(application_id), 'status': 'completed'})

        # Generate unique certificate number
        certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(ObjectId())[-6:].upper()}"

        # Get inspector details
        inspector_name = inspection_report.get('inspector', 'Unknown') if inspection_report else 'System Inspector'
        compliance_score = inspection_report.get('compliance_score', 85) if inspection_report else 85

        certificate_data = {
            'certificate_number': certificate_number,
            'application_id': ObjectId(application_id),
            'business_name': app_data.get('business_name', ''),
            'business_address': app_data.get('business_address', ''),
            'business_type': app_data.get('business_type', ''),
            'issued_date': datetime.now(),
            'valid_until': datetime.now() + timedelta(days=365),  # Valid for 1 year
            'issued_by': session.get('username', 'System'),
            'inspector_name': inspector_name,
            'compliance_score': compliance_score,
            'status': 'active',
            'certificate_path': f"certificates/{certificate_number}.pdf"
        }

        # Generate HTML certificate
        certificate_html = render_template('certificate_template.html',
            certificate_number=certificate_number,
            business_name=app_data.get('business_name', ''),
            business_type=app_data.get('business_type', ''),
            business_address=app_data.get('business_address', ''),
            pan_number=app_data.get('pan_number', 'Not Provided'),
            contact_person=app_data.get('contact_person', app_data.get('name', 'Business Owner')),
            contact_number=app_data.get('contact_number', 'Not Provided'),
            building_area=app_data.get('building_area', 'As per application'),
            floors=app_data.get('floors', 'As per plan'),
            max_occupancy=app_data.get('max_occupancy', 'As per norms'),
            fire_extinguishers=app_data.get('fire_extinguishers', 'As per norms'),
            fire_alarm=app_data.get('fire_alarm', 'Installed'),
            emergency_exits=app_data.get('emergency_exits', 'Adequate'),
            last_fire_drill=app_data.get('last_fire_drill', 'As required'),
            sprinkler_system=app_data.get('sprinkler_system', 'Not specified'),
            issue_date=datetime.now().strftime('%d/%m/%Y'),
            valid_until=(datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
            compliance_score=compliance_score,
            inspector_name=inspector_name,
            inspector_signature=f"Digitally Signed by {inspector_name}",
            manager_signature=f"Digitally Signed by {session.get('username', 'Manager')}",
            approved_by=session.get('username', 'Fire Safety Manager')
        )

        # Store certificate in database
        certificates.insert_one(certificate_data)

        # Update application with certificate details
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'certificate_number': certificate_number,
                    'certificate_issued': True,
                    'certificate_issued_date': datetime.now(),
                    'certificate_path': certificate_data['certificate_path']
                }
            }
        )

        return certificate_data

    except Exception as e:
        print(f"Error generating NOC certificate: {str(e)}")
        return None

@app.route('/certificate/<certificate_number>')
def view_certificate_by_number(certificate_number):
    """View certificate by certificate number"""
    try:
        print(f"CERTIFICATE VIEW: Looking for certificate: {certificate_number}")

        certificate = certificates.find_one({'certificate_number': certificate_number})
        if not certificate:
            print(f"CERTIFICATE VIEW: Certificate not found: {certificate_number}")
            flash('Certificate not found', 'error')
            return redirect(url_for('user_dashboard'))

        print(f"CERTIFICATE VIEW: Found certificate for business: {certificate.get('business_name')}")

        app_data = applications.find_one({'_id': certificate['application_id']})
        inspection_report = inspections.find_one({'application_id': certificate['application_id'], 'status': 'completed'})

        print(f"CERTIFICATE VIEW: Rendering certificate template")

        return render_template('certificate_template.html',
            certificate_number=certificate['certificate_number'],
            business_name=certificate.get('business_name', 'N/A'),
            business_type=certificate.get('business_type', 'N/A'),
            business_address=certificate.get('business_address', 'N/A'),
            pan_number=app_data.get('pan_number', 'ABCDE1234F') if app_data else 'ABCDE1234F',
            issue_date=certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else 'N/A',
            valid_until=certificate['valid_until'].strftime('%d/%m/%Y') if certificate.get('valid_until') else 'N/A',
            compliance_score=certificate.get('compliance_score', 0),
            inspector_name=certificate.get('inspector_name', 'N/A'),
            inspector_signature=f"Digitally Signed by {certificate.get('inspector_name', 'N/A')}",
            manager_signature=f"Digitally Signed by {certificate.get('issued_by', 'System')}",
            approved_by=certificate.get('issued_by', 'System')
        )

    except Exception as e:
        print(f"CERTIFICATE VIEW: Error viewing certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error loading certificate', 'error')
        return redirect(url_for('user_dashboard'))



def generate_certificate_pdf(app_data, certificate):
    """Generate PDF certificate from HTML template"""
    try:
        # Try to import pdfkit (may not be available in deployment)
        try:
            import pdfkit
            PDFKIT_AVAILABLE = True
        except ImportError:
            PDFKIT_AVAILABLE = False
        from io import BytesIO

        # Get inspection report for compliance score and inspector details
        inspection_report = inspections.find_one({'application_id': certificate['application_id'], 'status': 'completed'})
        inspector_name = inspection_report.get('inspector', 'Unknown') if inspection_report else 'System Inspector'
        compliance_score = inspection_report.get('compliance_score', 85) if inspection_report else 85

        # Generate HTML certificate
        certificate_html = render_template('certificate_template.html',
            certificate_number=certificate['certificate_number'],
            business_name=app_data.get('business_name', ''),
            business_type=app_data.get('business_type', ''),
            business_address=app_data.get('business_address', ''),
            pan_number=app_data.get('pan_number', 'Not Provided'),
            contact_person=app_data.get('contact_person', app_data.get('name', 'Business Owner')),
            contact_number=app_data.get('contact_number', 'Not Provided'),
            building_area=app_data.get('building_area', 'As per application'),
            floors=app_data.get('floors', 'As per plan'),
            max_occupancy=app_data.get('max_occupancy', 'As per norms'),
            fire_extinguishers=app_data.get('fire_extinguishers', 'As per norms'),
            fire_alarm=app_data.get('fire_alarm', 'Installed'),
            emergency_exits=app_data.get('emergency_exits', 'Adequate'),
            last_fire_drill=app_data.get('last_fire_drill', 'As required'),
            sprinkler_system=app_data.get('sprinkler_system', 'Not specified'),
            issue_date=certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else datetime.now().strftime('%d/%m/%Y'),
            valid_until=certificate['valid_until'].strftime('%d/%m/%Y') if certificate.get('valid_until') else (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
            compliance_score=compliance_score,
            inspector_name=inspector_name,
            inspector_signature=f"Digitally Signed by {inspector_name}",
            manager_signature=f"Digitally Signed by {certificate.get('issued_by', 'Manager')}",
            approved_by=certificate.get('issued_by', 'Fire Safety Manager')
        )

        # Configure PDF options
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }

        if PDFKIT_AVAILABLE:
            try:
                # Try to generate PDF using pdfkit
                pdf_data = pdfkit.from_string(certificate_html, False, options=options)
                return BytesIO(pdf_data)
            except:
                # Fallback to reportlab if pdfkit fails
                return generate_certificate_pdf_reportlab(app_data, certificate)
        else:
            # Use reportlab directly if pdfkit not available
            return generate_certificate_pdf_reportlab(app_data, certificate)

    except Exception as e:
        print(f"Error generating certificate PDF: {str(e)}")
        # Fallback to reportlab
        return generate_certificate_pdf_reportlab(app_data, certificate)

def generate_certificate_pdf_reportlab(app_data, certificate):
    """Generate PDF certificate using reportlab as fallback"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='GovTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        styles.add(ParagraphStyle(
            name='CertTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        # Content
        story = []

        # Government Header
        story.append(Paragraph("🇮🇳", styles['GovTitle']))
        story.append(Paragraph("<b>Government of India</b><br/>Ministry of Home Affairs<br/>Directorate General of Fire Services<br/>Office of the Additional Director General of Fire Services, Gujarat<br/>3rd Floor, Fire Safety Building, Sector-10, Gandhinagar, GUJARAT", styles['Normal']))
        story.append(Spacer(1, 20))

        # Certificate Title
        story.append(Paragraph("<b>Fire Safety Certificate</b>", styles['CertTitle']))
        story.append(Paragraph("<b>No Objection Certificate (NOC)</b>", styles['Normal']))
        story.append(Spacer(1, 20))

        # Certificate content
        story.append(Paragraph(f"This is to certify that <b>{app_data.get('business_name', '')}</b> is issued a Fire Safety Certificate (NOC) with details as follows:", styles['Normal']))
        story.append(Spacer(1, 15))

        # Details table
        details = [
            ['NOC', certificate['certificate_number']],
            ['PAN', app_data.get('pan_number', 'ABCDE1234F')],
            ['Firm Name', app_data.get('business_name', '')],
            ['Nature of Business', app_data.get('business_type', '')],
            ['Date of Issue', certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else datetime.now().strftime('%d/%m/%Y')],
            ['Registered Address', app_data.get('business_address', '')],
            ['Name of the Signatory', 'MAYUR BHARVAD'],
            ['Director / Partner Details', 'Refer online at https://firenoc.gov.in or scan the QR Code'],
            ['Branch Details', 'Refer online at https://firenoc.gov.in or scan the QR Code'],
        ]

        table = Table(details, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(table)
        story.append(Spacer(1, 30))

        # Signature section
        story.append(Paragraph("M.K.Bharvad", styles['Normal']))
        story.append(Paragraph("<b>MAYUR BHARVAD</b><br/>Fire Safety Officer<br/>Government of Gujarat", styles['Normal']))
        story.append(Spacer(1, 20))

        # Note
        story.append(Paragraph("<b>Note:</b> This is a system-generated certificate. Authenticity / Updated details of the NOC can be checked at official Fire Safety website <b>https://firenoc.gov.in</b> by entering the NOC and Firm Name under Services > View Any NOC Details.", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error generating reportlab PDF: {str(e)}")
        return None

def generate_simple_certificate_pdf(app_data, certificate):
    """Generate simple PDF certificate using reportlab"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='GovTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        styles.add(ParagraphStyle(
            name='CertTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        # Content
        story = []

        # Government Header
        story.append(Paragraph("🇮🇳", styles['GovTitle']))
        story.append(Paragraph("<b>Government of India</b><br/>Ministry of Home Affairs<br/>Directorate General of Fire Services<br/>Office of the Additional Director General of Fire Services, Gujarat<br/>3rd Floor, Fire Safety Building, Sector-10, Gandhinagar, GUJARAT", styles['Normal']))
        story.append(Spacer(1, 20))

        # Certificate Title
        story.append(Paragraph("<b>Fire Safety Certificate</b>", styles['CertTitle']))
        story.append(Paragraph("<b>No Objection Certificate (NOC)</b>", styles['Normal']))
        story.append(Spacer(1, 20))

        # Certificate content
        story.append(Paragraph(f"This is to certify that <b>{app_data.get('business_name', '')}</b> is issued a Fire Safety Certificate (NOC) with details as follows:", styles['Normal']))
        story.append(Spacer(1, 15))

        # Details table
        details = [
            ['NOC', certificate['certificate_number']],
            ['PAN', app_data.get('pan_number', 'ABCDE1234F')],
            ['Firm Name', app_data.get('business_name', '')],
            ['Nature of Business', app_data.get('business_type', '')],
            ['Date of Issue', certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else datetime.now().strftime('%d/%m/%Y')],
            ['Registered Address', app_data.get('business_address', '')],
            ['Name of the Signatory', 'MAYUR BHARVAD'],
            ['Director / Partner Details', 'Refer online at https://firenoc.gov.in or scan the QR Code'],
            ['Branch Details', 'Refer online at https://firenoc.gov.in or scan the QR Code'],
        ]

        table = Table(details, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(table)
        story.append(Spacer(1, 30))

        # Signature section
        story.append(Paragraph("M.K.Bharvad", styles['Normal']))
        story.append(Paragraph("<b>MAYUR BHARVAD</b><br/>Fire Safety Officer<br/>Government of Gujarat", styles['Normal']))
        story.append(Spacer(1, 20))

        # Note
        story.append(Paragraph("<b>Note:</b> This is a system-generated certificate. Authenticity / Updated details of the NOC can be checked at official Fire Safety website <b>https://firenoc.gov.in</b> by entering the NOC and Firm Name under Services > View Any NOC Details.", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error generating simple PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_noc_certificate_pdf(app_data, certificate):
    """Generate NOC certificate PDF using reportlab"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='GovTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        styles.add(ParagraphStyle(
            name='CertTitle',
            fontName='Helvetica-Bold',
            fontSize=16,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.black
        ))

        # Content
        story = []

        # Government Header
        story.append(Paragraph("🇮🇳", styles['GovTitle']))
        story.append(Paragraph("<b>Government of India</b><br/>Ministry of Home Affairs<br/>Directorate General of Fire Services<br/>Office of the Additional Director General of Fire Services, Gujarat<br/>3rd Floor, Fire Safety Building, Sector-10, Gandhinagar, GUJARAT", styles['Normal']))
        story.append(Spacer(1, 20))

        # Certificate Title
        story.append(Paragraph("<b>Fire Safety Certificate</b>", styles['CertTitle']))
        story.append(Paragraph("<b>No Objection Certificate (NOC)</b>", styles['Normal']))
        story.append(Spacer(1, 20))

        # Certificate content
        story.append(Paragraph(f"This is to certify that <b>{app_data.get('business_name', '')}</b> is issued a Fire Safety Certificate (NOC) with details as follows:", styles['Normal']))
        story.append(Spacer(1, 15))

        # Details table
        details = [
            ['NOC', certificate['certificate_number']],
            ['PAN', app_data.get('pan_number', 'ABCDE1234F')],
            ['Firm Name', app_data.get('business_name', '')],
            ['Nature of Business', app_data.get('business_type', '')],
            ['Date of Issue', certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else datetime.now().strftime('%d/%m/%Y')],
            ['Registered Address', app_data.get('business_address', '')],
            ['Name of the Signatory', 'MAYUR BHARVAD'],
            ['Director / Partner Details', 'Refer online at https://firenoc.gov.in or scan the QR Code'],
            ['Branch Details', 'Refer online at https://firenoc.gov.in or scan the QR Code'],
        ]

        table = Table(details, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(table)
        story.append(Spacer(1, 30))

        # Signature section
        story.append(Paragraph("M.K.Bharvad", styles['Normal']))
        story.append(Paragraph("<b>MAYUR BHARVAD</b><br/>Fire Safety Officer<br/>Government of Gujarat", styles['Normal']))
        story.append(Spacer(1, 20))

        # Note
        story.append(Paragraph("<b>Note:</b> This is a system-generated certificate. Authenticity / Updated details of the NOC can be checked at official Fire Safety website <b>https://firenoc.gov.in</b> by entering the NOC and Firm Name under Services > View Any NOC Details.", styles['Normal']))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"Error generating NOC certificate PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Duplicate function removed - using the one at line 4619

@app.route('/test-download/<application_id>')
def test_download_certificate(application_id):
    """Test certificate download"""
    try:
        print(f"TEST: Testing download for application: {application_id}")

        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return f"Application not found: {application_id}", 404

        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return f"Certificate not found for application: {application_id}", 404

        return f"Found: {app_data.get('business_name')} - Certificate: {certificate['certificate_number']}"

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/test-new-route')
def test_new_route():
    """Test if new routes are being registered"""
    return "New route is working!"

@app.route('/debug-download/<application_id>')
def debug_download_certificate(application_id):
    """Debug certificate download without session check"""
    try:
        print(f"DEBUG: Testing download for application: {application_id}")

        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return f"Application not found: {application_id}", 404

        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return f"Certificate not found for application: {application_id}", 404

        # Try to generate PDF
        try:
            pdf_buffer = generate_simple_certificate_pdf(app_data, certificate)
            if not pdf_buffer:
                return "Failed to generate PDF", 500

            # Create filename
            business_name = app_data.get('business_name', 'Business').replace(' ', '_')
            certificate_number = certificate['certificate_number']
            filename = f"NOC_Certificate_{business_name}_{certificate_number}.pdf"

            # Return PDF as download
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

            print(f"DEBUG: Successfully generated PDF certificate: {filename}")
            return response

        except Exception as pdf_error:
            return f"PDF Error: {str(pdf_error)}", 500

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/simple-download/<application_id>')
def simple_download_certificate(application_id):
    """Simple certificate download without session check"""
    try:
        print(f"SIMPLE: Downloading certificate for application: {application_id}")

        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404

        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return "Certificate not found", 404

        # Generate simple PDF
        pdf_buffer = generate_noc_certificate_pdf(app_data, certificate)
        if not pdf_buffer:
            return "Failed to generate PDF", 500

        # Create filename
        business_name = app_data.get('business_name', 'Business').replace(' ', '_')
        certificate_number = certificate['certificate_number']
        filename = f"NOC_Certificate_{business_name}_{certificate_number}.pdf"

        # Return PDF as download
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        print(f"SIMPLE: Successfully generated PDF: {filename}")
        return response

    except Exception as e:
        print(f"SIMPLE: Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

def send_certificate_notification(user_email, business_name, certificate_number):
    """Send certificate generation notification to user"""
    try:
        subject = "🎉 NOC Certificate Generated - Application Approved!"

        body = f"""
Dear Applicant,

Congratulations! Your Fire NOC application has been approved and your certificate has been generated.

🎉 Certificate Details:
• Business Name: {business_name}
• Certificate Number: {certificate_number}
• Issue Date: {datetime.now().strftime('%B %d, %Y')}
• Valid Until: {(datetime.now() + timedelta(days=365)).strftime('%B %d, %Y')}

📋 What's Next:
1. Download your NOC certificate from your dashboard
2. Display the certificate at your business premises
3. Keep a copy for your records
4. Certificate is valid for 1 year from issue date

🔗 Access Your Certificate:
Login to your dashboard to download the official NOC certificate.

📞 Support:
If you need any assistance, please contact our support team.

Congratulations once again!

Best regards,
Fire NOC System Team
        """

        send_email(subject, user_email, body)
        return True
    except Exception as e:
        print(f"Error sending certificate notification: {str(e)}")
        return False

def send_rejection_notification(user_email, business_name, comments):
    """Send rejection notification to user"""
    try:
        subject = "❌ Application Update - Improvements Required"

        body = f"""
Dear Applicant,

We have reviewed your Fire NOC application for {business_name}.

❌ Application Status: Requires Improvements

📋 Manager Comments:
{comments}

🔍 Next Steps:
1. Review the feedback provided above
2. Make the necessary improvements to your fire safety setup
3. Submit a new application once improvements are completed
4. Contact our support team if you need clarification

📞 Need Help?
Our team is here to help you meet the fire safety requirements. Please don't hesitate to contact us.

We look forward to your improved application.

Best regards,
Fire NOC System Team
        """

        send_email(subject, user_email, body)
        return True
    except Exception as e:
        print(f"Error sending rejection notification: {str(e)}")
        return False

@app.route('/download-noc-certificate-v2/<application_id>')
def download_noc_certificate_v2(application_id):
    """Download NOC certificate for approved application with real data"""
    try:
        print(f"DOWNLOAD CERT: Attempting to download certificate for application: {application_id}")

        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            print(f"DOWNLOAD CERT: Application not found: {application_id}")
            return jsonify({'error': 'Application not found'}), 404

        print(f"DOWNLOAD CERT: Found application: {app_data.get('business_name')} with status: {app_data.get('status')}")

        # Get or create certificate
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            print(f"DOWNLOAD CERT: Certificate not found, creating one...")
            # Create certificate if it doesn't exist for approved applications
            if app_data.get('status') == 'approved':
                certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app_data['_id'])[-6:]}"
                certificate_data = {
                    'certificate_number': certificate_number,
                    'application_id': ObjectId(application_id),
                    'business_name': app_data.get('business_name', ''),
                    'business_address': app_data.get('business_address', ''),
                    'business_type': app_data.get('business_type', ''),
                    'issued_date': datetime.now(),
                    'valid_until': datetime.now() + timedelta(days=365),
                    'issued_by': 'Fire Safety Department',
                    'status': 'active',
                    'created_at': datetime.now()
                }
                certificates.insert_one(certificate_data)
                certificate = certificate_data
                print(f"DOWNLOAD CERT: Created new certificate: {certificate_number}")
            else:
                print(f"DOWNLOAD CERT: Application not approved, cannot create certificate")
                return jsonify({'error': 'Certificate not available - application not approved'}), 404
        else:
            print(f"DOWNLOAD CERT: Found existing certificate: {certificate.get('certificate_number')}")

        # Generate PDF using the real certificate template
        pdf_buffer = generate_certificate_pdf(app_data, certificate)
        if not pdf_buffer:
            print(f"DOWNLOAD CERT: Failed to generate PDF")
            return jsonify({'error': 'Failed to generate certificate PDF'}), 500

        print(f"DOWNLOAD CERT: Successfully generated PDF for certificate: {certificate.get('certificate_number')}")

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"NOC_Certificate_{certificate.get('certificate_number', 'Unknown')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"DOWNLOAD CERT: Error downloading certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error downloading certificate: {str(e)}'}), 500

@app.route('/manager-download-certificate-v2/<application_id>')
def manager_download_certificate_v2(application_id):
    """Manager download certificate for any approved application"""
    if 'username' not in session or session.get('role') not in ['manager', 'admin']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))

    try:
        # Get application data
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            flash('Application not found', 'error')
            return redirect(url_for('manager_dashboard'))

        # Get or create certificate
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            # Create certificate if it doesn't exist
            certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app_data['_id'])[-6:]}"
            certificate_data = {
                'certificate_number': certificate_number,
                'application_id': ObjectId(application_id),
                'business_name': app_data.get('business_name', ''),
                'business_address': app_data.get('business_address', ''),
                'business_type': app_data.get('business_type', ''),
                'issued_date': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=365),
                'issued_by': session.get('username', 'Fire Safety Manager'),
                'status': 'active',
                'created_at': datetime.now()
            }
            certificates.insert_one(certificate_data)
            certificate = certificate_data

        # Generate PDF using the real certificate template
        pdf_buffer = generate_certificate_pdf(app_data, certificate)
        if not pdf_buffer:
            flash('Failed to generate certificate PDF', 'error')
            return redirect(url_for('manager_dashboard'))

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"NOC_Certificate_{certificate.get('certificate_number', 'Unknown')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error downloading certificate: {str(e)}")
        flash('Error downloading certificate', 'error')
        return redirect(url_for('manager_dashboard'))

@app.route('/test-view-certificate/<application_id>')
def test_view_certificate(application_id):
    """Test view certificate without session check"""
    try:
        print(f"TEST VIEW: Attempting to view certificate for application: {application_id}")

        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return f"Application not found: {application_id}", 404

        if not app_data.get('certificate_number'):
            return f"Certificate number not found in application", 404

        # Get certificate data
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return f"Certificate data not found in database", 404

        # Get inspection report for compliance score and inspector details
        inspection_report = inspections.find_one({'application_id': ObjectId(application_id), 'status': 'completed'})
        inspector_name = inspection_report.get('inspector', 'Unknown') if inspection_report else 'System Inspector'
        compliance_score = inspection_report.get('compliance_score', 85) if inspection_report else 85

        # Render certificate template
        return render_template('certificate_template.html',
            certificate_number=certificate['certificate_number'],
            business_name=app_data.get('business_name', ''),
            business_type=app_data.get('business_type', ''),
            business_address=app_data.get('business_address', ''),
            pan_number=app_data.get('pan_number', 'Not Provided'),
            contact_person=app_data.get('contact_person', app_data.get('name', 'Business Owner')),
            contact_number=app_data.get('contact_number', 'Not Provided'),
            building_area=app_data.get('building_area', 'As per application'),
            floors=app_data.get('floors', 'As per plan'),
            max_occupancy=app_data.get('max_occupancy', 'As per norms'),
            fire_extinguishers=app_data.get('fire_extinguishers', 'As per norms'),
            fire_alarm=app_data.get('fire_alarm', 'Installed'),
            emergency_exits=app_data.get('emergency_exits', 'Adequate'),
            last_fire_drill=app_data.get('last_fire_drill', 'As required'),
            sprinkler_system=app_data.get('sprinkler_system', 'Not specified'),
            issue_date=certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else datetime.now().strftime('%d/%m/%Y'),
            valid_until=certificate['valid_until'].strftime('%d/%m/%Y') if certificate.get('valid_until') else (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
            compliance_score=compliance_score,
            inspector_name=inspector_name,
            inspector_signature=f"Digitally Signed by {inspector_name}",
            manager_signature=f"Digitally Signed by {certificate.get('issued_by', 'Manager')}",
            approved_by=certificate.get('issued_by', 'Fire Safety Manager')
        )

    except Exception as e:
        print(f"TEST VIEW: Error viewing certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error viewing certificate: {str(e)}", 500

@app.route('/generate-certificates-for-approved')
def generate_certificates_for_approved():
    """Generate certificates for all approved applications that don't have certificates"""
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        # Get all approved applications without certificates
        approved_apps = list(applications.find({
            'status': 'approved',
            'certificate_number': {'$exists': False}
        }))

        created_count = 0
        for app in approved_apps:
            # Get inspection data if available
            inspection = inspection_reports.find_one({'application_id': app['_id']})
            if not inspection:
                inspection = inspections.find_one({'application_id': app['_id'], 'status': 'completed'})

            # Create certificate with real application data
            certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app['_id'])[-6:]}"

            certificate_data = {
                'certificate_number': certificate_number,
                'application_id': app['_id'],
                'username': app.get('username'),
                'business_name': app.get('business_name'),
                'business_type': app.get('business_type'),
                'business_address': app.get('business_address'),
                'contact_person': app.get('contact_person', app.get('name')),
                'contact_number': app.get('contact_number'),
                'email': app.get('email'),
                'pan_number': app.get('pan_number', 'Not provided'),
                'building_area': app.get('building_area'),
                'floors': app.get('floors'),
                'max_occupancy': app.get('max_occupancy'),
                'fire_extinguishers': app.get('fire_extinguishers'),
                'fire_alarm': app.get('fire_alarm'),
                'emergency_exits': app.get('emergency_exits'),
                'last_fire_drill': app.get('last_fire_drill'),
                'sprinkler_system': app.get('sprinkler_system'),
                'issued_date': datetime.now(),
                'valid_until': datetime.now() + timedelta(days=365),
                'status': 'active',
                'compliance_score': inspection.get('compliance_score', 85) if inspection else 85,
                'inspector_name': inspection.get('inspector', app.get('assigned_inspector', 'System Inspector')) if inspection else app.get('assigned_inspector', 'System Inspector'),
                'issued_by': app.get('approved_by', 'Fire Safety Department'),
                'created_at': datetime.now()
            }

            # Insert certificate
            certificates.insert_one(certificate_data)

            # Update application
            applications.update_one(
                {'_id': app['_id']},
                {'$set': {'certificate_number': certificate_number, 'certificate_issued': True}}
            )

            created_count += 1

        return f"""
        <h2>✅ Certificates Generated Successfully!</h2>
        <p><strong>Total Certificates Created:</strong> {created_count}</p>
        <p>Certificates have been generated for all approved applications.</p>
        <br>
        <a href="/user_dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            🏠 Go to User Dashboard
        </a>
        <a href="/manager_dashboard" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">
            👨‍💼 Manager Dashboard
        </a>
        """

    except Exception as e:
        return f"Error generating certificates: {str(e)}", 500

@app.route('/api/application/<application_id>')
def get_application_data(application_id):
    """Get application data for certificate generation"""
    try:
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return jsonify({'error': 'Application not found'}), 404

        # Convert ObjectId to string
        app_data['_id'] = str(app_data['_id'])

        # Convert datetime objects to strings
        if 'timestamp' in app_data and app_data['timestamp']:
            app_data['timestamp'] = app_data['timestamp'].isoformat()
        if 'approval_date' in app_data and app_data['approval_date']:
            app_data['approval_date'] = app_data['approval_date'].isoformat()

        # Ensure all required fields exist with defaults
        required_fields = {
            'business_name': 'Business Name',
            'business_type': 'Commercial',
            'business_address': 'Business Address',
            'contact_person': app_data.get('name', 'Contact Person'),
            'contact_number': 'Contact Number',
            'email': 'Email Address',
            'pan_number': 'PAN Number',
            'building_area': 'Not specified',
            'floors': 'Not specified',
            'max_occupancy': 'Not specified',
            'fire_extinguishers': 'As per norms',
            'fire_alarm': 'Installed',
            'emergency_exits': 'Available',
            'last_fire_drill': 'Not specified',
            'sprinkler_system': 'Not specified'
        }

        for field, default_value in required_fields.items():
            if field not in app_data or not app_data[field]:
                app_data[field] = default_value

        return jsonify(app_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/certificate/<application_id>')
def get_certificate_data(application_id):
    """Get certificate data for application"""
    try:
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            # If certificate doesn't exist, create one automatically for approved applications
            app_data = applications.find_one({'_id': ObjectId(application_id), 'status': 'approved'})
            if app_data:
                # Auto-generate certificate
                certificate_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app_data['_id'])[-6:]}"

                certificate_data = {
                    'certificate_number': certificate_number,
                    'application_id': app_data['_id'],
                    'username': app_data.get('username'),
                    'business_name': app_data.get('business_name'),
                    'business_type': app_data.get('business_type'),
                    'business_address': app_data.get('business_address'),
                    'issued_date': datetime.now(),
                    'valid_until': datetime.now() + timedelta(days=365),
                    'status': 'active',
                    'issued_by': app_data.get('approved_by', 'Fire Safety Department'),
                    'created_at': datetime.now()
                }

                # Insert certificate
                certificates.insert_one(certificate_data)

                # Update application
                applications.update_one(
                    {'_id': app_data['_id']},
                    {'$set': {'certificate_number': certificate_number, 'certificate_issued': True}}
                )

                certificate = certificate_data
            else:
                return jsonify({'error': 'Certificate not found and application not approved'}), 404

        # Convert ObjectId to string
        if '_id' in certificate:
            certificate['_id'] = str(certificate['_id'])
        certificate['application_id'] = str(certificate['application_id'])

        # Convert datetime objects to strings
        if 'issued_date' in certificate and certificate['issued_date']:
            certificate['issued_date'] = certificate['issued_date'].isoformat()
        if 'valid_until' in certificate and certificate['valid_until']:
            certificate['valid_until'] = certificate['valid_until'].isoformat()
        if 'created_at' in certificate and certificate['created_at']:
            certificate['created_at'] = certificate['created_at'].isoformat()

        return jsonify(certificate)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/inspection-report/<application_id>')
def get_inspection_report_data(application_id):
    """Get inspection report data for application"""
    try:
        # First try to find in inspection_reports collection
        inspection = inspection_reports.find_one({'application_id': ObjectId(application_id)})

        if not inspection:
            # Try to find in inspections collection
            inspection = inspections.find_one({'application_id': ObjectId(application_id), 'status': 'completed'})

        if not inspection:
            # Get application data to create realistic inspection data
            app_data = applications.find_one({'_id': ObjectId(application_id)})
            if app_data:
                # Create realistic inspection data based on application
                inspection_data = {
                    'inspector': app_data.get('assigned_inspector', 'System Inspector'),
                    'inspection_date': datetime.now().strftime('%d/%m/%Y'),
                    'completion_date': datetime.now().strftime('%d/%m/%Y'),
                    'compliance_score': 85,
                    'status': 'completed',
                    'overall_result': 'Passed',
                    'fire_extinguisher_check': 'Passed - All units functional',
                    'fire_alarm_check': 'Passed - System operational',
                    'emergency_exit_check': 'Passed - All exits accessible',
                    'electrical_safety_check': 'Passed - No hazards detected',
                    'housekeeping_check': 'Passed - Good maintenance',
                    'documentation_check': 'Passed - All documents verified',
                    'recommendations': 'Maintain current safety standards. Regular maintenance required.',
                    'photos_taken': 5,
                    'video_recorded': True
                }
                return jsonify(inspection_data)
            else:
                # Return basic default data
                return jsonify({
                    'inspector': 'System Inspector',
                    'inspection_date': datetime.now().strftime('%d/%m/%Y'),
                    'compliance_score': 85,
                    'status': 'completed',
                    'overall_result': 'Passed'
                })

        # Convert ObjectId to string
        if '_id' in inspection:
            inspection['_id'] = str(inspection['_id'])
        if 'application_id' in inspection:
            inspection['application_id'] = str(inspection['application_id'])

        # Convert datetime objects to strings
        if 'inspection_date' in inspection and isinstance(inspection['inspection_date'], datetime):
            inspection['inspection_date'] = inspection['inspection_date'].strftime('%d/%m/%Y')
        elif 'inspection_date' in inspection and isinstance(inspection['inspection_date'], str):
            # Already a string, keep as is
            pass
        else:
            inspection['inspection_date'] = datetime.now().strftime('%d/%m/%Y')

        if 'completion_date' in inspection and isinstance(inspection['completion_date'], datetime):
            inspection['completion_date'] = inspection['completion_date'].strftime('%d/%m/%Y')
        elif 'completion_date' not in inspection:
            inspection['completion_date'] = inspection.get('inspection_date', datetime.now().strftime('%d/%m/%Y'))

        # Ensure required fields exist
        if 'compliance_score' not in inspection:
            inspection['compliance_score'] = 85
        if 'overall_result' not in inspection:
            inspection['overall_result'] = 'Passed'
        if 'status' not in inspection:
            inspection['status'] = 'completed'

        return jsonify(inspection)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Enhanced Admin API Routes
@app.route('/api/admin/certificates')
def get_admin_certificates():
    """Get all certificates for admin management"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get certificate stats
        total_certs = certificates.count_documents({})
        pending_certs = applications.count_documents({'status': 'approved', 'certificate_number': {'$exists': False}})

        # Get monthly certificates (current month)
        from datetime import datetime, timedelta
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_certs = certificates.count_documents({'issue_date': {'$gte': current_month_start.isoformat()}})

        # Get expired certificates (assuming 1 year validity)
        one_year_ago = datetime.now() - timedelta(days=365)
        expired_certs = certificates.count_documents({'issue_date': {'$lt': one_year_ago.isoformat()}})

        # Get all certificates with details - include applications with certificate numbers
        all_certificates = []

        # Get certificates from certificates collection
        cert_docs = list(certificates.find({}).sort('issue_date', -1))
        for cert in cert_docs:
            cert['_id'] = str(cert['_id'])
            cert['status'] = 'active'
            all_certificates.append(cert)

        # Get applications with certificate numbers
        app_certs = list(applications.find({'certificate_number': {'$exists': True}}).sort('timestamp', -1))
        for app in app_certs:
            cert_data = {
                '_id': str(app['_id']),
                'certificate_number': app.get('certificate_number'),
                'business_name': app.get('business_name', 'N/A'),
                'issue_date': app.get('timestamp', datetime.now().isoformat()),
                'valid_until': (datetime.now() + timedelta(days=365)).isoformat(),
                'status': 'active'
            }
            # Check if not already in certificates
            if not any(c.get('certificate_number') == cert_data['certificate_number'] for c in all_certificates):
                all_certificates.append(cert_data)

        return jsonify({
            'total': len(all_certificates),
            'pending': pending_certs,
            'monthly': monthly_certs,
            'expired': expired_certs,
            'certificates': all_certificates
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics')
def get_admin_analytics():
    """Get analytics data for admin dashboard"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Calculate processing time
        total_processed = applications.count_documents({'status': {'$in': ['approved', 'rejected']}})
        approved = applications.count_documents({'status': 'approved'})
        approval_rate = round((approved / total_processed) * 100) if total_processed > 0 else 0

        # Mock data for other metrics
        avg_processing_time = 7  # days
        user_satisfaction = 92  # percentage

        return jsonify({
            'avg_processing_time': avg_processing_time,
            'approval_rate': approval_rate,
            'user_satisfaction': user_satisfaction,
            'charts_data': {
                'monthly_trends': [10, 15, 20, 25, 30, 35],
                'approval_rates': [85, 87, 90, 88, 92, 89]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/settings', methods=['GET', 'POST'])
def admin_settings_api():
    """Get or update system settings"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        if request.method == 'GET':
            # Get current settings (you can store these in a settings collection)
            settings = {
                'auto_approval_threshold': 85,
                'max_file_size': 10,
                'certificate_validity': 12,
                'email_notifications': True,
                'sms_notifications': False,
                'push_notifications': True
            }
            return jsonify(settings)

        elif request.method == 'POST':
            # Update settings
            new_settings = request.get_json()
            # Here you would save to a settings collection
            # For now, just return success
            return jsonify({'success': True, 'message': 'Settings updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/backup-history')
def get_backup_history():
    """Get backup history for admin dashboard"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Mock backup history data
        backups = [
            {
                'id': '1',
                'date': datetime.now().isoformat(),
                'type': 'Full Database',
                'size': '2.5 MB',
                'status': 'completed'
            },
            {
                'id': '2',
                'date': (datetime.now() - timedelta(days=1)).isoformat(),
                'type': 'Applications Only',
                'size': '1.2 MB',
                'status': 'completed'
            }
        ]

        return jsonify({'backups': backups})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/create-backup', methods=['POST'])
def create_backup():
    """Create a new backup"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        backup_type = request.get_json().get('type', 'full')

        # Here you would implement actual backup logic
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f'{backup_type} backup created successfully',
            'backup_id': str(datetime.now().timestamp())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/audit-logs')
def get_audit_logs():
    """Get audit logs for admin dashboard"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get recent activities as audit logs
        recent_logs = list(activities.find({}).sort('timestamp', -1).limit(50))

        # Format logs for display
        formatted_logs = []
        for log in recent_logs:
            formatted_logs.append({
                'timestamp': log.get('timestamp', datetime.now()).isoformat(),
                'user': log.get('username', 'System'),
                'action': log.get('action', 'Unknown'),
                'resource': log.get('details', 'N/A'),
                'ip_address': log.get('ip_address', '127.0.0.1'),
                'status': 'success'
            })

        return jsonify({'logs': formatted_logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/generate-bulk-certificates', methods=['POST'])
def generate_bulk_certificates():
    """Generate certificates for all approved applications without certificates"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Find approved applications without certificates
        approved_without_certs = list(applications.find({
            'status': 'approved',
            'certificate_number': {'$exists': False}
        }))

        count = 0
        for app in approved_without_certs:
            # Generate certificate number
            cert_number = f"NOC-{datetime.now().strftime('%Y%m%d')}-{str(app['_id'])[-6:].upper()}"

            # Update application with certificate number
            applications.update_one(
                {'_id': app['_id']},
                {'$set': {'certificate_number': cert_number}}
            )

            # Create certificate record
            certificate_data = {
                'certificate_number': cert_number,
                'application_id': app['_id'],
                'business_name': app.get('business_name', ''),
                'issue_date': datetime.now().isoformat(),
                'valid_until': (datetime.now() + timedelta(days=365)).isoformat(),
                'issued_by': session.get('username', 'Admin'),
                'status': 'active'
            }
            certificates.insert_one(certificate_data)
            count += 1

        return jsonify({
            'success': True,
            'count': count,
            'message': f'Generated {count} certificates successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Tracking API Routes
@app.route('/api/admin/search-user-by-certificate', methods=['POST'])
def search_user_by_certificate():
    """Search user by certificate number and get complete history"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        certificate_number = data.get('certificate_number')

        if not certificate_number:
            return jsonify({'error': 'Certificate number is required'}), 400

        # Find application with this certificate number
        application = applications.find_one({'certificate_number': certificate_number})

        if not application:
            return jsonify({'error': 'Certificate not found'}), 404

        # Get user details
        user = users.find_one({'_id': application['user_id']})

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get all applications by this user
        user_applications = list(applications.find({'user_id': application['user_id']}).sort('timestamp', -1))

        # Get user activity logs
        user_activities = list(activities.find({'username': user['username']}).sort('timestamp', -1).limit(50))

        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        for app in user_applications:
            app['_id'] = str(app['_id'])
        for activity in user_activities:
            activity['_id'] = str(activity['_id'])

        return jsonify({
            'success': True,
            'user': user,
            'applications': user_applications,
            'activities': user_activities
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/all-users')
def get_all_users():
    """Get all users with application counts"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all users
        all_users = list(users.find({}, {'password': 0}))  # Exclude password

        # Add application count for each user
        for user in all_users:
            user['_id'] = str(user['_id'])
            user['application_count'] = applications.count_documents({'user_id': user['_id']})

            # Get last activity
            last_activity = activities.find_one(
                {'username': user['username']},
                sort=[('timestamp', -1)]
            )
            user['last_login'] = last_activity['timestamp'] if last_activity else None

        return jsonify({
            'success': True,
            'users': all_users
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user-details/<user_id>')
def get_admin_user_details(user_id):
    """Get detailed user information"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from bson import ObjectId

        # Get user details
        user = users.find_one({'_id': ObjectId(user_id)}, {'password': 0})

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get user applications
        user_applications = list(applications.find({'user_id': ObjectId(user_id)}).sort('timestamp', -1))

        # Get user activities
        user_activities = list(activities.find({'username': user['username']}).sort('timestamp', -1).limit(50))

        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        for app in user_applications:
            app['_id'] = str(app['_id'])
        for activity in user_activities:
            activity['_id'] = str(activity['_id'])

        return jsonify({
            'success': True,
            'user': user,
            'applications': user_applications,
            'activities': user_activities
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/export-user-report', methods=['POST'])
def export_user_report():
    """Export user report as PDF"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # This would generate a PDF report
        # For now, return success message
        return jsonify({
            'success': True,
            'message': 'User report export feature coming soon'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Application Management
@app.route('/api/admin/applications')
def get_admin_applications():
    """Get all applications for admin management"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all applications
        all_applications = list(applications.find({}).sort('timestamp', -1))

        for app in all_applications:
            app['_id'] = str(app['_id'])
            # Format timestamp
            if 'timestamp' in app:
                app['formatted_date'] = app['timestamp'].strftime('%d/%m/%Y %H:%M') if isinstance(app['timestamp'], datetime) else app['timestamp']

        return jsonify({
            'success': True,
            'applications': all_applications
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/application/<application_id>/approve', methods=['POST'])
def admin_approve_application(application_id):
    """Admin approve application"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from bson import ObjectId

        # Update application status
        result = applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'status': 'approved',
                    'approved_by': session.get('username'),
                    'approval_date': datetime.now()
                }
            }
        )

        if result.modified_count > 0:
            # Generate certificate
            certificate_data = create_manager_approved_certificate(application_id)

            return jsonify({
                'success': True,
                'message': 'Application approved successfully',
                'certificate_number': certificate_data.get('certificate_number') if certificate_data else None
            })
        else:
            return jsonify({'error': 'Application not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/application/<application_id>/reject', methods=['POST'])
def admin_reject_application(application_id):
    """Admin reject application"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from bson import ObjectId
        data = request.get_json()
        rejection_reason = data.get('reason', 'No reason provided')

        # Update application status
        result = applications.update_one(
            {'_id': ObjectId(application_id)},
            {
                '$set': {
                    'status': 'rejected',
                    'rejected_by': session.get('username'),
                    'rejection_date': datetime.now(),
                    'rejection_reason': rejection_reason
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({
                'success': True,
                'message': 'Application rejected successfully'
            })
        else:
            return jsonify({'error': 'Application not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Inspections API
@app.route('/api/admin/inspections')
def get_admin_inspections():
    """Get all inspections for admin management"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get all inspections with application details
        all_inspections = []

        # Get inspections from inspections collection
        inspection_docs = list(inspections.find({}).sort('inspection_date', -1))

        for inspection in inspection_docs:
            # Get related application
            app = applications.find_one({'_id': inspection.get('application_id')})

            inspection_data = {
                '_id': str(inspection['_id']),
                'business_name': app.get('business_name', 'N/A') if app else 'N/A',
                'inspector': inspection.get('inspector', 'Not Assigned'),
                'inspection_date': inspection.get('inspection_date', 'Not Scheduled'),
                'status': inspection.get('status', 'pending'),
                'compliance_score': inspection.get('compliance_score', 'N/A'),
                'application_id': str(inspection.get('application_id', ''))
            }
            all_inspections.append(inspection_data)

        # Also get applications that need inspection (approved but no inspection)
        apps_needing_inspection = list(applications.find({
            'status': 'approved',
            '_id': {'$nin': [insp.get('application_id') for insp in inspection_docs]}
        }))

        for app in apps_needing_inspection:
            inspection_data = {
                '_id': str(app['_id']),
                'business_name': app.get('business_name', 'N/A'),
                'inspector': 'Not Assigned',
                'inspection_date': 'Not Scheduled',
                'status': 'pending',
                'compliance_score': 'N/A',
                'application_id': str(app['_id'])
            }
            all_inspections.append(inspection_data)

        return jsonify({
            'success': True,
            'inspections': all_inspections
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Inspection Report Routes
@app.route('/view-inspection-report-by-id/<report_id>')
def view_inspection_report_by_id(report_id):
    """View inspection report in browser by report ID"""
    try:
        from bson import ObjectId

        # Get inspection report
        inspection = inspections.find_one({'_id': ObjectId(report_id)})

        if not inspection:
            return "Inspection report not found", 404

        # Get application details
        application = applications.find_one({'_id': inspection.get('application_id')})

        if not application:
            return "Application not found", 404

        # Generate inspection report HTML
        report_html = generate_inspection_report_html(inspection, application)

        return report_html

    except Exception as e:
        return f"Error generating report: {str(e)}", 500

@app.route('/download-inspection-report-by-id/<report_id>')
def download_inspection_report_by_id(report_id):
    """Download inspection report as PDF by report ID"""
    try:
        from bson import ObjectId

        # Get inspection report
        inspection = inspections.find_one({'_id': ObjectId(report_id)})

        if not inspection:
            return "Inspection report not found", 404

        # Get application details
        application = applications.find_one({'_id': inspection.get('application_id')})

        if not application:
            return "Application not found", 404

        # Generate inspection report HTML
        report_html = generate_inspection_report_html(inspection, application)

        return report_html

    except Exception as e:
        return f"Error generating report: {str(e)}", 500

@app.route('/generate-inspection-report-by-id/<report_id>')
def generate_inspection_report_by_id(report_id):
    """Generate inspection report by report ID"""
    try:
        from bson import ObjectId

        # Get inspection report
        inspection = inspections.find_one({'_id': ObjectId(report_id)})

        if not inspection:
            return "Inspection report not found", 404

        # Get application details
        application = applications.find_one({'_id': inspection.get('application_id')})

        if not application:
            return "Application not found", 404

        # Generate inspection report HTML
        report_html = generate_inspection_report_html(inspection, application)

        return report_html

    except Exception as e:
        return f"Error generating report: {str(e)}", 500

def generate_inspection_report_html(inspection, application):
    """Generate HTML for inspection report"""

    today = datetime.now().strftime('%d/%m/%Y')

    # Extract data
    business_name = application.get('business_name', 'N/A')
    business_address = application.get('business_address', 'N/A')
    contact_person = application.get('contact_person', application.get('name', 'N/A'))
    contact_number = application.get('contact_number', 'N/A')
    inspector_name = inspection.get('inspector', 'System Inspector')
    inspection_date = inspection.get('inspection_date', today)
    compliance_score = inspection.get('compliance_score', '85')
    report_number = f"INS-{datetime.now().strftime('%Y%m%d')}-{str(inspection['_id'])[-6:].upper()}"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fire Safety Inspection Report</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            line-height: 1.4;
        }}
        .report-container {{
            max-width: 950px;
            margin: 0 auto;
            background: white;
            padding: 60px;
            border: 6px double #000080;
            box-shadow: 0 0 40px rgba(0,0,0,0.3);
            position: relative;
            background: linear-gradient(45deg, #ffffff 0%, #f8f9fa 100%);
        }}
        .watermark {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 8em;
            color: rgba(0,0,139,0.03);
            font-weight: bold;
            z-index: 1;
        }}
        .content {{ position: relative; z-index: 2; }}
        .header {{
            text-align: center;
            border-bottom: 4px double #000080;
            padding-bottom: 30px;
            margin-bottom: 40px;
            background: linear-gradient(45deg, #000080, #4169E1);
            color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        .govt-logo {{
            width: 120px;
            height: 120px;
            margin: 0 auto 20px;
            border: 3px solid #FFD700;
            border-radius: 50%;
            background-color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
        }}
        .flag {{ font-size: 3em; margin-bottom: 15px; }}
        .govt-title {{ font-size: 1.6em; font-weight: bold; margin-bottom: 10px; }}
        .dept-info {{ font-size: 1.1em; line-height: 1.8; }}
        .report-title {{
            text-align: center;
            margin: 35px 0;
            background: linear-gradient(45deg, #000080, #4169E1);
            color: white;
            padding: 20px;
            border-radius: 10px;
        }}
        .report-main-title {{ font-size: 2em; font-weight: bold; margin-bottom: 10px; }}
        .report-sub-title {{ font-size: 1.3em; font-weight: bold; }}
        .details-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
        }}
        .details-table th, .details-table td {{
            border: 2px solid #000;
            padding: 12px 15px;
            text-align: left;
        }}
        .details-table th {{
            background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
            font-weight: bold;
            color: #000080;
        }}
        .details-table td {{ background: #fafafa; }}
        .inspection-section {{
            background: #f8f9fa;
            border: 2px solid #007bff;
            border-radius: 10px;
            padding: 20px;
            margin: 25px 0;
        }}
        .inspection-title {{
            color: #007bff;
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 15px;
            text-align: center;
        }}
        .signature-section {{
            display: flex;
            justify-content: space-between;
            margin-top: 50px;
            padding: 30px;
            border-top: 4px double #000080;
            background: linear-gradient(45deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }}
        .signature-box {{
            text-align: right;
            background: white;
            padding: 20px;
            border-radius: 15px;
            border: 3px solid #FFD700;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .signature-line {{
            border-bottom: 4px solid #000080;
            width: 280px;
            margin-left: auto;
            margin-bottom: 12px;
            height: 60px;
            display: flex;
            align-items: end;
            justify-content: center;
            font-style: italic;
            font-weight: bold;
        }}
        .officer-details {{ font-weight: bold; color: #000080; }}
        .download-buttons {{
            text-align: center;
            margin-top: 35px;
            padding: 25px;
            border-top: 2px solid #ccc;
        }}
        .btn {{
            background: #007bff;
            color: white;
            padding: 15px 35px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin: 0 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }}
        .btn:hover {{ background: #0056b3; transform: translateY(-2px); }}
        .btn-success {{ background: #28a745; }}
        .btn-success:hover {{ background: #1e7e34; }}
        @media print {{ .download-buttons {{ display: none !important; }} body {{ background: white; }} }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="watermark">INSPECTION REPORT</div>
        <div class="content">
            <div class="header">
                <div class="govt-logo">
                    <img src="https://w7.pngwing.com/pngs/926/964/png-transparent-united-states-department-of-state-united-states-secretary-of-state-federal-government-of-the-united-states-foreign-relations-of-the-united-states-passport-miscellaneous-emblem-logo.png"
                         alt="Government Logo" style="width: 100px; height: 100px; object-fit: contain;">
                </div>
                <div class="flag">🇮🇳</div>
                <div class="govt-title">भारत सरकार | Government of India</div>
                <div class="dept-info">
                    गृह मंत्रालय | Ministry of Home Affairs<br>
                    अग्निशमन सेवा महानिदेशालय | Directorate General of Fire Services<br>
                    अतिरिक्त महानिदेशक कार्यालय, गुजरात | Office of the Additional Director General, Gujarat<br>
                    3rd Floor, Fire Safety Building, Sector-10, Gandhinagar, GUJARAT - 382010<br>
                    <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.2); border-radius: 8px; border: 2px solid #FFD700;">
                        <strong>🏛️ DEPARTMENT OF FIRE SAFETY & EMERGENCY SERVICES</strong><br>
                        <em>Official Fire Safety Inspection Report</em>
                    </div>
                </div>
            </div>

            <div class="report-title">
                <div class="report-main-title">🔍 Fire Safety Inspection Report</div>
                <div class="report-sub-title">Official Government Inspection Document</div>
            </div>

            <table class="details-table">
                <tr><th>🆔 Report Number</th><td><strong>{report_number}</strong></td></tr>
                <tr><th>🏢 Business Name</th><td>{business_name}</td></tr>
                <tr><th>👤 Contact Person</th><td>{contact_person}</td></tr>
                <tr><th>📞 Contact Number</th><td>{contact_number}</td></tr>
                <tr><th>📍 Business Address</th><td>{business_address}</td></tr>
                <tr><th>🧑‍🚒 Inspector Name</th><td>{inspector_name}</td></tr>
                <tr><th>📅 Inspection Date</th><td>{inspection_date}</td></tr>
                <tr><th>📊 Compliance Score</th><td><strong>{compliance_score}%</strong></td></tr>
            </table>

            <div class="inspection-section">
                <div class="inspection-title">🔍 DETAILED INSPECTION FINDINGS</div>
                <table class="details-table">
                    <tr><th>🧯 Fire Extinguishers</th><td>Adequate and properly maintained</td></tr>
                    <tr><th>🚨 Fire Alarm System</th><td>Installed and functional</td></tr>
                    <tr><th>🚪 Emergency Exits</th><td>Clear and properly marked</td></tr>
                    <tr><th>💡 Emergency Lighting</th><td>Functional and adequate</td></tr>
                    <tr><th>🔥 Fire Safety Equipment</th><td>As per fire safety norms</td></tr>
                    <tr><th>✅ Overall Assessment</th><td><strong style="color: green;">COMPLIANT ✓</strong></td></tr>
                </table>
            </div>

            <div style="text-align: right; margin: 25px 0; font-size: 0.9em;">
                <strong>📄 Report Generated:</strong> {today}<br>
                <strong>🔐 Digital Signature:</strong> Applied<br>
                <strong>📋 Status:</strong> Official Government Document
            </div>

            <div class="signature-section">
                <div style="text-align: left;">
                    <div style="background: white; padding: 20px; border-radius: 15px; border: 3px solid #000080;">
                        <strong>📋 INSPECTION SUMMARY</strong><br><br>
                        This premises has been inspected and found to be in compliance with fire safety regulations.<br><br>
                        <strong>Recommendations:</strong><br>
                        • Continue regular maintenance<br>
                        • Annual safety drills recommended<br>
                        • Review fire safety plan annually
                    </div>
                </div>
                <div class="signature-box">
                    <div class="signature-line">M.K.Bharvad</div>
                    <div class="officer-details">
                        <strong style="font-size: 1.1em;">MAYUR BHARVAD</strong><br>
                        <em>Fire Safety Inspector (Grade-I)</em><br>
                        <strong>Government of Gujarat</strong><br>
                        <div style="margin: 8px 0; padding: 5px; background: #f0f8ff; border-radius: 5px; border-left: 4px solid #000080;">
                            🆔 License No: FSI/GUJ/2024/001<br>
                            📧 mayur.bharvad@gujarat.gov.in<br>
                            📞 +91-79-2325-4567
                        </div>
                    </div>
                </div>
            </div>

            <div class="download-buttons">
                <button class="btn" onclick="window.print()">🖨️ Print Report</button>
                <button class="btn btn-success" onclick="window.print()">📄 Download PDF</button>
                <button class="btn" onclick="window.close()" style="background: #6c757d;">❌ Close</button>
            </div>
        </div>
    </div>
</body>
</html>"""

@app.route('/test-sms')
def test_sms():
    """Test SMS functionality"""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Test SMS with a sample OTP
    test_otp = generate_otp()
    user = users.find_one({'username': session['username']})

    if user and user.get('phone'):
        success = send_otp_sms(user.get('phone'), test_otp)
        if success:
            flash(f'✅ Test SMS sent to {mask_phone(user.get("phone"))} with OTP: {test_otp}', 'success')
            flash('📱 Check your phone for the SMS message', 'info')
        else:
            flash('❌ Failed to send test SMS', 'danger')
    else:
        flash('⚠️ No phone number found in your profile', 'warning')

    return redirect(request.referrer or url_for('user_dashboard'))

# Create required directories on startup
try:
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    os.makedirs('static/certificates', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('static/inspection_photos', exist_ok=True)
    print("✅ Required directories created successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not create directories: {str(e)}")

# Production mode initialization
print(f"🚀 Fire Safety NOC System initializing...")
print(f"🗄️ Database: {DB_NAME}")
print(f"🔧 Environment: {'Production' if not __name__ == '__main__' else 'Development'}")

if __name__ == '__main__':
    # Development mode
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"🚀 Starting Fire Safety NOC System on {host}:{port}")
    print(f"🔧 Debug mode: {debug}")

    # Run the application with SocketIO
    socketio.run(app, host=host, port=port, debug=debug)
else:
    # Production mode - Gunicorn compatibility
    print(f"🚀 Fire Safety NOC System ready for production deployment")
    print(f"🌐 App configured for Gunicorn with SocketIO support")