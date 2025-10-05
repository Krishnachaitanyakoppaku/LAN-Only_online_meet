#!/usr/bin/env python3
"""
Test script to verify video functionality
"""

import sys
import time
import threading
from client.main_client import LANVideoClient
from shared.utils import logger

def test_video_client():
    """Test video client functionality"""
    print("Testing video client...")
    
    # Create client
    client = LANVideoClient()
    
    # Test camera initialization
    print("Testing camera initialization...")
    if client.video_client.start_camera():
        print("✓ Camera started successfully")
        
        # Test frame capture
        print("Testing frame capture...")
        time.sleep(2)  # Let it capture a few frames
        
        # Check if frames are being sent
        stats = client.video_client.get_video_stats()
        print(f"Video stats: {stats}")
        
        # Stop camera
        client.video_client.stop_camera()
        print("✓ Camera stopped successfully")
    else:
        print("✗ Failed to start camera")
        return False
    
    return True

def test_server_connection():
    """Test server connection"""
    print("Testing server connection...")
    
    client = LANVideoClient()
    
    # Set up callbacks
    def on_connect(data):
        print("✓ Connected to server")
    
    def on_error(error):
        print(f"✗ Connection error: {error}")
    
    client.set_callback('on_connect', on_connect)
    client.set_callback('on_error', on_error)
    
    # Try to connect
    if client.connect("127.0.0.1", 8888, "test_user"):
        print("✓ Successfully connected to server")
        time.sleep(1)
        client.disconnect()
        return True
    else:
        print("✗ Failed to connect to server")
        return False

if __name__ == "__main__":
    print("LAN Video Calling - Video Functionality Test")
    print("=" * 50)
    
    # Test video client
    video_ok = test_video_client()
    
    # Test server connection
    server_ok = test_server_connection()
    
    print("\nTest Results:")
    print(f"Video Client: {'PASS' if video_ok else 'FAIL'}")
    print(f"Server Connection: {'PASS' if server_ok else 'FAIL'}")
    
    if video_ok and server_ok:
        print("\n✓ All tests passed! Video functionality should work.")
    else:
        print("\n✗ Some tests failed. Check the logs for details.")
        sys.exit(1)

