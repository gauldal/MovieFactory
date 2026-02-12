@echo off
setlocal

REM ===== MovieFactory baseline updater (separate to avoid accidents) =====
cd /d "%~dp0"

set "YAML=moviefactory\eval\text_queries_intent.yaml"

echo.
echo [RUN] python -m moviefactory.eval.regression_check %YAML% --update-baseline
echo.

python -m moviefactory.eval.regression_check "%YAML%" --update-baseline
set "EC=%ERRORLEVEL%"

echo.
if "%EC%"=="0" (
  echo ✅ Baseline updated.
) else (
  echo ❌ Failed to update baseline. (exitcode=%EC%)
)

echo.
pause
exit /b %EC%
