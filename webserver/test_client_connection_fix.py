#!/usr/bin/env python3
"""
Test that clients connect to the correct server IP
"""
import requests
import socket
import time

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

def test_client_connection_fix():
    """Test that the client connection fix works"""
    local_ip = get_local_ip()
    
    print(f"🧪 Testing Client Connection Fix")
    print(f"🌐 Server IP: {local_ip}")
    print("=" * 50)
    
    # Test 1: Access simple-join page from network IP
    try:
        url = f"http://{local_ip}:5000/simple-join"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Simple-join page accessible from network IP")
            
            # Check if the page contains the correct socket.io connection code
            content = response.text
            if 'window.location.host' in content:
                print(f"✅ Page uses window.location.host for socket connection")
            else:
                print(f"❌ Page doesn't use window.location.host")
                
            if 'console.log' in content and 'Connecting to server at' in content:
                print(f"✅ Page has debug logging for connection URL")
            else:
                print(f"⚠️ Page missing debug logging")
                
        else:
            print(f"❌ Simple-join page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing simple-join page: {e}")
    
    # Test 2: Check that session page also uses correct connection
    try:
        url = f"http://{local_ip}:5000/session"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Session page accessible from network IP")
            
            # This page uses session.js, check if it's fixed
            js_url = f"http://{local_ip}:5000/static/js/session.js"
            js_response = requests.get(js_url, timeout=5)
            
            if js_response.status_code == 200:
                js_content = js_response.text
                if 'window.location.host' in js_content:
                    print(f"✅ Session.js uses window.location.host")
                else:
                    print(f"❌ Session.js doesn't use window.location.host")
            
        else:
            print(f"❌ Session page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing session page: {e}")
    
    # Test 3: Verify API endpoints work from network IP
    try:
        url = f"http://{local_ip}:5000/api/sessions"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accessible from network IP")
            print(f"   Available sessions: {len(data.get('sessions', []))}")
            print(f"   Server IP reported: {data.get('server_ip')}")
        else:
            print(f"❌ API not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing API: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 INSTRUCTIONS FOR CLIENTS:")
    print(f"   1. Use this URL: http://{local_ip}:5000/simple-join")
    print(f"   2. Enter name and click 'Join Meeting'")
    print(f"   3. Client will automatically connect to {local_ip}:5000")
    print("=" * 50)

if __name__ == "__main__":
    test_client_connection_fix()