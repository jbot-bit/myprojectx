@echo off
REM ============================================================================
REM CLEANUP FROZEN JOBS
REM ============================================================================
REM Use this script if a batch job freezes and you need to clean up
REM ============================================================================

echo ============================================================================
echo CLEANUP FROZEN JOBS
echo ============================================================================
echo.
echo This will:
echo   1. Kill all Python processes
echo   2. Wait for database locks to release
echo   3. Optionally wipe partial execution_grid tables
echo.
echo Press CTRL+C to cancel, or any key to continue...
pause >nul

echo.
echo [1/3] Killing all Python processes...
for /f "tokens=2" %%i in ('tasklist 2^>nul ^| findstr /i "python.exe"') do (
    echo   Terminating PID %%i
    taskkill /PID %%i /F >nul 2>&1
)
echo Done.

echo.
echo [2/3] Waiting for database locks to release...
timeout /t 3
echo Done.

echo.
echo [3/3] Do you want to wipe partial execution_grid tables?
echo This will DELETE execution_grid_configs and execution_grid_results tables.
echo.
choice /C YN /M "Wipe execution_grid tables"

if errorlevel 2 (
    echo Skipping table cleanup.
    goto END
)

echo Dropping execution_grid tables...
python -c "import duckdb; con = duckdb.connect('gold.db'); con.execute('DROP TABLE IF EXISTS execution_grid_results'); con.execute('DROP TABLE IF EXISTS execution_grid_configs'); print('Tables dropped successfully'); con.commit(); con.close()"

if errorlevel 1 (
    echo WARNING: Failed to drop tables. Database might still be locked.
    echo Try running this script again in a few seconds.
) else (
    echo Tables dropped successfully.
)

:END
echo.
echo ============================================================================
echo CLEANUP COMPLETE
echo ============================================================================
echo.
echo You can now restart your overnight job.
echo.
pause
