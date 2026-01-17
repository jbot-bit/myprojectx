@echo off
REM ============================================================================
REM Mobile App Connection Diagnostics
REM ============================================================================

echo.
echo ========================================
echo   MOBILE APP CONNECTION DIAGNOSTICS
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    goto :error
)
echo ✓ Python OK
echo.

echo [2/5] Checking Streamlit installation...
python -c "import streamlit; print(f'Streamlit {streamlit.__version__}')"
if errorlevel 1 (
    echo ERROR: Streamlit not installed!
    echo Run: pip install -r trading_app/requirements.txt
    goto :error
)
echo ✓ Streamlit OK
echo.

echo [3/5] Finding your PC's IP addresses...
echo.
ipconfig | findstr /C:"IPv4"
echo.
echo ✓ Use one of these IPs in your phone APK
echo.

echo [4/5] Checking if port 8501 is available...
netstat -ano | findstr ":8501"
if errorlevel 1 (
    echo ✓ Port 8501 is FREE (good!)
) else (
    echo ⚠ Port 8501 is IN USE (Streamlit might already be running)
)
echo.

echo [5/5] Checking firewall rule...
netsh advfirewall firewall show rule name="Streamlit" >nul 2>&1
if errorlevel 1 (
    echo ⚠ No firewall rule found for Streamlit
    echo.
    echo Do you want to add a firewall rule? (requires admin)
    echo This will allow port 8501 through Windows Firewall.
    echo.
    choice /C YN /M "Add firewall rule"
    if errorlevel 2 goto :skip_firewall
    if errorlevel 1 goto :add_firewall
    :add_firewall
    netsh advfirewall firewall add rule name="Streamlit" dir=in action=allow protocol=TCP localport=8501
    if errorlevel 1 (
        echo ERROR: Failed to add firewall rule (need admin rights)
        echo Right-click this file and "Run as Administrator"
    ) else (
        echo ✓ Firewall rule added!
    )
    :skip_firewall
) else (
    echo ✓ Firewall rule exists
)
echo.

echo ========================================
echo   DIAGNOSIS COMPLETE
echo ========================================
echo.
echo NEXT STEPS:
echo.
echo 1. Run: START_MOBILE_APP.bat
echo    (This starts Streamlit on http://0.0.0.0:8501)
echo.
echo 2. Open browser on PC and test: http://localhost:8501
echo    (Make sure it works on PC first!)
echo.
echo 3. On your phone:
echo    - Make sure phone is on SAME Wi-Fi as PC
echo    - Open the APK
echo    - Enter: http://YOUR_IP_FROM_ABOVE:8501
echo    - Example: http://192.168.0.128:8501
echo.
echo 4. If it still doesn't work:
echo    - Check PC firewall allows port 8501
echo    - Check router doesn't block local connections
echo    - Try different IP address if you have multiple
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo   DIAGNOSTIC FAILED
echo ========================================
echo.
echo Fix the errors above and try again.
echo.
pause
exit /b 1
