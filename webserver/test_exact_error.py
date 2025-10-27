#!/usr/bin/env python3
"""
Test to capture the exact error message being returned
"""

import socketio
import time
import requests

def test_exact_error():
    print("🔍 Testing Exact Error Message")
    print("=" * 50)
    
    server_url = "http://172.17.213.107:5000"
    
    # Test 1: Try with wrong session ID to see error message
    print("1️⃣ Testing with wrong session ID...")
    test_wrong_session_id(server_url)
    
    print("\n2️⃣ Testing with correct session ID...")
    test_correct_session_id(server_url)
    
    print("\n3️⃣ Testing with client IP as session ID...")
    test_client_ip_as_session_id(server_url)

def test_wrong_session_id(server_url):
    """Test with a clearly wrong session ID"""
    sio = socketio.Client()
    error_received = None
    
    @sio.event
    def connect():
        print("   ✅ Connected")
        sio.emit('join_session', {
            'username': 'test_user',
            'session_id': 'wrong_session_id'
        })
    
    @sio.event
    def join_error(data):
        nonlocal error_received
        error_received = data.get('message', 'No message')
        print(f"   ❌ Error: {error_received}")
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

def test_correct_session_id(server_url):
    """Test with the correct session ID"""
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("   ✅ Connected")
        sio.emit('join_session', {
            'username': 'test_user_correct',
            'session_id': '172.17.213.107'
        })
    
    @sio.event
    def join_error(data):
        error_msg = data.get('message', 'No message')
        print(f"   ❌ Unexpected error: {error_msg}")
        sio.disconnect()
    
    @sio.event
    def join_success(data):
        print(f"   ✅ Success: Session={data.get('session')}, Users={len(data.get('users', []))}")
        sio.disconnect()
    
    try:
        sio.connect(server_url)
        time.sleep(3)
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

def test_client_ip_as_session_id(server_url):
    """Test with client IP as session ID (what user might be trying)"""
    sio = socketio.Client()
    error_received = None
    
    @sio.event
    def connect():
        print("   ✅ Connected")
        sio.emit('join_session', {
            'username': 'test_user_client_ip',
            'session_id': '172.17.222.34'  # Client IP instead of server IP
        })
    
    @sio.event
    def join_error(data):
        nonlocal error_received
        error_received = data.get('message', 'No message')
        print(f"   ❌ Error when using client IP: {error_received}")
        
        # Check if error mentions "client ip"
        if 'client ip' in error_received.lower():
            print("   🐛 BUG: Error message incorrectly mentions 'client ip'")
        elif 'server ip' in error_received.lower():
            print("   ✅ Error message correctly mentions 'server ip'")
        
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

if __name__ == "__main__":
    test_exact_error()