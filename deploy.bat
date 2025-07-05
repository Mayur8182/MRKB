@echo off
echo 🔥 Fire Shakti - PWA Deployment Script
echo =====================================

echo.
echo 📋 Checking Git status...
git status

echo.
echo 📦 Adding all files to Git...
git add .

echo.
echo 💬 Committing changes...
set /p commit_message="Enter commit message (or press Enter for default): "
if "%commit_message%"=="" set commit_message="PWA deployment ready - Added manifest, service worker, and Render config"

git commit -m "%commit_message%"

echo.
echo 🚀 Pushing to GitHub...
git push origin main

echo.
echo ✅ Deployment complete!
echo.
echo 📱 Next steps:
echo 1. Go to Render.com and connect your GitHub repository
echo 2. Render will automatically detect render.yaml and deploy
echo 3. Your PWA will be live and installable!
echo.
echo 🔗 GitHub Repository: https://github.com/Mayur8182/MRKBsara
echo 📱 After deployment, users can install the PWA from browser
echo 📦 Use Bubblewrap to generate APK: cd fire-shakti-apk && bubblewrap build
echo.
pause
