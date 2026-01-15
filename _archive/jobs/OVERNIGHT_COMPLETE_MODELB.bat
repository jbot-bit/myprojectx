@echo off
REM ============================================================================
REM COMPLETE OVERNIGHT REBUILD + EDGE DISCOVERY (MODEL B)
REM ============================================================================
REM
REM This script runs HOURS of work:
REM   1. Rebuild all features with correct Model B execution (30-60 min)
REM   2. Full edge discovery for ALL 6 sessions (60-120 min)
REM   3. State-filtered analysis for each session (60-90 min)
REM   4. Comparison reports (old vs new) (10-20 min)
REM   5. Final validated edges report (10 min)
REM
REM TOTAL TIME: 3-5 hours
REM ============================================================================

echo ============================================================================
echo COMPLETE OVERNIGHT REBUILD + EDGE DISCOVERY (MODEL B)
echo ============================================================================
echo.
echo This will run for 3-5 HOURS and includes:
echo   - Feature rebuild with Model B execution (entry-anchored risk)
echo   - Full edge discovery for all 6 sessions
echo   - State-filtered analysis
echo   - Comparison with old (incorrect) results
echo   - Final validated edges report
echo.
echo Start time: %date% %time%
echo.
pause

REM ============================================================================
REM PHASE 1: REBUILD FEATURES WITH MODEL B (30-60 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 1/5: REBUILDING FEATURES WITH MODEL B EXECUTION
echo ============================================================================
echo.
echo This phase rebuilds all features with correct execution:
echo   - 5-minute ORB (00:30-00:35)
echo   - Entry at next bar OPEN
echo   - Risk from ENTRY to STOP (not ORB edge to stop)
echo.

REM Step 1.1: Full-SL
echo [1/2] Building FULL-SL features...

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

echo [OK] Full-SL rebuild complete
echo.

REM Step 1.2: Half-SL
echo [2/2] Building HALF-SL features...

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

echo [OK] Half-SL rebuild complete
echo.

REM Step 1.3: Create views
echo Creating convenience views...
python create_v3_modelb_views.py

echo.
echo [PHASE 1 COMPLETE] Features rebuilt with Model B
echo Phase 1 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 2: BASELINE ANALYSIS - ALL 6 SESSIONS (20-30 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 2/5: BASELINE ANALYSIS - ALL 6 SESSIONS
echo ============================================================================
echo.
echo Analyzing baseline performance for all ORBs with both full and half SL
echo.

python analyze_all_sessions_modelb_baseline.py > results_modelb_baseline.txt 2>&1

if errorlevel 1 (
    echo WARNING: Baseline analysis had errors, continuing anyway
)

echo [PHASE 2 COMPLETE] Baseline analysis done
echo Phase 2 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 3: STATE-FILTERED EDGE DISCOVERY (90-120 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 3/5: STATE-FILTERED EDGE DISCOVERY - ALL SESSIONS
echo ============================================================================
echo.
echo Running comprehensive state-filtered analysis for each session
echo This is the longest phase (90-120 minutes)
echo.

REM 0900 ORB
echo [1/6] Analyzing 0900 ORB (COMPREHENSIVE: baseline, states, directions, patterns, ORB size)...
python analyze_0900_modelb_comprehensive.py > results_0900_modelb_comprehensive.txt 2>&1
echo [OK] 0900 complete
echo.

REM 1000 ORB
echo [2/6] Analyzing 1000 ORB (COMPREHENSIVE)...
python analyze_1000_modelb_comprehensive.py > results_1000_modelb_comprehensive.txt 2>&1
echo [OK] 1000 complete
echo.

REM 1100 ORB
echo [3/6] Analyzing 1100 ORB (COMPREHENSIVE)...
python analyze_1100_modelb_comprehensive.py > results_1100_modelb_comprehensive.txt 2>&1
echo [OK] 1100 complete
echo.

REM 1800 ORB
echo [4/6] Analyzing 1800 ORB (COMPREHENSIVE)...
python analyze_1800_modelb_comprehensive.py > results_1800_modelb_comprehensive.txt 2>&1
echo [OK] 1800 complete
echo.

REM 2300 ORB
echo [5/6] Analyzing 2300 ORB (COMPREHENSIVE)...
python analyze_2300_modelb_comprehensive.py > results_2300_modelb_comprehensive.txt 2>&1
echo [OK] 2300 complete
echo.

REM 0030 ORB
echo [6/6] Analyzing 0030 ORB (COMPREHENSIVE)...
python analyze_0030_modelb_comprehensive.py > results_0030_modelb_comprehensive.txt 2>&1
echo [OK] 0030 complete
echo.

echo [PHASE 3 COMPLETE] State-filtered edge discovery done
echo Phase 3 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 4: OLD VS NEW COMPARISON (10-20 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 4/5: OLD VS NEW COMPARISON
echo ============================================================================
echo.
echo Comparing old (ORB-anchored) results with new (entry-anchored) results
echo to show the impact of correct risk calculation
echo.

python compare_old_vs_new_modelb.py > results_old_vs_new_comparison.txt 2>&1

if errorlevel 1 (
    echo WARNING: Comparison script had errors (old tables might not exist)
)

echo [PHASE 4 COMPLETE] Comparison done
echo Phase 4 end time: %date% %time%
echo.

REM ============================================================================
REM PHASE 5: FINAL VALIDATED EDGES REPORT (10 min)
REM ============================================================================

echo.
echo ============================================================================
echo PHASE 5/5: GENERATING FINAL VALIDATED EDGES REPORT
echo ============================================================================
echo.
echo Compiling all validated edges that meet criteria:
echo   - >=40 trades
echo   - >=+0.10R delta vs baseline
echo   - 3/3 temporal chunks positive
echo   - <50%% selectivity
echo.

python generate_final_validated_edges_modelb.py > FINAL_VALIDATED_EDGES_MODELB.txt 2>&1

echo [PHASE 5 COMPLETE] Final report generated
echo Phase 5 end time: %date% %time%
echo.

REM ============================================================================
REM VERIFICATION
REM ============================================================================

echo.
echo ============================================================================
echo VERIFICATION
echo ============================================================================
echo.

python verify_modelb_results.py > results_modelb_verification.txt 2>&1

REM ============================================================================
REM COMPLETE
REM ============================================================================

echo.
echo ============================================================================
echo OVERNIGHT JOB COMPLETE
echo ============================================================================
echo.
echo End time: %date% %time%
echo.
echo Tables created:
echo   - daily_features_v3_modelb (full SL, entry-anchored)
echo   - daily_features_v3_modelb_half (half SL, entry-anchored)
echo.
echo Results generated:
echo   - results_modelb_baseline.txt (baseline for all sessions)
echo   - results_0900_modelb_comprehensive.txt (0900 FULL ANALYSIS)
echo   - results_1000_modelb_comprehensive.txt (1000 FULL ANALYSIS)
echo   - results_1100_modelb_comprehensive.txt (1100 FULL ANALYSIS)
echo   - results_1800_modelb_comprehensive.txt (1800 FULL ANALYSIS)
echo   - results_2300_modelb_comprehensive.txt (2300 FULL ANALYSIS)
echo   - results_0030_modelb_comprehensive.txt (0030 FULL ANALYSIS)
echo   - results_old_vs_new_comparison.txt (old vs new comparison)
echo   - results_modelb_verification.txt (verification)
echo   - FINAL_VALIDATED_EDGES_MODELB.txt (FINAL REPORT - READ THIS!)
echo.
echo ============================================================================
echo NEXT STEPS:
echo ============================================================================
echo.
echo 1. Read FINAL_VALIDATED_EDGES_MODELB.txt for validated edges
echo 2. Review individual session results files
echo 3. Check results_old_vs_new_comparison.txt to see impact of correct math
echo 4. Expect worse results than before (this is GOOD - old results were fake)
echo.
echo ============================================================================
echo.
pause
