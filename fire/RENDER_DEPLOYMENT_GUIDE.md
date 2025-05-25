# 🚀 Fire Safety NOC System - Render Deployment Guide

## 📋 Overview
This guide will help you deploy your Fire Safety NOC System to Render platform with MongoDB Atlas integration.

## 🔧 Prerequisites
1. **Render Account**: Sign up at [render.com](https://render.com)
2. **MongoDB Atlas**: Your database is already configured
3. **GitHub Repository**: Your code should be in a GitHub repository

## 📁 Project Structure
```
fire/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── Procfile                 # Process configuration for Render
├── render.yaml              # Render deployment configuration
├── runtime.txt              # Python version specification
├── .env                     # Environment variables (for local development)
├── templates/               # HTML templates
├── static/                  # Static files (CSS, JS, images)
└── uploads/                 # File uploads directory
```

## 🗄️ Database Configuration
Your MongoDB Atlas connection is already configured:
- **Connection String**: `mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
- **Database Name**: `aek_noc`
- **Collections**: users, applications, contacts, activities, reports, otp_codes, inspections, notifications, licenses, inspection_reports, certificates, inventory

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository
1. Ensure all files are in your GitHub repository
2. Make sure the `fire/` directory contains all necessary files
3. Commit and push all changes

### Step 2: Create Render Web Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select your repository and branch

### Step 3: Configure Build Settings
```
Build Command: pip install -r requirements.txt
Start Command: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

### Step 4: Set Environment Variables
Add these environment variables in Render dashboard:

**Flask Configuration:**
- `FLASK_APP`: `app.py`
- `FLASK_ENV`: `production`
- `FLASK_DEBUG`: `False`

**Database Configuration:**
- `DATABASE_URL`: `mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
- `MONGODB_URI`: `mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
- `DB_NAME`: `aek_noc`

**Security:**
- `SECRET_KEY`: `your_super_secure_secret_key_change_this_in_production_2024_render`

**Email Configuration:**
- `MAIL_SERVER`: `smtp.gmail.com`
- `MAIL_PORT`: `587`
- `MAIL_USERNAME`: `mkbharvad534@gmail.com`
- `MAIL_PASSWORD`: `dwtp fmiq miyl ccvq`
- `MAIL_USE_TLS`: `True`
- `MAIL_USE_SSL`: `False`

**SMS Configuration:**
- `TWILIO_ACCOUNT_SID`: `YOUR_TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`: `YOUR_TWILIO_AUTH_TOKEN`
- `MSG91_AUTH_KEY`: `YOUR_MSG91_API_KEY`

### Step 5: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. Monitor the build logs for any errors

## 🔍 Verification Steps

### 1. Check Application Status
- Verify the service is running in Render dashboard
- Check build and deploy logs for errors

### 2. Test Database Connection
- Visit your deployed URL
- Try to register a new user
- Check if data is saved in MongoDB Atlas

### 3. Test Core Features
- **User Registration**: With email and SMS OTP
- **Login System**: With 2FA authentication
- **Dashboard Access**: User, Manager, Inspector, Admin dashboards
- **NOC Application**: Submit and manage applications
- **File Uploads**: Profile images and documents
- **Email Notifications**: Registration, OTP, certificates
- **Certificate Generation**: Download and view certificates

## 🛠️ Troubleshooting

### Common Issues:

**1. Build Failures:**
- Check `requirements.txt` for invalid packages
- Verify Python version in `runtime.txt`
- Review build logs in Render dashboard

**2. Database Connection Issues:**
- Verify MongoDB Atlas connection string
- Check network access settings in MongoDB Atlas
- Ensure database name is correct

**3. Environment Variables:**
- Double-check all environment variable names and values
- Ensure sensitive data is properly configured
- Verify boolean values are strings ("True"/"False")

**4. File Upload Issues:**
- Render has ephemeral storage
- Consider using cloud storage (AWS S3, Cloudinary) for production
- Static files are served correctly

**5. Email/SMS Issues:**
- Verify Gmail app password is correct
- Check Twilio and MSG91 credentials
- Test with actual phone numbers

## 📊 Monitoring & Maintenance

### 1. Application Monitoring
- Monitor application logs in Render dashboard
- Set up alerts for application downtime
- Monitor database performance in MongoDB Atlas

### 2. Database Maintenance
- Regular backups in MongoDB Atlas
- Monitor database size and performance
- Clean up old OTP codes and temporary data

### 3. Security
- Regularly update dependencies
- Monitor for security vulnerabilities
- Keep API keys and passwords secure

## 🌐 Production URLs
After deployment, your application will be available at:
- **Main URL**: `https://your-app-name.onrender.com`
- **Admin Dashboard**: `https://your-app-name.onrender.com/admin_dashboard`
- **API Endpoints**: `https://your-app-name.onrender.com/api/*`

## 📞 Support
If you encounter issues:
1. Check Render documentation
2. Review application logs
3. Verify MongoDB Atlas connectivity
4. Test locally with production environment variables

## 🎉 Success!
Once deployed successfully, your Fire Safety NOC System will be:
- ✅ Running on Render platform
- ✅ Connected to MongoDB Atlas
- ✅ Accessible worldwide
- ✅ Ready for production use

Your application includes:
- 🔐 2FA Authentication (Email + SMS)
- 👥 Multi-role dashboards (User, Inspector, Manager, Admin)
- 📄 NOC application management
- 🏆 Certificate generation and verification
- 📧 Email notification system
- 📱 SMS OTP verification
- 🔍 Advanced inspection workflows
- 📊 Analytics and reporting
- 🛡️ Security features and audit logs
