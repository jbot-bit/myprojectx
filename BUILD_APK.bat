@echo off
REM Build Trading Hub Android APK
REM Requires: Java JDK 17+ installed

echo ========================================
echo   Trading Hub - Android APK Builder
echo ========================================
echo.

REM Check for Java
java -version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Java JDK not found!
    echo.
    echo Please install Java JDK 17:
    echo https://adoptium.net/temurin/releases/?version=17
    echo.
    echo After installing, run this script again.
    pause
    exit /b 1
)

echo Java found! Building APK...
echo.

cd android_app\android
call gradlew.bat assembleDebug

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! APK Built!
echo ========================================
echo.
echo APK Location:
echo android_app\android\app\build\outputs\apk\debug\app-debug.apk
echo.
echo Next Steps:
echo 1. Copy app-debug.apk to your phone
echo 2. Enable "Install from Unknown Sources"
echo 3. Tap the APK to install
echo.
pause
