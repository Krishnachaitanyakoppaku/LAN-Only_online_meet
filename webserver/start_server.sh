#!/bin/bash

echo "LAN Communication Hub - Linux/macOS Startup Script"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found. Starting server..."
echo ""

# Start the server
python3 start_server.py
