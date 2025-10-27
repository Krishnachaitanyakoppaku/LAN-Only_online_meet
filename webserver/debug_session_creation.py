#!/usr/bin/env python3
"""
Debug session creation issue on remote server
"""

import socketio
import time
import requests

def debug_session_creation():
    print("🔍 Debugging Session Creation Issue")
    print("=" * 50)
    
    remote_server = "10.14.84.28"
    
    # First check current state
    print("1️⃣ Checking current server state...")
    try:
        response = requests.get(f'http://{remote_server}:5000/api/debug/sessions')
        data = response.json()
        print(f"   Sessions: {data['total_sessions']}")
        print(f"   Users: {data['total_users']}")
        print(f"   Connected users: {data['connected_users']}")
    except Exception as e:
        print(f"   ❌ Failed to get server state: {e}")
        return
    
    # Try to create a session via socket
    print("\n2️⃣ Attempting to create a test session...")
    
    sio = socketio.Client()
    session_created = False
    error_received = None
    
    @sio.event
    def connect():
        print("   ✅ Connected to server")
        # Try to create a session
        sio.emit('create_session', {
            'username': 'debug_user',
            'session_id': '10.14.84.28'  # Use the server IP as session ID
        })
    
    @sio.event
    def create_success(data):
        nonlocal session_created
        session_created = True
        print(f"   ✅ Session created successfully!")
        print(f"      Session ID: {data['session']}")
        print(f"      Users: {data['users']}")
        print(f"      Is Host: {data['is_host']}")
    
    @sio.event
    def create_error(data):
        nonlocal error_received
        error_received = data['message']
        print(f"   ❌ Session creation failed: {data['message']}")
    
    @sio.event
    def join_success(data):
        print(f"   ℹ️  Joined existing session instead:")
        print(f"      Session ID: {data['session']}")
        print(f"      Users: {data['users']}")
        print(f"      Host: {data['host']}")
        print(f"      Is Host: {data['is_host']}")
    
    try:
        sio.connect(f'http://{remote_server}:5000')
        time.sleep(3)  # Wait for response
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    finally:
        if sio.connected:
            sio.disconnect()
    
    # Check server state after attempt
    print("\n3️⃣ Checking server state after session creation attempt...")
    try:
        response = requests.get(f'http://{remote_server}:5000/api/debug/sessions')
        data = response.json()
        print(f"   Sessions: {data['total_sessions']}")
        print(f"   Users: {data['total_users']}")
        print(f"   Connected users: {data['connected_users']}")
        
        if data['active_sessions']:
            print("   📋 Active sessions found:")
            for session_id, session_data in data['active_sessions'].items():
                print(f"      • {session_id}: Host={session_data['host']}, Users={session_data['user_count']}")
        else:
            print("   ⚠️  Still no active sessions")
    except Exception as e:
        print(f"   ❌ Failed to get updated server state: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 ANALYSIS:")
    print("=" * 50)
    
    if session_created:
        print("✅ Session creation works - the issue might be elsewhere")
    elif error_received:
        print(f"❌ Session creation failed with error: {error_received}")
        print("   This suggests a server-side issue in session management")
    else:
        print("❓ No clear response received - possible server communication issue")
    
    print("\n💡 POSSIBLE CAUSES:")
    print("1. Session cleanup: Sessions might be getting deleted immediately")
    print("2. IP mismatch: Server might be using different IP internally")
    print("3. Session storage: In-memory storage might be getting cleared")
    print("4. Multiple server instances: Different processes handling requests")
    print("5. Network issues: Packets getting lost between create and query")

if __name__ == "__main__":
    debug_session_creation()