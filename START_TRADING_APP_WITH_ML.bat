@echo off
echo ======================================
echo Starting Trading App with ML System
echo ======================================
echo.

cd /d "%~dp0trading_app"

echo Checking Python environment...
python --version
echo.

echo Starting Streamlit app...
echo App will open in browser at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the app
echo ======================================
echo.

streamlit run app_trading_hub.py

pause
