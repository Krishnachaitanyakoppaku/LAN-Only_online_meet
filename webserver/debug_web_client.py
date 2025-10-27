#!/usr/bin/env python3
"""
Debug web client issues
"""
import requests
import socket

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

def test_web_pages():
    """Test web page accessibility"""
    local_ip = get_local_ip()
    
    pages_to_test = [
        f"http://localhost:5000/",
        f"http://localhost:5000/simple-join",
        f"http://localhost:5000/simple-host",
        f"http://{local_ip}:5000/",
        f"http://{local_ip}:5000/simple-join",
        f"http://{local_ip}:5000/simple-host",
    ]
    
    print(f"🌐 Local IP: {local_ip}")
    print(f"🧪 Testing web page accessibility...\n")
    
    for url in pages_to_test:
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
    
    # Test API endpoints
    print(f"\n🔍 Testing API endpoints...")
    api_endpoints = [
        f"http://localhost:5000/api/server-info",
        f"http://localhost:5000/api/sessions",
        f"http://localhost:5000/api/debug/sessions",
        f"http://{local_ip}:5000/api/server-info",
        f"http://{local_ip}:5000/api/sessions",
        f"http://{local_ip}:5000/api/debug/sessions",
    ]
    
    for url in api_endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {url}")
                if 'sessions' in data:
                    print(f"   Sessions: {len(data.get('sessions', []))}")
                if 'total_sessions' in data:
                    print(f"   Total sessions: {data.get('total_sessions')}")
                if 'server_ip' in data:
                    print(f"   Server IP: {data.get('server_ip')}")
            else:
                print(f"⚠️ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")

if __name__ == "__main__":
    test_web_pages()