#!/usr/bin/env python3
"""
Test script to verify host can see client videos
"""

import time
import threading
from client.main_client import LANVideoClient
from server.host_server import HostServer
from shared.utils import logger

def test_host_client_video():
    """Test that host can see client video"""
    print("Testing Host-Client Video Communication")
    print("=====================================")
    
    # Start host server
    print("Starting host server...")
    server = HostServer("127.0.0.1", 8891, "TestHost")
    if not server.start_host_mode():
        print("❌ Failed to start host server")
        return False
    print("✅ Host server started")
    
    # Wait for server to be ready
    time.sleep(1)
    
    # Create host client
    print("Creating host client...")
    host_client = LANVideoClient()
    
    # Create regular client
    print("Creating regular client...")
    client = LANVideoClient()
    
    # Set up callbacks
    host_frames_received = []
    client_frames_received = []
    
    def on_host_connect(data):
        print(f"✅ Host connected: {data.get('user_id')}")
    
    def on_client_connect(data):
        print(f"✅ Client connected: {data.get('user_id')}")
    
    def on_host_video_frame(user_id, frame):
        print(f"✅ Host received video frame from: {user_id}")
        host_frames_received.append((user_id, time.time()))
    
    def on_client_video_frame(user_id, frame):
        print(f"✅ Client received video frame from: {user_id}")
        client_frames_received.append((user_id, time.time()))
    
    def on_host_local_frame(frame):
        print("✅ Host local frame captured")
    
    def on_client_local_frame(frame):
        print("✅ Client local frame captured")
    
    # Set up host callbacks
    host_client.set_callback('on_connect', on_host_connect)
    host_client.set_callback('on_frame_received', on_host_video_frame)
    host_client.set_callback('on_local_frame', on_host_local_frame)
    
    # Set up client callbacks
    client.set_callback('on_connect', on_client_connect)
    client.set_callback('on_frame_received', on_client_video_frame)
    client.set_callback('on_local_frame', on_client_local_frame)
    
    # Connect host
    print("Connecting host...")
    if not host_client.connect("127.0.0.1", 8891, "TestHost"):
        print("❌ Host failed to connect")
        server.stop()
        return False
    print("✅ Host connected")
    
    # Wait for host to be ready
    time.sleep(2)
    
    # Connect client
    print("Connecting client...")
    if not client.connect("127.0.0.1", 8891, "TestClient"):
        print("❌ Client failed to connect")
        host_client.disconnect()
        server.stop()
        return False
    print("✅ Client connected")
    
    # Wait for both to be ready
    time.sleep(2)
    
    # Start video on client
    print("Starting video on client...")
    if not client.start_video():
        print("❌ Client failed to start video")
        client.disconnect()
        host_client.disconnect()
        server.stop()
        return False
    print("✅ Client video started")
    
    # Wait a moment for video to start
    time.sleep(2)
    
    # Start video on host
    print("Starting video on host...")
    if not host_client.start_video():
        print("❌ Host failed to start video")
        host_client.disconnect()
        client.disconnect()
        server.stop()
        return False
    print("✅ Host video started")
    
    # Let them exchange video for 10 seconds
    print("Exchanging video for 10 seconds...")
    for i in range(10):
        time.sleep(1)
        print(f"  {i+1}/10 seconds...")
    
    # Check results
    print("\nResults:")
    print(f"Host received {len(host_frames_received)} video frames")
    print(f"Client received {len(client_frames_received)} video frames")
    
    # Check if host received frames from client
    client_user_id = client.user_id
    host_received_from_client = any(user_id == client_user_id for user_id, _ in host_frames_received)
    
    if host_received_from_client:
        print("✅ SUCCESS: Host can see client video!")
    else:
        print("❌ FAILED: Host cannot see client video")
    
    # Check if client received frames from host
    host_user_id = host_client.user_id
    client_received_from_host = any(user_id == host_user_id for user_id, _ in client_frames_received)
    
    if client_received_from_host:
        print("✅ SUCCESS: Client can see host video!")
    else:
        print("❌ FAILED: Client cannot see host video")
    
    # Cleanup
    print("\nCleaning up...")
    client.stop_video()
    host_client.stop_video()
    client.disconnect()
    host_client.disconnect()
    server.stop()
    
    return host_received_from_client and client_received_from_host

if __name__ == "__main__":
    success = test_host_client_video()
    if success:
        print("\n🎉 All tests passed! Host and client can see each other's video.")
    else:
        print("\n❌ Some tests failed. Check the logs above.")
