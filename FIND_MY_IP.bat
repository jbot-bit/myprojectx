@echo off
REM ============================================================================
REM Find Your PC's IP Address (NOT the router!)
REM ============================================================================

echo.
echo ========================================
echo   FINDING YOUR PC'S IP ADDRESS
echo ========================================
echo.
echo Looking for your PC's IP (NOT router 192.168.0.1)...
echo.

REM Get all IPv4 addresses that are NOT 127.0.0.1 (localhost)
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    set ip=%%a
    setlocal enabledelayedexpansion
    set ip=!ip: =!
    echo Found IP: !ip!

    REM Check if it's not localhost
    echo !ip! | findstr /C:"127.0.0.1" >nul
    if errorlevel 1 (
        echo.
        echo ========================================
        echo   YOUR PC IP ADDRESS:
        echo   !ip!
        echo ========================================
        echo.
        echo USE THIS IN YOUR PHONE APK:
        echo   http://!ip!:8501
        echo.
        echo Copy this URL and paste it in your Android app!
        echo.
    )
    endlocal
)

echo.
echo If you see multiple IPs above, try each one.
echo Usually it's the one starting with 192.168.X.X or 10.0.X.X
echo.
echo REMEMBER: 192.168.0.1 is your ROUTER, not your PC!
echo.
pause
