@echo off
echo.
echo ================================================================================
echo COMPLETE DATA ACCURACY AND CALCULATION AUDIT
echo ================================================================================
echo.
echo This will verify all calculations and data integrity in your trading system.
echo.
echo Press any key to start the audit...
pause >nul
echo.

python audit_complete_accuracy.py

echo.
echo.
echo Audit complete! Review results above.
echo.
pause
