@echo off
REM Master Audit System - Complete Validation Suite
REM Runs all tests from STEPONE through STEPTHREE

echo.
echo ========================================
echo MASTER AUDIT SYSTEM
echo Trading System Validation Framework
echo ========================================
echo.

REM Check if gold.db exists
if not exist gold.db (
    echo ERROR: gold.db not found!
    echo.
    echo Make sure you run this from the project directory.
    echo.
    pause
    exit /b 1
)

echo Running complete audit suite...
echo This includes:
echo   - Step 1: Data Integrity
echo   - Step 2: Feature Verification
echo.

python audit_master.py

echo.
echo ========================================
echo Audit complete!
echo.
echo Check audit_reports/ folder for detailed results:
echo   - master_audit_report.json
echo   - audit_summary.csv
echo   - step1_data_integrity_report.json
echo   - step2_feature_verification_report.json
echo ========================================
echo.

pause
