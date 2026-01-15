@echo off
cls
echo ============================================
echo GETTING YOUR PHONE URL...
echo ============================================
echo.
echo Starting ngrok tunnel...
echo.

REM Full path to ngrok
"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" http 8501
