#!/usr/bin/env python3
"""
Test the IP detection fix
"""

import requests
import socketio
import time

def test_ip_fix():
    print("🔍 Testing IP Detection Fix")
    print("=" * 50)
    
    server_url = "http://172.17.213.107:5000"
    
    # Test 1: Check server-info endpoint
    print("1️⃣ Testing server-info endpoint...")
    try:
        response = requests.get(f'{server_url}/api/server-info')
        server_info = response.json()
        reported_ip = server_info['server_ip']
        print(f"   Server reports IP: {reported_ip}")
        
        if reported_ip == "172.17.213.107":
            print("   ✅ Server correctly reports its IP")
        else:
            print(f"   ❌ Server reports wrong IP: {reported_ip}")
    except Exception as e:
        print(f"   ❌ Failed to get server info: {e}")
        return
    
    # Test 2: Trigger the error message to see if it shows correct IP
    print("\n2️⃣ Testing error message with correct IP...")
    
    sio = socketio.Client()
    error_received = None
    
    @sio.event
    def connect():
        print("   ✅ Connected to server")
        # Try to join non-existent session to trigger error
        sio.emit('join_session', {
            'username': 'test_user_ip_fix',
            'session_id': 'non_existent_session_12345'
        })
    
    @sio.event
    def join_error(data):
        nonlocal error_received
        error_received = data.get('message', '')
        print(f"   ❌ Error message received:")
        print(f"      {error_received}")
        
        if '172.17.213.107' in error_received:
            print("   ✅ Error message correctly shows server IP (172.17.213.107)")
        elif '172.17.222.34' in error_received:
            print("   ❌ BUG STILL EXISTS: Error shows client IP (172.17.222.34)")
        else:
            print("   ❓ Error message doesn't contain expected IP")
        
        sio.disconnect()
    
    @sio.event
    def join_success(data):
        print(f"   ✅ Unexpected success: {data}")
        sio.disconnect()
    
    try:
        sio.connect(server_url)
        time.sleep(3)
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()
    
    # Test 3: Test the "no active sessions" error path specifically
    print("\n3️⃣ Testing 'no active sessions' error path...")
    
    # First, check if there are sessions and clear them if needed
    try:
        response = requests.get(f'{server_url}/api/debug/sessions')
        data = response.json()
        if data['total_sessions'] > 0:
            print("   ℹ️  Active sessions exist, testing with wrong session ID instead")
            test_session_id = "definitely_wrong_session_id"
        else:
            print("   ℹ️  No active sessions, testing no-sessions error path")
            test_session_id = "172.17.213.107"
    except:
        test_session_id = "test_session"
    
    sio2 = socketio.Client()
    
    @sio2.event
    def connect():
        print("   ✅ Connected for no-sessions test")
        sio2.emit('join_session', {
            'username': 'test_no_sessions_ip_fix',
            'session_id': test_session_id
        })
    
    @sio2.event
    def join_error(data):
        error_msg = data.get('message', '')
        print(f"   ❌ No-sessions error:")
        print(f"      {error_msg}")
        
        if '172.17.213.107' in error_msg:
            print("   ✅ No-sessions error correctly shows server IP")
        elif '172.17.222.34' in error_msg:
            print("   ❌ BUG: No-sessions error shows client IP")
        else:
            print("   ❓ No-sessions error doesn't contain expected IP")
        
        sio2.disconnect()
    
    @sio2.event
    def join_success(data):
        print(f"   ✅ Joined successfully: {data}")
        sio2.disconnect()
    
    try:
        sio2.connect(server_url)
        time.sleep(3)
    except Exception as e:
        print(f"   ❌ Second connection failed: {e}")
    finally:
        if sio2.connected:
            sio2.disconnect()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("=" * 50)
    print("If the fix worked correctly, you should see:")
    print("✅ Server reports correct IP: 172.17.213.107")
    print("✅ Error messages show server IP: 172.17.213.107")
    print("❌ Error messages should NOT show client IP: 172.17.222.34")

if __name__ == "__main__":
    test_ip_fix()