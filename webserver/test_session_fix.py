#!/usr/bin/env python3
"""
Test script to verify session management fixes
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from server import SessionManager

def test_session_management():
    """Test the session management functionality"""
    print("Testing Session Management Fixes...")
    
    # Create session manager
    sm = SessionManager()
    
    # Test 1: Create session
    print("\n1. Testing session creation...")
    result = sm.create_session("192.168.1.100", "host_user")
    print(f"   Create session result: {result}")
    print(f"   Available sessions: {list(sm.sessions.keys())}")
    
    # Test 2: Join with exact match
    print("\n2. Testing exact session join...")
    result = sm.join_session("192.168.1.100", "client1")
    print(f"   Join session result: {result}")
    print(f"   Session users: {sm.get_session_users('192.168.1.100')}")
    
    # Test 3: Join with localhost (should find IP session)
    print("\n3. Testing localhost join (should find IP session)...")
    result = sm.join_session("localhost", "client2")
    print(f"   Join session result: {result}")
    print(f"   Session users: {sm.get_session_users('192.168.1.100')}")
    
    # Test 4: Join with 127.0.0.1 (should find IP session)
    print("\n4. Testing 127.0.0.1 join (should find IP session)...")
    result = sm.join_session("127.0.0.1", "client3")
    print(f"   Join session result: {result}")
    print(f"   Session users: {sm.get_session_users('192.168.1.100')}")
    
    # Test 5: Join non-existent session
    print("\n5. Testing non-existent session join...")
    result = sm.join_session("192.168.1.200", "client4")
    print(f"   Join session result: {result}")
    
    # Test 6: Create localhost session and join with IP
    print("\n6. Testing localhost session with IP join...")
    sm2 = SessionManager()
    result = sm2.create_session("localhost", "host2")
    print(f"   Create localhost session result: {result}")
    result = sm2.join_session("192.168.1.100", "client5")
    print(f"   Join with IP result: {result}")
    print(f"   Session users: {sm2.get_session_users('localhost')}")
    
    print("\n✅ Session management tests completed!")

if __name__ == "__main__":
    test_session_management()