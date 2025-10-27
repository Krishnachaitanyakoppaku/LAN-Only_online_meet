#!/usr/bin/env python3
"""
Test script to verify the correct session ID and demonstrate the fix
"""

import requests
import json

def test_session_fix():
    print("🔍 Testing Session Fix")
    print("=" * 50)
    
    # Get server info
    try:
        response = requests.get('http://localhost:5000/api/server-info')
        server_info = response.json()
        correct_ip = server_info['server_ip']
        print(f"✅ Server IP: {correct_ip}")
    except Exception as e:
        print(f"❌ Failed to get server info: {e}")
        return
    
    # Check current sessions
    try:
        response = requests.get('http://localhost:5000/api/debug/sessions')
        debug_info = response.json()
        print(f"📊 Active sessions: {debug_info['total_sessions']}")
        print(f"👥 Connected users: {debug_info['total_users']}")
        
        if debug_info['active_sessions']:
            print("📋 Available sessions:")
            for session_id, session_data in debug_info['active_sessions'].items():
                print(f"  • {session_id} (Host: {session_data['host']}, Users: {session_data['user_count']})")
        else:
            print("⚠️  No active sessions found")
            
    except Exception as e:
        print(f"❌ Failed to get debug info: {e}")
        return
    
    print("\n" + "=" * 50)
    print("🔧 SOLUTION:")
    print("=" * 50)
    print(f"1. Host should create session at: http://{correct_ip}:5000")
    print(f"2. Session ID will be: {correct_ip}")
    print(f"3. Participants should join using session ID: {correct_ip}")
    print(f"4. NOT: 10.14.84.28 (this is wrong!)")
    
    print("\n📝 Steps to fix:")
    print("1. Host: Go to the server and click 'Host Session'")
    print("2. Host: Share the correct session ID with participants")
    print(f"3. Participants: Use session ID '{correct_ip}' to join")

if __name__ == "__main__":
    test_session_fix()