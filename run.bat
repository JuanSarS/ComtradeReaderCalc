@echo off
REM COMTRADE Analysis Tool - Windows Launcher
REM ============================================
REM This batch file launches the COMTRADE Analysis Tool

echo Starting COMTRADE Analysis Tool...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Launch the application
echo Launching application...
python src\main.py

pause
