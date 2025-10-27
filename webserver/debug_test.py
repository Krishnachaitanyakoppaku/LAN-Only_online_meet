#!/usr/bin/env python3
"""
Debug Test Script for LAN Communication Hub
This script helps test the session creation and joining functionality
"""

import requests
import json
import socketio
import time

def get_host_ip():
    """Get the host machine's IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def test_server_connection():
    """Test if server is running"""
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False

def test_session_creation():
    """Test session creation via SocketIO"""
    print("\n🧪 Testing Session Creation...")
    
    sio = socketio.SimpleClient()
    
    try:
        # Connect to server
        sio.connect('http://localhost:5000')
        print("✅ Connected to server")
        
        # Create session
        sio.emit('create_session', {
            'username': 'TestHost',
            'session_id': None  # Let server generate IP-based ID
        })
        
        # Wait for response
        time.sleep(1)
        
        # Check if we received any events
        events = sio.get_received()
        print(f"📡 Received {len(events)} events")
        
        for event in events:
            print(f"   Event: {event['name']}")
            if event['name'] == 'create_success':
                data = event['args'][0]
                print(f"✅ Session created successfully!")
                print(f"   Session ID: {data['session']}")
                print(f"   Users: {data['users']}")
                print(f"   Is Host: {data['is_host']}")
                return data['session']
            elif event['name'] == 'create_error':
                data = event['args'][0]
                print(f"❌ Session creation failed: {data['message']}")
                return None
        
        sio.disconnect()
        return None
        
    except Exception as e:
        print(f"❌ Session creation test failed: {e}")
        return None

def test_session_joining(session_id):
    """Test joining an existing session"""
    if not session_id:
        print("❌ No session ID to test joining")
        return False
        
    print(f"\n🧪 Testing Session Joining (ID: {session_id})...")
    
    sio = socketio.SimpleClient()
    
    try:
        # Connect to server
        sio.connect('http://localhost:5000')
        print("✅ Connected to server")
        
        # Join session
        sio.emit('join_session', {
            'username': 'TestParticipant',
            'session_id': session_id
        })
        
        # Wait for response
        time.sleep(1)
        
        # Check if we received any events
        events = sio.get_received()
        print(f"📡 Received {len(events)} events")
        
        for event in events:
            print(f"   Event: {event['name']}")
            if event['name'] == 'join_success':
                data = event['args'][0]
                print(f"✅ Joined session successfully!")
                print(f"   Session ID: {data['session']}")
                print(f"   Users: {data['users']}")
                print(f"   Host: {data['host']}")
                print(f"   Is Host: {data['is_host']}")
                sio.disconnect()
                return True
            elif event['name'] == 'join_error':
                data = event['args'][0]
                print(f"❌ Join session failed: {data['message']}")
                sio.disconnect()
                return False
        
        print("❌ No response received")
        sio.disconnect()
        return False
        
    except Exception as e:
        print(f"❌ Session joining test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 LAN Communication Hub - Debug Test")
    print("=" * 50)
    
    # Test server connection
    if not test_server_connection():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python3 server.py")
        return
    
    # Get host IP
    host_ip = get_host_ip()
    print(f"\n🌐 Host IP Address: {host_ip}")
    
    # Test session creation
    session_id = test_session_creation()
    
    # Test session joining
    if session_id:
        test_session_joining(session_id)
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    
    if session_id:
        print(f"\n📋 Manual Test Instructions:")
        print(f"1. Open browser to: http://localhost:5000")
        print(f"2. Click 'Host Session' and enter username 'Host'")
        print(f"3. Session ID should be: {session_id}")
        print(f"4. Open another browser tab")
        print(f"5. Click 'Join Session' and enter:")
        print(f"   - Username: 'Participant'")
        print(f"   - Session ID: {session_id}")
        print(f"6. Check browser console (F12) for any errors")

if __name__ == "__main__":
    main()
