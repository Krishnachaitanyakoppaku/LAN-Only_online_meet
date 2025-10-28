#!/bin/bash
echo "🔗 Setting up SSH tunnel for LAN Communication Hub"
echo "Server IP: 172.17.253.127"
echo ""
read -p "Enter username for 172.17.253.127 (default: chaitu): " username
username=${username:-chaitu}
echo ""
echo "This will create a tunnel so you can access the server via localhost"
echo "Keep this terminal open while using the application"
echo ""
ssh -L 5000:172.17.253.127:5000 $username@172.17.253.127
