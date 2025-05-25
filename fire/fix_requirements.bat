@echo off
echo 🔧 Fixing Requirements.txt Dependency Conflict
echo ===============================================

echo 📁 Adding updated requirements.txt...
git add requirements.txt

echo 📝 Committing fix...
git commit -m "🔧 Fix dependency conflict: Update werkzeug version for Flask compatibility

- Changed werkzeug==2.3.4 to werkzeug>=2.3.7
- Resolves Flask 2.3.3 dependency conflict
- Ensures compatibility with all Flask dependencies"

echo 🚀 Pushing to GitHub...
git push origin main

echo ✅ Requirements.txt updated successfully!
echo 🔄 Render will now automatically redeploy with fixed dependencies.
echo.
pause
