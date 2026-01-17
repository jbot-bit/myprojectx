@echo off
echo ======================================
echo Starting ML Performance Dashboard
echo ======================================
echo.

cd /d "%~dp0trading_app"

echo Dashboard will open at: http://localhost:8502
echo.
echo Press Ctrl+C to stop
echo ======================================
echo.

streamlit run ml_dashboard.py --server.port 8502

pause
