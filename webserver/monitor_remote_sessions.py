#!/usr/bin/env python3
"""
Monitor remote server for session availability
"""

import requests
import time
import json

def monitor_sessions():
    remote_server = "10.14.84.28"
    print(f"🔍 Monitoring sessions on {remote_server}:5000")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    try:
        while True:
            try:
                response = requests.get(f'http://{remote_server}:5000/api/debug/sessions', timeout=3)
                data = response.json()
                
                timestamp = time.strftime("%H:%M:%S")
                sessions = data['total_sessions']
                users = data['total_users']
                
                if sessions > 0:
                    print(f"✅ [{timestamp}] Sessions available: {sessions}, Users: {users}")
                    for session_id, session_data in data['active_sessions'].items():
                        print(f"   📋 Session ID: {session_id}")
                        print(f"      Host: {session_data['host']}")
                        print(f"      Users: {session_data['user_count']}")
                    print(f"\n🎉 You can now join at: http://{remote_server}:5000")
                    print(f"   Use session ID: {list(data['active_sessions'].keys())[0]}")
                    break
                else:
                    print(f"⏳ [{timestamp}] Waiting for host to create session... (Users connected: {users})")
                
            except Exception as e:
                print(f"❌ [{time.strftime('%H:%M:%S')}] Connection error: {e}")
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    monitor_sessions()