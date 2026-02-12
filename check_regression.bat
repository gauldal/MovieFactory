@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [RUN] python -m moviefactory.eval.regression_check moviefactory\eval\text_queries_intent.yaml
python -m moviefactory.eval.regression_check moviefactory\eval\text_queries_intent.yaml
set EC=%ERRORLEVEL%

echo.
if %EC%==0 (
  echo ✅ PASS (no regression)  (exitcode=%EC%)
) else (
  echo ❌ FAIL (regression detected or error)  (exitcode=%EC%)
)

exit /b %EC%
