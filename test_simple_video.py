#!/usr/bin/env python3
"""
Simple video test - just start video and see if it works
"""

import time
from client.main_client import LANVideoClient
from server.host_server import HostServer

def test_simple_video():
    print("Simple Video Test")
    print("================")
    
    # Start server
    print("Starting server...")
    server = HostServer("127.0.0.1", 8890, "TestHost")
    if not server.start_host_mode():
        print("❌ Failed to start server")
        return False
    print("✅ Server started")
    
    # Wait a moment
    time.sleep(1)
    
    # Create client
    print("Creating client...")
    client = LANVideoClient()
    
    # Connect
    print("Connecting...")
    if not client.connect("127.0.0.1", 8890, "TestUser"):
        print("❌ Failed to connect")
        server.stop()
        return False
    print("✅ Connected")
    
    # Wait for authentication
    time.sleep(1)
    
    # Start video
    print("Starting video...")
    if client.start_video():
        print("✅ Video started!")
        print("You should see video frames being captured...")
        
        # Let it run for 10 seconds
        for i in range(10):
            time.sleep(1)
            stats = client.video_client.get_video_stats()
            print(f"Frames sent: {stats['frames_sent']}, FPS: {stats['fps_sent']:.1f}")
        
        # Stop video
        client.stop_video()
        print("✅ Video stopped")
    else:
        print("❌ Failed to start video")
    
    # Cleanup
    client.disconnect()
    server.stop()
    print("✅ Test completed")
    return True

if __name__ == "__main__":
    test_simple_video()


