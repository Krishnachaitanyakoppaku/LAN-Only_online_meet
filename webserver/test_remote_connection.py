#!/usr/bin/env python3
"""
Test connection to remote server at 10.14.84.28
"""

import requests
import json

def test_remote_server():
    print("🔍 Testing Connection to Remote Server")
    print("=" * 50)
    
    remote_server_ip = "10.14.84.28"
    your_ip = "10.14.84.126"
    
    print(f"🖥️  Remote server IP: {remote_server_ip}")
    print(f"💻 Your IP: {your_ip}")
    print()
    
    # Test basic connectivity
    print("1️⃣ Testing basic connectivity...")
    try:
        response = requests.get(f'http://{remote_server_ip}:5000', timeout=5)
        print(f"✅ Server is reachable (Status: {response.status_code})")
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - server may be down or unreachable")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - server is not running or port is blocked")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Get server info
    print("\n2️⃣ Getting server information...")
    try:
        response = requests.get(f'http://{remote_server_ip}:5000/api/server-info', timeout=5)
        server_info = response.json()
        print(f"✅ Server IP (reported): {server_info['server_ip']}")
        print(f"✅ Server Port: {server_info['server_port']}")
        print(f"✅ UDP Port: {server_info['udp_port']}")
    except Exception as e:
        print(f"❌ Failed to get server info: {e}")
        return False
    
    # Check active sessions
    print("\n3️⃣ Checking active sessions...")
    try:
        response = requests.get(f'http://{remote_server_ip}:5000/api/debug/sessions', timeout=5)
        debug_info = response.json()
        print(f"📊 Active sessions: {debug_info['total_sessions']}")
        print(f"👥 Connected users: {debug_info['total_users']}")
        
        if debug_info['active_sessions']:
            print("📋 Available sessions:")
            for session_id, session_data in debug_info['active_sessions'].items():
                print(f"  • Session ID: {session_id}")
                print(f"    Host: {session_data['host']}")
                print(f"    Users: {session_data['user_count']}")
                print(f"    Participants: {', '.join(session_data.get('users', []))}")
        else:
            print("⚠️  No active sessions found")
            
    except Exception as e:
        print(f"❌ Failed to get session info: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🔧 SOLUTION:")
    print("=" * 50)
    
    if debug_info['total_sessions'] == 0:
        print("❗ The host on the remote server needs to create a session first!")
        print()
        print("📝 Steps to fix:")
        print(f"1. Host (on {remote_server_ip}): Go to http://{remote_server_ip}:5000")
        print("2. Host: Click 'Host Session' and create a session")
        print("3. Host: Share the session ID with you")
        print(f"4. You: Go to http://{remote_server_ip}:5000 and join with the session ID")
        print()
        print("💡 The session ID will likely be one of these:")
        print(f"   • {remote_server_ip} (most common)")
        print(f"   • localhost (if host uses localhost)")
        print(f"   • Custom ID (if host sets a custom session ID)")
    else:
        available_sessions = list(debug_info['active_sessions'].keys())
        print("✅ Sessions are available! You can join using:")
        print(f"   URL: http://{remote_server_ip}:5000")
        print(f"   Session ID: {available_sessions[0]} (or any from the list above)")
    
    return True

if __name__ == "__main__":
    test_remote_server()