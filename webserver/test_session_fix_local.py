#!/usr/bin/env python3
"""
Test the session fix on local server
"""

import socketio
import time
import requests
import threading

def test_session_persistence():
    print("🔍 Testing Session Persistence Fix")
    print("=" * 50)
    
    server_url = "http://localhost:5000"
    
    # Check if local server is running
    try:
        response = requests.get(f'{server_url}/api/debug/sessions', timeout=3)
        print("✅ Local server is running")
    except:
        print("❌ Local server is not running. Please start it first:")
        print("   python3 server.py")
        return
    
    print("\n1️⃣ Creating session...")
    
    # Create session
    sio1 = socketio.Client()
    session_created = False
    session_id = None
    
    @sio1.event
    def connect():
        print("   ✅ Connected to server")
        sio1.emit('create_session', {
            'username': 'test_host',
            'session_id': 'test_se