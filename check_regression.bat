@echo off
setlocal

cd /d "%~dp0"

echo.
echo ====================================================
echo   MovieFactory Search Regression Check
echo ====================================================
echo.

python -m moviefactory.eval.regression_check moviefactory\eval\text_queries_intent.yaml
set ERR=%ERRORLEVEL%

echo.
if NOT "%ERR%"=="0" (
    echo ####################################################
    echo  ❌ REGRESSION FOUND
    echo  Check: moviefactory\eval\eval_reports\latest.json
    echo ####################################################
) else (
    echo ####################################################
    echo  ✅ PASS - NO REGRESSION
    echo ####################################################
)

echo.
pause
exit /b %ERR%
