@echo off
echo ============================================
echo URGENT: PHONE ACCESS SETUP
echo ============================================
echo.

REM Kill any existing Streamlit processes
taskkill /F /IM streamlit.exe >nul 2>nul

echo Step 1: Starting Streamlit app...
echo.

REM Start Streamlit
start "Streamlit App" streamlit run app_trading_hub.py --server.port 8501

echo Waiting 10 seconds for app to start...
timeout /t 10 /nobreak >nul

echo.
echo ============================================
echo Step 2: NOW RUN THIS COMMAND IN A NEW WINDOW:
echo ============================================
echo.
echo     ngrok http 8501
echo.
echo ============================================
echo Then copy the HTTPS URL and open on your phone!
echo ============================================
echo.
echo Press any key to continue...
pause >nul
