# 🔥 Fire Safety NOC System

A comprehensive Fire Safety No Objection Certificate (NOC) management system built with Flask, MongoDB Atlas, and modern web technologies. This system revolutionizes fire safety compliance management with advanced features including 2FA authentication, multi-role dashboards, AI-powered document verification, and automated certificate generation.

## 🌟 Key Features

### 🔐 Advanced Authentication & Security
- **2FA Authentication**: Email + SMS OTP verification
- **Multi-role Access Control**: User, Inspector, Manager, Admin roles
- **Secure Session Management**: Extended session lifetime with proper security
- **Password Encryption**: bcrypt hashing for secure password storage

### 👥 Multi-Role Dashboard System
- **User Dashboard**: Application submission, status tracking, certificate downloads
- **Inspector Dashboard**: Site inspection tools, video capabilities, report generation
- **Manager Dashboard**: Application approval, inspector assignment, analytics
- **Admin Dashboard**: Complete system control, user management, audit logs

### 📄 NOC Application Management
- **Smart Application Forms**: Dynamic form validation and real-time feedback
- **Document Upload**: Secure file handling with verification
- **Status Tracking**: Real-time application status updates
- **Automated Workflows**: Streamlined approval processes

### 🏆 Certificate Generation & Verification
- **Government-Style Certificates**: Professional NOC certificates with official formatting
- **QR Code Integration**: Scannable QR codes for certificate verification
- **Digital Signatures**: M.K.Bharvad signature with official officer details
- **Bulk Certificate Generation**: Admin tools for mass certificate creation

### 📧 Communication System
- **Email Notifications**: Comprehensive email system for all workflow stages
- **SMS Integration**: Twilio and MSG91 integration for OTP and notifications
- **Real-time Updates**: Socket.IO for live dashboard updates
- **Enhanced Email Templates**: Professional HTML email designs

### 🔍 Advanced Inspection Workflow
- **Inspector Assignment**: Automated inspector allocation system
- **Site Inspection Tools**: Photo/video capture capabilities
- **Compliance Scoring**: Automated compliance assessment
- **Report Generation**: Comprehensive inspection reports with government formatting

### 📊 Analytics & Reporting
- **Real-time Analytics**: Live dashboard statistics and metrics
- **Performance Tracking**: Inspector and manager performance monitoring
- **Audit Logs**: Complete activity tracking and audit trails
- **Data Visualization**: Charts and graphs for insights

### 🤖 AI & Automation Features
- **Document Verification**: AI-powered document analysis
- **Predictive Analytics**: Fire risk assessment algorithms
- **Automated Processing**: Smart application routing and approval
- **Blockchain Integration**: Certificate verification on blockchain

## 🛠️ Technology Stack

### Backend
- **Flask 2.3.3**: Modern Python web framework
- **MongoDB Atlas**: Cloud database with global distribution
- **PyMongo 4.5.0**: MongoDB driver for Python
- **Flask-SocketIO**: Real-time communication
- **bcrypt**: Password hashing and security

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **jQuery**: Dynamic frontend interactions
- **Chart.js**: Data visualization
- **Font Awesome**: Icon library
- **Custom CSS**: Modern design system

### Communication & Notifications
- **Flask-Mail**: Email service integration
- **Twilio**: SMS and voice services
- **MSG91**: Indian SMS service provider
- **SMTP**: Gmail integration for emails

### File Processing & Generation
- **Pillow (PIL)**: Image processing
- **ReportLab**: PDF generation
- **pytesseract**: OCR capabilities
- **QR Code Generation**: Certificate verification

### Production & Deployment
- **Gunicorn**: WSGI HTTP Server
- **Eventlet**: Async networking library
- **Render Platform**: Cloud deployment
- **Environment Variables**: Secure configuration management

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MongoDB Atlas account
- Gmail account for email services
- Twilio account for SMS (optional)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <your-repository-url>
cd fire
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run startup checks**
```bash
python start.py
```

5. **Start the application**
```bash
python app.py
```

6. **Access the application**
- Open http://localhost:5000
- Register a new account
- Explore the features

### Production Deployment (Render)

1. **Prepare for deployment**
```bash
python start.py  # Verify configuration
```

2. **Deploy to Render**
- Follow the detailed guide in `RENDER_DEPLOYMENT_GUIDE.md`
- Configure environment variables in Render dashboard
- Deploy and monitor

3. **Verify deployment**
```bash
python test_deployment.py
```

## 📁 Project Structure

```
fire/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── Procfile                       # Render deployment configuration
├── render.yaml                    # Render service configuration
├── runtime.txt                    # Python version specification
├── start.py                       # Startup verification script
├── test_deployment.py             # Deployment testing script
├── .env                          # Environment variables (local)
├── .gitignore                    # Git ignore rules
├── RENDER_DEPLOYMENT_GUIDE.md     # Comprehensive deployment guide
│
├── templates/                     # HTML templates
│   ├── base.html                 # Base template
│   ├── index.html                # Homepage
│   ├── login.html                # Login page
│   ├── register.html             # Registration page
│   ├── user_dashboard.html       # User dashboard
│   ├── manager_dashboard.html    # Manager dashboard
│   ├── inspector_dashboard.html  # Inspector dashboard
│   ├── admin_dashboard.html      # Admin dashboard
│   └── certificate_template.html # Certificate template
│
├── static/                       # Static files
│   ├── css/                     # Stylesheets
│   ├── js/                      # JavaScript files
│   ├── images/                  # Images and logos
│   ├── certificates/            # Generated certificates
│   ├── reports/                 # Inspection reports
│   ├── profile_images/          # User profile images
│   └── inspection_photos/       # Inspection photos
│
├── uploads/                      # File uploads
├── models/                       # AI models (if any)
└── data/                        # Data files and backups
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=False

# Database Configuration
DATABASE_URL=mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGODB_URI=mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=aek_noc

# Security
SECRET_KEY=your_super_secure_secret_key_change_this_in_production_2024

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=mkbharvad534@gmail.com
MAIL_PASSWORD=dwtp fmiq miyl ccvq
MAIL_USE_TLS=True

# SMS Configuration
TWILIO_ACCOUNT_SID=YOUR_TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN=YOUR_TWILIO_AUTH_TOKEN
MSG91_AUTH_KEY=YOUR_MSG91_API_KEY

# Application Settings
UPLOAD_FOLDER=static/profile_images
MAX_CONTENT_LENGTH=16777216
PORT=5000
HOST=0.0.0.0
```
