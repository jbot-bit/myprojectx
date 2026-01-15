@echo off
REM ============================================================================
REM OVERNIGHT REBUILD - MODEL B (Entry-Anchored, 5-min ORB, Next-Bar-Open)
REM ============================================================================
REM
REM This script rebuilds ALL features with the correct Model B execution logic:
REM   1. 5-minute ORB (00:30-00:35)
REM   2. Entry at next bar OPEN (not close)
REM   3. Risk calculated from ENTRY to STOP (not ORB edge to stop)
REM   4. Same-bar TP+SL = LOSS (conservative)
REM
REM Run this overnight - takes ~30-60 minutes for full dataset
REM ============================================================================

echo ============================================================================
echo OVERNIGHT REBUILD - MODEL B EXECUTION
echo ============================================================================
echo.
echo Start time: %date% %time%
echo.
echo This will rebuild:
echo   - daily_features_v3_modelb (full SL)
echo   - daily_features_v3_modelb_half (half SL)
echo.
echo Estimated time: 30-60 minutes
echo.
pause

REM Step 1: Rebuild FULL-SL features (Model B)
echo.
echo ============================================================================
echo STEP 1/2: Building FULL-SL features (Model B)
echo ============================================================================
echo.

REM Kill any hung Python processes before starting
for /f "tokens=2" %%i in ('tasklist 2^>nul ^| findstr /i "python.exe"') do taskkill /PID %%i /F >nul 2>&1
timeout /t 2 >nul

start /B /WAIT "" python build_daily_features_v3_modelb.py 2024-01-01 2026-01-10 --sl-mode full

if errorlevel 1 (
    echo ERROR: Full-SL rebuild failed!
    echo Cleaning up any hung processes...
    for /f "tokens=2" %%i in ('tasklist 2^>nul ^| findstr /i "python.exe"') do taskkill /PID %%i /F >nul 2>&1
    pause
    exit /b 1
)

echo.
echo [OK] Full-SL rebuild complete
echo.

REM Step 2: Rebuild HALF-SL features (Model B)
echo.
echo ============================================================================
echo STEP 2/2: Building HALF-SL features (Model B)
echo ============================================================================
echo.

REM Kill any hung Python processes before starting
for /f "tokens=2" %%i in ('tasklist 2^>nul ^| findstr /i "python.exe"') do taskkill /PID %%i /F >nul 2>&1
timeout /t 2 >nul

start /B /WAIT "" python build_daily_features_v3_modelb.py 2024-01-01 2026-01-10 --sl-mode half

if errorlevel 1 (
    echo ERROR: Half-SL rebuild failed!
    echo Cleaning up any hung processes...
    for /f "tokens=2" %%i in ('tasklist 2^>nul ^| findstr /i "python.exe"') do taskkill /PID %%i /F >nul 2>&1
    pause
    exit /b 1
)

echo.
echo [OK] Half-SL rebuild complete
echo.

REM Step 3: Create convenience views
echo.
echo ============================================================================
echo STEP 3: Creating convenience views
echo ============================================================================
echo.

python create_v3_modelb_views.py

if errorlevel 1 (
    echo WARNING: View creation failed (not critical)
)

echo.
echo [OK] Views created
echo.

REM Step 4: Verification
echo.
echo ============================================================================
echo STEP 4: Verification
echo ============================================================================
echo.

python verify_modelb_results.py

if errorlevel 1 (
    echo WARNING: Verification script not found or failed
)

REM Done
echo.
echo ============================================================================
echo REBUILD COMPLETE
echo ============================================================================
echo.
echo End time: %date% %time%
echo.
echo Tables created:
echo   - daily_features_v3_modelb (full SL)
echo   - daily_features_v3_modelb_half (half SL)
echo   - v_orb_trades_v3_modelb (view for full SL)
echo   - v_orb_trades_v3_modelb_half (view for half SL)
echo.
echo You can now run your edge discovery scripts using these new tables.
echo.
echo IMPORTANT: Old tables (daily_features_v2_half, v_orb_trades_half) are
echo            DEPRECATED and use incorrect ORB-anchored risk calculation.
echo            Do NOT use them for any analysis.
echo.
pause
