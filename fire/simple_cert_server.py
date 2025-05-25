from flask import Flask, render_template, request, make_response, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fire_noc_system']
    applications = db['applications']
    certificates = db['certificates']
    inspections = db['inspections']
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@app.route('/')
def home():
    return "Certificate Server Running"

@app.route('/view-certificate/<application_id>')
def view_certificate(application_id):
    """View certificate HTML for application"""
    try:
        print(f"VIEW CERT: Attempting to view certificate for application: {application_id}")

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
            pan_number=app_data.get('pan_number', 'ABCDE1234F'),
            issue_date=certificate['issued_date'].strftime('%d/%m/%Y') if certificate.get('issued_date') else datetime.now().strftime('%d/%m/%Y'),
            valid_until=certificate['valid_until'].strftime('%d/%m/%Y') if certificate.get('valid_until') else (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
            compliance_score=compliance_score,
            inspector_name=inspector_name,
            inspector_signature=f"Digitally Signed by {inspector_name}",
            manager_signature=f"Digitally Signed by {certificate.get('issued_by', 'Manager')}",
            approved_by=certificate.get('issued_by', 'Fire Safety Manager')
        )

    except Exception as e:
        print(f"VIEW CERT: Error viewing certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error viewing certificate: {str(e)}", 500

@app.route('/download-certificate/<application_id>')
def download_certificate(application_id):
    """Download certificate as PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        app_data = applications.find_one({'_id': ObjectId(application_id)})
        if not app_data:
            return "Application not found", 404
            
        certificate = certificates.find_one({'application_id': ObjectId(application_id)})
        if not certificate:
            return "Certificate not found", 404
        
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
        
        # Content
        story = []
        
        # Government Header
        story.append(Paragraph("🇮🇳", styles['GovTitle']))
        story.append(Paragraph("<b>Government of India</b><br/>Ministry of Home Affairs<br/>Directorate General of Fire Services<br/>Office of the Additional Director General of Fire Services, Gujarat<br/>3rd Floor, Fire Safety Building, Sector-10, Gandhinagar, GUJARAT", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Certificate Title
        story.append(Paragraph("<b>Fire Safety Certificate</b>", styles['GovTitle']))
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
        
        # Create filename
        business_name = app_data.get('business_name', 'Business').replace(' ', '_')
        certificate_number = certificate['certificate_number']
        filename = f"NOC_Certificate_{business_name}_{certificate_number}.pdf"

        # Return PDF as download
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error generating PDF: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)
