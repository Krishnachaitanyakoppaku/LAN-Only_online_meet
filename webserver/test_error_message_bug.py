#!/usr/bin/env python3
"""
Test to reproduce the exact error message bug
"""

import socketio
import time

def test_error_message():
    print("🔍 Testing Error Message Bug")
    print("=" * 50)
    
    # Connect from client IP 172.17.222.34 to server 172.17.213.107
    server_url = "http://172.17.213.107:5000"
    
    print(f"Connecting to: {server_url}")
    print("Attempting to join non-existent session to trigger error...")
    
    sio = socketio.Client()
    error_received = None
    
    @sio.event
    def connect():
        print("✅ Connected to server")
        # Try to join a session that doesn't exist to trigger the error path
        sio.emit('join_session', {
            'username': 'test_user_from_222_34',
            'session_id': 'non_existent_session'
        })
    
    @sio.event
    def join_error(data):
        nonlocal error_received
        error_received = data.get('message', '')
        print(f"❌ Error received:")
        print(f"   {error_received}")
        
        # Check if the error contains the wrong IP
        if '172.17.222.34' in error_received:
            print("\n🐛 BUG CONFIRMED!")
            print("   Error message contains client IP (172.17.222.34) instead of server IP!")
        elif '172.17.213.107' in error_received:
            print("\n✅ Error message correctly contains server IP")
        else:
            print("\n❓ Error message doesn't contain any IP address")
        
        sio.disconnect()
    
    @sio.event
    def join_success(data):
        print(f"✅ Unexpected success: {data}")
        sio.disconnect()
    
    try:
        sio.connect(server_url)
        time.sleep(3)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()
    
    # Now test the specific scenario: no active sessions
    print(f"\n2️⃣ Testing 'no active sessions' error path...")
    
    # First check if there are active sessions
    import requests
    try:
        response = requests.get(f'{server_url}/api/debug/sessions')
        data = response.json()
        if data['total_sessions'] > 0:
            print("   ⚠️  There are active sessions, so we won't get the 'no sessions' error")
            print(f"   Active sessions: {list(data['active_sessions'].keys())}")
            return
    except:
        pass
    
    # If no sessions, try to join any session to trigger the "no active sessions" error
    sio2 = socketio.Client()
    
    @sio2.event
    def connect():
        print("✅ Connected for no-sessions test")
        sio2.emit('join_session', {
            'username': 'test_no_sessions',
            'session_id': '172.17.213.107'  # Try to join server IP session
        })
    
    @sio2.event
    def join_error(data):
        error_msg = data.get('message', '')
        print(f"❌ No-sessions error:")
        print(f"   {error_msg}")
        
        if '172.17.222.34' in error_msg:
            print("\n🐛 BUG CONFIRMED IN NO-SESSIONS PATH!")
            print("   Server is returning client IP instead of server IP!")
        elif '172.17.213.107' in error_msg:
            print("\n✅ No-sessions error correctly shows server IP")
        
        sio2.disconnect()
    
    try:
        sio2.connect(server_url)
        time.sleep(3)
    except Exception as e:
        print(f"❌ Second connection failed: {e}")
    finally:
        if sio2.connected:
            sio2.disconnect()

if __name__ == "__main__":
    test_error_message()