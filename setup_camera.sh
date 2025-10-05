#!/bin/bash
# Camera Setup Script for LAN Video Calling Application

echo "LAN Video Calling - Camera Setup"
echo "================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root"
    echo "   Run as a regular user and use sudo when needed"
    exit 1
fi

# Check if user is in video group
if groups | grep -q video; then
    echo "✅ User is already in video group"
else
    echo "❌ User is not in video group"
    echo "🔧 Adding user to video group..."
    sudo usermod -a -G video $USER
    if [ $? -eq 0 ]; then
        echo "✅ Successfully added user to video group"
        echo "⚠️  You need to log out and log back in for changes to take effect"
    else
        echo "❌ Failed to add user to video group"
        exit 1
    fi
fi

# Check camera devices
echo ""
echo "Checking camera devices..."
if ls /dev/video* >/dev/null 2>&1; then
    echo "✅ Found camera devices:"
    ls -la /dev/video*
else
    echo "❌ No camera devices found at /dev/video*"
    echo "   Make sure a camera is connected"
fi

# Check camera permissions
echo ""
echo "Checking camera permissions..."
for device in /dev/video*; do
    if [ -r "$device" ] && [ -w "$device" ]; then
        echo "✅ $device is accessible"
    else
        echo "❌ $device is not accessible (permission denied)"
    fi
done

# Test camera with cheese if available
echo ""
echo "Testing camera..."
if command -v cheese >/dev/null 2>&1; then
    echo "✅ Cheese is available for testing"
    echo "   You can test your camera by running: cheese"
elif command -v guvcview >/dev/null 2>&1; then
    echo "✅ guvcview is available for testing"
    echo "   You can test your camera by running: guvcview"
else
    echo "⚠️  No camera testing software found"
    echo "   Install cheese or guvcview to test your camera"
fi

echo ""
echo "Setup complete!"
echo "If you were added to the video group, please log out and log back in"
echo "Then run: python fix_camera_permissions.py"



