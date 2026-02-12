@echo off
setlocal enabledelayedexpansion

REM ===== MovieFactory one-click regression check (CI-identical) =====
cd /d "%~dp0"

set "YAML=moviefactory\eval\text_queries_intent.yaml"

echo.
echo [RUN] python -m moviefactory.eval.regression_check %YAML%
echo.

python -m moviefactory.eval.regression_check "%YAML%"
set "EC=%ERRORLEVEL%"

echo.
if "%EC%"=="0" (
  echo ✅ PASS (no regression)
) else (
  echo ❌ FAIL (regression detected or error)  (exitcode=%EC%)
)

echo.
pause
exit /b %EC%
