#!/usr/bin/env python3
"""
Test Script for Cross-Computer Session Joining
"""

import requests
import json

def test_server_info():
    """Test server info API"""
    try:
        response = requests.get('http://localhost:5000/api/server-info', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server Info API working")
            print(f"   Server IP: {data['server_ip']}")
            print(f"   Server Port: {data['server_port']}")
            return data['server_ip']
        else:
            print(f"❌ Server Info API failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Server Info API error: {e}")
        return None

def test_main_page():
    """Test main page loads"""
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            return True
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main page error: {e}")
        return False

def main():
    print("🔧 Cross-Computer Session Joining Test")
    print("=" * 50)
    
    # Test main page
    if not test_main_page():
        print("Please start the server first: python3 server.py")
        return
    
    # Test server info
    server_ip = test_server_info()
    if not server_ip:
        print("Server info API not working")
        return
    
    print(f"\n🌐 Server IP Address: {server_ip}")
    
    print("\n📋 Instructions for Cross-Computer Testing:")
    print("1. On the HOST computer:")
    print(f"   - Open browser to: http://localhost:5000")
    print(f"   - Click 'Host Session' and enter username 'Host'")
    print(f"   - Session ID will be: {server_ip}")
    
    print("\n2. On CLIENT computers (same LAN):")
    print(f"   - Open browser to: http://{server_ip}:5000")
    print(f"   - Click 'Join Session' and enter:")
    print(f"     - Username: 'Client1', 'Client2', etc.")
    print(f"     - Session ID: {server_ip}")
    print(f"   - Click 'Join Session'")
    
    print("\n🔍 What to check:")
    print("- Server terminal should show session creation and joining logs")
    print("- All participants should appear in the participants list")
    print("- Host should see '(Host)' badge and 'Logs' button")
    print("- Host should be able to control other participants")
    
    print(f"\n💡 Key Points:")
    print(f"- Use {server_ip} as the Session ID (not localhost)")
    print(f"- All computers must be on the same LAN network")
    print(f"- Server IP is displayed at the top of the page")

if __name__ == "__main__":
    main()

