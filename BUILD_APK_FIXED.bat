@echo off
REM Fixed APK Build Script - Handles OneDrive and Java version issues

echo ========================================
echo   Trading Hub - Android APK Builder
echo   (Fixed for OneDrive + Java 21)
echo ========================================
echo.

REM Step 1: Check if project is in local folder
if not exist "C:\temp\trading_hub_android" (
    echo [1/4] Copying project out of OneDrive...
    echo This avoids file locking issues during build.
    echo.

    mkdir "C:\temp\trading_hub_android" 2>nul

    echo Copying source files (this may take a minute)...
    xcopy "%~dp0android_app\www" "C:\temp\trading_hub_android\www\" /E /I /Y /Q >nul
    xcopy "%~dp0android_app\android\app\src" "C:\temp\trading_hub_android\android\app\src\" /E /I /Y /Q >nul
    xcopy "%~dp0android_app\android\gradle" "C:\temp\trading_hub_android\android\gradle\" /E /I /Y /Q >nul
    copy "%~dp0android_app\android\build.gradle" "C:\temp\trading_hub_android\android\" /Y >nul
    copy "%~dp0android_app\android\gradle.properties" "C:\temp\trading_hub_android\android\" /Y >nul
    copy "%~dp0android_app\android\gradlew.bat" "C:\temp\trading_hub_android\android\" /Y >nul
    copy "%~dp0android_app\android\gradlew" "C:\temp\trading_hub_android\android\" /Y >nul
    copy "%~dp0android_app\android\settings.gradle" "C:\temp\trading_hub_android\android\" /Y >nul
    copy "%~dp0android_app\android\local.properties" "C:\temp\trading_hub_android\android\" /Y >nul
    copy "%~dp0android_app\capacitor.config.json" "C:\temp\trading_hub_android\" /Y >nul
    copy "%~dp0android_app\package.json" "C:\temp\trading_hub_android\" /Y >nul

    echo Done! Project copied to C:\temp\trading_hub_android\
    echo.
) else (
    echo [1/4] Project already in local folder (C:\temp\trading_hub_android\)
    echo.
)

REM Step 2: Check Java 21
echo [2/4] Checking Java version...
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.5.11-hotspot

if not exist "%JAVA_HOME%\bin\java.exe" (
    echo Java 21 not found!
    echo.
    echo Installing Java 21 via winget...
    winget install EclipseAdoptium.Temurin.21.JDK --accept-source-agreements --accept-package-agreements

    echo.
    echo Java 21 installed! Please close this window and run BUILD_APK_FIXED.bat again.
    pause
    exit /b 1
)

"%JAVA_HOME%\bin\java.exe" -version
echo Java 21 found!
echo.

REM Step 3: Clean any previous build artifacts
echo [3/4] Cleaning previous build...
cd /d "C:\temp\trading_hub_android\android"
if exist ".gradle" rd /s /q ".gradle" 2>nul
if exist "app\build" rd /s /q "app\build" 2>nul
echo Done!
echo.

REM Step 4: Build APK
echo [4/4] Building APK (this takes 2-3 minutes)...
echo.

call gradlew.bat assembleDebug

if errorlevel 1 (
    echo.
    echo ========================================
    echo   BUILD FAILED!
    echo ========================================
    echo.
    echo Check the error messages above.
    echo Common issues:
    echo - Android SDK not found (install Android Studio)
    echo - Java version mismatch (needs Java 21)
    echo - OneDrive file locking (project now in C:\temp)
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! APK Built!
echo ========================================
echo.
echo APK Location:
echo C:\temp\trading_hub_android\android\app\build\outputs\apk\debug\app-debug.apk
echo.
echo File size:
for %%A in ("C:\temp\trading_hub_android\android\app\build\outputs\apk\debug\app-debug.apk") do echo %%~zA bytes (%%~zK KB)
echo.
echo Next Steps:
echo 1. Copy app-debug.apk to your Android phone
echo 2. Enable "Install from Unknown Sources" in Settings
echo 3. Tap the APK file to install
echo 4. Open the app and enter your server URL
echo.
echo Server URL (local): http://192.168.0.128:8501
echo.
pause

REM Optionally copy APK back to original location
echo.
echo Copy APK back to original project folder? (Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    copy "C:\temp\trading_hub_android\android\app\build\outputs\apk\debug\app-debug.apk" "%~dp0app-debug.apk" /Y
    echo Copied to: %~dp0app-debug.apk
    echo.
)

echo All done!
pause
