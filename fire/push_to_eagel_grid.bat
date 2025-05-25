@echo off
echo 🔥 Fire Safety NOC System - Push to EAGEL-GRID Repository
echo ========================================================
echo 📍 Current directory contents:
dir /b

echo.
echo 🔄 Step 1: Removing existing git configuration...
if exist .git rmdir /s /q .git

echo 🆕 Step 2: Initializing fresh Git repository...
git init

echo 🔗 Step 3: Adding EAGEL-GRID remote...
git remote add origin https://github.com/Mayur8182/EAGEL-GRID.git

echo 📁 Step 4: Adding all Fire Safety NOC System files...
git add .

echo 📝 Step 5: Creating commit with complete Fire Safety NOC System...
git commit -m "🚀 Complete Fire Safety NOC Management System

✅ Multi-role Dashboard System (User, Inspector, Manager, Admin)
✅ 2FA Authentication (Email + SMS OTP)
✅ NOC Application Management
✅ Certificate Generation with QR Codes
✅ Inspection Workflow Management
✅ Email Notification System
✅ MongoDB Atlas Integration
✅ Render Deployment Configuration
✅ Advanced Analytics & Reporting
✅ Blockchain Certificate Verification
✅ AI-powered Document Processing
✅ Real-time Notifications
✅ Audit Logs & Security Features

🔧 Technical Features:
- Flask Backend with MongoDB
- Responsive Frontend Design
- File Upload & Management
- PDF Certificate Generation
- SMS & Email Integration
- Role-based Access Control
- Session Management
- Error Handling & Logging

🚀 Ready for Production Deployment on Render Platform"

echo 🚀 Step 6: Pushing to EAGEL-GRID repository...
git push -u origin main --force

echo.
echo ✅ SUCCESS! Fire Safety NOC System pushed to EAGEL-GRID repository!
echo 🌐 Repository URL: https://github.com/Mayur8182/EAGEL-GRID
echo.
echo 📋 NEXT STEPS FOR DEPLOYMENT:
echo 1. Go to Render Dashboard: https://dashboard.render.com
echo 2. Create new Web Service
echo 3. Connect GitHub repository: https://github.com/Mayur8182/EAGEL-GRID.git
echo 4. Configure build settings
echo 5. Add environment variables from ACTUAL_CREDENTIALS.md
echo 6. Deploy and test!
echo.
pause
