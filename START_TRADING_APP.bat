@echo off
REM ============================================================================
REM TRADING APP LAUNCHER
REM Source of Truth: trading_app/app_trading_hub.py
REM ============================================================================

echo.
echo ========================================
echo   STARTING TRADING APP
echo ========================================
echo.
echo Source: trading_app/app_trading_hub.py (DESKTOP UI)
echo URL: http://localhost:8501
echo.

cd /d "%~dp0"

REM Kill any existing Streamlit instances
taskkill /F /IM streamlit.exe >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq streamlit*" >nul 2>&1
timeout /t 2 >nul 2>&1

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Launch the DESKTOP trading hub
echo Starting Trading Hub (Desktop version with sidebar)...
python -m streamlit run trading_app\app_trading_hub.py

pause
