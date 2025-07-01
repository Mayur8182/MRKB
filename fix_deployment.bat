@echo off
echo ======================================================
echo 🔧 Fire Safety NOC System - Deployment Fix Script
echo ======================================================
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
echo ✅ Deployment fix completed!
echo.
echo 📝 Note: If you still encounter issues, try the following:
echo  - Use Python 3.10.13 instead of Python 3.13.4
echo  - Install dependencies one by one
echo  - Check for any conflicting dependencies
echo.
echo Press any key to exit...
pause > nul