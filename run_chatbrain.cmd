@echo off
title ChatBrain

cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

echo ========================================
echo          CHATBRAIN STARTING
echo ========================================
echo.

echo Starting YouTube ChatBrain...
start "" /D "%~dp0" cmd /k "%PYTHON_CMD% youtube.py"

timeout /t 5 /nobreak >nul

echo Starting Streamlit Dashboard...
start "" /D "%~dp0" cmd /k "%PYTHON_CMD% -m streamlit run app.py"

echo.
echo ========================================
echo          CHATBRAIN STARTED
echo ========================================
echo.
pause