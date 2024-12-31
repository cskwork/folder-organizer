@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ===================================
echo Intelligent File Organizer Setup
echo ===================================

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed. Please install Python 3.8 or later.
    pause
    exit /b 1
)

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
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install/upgrade pip
python -m pip install --upgrade pip

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
