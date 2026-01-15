@echo off
cls
echo ============================================
echo PHONE ACCESS - 2 SIMPLE STEPS
echo ============================================
echo.

REM Kill existing processes
taskkill /F /IM streamlit.exe 2>nul
taskkill /F /IM ngrok.exe 2>nul

echo Step 1: Starting Streamlit app with virtual environment...
echo (A browser window will open - you can close it)
echo.

REM Activate venv and start Streamlit
start "Streamlit" cmd /c "cd /d C:\Users\sydne\OneDrive\myprojectx && .venv\Scripts\activate && streamlit run app_trading_hub.py --server.port 8501"

echo Waiting 10 seconds for app to fully start...
timeout /t 10 /nobreak

cls
echo ============================================
echo Step 2: Starting ngrok tunnel...
echo ============================================
echo.
echo COPY THE HTTPS URL BELOW AND OPEN ON YOUR PHONE:
echo.
echo ============================================
echo.

C:\Users\sydne\AppData\Local\Microsoft\WinGet\Links\ngrok.exe http 8501
