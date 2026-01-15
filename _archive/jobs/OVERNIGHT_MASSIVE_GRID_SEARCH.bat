@echo off
REM ============================================================================
REM MASSIVE OVERNIGHT GRID SEARCH (6-12 HOURS)
REM ============================================================================
REM
REM This tests HUNDREDS of execution variants:
REM   - ORB sizes: 5min, 10min, 15min
REM   - Entry methods: close, next-open, 2-bar-confirm
REM   - Buffers: 0, 0.5 ticks
REM   - Stops: full-SL, half-SL, 75pct-SL
REM   - Confirmations: 1-bar, 2-bar
REM   - R:R: 1.0, 1.5, 2.0
REM
REM Total: 3 x 3 x 2 x 3 x 2 x 3 = 324 CONFIGURATIONS
REM On 740 days = 239,760 backtest runs!
REM
REM Then analyzes ALL configs for ALL 6 sessions and finds best ones.
REM
REM WARNING: THIS WILL RUN FOR 6-12 HOURS
REM ============================================================================

echo ============================================================================
echo MASSIVE OVERNIGHT GRID SEARCH
echo ============================================================================
echo.
echo This will run for 6-12 HOURS and test 324 execution configurations:
echo   - 3 ORB sizes (5min, 10min, 15min)
echo   - 3 entry methods (close, next-open, 2-bar-confirm)
echo   - 2 buffer options (0, 0.5 ticks)
echo   - 3 stop modes (full-SL, half-SL, 75pct-SL)
echo   - 2 confirmation requirements (1-bar, 2-bar)
echo   - 3 R:R ratios (1.0, 1.5, 2.0)
echo.
echo Total: 324 configs x 740 days = 239,760 backtest runs
echo.
echo Start time: %date% %time%
echo.
echo Press CTRL+C now to cancel, or press any key to start...
pause

REM ============================================================================
REM PHASE 1: BUILD EXECUTION GRID (4-8 HOURS)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 1: BUILDING EXECUTION GRID (This takes 4-8 hours)
echo ============================================================================
echo.
echo Testing all 324 execution configurations on every date...
echo Progress shown every 10 days.
echo.

REM Build with automatic retry (resumes from checkpoint if interrupted)
set RETRY_COUNT=0
set MAX_RETRIES=5

:BUILD_RETRY
set /a RETRY_COUNT+=1

if %RETRY_COUNT% GTR %MAX_RETRIES% (
    echo ERROR: Maximum retries ^(%MAX_RETRIES%^) reached. Build failed.
    echo Check results_grid_build.txt for errors.
    pause
    exit /b 1
)

if %RETRY_COUNT% GTR 1 (
    echo.
    echo [RETRY %RETRY_COUNT%/%MAX_RETRIES%] Checking for hung processes...
    REM Kill any hung Python processes that might be holding DB lock
    for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do (
        echo Terminating potential hung process: %%i
        taskkill /PID %%i /F >nul 2>&1
    )
    timeout /t 3
    echo Retrying build...
    echo.
)

REM Start Python with explicit error logging
echo [%date% %time%] Starting build ^(attempt %RETRY_COUNT%/%MAX_RETRIES%^)... >> results_grid_build.txt
start /B /WAIT "" python build_execution_grid_features.py 2024-01-01 2026-01-10 >> results_grid_build.txt 2>&1

REM Check if process completed successfully
if errorlevel 1 (
    echo [%date% %time%] Build attempt %RETRY_COUNT% failed with error level %ERRORLEVEL% >> results_grid_build.txt
    echo WARNING: Build process encountered error ^(attempt %RETRY_COUNT%/%MAX_RETRIES%^)
    echo Waiting 10 seconds before retry...
    timeout /t 10
    goto BUILD_RETRY
)

REM Verify tables were created successfully
python -c "import duckdb; con = duckdb.connect('gold.db', read_only=True); cnt = con.execute('SELECT COUNT(*) FROM execution_grid_results').fetchone()[0]; print(f'Results count: {cnt}'); exit(0 if cnt > 0 else 1)" 2>nul
if errorlevel 1 (
    echo [%date% %time%] Build completed but no results found in database >> results_grid_build.txt
    echo WARNING: Build completed but no results in database. Retrying...
    timeout /t 10
    goto BUILD_RETRY
)

echo [%date% %time%] Build completed successfully >> results_grid_build.txt

echo.
echo [PHASE 1 COMPLETE] Execution grid built
echo Phase 1 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 2: ANALYZE GRID FOR ALL SESSIONS (30-60 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 2: ANALYZING ALL CONFIGS FOR ALL SESSIONS
echo ============================================================================
echo.
echo Finding best execution configurations for each session...
echo.

python analyze_execution_grid_all_sessions.py > results_grid_analysis.txt 2>&1

echo.
echo [PHASE 2 COMPLETE] Grid analysis done
echo Phase 2 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 3: STATE FILTERING ON BEST CONFIGS (30-60 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 3: STATE FILTERING ON BEST CONFIGS
echo ============================================================================
echo.
echo For each session's best configs, testing state combinations...
echo.

python combine_best_configs_with_states.py > results_best_configs_states.txt 2>&1

if errorlevel 1 (
    echo WARNING: State filtering script had errors, continuing anyway
)

echo.
echo [PHASE 3 COMPLETE] State filtering done
echo Phase 3 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 4: FINAL VALIDATED EDGES REPORT (10 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 4: GENERATING FINAL REPORT
echo ============================================================================
echo.

python generate_final_grid_report.py > FINAL_GRID_SEARCH_REPORT.txt 2>&1

echo.
echo [PHASE 4 COMPLETE] Final report generated
echo Phase 4 end time: %date% %time%
echo.

REM ============================================================================
REM COMPLETE
REM ============================================================================

echo.
echo ============================================================================
echo MASSIVE GRID SEARCH COMPLETE
echo ============================================================================
echo.
echo End time: %date% %time%
echo.
echo Results generated:
echo   - results_grid_build.txt (build log)
echo   - results_grid_analysis.txt (analysis of all configs)
echo   - results_best_configs_states.txt (state filtering on best)
echo   - FINAL_GRID_SEARCH_REPORT.txt (FINAL REPORT - READ THIS!)
echo.
echo Database tables created:
echo   - execution_grid_configs (324 configs)
echo   - execution_grid_results (239,760 backtest runs)
echo.
echo ============================================================================
echo NEXT STEPS:
echo ============================================================================
echo.
echo 1. Read FINAL_GRID_SEARCH_REPORT.txt for best execution configs
echo 2. Review results_grid_analysis.txt for detailed breakdown
echo 3. Compare different ORB sizes, entry methods, stop placements
echo 4. Deploy best validated configs (if any found)
echo.
echo This tested EVERYTHING - if no edges found, there are no edges.
echo.
echo ============================================================================
echo.
pause
