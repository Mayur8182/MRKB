@echo off
echo 🔧 Adding OpenCV dependency for AI models
echo ==========================================

echo 📁 Adding updated requirements.txt...
git add requirements.txt

echo 📝 Committing OpenCV fix...
git commit -m "🔧 Add OpenCV dependency for AI models

- Added opencv-python-headless==4.8.1.78 for computer vision functionality
- Resolves ModuleNotFoundError: No module named 'cv2'
- Required for real_ai_models.py image processing features
- Using headless version for server deployment (no GUI dependencies)"

echo 🚀 Pushing to GitHub...
git push origin main

echo ✅ OpenCV dependency added successfully!
echo 🔄 Render will now automatically redeploy with OpenCV support.
echo.
echo 📋 Added dependency:
echo - opencv-python-headless==4.8.1.78
echo.
pause
