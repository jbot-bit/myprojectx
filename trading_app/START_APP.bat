@echo off
echo ================================================
echo   TRADING HUB - STARTING APP
echo ================================================
echo.
echo Opening app on http://localhost:8504
echo.
echo Press CTRL+C to stop the app
echo.

cd /d "%~dp0"
streamlit run app_trading_hub.py --server.port=8504

pause
