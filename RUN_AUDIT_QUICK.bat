@echo off
REM Quick Audit - Critical Tests Only
REM Fast validation of essential data integrity

echo ========================================
echo QUICK AUDIT MODE
echo Critical Tests Only (Fast)
echo ========================================
echo.

python audit_master.py --quick

echo.
pause
