@echo off
echo 🚀 Fire Safety NOC System - Simple Push
echo ========================================

echo 🔧 Checking current directory...
dir

echo 🗑️ Removing any existing .git folder...
if exist .git rmdir /s /q .git

echo 🆕 Initializing new Git repository...
git init

echo 📡 Adding GitHub remote...
git remote add origin https://github.com/Mayur8182/EAGEL-GRID.git

echo 📄 Checking what files we have...
git status

echo ➕ Adding all files...
git add .

echo 📝 Creating commit...
git commit -m "Fire Safety NOC System - Complete Production System"

echo 🌐 Setting upstream and pushing...
git branch -M main
git push -u origin main

echo ✅ Done! Check your GitHub repository now.
echo 🔗 https://github.com/Mayur8182/EAGEL-GRID

pause
