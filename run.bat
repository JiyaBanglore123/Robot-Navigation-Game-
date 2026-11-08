@echo off
REM ==============================================================================
REM Robot Navigation Game — Windows Startup Batch Script
REM Author: Ankur (Person 2)
REM ==============================================================================

setlocal enabledelayedexpansion

REM 1. Detect and navigate to project root directory
cd /d "%~dp0"

echo ==========================================================
echo  Starting DFA-Based Robot Navigation Game (FLA Project)
echo  Working directory: %CD%
echo ==========================================================

REM 2. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.10+ and ensure "Add Python to PATH" is checked.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [1/5] Detected Python: !PYTHON_VER!

REM 3. Check or create virtual environment
if not exist ".venv" (
    echo [2/5] Creating Python virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [2/5] Existing virtual environment found in .venv.
)

REM 4. Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Cannot find .venv\Scripts\activate.bat.
    pause
    exit /b 1
)

REM 5. Upgrade pip
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM 6. Install dependencies
echo [4/5] Checking and installing requirements from requirements.txt...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install required packages.
    pause
    exit /b 1
)

REM 7. Configure Host & Port
if "%HOST%"=="" set HOST=127.0.0.1
if "%PORT%"=="" set PORT=5000

echo [5/5] Launching Flask Server...
echo ==========================================================
echo  Application running at: http://%HOST%:%PORT%
echo  Press Ctrl+C to stop the application server.
echo ==========================================================

python -m flask --app app run --host %HOST% --port %PORT%

if %errorlevel% neq 0 (
    echo [ERROR] Server exited with an error.
    pause
)
