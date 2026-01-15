@echo off
echo ============================================
echo STARTING APP FOR LOCAL NETWORK ACCESS
echo ============================================
echo.
echo This will work if your phone is on the SAME WiFi
echo.

REM Kill existing
taskkill /F /IM streamlit.exe >nul 2>nul

echo Starting app...
echo.
echo ============================================
echo COPY THE "Network URL" SHOWN BELOW
echo OPEN IT ON YOUR PHONE (must be same WiFi)
echo ============================================
echo.

streamlit run app_trading_hub.py --server.address 0.0.0.0 --server.port 8501
