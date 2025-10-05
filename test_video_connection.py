#!/usr/bin/env python3
"""
Test script to verify video connection between client and server
"""

import sys
import time
import threading
from client.main_client import LANVideoClient
from server.host_server import HostServer
from shared.utils import logger

def test_video_connection():
    """Test video connection between client and server"""
    print("Testing video connection between client and server...")
    
    # Start host server
    print("Starting host server...")
    server = HostServer("127.0.0.1", 8889, "TestHost")
    
    if not server.start_host_mode():
        print("❌ Failed to start host server")
        return False
    
    print("✅ Host server started")
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Create client
    print("Creating client...")
    client = LANVideoClient()
    
    # Set up callbacks
    def on_connect(data):
        print("✅ Client connected to server")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Is Host: {data.get('is_host', False)}")
    
    def on_error(error):
        print(f"❌ Client error: {error}")
    
    def on_frame_received(user_id, frame):
        print(f"✅ Received video frame from user: {user_id}")
    
    def on_local_frame(frame):
        print("✅ Local video frame captured")
    
    client.set_callback('on_connect', on_connect)
    client.set_callback('on_error', on_error)
    client.set_callback('on_frame_received', on_frame_received)
    client.set_callback('on_local_frame', on_local_frame)
    
    # Connect client
    print("Connecting client to server...")
    if not client.connect("127.0.0.1", 8889, "TestUser"):
        print("❌ Failed to connect client to server")
        server.stop()
        return False
    
    print("✅ Client connected successfully")
    
    # Wait for connection to be established
    time.sleep(2)
    
    # Check if client is authenticated
    print(f"Client authenticated: {client.is_authenticated}")
    print(f"User ID: {client.user_id}")
    
    # Test video start (no room required)
    print("Testing video start...")
    if client.start_video():
        print("✅ Video started successfully")
        
        # Let it run for a few seconds
        print("Capturing video for 5 seconds...")
        time.sleep(5)
        
        # Check video stats
        stats = client.video_client.get_video_stats()
        print(f"Video stats: {stats}")
        
        if stats['frames_sent'] > 0:
            print("✅ Video frames are being sent")
        else:
            print("❌ No video frames were sent")
        
        # Stop video
        client.stop_video()
        print("✅ Video stopped")
    else:
        print("❌ Failed to start video")
    
    # Disconnect
    print("Disconnecting...")
    client.disconnect()
    server.stop()
    print("✅ Test completed")
    
    return True

def test_camera_only():
    """Test camera functionality only"""
    print("Testing camera functionality...")
    
    client = LANVideoClient()
    
    # Test camera start
    if client.video_client.start_camera():
        print("✅ Camera started")
        
        # Let it capture frames
        time.sleep(3)
        
        # Check stats
        stats = client.video_client.get_video_stats()
        print(f"Camera stats: {stats}")
        
        # Stop camera
        client.video_client.stop_camera()
        print("✅ Camera stopped")
        return True
    else:
        print("❌ Failed to start camera")
        return False

if __name__ == "__main__":
    print("LAN Video Calling - Video Connection Test")
    print("=" * 50)
    
    # Test 1: Camera only
    print("\n1. Testing camera functionality...")
    camera_ok = test_camera_only()
    
    # Test 2: Full video connection
    print("\n2. Testing full video connection...")
    connection_ok = test_video_connection()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Camera functionality: {'PASS' if camera_ok else 'FAIL'}")
    print(f"Video connection: {'PASS' if connection_ok else 'FAIL'}")
    
    if camera_ok and connection_ok:
        print("\n🎉 All video tests passed!")
        print("Video should work in the actual application.")
    else:
        print("\n❌ Some tests failed.")
        print("Check the logs above for specific issues.")
        sys.exit(1)
