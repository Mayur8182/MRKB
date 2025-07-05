# 🚀 Fire Safety NOC System - Render Deployment Checklist

Use this checklist to ensure a successful deployment on Render.

## 📋 Pre-Deployment Checklist

- [ ] Updated `requirements.txt` with compatible dependencies
  - [ ] Downgraded Pillow to 9.0.1
  - [ ] Commented out tensorflow and keras
  - [ ] Downgraded pandas to 2.0.3
  - [ ] Added pip, setuptools, and wheel
  - [ ] Added build package

- [ ] Updated `runtime.txt` to specify Python 3.10.13

- [ ] Verified all necessary files exist in the root directory
  - [ ] `app.py`
  - [ ] `requirements.txt`
  - [ ] `runtime.txt`
  - [ ] `Procfile`
  - [ ] `render.yaml`
  - [ ] `simple_wsgi.py`

## 🔧 Render Dashboard Configuration

- [ ] Created a new Web Service
  - [ ] Connected to GitHub repository
  - [ ] Selected Python environment
  - [ ] Set build command: `pip install -r requirements.txt`
  - [ ] Set start command: `gunicorn --bind 0.0.0.0:$PORT simple_wsgi:application`

- [ ] Added all required environment variables
  - [ ] Core Configuration (FLASK_APP, FLASK_ENV, etc.)
  - [ ] Database Configuration (MONGODB_URI, DB_NAME)
  - [ ] Security Configuration (SECRET_KEY, SESSION_PERMANENT, etc.)
  - [ ] Email Configuration (MAIL_SERVER, MAIL_PORT, etc.)
  - [ ] SMS Configuration (MSG91_AUTH_KEY, MSG91_SENDER_ID, etc.)
  - [ ] File Upload Configuration (UPLOAD_FOLDER, MAX_CONTENT_LENGTH, etc.)

## 🚀 Deployment Process

- [ ] Initiated deployment
- [ ] Monitored build logs for errors
- [ ] Verified deployment was successful
- [ ] Tested application functionality
  - [ ] User registration and login
  - [ ] OTP verification
  - [ ] File uploads
  - [ ] Form submissions
  - [ ] Email notifications
  - [ ] SMS notifications
  - [ ] Certificate generation and verification

## 🔍 Troubleshooting

If you encounter issues during deployment, check the following:

- [ ] Build logs for dependency installation errors
- [ ] Application logs for runtime errors
- [ ] Environment variables for missing or incorrect values
- [ ] Database connection for authentication or network issues
- [ ] File permissions for upload issues

## 📝 Post-Deployment Tasks

- [ ] Set up custom domain (if needed)
- [ ] Configure SSL certificate
- [ ] Set up monitoring and alerts
- [ ] Create backup and restore procedures
- [ ] Document deployment process for future reference

## 🔄 Update Process

- [ ] Make changes to the codebase
- [ ] Push changes to GitHub
- [ ] Monitor automatic deployment
- [ ] Verify changes were deployed successfully