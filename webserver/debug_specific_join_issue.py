#!/usr/bin/env python3
"""
Debug the specific join issue with client 172.17.222.34 trying to join server 172.17.213.107
"""

import socketio
import time
import requests

def debug_join_issue():
    print("🔍 Debugging Specific Join Issue")
    print("=" * 60)
    
    client_ip = "172.17.222.34"
    server_ip = "172.17.213.107"
    server_url = f"http://{server_ip}:5000"
    
    print(f"Client IP: {client_ip}")
    print(f"Server IP: {server_ip}")
    print(f"Server URL: {server_url}")
    print()
    
    # First, check what sessions are available
    print("1️⃣ Checking available sessions...")
    try:
        response = requests.get(f'{server_url}/api/debug/sessions')
        data = response.json()
        print(f"   Active sessions: {data['total_sessions']}")
        print(f"   Connected users: {data['total_users']}")
        
        if data['active_sessions']:
            print("   📋 Available sessions:")
            for session_id, session_data in data['active_sessions'].items():
                print(f"      • Session ID: '{session_id}'")
                print(f"        Host: {session_data['host']}")
                print(f"        Users: {session_data['user_count']}")
                print(f"        User list: {session_data.get('users', [])}")
        else:
            print("   ⚠️  No active sessions")
            return
            
    except Exception as e:
        print(f"   ❌ Failed to get session info: {e}")
        return
    
    # Get the session ID to try joining
    available_sessions = list(data['active_sessions'].keys())
    session_to_join = available_sessions[0] if available_sessions else server_ip
    
    print(f"\n2️⃣ Attempting to join session '{session_to_join}'...")
    
    # Try to join via socket
    sio = socketio.Client()
    join_success = False
    join_error = None
    
    @sio.event
    def connect():
        print("   ✅ Socket connected to server")
        # Try to join the session
        sio.emit('join_session', {
            'username': 'test_client_172_17_222_34',
            'session_id': session_to_join
        })
    
    @sio.event
    def join_success_event(data):
        nonlocal join_success
        join_success = True
        print(f"   ✅ Join successful!")
        print(f"      Session: {data['session']}")
        print(f"      Users: {data['users']}")
        print(f"      Host: {data['host']}")
        print(f"      Is Host: {data['is_host']}")
    
    @sio.event
    def join_error(data):
        nonlocal join_error
        join_error = data['message']
        print(f"   ❌ Join failed: {data['message']}")
    
    @sio.event
    def disconnect():
        print("   ℹ️  Socket disconnected")
    
    try:
        sio.connect(server_url)
        time.sleep(3)  # Wait for response
    except Exception as e:
        print(f"   ❌ Socket connection failed: {e}")
        return
    finally:
        if sio.connected:
            sio.disconnect()
    
    # Check sessions again after join attempt
    print(f"\n3️⃣ Checking sessions after join attempt...")
    try:
        response = requests.get(f'{server_url}/api/debug/sessions')
        data = response.json()
        print(f"   Active sessions: {data['total_sessions']}")
        print(f"   Connected users: {data['total_users']}")
        
        if data['active_sessions']:
            for session_id, session_data in data['active_sessions'].items():
                print(f"   • Session '{session_id}': {session_data['user_count']} users")
                print(f"     Users: {session_data.get('users', [])}")
    except Exception as e:
        print(f"   ❌ Failed to get updated session info: {e}")
    
    print("\n" + "=" * 60)
    print("🔧 ANALYSIS")
    print("=" * 60)
    
    if join_success:
        print("✅ Join was successful - the issue might be in the UI")
    elif join_error:
        print(f"❌ Join failed with error: {join_error}")
        
        # Analyze the error message
        if "client ip" in join_error.lower():
            print("\n🐛 BUG IDENTIFIED:")
            print("The error message is incorrect!")
            print("It should say 'use server IP' not 'use client IP'")
            print("This is a bug in the error message generation.")
        
        if "not found" in join_error.lower():
            print("\n🔍 SESSION LOOKUP ISSUE:")
            print("The session exists but the lookup is failing")
            print("This could be due to:")
            print("1. String matching issues (spaces, case sensitivity)")
            print("2. IP address format differences")
            print("3. Session cleanup happening too quickly")
    else:
        print("❓ No clear response - possible timeout or connection issue")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"1. Use session ID: '{session_to_join}'")
    print(f"2. Make sure to use the exact session ID (case sensitive)")
    print(f"3. If still failing, there may be a bug in the session lookup logic")

if __name__ == "__main__":
    debug_join_issue()