@echo off
REM COMTRADE Pro - Windows Launcher
REM ============================================
REM This batch file launches the COMTRADE Pro

echo Starting COMTRADE Pro...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

set "PYTHON_EXE="

REM Prefer .venv (project standard), fallback to venv if present
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    echo No virtual environment found. Creating .venv...
    python -m venv .venv
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo Installing dependencies...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
)

REM Ensure required GUI modules are available in selected environment
"%PYTHON_EXE%" -c "from PyQt6.QtWebEngineWidgets import QWebEngineView" >nul 2>&1
if errorlevel 1 (
    echo Installing/updating dependencies in selected environment...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
)

REM Launch the application
echo Launching application...
"%PYTHON_EXE%" src\main.py

pause
