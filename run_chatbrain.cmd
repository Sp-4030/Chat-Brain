@echo off
title ChatBrain
cd /d "%~dp0"

if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
    ) else (
        set "PYTHON_CMD=python"
    )
)

echo ========================================
echo          CHATBRAIN STARTING
echo ========================================
echo.

echo Starting YouTube ChatBrain...
start "ChatBrain Service" /D "%~dp0" cmd /k ""%PYTHON_CMD%" main.py"

timeout /t 4 /nobreak >nul

echo Starting Streamlit Dashboard...
start "ChatBrain Dashboard" /D "%~dp0" cmd /k ""%PYTHON_CMD%" -m streamlit run app.py"

echo.
echo ========================================
echo          CHATBRAIN STARTED
echo ========================================
echo.
pause