@echo off
title ChatBrain Launcher
cd /d "%~dp0"

echo ========================================
echo        CHATBRAIN WINDOWS LAUNCHER
echo ========================================
echo.

:: Check for virtual environment first
if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
    echo Using virtual environment: venv
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    echo Using virtual environment: .venv
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
        echo Using system Python (py launcher)
    ) else (
        where python >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_CMD=python"
            echo Using system Python
        ) else (
            echo [ERROR] Python was not found on your system!
            echo Please install Python 3.10+ or set up a virtual environment.
            echo.
            pause
            exit /b 1
        )
    )
)

echo.
echo Starting ChatBrain Engine (main.py)...
start "ChatBrain Engine" /D "%~dp0" cmd /k ""%PYTHON_CMD%" main.py"

timeout /t 3 /nobreak >nul

echo Starting Streamlit Dashboard...
start "ChatBrain Dashboard" /D "%~dp0" cmd /k ""%PYTHON_CMD%" -m streamlit run app.py"

echo.
echo ========================================
echo         CHATBRAIN IS RUNNING
echo ========================================
echo ChatBrain engine and dashboard opened in separate windows.
echo Close those windows or press Ctrl+C to stop.
echo.
pause
