#!/usr/bin/env python3
"""
Test the new session discovery approach
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

def test_session_discovery():
    """Test the session discovery functionality"""
    local_ip = get_local_ip()
    
    print(f"🧪 Testing Session Discovery Approach")
    print(f"🌐 Server IP: {local_ip}")
    print("=" * 60)
    
    # Test 1: Check if meeting finder page is accessible
    try:
        finder_url = f"http://{local_ip}:5000/static/meeting-finder.html"
        response = requests.get(finder_url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Meeting finder page accessible")
            print(f"   URL: {finder_url}")
        else:
            print(f"❌ Meeting finder page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing meeting finder: {e}")
    
    # Test 2: Check if session discovery page is accessible
    try:
        discovery_url = f"http://{local_ip}:5000/find-meeting"
        response = requests.get(discovery_url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Session discovery page accessible")
            print(f"   URL: {discovery_url}")
        else:
            print(f"❌ Session discovery page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing session discovery: {e}")
    
    # Test 3: Test API endpoint that clients will use to verify server
    try:
        api_url = f"http://{local_ip}:5000/api/server-info"
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server info API working")
            print(f"   Server IP: {data.get('server_ip')}")
            print(f"   Server Port: {data.get('server_port')}")
        else:
            print(f"❌ Server info API not working: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing server info API: {e}")
    
    # Test 4: Test CORS headers (important for cross-origin requests)
    try:
        api_url = f"http://{local_ip}:5000/api/server-info"
        response = requests.get(api_url, timeout=5)
        
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            print(f"✅ CORS headers present: {cors_header}")
        else:
            print(f"⚠️ No CORS headers found (might cause issues with meeting finder)")
            
    except Exception as e:
        print(f"❌ Error checking CORS headers: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 NEW USER WORKFLOW:")
    print(f"   1. Host creates meeting at: http://{local_ip}:5000/simple-host")
    print(f"   2. Host shares session ID: {local_ip}")
    print(f"   3. Client uses meeting finder: http://any-server/static/meeting-finder.html")
    print(f"   4. Client enters session ID: {local_ip}")
    print(f"   5. Client gets redirected to: http://{local_ip}:5000/simple-join")
    print(f"   6. Client joins meeting automatically!")
    print("=" * 60)
    
    print(f"\n📋 SHARING OPTIONS FOR HOST:")
    print(f"   Option 1 - Direct Link: http://{local_ip}:5000/simple-join")
    print(f"   Option 2 - Universal Finder: http://{local_ip}:5000/static/meeting-finder.html?session={local_ip}")
    print(f"   Option 3 - Session ID Only: {local_ip}")

if __name__ == "__main__":
    test_session_discovery()