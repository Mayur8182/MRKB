@echo off
echo 🔧 Fixing Flask-WTF and Werkzeug Compatibility Issue
echo ===================================================

echo 📁 Adding updated requirements.txt...
git add requirements.txt

echo 📝 Committing compatibility fix...
git commit -m "🔧 Fix Flask-WTF and Werkzeug compatibility issue

- Updated Flask-WTF from 1.0.1 to 1.2.1 (compatible with newer Werkzeug)
- Fixed werkzeug version to 2.3.7 for stability
- Resolves ImportError: cannot import name 'url_encode' from 'werkzeug.urls'
- Ensures compatibility between Flask-WTF and Werkzeug versions"

echo 🚀 Pushing to GitHub...
git push origin main

echo ✅ Flask-WTF compatibility issue fixed!
echo 🔄 Render will now automatically redeploy with compatible versions.
echo.
echo 📋 Changes made:
echo - Flask-WTF: 1.0.1 → 1.2.1
echo - Werkzeug: >=2.3.7 → 2.3.7 (fixed version)
echo.
pause
