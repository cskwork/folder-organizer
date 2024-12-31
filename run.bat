@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo ===================================
echo Intelligent File Organizer Setup
echo ===================================

:: Check Python installation
@REM python --version > nul 2>&1
@REM if errorlevel 1 (
@REM     echo Error: Python is not installed or not in PATH
@REM     echo Please install Python 3.10 or higher from https://www.python.org/
@REM     pause
@REM     exit /b 1
@REM )

@REM :: Check Python version
@REM for /f "tokens=2 delims=." %%I in ('python -c "import sys; print(sys.version.split('.')[0])"') do set PYTHON_VERSION=%%I
@REM if %PYTHON_VERSION% LSS 10 (
@REM     echo Error: Python version 3.10 or higher is required
@REM     echo Current version: 3.%PYTHON_VERSION%
@REM     pause
@REM     exit /b 1
@REM )

:: Check and create virtual environment if not exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install required packages
echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install required packages
    pause
    exit /b 1
)

:: Check Ollama installation
echo Checking Ollama installation...
curl -s http://localhost:11434/api/version > nul
if errorlevel 1 (
    echo Warning: Ollama is not running or not installed
    echo Please install Ollama from https://ollama.ai/
    echo and ensure it is running before using content analysis
    timeout /t 5
)

:: Run main program
echo ===================================
echo Starting the program...
echo ===================================
python main.py

:: Check if program exited with error
if errorlevel 1 (
    echo Program exited with error code %errorlevel%
    pause
)

:: Deactivate virtual environment
call venv\Scripts\deactivate

endlocal
