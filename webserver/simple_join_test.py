#!/usr/bin/env python3
"""
Simple test to understand the join issue
"""

import socketio
import time

def simple_join_test():
    print("🔍 Simple Join Test")
    print("=" * 40)
    
    server_url = "http://172.17.213.107:5000"
    session_id = "172.17.213.107"
    username = "test_user_from_222_34"
    
    print(f"Server: {server_url}")
    print(f"Session ID: {session_id}")
    print(f"Username: {username}")
    print()
    
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ Connected to server")
        print("🔄 Sending join request...")
        sio.emit('join_session', {
            'username': username,
            'session_id': session_id
        })
    
    @sio.event
    def join_success(data):
        print("🎉 JOIN SUCCESS!")
        print(f"   Session: {data.get('session')}")
        print(f"   Users: {data.get('users')}")
        print(f"   Host: {data.get('host')}")
        print(f"   Is Host: {data.get('is_host')}")
        sio.disconnect()
    
    @sio.event
    def join_error(data):
        print("❌ JOIN ERROR!")
        print(f"   Message: {data.get('message')}")
        sio.disconnect()
    
    @sio.event
    def disconnect():
        print("ℹ️  Disconnected from server")
    
    # Add more event handlers to catch any other responses
    @sio.event
    def connect_error(data):
        print(f"❌ Connection error: {data}")
    
    @sio.on('*')
    def catch_all(event, data):
        print(f"📨 Received event '{event}': {data}")
    
    try:
        print("🔌 Connecting to server...")
        sio.connect(server_url)
        
        # Wait for response
        print("⏳ Waiting for response...")
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if sio.connected:
            print("🔌 Disconnecting...")
            sio.disconnect()
    
    print("\n✅ Test completed")

if __name__ == "__main__":
    simple_join_test()