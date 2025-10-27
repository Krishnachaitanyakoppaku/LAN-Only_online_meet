#!/usr/bin/env python3
"""
Test client joining process from network IP
"""
import socketio
import time
import socket

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def test_network_client_join():
    """Test the client join process from network IP"""
    local_ip = get_local_ip()
    server_url = f"http://{local_ip}:5000"
    
    print(f"🧪 Testing client join from network IP: {server_url}")
    
    # Create a Socket.IO client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ Client connected to server via network IP")
        
        # Try to join session
        print("📝 Attempting to join session...")
        sio.emit('join_session', {
            'username': 'network_test_client'
            # No session_id - should auto-join main_session
        })
    
    @sio.event
    def disconnect():
        print("❌ Client disconnected from server")
    
    @sio.event
    def join_success(data):
        print(f"✅ Successfully joined session from network IP!")
        print(f"   Session: {data.get('session')}")
        print(f"   Users: {data.get('users')}")
        print(f"   Host: {data.get('host')}")
        print(f"   Is Host: {data.get('is_host')}")
        sio.disconnect()
    
    @sio.event
    def join_error(data):
        print(f"❌ Failed to join session: {data.get('message')}")
        sio.disconnect()
    
    try:
        # Connect to server via network IP
        print(f"🔌 Connecting to server at {server_url}...")
        sio.connect(server_url)
        
        # Wait for events
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    test_network_client_join()