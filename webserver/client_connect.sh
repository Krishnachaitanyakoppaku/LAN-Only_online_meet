#!/bin/bash
echo "🔗 LAN Communication Hub - Client Connection"
echo ""
python3 connect_client.py || python connect_client.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Python connection failed"
    echo "💡 Make sure Python is installed and try again"
fi
