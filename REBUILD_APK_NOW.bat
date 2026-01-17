@echo off
echo ========================================
echo   REBUILDING APK WITH CLOUD URL
echo ========================================
echo.

REM Update the temp folder with latest index.html
echo [1/3] Copying updated index.html to build folder...
copy android_app\www\index.html C:\temp\trading_hub_android\www\index.html /Y
echo Done!
echo.

REM Navigate to build folder
cd /d C:\temp\trading_hub_android\android

REM Set Java 21
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.5.11-hotspot

REM Clean old build
echo [2/3] Cleaning old build...
if exist "app\build\outputs" rd /s /q "app\build\outputs" 2>nul
echo Done!
echo.

REM Build APK
echo [3/3] Building APK (2-3 minutes)...
echo.
call gradlew.bat assembleDebug

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! APK REBUILT!
echo ========================================
echo.

REM Copy back to project
copy "app\build\outputs\apk\debug\app-debug.apk" "%~dp0app-debug.apk" /Y
echo.
echo APK Location: %~dp0app-debug.apk
echo APK Size:
for %%A in ("%~dp0app-debug.apk") do echo   %%~zA bytes (%.0f MB)

echo.
echo Cloud URL in APK: https://myprojectx-4uh3okcgzcdlcweor45kmq.streamlit.app
echo.
echo Next Steps:
echo 1. Transfer app-debug.apk to your phone
echo 2. Install it (may need to uninstall old version first)
echo 3. Open app - it will auto-connect to cloud!
echo 4. Works from ANYWHERE now (cellular, any Wi-Fi)
echo.
pause
