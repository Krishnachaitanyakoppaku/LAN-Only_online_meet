#!/usr/bin/env python3
"""
LAN Multi-User Communication Server
Handles all client connections and manages real-time communication
"""

import os
import json
import base64
import threading
import time
import socket
import struct
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import cv2
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lan_communication_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global variables for session management
connected_users = {}
active_sessions = {}
file_transfers = {}
presenter_id = None
screen_share_active = False
upload_logs = []
download_logs = []

# UDP socket for video/audio streaming
UDP_SOCKET = None
UDP_PORT = 5001

def get_host_ip():
    """Get the host machine's IP address"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"Detected host IP: {local_ip}")
        return local_ip
    except Exception as e:
        print(f"Failed to detect IP, using localhost: {e}")
        return "localhost"

class SessionManager:
    """Manages user sessions and room operations"""
    
    def __init__(self):
        self.sessions = {}
        self.user_sessions = {}
    
    def create_session(self, session_id, host_user):
        """Create a new session"""
        self.sessions[session_id] = {
            'host': host_user,
            'users': [host_user],
            'created_at': datetime.now(),
            'presenter': None,
            'screen_share': False,
            'user_permissions': {
                host_user: {
                    'video_enabled': True,
                    'audio_enabled': True,
                    'screen_share_enabled': True,
                    'is_host': True
                }
            }
        }
        self.user_sessions[host_user] = session_id
        return True
    
    def join_session(self, session_id, user):
        """Join an existing session"""
        print(f"Attempting to join session: {session_id}")
        print(f"Available sessions: {list(self.sessions.keys())}")
        
        # Try exact match first
        if session_id in self.sessions:
            # Check if user is already in the session
            if user in self.sessions[session_id]['users']:
                print(f"User {user} is already in session {session_id}")
                return True
            
            self.sessions[session_id]['users'].append(user)
            self.user_sessions[user] = session_id
            
            # Set default permissions for new user
            self.sessions[session_id]['user_permissions'][user] = {
                'video_enabled': True,
                'audio_enabled': True,
                'screen_share_enabled': True,
                'is_host': False
            }
            print(f"Successfully added user {user} to session {session_id}")
            return True
        
        # Try to find session with different IP format (localhost vs actual IP)
        for existing_session_id in self.sessions.keys():
            if existing_session_id == "localhost" and session_id != "localhost":
                print(f"Found localhost session, allowing join with IP {session_id}")
                return self.join_session(existing_session_id, user)
            elif existing_session_id != "localhost" and session_id == "localhost":
                print(f"Found IP session {existing_session_id}, allowing join with localhost")
                return self.join_session(existing_session_id, user)
        
        print(f"Session {session_id} not found")
        return False
    
    def leave_session(self, user):
        """Leave current session"""
        if user in self.user_sessions:
            session_id = self.user_sessions[user]
            if session_id in self.sessions:
                self.sessions[session_id]['users'].remove(user)
                if user in self.sessions[session_id]['user_permissions']:
                    del self.sessions[session_id]['user_permissions'][user]
                
                # If host leaves, transfer host to first remaining user
                if self.sessions[session_id]['host'] == user and len(self.sessions[session_id]['users']) > 0:
                    new_host = self.sessions[session_id]['users'][0]
                    self.sessions[session_id]['host'] = new_host
                    self.sessions[session_id]['user_permissions'][new_host]['is_host'] = True
                
                if not self.sessions[session_id]['users']:
                    del self.sessions[session_id]
            del self.user_sessions[user]
            return session_id
        return None
    
    def get_session_users(self, session_id):
        """Get all users in a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['users']
        return []
    
    def get_session_host(self, session_id):
        """Get the host of a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['host']
        return None
    
    def is_host(self, user, session_id):
        """Check if user is the host of a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['host'] == user
        return False
    
    def update_user_permission(self, session_id, target_user, permission, value):
        """Update user permission (host only)"""
        if session_id in self.sessions and target_user in self.sessions[session_id]['user_permissions']:
            self.sessions[session_id]['user_permissions'][target_user][permission] = value
            return True
        return False
    
    def get_user_permissions(self, session_id, user):
        """Get user permissions"""
        if session_id in self.sessions and user in self.sessions[session_id]['user_permissions']:
            return self.sessions[session_id]['user_permissions'][user]
        return None

session_manager = SessionManager()

def setup_udp_socket():
    """Setup UDP socket for video/audio streaming"""
    global UDP_SOCKET
    try:
        UDP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDP_SOCKET.bind(('0.0.0.0', UDP_PORT))
        print(f"UDP socket listening on port {UDP_PORT}")
        return True
    except Exception as e:
        print(f"Failed to setup UDP socket: {e}")
        return False

def start_udp_listener():
    """Start UDP listener thread for video/audio data"""
    def udp_listener():
        while True:
            try:
                data, addr = UDP_SOCKET.recvfrom(65536)
                # Process incoming video/audio data
                process_media_data(data, addr)
            except Exception as e:
                print(f"UDP listener error: {e}")
                break
    
    if UDP_SOCKET:
        thread = threading.Thread(target=udp_listener, daemon=True)
        thread.start()

def process_media_data(data, addr):
    """Process incoming media data and broadcast to other clients"""
    try:
        # Parse media data (simplified - in real implementation, you'd have proper headers)
        # For now, just broadcast to all connected users
        socketio.emit('media_data', {
            'data': base64.b64encode(data).decode('utf-8'),
            'from': addr[0]
        }, broadcast=True)
    except Exception as e:
        print(f"Error processing media data: {e}")

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/join')
def join():
    """Join session page"""
    return render_template('join.html')

@app.route('/host')
def host():
    """Host session page"""
    return render_template('host.html')

@app.route('/session')
def session():
    """Session page"""
    return render_template('session.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'success'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")
    # Clean up user data
    user_id = None
    for uid, sid in connected_users.items():
        if sid == request.sid:
            user_id = uid
            break
    
    if user_id:
        session_id = session_manager.leave_session(user_id)
        del connected_users[user_id]
        
        # Notify other users
        if session_id:
            socketio.emit('user_left', {
                'user': user_id,
                'session': session_id
            }, room=session_id)

@socketio.on('join_session')
def handle_join_session(data):
    """Handle user joining a session"""
    username = data.get('username')
    session_id = data.get('session_id')
    
    print(f"Join session request: username={username}, session_id={session_id}")
    print(f"Current connected users: {list(connected_users.keys())}")
    print(f"Current sessions: {list(session_manager.sessions.keys())}")
    
    if not username or not session_id:
        print("Join session error: Missing username or session_id")
        emit('join_error', {'message': 'Username and session ID required'})
        return
    
    # Check if username is already connected
    if username in connected_users:
        print(f"User {username} is already connected, updating connection")
    
    # Store user connection
    connected_users[username] = request.sid
    
    # Join session
    if session_manager.join_session(session_id, username):
        join_room(session_id)
        
        print(f"User {username} successfully joined session {session_id}")
        print(f"Session host: {session_manager.get_session_host(session_id)}")
        print(f"Is {username} host: {session_manager.is_host(username, session_id)}")
        
        # Notify other users
        socketio.emit('user_joined', {
            'user': username,
            'session': session_id,
            'users': session_manager.get_session_users(session_id)
        }, room=session_id)
        
        emit('join_success', {
            'session': session_id,
            'users': session_manager.get_session_users(session_id),
            'host': session_manager.get_session_host(session_id),
            'is_host': session_manager.is_host(username, session_id)
        })
    else:
        print(f"Join session error: Session {session_id} not found")
        print(f"Available sessions: {list(session_manager.sessions.keys())}")
        emit('join_error', {'message': f'Session "{session_id}" not found. Please check the session ID or ask the host to create the session first.'})

@socketio.on('create_session')
def handle_create_session(data):
    """Handle creating a new session"""
    username = data.get('username')
    custom_session_id = data.get('session_id')
    
    # Use IP address as session ID
    session_id = get_host_ip()
    
    print(f"Create session request: username={username}, session_id={session_id}")
    
    if not username:
        print("Create session error: Missing username")
        emit('create_error', {'message': 'Username required'})
        return
    
    # Store user connection
    connected_users[username] = request.sid
    
    # Create session
    if session_manager.create_session(session_id, username):
        join_room(session_id)
        
        print(f"Session {session_id} created successfully by {username}")
        print(f"Session data: {session_manager.sessions[session_id]}")
        
        emit('create_success', {
            'session': session_id,
            'users': session_manager.get_session_users(session_id),
            'is_host': True
        })
    else:
        print(f"Create session error: Failed to create session {session_id}")
        emit('create_error', {'message': 'Failed to create session'})

@socketio.on('send_message')
def handle_message(data):
    """Handle chat messages"""
    username = data.get('username')
    message = data.get('message')
    session_id = data.get('session_id')
    
    if username and message and session_id:
        message_data = {
            'username': username,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all users in session
        socketio.emit('new_message', message_data, room=session_id)

@socketio.on('start_screen_share')
def handle_start_screen_share(data):
    """Handle starting screen share"""
    username = data.get('username')
    session_id = data.get('session_id')
    
    global presenter_id, screen_share_active
    
    if username and session_id:
        presenter_id = username
        screen_share_active = True
        
        socketio.emit('screen_share_started', {
            'presenter': username,
            'session': session_id
        }, room=session_id)

@socketio.on('stop_screen_share')
def handle_stop_screen_share(data):
    """Handle stopping screen share"""
    session_id = data.get('session_id')
    
    global presenter_id, screen_share_active
    
    if session_id:
        presenter_id = None
        screen_share_active = False
        
        socketio.emit('screen_share_stopped', {
            'session': session_id
        }, room=session_id)

@socketio.on('screen_data')
def handle_screen_data(data):
    """Handle screen sharing data"""
    session_id = data.get('session_id')
    screen_data = data.get('data')
    
    if session_id and screen_data:
        # Broadcast screen data to all users except sender
        socketio.emit('screen_update', {
            'data': screen_data
        }, room=session_id, include_self=False)

@socketio.on('upload_file')
def handle_file_upload(data):
    """Handle file upload"""
    username = data.get('username')
    filename = data.get('filename')
    file_data = data.get('file_data')
    session_id = data.get('session_id')
    
    if username and filename and file_data and session_id:
        # Store file data
        file_id = f"{username}_{int(time.time())}"
        file_transfers[file_id] = {
            'filename': filename,
            'data': file_data,
            'uploader': username,
            'upload_time': datetime.now().isoformat(),
            'size': len(file_data)
        }
        
        # Log upload
        upload_logs.append({
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'filename': filename,
            'size': len(file_data),
            'session_id': session_id
        })
        
        # Notify all users about new file
        socketio.emit('file_available', {
            'file_id': file_id,
            'filename': filename,
            'uploader': username,
            'size': len(file_data)
        }, room=session_id)

@socketio.on('download_file')
def handle_file_download(data):
    """Handle file download request"""
    file_id = data.get('file_id')
    username = data.get('username')
    session_id = data.get('session_id')
    
    if file_id in file_transfers:
        file_info = file_transfers[file_id]
        
        # Log download
        download_logs.append({
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'filename': file_info['filename'],
            'size': file_info['size'],
            'session_id': session_id
        })
        
        emit('file_data', {
            'file_id': file_id,
            'filename': file_info['filename'],
            'data': file_info['data'],
            'size': file_info['size']
        })

@socketio.on('video_data')
def handle_video_data(data):
    """Handle video streaming data"""
    username = data.get('username')
    video_data = data.get('data')
    session_id = data.get('session_id')
    
    if username and video_data and session_id:
        # Broadcast video data to all users except sender
        socketio.emit('video_stream', {
            'username': username,
            'data': video_data
        }, room=session_id, include_self=False)

@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio streaming data"""
    username = data.get('username')
    audio_data = data.get('data')
    session_id = data.get('session_id')
    
    if username and audio_data and session_id:
        # Check if user has audio permission
        permissions = session_manager.get_user_permissions(session_id, username)
        if permissions and not permissions.get('audio_enabled', True):
            return
        
        # Broadcast audio data to all users except sender
        socketio.emit('audio_stream', {
            'username': username,
            'data': audio_data
        }, room=session_id, include_self=False)

# Host Control Events
@socketio.on('toggle_user_video')
def handle_toggle_user_video(data):
    """Host toggles user's video permission"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    enabled = data.get('enabled')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can control user permissions'})
        return
    
    if session_manager.update_user_permission(session_id, target_user, 'video_enabled', enabled):
        # Notify the target user
        socketio.emit('video_permission_changed', {
            'enabled': enabled,
            'controlled_by': host_user
        }, room=connected_users.get(target_user))
        
        # Notify all users in session
        socketio.emit('user_permission_updated', {
            'user': target_user,
            'permission': 'video',
            'enabled': enabled,
            'controlled_by': host_user
        }, room=session_id)

@socketio.on('toggle_user_audio')
def handle_toggle_user_audio(data):
    """Host toggles user's audio permission"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    enabled = data.get('enabled')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can control user permissions'})
        return
    
    if session_manager.update_user_permission(session_id, target_user, 'audio_enabled', enabled):
        # Notify the target user
        socketio.emit('audio_permission_changed', {
            'enabled': enabled,
            'controlled_by': host_user
        }, room=connected_users.get(target_user))
        
        # Notify all users in session
        socketio.emit('user_permission_updated', {
            'user': target_user,
            'permission': 'audio',
            'enabled': enabled,
            'controlled_by': host_user
        }, room=session_id)

@socketio.on('toggle_user_screen_share')
def handle_toggle_user_screen_share(data):
    """Host toggles user's screen share permission"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    enabled = data.get('enabled')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can control user permissions'})
        return
    
    if session_manager.update_user_permission(session_id, target_user, 'screen_share_enabled', enabled):
        # Notify the target user
        socketio.emit('screen_share_permission_changed', {
            'enabled': enabled,
            'controlled_by': host_user
        }, room=connected_users.get(target_user))
        
        # Notify all users in session
        socketio.emit('user_permission_updated', {
            'user': target_user,
            'permission': 'screen_share',
            'enabled': enabled,
            'controlled_by': host_user
        }, room=session_id)

@socketio.on('kick_user')
def handle_kick_user(data):
    """Host kicks a user from the session"""
    host_user = data.get('host_user')
    target_user = data.get('target_user')
    session_id = data.get('session_id')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can kick users'})
        return
    
    # Notify the target user
    socketio.emit('kicked_from_session', {
        'reason': 'Kicked by host',
        'kicked_by': host_user
    }, room=connected_users.get(target_user))
    
    # Remove user from session
    session_manager.leave_session(target_user)
    
    # Notify all users in session
    socketio.emit('user_kicked', {
        'user': target_user,
        'kicked_by': host_user
    }, room=session_id)

@socketio.on('get_session_logs')
def handle_get_session_logs(data):
    """Host requests session logs"""
    host_user = data.get('host_user')
    session_id = data.get('session_id')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can view logs'})
        return
    
    emit('session_logs', {
        'upload_logs': upload_logs[-50:],  # Last 50 uploads
        'download_logs': download_logs[-50:]  # Last 50 downloads
    })

@socketio.on('get_user_permissions')
def handle_get_user_permissions(data):
    """Get user permissions for host control panel"""
    host_user = data.get('host_user')
    session_id = data.get('session_id')
    
    if not session_manager.is_host(host_user, session_id):
        emit('permission_error', {'message': 'Only host can view permissions'})
        return
    
    session_data = session_manager.sessions.get(session_id, {})
    permissions = {}
    
    for user in session_data.get('users', []):
        user_perms = session_data.get('user_permissions', {}).get(user, {})
        permissions[user] = {
            'video_enabled': user_perms.get('video_enabled', True),
            'audio_enabled': user_perms.get('audio_enabled', True),
            'screen_share_enabled': user_perms.get('screen_share_enabled', True),
            'is_host': user_perms.get('is_host', False)
        }
    
    emit('user_permissions_data', {
        'permissions': permissions,
        'host': session_data.get('host')
    })

if __name__ == '__main__':
    # Setup UDP socket for media streaming
    if setup_udp_socket():
        start_udp_listener()
    
    print("Starting LAN Communication Server...")
    print("Server will be available at: http://localhost:5000")
    print("UDP streaming port: 5001")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
