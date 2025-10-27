@echo off
echo LAN Communication Hub - Windows Startup Script
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found. Starting server...
echo.

REM Start the server
python start_server.py

pause
