@echo off
echo 🔥 Fire Shakti APK Generation Script
echo ====================================

echo.
echo 📱 Method 1: PWA2APK Online Tool (Recommended)
echo -----------------------------------------------
echo 1. Go to: https://www.pwa2apk.com/
echo 2. Enter URL: https://mrkb.onrender.com
echo 3. Configure:
echo    - App Name: Fire Shakti NOC Portal
echo    - Package: com.fireshakti.nocportal
echo    - Version: 1.0.0
echo 4. Click "Generate APK"
echo 5. Download your APK!

echo.
echo 📱 Method 2: PWABuilder by Microsoft
echo ------------------------------------
echo 1. Go to: https://www.pwabuilder.com/
echo 2. Enter URL: https://mrkb.onrender.com
echo 3. Follow the wizard
echo 4. Download Android package

echo.
echo 📱 Method 3: Bubblewrap CLI (Advanced)
echo --------------------------------------
echo Prerequisites:
echo - Node.js ✅ Installed
echo - Java JDK ✅ Installed
echo - Android SDK ✅ Installed

echo.
echo Running Bubblewrap commands...
cd fire-shakti-apk

echo.
echo 🔧 Initializing Bubblewrap project...
bubblewrap init --manifest=twa-manifest.json

if %ERRORLEVEL% EQU 0 (
    echo ✅ Bubblewrap initialization successful!
    echo.
    echo 🏗️ Building APK...
    bubblewrap build
    
    if %ERRORLEVEL% EQU 0 (
        echo ✅ APK build successful!
        echo.
        echo 📱 APK Location: fire-shakti-apk\app\build\outputs\apk\release\
        echo.
        echo 🎉 Your Fire Shakti APK is ready!
    ) else (
        echo ❌ APK build failed. Try online methods instead.
    )
) else (
    echo ❌ Bubblewrap initialization failed.
    echo.
    echo 💡 Recommended: Use PWA2APK online tool instead
    echo    URL: https://www.pwa2apk.com/
    echo    Enter: https://mrkb.onrender.com
)

echo.
echo 🔗 Your PWA is live at: https://mrkb.onrender.com
echo 📋 APK Package ID: com.fireshakti.nocportal
echo 🎯 App Name: Fire Shakti NOC Portal

pause
