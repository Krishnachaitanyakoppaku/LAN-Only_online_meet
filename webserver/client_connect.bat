@echo off
echo 🔗 Setting up SSH tunnel for LAN Communication Hub
echo Server IP: 172.17.253.127
echo.
set /p username="Enter username for 172.17.253.127 (default: chaitu): "
if "%username%"=="" set username=chaitu
echo.
echo This will create a tunnel so you can access the server via localhost
echo Keep this window open while using the application
echo.
ssh -L 5000:172.17.253.127:5000 %username%@172.17.253.127
