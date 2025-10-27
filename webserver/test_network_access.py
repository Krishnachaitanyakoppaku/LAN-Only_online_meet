#!/usr/bin/env python3
"""
Test network accessibility of the server
"""
import socket
import requests
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
        return None

def test_server_access():
    """Test if server is accessible"""
    local_ip = get_local_ip()
    print(f"🌐 Detected local IP: {local_ip}")
    
    # Test localhost access
    try:
        response = requests.get("http://localhost:5000/api/server-info", timeout=5)
        print(f"✅ Localhost access: {response.status_code}")
        print(f"   Server info: {response.json()}")
    except Exception as e:
        print(f"❌ Localhost access failed: {e}")
    
    # Test network IP access
    if local_ip:
        try:
            response = requests.get(f"http://{local_ip}:5000/api/server-info", timeout=5)
            print(f"✅ Network IP access: {response.status_code}")
            print(f"   Server info: {response.json()}")
        except Exception as e:
            print(f"❌ Network IP access failed: {e}")
    
    # Test socket binding
    print(f"\n🔍 Testing socket binding...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(("localhost", 5000))
        print(f"✅ Can connect to localhost:5000")
        s.close()
    except Exception as e:
        print(f"❌ Cannot connect to localhost:5000: {e}")
    
    if local_ip:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((local_ip, 5000))
            print(f"✅ Can connect to {local_ip}:5000")
            s.close()
        except Exception as e:
            print(f"❌ Cannot connect to {local_ip}:5000: {e}")

if __name__ == "__main__":
    test_server_access()