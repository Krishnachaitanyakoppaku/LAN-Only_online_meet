#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from server import SessionManager

# Test the session manager
sm = SessionManager()
print('Testing session manager...')

# Create main_session
result = sm.create_session('main_session', 'test_host')
print(f'Create main_session: {result}')
print(f'Available sessions: {list(sm.sessions.keys())}')

# Try to join main_session
result = sm.join_session('main_session', 'test_client')
print(f'Join main_session: {result}')
print(f'Session users: {sm.get_session_users("main_session")}')

# Try to join with empty session_id (should auto-find main_session)
result = sm.join_session('', 'test_client2')
print(f'Join with empty session_id: {result}')

# Try to join with None session_id
result = sm.join_session(None, 'test_client3')
print(f'Join with None session_id: {result}')