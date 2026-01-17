@echo off
REM ============================================================================
REM Update APK to Use Cloud URL
REM ============================================================================

echo.
echo ========================================
echo   UPDATE APK FOR CLOUD DEPLOYMENT
echo ========================================
echo.

set /p CLOUD_URL="Enter your Streamlit Cloud URL (e.g., https://myapp.streamlit.app): "

if "%CLOUD_URL%"=="" (
    echo ERROR: No URL provided!
    pause
    exit /b 1
)

echo.
echo Updating android_app/www/index.html...
echo Setting default URL to: %CLOUD_URL%
echo.

REM Create backup
copy android_app\www\index.html android_app\www\index.html.backup >nul 2>&1

REM Use PowerShell to replace the URL
powershell -Command "(Get-Content android_app\www\index.html) -replace 'value=\"http://192.168.0.[0-9]+:8501\"', 'value=\"%CLOUD_URL%\"' | Set-Content android_app\www\index.html"

echo ✓ Updated index.html
echo.
echo Now rebuilding APK...
echo.

REM Rebuild APK
call BUILD_APK_FIXED.bat

echo.
echo ========================================
echo   APK UPDATED!
echo ========================================
echo.
echo Your APK now points to: %CLOUD_URL%
echo.
echo Next steps:
echo 1. Find app-debug.apk in project folder
echo 2. Copy to phone and install
echo 3. Open app - it will auto-connect to cloud!
echo.
pause
