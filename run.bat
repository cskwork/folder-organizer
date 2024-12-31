@echo off
chcp 65001 > nul
setlocal

:: Check and create virtual environment if not exists
if not exist venv (
    echo Creating virtual environment...
    py -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
venv\Scripts\activate

:: Install required packages
echo Installing required packages...
REM Install others
pip install -r requirements.txt

:: Run main program
echo Running the program...
py main.py

:: Deactivate virtual environment
:: deactivate

endlocal
