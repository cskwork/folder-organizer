@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo Installing/Updating dependencies...
python -m pip install -r requirements.txt

:: Run the application
echo Starting application...
python src/main.py

:: Deactivate virtual environment
deactivate

:: Check Ollama installation
echo Checking Ollama installation...
curl -s http://localhost:11434/api/version > nul
if errorlevel 1 (
    echo Warning: Ollama is not running or not installed
    echo Please install Ollama from https://ollama.ai/
    echo and ensure it is running before using content analysis
    timeout /t 5
)

:: Check if program exited with error
if errorlevel 1 (
    echo Program exited with error code %errorlevel%
    pause
)

endlocal
