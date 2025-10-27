#!/usr/bin/env python3
"""
Simulate the exact error the user encountered
"""

import socketio
import time

def simulate_join_error():
    print("🔍 Simulating the exact error you encountered...")
    print("=" * 60)
    
    # Create socket connection
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ Connected to server")
        
        # Try to join with the wrong session ID (the one you used)
        print("🔄 Attempting to join session '10.14.84.28'...")
        sio.emit('join_session', {
            'username': 'test_user',
            'session_id': '10.14.84.28'
        })
    
    @sio.event
    def join_error(data):
        print("❌ Join Error Received:")
        print(f"   {data['message']}")
        sio.disconnect()
    
    @sio.event
    def join_success(data):
        print("✅ Join Success (unexpected):")
        print(f"   {data}")
        sio.disconnect()
    
    try:
        sio.connect('http://localhost:5000')
        time.sleep(2)  # Wait for response
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    simulate_join_error()