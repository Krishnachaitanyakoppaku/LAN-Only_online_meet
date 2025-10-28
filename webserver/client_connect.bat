@echo off
echo 🔗 LAN Communication Hub - Client Connection
echo.
python connect_client.py
if errorlevel 1 (
    echo.
    echo ❌ Python connection failed
    echo 💡 Make sure Python is installed and try again
)
pause
