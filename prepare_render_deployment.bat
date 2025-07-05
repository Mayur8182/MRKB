@echo off
echo ======================================================
echo 🚀 Fire Safety NOC System - Render Deployment Preparation
echo ======================================================
echo.

echo 📋 Checking for required files...

if not exist "requirements.txt" (
    echo ❌ requirements.txt not found in root directory
    echo 📝 Copying from fire directory...
    copy "fire\requirements.txt" "requirements.txt"
) else (
    echo ✅ requirements.txt found
)

if not exist "runtime.txt" (
    echo ❌ runtime.txt not found in root directory
    echo 📝 Creating runtime.txt...
    echo python-3.10.13 > runtime.txt
) else (
    echo ✅ runtime.txt found
)

if not exist "Procfile" (
    echo ❌ Procfile not found in root directory
    echo 📝 Creating Procfile...
    echo web: gunicorn --bind 0.0.0.0:$PORT simple_wsgi:application > Procfile
) else (
    echo ✅ Procfile found
)

if not exist "simple_wsgi.py" (
    echo ❌ simple_wsgi.py not found in root directory
    echo 📝 Copying from fire directory...
    copy "fire\simple_wsgi.py" "simple_wsgi.py"
) else (
    echo ✅ simple_wsgi.py found
)

if not exist "render.yaml" (
    echo ❌ render.yaml not found in root directory
    echo 📝 Copying from fire directory...
    copy "fire\render.yaml" "render.yaml"
) else (
    echo ✅ render.yaml found
)

echo.
echo 📦 Updating pip, setuptools, and wheel...
pip install --upgrade pip setuptools wheel

echo.
echo 📋 Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo 🔍 Checking dependencies...
python check_dependencies.py

echo.
echo ✅ Deployment preparation completed!
echo.
echo 📝 Next steps:
echo  1. Push your code to GitHub
echo  2. Create a new Web Service on Render
echo  3. Connect to your GitHub repository
echo  4. Set build command: pip install -r requirements.txt
echo  5. Set start command: gunicorn --bind 0.0.0.0:$PORT simple_wsgi:application
echo  6. Add all required environment variables
echo  7. Deploy your application
echo.
echo Press any key to exit...
pause > nul