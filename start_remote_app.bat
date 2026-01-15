@echo off
REM Quick script to start Streamlit app with remote access

echo ========================================
echo STARTING STREAMLIT APP WITH REMOTE ACCESS
echo ========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok is not installed!
    echo.
    echo Please install ngrok:
    echo 1. Download from: https://ngrok.com/download
    echo 2. Or run: winget install ngrok
    echo.
    pause
    exit /b 1
)

echo Starting Streamlit app on port 8501...
echo.

REM Start Streamlit in background
start /B streamlit run app_trading_hub.py --server.port 8501 --server.headless true

REM Wait for Streamlit to start
timeout /t 5 /nobreak

echo.
echo Starting ngrok tunnel...
echo.

REM Start ngrok
echo ========================================
echo COPY THE HTTPS URL BELOW TO ACCESS ON YOUR PHONE:
echo ========================================
echo.

ngrok http 8501
