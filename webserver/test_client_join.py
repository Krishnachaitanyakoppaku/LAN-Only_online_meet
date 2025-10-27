#!/usr/bin/env python3
"""
Test client joining process
"""
import socketio
import time
import threading

def test_client_join():
    """Test the client join process"""
    print("🧪 Testing client join process...")
    
    # Create a Socket.IO client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ Client connected to server")
        
        # Try to join session
        print("📝 Attempting to join session...")
        sio.emit('join_session', {
            'username': 'test_client'
            # No session_id - should auto-join main_session
        })
    
    @sio.event
    def disconnect():
        print("❌ Client disconnected from server")
    
    @sio.event
    def join_success(data):
        print(f"✅ Successfully joined session!")
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
        # Connect to server
        print("🔌 Connecting to server...")
        sio.connect('http://localhost:5000')
        
        # Wait for events
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    test_client_join()