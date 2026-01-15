@echo off
echo ========================================
echo MPL OVERNIGHT ANALYSIS
echo ========================================
echo Starting at %date% %time%
echo.
echo This will run for 2-4 hours depending on data size.
echo Check mpl_overnight.log for progress.
echo.
echo Press Ctrl+C to cancel, or wait 5 seconds to start...
timeout /t 5

python OVERNIGHT_PLATINUM_COMPLETE.py

echo.
echo ========================================
echo COMPLETE
echo ========================================
echo.
echo Results:
echo - MPL_OVERNIGHT_RESULTS.md (full report)
echo - MPL_TRADING_PLAN.md (quick reference)
echo - mpl_overnight.log (execution log)
echo.
echo Finished at %date% %time%
pause
