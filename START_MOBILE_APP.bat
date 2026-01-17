@echo off
REM Trading Hub Mobile - Launcher
REM Start the mobile-optimized trading app

echo ========================================
echo   Trading Hub Mobile
echo   Card-based mobile-first interface
echo ========================================
echo.

REM Set mobile mode environment variable
set MOBILE_MODE=true

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

echo Starting mobile app on port 8501...
echo.
echo Open in browser:
echo   - Desktop: http://localhost:8501
echo   - Mobile: Find your PC IP and use http://YOUR_IP:8501
echo.
echo Use Chrome DevTools Device Mode to test mobile view
echo Press Ctrl+C to stop
echo.

cd trading_app
python -m streamlit run app_mobile.py --server.port 8501 --server.address 0.0.0.0

pause
