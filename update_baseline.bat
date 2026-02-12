@echo off
setlocal

cd /d "%~dp0"

echo ==========================================
echo  Update Baseline (INTENDED ONLY)
echo ==========================================
echo.

python -m moviefactory.eval.regression_check moviefactory\eval\text_queries_intent.yaml --update-baseline
set ERR=%ERRORLEVEL%

echo.
if NOT "%ERR%"=="0" (
  echo ❌ FAILED to update baseline (exitcode=%ERR%)
  pause
  exit /b %ERR%
) else (
  echo ✅ Baseline updated: moviefactory\eval\baseline.json
  pause
  exit /b 0
)
