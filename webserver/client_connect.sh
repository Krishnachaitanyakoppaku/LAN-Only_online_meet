#!/bin/bash
echo "🔗 Setting up SSH tunnel for LAN Communication Hub"
echo "Server IP: 10.14.84.126"
echo ""
read -p "Enter username for 10.14.84.126 (default: chaitu): " username
username=${username:-chaitu}
echo ""
echo "This will create a tunnel so you can access the server via localhost"
echo "Keep this terminal open while using the application"
echo ""
ssh -L 5000:10.14.84.126:5000 $username@10.14.84.126
