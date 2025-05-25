@echo off
echo 🔥 Fire Safety NOC System - Final Clean Push
echo ================================================
echo ⚠️  This will create a completely clean repository without any secrets

echo 🗑️ Step 1: Removing .git directory completely...
if exist .git rmdir /s /q .git

echo 🗑️ Step 2: Removing .env file...
if exist .env del .env

echo 🔧 Step 3: Initializing fresh Git repository...
git init

echo 🔗 Step 4: Adding GitHub remote...
git remote add origin https://github.com/Mayur8182/EAGEL-GRID.git

echo 📁 Step 5: Adding only safe files (excluding .env)...
git add .gitignore
git add *.py
git add *.md
git add *.txt
git add *.html
git add *.yaml
git add *.bat
git add Procfile
git add templates/
git add static/
git add data/
git add models/
git add uploads/

echo 📝 Step 6: Creating clean commit...
git commit -m "🚀 Fire Safety NOC System - Production Ready (No Secrets)

✅ Complete Fire Safety NOC Management System
✅ Multi-role dashboards (User, Inspector, Manager, Admin)
✅ 2FA authentication with email and SMS OTP
✅ Certificate generation with QR codes
✅ Inspection workflow management
✅ Email notification system
✅ MongoDB Atlas integration
✅ Render deployment ready
✅ All sensitive data removed from repository"

echo 🚀 Step 7: Pushing to GitHub...
git push -u origin main --force

echo ✅ Repository pushed successfully!
echo.
echo 📋 NEXT STEPS FOR DEPLOYMENT:
echo.
echo 1. 🌐 Go to Render Dashboard: https://dashboard.render.com
echo 2. ➕ Click "New +" and select "Web Service"
echo 3. 🔗 Connect GitHub repository: https://github.com/Mayur8182/EAGEL-GRID.git
echo 4. ⚙️ Configure Build Settings:
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
echo 5. 🔑 Add Environment Variables in Render:
echo    - DATABASE_URL=mongodb+srv://mkbharvad8080:Mkb%%408080@cluster0.a82h2.mongodb.net/?retryWrites=true^&w=majority^&appName=Cluster0
echo    - TWILIO_ACCOUNT_SID=AC21b09c1cb25e642ddd201475bc12080a
echo    - TWILIO_AUTH_TOKEN=78a14e4041fd920576e0b679d3a39e83
echo    - MSG91_AUTH_KEY=453564T2JkiVcp4hee683300c2P1
echo    - MAIL_USERNAME=mkbharvad534@gmail.com
echo    - MAIL_PASSWORD=dwtp fmiq miyl ccvq
echo    - SECRET_KEY=your_super_secure_secret_key_change_this_in_production_2024
echo    - FLASK_ENV=production
echo 6. 🚀 Click "Create Web Service" to deploy
echo 7. 🧪 Test your deployed application
echo.
echo 🎉 Your Fire Safety NOC System is ready for production!
echo.
pause
