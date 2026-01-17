@echo off
REM ============================================================================
REM ADD CASCADE AND SINGLE_LIQUIDITY STRATEGIES TO DATABASE
REM ============================================================================

echo.
echo ========================================
echo   ADDING CONTEXTUAL STRATEGIES
echo ========================================
echo.
echo This will add to your database:
echo   - CASCADE strategy (S+ tier, +1.95R avg)
echo   - SINGLE_LIQUIDITY strategy (S tier, +1.44R avg)
echo.

cd /d "%~dp0"

REM Kill any existing Streamlit instances
echo Closing any running apps...
taskkill /F /IM streamlit.exe >nul 2>&1
timeout /t 2 >nul

REM Add strategies to database
echo.
echo Running script...
python add_contextual_strategies.py

echo.
echo ========================================
echo   COMPLETE
echo ========================================
echo.
echo Your AI will now know about ALL strategies:
echo   - CASCADE (S+): 19%% WR, +1.95R, ~35 trades/year
echo   - SINGLE_LIQUIDITY (S): 33.7%% WR, +1.44R, ~59 trades/year
echo   - 6 baseline ORB setups
echo.
echo Total system: ~450-600R/year
echo.
pause
