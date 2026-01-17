@echo off
echo.
echo ================================================================================
echo PROJECT CLEANUP UTILITY
echo ================================================================================
echo.
echo This will remove all temporary and cache files from your project:
echo   - Python cache files (__pycache__, *.pyc)
echo   - SQLite temporary files (*.db-shm, *.db-wal)
echo   - Test cache directories (.pytest_cache, .mypy_cache)
echo   - Temporary files (*.tmp, *.log, *.bak)
echo   - Backup files (*~)
echo.
echo WARNING: This will NOT delete your actual data files (gold.db, trades.db, etc)
echo.
pause

echo.
echo [1/6] Deleting Python cache directories...
powershell -Command "Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
echo Done.

echo [2/6] Deleting .pyc files...
powershell -Command "Get-ChildItem -Path . -Filter *.pyc -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue"
echo Done.

echo [3/6] Deleting test cache directories...
powershell -Command "Get-ChildItem -Path . -Include .pytest_cache,.mypy_cache,.coverage -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
echo Done.

echo [4/6] Deleting SQLite temporary files...
del /s *.db-shm *.db-wal 2>nul
echo Done.

echo [5/6] Deleting temporary and backup files...
del /s *.tmp *.bak *~ 2>nul
echo Done.

echo [6/6] Cleaning up log files (keeping important ones)...
:: Delete generic log files but keep specific trading logs
for %%f in (debug.log error.log temp.log test.log) do (
    if exist %%f del %%f 2>nul
)
echo Done.

echo.
echo ================================================================================
echo CLEANUP COMPLETE
echo ================================================================================
echo.
echo Your project folder is now clean!
echo.
echo Kept (important files):
echo   - gold.db (main data)
echo   - trades.db (trade journal)
echo   - trading_app/live_data.db (live market data)
echo   - trading_app/trading_app.db (AI memory)
echo   - dbn/ folder (historical data)
echo   - _archive/ folder (archived files)
echo.
pause
