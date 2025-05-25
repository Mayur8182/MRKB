#!/usr/bin/env python3
"""
Enhanced Email Service for Fire NOC System
Provides comprehensive email notifications for the entire inspection workflow
"""

from datetime import datetime
from flask_mail import Message
import os

class EmailService:
    def __init__(self, mail_instance, app_config):
        self.mail = mail_instance
        self.config = app_config

    def send_email_with_template(self, subject, recipient, template_data, attachments=None):
        """Send email using HTML template"""
        try:
            # Generate HTML content
            html_body = self.generate_html_template(template_data)

            msg = Message(
                subject=subject,
                sender=self.config['MAIL_USERNAME'],
                recipients=[recipient]
            )
            msg.html = html_body
            msg.body = template_data.get('plain_text', '')

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, dict):
                        msg.attach(
                            attachment.get('filename', 'attachment'),
                            attachment.get('content_type', 'application/pdf'),
                            attachment.get('data')
                        )

            self.mail.send(msg)
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def generate_html_template(self, data):
        """Generate professional HTML email template"""
        template_type = data.get('template_type', 'default')

        # Base HTML structure
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{data.get('title', 'Fire NOC System')}</title>
            <style>
                {self.get_email_css()}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo-section">
                        <h1>🔥 Fire NOC System</h1>
                        <p>Government Fire Safety Department</p>
                    </div>
                </div>

                <div class="content">
                    {self.get_template_content(template_type, data)}
                </div>

                <div class="footer">
                    <p>Fire Safety Department | Government Portal</p>
                    <p>📧 support@firenoc.gov.in | 📞 1800-XXX-XXXX</p>
                    <p><small>This is an automated message. Please do not reply to this email.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def get_email_css(self):
        """Professional email CSS styling"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(135deg, #ff6b35, #f7931e);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 0;
        }
        .status-scheduled { background-color: #e3f2fd; color: #1976d2; }
        .status-started { background-color: #fff3e0; color: #f57c00; }
        .status-completed { background-color: #e8f5e8; color: #388e3c; }
        .status-approved { background-color: #e8f5e8; color: #2e7d32; }
        .info-box {
            background-color: #f8f9fa;
            border-left: 4px solid #ff6b35;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #ff6b35;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 15px 0;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }
        .details-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .details-table th, .details-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .details-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        """

    def get_template_content(self, template_type, data):
        """Generate content based on template type"""
        if template_type == 'application_received':
            return self.application_received_template(data)
        elif template_type == 'inspection_scheduled':
            return self.inspection_scheduled_template(data)
        elif template_type == 'inspector_assignment':
            return self.inspector_assignment_template(data)
        elif template_type == 'inspection_started':
            return self.inspection_started_template(data)
        elif template_type == 'inspection_completed':
            return self.inspection_completed_template(data)
        elif template_type == 'manager_approval':
            return self.manager_approval_template(data)
        elif template_type == 'certificate_issued':
            return self.certificate_issued_template(data)
        else:
            return self.default_template(data)

    def application_received_template(self, data):
        """Template for when manager receives new application"""
        return f"""
        <h2>🆕 New NOC Application Received</h2>
        <p>Dear Manager,</p>
        <p>A new Fire NOC application has been submitted and requires your review.</p>

        <div class="info-box">
            <h3>Application Details:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Business Type:</th><td>{data.get('business_type', 'N/A')}</td></tr>
                <tr><th>Applicant:</th><td>{data.get('applicant_name', 'N/A')}</td></tr>
                <tr><th>Application ID:</th><td>{data.get('application_id', 'N/A')}</td></tr>
                <tr><th>Submitted Date:</th><td>{data.get('submission_date', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Review the application documents</li>
            <li>Assign an inspector for site inspection</li>
            <li>Schedule the inspection date</li>
        </ul>

        <a href="{data.get('dashboard_url', '#')}" class="button">Review Application</a>
        """

    def inspection_scheduled_template(self, data):
        """Template for user notification about scheduled inspection"""
        return f"""
        <h2>📅 Inspection Scheduled for Your Application</h2>
        <p>Dear {data.get('user_name', 'Applicant')},</p>
        <p>Great news! An inspector has been assigned to your Fire NOC application.</p>

        <div class="status-badge status-scheduled">Inspection Scheduled</div>

        <div class="info-box">
            <h3>Inspection Details:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Inspector Name:</th><td>{data.get('inspector_name', 'N/A')}</td></tr>
                <tr><th>Scheduled Date:</th><td>{data.get('inspection_date', 'N/A')}</td></tr>
                <tr><th>Application ID:</th><td>{data.get('application_id', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>🔍 What to Prepare:</strong></p>
        <ul>
            <li>Ensure all fire safety equipment is accessible</li>
            <li>Have all required documents ready for verification</li>
            <li>Designate a responsible person to accompany the inspector</li>
            <li>Ensure clear access to all areas of the premises</li>
        </ul>

        <a href="{data.get('application_url', '#')}" class="button">View Application Status</a>
        """

    def inspector_assignment_template(self, data):
        """Template for inspector assignment notification"""
        return f"""
        <h2>🔍 New Inspection Assignment</h2>
        <p>Dear {data.get('inspector_name', 'Inspector')},</p>
        <p>You have been assigned a new inspection. Please review the details below and plan your visit accordingly.</p>

        <div class="status-badge status-scheduled">New Assignment</div>

        <div class="info-box">
            <h3>Assignment Details:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Business Address:</th><td>{data.get('business_address', 'N/A')}</td></tr>
                <tr><th>Business Type:</th><td>{data.get('business_type', 'N/A')}</td></tr>
                <tr><th>Scheduled Date:</th><td>{data.get('inspection_date', 'N/A')}</td></tr>
                <tr><th>Application ID:</th><td>{data.get('application_id', 'N/A')}</td></tr>
                <tr><th>Assigned By:</th><td>{data.get('assigned_by', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>📋 Inspection Checklist:</strong></p>
        <ul>
            <li>Verify fire safety equipment installation</li>
            <li>Check emergency exit routes</li>
            <li>Inspect fire extinguisher placement</li>
            <li>Document findings with photos/videos</li>
            <li>Complete inspection report</li>
        </ul>

        <a href="{data.get('inspector_dashboard_url', '#')}" class="button">Access Inspector Dashboard</a>
        """

    def inspection_started_template(self, data):
        """Template for user notification when inspection starts"""
        return f"""
        <h2>🚀 Inspection Started</h2>
        <p>Dear {data.get('user_name', 'Applicant')},</p>
        <p>Your Fire NOC inspection has officially started. Our inspector is now conducting the site evaluation.</p>

        <div class="status-badge status-started">Inspection In Progress</div>

        <div class="info-box">
            <h3>Current Status:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Inspector:</th><td>{data.get('inspector_name', 'N/A')}</td></tr>
                <tr><th>Started At:</th><td>{data.get('start_time', 'N/A')}</td></tr>
                <tr><th>Application ID:</th><td>{data.get('application_id', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>⏱️ What's Happening Now:</strong></p>
        <ul>
            <li>Inspector is evaluating your fire safety measures</li>
            <li>Documentation and photos are being taken</li>
            <li>Compliance assessment is in progress</li>
            <li>You will receive a detailed report upon completion</li>
        </ul>

        <p><em>Please cooperate with the inspector and provide any requested information.</em></p>

        <a href="{data.get('application_url', '#')}" class="button">Track Progress</a>
        """

    def inspection_completed_template(self, data):
        """Template for user notification when inspection is completed"""
        return f"""
        <h2>✅ Inspection Completed</h2>
        <p>Dear {data.get('user_name', 'Applicant')},</p>
        <p>Your Fire NOC inspection has been successfully completed. Please find the detailed inspection report attached.</p>

        <div class="status-badge status-completed">Inspection Complete</div>

        <div class="info-box">
            <h3>Inspection Summary:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Inspector:</th><td>{data.get('inspector_name', 'N/A')}</td></tr>
                <tr><th>Completed At:</th><td>{data.get('completion_time', 'N/A')}</td></tr>
                <tr><th>Compliance Score:</th><td>{data.get('compliance_score', 'N/A')}%</td></tr>
                <tr><th>Overall Result:</th><td>{data.get('overall_result', 'N/A')}</td></tr>
                <tr><th>Report Number:</th><td>{data.get('report_number', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>📋 Next Steps:</strong></p>
        <ul>
            <li>Review the attached inspection report</li>
            <li>Address any recommendations mentioned</li>
            <li>Wait for manager approval</li>
            <li>Certificate will be issued upon approval</li>
        </ul>

        <p><strong>📎 Attachments:</strong> Detailed Inspection Report (PDF)</p>

        <a href="{data.get('application_url', '#')}" class="button">View Full Report</a>
        """

    def manager_approval_template(self, data):
        """Template for manager notification about completed inspection"""
        return f"""
        <h2>📊 Inspection Report Ready for Review</h2>
        <p>Dear Manager,</p>
        <p>An inspection has been completed and requires your review and approval. The detailed report is attached for your evaluation.</p>

        <div class="status-badge status-completed">Awaiting Approval</div>

        <div class="info-box">
            <h3>Inspection Details:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Inspector:</th><td>{data.get('inspector_name', 'N/A')}</td></tr>
                <tr><th>Completed Date:</th><td>{data.get('completion_date', 'N/A')}</td></tr>
                <tr><th>Compliance Score:</th><td>{data.get('compliance_score', 'N/A')}%</td></tr>
                <tr><th>Inspector Recommendation:</th><td>{data.get('recommendation', 'N/A')}</td></tr>
                <tr><th>Application ID:</th><td>{data.get('application_id', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>🔍 Key Findings:</strong></p>
        <ul>
            {self.format_findings_list(data.get('key_findings', []))}
        </ul>

        <p><strong>📎 Attachments:</strong> Complete Inspection Report with Photos (PDF)</p>

        <a href="{data.get('manager_dashboard_url', '#')}" class="button">Review & Approve</a>
        """

    def certificate_issued_template(self, data):
        """Template for user notification when certificate is issued"""
        return f"""
        <h2>🎉 NOC Certificate Issued!</h2>
        <p>Dear {data.get('user_name', 'Applicant')},</p>
        <p>Congratulations! Your Fire NOC application has been approved and your certificate has been issued.</p>

        <div class="status-badge status-approved">Certificate Issued</div>

        <div class="info-box">
            <h3>Certificate Details:</h3>
            <table class="details-table">
                <tr><th>Business Name:</th><td>{data.get('business_name', 'N/A')}</td></tr>
                <tr><th>Certificate Number:</th><td><strong>{data.get('certificate_number', 'N/A')}</strong></td></tr>
                <tr><th>Issue Date:</th><td>{data.get('issue_date', 'N/A')}</td></tr>
                <tr><th>Valid Until:</th><td>{data.get('valid_until', 'N/A')}</td></tr>
                <tr><th>Approved By:</th><td>{data.get('approved_by', 'N/A')}</td></tr>
            </table>
        </div>

        <p><strong>🏆 Your Certificate is Ready!</strong></p>
        <ul>
            <li>Official government-issued Fire NOC certificate</li>
            <li>Blockchain-verified for authenticity</li>
            <li>Valid for business operations</li>
            <li>QR code for instant verification</li>
        </ul>

        <p><strong>📎 Attachments:</strong> Official NOC Certificate (PDF)</p>

        <a href="{data.get('certificate_url', '#')}" class="button">Download Certificate</a>

        <p><em>Please keep this certificate safe and display it at your business premises as required by law.</em></p>
        """

    def default_template(self, data):
        """Default template for general notifications"""
        return f"""
        <h2>{data.get('title', 'Fire NOC System Notification')}</h2>
        <p>Dear {data.get('recipient_name', 'User')},</p>
        <p>{data.get('message', 'You have received a new notification from the Fire NOC System.')}</p>

        <div class="info-box">
            <p>{data.get('details', 'Please check your dashboard for more information.')}</p>
        </div>

        <a href="{data.get('action_url', '#')}" class="button">{data.get('action_text', 'View Details')}</a>
        """

    def format_findings_list(self, findings):
        """Format findings list for email template"""
        if not findings:
            return "<li>No specific findings reported</li>"

        formatted_items = []
        for finding in findings[:5]:  # Limit to 5 items for email
            formatted_items.append(f"<li>{finding}</li>")

        if len(findings) > 5:
            formatted_items.append("<li>...and more (see full report)</li>")

        return "\n".join(formatted_items)
