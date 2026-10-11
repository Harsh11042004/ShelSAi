@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ShelSAi's virtual environment was not found.
    echo Follow the setup instructions in README.md first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "main.py"
if errorlevel 1 (
    echo ShelSAi stopped because an error occurred.
    pause
    exit /b 1
)