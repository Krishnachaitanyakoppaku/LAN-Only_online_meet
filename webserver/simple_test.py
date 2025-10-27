#!/usr/bin/env python3
"""
Simple Test Script for Session Joining
"""

import requests
import time

def test_server():
    """Test if server is running"""
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False

def get_host_ip():
    """Get the host machine's IP address"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def main():
    print("🔧 Session Joining Test")
    print("=" * 30)
    
    if not test_server():
        print("Please start the server first: python3 server.py")
        return
    
    host_ip = get_host_ip()
    print(f"🌐 Host IP: {host_ip}")
    
    print("\n📋 Manual Test Instructions:")
    print("1. Open browser to: http://localhost:5000")
    print("2. Click 'Host Session' and enter username 'Host'")
    print(f"3. Note the Session ID (should be: {host_ip})")
    print("4. Open another browser tab")
    print("5. Click 'Join Session' and enter:")
    print(f"   - Username: 'Participant'")
    print(f"   - Session ID: {host_ip}")
    print("6. Check server terminal for debug logs")
    print("7. Check browser console (F12) for any errors")
    
    print("\n🔍 What to look for:")
    print("- Server terminal should show session creation and joining logs")
    print("- Browser should redirect to session page after joining")
    print("- Participants list should show both users")
    print("- Host should see '(Host)' badge and 'Logs' button")

if __name__ == "__main__":
    main()
